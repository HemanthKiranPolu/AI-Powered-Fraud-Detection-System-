from __future__ import annotations

import json
import os
import time
import traceback

from .aws_clients import client
from .config import get_worker_settings
from .processor import process_case


def main():
    settings = get_worker_settings()
    sqs = client("sqs")
    while True:
        msgs = sqs.receive_message(
            QueueUrl=settings.sqs_queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=15,
            VisibilityTimeout=60,
        ).get("Messages", [])
        if not msgs:
            continue
        for m in msgs:
            receipt = m["ReceiptHandle"]
            try:
                body = json.loads(m["Body"])
                process_case(body)
                sqs.delete_message(QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt)
            except Exception:
                # Let SQS redrive to DLQ via policy
                traceback.print_exc()
                continue


if __name__ == "__main__":
    main()

