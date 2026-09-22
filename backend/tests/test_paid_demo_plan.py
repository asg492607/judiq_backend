import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from session import DatabaseManager

client = TestClient(app)

def test_free_demo_mode_3_reports_and_free_drafts():
    """Verify Free Demo mode: 3 free reports for custom/demo cases, free drafts, quota exhaustion on 4th run."""
    uid = f"USR_FREE_DEMO_{uuid.uuid4().hex[:6]}"
    email = f"free_demo_{uuid.uuid4().hex[:6]}@lawfirm.in"

    # 1. New user starts in Free Demo with 3 free reports
    q = DatabaseManager.get_or_create_user_quota(uid, email)
    assert q["monthly_report_limit"] == 3
    assert q["remaining_reports"] == 3
    assert q["reports_used_this_month"] == 0
    assert q["is_active"] is True
    assert q["plan_status"] == "ACTIVE"

    # 2. Draft Studio (Word & PDF) is completely FREE and unblocked
    draft_word_res = client.post("/api/v1/documents/draft-word", json={
        "user_id": uid,
        "email": email,
        "title": "Free_Notice_Draft",
        "content": "Sample legal notice content for Section 138"
    })
    assert draft_word_res.status_code == 200, f"Draft Word must succeed freely, got {draft_word_res.status_code}"
    assert len(draft_word_res.content) > 0

    draft_pdf_res = client.post("/api/v1/documents/draft-pdf", json={
        "user_id": uid,
        "email": email,
        "title": "Free_Notice_PDF",
        "content": "Sample legal notice content in PDF format"
    })
    assert draft_pdf_res.status_code == 200, f"Draft PDF must succeed freely, got {draft_pdf_res.status_code}"

    # Draft generation does not consume report quota
    q_after_draft = DatabaseManager.get_or_create_user_quota(uid, email)
    assert q_after_draft["remaining_reports"] == 3

    # 3. User can run 3 Custom Case Analyses (Fully editable / custom payloads)
    for i in range(1, 4):
        custom_payload = {
            "user_id": uid,
            "email": email,
            "case_description": f"Custom cheque bounce case number {i}.",
            "cheque_amount": 100000 * i,
            "cheque_date": "2026-05-01",
            "dishonour_date": "2026-05-10",
            "notice_date": "2026-05-20",
            "recipient_received_date": "2026-05-25",
            "complaint_date": "2026-06-15",
            "complainant_type": "company",
            "accused_type": "individual",
            "is_demo_case": False
        }
        res = client.post("/api/v1/analyze", json=custom_payload)
        assert res.status_code == 200, f"Custom analysis #{i} on Free Demo should succeed, got {res.status_code}: {res.text}"

    # 4. Quota check after 3 analyses: 3 used, 0 remaining
    q_used = DatabaseManager.get_or_create_user_quota(uid, email)
    assert q_used["reports_used_this_month"] == 3
    assert q_used["remaining_reports"] == 0

    # 5. 4th analysis attempt is BLOCKED with QUOTA_EXCEEDED
    fourth_payload = {
        "user_id": uid,
        "email": email,
        "case_description": "Fourth analysis attempt exceeding free demo limit.",
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
    res4 = client.post("/api/v1/analyze", json=fourth_payload)
    assert res4.status_code == 403
    assert res4.json()["error_code"] == "QUOTA_EXCEEDED"
    assert "Free demo" in res4.json()["error"] or "limit reached" in res4.json()["error"]

    # 6. User can upgrade to a standard subscription plan (e.g. Section 138 Plan)
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

    # 7. Analysis now SUCCEEDS again with renewed subscription
    res_sub = client.post("/api/v1/analyze", json=fourth_payload)
    assert res_sub.status_code == 200
