import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Request, Depends
from pydantic import BaseModel, Field
from session import DatabaseManager
from security import get_current_user_optional
from audit_service import AuditService
import json

router = APIRouter()

class CaseCreatePayload(BaseModel):
    case_name: str
    case_type: Optional[str] = "section_138"
    priority: Optional[str] = "medium"
    description: Optional[str] = ""
    tags: Optional[List[str]] = []
    creditor_data: Optional[Dict[str, Any]] = {}
    debtor_data: Optional[Dict[str, Any]] = {}
    company_data: Optional[Dict[str, Any]] = {}
    financial_data: Optional[Dict[str, Any]] = {}
    collateral_data: Optional[Dict[str, Any]] = {}
    court_data: Optional[Dict[str, Any]] = {}
    access_level: Optional[str] = "private"
    org_id: Optional[str] = None

class CaseUpdatePayload(BaseModel):
    case_name: Optional[str] = None
    case_type: Optional[str] = None
    case_status: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    creditor_data: Optional[Dict[str, Any]] = None
    debtor_data: Optional[Dict[str, Any]] = None
    company_data: Optional[Dict[str, Any]] = None
    financial_data: Optional[Dict[str, Any]] = None
    collateral_data: Optional[Dict[str, Any]] = None
    court_data: Optional[Dict[str, Any]] = None
    access_level: Optional[str] = None

class StatusUpdatePayload(BaseModel):
    status: str

class SharePayload(BaseModel):
    user_ids: List[str]

@router.post("/cases")
def create_case(
    payload: CaseCreatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    # Auto-generate Case ID: CSE-YYYY-MM-NNNNNN
    now = datetime.now()
    case_id = f"CSE-{now.strftime('%Y-%m')}-{uuid.uuid4().hex[:6].upper()}"

    res = DatabaseManager.cms_create_case(
        case_id=case_id,
        user_id=actual_user,
        case_name=payload.case_name,
        case_type=payload.case_type or "section_138",
        priority=payload.priority or "medium",
        description=payload.description or "",
        tags=payload.tags or [],
        creditor_data=payload.creditor_data or {},
        debtor_data=payload.debtor_data or {},
        company_data=payload.company_data or {},
        financial_data=payload.financial_data or {},
        collateral_data=payload.collateral_data or {},
        court_data=payload.court_data or {},
        access_level=payload.access_level or "private",
        org_id=payload.org_id
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to create case"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="CASE_CREATED",
        entity_type="case",
        entity_id=case_id,
        case_id=case_id,
        after_state={"case_name": payload.case_name, "case_type": payload.case_type, "priority": payload.priority},
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Created case {case_id}: {payload.case_name}"
    )

    return {
        "success": True,
        "case_id": case_id,
        "case_name": payload.case_name,
        "created_at": res.get("created_at")
    }

@router.get("/cases")
def list_cases(
    status: Optional[str] = Query("all"),
    case_type: Optional[str] = Query("all"),
    priority: Optional[str] = Query("all"),
    search: Optional[str] = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    return DatabaseManager.cms_list_cases(
        user_id=actual_user,
        status=status,
        case_type=case_type,
        priority=priority,
        search=search,
        page=page,
        limit=limit
    )

@router.get("/cases/{case_id}")
def get_case_detail(
    case_id: str,
    user_id: str = Depends(get_current_user_optional)
):
    case = DatabaseManager.cms_get_case(case_id=case_id, user_id=user_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case

@router.put("/cases/{case_id}")
def update_case(
    case_id: str,
    payload: CaseUpdatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    before = DatabaseManager.cms_get_case(case_id=case_id)
    if not before:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    updates = {k: v for k, v in payload.dict().items() if v is not None}
    res = DatabaseManager.cms_update_case(case_id=case_id, updates=updates)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to update case"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="CASE_UPDATED",
        entity_type="case",
        entity_id=case_id,
        case_id=case_id,
        after_state=updates,
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Updated case {case_id}"
    )

    return {"success": True, "case_id": case_id, "updated_at": res.get("updated_at")}

@router.patch("/cases/{case_id}/status")
def update_case_status(
    case_id: str,
    payload: StatusUpdatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    before = DatabaseManager.cms_get_case(case_id=case_id)
    if not before:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    res = DatabaseManager.cms_update_case_status(case_id=case_id, new_status=payload.status)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to update status"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="STATUS_CHANGED",
        entity_type="case",
        entity_id=case_id,
        case_id=case_id,
        before_state={"status": before.get("case_status")},
        after_state={"status": payload.status},
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Status changed from {before.get('case_status')} to {payload.status}"
    )

    return {"success": True, "case_id": case_id, "status": payload.status}

@router.delete("/cases/{case_id}")
def delete_case(
    case_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    res = DatabaseManager.cms_update_case_status(case_id=case_id, new_status="archived")
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to archive case"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="CASE_ARCHIVED",
        entity_type="case",
        entity_id=case_id,
        case_id=case_id,
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Archived case {case_id}"
    )

    return {"success": True, "case_id": case_id, "status": "archived"}

@router.post("/cases/{case_id}/share")
def share_case(
    case_id: str,
    payload: SharePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    case = DatabaseManager.cms_get_case(case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    existing_shared = case.get("shared_with") or []
    if isinstance(existing_shared, str):
        try:
            existing_shared = json.loads(existing_shared)
        except Exception:
            existing_shared = []
    
    updated_shared = list(set(existing_shared + payload.user_ids))
    DatabaseManager.cms_update_case(case_id=case_id, updates={"shared_with": updated_shared})

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="CASE_SHARED",
        entity_type="case",
        entity_id=case_id,
        case_id=case_id,
        after_state={"shared_with": updated_shared},
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Shared case with {len(payload.user_ids)} users"
    )

    return {"success": True, "case_id": case_id, "shared_with": updated_shared}

@router.get("/cases/{case_id}/timeline")
def get_case_timeline(case_id: str):
    trail = AuditService.get_case_trail(case_id=case_id, limit=100)
    return {"case_id": case_id, "timeline": trail}

@router.post("/cases/{case_id}/analyze")
def analyze_case(
    case_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    case = DatabaseManager.cms_get_case(case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Map CMS case data to analysis input structure
    cdata = case.get("financial_data") or {}
    creditor = case.get("creditor_data") or {}
    debtor = case.get("debtor_data") or {}
    court = case.get("court_data") or {}

    analysis_input = {
        "case_title": case.get("case_name"),
        "case_type": case.get("case_type"),
        "complainant_name": creditor.get("name") or creditor.get("complainant_name", ""),
        "accused_name": debtor.get("name") or debtor.get("accused_name", ""),
        "court_name": court.get("court_name", ""),
        "filing_date": court.get("filing_date", datetime.now().strftime("%Y-%m-%d")),
        **cdata
    }

    try:
        from analysis import run_12_pillar_analysis
        result = run_12_pillar_analysis(analysis_input)
        
        score = result.get("score") or result.get("overall_score") or 0.0
        verdict = result.get("verdict") or "PENDING"
        
        DatabaseManager.cms_update_case(case_id=case_id, updates={
            "analysis_result": result,
            "compliance_score": score,
            "verdict": verdict,
            "case_status": "ongoing" if case.get("case_status") == "draft" else case.get("case_status")
        })

        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        AuditService.log(
            user_id=actual_user,
            action="ANALYSIS_RUN",
            entity_type="case",
            entity_id=case_id,
            case_id=case_id,
            after_state={"score": score, "verdict": verdict},
            ip_address=client_ip,
            user_agent=user_agent,
            note=f"Ran 12-pillar analysis: Score {score}, Verdict {verdict}"
        )

        return {
            "success": True,
            "case_id": case_id,
            "compliance_score": score,
            "verdict": verdict,
            "analysis_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
