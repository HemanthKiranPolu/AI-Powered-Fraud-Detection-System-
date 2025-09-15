import base64
import hashlib
import re
from typing import Tuple


DATA_URI_RE = re.compile(r"^data:(?P<mime>[-\w./+]+);base64,(?P<data>.*)$", re.IGNORECASE)


def decode_base64_image(b64: str) -> Tuple[bytes, str]:
    """Decode base64 image string, supports data URI. Returns bytes and inferred mime type.
    Defaults mime to image/jpeg when unknown.
    """
    match = DATA_URI_RE.match(b64)
    if match:
        mime = match.group("mime")
        data = match.group("data")
        raw = base64.b64decode(data)
        return raw, mime
    # Plain base64
    try:
        raw = base64.b64decode(b64, validate=True)
        return raw, "image/jpeg"
    except Exception:
        # try forgiving decode
        raw = base64.b64decode(b64)
        return raw, "image/jpeg"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mask_identifier(value: str) -> str:
    """Mask identifiers like ID numbers; show only last 4 chars.
    Keep non-digits as-is but mask alphanumerics conservatively.
    """
    if not value:
        return value
    keep = value[-4:]
    return ("*" * max(0, len(value) - 4)) + keep

