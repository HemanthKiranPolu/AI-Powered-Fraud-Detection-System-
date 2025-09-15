import os
from functools import lru_cache
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig


class Settings:
    # Core AWS
    aws_region: str = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

    # Data storage
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    kms_key_arn: str = os.getenv("KMS_KEY_ARN", "")
    dynamo_cases_table: str = os.getenv("DYNAMO_CASES_TABLE", "fraud_cases")
    dynamo_events_table: str = os.getenv("DYNAMO_EVENTS_TABLE", "fraud_events")

    # Messaging
    sqs_queue_url: str = os.getenv("SQS_QUEUE_URL", "")

    # Auth
    api_key_secret_name: str = os.getenv("API_KEY_SECRET_NAME", "fraud_api_key")
    api_key_env_fallback: str = os.getenv("API_KEY", "")

    # Observability
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Compliance
    image_ttl_days: int = int(os.getenv("IMAGE_TTL_DAYS", "30"))

    # Network / risk
    risky_ips: list[str] = [s for s in os.getenv("RISKY_IPS", "").split(",") if s]

    def boto_session(self) -> boto3.session.Session:
        return boto3.session.Session(region_name=self.aws_region)

    def boto_client(self, service: str):
        return self.boto_session().client(service, config=BotoConfig(retries={"max_attempts": 8, "mode": "standard"}))


@lru_cache
def get_settings() -> Settings:
    return Settings()

