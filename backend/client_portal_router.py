"""
JudiQ Client Portal API Router
Exposes client-facing status updates, document checklists, and upload verification endpoints.
"""

from fastapi import APIRouter, HTTPException, Path, Body
from typing import Optional, Dict, Any
from pydantic import BaseModel

from client_portal import ClientPortalService, ClientCaseDossier

router = APIRouter()


class DocumentUploadPayload(BaseModel):
    document_id: str
    file_name: str


@router.get("/case/{token}", response_model=ClientCaseDossier, tags=["Client Portal"])
def get_client_case_dossier_endpoint(token: str = Path(..., description="Unique client access token")):
    """
    Retrieves client-facing case dossier with milestones, hearing schedules, and document checklists.
    """
    dossier = ClientPortalService.get_dossier_by_token(token)
    if not dossier:
        raise HTTPException(status_code=404, detail="Invalid client access token or case not found.")
    return dossier


@router.post("/case/{token}/upload-document", response_model=Dict[str, Any], tags=["Client Portal"])
def upload_client_document_endpoint(
    token: str = Path(..., description="Unique client access token"),
    payload: DocumentUploadPayload = Body(...)
):
    """
    Records a client document upload against the case checklist.
    """
    try:
        return ClientPortalService.record_client_document_upload(
            token=token,
            document_id=payload.document_id,
            file_name=payload.file_name
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
