from db.interface import AbstractDatabase
import boto3
import os
from typing import List
from models import Poll, Vote
from datetime import datetime


class DynamoDBAdapter(AbstractDatabase):
    def __init__(self):
        dynamodb = boto3.resource("dynamodb")
        self.poll_table = dynamodb.Table(os.environ.get("POLL_TABLE"))
        self.main_page_gsi = os.environ.get("MAIN_PAGE_GSI")

    def insert_poll(self, poll: Poll) -> None:
        self.poll_table.put_item(
            Item={
                "id": poll.id,
                "SK": "poll_info",
                "date": poll.date.isoformat(),
                "question": poll.question,
                "result": dict(poll.result),
                "SK1": poll.id,
                "PK1": poll.user,
                "PK2": poll.id,
            }
        )
