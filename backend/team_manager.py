import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Request, Depends
from pydantic import BaseModel
from session import DatabaseManager
from security import get_current_user_optional
from audit_service import AuditService

router = APIRouter()

class TeamMemberCreatePayload(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    role: Optional[str] = "officer"  # 'admin', 'lead_counsel', 'associate', 'officer', 'paralegal'
    department: Optional[str] = "Litigation"
    supervisor_id: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = {}
    org_id: Optional[str] = "default_org"

class TeamMemberUpdatePayload(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    supervisor_id: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None

class ToggleStatusPayload(BaseModel):
    is_active: bool

@router.post("/team/members")
def add_team_member(
    payload: TeamMemberCreatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    member_id = f"MEM-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
    member_user_id = f"usr_{uuid.uuid4().hex[:8]}"

    res = DatabaseManager.cms_add_team_member(
        member_id=member_id,
        org_id=payload.org_id or "default_org",
        user_id=member_user_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role or "officer",
        department=payload.department,
        supervisor_id=payload.supervisor_id,
        permissions=payload.permissions or {}
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to add team member"))

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="TEAM_MEMBER_ADDED",
        entity_type="team_member",
        entity_id=member_id,
        after_state={"name": payload.name, "role": payload.role, "email": payload.email},
        ip_address=client_ip,
        note=f"Added team member {payload.name} ({payload.role})"
    )

    return {"success": True, "member_id": member_id, "name": payload.name}

@router.get("/team/members")
def list_team_members(org_id: Optional[str] = Query(None)):
    return DatabaseManager.cms_list_team_members(org_id=org_id)

@router.put("/team/members/{member_id}")
def update_team_member(
    member_id: str,
    payload: TeamMemberUpdatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    res = DatabaseManager.cms_update_team_member(member_id=member_id, updates=updates)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to update team member"))

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="TEAM_MEMBER_UPDATED",
        entity_type="team_member",
        entity_id=member_id,
        after_state=updates,
        ip_address=client_ip,
        note=f"Updated team member {member_id}"
    )

    return {"success": True, "member_id": member_id}

@router.patch("/team/members/{member_id}/status")
def toggle_member_status(
    member_id: str,
    payload: ToggleStatusPayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    DatabaseManager.cms_update_team_member(member_id=member_id, updates={"is_active": 1 if payload.is_active else 0})

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="TEAM_MEMBER_STATUS_TOGGLED",
        entity_type="team_member",
        entity_id=member_id,
        after_state={"is_active": payload.is_active},
        ip_address=client_ip,
        note=f"Set team member {member_id} active={payload.is_active}"
    )

    return {"success": True, "member_id": member_id, "is_active": payload.is_active}
