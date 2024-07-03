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