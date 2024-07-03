from aws_cdk.aws_sqs import Queue
from aws_cdk import core
from aws_cdk.aws_apigatewayv2 import HttpApi, HttpMethod, LambdaProxyIntegration
from aws_cdk.aws_dynamodb import (
    Attribute,
    AttributeType,
    StreamViewType,
    Table,
    ProjectionType,
)
from aws_cdk.aws_lambda import Function, Runtime, StartingPosition, Code, LayerVersion
from aws_cdk.aws_lambda_event_sources import DynamoEventSource, SqsDlq, SqsEventSource
from aws_cdk.aws_cognito import UserPool
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_cloudfront import (
    CloudFrontWebDistribution,
    CustomOriginConfig,
    SourceConfiguration,
    Behavior,
    OriginProtocolPolicy,
    CfnDistribution,
)
from aws_cdk.aws_s3_deployment import BucketDeployment, Source
from utils import api_lambda_function

GET = HttpMethod.GET
POST = HttpMethod.POST
PYTHON_RUNTIME = Runtime.PYTHON_3_8

FRONTEND_DOMAIN_NAME = "https://vote.fadhil-blog.dev"

MAIN_PAGE_GSI = "main_page_gsi"


class VotingServerlessCdkStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        """
        Create Lambda Layer

        The packages should be stored in `python/lib/python3.7/site-packages`
        which translates to `/opt/python/lib/python3.7/site-packages` in AWS Lambda

        Refer here: https://stackoverflow.com/a/58702328/7999204
        """
        python_deps_layer = LayerVersion(
            self,
            "PythonDepsLayer",
            code=Code.from_asset("./python-deps-layer"),
            compatible_runtimes=[PYTHON_RUNTIME],
            description="A layer that contains Python Dependencies",
        )

        """
        Create DynamoDB Tables
        """
        poll_table = Table(
            self,
            "PollTable",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            sort_key=Attribute(name="SK", type=AttributeType.STRING),
            read_capacity=10,
            write_capacity=10,
            stream=StreamViewType.NEW_IMAGE,
        )

        # DynamoDB Lambda consumer worker
        aggregate_votes_function = Function(
            self,
            "AggregateVotesLambda",
            handler="ddb_stream.aggregate_vote_table",
            runtime=PYTHON_RUNTIME,
            code=Code.asset("./backend"),
            layers=[python_deps_layer],
            timeout=core.Duration.seconds(30),
        )
        aggregate_votes_function.add_environment("POLL_TABLE", poll_table.table_name)

        # DynamoDB Stream (Lambda Event Source)
        poll_table.grant_stream_read(aggregate_votes_function)
        poll_table.grant_read_write_data(aggregate_votes_function)
        ddb_aggregate_votes_event_source = DynamoEventSource(
            poll_table, starting_position=StartingPosition.LATEST
        )
        aggregate_votes_function.add_event_source(ddb_aggregate_votes_event_source)

        # DynamoDB main_page GSI
        poll_table.add_global_secondary_index(
            partition_key=Attribute(name="PK2", type=AttributeType.STRING),
            projection_type=ProjectionType.INCLUDE,
            index_name=MAIN_PAGE_GSI,
            non_key_attributes=["date", "question", "result"],
        )

        """
        Create AWS Cognito User Pool
        """
        self.users = UserPool(self, "vote-user")

        """
        HTTP API API Gateway with CORS
        """
        api = HttpApi(
            self,
            "VoteHttpApi",
            cors_preflight={
                "allow_headers": ["*"],
                "allow_methods": [
                    HttpMethod.GET,
                    HttpMethod.HEAD,
                    HttpMethod.OPTIONS,
                    HttpMethod.POST,
                ],
                "allow_origins": ["*"],
                "max_age": core.Duration.days(10),
            },
        )

        """
        HTTP API Lambda functions
        """
        get_all_votes_function = api_lambda_function(
            self,
            "GetAllVoteLambda",
            "api.get_all_votes",
            api,
            "/vote",
            GET,
            [python_deps_layer],
            [poll_table],
        )
        
        poll_table.grant_read_data(get_all_votes_function)

        get_vote_function = api_lambda_function(
            self,
            "GetVoteLambda",
            "api.get_vote_by_id",
            api,
            "/vote/{vote_id}",
            GET,
            [python_deps_layer],
            [poll_table],
        )
        poll_table.grant_read_data(get_vote_function)

        create_poll_function = api_lambda_function(
            self,
            "CreatePollLambda",
            "api.create_poll",
            api,
            "/vote",
            POST,
            [python_deps_layer],
            [poll_table],
        )
        poll_table.grant_write_data(create_poll_function)

        post_vote_function = api_lambda_function(
            self,
            "PostVoteLambda",
            "api.vote",
            api,
            "/vote/{vote_id}",
            POST,
            [python_deps_layer],
            [poll_table],
        )
