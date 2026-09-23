import pytest
import io
from fastapi.testclient import TestClient
from main import app
from session import DatabaseManager

import uuid

client = TestClient(app)

def test_free_tier_and_pricing_rules():
    uid = uuid.uuid4().hex[:8]
    test_user = f"user_test_free_{uid}"
    test_email = f"test_{uid}@example.com"

    # 1. New user gets Free Tier with 5 lifetime reports
    quota = DatabaseManager.get_or_create_user_quota(test_user, test_email, role="advocate")
    assert quota["monthly_report_limit"] == 5
    assert quota["plan_name"] == "Free Tier"

    # 2. Check draft quota for Free Tier: First draft of LEGAL_NOTICE in English is allowed
    res1 = DatabaseManager.check_and_consume_draft_quota(
        user_id=test_user, email=test_email, draft_type="LEGAL_NOTICE", lang="en", role="advocate"
    )
    assert res1["allowed"] is True
    assert res1["reason"] == "FREE_TIER_FIRST_DRAFT"

    # 3. Second draft of same type (LEGAL_NOTICE) is BLOCKED on Free Tier
    res2 = DatabaseManager.check_and_consume_draft_quota(
        user_id=test_user, email=test_email, draft_type="LEGAL_NOTICE", lang="en", role="advocate"
    )
    assert res2["allowed"] is False
    assert res2["reason"] == "DRAFT_LIMIT_REACHED"

    # 4. Another draft type (APPLICATION_143A) in English is allowed for its 1st time
    res3 = DatabaseManager.check_and_consume_draft_quota(
        user_id=test_user, email=test_email, draft_type="APPLICATION_143A", lang="en", role="advocate"
    )
    assert res3["allowed"] is True

    # 5. Multilingual drafting (Marathi / Hindi) is BLOCKED on Free Tier
    res_mr = DatabaseManager.check_and_consume_draft_quota(
        user_id=test_user, email=test_email, draft_type="COMPLAINT", lang="mr", role="advocate"
    )
    assert res_mr["allowed"] is False
    assert res_mr["reason"] == "MULTILINGUAL_LOCKED"

    res_hi = DatabaseManager.check_and_consume_draft_quota(
        user_id=test_user, email=test_email, draft_type="COMPLAINT", lang="hi", role="advocate"
    )
    assert res_hi["allowed"] is False
    assert res_hi["reason"] == "MULTILINGUAL_LOCKED"

    # 6. Single report top-up: ₹149 adds +1 report to quota
    topup_sub = DatabaseManager.submit_subscription_plan(
        user_id=test_user,
        email=test_email,
        selected_modules=["s138"],
        monthly_price_inr=149,
        requested_quota=1,
        role="advocate",
        plan_name="Single Report Top-up",
        razorpay_payment_id="pay_topup_149_001",
        status="PAID"
    )
    assert topup_sub["success"] is True
    updated_q = DatabaseManager.get_or_create_user_quota(test_user, test_email)
    assert updated_q["monthly_report_limit"] == 6  # 5 + 1

    # 7. Standard Monthly Plan upgrade: ₹999 for 10 reports/month
    std_sub = DatabaseManager.submit_subscription_plan(
        user_id=test_user,
        email=test_email,
        selected_modules=["s138"],
        monthly_price_inr=999,
        requested_quota=10,
        role="advocate",
        plan_name="Standard Monthly Plan",
        razorpay_payment_id="pay_std_999_001",
        status="PAID"
    )
    assert std_sub["success"] is True
    paid_q = DatabaseManager.get_or_create_user_quota(test_user, test_email)
    assert paid_q["monthly_report_limit"] == 10
    assert paid_q["plan_status"] == "ACTIVE"

    # 8. Standard Plan allows unlimited drafting and multilingual Marathi / Hindi
    res_paid_mr = DatabaseManager.check_and_consume_draft_quota(
        user_id=test_user, email=test_email, draft_type="LEGAL_NOTICE", lang="mr", role="advocate"
    )
    assert res_paid_mr["allowed"] is True
    assert res_paid_mr["language_allowed"] is True

    res_paid_hi = DatabaseManager.check_and_consume_draft_quota(
        user_id=test_user, email=test_email, draft_type="LEGAL_NOTICE", lang="hi", role="advocate"
    )
    assert res_paid_hi["allowed"] is True
    assert res_paid_hi["language_allowed"] is True

def test_doc_intel_extract_auto_creates_case():
    # Test uploading a text file via /api/v1/doc-intel/extract and check case_id auto-creation
    file_bytes = b"CHEQUE BOUNCE DEMAND NOTICE\nPayee: Apex Logistics Pvt Ltd\nDrawer: Delta Infra Corp\nAmount: Rs 5,50,000\nCheque No: 492019\nBank: HDFC Bank"
    files = [("files", ("notice.txt", io.BytesIO(file_bytes), "text/plain"))]
    data = {"workflow_type": "cheque_bounce"}

    response = client.post("/api/v1/doc-intel/extract", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "case_id" in res_data
    assert res_data["case_id"].startswith("CSE-")
    assert res_data["case_name"] != ""

    # Verify case exists in DatabaseManager
    case = DatabaseManager.cms_get_case(res_data["case_id"])
    assert case is not None
    assert case["case_id"] == res_data["case_id"]

def test_translate_draft_endpoint():
    # 1. Free tier blocked from translating to Marathi
    res_free = client.post("/api/v1/documents/translate-draft", json={
        "content": "This is a legal demand notice for dishonour of cheque.",
        "draft_type": "LEGAL_NOTICE",
        "lang": "mr",
        "user_id": "anon_trial_user_999",
        "email": "anon_trial_user_999@example.com"
    })
    assert res_free.status_code == 403
    assert res_free.json()["reason"] == "MULTILINGUAL_LOCKED"

    # 2. Admin or paid user translation succeeds
    res_admin = client.post("/api/v1/documents/translate-draft", json={
        "content": "This is a legal demand notice under Section 138 of Negotiable Instruments Act.",
        "draft_type": "LEGAL_NOTICE",
        "lang": "mr",
        "user_id": "admin",
        "role": "admin",
        "email": "aixynztechnologies@gmail.com"
    })
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert data["success"] is True
    assert data["language"] == "mr"
    assert "कायदेशीर" in data["draft"] or "कलम" in data["draft"] or len(data["draft"]) > 50
