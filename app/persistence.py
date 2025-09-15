from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .config import get_settings
from .logging_utils import setup_logger


log = setup_logger(__name__)


def new_case_id() -> str:
    return uuid.uuid4().hex


def _dynamo():
    return get_settings().boto_session().resource("dynamodb")


def insert_case_pending(case_id: str, keys: Dict[str, Optional[str]], metadata: Optional[dict] = None):
    settings = get_settings()
    table = _dynamo().Table(settings.dynamo_cases_table)
    now = datetime.now(timezone.utc).isoformat()
    item: Dict[str, Any] = {
        "case_id": case_id,
        "status": "PENDING",
        "fraud_score": None,
        "reasons": [],
        "created_at": now,
        "updated_at": now,
        "s3_keys": keys,
        "metadata": metadata or {},
    }
    table.put_item(Item=item)
    write_event(case_id, "INGEST", {"device_hash": (metadata or {}).get("device_hash"), "ip": (metadata or {}).get("ip")})


def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    table = _dynamo().Table(settings.dynamo_cases_table)
    r = table.get_item(Key={"case_id": case_id})
    return r.get("Item")


def update_case_status(case_id: str, status: str):
    settings = get_settings()
    table = _dynamo().Table(settings.dynamo_cases_table)
    now = datetime.now(timezone.utc).isoformat()
    table.update_item(
        Key={"case_id": case_id},
        UpdateExpression="SET #s = :s, updated_at = :u",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status, ":u": now},
    )


def update_case_results(case_id: str, fraud_score: float, reasons: list[str], decision: Optional[str] = None):
    settings = get_settings()
    table = _dynamo().Table(settings.dynamo_cases_table)
    now = datetime.now(timezone.utc).isoformat()
    expr = "SET fraud_score=:f, reasons=:r, updated_at=:u"
    eav = {":f": fraud_score, ":r": reasons, ":u": now}
    ean = {}
    if decision:
        expr += ", decision=:d"
        eav[":d"] = decision
    table.update_item(Key={"case_id": case_id}, UpdateExpression=expr, ExpressionAttributeValues=eav, ExpressionAttributeNames=ean)
    write_event(case_id, "SCORED", {"fraud_score": fraud_score, "reasons": reasons, "decision": decision})


def write_event(case_id: str, event_type: str, payload: dict):
    settings = get_settings()
    table = _dynamo().Table(settings.dynamo_events_table)
    ts = int(time.time())
    item = {
        "case_id": case_id,
        "ts": ts,
        "type": event_type,
        # Only store minimal payload and avoid raw PII
        "payload": {k: v for k, v in (payload or {}).items() if k not in {"raw", "image", "pii"}},
        # TTL for retention (default 90 days unless configured on table)
        "ttl": ts + 90 * 24 * 3600,
        # Useful for GSI on device velocity
        "device_hash": (payload or {}).get("device_hash"),
        "ip": (payload or {}).get("ip"),
    }
    table.put_item(Item={k: v for k, v in item.items() if v is not None})

