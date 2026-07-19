from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import uuid
from datetime import datetime
from session import DatabaseManager
from auth.utils import get_current_user

router = APIRouter(tags=["auth"])

class RegisterSyncRequest(BaseModel):
    first_name: str
    last_name: str
    organization_name: str
    organization_type: str

class LoginSyncRequest(BaseModel):
    expected_org_type: str = None  # e.g., 'FINANCIAL_INSTITUTION' for enterprise portal

@router.post("/register-sync")
async def register_sync(req: RegisterSyncRequest, current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        user_id = current_user.get("uid")
        email = current_user.get("email")
        if not user_id or not email:
            raise HTTPException(status_code=400, detail="Invalid Firebase token payload")

        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User already synced")

        # Create Organization
        cursor.execute(
            "INSERT INTO organizations (name, type, created_at) VALUES (?, ?, ?)",
            (req.organization_name, req.organization_type, datetime.utcnow().isoformat())
        )
        org_id = cursor.lastrowid
        
        # Create User
        # Using dummy password hash since Firebase handles auth
        cursor.execute(
            "INSERT INTO users (id, email, password_hash, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email, "FIREBASE_MANAGED", req.first_name, req.last_name, datetime.utcnow().isoformat())
        )
        
        # Create User Workspace (Super Admin for this org)
        cursor.execute(
            "INSERT INTO user_workspaces (user_id, org_id, role) VALUES (?, ?, ?)",
            (user_id, org_id, "SUPER_ADMIN")
        )
        
        conn.commit()
        return {"status": "success", "user_id": user_id, "org_id": org_id, "org_type": req.organization_type}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.post("/login-sync")
async def login_sync(req: LoginSyncRequest, current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        user_id = current_user.get("uid")
        email = current_user.get("email")
        
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        # Fetch user
        cursor.execute("SELECT id, email, first_name, last_name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not synced with backend. Please register first.")
            
        # Fetch workspace context
        cursor.execute("""
            SELECT uw.org_id, uw.role, o.type, o.name
            FROM user_workspaces uw
            JOIN organizations o ON uw.org_id = o.id
            WHERE uw.user_id = ?
        """, (user_id,))
        workspace = cursor.fetchone()
        
        if not workspace:
            raise HTTPException(status_code=403, detail="No workspace assigned")
            
        org_id, role, org_type, org_name = workspace
        
        # Role-Based Access Control / Portal Separation
        if req.expected_org_type:
            if req.expected_org_type == 'FINANCIAL_INSTITUTION' and org_type != 'FINANCIAL_INSTITUTION':
                raise HTTPException(status_code=403, detail="Unauthorized: Standard users cannot access Enterprise portal.")
            if req.expected_org_type == 'STANDARD' and org_type == 'FINANCIAL_INSTITUTION':
                raise HTTPException(status_code=403, detail="Unauthorized: Enterprise users must use the Enterprise portal.")

        # Determine redirect path based on organization_type
        redirect_url = "/advocate/dashboard.html"
        if org_type == "FINANCIAL_INSTITUTION":
            redirect_url = "/enterprise/dashboard.html"
        elif org_type == "LEGAL_PRACTICE":
            redirect_url = "/lawfirm/dashboard.html"
            
        return {
            "status": "success",
            "redirect": redirect_url,
            "user": {
                "id": user[0],
                "email": user[1],
                "first_name": user[2],
                "last_name": user[3]
            },
            "workspace": {
                "org_id": org_id,
                "org_name": org_name,
                "org_type": org_type,
                "role": role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"status": "success", "user": current_user}
