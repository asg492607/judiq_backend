import os
import uuid
import hashlib
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from cryptography.fernet import Fernet
from config import settings
from session import DatabaseManager
from security import get_current_user_optional
from audit_service import AuditService
from ocr_engine import OCREngine
from document_intelligence import DocumentIntelligence

router = APIRouter()

try:
    _raw_key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
    fernet = Fernet(_raw_key)
except Exception as e:
    raise RuntimeError(f"FATAL: ENCRYPTION_KEY is invalid or missing: {e}")

class S65BCertifyPayload(BaseModel):
    certifier_name: str
    certifier_designation: str
    device_description: Optional[str] = "Office Desktop / Official Scanner"
    hash_verified: Optional[bool] = True

@router.post("/cases/{case_id}/documents")
async def upload_document(
    case_id: str,
    request: Request,
    file: UploadFile = File(...),
    doc_type: str = Form("other"),
    notes: Optional[str] = Form(""),
    tags: Optional[str] = Form(""),
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    case = DatabaseManager.cms_get_case(case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    ALLOWED_MIMES = {
        "application/pdf", "image/jpeg", "image/png", "image/webp",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    }
    if file.content_type and file.content_type not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Compute SHA-256 hash before encryption
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Save to storage directory
    upload_dir = os.path.join(os.getcwd(), "uploads", "cms", case_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    doc_id = f"DOC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    safe_filename = os.path.basename(file.filename)
    stored_filename = f"{doc_id}_{safe_filename}"
    file_path = os.path.join(upload_dir, stored_filename)

    # Encrypt
    encrypted_bytes = fernet.encrypt(content)
    with open(file_path, "wb") as f:
        f.write(encrypted_bytes)

    # OCR text extraction if image/pdf
    extracted_text = ""
    extracted_data = {}
    try:
        # In a real environment with tesseract/pdfminer, we'd extract text:
        # For now, pass to DocumentIntelligence if it looks like memo or notice
        if "memo" in doc_type.lower() or "cheque" in doc_type.lower():
            extracted_data = DocumentIntelligence.extract_memo_data(safe_filename)
        elif "notice" in doc_type.lower():
            extracted_data = DocumentIntelligence.extract_notice_data(safe_filename)
    except Exception:
        pass

    # Save document record in DB
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    res = DatabaseManager.cms_save_document(
        document_id=doc_id,
        case_id=case_id,
        uploader_id=actual_user,
        file_name=safe_filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        doc_type=doc_type,
        encryption_hash=sha256_hash,
        ocr_text=extracted_text,
        extracted_data=extracted_data,
        tags=tag_list,
        notes=notes
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Failed to save document metadata"))

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    AuditService.log(
        user_id=actual_user,
        action="DOCUMENT_UPLOADED",
        entity_type="document",
        entity_id=doc_id,
        case_id=case_id,
        after_state={"file_name": safe_filename, "doc_type": doc_type, "sha256": sha256_hash},
        ip_address=client_ip,
        user_agent=user_agent,
        note=f"Uploaded {safe_filename} ({doc_type}) with SHA-256: {sha256_hash[:12]}..."
    )

    return {
        "success": True,
        "document_id": doc_id,
        "file_name": safe_filename,
        "doc_type": doc_type,
        "file_size": len(content),
        "encryption_hash": sha256_hash,
        "extracted_data": extracted_data
    }

@router.get("/cases/{case_id}/documents")
def list_case_documents(case_id: str):
    return DatabaseManager.cms_list_documents(case_id=case_id)

@router.get("/documents/{document_id}")
def get_document_detail(document_id: str):
    doc = DatabaseManager.cms_get_document(document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    # Hide server file_path for security
    doc.pop("file_path", None)
    return doc

@router.get("/documents/{document_id}/download")
def download_document(
    document_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    doc = DatabaseManager.cms_get_document(document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    file_path = doc.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Underlying file not found on disk")

    try:
        with open(file_path, "rb") as f:
            encrypted_bytes = f.read()
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        
        client_ip = request.client.host if request.client else None
        AuditService.log(
            user_id=user_id or "ANONYMOUS",
            action="DOCUMENT_DOWNLOADED",
            entity_type="document",
            entity_id=document_id,
            case_id=doc.get("case_id"),
            ip_address=client_ip,
            note=f"Downloaded document {doc.get('file_name')}"
        )

        return Response(
            content=decrypted_bytes,
            media_type=doc.get("mime_type") or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{doc.get("file_name")}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decrypt document: {e}")

@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    doc = DatabaseManager.cms_get_document(document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    DatabaseManager.cms_delete_document(document_id=document_id)

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="DOCUMENT_DELETED",
        entity_type="document",
        entity_id=document_id,
        case_id=doc.get("case_id"),
        ip_address=client_ip,
        note=f"Deleted document {doc.get('file_name')}"
    )

    return {"success": True, "document_id": document_id}

@router.post("/documents/{document_id}/s65b")
def generate_s65b_certificate_template(document_id: str):
    doc = DatabaseManager.cms_get_document(document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    cert_text = f"""
CERTIFICATE UNDER SECTION 65B OF THE INDIAN EVIDENCE ACT, 1872
(Corresponding to Section 63 of Bharatiya Sakshya Adhiniyam, 2023)

I, [Name of Certifier], [Designation], hereby certify as follows:

1. That I am the authorized custodian / handler of the computer system / electronic device on which the document titled "{doc.get('file_name')}" was produced / received in the ordinary course of business.

2. That the computer system was operating properly during the relevant period, and that the electronic record contained in SHA-256 Hash:
   {doc.get('encryption_hash')}
   has not been tampered with or altered in any manner.

3. That the output reproduced herein is a true and faithful copy of the electronic record.

Date: {datetime.now().strftime('%d-%b-%Y')}
Place: [City / Jurisdiction]

Signature: __________________________
Name: [Name of Certifier]
Designation: [Designation]
"""
    return {
        "success": True,
        "document_id": document_id,
        "file_name": doc.get("file_name"),
        "sha256_hash": doc.get("encryption_hash"),
        "certificate_template": cert_text.strip()
    }

@router.post("/documents/{document_id}/certify")
def certify_document(
    document_id: str,
    payload: S65BCertifyPayload,
    request: Request,
    user_id: str = Depends(get_current_user_optional)
):
    actual_user = user_id or "ANONYMOUS"
    doc = DatabaseManager.cms_get_document(document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    cert_data = {
        "certifier_name": payload.certifier_name,
        "certifier_designation": payload.certifier_designation,
        "device_description": payload.device_description,
        "certified_at": datetime.now().isoformat(),
        "certified_by_user": actual_user,
        "hash_verified": payload.hash_verified,
        "sha256_hash": doc.get("encryption_hash")
    }

    DatabaseManager.cms_update_document(document_id=document_id, updates={
        "s65b_status": "certified",
        "s65b_cert_data": cert_data
    })

    client_ip = request.client.host if request.client else None
    AuditService.log(
        user_id=actual_user,
        action="DOCUMENT_CERTIFIED_S65B",
        entity_type="document",
        entity_id=document_id,
        case_id=doc.get("case_id"),
        after_state=cert_data,
        ip_address=client_ip,
        note=f"Certified {doc.get('file_name')} under S.65B by {payload.certifier_name}"
    )

    return {"success": True, "document_id": document_id, "s65b_status": "certified", "cert_data": cert_data}
