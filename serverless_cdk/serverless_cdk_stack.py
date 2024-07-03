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
