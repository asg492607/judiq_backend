import hashlib
import secrets
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from session import DatabaseManager

router = APIRouter()

class CreateShareReportRequest(BaseModel):
    case_id: Optional[str] = None
    user_id: Optional[str] = "ANONYMOUS"
    title: Optional[str] = "Litigation Analysis Report"
    domain: Optional[str] = "ni_act"
    password: Optional[str] = None
    case_data: Dict[str, Any] = Field(default_factory=dict)
    analysis_result: Dict[str, Any] = Field(default_factory=dict)

class VerifyReportPasswordRequest(BaseModel):
    password: str

def hash_report_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

@router.post("/share", tags=["Share Reports"])
def create_shared_report_endpoint(req: CreateShareReportRequest):
    # Generate unique 10-character URL-safe alphanumeric token
    share_id = secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:10]
    if len(share_id) < 8:
        share_id = f"rpt{secrets.token_hex(4)}"
        
    password_hash = None
    if req.password and req.password.strip():
        password_hash = hash_report_password(req.password.strip())
        
    title = req.title or (req.case_data.get("case_title") if req.case_data else None) or "Section 138 NI Act Analysis"
    case_id = req.case_id or (req.case_data.get("case_id") if req.case_data else None) or f"CASE_{secrets.token_hex(4).upper()}"
    
    success = DatabaseManager.create_shared_report(
        share_id=share_id,
