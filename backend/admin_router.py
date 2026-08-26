import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from pydantic import BaseModel, Field
from security import require_admin, get_current_user, get_current_user_optional, is_admin_user, SecurityManager
from session import DatabaseManager

logger = logging.getLogger("JudiQ.Admin")
router = APIRouter()

class QuotaAllocationRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")
    monthly_limit: int = Field(..., description="Monthly report quota limit (-1 for unlimited)")
    role: Optional[str] = Field(None, description="Optional role/plan designation")
    email: Optional[str] = Field(None, description="User email address")

class UserStatusToggleRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")
    is_active: bool = Field(..., description="Active status flag")

class ResetUsageRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")

class AdminAuthRequest(BaseModel):
    email: str = Field(..., description="Admin Email Address")
    admin_secret: Optional[str] = Field(None, description="Optional Admin Access Key")

@router.post("/auth/verify", tags=["Admin Control"])
def verify_admin_status(payload: AdminAuthRequest = Body(...)):
    """
    Checks if an email/user has administrative privileges and issues an authorized admin token.
    """
    email = payload.email.strip().lower()
    if is_admin_user(email, email):
        token = SecurityManager.create_access_token(data={"sub": email, "email": email, "role": "admin"})
        return {
            "success": True,
            "is_admin": True,
            "token": token,
            "email": email,
            "role": "admin"
        }
    return {
        "success": False,
        "is_admin": False,
        "message": "User does not have administrative privileges."
    }

@router.get("/stats", tags=["Admin Control"])
def get_admin_stats(admin: dict = Depends(require_admin)):
    """
    Returns platform-wide metrics: Total Users, Active Users, Monthly Reports Generated, Cases.
    """
    stats = DatabaseManager.get_platform_admin_stats()
    return {"success": True, "stats": stats, "admin_user": admin["email"]}

@router.get("/users", tags=["Admin Control"])
def get_admin_users(admin: dict = Depends(require_admin)):
    """
    Returns all registered litigators, monthly quota allocations, usage progress, and account status.
    """
    users = DatabaseManager.get_all_users_quotas()
    return {"success": True, "users": users, "total": len(users)}

@router.post("/users/allocate", tags=["Admin Control"])
def allocate_user_quota(req: QuotaAllocationRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Updates the monthly report allocation limit and role for a user.
    """
    success = DatabaseManager.update_user_quota_allocation(
        user_id=req.user_id,
        monthly_limit=req.monthly_limit,
        role=req.role,
        email=req.email
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user quota allocation.")
    
    updated_quota = DatabaseManager.get_or_create_user_quota(req.user_id, req.email or "")
    logger.info(f"[ADMIN] Admin {admin.get('email')} updated quota for {req.user_id} to {req.monthly_limit}")
    return {"success": True, "quota": updated_quota, "message": f"Successfully set monthly limit to {req.monthly_limit} reports."}

@router.post("/users/reset-usage", tags=["Admin Control"])
def reset_user_usage(req: ResetUsageRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Resets a user's monthly report usage counter back to 0.
    """
    success = DatabaseManager.reset_user_monthly_usage(req.user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset user usage counter.")
    
    updated_quota = DatabaseManager.get_or_create_user_quota(req.user_id)
    logger.info(f"[ADMIN] Admin {admin.get('email')} reset monthly usage for {req.user_id}")
    return {"success": True, "quota": updated_quota, "message": "User monthly usage counter reset to 0."}

@router.post("/users/toggle-status", tags=["Admin Control"])
def toggle_user_status(req: UserStatusToggleRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Activates or suspends a litigator's platform access.
    """
    success = DatabaseManager.update_user_quota_allocation(
        user_id=req.user_id,
        is_active=req.is_active
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user status.")
    
    status_str = "ACTIVE" if req.is_active else "SUSPENDED"
    logger.info(f"[ADMIN] Admin {admin.get('email')} changed status of {req.user_id} to {status_str}")
    return {"success": True, "is_active": req.is_active, "message": f"User status set to {status_str}."}

user_quota_router = APIRouter()

@user_quota_router.get("/quota", tags=["User Quota"])
def get_user_quota_endpoint(user_id: str = Query(None), email: str = Query(None)):
    """
    Returns monthly report quota and remaining allowance for the specified user or current user.
    """
    effective_id = user_id or "demo_user_123"
    effective_email = email or ""
    quota = DatabaseManager.get_or_create_user_quota(effective_id, effective_email)
    return {"success": True, "quota": quota}
