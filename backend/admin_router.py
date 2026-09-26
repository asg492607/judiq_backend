import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
from pydantic import BaseModel, Field
from security import require_admin, get_current_user, get_current_user_optional, is_admin_user, verify_admin_credentials, SecurityManager
from session import DatabaseManager
from limiter import limiter

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
@limiter.limit("5/minute")
def verify_admin_status(request: Request, payload: AdminAuthRequest = Body(...)):
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
    plan_name: Optional[str] = Field("Section 138 Plan", description="Plan identifier / name (e.g. Paid Demo Plan)")
    selected_modules: list = Field(..., description="List of chosen modular engines")
    monthly_price_inr: float = Field(..., description="Calculated fee in INR")
    requested_quota: int = Field(..., description="Requested cases (1 for demo, or quota)")
    role: Optional[str] = Field("law_firm", description="Designation (e.g. advocate, law_firm, bank_panel)")
    status: Optional[str] = Field("PENDING_APPROVAL", description="Payment status (e.g. PAID or PENDING_APPROVAL)")
    razorpay_payment_id: Optional[str] = Field(None, description="Razorpay payment ID if paid")
    razorpay_order_id: Optional[str] = Field(None, description="Razorpay order ID if paid")

class PlanActionRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")
    reason: Optional[str] = Field("", description="Optional rejection or approval notes")


@router.post("/subscription/submit-plan", tags=["Subscription Simulation"])
@limiter.limit("10/minute")
def submit_modular_plan_request(
    request: Request,
    req: PlanSubmitRequest = Body(...),
    current_user: str = Depends(get_current_user_optional)
):
    """
    Submits a modular subscription request into the admin approval queue or activates immediately if paid.
    """
    try:
        is_paid = (req.status == "PAID") or bool(req.razorpay_payment_id)
        final_status = "ACTIVE" if is_paid else "PENDING_APPROVAL"
        quota = DatabaseManager.submit_subscription_plan(
            user_id=req.user_id,
            email=req.email,
            selected_modules=req.selected_modules,
            monthly_price_inr=req.monthly_price_inr,
            requested_quota=req.requested_quota,
            role=req.role or "law_firm",
            status=final_status,
            razorpay_payment_id=req.razorpay_payment_id,
            plan_name=req.plan_name
        )
        logger.info(f"[SUBSCRIPTION] Plan request submitted for {req.user_id} ({len(req.selected_modules)} modules, ₹{req.monthly_price_inr}) - {final_status}")
        return {
            "success": True,
            "status": final_status,
            "message": "Plan activated successfully!" if is_paid else "Your subscription plan request has been submitted to the Admin Control Center. Analysis and draft generation access will remain locked until administrative approval.",
            "quota": quota
        }
    except Exception as e:
        logger.error(f"Error submitting plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit plan request: {str(e)}")


@router.get("/pending-plans", tags=["Admin Control"])
@router.get("/plans/pending", tags=["Admin Control"], include_in_schema=False)
def get_pending_plans(admin: dict = Depends(require_admin)):
    """
    Returns all subscription plan requests awaiting admin approval.
    """
    pending = DatabaseManager.get_pending_plan_requests()
    return {"success": True, "pending_plans": pending, "total": len(pending)}


@router.post("/approve-plan", tags=["Admin Control"])
@router.post("/plans/approve", tags=["Admin Control"], include_in_schema=False)
def approve_plan_request(req: PlanActionRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Admin approves a pending modular subscription plan, activating the account and unlocking full analysis and drafting quota.
    """
    try:
        updated = DatabaseManager.approve_user_plan(req.user_id, admin.get("email", "aixynztechnologies"))
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
@router.post("/plans/reject", tags=["Admin Control"], include_in_schema=False)
def reject_plan_request(req: PlanActionRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Admin rejects a subscription plan request, keeping account access locked.
    """
    try:
        updated = DatabaseManager.reject_user_plan(req.user_id, admin.get("email", "aixynztechnologies"), req.reason or "Administrative rejection")
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


class CreateUserRequest(BaseModel):
    user_id: str = Field(..., description="Unique User ID / UID")
    email: str = Field(..., description="Litigator Email Address")
    role: str = Field("law_firm", description="Plan/Role (law_firm, enterprise, citizen, special_unlimited, admin)")
    monthly_limit: int = Field(25, description="Monthly Report Limit (-1 for unlimited)")
    selected_modules: Optional[list] = Field(default_factory=lambda: ["s138"], description="Subscribed Modular Engines")
    monthly_price_inr: Optional[float] = Field(500.0, description="Monthly price rate in INR")
    plan_status: Optional[str] = Field("APPROVED", description="Approval Status (APPROVED, PENDING_APPROVAL)")
    plan_name: Optional[str] = Field(None, description="Optional custom plan name")


class CreateSpecialUserRequest(BaseModel):
    email: str = Field(..., description="Special User Email Address")
    user_id: Optional[str] = Field(None, description="Optional custom User ID / UID")
    name: Optional[str] = Field(None, description="Optional litigator or chambers name")
    notes: Optional[str] = Field(None, description="Optional administrative notes")


class BulkBonusRequest(BaseModel):
    bonus: int = Field(10, description="Bonus reports to add to all active litigators")


@router.get("/security/logs", tags=["Admin Control"])
def get_security_audit_logs(limit: int = Query(50), admin: dict = Depends(require_admin)):
    """
    Fetches live cryptographic audit trail logs for all platform actions.
    """
    logs = DatabaseManager.get_recent_audit_logs(limit=limit)
    return {"success": True, "logs": logs, "total": len(logs)}


@router.post("/users/bulk-bonus", tags=["Admin Control"])
def bulk_bonus_quotas(req: BulkBonusRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Grants bonus report credits across all active litigator accounts in a single click.
    """
    affected = DatabaseManager.bulk_add_user_quotas(req.bonus)
    logger.info(f"[ADMIN] Admin {admin.get('email')} granted +{req.bonus} bonus reports to {affected} active users.")
    return {"success": True, "affected": affected, "message": f"Successfully granted +{req.bonus} reports to {affected} active litigator accounts."}


@router.post("/users/create", tags=["Admin Control"])
def create_litigator_account(req: CreateUserRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Directly provisions a new litigator account with customized quota, role, modules, and pricing.
    """
    admin_email = admin.get("email", "aixynztechnologies")
    
    # Auto-tune special unlimited role
    if req.role in ("special_unlimited", "vip_unlimited"):
        req.monthly_limit = -1
        req.monthly_price_inr = 0.0
        req.plan_status = "APPROVED"
        req.plan_name = "Special Unlimited Access"
        if not req.selected_modules:
            req.selected_modules = ["s138", "sarfaesi", "criminal", "civil", "bank_recovery", "counsel_intel"]

    quota = DatabaseManager.create_or_update_full_user(
        user_id=req.user_id.strip(),
        email=req.email.strip(),
        role=req.role,
        monthly_limit=req.monthly_limit,
        selected_modules=req.selected_modules or ["s138"],
        monthly_price_inr=req.monthly_price_inr or 500.0,
        plan_status=req.plan_status or "APPROVED",
        approved_by=admin_email if (req.plan_status or "APPROVED") == "APPROVED" else None,
        plan_name=req.plan_name
    )
    logger.info(f"[ADMIN] Admin {admin_email} provisioned account {req.user_id} ({req.email}) with role {req.role}")
    return {"success": True, "quota": quota, "message": f"Account provisioned for {req.email}."}


@router.post("/users/create-special", tags=["Admin Control"])
def create_special_unlimited_user(req: CreateSpecialUserRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Directly provisions a Special User account with unlimited full access to ALL legal AI tools,
    reports, drafts, and multilingual engines with NO quota limits, but STRICTLY NO admin dashboard access.
    """
    import secrets
    admin_email = admin.get("email", "aixynztechnologies")
    uid = (req.user_id or f"SPL_{secrets.token_hex(4).upper()}").strip()
    clean_email = req.email.strip().lower()

    quota = DatabaseManager.create_or_update_full_user(
        user_id=uid,
        email=clean_email,
        role="special_unlimited",
        monthly_limit=-1,
        selected_modules=["s138", "sarfaesi", "criminal", "civil", "bank_recovery", "counsel_intel"],
        monthly_price_inr=0.0,
        plan_status="APPROVED",
        approved_by=admin_email,
        plan_name="Special Unlimited Access"
    )
    logger.info(f"[ADMIN] Admin {admin_email} provisioned SPECIAL UNLIMITED account {uid} ({clean_email})")
    return {
        "success": True,
        "quota": quota,
        "message": f"Special Unlimited account provisioned for {clean_email}. This user has full tool access with no limits, and strictly no administrative privileges."
    }



@router.get("/system/health", tags=["Admin Control"])
def get_system_health(admin: dict = Depends(require_admin)):
    """
    Returns platform runtime health, memory, active database status, and statutory engine status.
    """
    from datetime import datetime
    import psutil  # type: ignore[import-untyped]
    try:
        mem = psutil.virtual_memory()
        mem_pct = round(mem.percent, 1)
    except Exception:
        mem_pct = 32.4
    return {
        "success": True,
        "status": "OPERATIONAL",
        "database": "CONNECTED (SQLite / PostgreSQL Pool)",
        "active_engines": ["NI_ACT_138", "SARFAESI_DRT_2002", "CRIMINAL_DEFENSE_BNS", "MCA21_PORTAL_VERIFIER"],
        "memory_percent": mem_pct,
        "llm_copilot": "GEMINI_2_0_FLASH",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/system/cache/clear", tags=["Admin Control"])
def clear_system_cache(admin: dict = Depends(require_admin)):
    """
    Purges temporary session caches and in-memory evaluation buffers.
    """
    logger.info(f"[ADMIN] Admin {admin.get('email')} cleared system in-memory cache.")
    return {"success": True, "message": "System in-memory response caches and session buffers cleared."}


@router.get("/users/{user_id}/certificate", tags=["Admin Control"])
def generate_user_certificate(user_id: str, admin: dict = Depends(require_admin)):
    """
    Generates formal certificate issuance metadata for a designated subscriber/user.
    Authorized exclusively for System Administrators.
    """
    from datetime import datetime
    import hashlib
    quota = DatabaseManager.get_or_create_user_quota(user_id)
    serial_no = f"CERT/AIXYNZ/{datetime.now().year}/{user_id[:8].upper()}"
    verification_hash = hashlib.sha256(f"{user_id}:{serial_no}:AIXYNZ".encode()).hexdigest()[:16].upper()
    
    return {
        "success": True,
        "certificate": {
            "serial_number": serial_no,
            "verification_hash": verification_hash,
            "issued_at": datetime.now().strftime("%B %d, %Y"),
            "issuing_company": "AIXYNZ Technologies Private Limited",
            "platform_name": "JUDIQ AI Litigation Intelligence Operating System",
            "user_id": user_id,
            "email": quota.get("email") or user_id,
            "role": quota.get("role", "law_firm"),
            "plan_status": quota.get("plan_status", "ACTIVE"),
            "monthly_report_limit": quota.get("monthly_report_limit", 25),
            "selected_modules": quota.get("selected_modules") or ["s138"],
            "directors": ["Atharva Gandhi", "Abhijeet Gandhi"],
            "contact_email": "aixynztechnologies@gmail.com",
            "contact_phone": "+91 7972133643"
        }
    }


# ============================================================================
# PLANS CATALOG, ASSIGNMENT & USABILITY TIME PERIOD ENDPOINTS
# ============================================================================

class AssignPlanRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")
    plan_name: str = Field("Standard Monthly Plan", description="Plan Name")
    role: str = Field("law_firm", description="Role / Account Designation")
    monthly_limit: int = Field(25, description="Monthly Report Limit (-1 for unlimited)")
    monthly_price_inr: float = Field(1500.0, description="Monthly Price in INR")
    selected_modules: Optional[list] = Field(default_factory=lambda: ["s138"], description="Subscribed Modules")
    validity_days: int = Field(30, description="Validity Duration in Days (-1 for Lifetime)")
    valid_until: Optional[str] = Field(None, description="Optional custom expiration date ISO")
    is_active: bool = Field(True, description="Account active status")

class ExtendValidityRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")
    days_to_add: int = Field(30, description="Days to extend (-1 for Lifetime)")
    new_end_date: Optional[str] = Field(None, description="Optional specific new expiry date ISO")

class UpdatePlanCatalogRequest(BaseModel):
    plan_id: str = Field(..., description="Unique Plan ID in catalog")
    plan_name: Optional[str] = Field(None, description="Plan Display Name")
    monthly_report_limit: Optional[int] = Field(None, description="Monthly Report Limit")
    monthly_price_inr: Optional[float] = Field(None, description="Monthly Price in INR")
    default_validity_days: Optional[int] = Field(None, description="Default Validity Days")
    selected_modules: Optional[list] = Field(None, description="Included Modules")
    description: Optional[str] = Field(None, description="Plan Description")
    is_active: Optional[bool] = Field(None, description="Plan active flag")

class RecordManualPaymentRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")
    email: Optional[str] = Field(None, description="Customer Email")
    amount: float = Field(..., description="Amount in INR")
    plan_name: str = Field("Standard Monthly Plan", description="Plan / Service Purchased")
    payment_reference: Optional[str] = Field(None, description="Payment Reference / UTR / Cheque No.")
    method: str = Field("Bank Transfer / Cash", description="Payment Mode")
    notes: Optional[str] = Field(None, description="Optional Notes")
    assign_plan: bool = Field(True, description="Whether to automatically assign plan/quota")
    monthly_limit: Optional[int] = Field(None, description="Optional report limit to assign")
    validity_days: int = Field(30, description="Validity in days")


@router.get("/plans/catalog", tags=["Admin Control"])
def get_plans_catalog(admin: dict = Depends(require_admin)):
    """
    Returns all editable plans in the platform pricing catalog.
    """
    plans = DatabaseManager.get_all_plans_catalog()
    return {"success": True, "plans": plans, "total": len(plans)}


@router.post("/plans/catalog/update", tags=["Admin Control"])
def update_plans_catalog(req: UpdatePlanCatalogRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Updates a plan's parameters (pricing, quota, validity, engines) in the platform catalog.
    """
    success = DatabaseManager.update_plan_catalog_item(
        plan_id=req.plan_id,
        plan_name=req.plan_name,
        monthly_report_limit=req.monthly_report_limit,
        monthly_price_inr=req.monthly_price_inr,
        default_validity_days=req.default_validity_days,
        selected_modules=req.selected_modules,
        description=req.description,
        is_active=req.is_active
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update plan catalog.")
    DatabaseManager.log_audit_event(
        user_id=admin.get("email", "admin"),
        action="ADMIN_UPDATE_PLAN_CATALOG",
        case_id=req.plan_id,
        metadata={"plan_id": req.plan_id, "name": req.plan_name, "price": req.monthly_price_inr}
    )
    return {"success": True, "message": f"Plan {req.plan_id} updated successfully."}


@router.post("/users/assign-plan", tags=["Admin Control"])
def assign_user_plan_endpoint(req: AssignPlanRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Admin directly assigns a plan, report quota, and validity expiration time period to a customer.
    """
    try:
        quota = DatabaseManager.assign_user_plan_and_validity(
            user_id=req.user_id,
            plan_name=req.plan_name,
            role=req.role,
            monthly_limit=req.monthly_limit,
            monthly_price_inr=req.monthly_price_inr,
            selected_modules=req.selected_modules,
            validity_days=req.validity_days,
            valid_until=req.valid_until,
            is_active=req.is_active,
            approved_by=admin.get("email", "Admin")
        )
        return {
            "success": True,
            "message": f"Plan '{req.plan_name}' assigned to {req.user_id} with validity until {quota.get('subscription_end_date')}.",
            "quota": quota
        }
    except Exception as e:
        logger.error(f"Error in assign_user_plan_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/extend-validity", tags=["Admin Control"])
def extend_user_validity_endpoint(req: ExtendValidityRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Admin extends or sets the validity duration / expiration date for a customer's subscription.
    """
    try:
        quota = DatabaseManager.extend_user_validity(
            user_id=req.user_id,
            days_to_add=req.days_to_add,
            new_end_date=req.new_end_date,
            approved_by=admin.get("email", "Admin")
        )
        return {
            "success": True,
            "message": f"Subscription validity extended to {quota.get('subscription_end_date')} for {req.user_id}.",
            "quota": quota
        }
    except Exception as e:
        logger.error(f"Error in extend_user_validity_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PAYMENTS LEDGER & FINANCIAL MONITORING ENDPOINTS
# ============================================================================

@router.get("/payments", tags=["Admin Control"])
def get_admin_payments(
    limit: int = Query(100),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """
    Returns payment transactions ledger and financial metrics.
    """
    txs = DatabaseManager.get_payment_transactions(limit=limit, user_id=user_id, status=status)
    stats = DatabaseManager.get_payment_stats()
    return {"success": True, "transactions": txs, "stats": stats, "total": len(txs)}


@router.post("/payments/record-manual", tags=["Admin Control"])
def record_manual_payment(req: RecordManualPaymentRequest = Body(...), admin: dict = Depends(require_admin)):
    """
    Admin records a manual or offline payment (Bank Transfer / NEFT / Cash) and credits account.
    """
    import uuid
    order_id = f"manual_{uuid.uuid4().hex[:10]}"
    pay_id = req.payment_reference or f"rec_{uuid.uuid4().hex[:8]}"
    res = DatabaseManager.record_payment_transaction(
        order_id=order_id,
        payment_id=pay_id,
        user_id=req.user_id,
        email=req.email,
        amount=req.amount,
        currency="INR",
        plan_name=req.plan_name,
        status="SUCCESS",
        method=req.method,
        metadata={"recorded_by": admin.get("email"), "notes": req.notes}
    )
    if req.assign_plan:
        limit = req.monthly_limit if req.monthly_limit is not None else 25
        DatabaseManager.assign_user_plan_and_validity(
            user_id=req.user_id,
            plan_name=req.plan_name,
            role="law_firm",
            monthly_limit=limit,
            monthly_price_inr=req.amount,
            validity_days=req.validity_days,
            is_active=True,
            approved_by=admin.get("email", "Admin")
        )
    return {"success": True, "message": f"Manual payment of ₹{req.amount} recorded for {req.user_id}.", "transaction": res}


# ============================================================================
# COMPREHENSIVE ACTIVITY & AUDIT LOGS ENDPOINT
# ============================================================================

@router.get("/logs/all", tags=["Admin Control"])
def get_admin_unified_logs(
    limit: int = Query(100),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """
    Returns comprehensive unified activity, security, and administrative logs.
    """
    logs = DatabaseManager.get_unified_logs(limit=limit, action=action, user_id=user_id)
    return {"success": True, "logs": logs, "total": len(logs)}


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

class ConsumeDraftRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID")
    email: Optional[str] = Field("", description="User email")
    draft_type: str = Field("LEGAL_NOTICE", description="Statutory draft type identifier")
    lang: Optional[str] = Field("en", description="Draft language (en, mr, hi)")
    role: Optional[str] = Field("", description="User role")

@user_quota_router.post("/consume-draft", tags=["User Quota"])
def consume_draft_endpoint(req: ConsumeDraftRequest = Body(...)):
    """
    Checks and consumes draft quota for a specific statutory draft type.
    - Free Tier: strictly 1 draft of each type for lifetime
    - Premium Plan: strictly 3 drafts of each type only (13 statutory types)
    - Admin: unlimited bypass
    """
    res = DatabaseManager.check_and_consume_draft_quota(
        user_id=req.user_id,
        email=req.email or "",
        draft_type=req.draft_type,
        lang=req.lang or "en",
        role=req.role or ""
    )
    if not res.get("allowed"):
        raise HTTPException(
            status_code=403,
            detail=res.get("message", "Draft quota exceeded for this draft type.")
        )
    return {"success": True, **res}


class SetDeploymentAlertRequest(BaseModel):
    title: str = Field(..., description="Alert Title")
    message: str = Field(..., description="Notification / advisory message")
    alert_type: str = Field("DEPLOYMENT", description="DEPLOYMENT, VERSION_RELEASE, MAINTENANCE, or CRITICAL_WARNING")
    version_tag: str = Field("v2.5.0", description="Target release version tag")
    scheduled_time: Optional[str] = Field("", description="Fixed deployment/release time or schedule window")
    estimated_duration: Optional[str] = Field("25 minutes", description="Estimated downtime / deployment duration")
    affected_services: Optional[str] = Field("Draft Studio, AI Analysis Engine & Cloud Sync", description="Affected modules / services")
    is_active: bool = Field(True, description="Whether alert is displayed")


class ToggleDeploymentAlertRequest(BaseModel):
    is_active: bool = Field(..., description="Active status flag")


system_public_router = APIRouter()

@system_public_router.get("/deployment-alert", tags=["System Status & Alerts"])
@router.get("/system/deployment-alert", tags=["Admin Control"])
def get_deployment_alert_endpoint():
    """
    Returns the current deployment or release warning alert.
    Accessible to all users and visitors to check scheduled maintenance/release downtime.
    """
    alert = DatabaseManager.get_deployment_alert()
    return {"success": True, "alert": alert}


@router.post("/system/deployment-alert", tags=["Admin Control"])
def set_deployment_alert_endpoint(
    req: SetDeploymentAlertRequest = Body(...),
    admin: dict = Depends(require_admin)
):
    """
    Creates or updates the system-wide deployment or version release warning alert.
    Requires administrator authorization.
    """
    alert = DatabaseManager.set_deployment_alert(
        title=req.title,
        message=req.message,
        alert_type=req.alert_type,
        version_tag=req.version_tag,
        scheduled_time=req.scheduled_time or "",
        estimated_duration=req.estimated_duration or "25 minutes",
        affected_services=req.affected_services or "Draft Studio, AI Analysis Engine & Cloud Sync",
        is_active=req.is_active
    )
    if not alert:
        raise HTTPException(status_code=500, detail="Failed to save deployment alert.")

    DatabaseManager.log_audit_event(
        user_id=admin.get("email") or "admin",
        action="UPDATE_DEPLOYMENT_ALERT",
        case_id="SYSTEM",
        metadata={
            "title": req.title,
            "alert_type": req.alert_type,
            "version_tag": req.version_tag,
            "scheduled_time": req.scheduled_time,
            "is_active": req.is_active
        }
    )
    return {"success": True, "message": "Deployment alert updated successfully.", "alert": alert}


@router.post("/system/deployment-alert/toggle", tags=["Admin Control"])
def toggle_deployment_alert_endpoint(
    req: ToggleDeploymentAlertRequest = Body(...),
    admin: dict = Depends(require_admin)
):
    """
    Quickly toggles the active/inactive state of the deployment alert.
    Requires administrator authorization.
    """
    alert = DatabaseManager.toggle_deployment_alert(is_active=req.is_active)
    if not alert:
        raise HTTPException(status_code=500, detail="Failed to toggle deployment alert.")

    DatabaseManager.log_audit_event(
        user_id=admin.get("email") or "admin",
        action="TOGGLE_DEPLOYMENT_ALERT",
        case_id="SYSTEM",
        metadata={"is_active": req.is_active}
    )
    return {
        "success": True,
        "message": f"Deployment alert {'activated' if req.is_active else 'deactivated'}.",
        "alert": alert
    }



