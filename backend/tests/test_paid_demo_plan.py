import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from session import DatabaseManager

client = TestClient(app)

def test_free_demo_mode_restrictions():
    """Verify Free Demo mode: allows pre-loaded demo case preview, blocks custom cases & drafts."""
    uid = f"USR_FREE_DEMO_{uuid.uuid4().hex[:6]}"
    email = f"free_demo_{uuid.uuid4().hex[:6]}@lawfirm.in"

    # 1. New user starts in Free Demo (0 quota)
    q = DatabaseManager.get_or_create_user_quota(uid, email)
    assert q["monthly_report_limit"] == 0
    assert q["remaining_reports"] == 0

    # 2. Running a custom case without quota in Free Demo must be BLOCKED
    custom_payload = {
        "user_id": uid,
        "email": email,
        "case_description": "Custom non-demo cheque bounce dispute.",
        "cheque_amount": 500000,
        "cheque_date": "2026-05-01",
        "dishonour_date": "2026-05-10",
        "notice_date": "2026-05-20",
        "recipient_received_date": "2026-05-25",
        "complaint_date": "2026-06-15",
        "complainant_type": "company",
        "accused_type": "individual",
        "is_demo_case": False
    }
    custom_res = client.post("/api/v1/analyze", json=custom_payload)
    assert custom_res.status_code == 403
    assert custom_res.json()["error_code"] == "QUOTA_EXCEEDED"
    assert "Free Demo only supports running pre-loaded demo cases" in custom_res.json()["error"]

    # 3. Running a pre-loaded demo case in Free Demo must SUCCEED
    demo_payload = {
        "user_id": uid,
        "email": email,
        "case_id": "NI-DEMO-2026-001",
        "case_title": "Section 138 NI Act Demo Case",
        "case_description": "Cheque dishonoured due to funds insufficient. 15-day notice expired.",
        "cheque_amount": 100000,
        "cheque_date": "2026-05-01",
        "dishonour_date": "2026-05-10",
        "notice_date": "2026-05-20",
        "recipient_received_date": "2026-05-25",
        "complaint_date": "2026-06-15",
        "complainant_type": "company",
        "accused_type": "individual",
        "is_demo_case": True
    }
    demo_res = client.post("/api/v1/analyze", json=demo_payload)
    assert demo_res.status_code == 200, f"Demo case in Free Demo must succeed, got {demo_res.status_code}: {demo_res.text}"

    # 4. Access to Draft Studio / draft generation must be BLOCKED in Free Demo
    draft_res = client.post("/api/v1/documents/draft-word", json={
        "user_id": uid,
        "email": email,
        "title": "Test_Draft",
        "content": "Sample legal draft content"
    })
    assert draft_res.status_code == 403, f"Draft Studio must be blocked in Free Demo, got {draft_res.status_code}"


def test_paid_demo_plan_lifecycle_and_one_time_enforcement():
    """Verify ₹2 Paid Demo Plan gives 1 analysis, unlocks drafts, and is strictly 1-time per account."""
    uid = f"USR_PAID_DEMO_{uuid.uuid4().hex[:6]}"
    email = f"demo_advocate_{uuid.uuid4().hex[:6]}@lawfirm.in"

    # 1. Activate Paid Demo Plan (₹2 for 1 single report analysis)
    submit_res = client.post("/api/v1/admin/subscription/submit-plan", json={
        "user_id": uid,
        "email": email,
        "plan_name": "Paid Demo Plan",
        "selected_modules": ["s138"],
        "monthly_price_inr": 2.0,
        "requested_quota": 1,
        "role": "law_firm",
        "status": "PAID",
        "razorpay_payment_id": f"pay_{uuid.uuid4().hex[:10]}"
    })
    assert submit_res.status_code == 200
    data = submit_res.json()
    assert data["status"] == "ACTIVE"
    assert data["quota"]["monthly_report_limit"] == 1
    assert data["quota"]["remaining_reports"] == 1
    assert data["quota"]["paid_demo_used"] is True

    # 2. Run 1st Custom Case Analysis — Must SUCCEED on Paid Demo Plan
    analyze_payload = {
        "user_id": uid,
        "email": email,
        "case_description": "Cheque dishonoured due to funds insufficient. 15-day notice expired.",
        "cheque_amount": 100000,
        "cheque_date": "2026-05-01",
        "dishonour_date": "2026-05-10",
        "notice_date": "2026-05-20",
        "recipient_received_date": "2026-05-25",
        "complaint_date": "2026-06-15",
        "complainant_type": "company",
        "accused_type": "individual",
        "is_demo_case": False
    }
    res1 = client.post("/api/v1/analyze", json=analyze_payload)
    assert res1.status_code == 200, f"1st analysis on Paid Demo plan should succeed, got {res1.status_code}: {res1.text}"

    # 3. Quota exhausted after 1st analysis
    q_after = DatabaseManager.get_or_create_user_quota(uid, email)
    assert q_after["reports_used_this_month"] == 1
    assert q_after["remaining_reports"] == 0
    assert q_after["paid_demo_used"] is True

    # 4. 2nd custom case analysis without renewing is BLOCKED
    res2 = client.post("/api/v1/analyze", json=analyze_payload)
    assert res2.status_code == 403
    assert res2.json()["error_code"] == "QUOTA_EXCEEDED"

    # 5. Attempting to purchase / claim Paid Demo Plan a 2nd time must be REJECTED (One-time per account)
    second_demo_order = client.post("/api/v1/payments/create-order", json={
        "amount": 200,
        "user_id": uid,
        "email": email,
        "plan_name": "Paid Demo Plan",
        "is_paid_demo": True
    })
    assert second_demo_order.status_code == 400
    assert "already been claimed once" in second_demo_order.json()["detail"]

    # 6. User can still purchase standard plan (e.g. ₹499 Section 138 Plan)
    std_sub = client.post("/api/v1/admin/subscription/submit-plan", json={
        "user_id": uid,
        "email": email,
        "plan_name": "Section 138 Plan",
        "selected_modules": ["s138"],
        "monthly_price_inr": 499.0,
        "requested_quota": 25,
        "role": "law_firm",
        "status": "PAID",
        "razorpay_payment_id": f"pay_{uuid.uuid4().hex[:10]}"
    })
    assert std_sub.status_code == 200
    assert std_sub.json()["quota"]["monthly_report_limit"] == 25
    assert std_sub.json()["quota"]["remaining_reports"] == 25
