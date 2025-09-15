import hmac
from typing import Optional

import botocore
from fastapi import Depends, Header, HTTPException

from .config import get_settings


_cached_api_key: Optional[str] = None


def _load_api_key() -> str:
    global _cached_api_key
    if _cached_api_key:
        return _cached_api_key
    settings = get_settings()
    # Try Secrets Manager
    try:
        sm = settings.boto_client("secretsmanager")
        resp = sm.get_secret_value(SecretId=settings.api_key_secret_name)
        key = resp.get("SecretString") or ""
        if key:
            _cached_api_key = key
            return key
    except botocore.exceptions.ClientError:
        pass
    # Fallback to env var
    if settings.api_key_env_fallback:
        _cached_api_key = settings.api_key_env_fallback
        return _cached_api_key
    raise RuntimeError("API key not configured. Set API_KEY or create secret.")


def require_api_key(x_api_key: str = Header(...)):
    expected = _load_api_key()
    if not hmac.compare_digest(str(x_api_key), str(expected)):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

