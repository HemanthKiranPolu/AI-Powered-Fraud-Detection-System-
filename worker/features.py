from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .aws_clients import client, s3_get_object
from .config import get_worker_settings
from .image_ops import blur_score as _blur_score, glare_score as _glare_score
from .mrz import validate_mrz


def build_features(
    bucket: str,
    case_id: str,
    s3_keys: Dict[str, Optional[str]],
    tex_out: Dict[str, Any],
    face_similarity: Optional[float],
    metadata: Dict[str, Any] | None,
) -> Dict[str, Any]:
    settings = get_worker_settings()
    features: Dict[str, Any] = {}
    # Face similarity
    features["face_similarity"] = float(face_similarity or 0.0)

    # Textract confidence
    features["textract_conf_avg"] = float(tex_out.get("avg_conf") or 0.0)

    # MRZ validity if present
    mrz_lines = tex_out.get("mrz_lines", [])
    mrz_ok, mrz_parsed = validate_mrz(mrz_lines)
    features["mrz_valid"] = bool(mrz_ok)

    # Expiry validity from fields
    expiry_valid = None
    expiry = _parse_date(tex_out.get("fields", {}).get("date_of_expiry") or tex_out.get("fields", {}).get("expiry_date"))
    if expiry:
        expiry_valid = expiry > datetime.now(timezone.utc)
    features["expiry_valid"] = bool(expiry_valid) if expiry_valid is not None else False

    # Image quality
    blur = 0.0
    glare = 0.0
    if s3_keys.get("front"):
        img = s3_get_object(bucket, s3_keys["front"])  # bytes
        blur = _blur_score(img)
        glare = _glare_score(img)
    features["blur_score"] = float(1.0 - min(1.0, blur))  # higher worse
    features["glare_score"] = float(min(1.0, glare))

    # Template geometry score (placeholder) - assume mid if no template
    features["template_geom_score"] = 0.5

    # Velocity and device/ip risk
    device_hash = (metadata or {}).get("device_hash")
    ip = (metadata or {}).get("ip")
    features["device_hash_dup"], features["velocity_count_24h"] = device_velocity_count(device_hash)
    features["ip_risk_score"] = 1.0 if ip and ip in settings.risky_ips else 0.0

    # Basic field consistency checks (name capitalization, DOB format)
    fields = tex_out.get("fields", {})
    features["field_consistency_flags"] = int(_field_inconsistency_flags(fields))

    return features


def device_velocity_count(device_hash: Optional[str]) -> tuple[bool, int]:
    if not device_hash:
        return False, 0
    settings = get_worker_settings()
    dynamo = client("dynamodb")
    now = int(datetime.now(timezone.utc).timestamp())
    since = now - 24 * 3600
    try:
        resp = dynamo.query(
            TableName=settings.dynamo_events_table,
            IndexName="gsi_device",
            KeyConditionExpression="#dh = :dh AND #ts >= :since",
            ExpressionAttributeNames={"#dh": "device_hash", "#ts": "ts"},
            ExpressionAttributeValues={":dh": {"S": device_hash}, ":since": {"N": str(since)}},
            Select="COUNT",
        )
        count = int(resp.get("Count", 0))
        return (count > 3), count
    except Exception:
        return False, 0


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    v = value.strip().replace("/", "-")
    # Try YYYY-MM-DD, YYMMDD
    try:
        if len(v) == 6 and v.isdigit():
            # YYMMDD
            yy = int(v[0:2])
            mm = int(v[2:4])
            dd = int(v[4:6])
            year = 2000 + yy if yy < 70 else 1900 + yy
            return datetime(year, mm, dd, tzinfo=timezone.utc)
        from datetime import date

        return datetime.fromisoformat(v).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _field_inconsistency_flags(fields: Dict[str, Any]) -> int:
    flags = 0
    name = fields.get("surname") or fields.get("last_name") or fields.get("name")
    if name and name.islower():
        flags += 1
    dob = fields.get("date_of_birth") or fields.get("dob")
    if dob and not (_parse_date(dob) is not None):
        flags += 1
    return flags

