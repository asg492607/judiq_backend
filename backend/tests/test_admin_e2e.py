from fastapi.testclient import TestClient
from main import app
from session import DatabaseManager
from security import SecurityManager, is_admin_user

def test_admin_full_analysis():
    admin_email = "aixynztechnologies@judiq.ai"
    admin_user_id = "USR_ADMIN_LEGAL_01"
    
    assert is_admin_user(admin_user_id, admin_email, role="admin") is True

    client = TestClient(app)

    quota = DatabaseManager.get_or_create_user_quota(admin_user_id, admin_email, role="admin")
    assert quota.get("plan_status") == "ACTIVE"
    assert quota.get("monthly_report_limit") == -1

    payload = {
        "user_id": admin_user_id,
        "email": admin_email,
        "role": "admin",
        "case_id": "CC/2026/ADMIN_001",
        "case_title": "Apex Global Traders vs. Vanguard Tech Solutions",
        "case_type": "Cheque Bounce",
        "complainant_type": "Pvt Ltd/Ltd Company",
        "filing_date": "2026-06-15",
        "court_name": "JMFC Court, Pune",
        "condonation_attached": "No",
        "judicial_temperament": "Balanced",
        "complainant_name": "Apex Global Traders Pvt Ltd",
        "complainant_address": "Plot 12, Commercial Hub, Hinjewadi, Pune - 411057",
        "complainant_authorized": "Yes - Original",
        "authorized_person_name": "Mr. Vikram Joshi",
        "cheque_number": "489201",
        "cheque_amount": 750000,
        "cheque_date": "2026-04-10",
        "drawn_bank": "HDFC Bank",
        "drawn_branch": "Hinjewadi Pune Branch",
        "accused_account_no": "50200012345678",
        "dishonour_date": "2026-04-18",
        "dishonour_reason": "Funds Insufficient",
        "bank_memo_date": "2026-04-19",
        "bank_memo_received": "Yes - Original with Seal",
        "notice_date": "2026-04-28",
        "notice_dispatch_mode": "Registered Post AD",
        "postal_receipt_attached": "Yes",
        "recipient_received_date": "2026-05-02",
        "delivery_proof_attached": "Yes - India Post Tracking Consignment Complete",
        "accused_replied": "No",
        "debt_type": "Commercial Supply Agreement / Tax Invoices",
        "invoice_attached": "Yes - 3 Invoices with e-Way Bills",
        "part_payment_made": "No",
        "accused_name": "Mr. Rajiv Sharma",
        "accused_designation": "Managing Director",
        "accused_type": "Company Director (Vicarious Liability)",
        "company_name": "Vanguard Tech Solutions Pvt Ltd",
        "director_resigned_prior": "No",
        "form_dir12_attached": "Yes - Confirming Active Directorship on Cheque Date",
        "complaint_date": "2026-06-05"
    }

    res = client.post("/api/v1/analyze", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert data.get("success") is True or "score" in data or "data" in data

    draft_res = client.post("/api/v1/documents/draft-word", json={
        "user_id": admin_user_id,
        "email": admin_email,
        "role": "admin",
        "title": "Admin_Legal_Demand_Notice_S138",
        "content": "FORMAL DEMAND NOTICE UNDER SECTION 138 OF NI ACT...",
        "metadata": payload
    })
    assert draft_res.status_code == 200
