from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .aws_clients import client, s3_put_object
from .config import get_worker_settings


def update_case_with_results(
    case_id: str,
    bucket: str,
    s3_keys: Dict[str, Optional[str]],
    features: Dict[str, Any],
    score: float,
    reasons: list[str],
    decision: str,
    artifacts: Optional[Dict[str, Any]] = None,
):
    settings = get_worker_settings()
    dynamo = client("dynamodb")
    now = datetime.now(timezone.utc).isoformat()
    # Store a redacted artifact JSON to S3
    artifact_key = f"cases/{case_id}/artifacts/results.json"
    s3_put_object(bucket, artifact_key, json.dumps({"features": features, "score": score, "reasons": reasons, "decision": decision}).encode("utf-8"), kms_key_arn=settings.kms_key_arn, content_type="application/json")
    # Update DDB
    dynamo.update_item(
        TableName=settings.dynamo_cases_table,
        Key={"case_id": {"S": case_id}},
        UpdateExpression="SET fraud_score=:f, reasons=:r, updated_at=:u, decision=:d, status=:s, artifact_key=:a",
        ExpressionAttributeValues={
            ":f": {"N": str(score)},
            ":r": {"L": [{"S": str(x)} for x in reasons]},
            ":u": {"S": now},
            ":d": {"S": decision},
            ":s": {"S": "PROCESSED"},
            ":a": {"S": artifact_key},
        },
    )
    write_event(case_id, "DECISION", {"decision": decision, "score": score})


def write_event(case_id: str, event_type: str, payload: dict):
    settings = get_worker_settings()
    dynamo = client("dynamodb")
    ts = int(datetime.now(timezone.utc).timestamp())
    item = {
        "case_id": {"S": case_id},
        "ts": {"N": str(ts)},
        "type": {"S": event_type},
        "payload": {"S": json.dumps({k: v for k, v in (payload or {}).items() if k not in {"raw", "image", "pii"}})},
        "ttl": {"N": str(ts + 90 * 24 * 3600)},
    }
    dynamo.put_item(TableName=settings.dynamo_events_table, Item=item)

