import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Request, Depends
from pydantic import BaseModel
from session import DatabaseManager
from security import get_current_user_optional
from audit_service import AuditService

router = APIRouter()

class ClientCreatePayload(BaseModel):
    name: str
    client_type: str  # 'bank', 'nbfc', 'individual', 'company'
    role_type: Optional[str] = "creditor"
    legal_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company_info: Optional[Dict[str, Any]] = {}
    address_data: Optional[Dict[str, Any]] = {}
    tax_info: Optional[Dict[str, Any]] = {}
    banking_info: Optional[Dict[str, Any]] = {}
    comm_prefs: Optional[Dict[str, Any]] = {}
    notes: Optional[str] = None
    org_id: Optional[str] = None

class ClientUpdatePayload(BaseModel):
    name: Optional[str] = None
    client_type: Optional[str] = None
    role_type: Optional[str] = None
    legal_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company_info: Optional[Dict[str, Any]] = None
    address_data: Optional[Dict[str, Any]] = None
    tax_info: Optional[Dict[str, Any]] = None
    banking_info: Optional[Dict[str, Any]] = None
    comm_prefs: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class LinkClientPayload(BaseModel):
    client_id: str
    role: str = "creditor"

@router.post("/clients")
def create_client(
    payload: ClientCreatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    now = datetime.now()
    client_id = f"CLT-{now.strftime('%Y')}-{uuid.uuid4().hex[:4].upper()}"

    res = DatabaseManager.cms_create_client(
        client_id=client_id,
        user_id=actual_user,
        name=payload.name,
        client_type=payload.client_type,
        role_type=payload.role_type or "creditor",
        legal_name=payload.legal_name,
        email=payload.email,
        phone=payload.phone,
        mobile=payload.mobile,
        company_info=payload.company_info or {},
        address_data=payload.address_data or {},
        tax_info=payload.tax_info or {},
        banking_info=payload.banking_info or {},
        comm_prefs=payload.comm_prefs or {},
        notes=payload.notes,
        org_id=payload.org_id
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to create client"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="CLIENT_CREATED",
        entity_type="client",
        entity_id=client_id,
        after_state={"name": payload.name, "client_type": payload.client_type},
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Created client {client_id}: {payload.name}"
    )

    return {
        "success": True,
        "client_id": client_id,
        "name": payload.name,
        "created_at": res.get("created_at")
    }

@router.get("/clients")
def list_clients(
    search: Optional[str] = Query(""),
    client_type: Optional[str] = Query("all"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_optional)
):
    return DatabaseManager.cms_list_clients(
        user_id=user_id,
        search=search,
        client_type=client_type,
        page=page,
        limit=limit
    )

@router.get("/clients/{client_id}")
def get_client_detail(client_id: str):
    client = DatabaseManager.cms_get_client(client_id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client

@router.put("/clients/{client_id}")
def update_client(
    client_id: str,
    payload: ClientUpdatePayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    before = DatabaseManager.cms_get_client(client_id=client_id)
    if not before:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    updates = {k: v for k, v in payload.dict().items() if v is not None}
    res = DatabaseManager.cms_update_client(client_id=client_id, updates=updates)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to update client"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="CLIENT_UPDATED",
        entity_type="client",
        entity_id=client_id,
        after_state=updates,
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Updated client {client_id}"
    )

    return {"success": True, "client_id": client_id}

@router.post("/cases/{case_id}/link-client")
def link_client_to_case(
    case_id: str,
    payload: LinkClientPayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    res = DatabaseManager.cms_link_client(
        case_id=case_id,
        client_id=payload.client_id,
        role=payload.role,
        linked_by=actual_user
    )
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to link client"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="CLIENT_LINKED",
        entity_type="case_client",
        entity_id=f"{case_id}:{payload.client_id}",
        case_id=case_id,
        after_state={"client_id": payload.client_id, "role": payload.role},
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Linked client {payload.client_id} to case {case_id} as {payload.role}"
    )

    return {"success": True, "case_id": case_id, "client_id": payload.client_id, "role": payload.role}

@router.delete("/cases/{case_id}/unlink-client/{client_id}")
def unlink_client_from_case(
    case_id: str,
    client_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    res = DatabaseManager.cms_unlink_client(case_id=case_id, client_id=client_id)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to unlink client"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="CLIENT_UNLINKED",
        entity_type="case_client",
        entity_id=f"{case_id}:{client_id}",
        case_id=case_id,
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Unlinked client {client_id} from case {case_id}"
    )

    return {"success": True, "case_id": case_id, "client_id": client_id}
