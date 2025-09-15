from __future__ import annotations

from typing import Dict, Optional, Tuple

from .aws_clients import client, s3_get_object, s3_put_object
from .config import get_worker_settings
from .image_ops import crop_bbox


def detect_face_bbox(bucket: str, key: str) -> Optional[Tuple[float, float, float, float]]:
    rek = client("rekognition")
    resp = rek.detect_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}}, Attributes=["DEFAULT"])
    faces = resp.get("FaceDetails", [])
    if not faces:
        return None
    # choose largest by area
    best = max(faces, key=lambda f: (f.get("BoundingBox", {}).get("Width", 0) * f.get("BoundingBox", {}).get("Height", 0)))
    bbox = best.get("BoundingBox")
    return (bbox.get("Left"), bbox.get("Top"), bbox.get("Width"), bbox.get("Height"))


def extract_doc_face(bucket: str, case_id: str, front_key: str) -> Optional[str]:
    bbox = detect_face_bbox(bucket, front_key)
    if not bbox:
        return None
    # Crop and upload
    settings = get_worker_settings()
    raw = s3_get_object(bucket, front_key)
    crop = crop_bbox(raw, bbox)
    key_out = f"cases/{case_id}/doc_face.jpg"
    s3_put_object(bucket, key_out, crop, kms_key_arn=settings.kms_key_arn, content_type="image/jpeg")
    return key_out


def compare_faces(bucket: str, selfie_key: str, doc_face_key: str) -> Optional[float]:
    rek = client("rekognition")
    try:
        resp = rek.compare_faces(
            SourceImage={"S3Object": {"Bucket": bucket, "Name": selfie_key}},
            TargetImage={"S3Object": {"Bucket": bucket, "Name": doc_face_key}},
            SimilarityThreshold=70,
        )
        matches = resp.get("FaceMatches", [])
        if not matches:
            return 0.0
        best = max(matches, key=lambda m: m.get("Similarity", 0))
        return float(best.get("Similarity", 0.0))
    except Exception:
        return None

