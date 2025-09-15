import io
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from .config import get_settings
from .utils import decode_base64_image, sha256_hex


def save_images_to_s3(case_id: str, req) -> Dict[str, str]:
    settings = get_settings()
    s3 = settings.boto_client("s3")
    kms_key = settings.kms_key_arn or None

    def put_image(name: str, b64: Optional[str]) -> Optional[str]:
        if not b64:
            return None
        raw, mime = decode_base64_image(b64)
        key = f"cases/{case_id}/{name}.jpg"
        extra_args = {
            "Bucket": settings.s3_bucket,
            "Key": key,
            "Body": raw,
            "ContentType": mime or "image/jpeg",
            "Metadata": {
                "sha256": sha256_hex(raw),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        if kms_key:
            extra_args["ServerSideEncryption"] = "aws:kms"
            extra_args["SSEKMSKeyId"] = kms_key
        s3.put_object(**extra_args)
        return key

    front_key = put_image("front", req.doc_front_b64)
    back_key = put_image("back", req.doc_back_b64)
    selfie_key = put_image("selfie", req.selfie_b64)
    return {"front": front_key, "back": back_key, "selfie": selfie_key}


def save_image_bytes_to_s3(case_id: str, name: str, data: bytes, mime: str | None = None) -> str:
    """Save raw image bytes to S3 with SSE-KMS and metadata. Returns the object key."""
    settings = get_settings()
    s3 = settings.boto_client("s3")
    kms_key = settings.kms_key_arn or None
    key = f"cases/{case_id}/{name}.jpg"
    extra_args = {
        "Bucket": settings.s3_bucket,
        "Key": key,
        "Body": data,
        "ContentType": mime or "image/jpeg",
        "Metadata": {"sha256": sha256_hex(data)},
    }
    if kms_key:
        extra_args["ServerSideEncryption"] = "aws:kms"
        extra_args["SSEKMSKeyId"] = kms_key
    s3.put_object(**extra_args)
    return key


def enqueue_case(case_id: str, keys: Dict[str, Optional[str]], metadata: Optional[dict] = None):
    settings = get_settings()
    sqs = settings.boto_client("sqs")
    body = {
        "case_id": case_id,
        "s3_keys": keys,
        "bucket": settings.s3_bucket,
        "metadata": metadata or {},
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
    }
    sqs.send_message(QueueUrl=settings.sqs_queue_url, MessageBody=json.dumps(body))
