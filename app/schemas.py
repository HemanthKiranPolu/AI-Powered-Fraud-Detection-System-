from typing import Literal, Optional
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    doc_front_b64: str
    doc_back_b64: Optional[str] = None
    selfie_b64: Optional[str] = None
    metadata: Optional[dict] = None


class CaseResponse(BaseModel):
    case_id: str
    status: Literal["PENDING", "PROCESSED", "REVIEW", "ERROR"]
    fraud_score: Optional[float] = None
    reasons: list[str] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    decision: Literal["APPROVE", "DENY", "ESCALATE"]
    notes: Optional[str] = None

