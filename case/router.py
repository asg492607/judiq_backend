from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import os
import shutil
from session import DatabaseManager
from auth.utils import get_current_user
from ai.processor import process_document_async

router = APIRouter(tags=["case"])

# Utility to log activities
def log_activity(cursor, case_id: str, user_id: str, action: str, description: str):
    cursor.execute(
        "INSERT INTO case_activities (case_id, user_id, action, description, created_at) VALUES (?, ?, ?, ?, ?)",
        (case_id, user_id, action, description, datetime.utcnow().isoformat())
    )

class RegisterCaseRequest(BaseModel):
    customer_name: str
    account_number: str
    cheque_number: str
    cheque_amount: float
    litigation_type: str = 'CHEQUE_BOUNCE'
    priority: str = 'MEDIUM'

class UpdateStageRequest(BaseModel):
    workflow_stage: str

@router.post("/")
async def create_case(req: RegisterCaseRequest, current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        user_id = current_user.get("sub")
        org_id = current_user.get("org_id")
        
        cursor.execute(
            """INSERT INTO saved_cases (
                case_id, user_id, organization_id, litigation_type, workflow_stage, 
                customer_name, account_number, cheque_number, cheque_amount, priority, case_health, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (case_id, user_id, org_id, req.litigation_type, 'REGISTERED', 
             req.customer_name, req.account_number, req.cheque_number, req.cheque_amount, req.priority, 'HEALTHY', datetime.utcnow().isoformat())
        )
        
        log_activity(cursor, case_id, user_id, "CASE_REGISTERED", f"Case registered with priority {req.priority}")
        
        conn.commit()
        return {"status": "success", "case_id": case_id}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.get("/{case_id}")
async def get_case(case_id: str, current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        org_id = current_user.get("org_id")
        
        cursor.execute("""
            SELECT case_id, litigation_type, workflow_stage, customer_name, account_number, 
                   cheque_number, cheque_amount, priority, case_health, litigation_cost, 
                   recovered_amount, outstanding_amount, filing_date, next_hearing_date, created_at,
                   analysis_result, score
            FROM saved_cases 
            WHERE case_id = ? AND organization_id = ?
        """, (case_id, org_id))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Case not found or access denied")
            
        return {
            "status": "success",
            "data": {
                "case_id": row[0],
                "litigation_type": row[1],
                "workflow_stage": row[2],
                "customer_name": row[3],
                "account_number": row[4],
                "cheque_number": row[5],
                "cheque_amount": row[6],
                "priority": row[7],
                "case_health": row[8],
                "litigation_cost": row[9],
                "recovered_amount": row[10],
                "outstanding_amount": row[11],
                "filing_date": row[12],
                "next_hearing_date": row[13],
                "created_at": row[14],
                "analysis_result": row[15],
                "score": row[16]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

import csv
import io

# Workflow Rules Definition
ALLOWED_TRANSITIONS = {
    "REGISTERED": ["DOCUMENT_VERIFICATION"],
    "DOCUMENT_VERIFICATION": ["NOTICE_SENT"],
    "NOTICE_SENT": ["NOTICE_SERVED", "COMPLAINT_FILED"],
    "NOTICE_SERVED": ["COMPLAINT_FILED"],
    "COMPLAINT_FILED": ["HEARING"],
    "HEARING": ["JUDGMENT", "HEARING", "RECOVERY", "CLOSED"],
    "JUDGMENT": ["RECOVERY", "CLOSED"],
    "RECOVERY": ["CLOSED"],
    "CLOSED": []
}

PRECONDITIONS = {
    "NOTICE_SENT": ["CHEQUE", "RETURN_MEMO"],
    "COMPLAINT_FILED": ["LEGAL_NOTICE", "POSTAL_RECEIPT"]
}

@router.get("/workflow-rules")
async def get_workflow_rules():
    return {"status": "success", "data": ALLOWED_TRANSITIONS}

@router.patch("/{case_id}/stage")
async def update_stage(case_id: str, req: UpdateStageRequest, current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        org_id = current_user.get("org_id")
        user_id = current_user.get("sub")
        
        # 1. Fetch current stage to validate workflow rule
        cursor.execute("SELECT workflow_stage FROM saved_cases WHERE case_id = ? AND organization_id = ?", (case_id, org_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Case not found or access denied")
            
        current_stage = row[0]
        allowed_next = ALLOWED_TRANSITIONS.get(current_stage, [])
        
        if req.workflow_stage not in allowed_next:
            raise HTTPException(status_code=400, detail=f"Invalid transition. Cannot move from {current_stage} to {req.workflow_stage}.")
        
        # 2. Check Preconditions
        req_docs = PRECONDITIONS.get(req.workflow_stage, [])
        if req_docs:
            cursor.execute("SELECT document_type FROM case_documents WHERE case_id = ?", (case_id,))
            uploaded_docs = [r[0] for r in cursor.fetchall()]
            missing_docs = [d for d in req_docs if d not in uploaded_docs]
            if missing_docs:
                raise HTTPException(status_code=400, detail=f"Cannot advance to {req.workflow_stage}. Missing mandatory documents: {', '.join(missing_docs)}")
        
        # 3. Update stage
        cursor.execute(
            "UPDATE saved_cases SET workflow_stage = ?, updated_at = ? WHERE case_id = ? AND organization_id = ?",
            (req.workflow_stage, datetime.utcnow().isoformat(), case_id, org_id)
        )
            
        log_activity(cursor, case_id, user_id, "STAGE_ADVANCED", f"Workflow stage updated to {req.workflow_stage}")
        
        conn.commit()
        return {"status": "success", "message": f"Case advanced to {req.workflow_stage}"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/bulk-import")
async def bulk_import_cases(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported for bulk import.")
            
        org_id = current_user.get("org_id")
        user_id = current_user.get("sub")
        
        content = await file.read()
        text = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        success_count = 0
        failed_rows = []
        now = datetime.utcnow().isoformat()
        
        for idx, row in enumerate(reader):
            try:
                c_name = row.get("Customer Name")
                acc_num = row.get("Account Number")
                chq_num = row.get("Cheque Number")
                try:
                    chq_amt = float(row.get("Cheque Amount", 0))
                except ValueError:
                    failed_rows.append({"row": idx+2, "reason": "Invalid Cheque Amount"})
                    continue
                    
                if not all([c_name, acc_num, chq_num, chq_amt]):
                    failed_rows.append({"row": idx+2, "reason": "Missing mandatory fields"})
                    continue
                    
                case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
                
                cursor.execute(
                    """INSERT INTO saved_cases (
                        case_id, user_id, organization_id, litigation_type, workflow_stage, 
                        customer_name, account_number, cheque_number, cheque_amount, priority, case_health, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (case_id, user_id, org_id, 'CHEQUE_BOUNCE', 'REGISTERED', 
                     c_name, acc_num, chq_num, chq_amt, 'MEDIUM', 'HEALTHY', now)
                )
                
                log_activity(cursor, case_id, user_id, "CASE_REGISTERED", "Case registered via Bulk Import")
                success_count += 1
            except Exception as e:
                failed_rows.append({"row": idx+2, "reason": str(e)})
                
        conn.commit()
        return {
            "status": "success", 
            "message": "Bulk import completed", 
            "data": {
                "successful": success_count,
                "failed": len(failed_rows),
                "failures": failed_rows
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/{case_id}/document")
async def upload_document(
    case_id: str, 
    background_tasks: BackgroundTasks,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    conn = None
    try:
        org_id = current_user.get("org_id")
        user_id = current_user.get("sub")
        
        # Verify case ownership
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM saved_cases WHERE case_id = ? AND organization_id = ?", (case_id, org_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Case not found or access denied")

        # Save file locally for MVP
        upload_dir = f"uploads/{org_id}/{case_id}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = f"{upload_dir}/{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Insert DB Record
        cursor.execute(
            """INSERT INTO case_documents (case_id, uploader_id, document_type, file_path, uploaded_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (case_id, user_id, document_type, file_path, datetime.utcnow().isoformat())
        )
        
        log_activity(cursor, case_id, user_id, "DOCUMENT_UPLOADED", f"Uploaded {document_type}: {file.filename}")
        
        # Update case to show AI is processing
        cursor.execute("UPDATE saved_cases SET ai_status = 'PROCESSING' WHERE case_id = ? AND organization_id = ?", (case_id, org_id))
        
        conn.commit()
        
        # Trigger background AI task
        background_tasks.add_task(process_document_async, case_id, file_path, document_type, user_id, org_id)
        
        return {"status": "success", "message": "Document uploaded and AI extraction started"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.get("/{case_id}/documents")
async def get_documents(case_id: str, current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        org_id = current_user.get("org_id")
        
        # Security check implicit by joining saved_cases
        cursor.execute("""
            SELECT cd.id, cd.document_type, cd.file_path, cd.status, cd.uploaded_at 
            FROM case_documents cd
            JOIN saved_cases sc ON cd.case_id = sc.case_id
            WHERE sc.case_id = ? AND sc.organization_id = ?
            ORDER BY cd.uploaded_at DESC
        """, (case_id, org_id))
        
        docs = [{"id": r[0], "type": r[1], "file_name": os.path.basename(r[2]), "status": r[3], "uploaded_at": r[4]} for r in cursor.fetchall()]
        return {"status": "success", "data": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.get("/{case_id}/timeline")
async def get_timeline(case_id: str, current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        org_id = current_user.get("org_id")
        
        cursor.execute("""
            SELECT ca.action, ca.description, ca.created_at, u.first_name, u.last_name
            FROM case_activities ca
            JOIN saved_cases sc ON ca.case_id = sc.case_id
            LEFT JOIN users u ON ca.user_id = u.id
            WHERE sc.case_id = ? AND sc.organization_id = ?
            ORDER BY ca.created_at DESC
        """, (case_id, org_id))
        
        timeline = [{
            "action": r[0], 
            "description": r[1], 
            "created_at": r[2], 
            "user": f"{r[3]} {r[4]}" if r[3] else "System"
        } for r in cursor.fetchall()]
        return {"status": "success", "data": timeline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.get("/organization/all")
async def get_org_cases(current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        org_id = current_user.get("org_id")
        
        cursor.execute("""
            SELECT case_id, customer_name, cheque_amount, workflow_stage, next_hearing_date, priority, case_health, created_at
            FROM saved_cases 
            WHERE organization_id = ?
            ORDER BY created_at DESC
        """, (org_id,))
        
        cases = []
        for row in cursor.fetchall():
            cases.append({
                "case_id": row[0],
                "customer_name": row[1] or "Unknown",
                "cheque_amount": row[2] or 0.0,
                "workflow_stage": row[3],
                "next_hearing_date": row[4] or "Unscheduled",
                "priority": row[5],
                "case_health": row[6],
                "created_at": row[7]
            })
            
        return {"status": "success", "data": cases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()
