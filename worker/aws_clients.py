import io
import json
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config as BotoConfig

from .config import get_worker_settings


def session() -> boto3.session.Session:
    return boto3.session.Session(region_name=get_worker_settings().aws_region)


def client(service: str):
    return session().client(service, config=BotoConfig(retries={"max_attempts": 8, "mode": "standard"}))


def s3_get_object(bucket: str, key: str) -> bytes:
    s3 = client("s3")
    r = s3.get_object(Bucket=bucket, Key=key)
    return r["Body"].read()


def s3_put_object(bucket: str, key: str, data: bytes, kms_key_arn: Optional[str] = None, content_type: str = "image/jpeg", metadata: Optional[Dict[str, str]] = None):
    s3 = client("s3")
    args: Dict[str, Any] = {
        "Bucket": bucket,
        "Key": key,
        "Body": data,
        "ContentType": content_type,
        "Metadata": metadata or {},
    }
    if kms_key_arn:
        args["ServerSideEncryption"] = "aws:kms"
        args["SSEKMSKeyId"] = kms_key_arn
    s3.put_object(**args)


def put_metric(name: str, value: float, unit: str = "Count"):
    cw = client("cloudwatch")
    cw.put_metric_data(
        Namespace="FraudDetection",
        MetricData=[{"MetricName": name, "Value": value, "Unit": unit}],
    )

