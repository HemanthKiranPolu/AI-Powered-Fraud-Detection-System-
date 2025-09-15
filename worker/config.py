import os
from functools import lru_cache


class WorkerSettings:
    aws_region: str = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    kms_key_arn: str = os.getenv("KMS_KEY_ARN", "")
    sqs_queue_url: str = os.getenv("SQS_QUEUE_URL", "")
    dynamo_cases_table: str = os.getenv("DYNAMO_CASES_TABLE", "fraud_cases")
    dynamo_events_table: str = os.getenv("DYNAMO_EVENTS_TABLE", "fraud_events")
    rules_path: str = os.getenv("RULES_PATH", "config/rules.yaml")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    risky_ips: list[str] = [s for s in os.getenv("RISKY_IPS", "").split(",") if s]


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()

