import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Request, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from session import DatabaseManager
from security import get_current_user_optional
from audit_service import AuditService
import csv
import io

router = APIRouter()

class CaseNotifyPayload(BaseModel):
    subject: str
    message: str
    channels: Optional[List[str]] = ["email"]
    recipient_emails: Optional[List[str]] = None

@router.post("/cases/{case_id}/notify")
def send_case_notification(
    case_id: str,
    payload: CaseNotifyPayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    case = DatabaseManager.cms_get_case(case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    recipients = payload.recipient_emails or []
    if not recipients and case.get("linked_clients"):
        for cl in case.get("linked_clients", []):
            if cl.get("email"):
                recipients.append(cl.get("email"))

    # Log communication in audit trail
    comm_id = f"COM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="CLIENT_NOTIFICATION_SENT",
        entity_type="communication",
        entity_id=comm_id,
        case_id=case_id,
        after_state={
            "subject": payload.subject,
            "recipients": recipients,
            "channels": payload.channels
        },
        ip_address=client_ip,
        note=f"Sent notification '{payload.subject}' to {len(recipients)} recipients via {', '.join(payload.channels)}"
    )

    return {
        "success": True,
        "comm_id": comm_id,
        "case_id": case_id,
        "recipients_count": len(recipients),
        "channels": payload.channels,
        "status": "DISPATCHED"
    }

@router.get("/cases/{case_id}/communications")
def get_case_communications(case_id: str):
    all_trails = AuditService.get_case_trail(case_id=case_id, limit=50)
    comm_logs = [t for t in all_trails if "NOTIFICATION" in t.get("action", "") or "COMM" in t.get("action", "")]
    return {"case_id": case_id, "communications": comm_logs}

@router.get("/audit/case/{case_id}")
def get_case_audit_trail(case_id: str):
    return AuditService.get_case_trail(case_id=case_id, limit=100)

@router.get("/audit/export")
def export_audit_trail(
    case_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    logs = DatabaseManager.cms_get_audit_trail(case_id=case_id, user_id=user_id, limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log ID", "Timestamp", "User ID", "Case ID", "Action", "Entity Type", "Entity ID", "Note"])
    for l in logs:
        writer.writerow([
            l.get("log_id"), l.get("timestamp"), l.get("user_id"),
            l.get("case_id") or "", l.get("action"), l.get("entity_type") or "",
            l.get("entity_id") or "", l.get("note") or ""
        ])
    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="judiq_audit_trail.csv"'}
    )
