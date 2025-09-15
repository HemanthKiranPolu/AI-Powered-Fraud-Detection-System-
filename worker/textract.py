from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from .aws_clients import client


def run_textract(bucket: str, front_key: str, back_key: Optional[str] = None) -> Dict[str, Any]:
    tex = client("textract")
    out: Dict[str, Any] = {"fields": {}, "confidence": {}, "avg_conf": None, "raw": None, "mrz_lines": []}
    try:
        pages = [{"S3Object": {"Bucket": bucket, "Name": front_key}}]
        if back_key:
            pages.append({"S3Object": {"Bucket": bucket, "Name": back_key}})
        resp = tex.analyze_id(DocumentPages=pages)
        out["raw"] = resp
        fields: Dict[str, str] = {}
        confs: Dict[str, float] = {}
        confs_list = []
        for doc in resp.get("IdentityDocuments", []):
            for field in doc.get("IdentityDocumentFields", []):
                type_text = (field.get("Type") or {}).get("Text")
                val_text = (field.get("ValueDetection") or {}).get("Text")
                conf = (field.get("ValueDetection") or {}).get("Confidence")
                if type_text and val_text is not None:
                    key = normalize_field_name(type_text)
                    fields[key] = val_text
                    if conf is not None:
                        confs[key] = float(conf)
                        confs_list.append(float(conf))
        out["fields"] = fields
        out["confidence"] = confs
        out["avg_conf"] = sum(confs_list) / len(confs_list) if confs_list else None
        # MRZ lines occasionally appear as fields or blocks; keep placeholder empty for AnalyzeID
        return out
    except Exception:
        # Fallback to AnalyzeDocument (FORMS). We won't parse comprehensively here.
        resp = tex.analyze_document(
            Document={"S3Object": {"Bucket": bucket, "Name": front_key}}, FeatureTypes=["FORMS", "TABLES"]
        )
        out["raw"] = resp
        fields: Dict[str, str] = {}
        confs_list = []
        for block in resp.get("Blocks", []):
            if block.get("BlockType") == "KEY_VALUE_SET" and block.get("EntityTypes") == ["KEY"]:
                key_text = concat_child_text(block, resp)
                if key_text:
                    # naive: try to get value pair via relationships
                    val_text = find_value_for_key(block, resp)
                    if val_text:
                        fields[normalize_field_name(key_text)] = val_text
            if block.get("BlockType") == "LINE":
                txt = block.get("Text")
                if txt and len(txt) >= 30 and any(c in txt for c in ("<<", "<")):
                    out["mrz_lines"].append(txt)
        out["fields"] = fields
        out["avg_conf"] = sum(confs_list) / len(confs_list) if confs_list else None
        return out


def normalize_field_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def concat_child_text(block: Dict[str, Any], resp: Dict[str, Any]) -> str:
    id_to_block = {b["Id"]: b for b in resp.get("Blocks", []) if "Id" in b}
    text_parts = []
    for rel in block.get("Relationships", []) or []:
        if rel.get("Type") == "CHILD":
            for cid in rel.get("Ids", []):
                w = id_to_block.get(cid)
                if w and w.get("BlockType") == "WORD":
                    text_parts.append(w.get("Text", ""))
    return " ".join(text_parts).strip()


def find_value_for_key(key_block: Dict[str, Any], resp: Dict[str, Any]) -> Optional[str]:
    id_to_block = {b["Id"]: b for b in resp.get("Blocks", []) if "Id" in b}
    for rel in key_block.get("Relationships", []) or []:
        if rel.get("Type") == "VALUE":
            for vid in rel.get("Ids", []):
                v = id_to_block.get(vid)
                if not v:
                    continue
                txt = concat_child_text(v, resp)
                if txt:
                    return txt
    return None

