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
        case_id=case_id,
        user_id=req.user_id or "ANONYMOUS",
        title=title,
        domain=req.domain or "ni_act",
        password_hash=password_hash,
        case_data=req.case_data,
        analysis_result=req.analysis_result
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate secure shared report.")
        
    return {
        "success": True,
        "share_id": share_id,
        "is_protected": bool(password_hash),
        "title": title,
        "domain": req.domain or "ni_act"
    }

@router.get("/shared/{share_id}", tags=["Share Reports"])
def get_shared_report_endpoint(share_id: str):
    report = DatabaseManager.get_shared_report(share_id)
    if not report:
        raise HTTPException(status_code=404, detail="Shared report not found or has been revoked.")
        
    is_protected = bool(report.get("password_hash"))
    
    # If not password-protected, return full case and analysis data
    if not is_protected:
        DatabaseManager.increment_shared_report_views(share_id)
        return {
            "success": True,
            "share_id": report["share_id"],
            "case_id": report["case_id"],
            "title": report["title"],
            "domain": report["domain"],
            "is_protected": False,
            "created_at": report["created_at"],
            "views": report["views"] + 1,
            "case_data": report["case_data"],
            "analysis_result": report["analysis_result"]
        }
        
    # If password-protected, return metadata only (requires password unlock)
    return {
        "success": True,
        "share_id": report["share_id"],
        "case_id": report["case_id"],
        "title": report["title"],
        "domain": report["domain"],
        "is_protected": True,
        "created_at": report["created_at"],
        "views": report["views"]
    }

@router.post("/shared/{share_id}/verify", tags=["Share Reports"])
def verify_shared_report_password(share_id: str, req: VerifyReportPasswordRequest):
    report = DatabaseManager.get_shared_report(share_id)
    if not report:
        raise HTTPException(status_code=404, detail="Shared report not found.")
        
    stored_hash = report.get("password_hash")
    if not stored_hash:
        return {
            "success": True,
            "share_id": report["share_id"],
            "case_id": report["case_id"],
            "title": report["title"],
            "domain": report["domain"],
            "created_at": report["created_at"],
            "case_data": report["case_data"],
            "analysis_result": report["analysis_result"]
        }
        
    provided_hash = hash_report_password(req.password.strip())
    if provided_hash != stored_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Access to this litigation report is restricted."
        )
        
    DatabaseManager.increment_shared_report_views(share_id)
    return {
        "success": True,
        "share_id": report["share_id"],
        "case_id": report["case_id"],
        "title": report["title"],
        "domain": report["domain"],
        "created_at": report["created_at"],
        "case_data": report["case_data"],
        "analysis_result": report["analysis_result"]
    }
