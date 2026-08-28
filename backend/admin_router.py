import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from pydantic import BaseModel, Field
from security import require_admin, get_current_user, get_current_user_optional, is_admin_user, verify_admin_credentials, SecurityManager
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
    email: str = Field(..., description="Admin Email Address / Username")
    password: Optional[str] = Field(None, description="Admin Password")
    admin_secret: Optional[str] = Field(None, description="Optional Admin Access Key / Secret")

@router.post("/auth/verify", tags=["Admin Control"])
def verify_admin_status(payload: AdminAuthRequest = Body(...)):
    """
    Verifies admin credentials (email/username and password/secret) and issues an authorized admin JWT token.
    """
    email = payload.email.strip().lower()
    provided_password = payload.password or payload.admin_secret or ""

    if not is_admin_user(email, email):
        return {
            "success": False,
            "is_admin": False,
            "message": "User does not have administrative privileges."
        }

    if not verify_admin_credentials(email, provided_password):
        return {
            "success": False,
            "is_admin": False,
            "message": "Invalid administrator password or credentials."
        }

    token = SecurityManager.create_access_token(data={"sub": email, "email": email, "role": "admin"})
    return {
        "success": True,
        "is_admin": True,
        "token": token,
        "email": email,
        "role": "admin"
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


# ============================================================================
# MODULAR SUBSCRIPTION PLAN QUEUE & ADMIN APPROVAL ENDPOINTS
# ============================================================================

class PlanSubmitRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID or Unique Handle")
    email: str = Field(..., description="Litigator / Law Firm Work Email")
    selected_modules: list = Field(..., description="List of chosen modular engines")
    monthly_price_inr: float = Field(..., description="Calculated monthly fee in INR")
    requested_quota: int = Field(..., description="Requested monthly cases (10 per module)")
    role: Optional[str] = Field("law_firm", description="Designation (e.g. advocate, law_firm, bank_panel)")

class PlanActionRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")
    reason: Optional[str] = Field("", description="Optional rejection or approval notes")


@router.post("/subscription/submit-plan", tags=["Subscription Simulation"])
def submit_modular_plan_request(req: PlanSubmitRequest = Body(...)):
    """
    Submits a modular subscription request into the admin approval queue (PENDING_APPROVAL).
    Access to analysis and drafting remains locked until approved by platform admin.
    """
    try:
        quota = DatabaseManager.submit_subscription_plan(
            user_id=req.user_id,
            email=req.email,
            selected_modules=req.selected_modules,
            monthly_price_inr=req.monthly_price_inr,
            requested_quota=req.requested_quota,
            role=req.role or "law_firm"
        )
        logger.info(f"[SUBSCRIPTION] Plan request submitted for {req.user_id} ({len(req.selected_modules)} modules, ₹{req.monthly_price_inr}) - PENDING_APPROVAL")
        return {
            "success": True,
            "status": "PENDING_APPROVAL",
            "message": "Your subscription plan request has been submitted to the Admin Control Center. Analysis and draft generation access will remain locked until administrative approval.",
            "quota": quota
        }
    except Exception as e:
        logger.error(f"Error submitting plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit plan request: {str(e)}")


@router.get("/pending-plans", tags=["Admin Control"])
def get_pending_plans(admin: dict = Depends(require_admin)):
    """
    Returns all subscription plan requests awaiting admin approval.
    """
    pending = DatabaseManager.get_pending_plan_requests()
    return {"success": True, "pending_plans": pending, "total": len(pending)}


@router.post("/approve-plan", tags=["Admin Control"])
def approve_plan_request(req: PlanActionRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Admin approves a pending modular subscription plan, activating the account and unlocking full analysis and drafting quota.
    """
    try:
        updated = DatabaseManager.approve_user_plan(req.user_id, admin.get("email", "admin@judiq.ai"))
        logger.info(f"[ADMIN] Admin {admin.get('email')} APPROVED plan for {req.user_id}")
        return {
            "success": True,
            "message": f"Successfully approved plan for {req.user_id}. Account activated with {updated.get('monthly_report_limit')} monthly cases.",
            "quota": updated
        }
    except Exception as e:
        logger.error(f"Error approving plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve plan: {str(e)}")


@router.post("/reject-plan", tags=["Admin Control"])
def reject_plan_request(req: PlanActionRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Admin rejects a subscription plan request, keeping account access locked.
    """
    try:
        updated = DatabaseManager.reject_user_plan(req.user_id, admin.get("email", "admin@judiq.ai"), req.reason or "Administrative rejection")
        logger.info(f"[ADMIN] Admin {admin.get('email')} REJECTED plan for {req.user_id}")
        return {
            "success": True,
            "message": f"Plan request for {req.user_id} rejected.",
            "quota": updated
        }
    except Exception as e:
        logger.error(f"Error rejecting plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject plan: {str(e)}")


# ============================================================================
# BANK INSTITUTIONAL OPERATIONS & GOVERNANCE ENDPOINTS
# ============================================================================

class BankOfficerAllocationRequest(BaseModel):
    officer_id: str = Field(..., description="Target Bank Officer ID")
    monthly_audit_limit: int = Field(..., description="Monthly recovery audit quota limit (-1 for unlimited)")
    role: Optional[str] = Field(None, description="Bank role (bank_officer, sarb_manager, recovery_head)")
    branch_name: Optional[str] = Field(None, description="Branch name")
    bank_name: Optional[str] = Field(None, description="Bank name")
    email: Optional[str] = Field(None, description="Officer email")

class BankOfficerCreateRequest(BaseModel):
    officer_id: str = Field(..., description="Unique Bank Officer ID / Code")
    name: str = Field(..., description="Officer Full Name")
    bank_name: str = Field(..., description="Institutional Bank Name")
    branch_name: str = Field(..., description="Recovery Branch / Cell")
    role: str = Field("bank_officer", description="Role (bank_officer, sarb_manager, recovery_head)")
    email: str = Field(..., description="Official Bank Email")
    monthly_audit_limit: int = Field(100, description="Monthly audit quota")

class BankOfficerStatusToggleRequest(BaseModel):
    officer_id: str = Field(..., description="Target Bank Officer ID")
    is_active: bool = Field(..., description="Active status flag")


@router.get("/bank/stats", tags=["Admin Bank Operations"])
def get_admin_bank_stats(admin: dict = Depends(require_admin)):
    """
    Returns platform-wide banking & recovery stats: Total Officers, Active Branches, Audits Performed, Volume.
    """
    stats = DatabaseManager.get_bank_admin_stats()
    return {"success": True, "stats": stats, "admin_user": admin["email"]}


@router.get("/bank/officers", tags=["Admin Bank Operations"])
def get_admin_bank_officers(admin: dict = Depends(require_admin)):
    """
    Returns all registered bank officers, branch recovery units, monthly audit allocations, and usage progress.
    """
    officers = DatabaseManager.get_all_bank_officers()
    return {"success": True, "officers": officers, "total": len(officers)}


@router.post("/bank/officers/create", tags=["Admin Bank Operations"])
def create_bank_officer(req: BankOfficerCreateRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Provisions a new bank branch officer account with institutional recovery quota.
    """
    officer = DatabaseManager.get_or_create_bank_officer(
        officer_id=req.officer_id.strip(),
        name=req.name.strip(),
        bank_name=req.bank_name.strip(),
        branch_name=req.branch_name.strip(),
        email=req.email.strip()
    )
    if req.monthly_audit_limit != 100 or req.role != "bank_officer":
        DatabaseManager.update_bank_officer_allocation(
            officer_id=req.officer_id.strip(),
            monthly_limit=req.monthly_audit_limit,
            role=req.role
        )
        officer = DatabaseManager.get_or_create_bank_officer(req.officer_id.strip())

    logger.info(f"[ADMIN] Admin {admin.get('email')} created bank officer account {req.officer_id}")
    return {"success": True, "officer": officer, "message": f"Bank officer account {req.officer_id} provisioned."}


@router.post("/bank/officers/allocate", tags=["Admin Bank Operations"])
def allocate_bank_officer_quota(req: BankOfficerAllocationRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Updates the monthly recovery audit allocation limit, role, or branch assignment for a bank officer.
    """
    success = DatabaseManager.update_bank_officer_allocation(
        officer_id=req.officer_id,
        monthly_limit=req.monthly_audit_limit,
        role=req.role,
        branch_name=req.branch_name,
        bank_name=req.bank_name,
        email=req.email
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update bank officer quota allocation.")
    
    updated_officer = DatabaseManager.get_or_create_bank_officer(req.officer_id)
    logger.info(f"[ADMIN] Admin {admin.get('email')} updated bank quota for {req.officer_id} to {req.monthly_audit_limit}")
    return {"success": True, "officer": updated_officer, "message": f"Successfully updated monthly audit quota to {req.monthly_audit_limit}."}


@router.post("/bank/officers/toggle", tags=["Admin Bank Operations"])
def toggle_bank_officer_status(req: BankOfficerStatusToggleRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Activates or suspends a bank officer's access to the recovery audit engine.
    """
    success = DatabaseManager.update_bank_officer_allocation(
        officer_id=req.officer_id,
        is_active=req.is_active
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update bank officer status.")
    
    status_str = "ACTIVE" if req.is_active else "SUSPENDED"
    logger.info(f"[ADMIN] Admin {admin.get('email')} changed bank status of {req.officer_id} to {status_str}")
    return {"success": True, "is_active": req.is_active, "message": f"Bank officer status set to {status_str}."}


@router.get("/bank/audits", tags=["Admin Bank Operations"])
def get_admin_bank_audits(limit: int = Query(50), admin: dict = Depends(require_admin)):
    """
    Fetches the tamper-proof institutional compliance audit stream across all bank branches.
    """
    audits = DatabaseManager.get_all_bank_audits(limit=limit)
    return {"success": True, "audits": audits, "total": len(audits)}


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
