import dataclasses
import json
import logging
import os
import uuid
from collections import Counter
from datetime import datetime

import boto3
from aws_xray_sdk.core import patch_all, xray_recorder
from botocore.exceptions import ClientError


from db.dynamodb import DynamoDBAdapter
from models import Poll, Vote


logger = logging.getLogger()
logger.setLevel(logging.INFO)
patch_all()
sqs = boto3.client("sqs")


db = DynamoDBAdapter()
queue_url = os.environ.get("VOTING_QUEUE_URL")


def get_all_votes(event, context):
    """
    Get most recent polls from ddb
    """

    logger.info("get all polls")
    polls = db.get_all_polls()
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": Poll.schema().dumps(polls, many=True),
    }


def get_vote_by_id(event, context):
    """
    Read a single vote item from ddb
    """
    id = event.get("pathParameters").get("vote_id")
    poll = db.get_poll(id)

    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": poll.to_json(),
    }
