import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Request, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from session import DatabaseManager
from security import get_current_user_optional
from audit_service import AuditService
from draft_engine import decide_draft_type
from pdf_generator import PDFGenerator
from word_generator import WordGenerator

router = APIRouter()

class DraftCreatePayload(BaseModel):
    draft_type: Optional[str] = None
    tone: Optional[str] = "standard"
    custom_content: Optional[str] = None

class DraftUpdatePayload(BaseModel):
    content: str
    assigned_reviewer: Optional[str] = None

class ReviewPayload(BaseModel):
    comment: str
    status: Optional[str] = "IN_REVISION"  # 'IN_REVISION' or 'APPROVED'

class ApprovePayload(BaseModel):
    note: Optional[str] = None

class FiledPayload(BaseModel):
    filed_reference: str
    court_name: Optional[str] = None

@router.post("/cases/{case_id}/drafts")
def create_draft(
    case_id: str,
    payload: DraftCreatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    case = DatabaseManager.cms_get_case(case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    workflow_id = f"DRF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    draft_type = payload.draft_type or "LEGAL_NOTICE"

    content = payload.custom_content
    if not content:
        # Generate initial draft text using draft engine or templates
        cdata = case.get("financial_data") or {}
        creditor = case.get("creditor_data") or {}
        debtor = case.get("debtor_data") or {}
        court = case.get("court_data") or {}
        
        content = f"""
LEGAL DRAFT: {draft_type.replace('_', ' ').upper()}
Case ID: {case_id}
Date: {datetime.now().strftime('%d %B %Y')}

IN THE MATTER OF:
{creditor.get('name', 'COMPLAINANT / CREDITOR')}
... Complainant / Secured Creditor

VERSUS

{debtor.get('name', 'ACCUSED / BORROWER')}
... Accused / Respondent

1. That the Complainant is a legally recognized entity having its principal office at {creditor.get('address', '[Address]')}.
2. That the Accused approached the Complainant for financial accommodation / transaction dated {cdata.get('transaction_date', '[Date]')}.
3. That in discharge of legal debt / liability, the Accused issued Cheque / Instrument bearing details as recorded in case dossier.
4. That the said instrument was presented and dishonoured by bank with remarks recorded on memo.
5. That statutory demand notice was dispatched and delivered, yet the Accused failed to discharge liability.

WHEREFORE IT IS PRAYED THAT:
Appropriate orders and relief under applicable statutory provisions be passed against the Accused in the interest of justice.

DATED: {datetime.now().strftime('%d-%m-%Y')}
COUNSEL FOR COMPLAINANT
"""

    res = DatabaseManager.cms_create_draft_workflow(
        workflow_id=workflow_id,
        case_id=case_id,
        draft_type=draft_type,
        draft_content=content.strip(),
        created_by=actual_user
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to create draft workflow"))

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="DRAFT_CREATED",
        entity_type="draft",
        entity_id=workflow_id,
        case_id=case_id,
        after_state={"draft_type": draft_type, "status": "DRAFT"},
        ip_address=client_ip,
        note=f"Created {draft_type} draft ({workflow_id})"
    )

    return {
        "success": True,
        "workflow_id": workflow_id,
        "case_id": case_id,
        "draft_type": draft_type,
        "status": "DRAFT",
        "content": content.strip()
    }

@router.get("/cases/{case_id}/drafts")
def list_case_drafts(case_id: str):
    return DatabaseManager.cms_list_drafts(case_id=case_id)

@router.get("/drafts/{workflow_id}")
def get_draft_detail(workflow_id: str):
    wf = DatabaseManager.cms_get_draft_workflow(workflow_id=workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Draft workflow {workflow_id} not found")
    return wf

@router.put("/drafts/{workflow_id}")
def update_draft(
    workflow_id: str,
    payload: DraftUpdatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    wf = DatabaseManager.cms_get_draft_workflow(workflow_id=workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Draft workflow {workflow_id} not found")

    new_version = (wf.get("current_version") or 1) + 1
    updates = {
        "draft_content": payload.content,
        "current_version": new_version
    }
    if payload.assigned_reviewer:
        updates["assigned_reviewer"] = payload.assigned_reviewer

    DatabaseManager.cms_update_draft_workflow(workflow_id=workflow_id, updates=updates)

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="DRAFT_UPDATED",
        entity_type="draft",
        entity_id=workflow_id,
        case_id=wf.get("case_id"),
        after_state={"version": new_version},
        ip_address=client_ip,
        note=f"Updated draft {workflow_id} to v{new_version}"
    )

    return {"success": True, "workflow_id": workflow_id, "version": new_version}

@router.post("/drafts/{workflow_id}/submit")
def submit_draft_for_review(
    workflow_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    wf = DatabaseManager.cms_get_draft_workflow(workflow_id=workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Draft workflow {workflow_id} not found")

    DatabaseManager.cms_update_draft_workflow(workflow_id=workflow_id, updates={"status": "PENDING_APPROVAL"})

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="DRAFT_SUBMITTED",
        entity_type="draft",
        entity_id=workflow_id,
        case_id=wf.get("case_id"),
        before_state={"status": wf.get("status")},
        after_state={"status": "PENDING_APPROVAL"},
        ip_address=client_ip,
        note=f"Submitted draft {workflow_id} for review"
    )

    return {"success": True, "workflow_id": workflow_id, "status": "PENDING_APPROVAL"}

@router.post("/drafts/{workflow_id}/review")
def review_draft(
    workflow_id: str,
    payload: ReviewPayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    wf = DatabaseManager.cms_get_draft_workflow(workflow_id=workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Draft workflow {workflow_id} not found")

    existing_comments = wf.get("reviewer_comments") or []
    if isinstance(existing_comments, str):
        try:
            existing_comments = json.loads(existing_comments)
        except Exception:
            existing_comments = []

    comment_entry = {
        "user_id": actual_user,
        "comment": payload.comment,
        "status": payload.status,
        "timestamp": datetime.now().isoformat()
    }
    existing_comments.append(comment_entry)

    DatabaseManager.cms_update_draft_workflow(workflow_id=workflow_id, updates={
        "status": payload.status or "IN_REVISION",
        "reviewer_comments": existing_comments
    })

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="DRAFT_REVIEWED",
        entity_type="draft",
        entity_id=workflow_id,
        case_id=wf.get("case_id"),
        after_state={"status": payload.status, "comment": payload.comment},
        ip_address=client_ip,
        note=f"Reviewed draft {workflow_id}: {payload.comment[:40]}..."
    )

    return {"success": True, "workflow_id": workflow_id, "status": payload.status or "IN_REVISION"}

@router.post("/drafts/{workflow_id}/approve")
def approve_draft(
    workflow_id: str,
    payload: ApprovePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    wf = DatabaseManager.cms_get_draft_workflow(workflow_id=workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Draft workflow {workflow_id} not found")

    now_iso = datetime.now().isoformat()
    DatabaseManager.cms_update_draft_workflow(workflow_id=workflow_id, updates={
        "status": "APPROVED",
        "approved_by": actual_user,
        "approved_at": now_iso
    })

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="DRAFT_APPROVED",
        entity_type="draft",
        entity_id=workflow_id,
        case_id=wf.get("case_id"),
        after_state={"status": "APPROVED", "approved_by": actual_user},
        ip_address=client_ip,
        note=f"Approved draft {workflow_id}"
    )

    return {"success": True, "workflow_id": workflow_id, "status": "APPROVED", "approved_at": now_iso}

@router.post("/drafts/{workflow_id}/filed")
def mark_draft_filed(
    workflow_id: str,
    payload: FiledPayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    wf = DatabaseManager.cms_get_draft_workflow(workflow_id=workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Draft workflow {workflow_id} not found")

    now_iso = datetime.now().isoformat()
    DatabaseManager.cms_update_draft_workflow(workflow_id=workflow_id, updates={
        "status": "FILED",
        "filed_at": now_iso,
        "filed_reference": payload.filed_reference
    })

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="DRAFT_FILED",
        entity_type="draft",
        entity_id=workflow_id,
        case_id=wf.get("case_id"),
        after_state={"status": "FILED", "filed_reference": payload.filed_reference},
        ip_address=client_ip,
        note=f"Marked draft {workflow_id} as filed with ref: {payload.filed_reference}"
    )

    return {"success": True, "workflow_id": workflow_id, "status": "FILED", "filed_at": now_iso}

@router.get("/drafts/{workflow_id}/export/{format}")
def export_draft(
    workflow_id: str,
    format: str,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    wf = DatabaseManager.cms_get_draft_workflow(workflow_id=workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Draft workflow {workflow_id} not found")

    title = f"{wf.get('draft_type')}_{workflow_id}"
    content = wf.get("draft_content") or ""
    metadata = {
        "case_id": wf.get("case_id"),
        "status": wf.get("status"),
        "version": wf.get("current_version")
    }

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=user_id or "ANONYMOUS",
        action="DRAFT_EXPORTED",
        entity_type="draft",
        entity_id=workflow_id,
        case_id=wf.get("case_id"),
        ip_address=client_ip,
        note=f"Exported draft {workflow_id} as {format.upper()}"
    )

    if format.lower() == "pdf":
        pdf_bytes = PDFGenerator.generate_draft_pdf(title, content, metadata)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="JUDIQ_{title}.pdf"'}
        )
    elif format.lower() in ("word", "docx"):
        docx_bytes = WordGenerator.generate_draft_word(title, content, metadata)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="JUDIQ_{title}.docx"'}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'docx'")
