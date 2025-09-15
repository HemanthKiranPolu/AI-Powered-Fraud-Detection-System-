from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .aws_clients import put_metric
from .config import get_worker_settings
from .features import build_features
from .persistence import update_case_with_results
from .rekognition import compare_faces, extract_doc_face
from .scoring import load_rules, score_features
from .textract import run_textract


def process_case(msg: Dict[str, Any]):
    settings = get_worker_settings()
    case_id: str = msg["case_id"]
    s3_keys: Dict[str, Optional[str]] = msg["s3_keys"]
    bucket: str = msg.get("bucket") or settings.s3_bucket
    metadata: Dict[str, Any] = msg.get("metadata") or {}

    # Textract
    t_out = run_textract(bucket, s3_keys.get("front"), s3_keys.get("back"))

    # Face compare
    face_sim = None
    if s3_keys.get("selfie") and s3_keys.get("front"):
        doc_face_key = extract_doc_face(bucket, case_id, s3_keys["front"]) or s3_keys.get("front")
        if doc_face_key:
            face_sim = compare_faces(bucket, s3_keys["selfie"], doc_face_key)

    # Features
    feats = build_features(bucket, case_id, s3_keys, t_out, face_sim, metadata)

    # Scoring
    rules = load_rules(settings.rules_path)
    score, reasons, decision = score_features(feats, rules)

    # Persist
    update_case_with_results(case_id, bucket, s3_keys, feats, score, reasons, decision)
    put_metric("CasesProcessed", 1)
    return {"case_id": case_id, "score": score, "decision": decision}

