# Reference: https://github.com/linuxacademy/content-dynamodb-deepdive/blob/master/6.2.2-Aggregation_With_Streams/lambda_function.py

import decimal

import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from models import Poll
from db.dynamodb import DynamoDBAdapter
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

td = TypeDeserializer()
db = DynamoDBAdapter()


def aggregate_vote_table(event, context):
    logger.info(event)

    # Use in application cache so that it refresh everytime it runs
    polls = {}

    for record in event["Records"]:
        logger.info(record)

        if record["eventName"] != "INSERT":
            # If it's other operation other than INSERT, ignore it
            continue
