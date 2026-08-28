import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# --------------------------------------------------------------------------
# ANALYTICS DASHBOARD TESTS
# --------------------------------------------------------------------------
def test_analytics_dashboard_executive_metrics():
    res = client.get("/api/v1/analytics/executive")
    assert res.status_code == 200
    data = res.json()
    assert "firm_name" in data
    assert data["total_cases_analyzed"] >= 500
    assert data["overall_mean_compliance_score"] > 80.0
    assert len(data["portfolio_tier_breakdown"]) == 5
    assert len(data["monthly_trends"]) >= 6
    assert len(data["judge_benchmark_patterns"]) >= 3
    assert "estimated_legal_hours_saved" in data["roi_summary"]


# --------------------------------------------------------------------------
# CLIENT PORTAL TESTS
# --------------------------------------------------------------------------
def test_client_portal_get_case_dossier():
    res = client.get("/api/v1/portal/case/CLIENT_TKN_2026_01")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "CC-BLR-2026-8912"
    assert "Sunrise Logistics" in data["case_title"]
    assert len(data["milestones"]) >= 5
    assert len(data["document_checklist"]) >= 4
    assert data["claim_amount"] == 2450000.0


def test_client_portal_invalid_token():
    res = client.get("/api/v1/portal/case/INVALID_TOKEN_999")
    assert res.status_code == 404


def test_client_portal_document_upload():
    payload = {
        "document_id": "DOC_04",
        "file_name": "signed_custodian_affidavit.pdf"
    }
    res = client.post("/api/v1/portal/case/CLIENT_TKN_2026_01/upload-document", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "UPLOADED_PENDING_REVIEW"


# --------------------------------------------------------------------------
# DEADLINE TRACKER & ICALENDAR TESTS
# --------------------------------------------------------------------------
def test_deadline_tracker_section138_calculation():
    payload = {
        "case_reference": "SBI/BLR/S138/009",
        "borrower_or_accused_name": "Horizon Infra Pvt Ltd",
        "dispute_type": "SECTION_138",
        "dishonour_memo_date": "2026-08-10",
        "notice_received_date": "2026-08-20"
    }
    res = client.post("/api/v1/deadlines/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["case_reference"] == "SBI/BLR/S138/009"
    assert len(data["deadlines"]) >= 2
    assert any("Statutory Demand Notice" in d["title"] for d in data["deadlines"])
    assert any("Complaint" in d["title"] for d in data["deadlines"])
    assert ".ics" in data["ical_export_url"]


def test_deadline_tracker_sarfaesi_calculation():
    payload = {
        "case_reference": "HDFC/MUM/SARF/102",
        "borrower_or_accused_name": "Marvel Realty",
        "dispute_type": "SARFAESI",
        "section_13_2_notice_date": "2026-07-01",
        "borrower_representation_date": "2026-07-20"
    }
    res = client.post("/api/v1/deadlines/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert any("60-Day" in d["title"] for d in data["deadlines"])
    assert any("13(3A)" in d["title"] for d in data["deadlines"])


def test_deadline_ical_export_download():
    res = client.get("/api/v1/deadlines/SBI_BLR_S138_009/calendar.ics")
    assert res.status_code == 200
    assert "text/calendar" in res.headers["content-type"]
    text = res.text
    assert "BEGIN:VCALENDAR" in text
    assert "END:VCALENDAR" in text
    assert "BEGIN:VEVENT" in text
    assert "VALARM" in text
