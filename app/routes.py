from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from .aws import enqueue_case, save_images_to_s3
from .persistence import get_case, insert_case_pending, new_case_id, update_case_status, write_event
from .schemas import CaseResponse, IngestRequest, ReviewRequest
from .security import require_api_key


router = APIRouter()


@router.post("/ingest", response_model=CaseResponse)
def ingest(req: IngestRequest, _: Any = Depends(require_api_key)):
    if not req.doc_front_b64:
        raise HTTPException(status_code=400, detail="doc_front_b64 required")
    case_id = new_case_id()
    keys = save_images_to_s3(case_id, req)
    insert_case_pending(case_id, keys, metadata=req.metadata)
    enqueue_case(case_id, keys, metadata=req.metadata)
    return CaseResponse(case_id=case_id, status="PENDING", fraud_score=None, reasons=[])


@router.get("/case/{case_id}", response_model=CaseResponse)
def get_case_status(case_id: str, _: Any = Depends(require_api_key)):
    item = get_case(case_id)
    if not item:
        raise HTTPException(status_code=404, detail="case not found")
    return CaseResponse(
        case_id=case_id,
        status=item.get("status", "PENDING"),
        fraud_score=item.get("fraud_score"),
        reasons=item.get("reasons", []),
    )


@router.post("/review/{case_id}")
def review_case(case_id: str, req: ReviewRequest, _: Any = Depends(require_api_key)):
    item = get_case(case_id)
    if not item:
        raise HTTPException(status_code=404, detail="case not found")
    # Update decision and status
    if req.decision == "APPROVE":
        update_case_status(case_id, "PROCESSED")
    elif req.decision == "DENY":
        update_case_status(case_id, "PROCESSED")
    else:
        update_case_status(case_id, "REVIEW")
    write_event(case_id, "REVIEW", {"decision": req.decision, "notes": req.notes})
    item = get_case(case_id)
    return {
        "case_id": case_id,
        "status": item.get("status"),
        "fraud_score": item.get("fraud_score"),
        "reasons": item.get("reasons", []),
        "decision": req.decision,
    }

