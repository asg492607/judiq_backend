"""
payments_router.py — Razorpay Standard Checkout integration for JudiQ AI.

Endpoints:
  POST /api/v1/payments/create-order   → creates a Razorpay order, returns order metadata
  POST /api/v1/payments/verify-payment → verifies Razorpay HMAC-SHA256 signature

Credentials are loaded from environment variables (RAZORPAY_KEY_ID,
RAZORPAY_KEY_SECRET) via config.py — the KEY_SECRET NEVER reaches the frontend.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from typing import Any, cast, Optional

import razorpay
import razorpay.errors as razorpay_errors
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from config import settings

logger = logging.getLogger("JudiQ.Payments")

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_razorpay_client() -> razorpay.Client:
    """Return an authenticated Razorpay client, or raise 500 if not configured."""
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    if not key_id or not key_secret:
        logger.error("Razorpay credentials are not configured in environment variables.")
        raise HTTPException(
            status_code=500,
            detail="Payment gateway is not configured. Contact support.",
        )
    return razorpay.Client(auth=(key_id, key_secret))


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CreateOrderRequest(BaseModel):
    amount: int = Field(..., description="Amount in paise (INR x 100). Minimum 100.")
    currency: str = Field(default="INR", max_length=3)
    receipt: str = Field(
        default_factory=lambda: f"judiq_{uuid.uuid4().hex[:12]}",
        max_length=40,
    )
    user_id: Optional[str] = None
    email: Optional[str] = None
    plan_name: Optional[str] = None
    is_paid_demo: Optional[bool] = False

    @field_validator("amount")
    @classmethod
    def amount_minimum(cls, v: int) -> int:
        if v < 100:
            raise ValueError("amount must be at least 100 paise (Rs.1.00)")
        return v


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    receipt: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    plan: Optional[str] = "standard"
    plan_name: Optional[str] = "Standard Monthly Plan"
    modules: Optional[list] = None
    quota: Optional[int] = 10
    amount: Optional[float] = 999.0


class VerifyPaymentResponse(BaseModel):
    success: bool
    message: str
    quota: Optional[dict] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/key",
    tags=["Payments"],
    summary="Return the Razorpay public Key ID (safe for frontend consumption)",
)
async def get_razorpay_key() -> dict:
    """
    Returns only the PUBLIC Key ID so the frontend can open the checkout modal.
    The KEY_SECRET is NEVER included in this response.
    """
    key_id = settings.RAZORPAY_KEY_ID
    if not key_id:
        raise HTTPException(status_code=500, detail="Payment gateway is not configured.")
    return {"key_id": key_id}


@router.post(
    "/create-order",
    response_model=CreateOrderResponse,
    tags=["Payments"],
    summary="Create a Razorpay order",
)
async def create_order(payload: CreateOrderRequest) -> CreateOrderResponse:
    """
    Step 1 of Razorpay Standard Checkout.

    Creates a server-side order via the Razorpay Orders API and returns the
    order_id that the frontend needs to open the payment modal.
    """
    client = _get_razorpay_client()

    order_data = {
        "amount": payload.amount,
        "currency": payload.currency,
        "receipt": payload.receipt,
        "payment_capture": 1,  # auto-capture
    }

    try:
        # cast(Any, ...) silences Pyright's false-positive: the razorpay SDK
        # exposes .order at runtime but ships no PEP 561 type stubs.
        order = cast(Any, client).order.create(data=order_data)
    except razorpay_errors.BadRequestError as exc:
        logger.warning("Razorpay bad request: %s", exc)
        raise HTTPException(status_code=400, detail=f"Invalid order parameters: {exc}") from exc
    except razorpay_errors.SignatureVerificationError as exc:
        logger.error("Razorpay auth failure: %s", exc)
        raise HTTPException(status_code=401, detail="Payment gateway authentication failed.") from exc
    except Exception as exc:
        logger.error("Razorpay order creation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create payment order.") from exc

    logger.info("Razorpay order created: %s (Rs.%.2f)", order["id"], payload.amount / 100)
    try:
        from session import DatabaseManager
        DatabaseManager.record_payment_transaction(
            order_id=order["id"],
            user_id=payload.user_id or "ANON",
            email=payload.email,
            amount=round(payload.amount / 100, 2),
            currency=payload.currency,
            plan_name=payload.plan_name or "Standard Monthly Plan",
            status="CREATED",
            metadata={"receipt": order.get("receipt", payload.receipt)}
        )
    except Exception as e:
        logger.warning(f"Error recording created order transaction: {e}")

    return CreateOrderResponse(
        order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        receipt=order.get("receipt", payload.receipt),
    )


@router.post(
    "/verify-payment",
    response_model=VerifyPaymentResponse,
    tags=["Payments"],
    summary="Verify Razorpay payment signature",
)
async def verify_payment(payload: VerifyPaymentRequest) -> VerifyPaymentResponse:
    """
    Step 3 of Razorpay Standard Checkout.

    Verifies the HMAC-SHA256 signature using:
        signature = HMAC_SHA256(order_id + "|" + payment_id, KEY_SECRET)

    Returns 400 if the signature does not match -- never marks a payment as
    paid on mismatch.
    """
    key_secret = settings.RAZORPAY_KEY_SECRET
    if not key_secret:
        raise HTTPException(
            status_code=500,
            detail="Payment gateway is not configured. Contact support.",
        )

    if not payload.razorpay_order_id or not payload.razorpay_payment_id or not payload.razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing required payment fields.")

    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected_signature = hmac.new(
        key_secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
        logger.warning(
            "Razorpay signature mismatch for order %s / payment %s",
            payload.razorpay_order_id,
            payload.razorpay_payment_id,
        )
        raise HTTPException(status_code=400, detail="Payment verification failed: signature mismatch.")

    logger.info(
        "Payment verified  order=%s  payment=%s",
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
    )
    try:
        from session import DatabaseManager
        DatabaseManager.record_payment_transaction(
            order_id=payload.razorpay_order_id,
            payment_id=payload.razorpay_payment_id,
            user_id=payload.user_id,
            email=payload.email,
            amount=payload.amount or 999.0,
            currency="INR",
            plan_name=payload.plan_name or "Standard Monthly Plan",
            status="SUCCESS",
            method="Razorpay",
            metadata={"plan": payload.plan, "quota": payload.quota}
        )
    except Exception as e:
        logger.warning(f"Error recording verified payment transaction: {e}")

    activated_quota = None
    if payload.user_id or payload.email:
        try:
            from session import DatabaseManager
            target_uid = (payload.user_id or "").strip()
            target_email = (payload.email or "").strip().lower()
            if not target_uid and target_email:
                target_uid = f"USR_{target_email.split('@')[0].upper()}"

            is_topup = (
                (payload.plan_name and ("topup" in payload.plan_name.lower() or "single" in payload.plan_name.lower())) or 
                payload.plan in ("single_report", "topup_report") or 
                (payload.amount is not None and abs(payload.amount - 149.0) < 0.01)
            )
            is_paid_demo = (
                (payload.plan_name and "demo" in payload.plan_name.lower()) or 
                payload.plan == "paid_demo" or 
                (payload.quota == 1 and payload.amount == 2.0)
            )

            if is_topup:
                allocated_quota = payload.quota if (payload.quota and payload.quota > 0) else 1
                plan_name = "Single Report Top-up"
                plan_price = payload.amount or 149.0
            elif is_paid_demo:
                allocated_quota = 1
                plan_name = "Paid Demo Plan"
                plan_price = 2.0
            else:
                allocated_quota = payload.quota if (payload.quota and payload.quota > 0) else 10
                plan_name = payload.plan_name or "Standard Monthly Plan"
                plan_price = payload.amount or 999.0

            activated_quota = DatabaseManager.submit_subscription_plan(
                user_id=target_uid,
                email=target_email,
                selected_modules=payload.modules or ["s138"],
                monthly_price_inr=plan_price,
                requested_quota=allocated_quota,
                role="law_firm",
                status="ACTIVE",
                razorpay_payment_id=payload.razorpay_payment_id,
                plan_name=plan_name,
                paid_demo_used=1 if is_paid_demo else None
            )
            logger.info("Subscription activated immediately without admin approval for user=%s (%s), plan=%s (Rs.%.2f)", target_uid, target_email, plan_name, plan_price)
        except ValueError as ve:
            logger.warning("Subscription activation rejected: %s", ve)
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error("Error auto-activating subscription in verify-payment: %s", e)

    return VerifyPaymentResponse(
        success=True,
        message="Payment verified and subscription activated successfully.",
        quota=activated_quota
    )
