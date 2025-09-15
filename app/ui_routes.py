from __future__ import annotations

import base64
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .aws import enqueue_case, save_image_bytes_to_s3
from .persistence import get_case, insert_case_pending, new_case_id
from .schemas import CaseResponse


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/ui/ingest")
async def ui_ingest(
    request: Request,
    doc_front: UploadFile = File(...),
    doc_back: Optional[UploadFile] = File(None),
    selfie: Optional[UploadFile] = File(None),
):
    if not doc_front:
        raise HTTPException(status_code=400, detail="front image required")
    case_id = new_case_id()
    keys = {"front": None, "back": None, "selfie": None}
    keys["front"] = save_image_bytes_to_s3(case_id, "front", await doc_front.read(), doc_front.content_type)
    if doc_back is not None:
        keys["back"] = save_image_bytes_to_s3(case_id, "back", await doc_back.read(), doc_back.content_type)
    if selfie is not None:
        keys["selfie"] = save_image_bytes_to_s3(case_id, "selfie", await selfie.read(), selfie.content_type)
    insert_case_pending(case_id, keys, metadata={})
    enqueue_case(case_id, keys, metadata={})
    # Render case page
    return JSONResponse({"case_id": case_id, "redirect": f"/ui/case/{case_id}"})


@router.get("/ui/case/{case_id}", response_class=HTMLResponse)
def ui_case(request: Request, case_id: str):
    # Page polls the JSON endpoint
    return templates.TemplateResponse("case.html", {"request": request, "case_id": case_id})


@router.get("/ui/case/{case_id}/json", response_model=CaseResponse)
def ui_case_json(case_id: str):
    item = get_case(case_id)
    if not item:
        raise HTTPException(status_code=404, detail="case not found")
    return CaseResponse(
        case_id=case_id,
        status=item.get("status", "PENDING"),
        fraud_score=item.get("fraud_score"),
        reasons=item.get("reasons", []),
    )

