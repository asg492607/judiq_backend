import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_share_report_generation_and_view():
    payload = {
        "case_id": "TEST_CASE_138_001",
        "user_id": "TEST_USER_99",
        "title": "Rajesh Sharma vs ABC Corp",
        "domain": "ni_act",
        "case_data": {
            "complainant_name": "Rajesh Sharma",
            "accused_name": "ABC Corp",
            "cheque_amount": 250000
        },
        "analysis_result": {
            "score": 92,
            "verdict": "STRONG_CASE",
            "summary": "Valid Section 138 cause of action."
        }
    }

    # 1. Create shared report
    res = client.post("/api/v1/reports/share", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert "share_id" in data
    share_id = data["share_id"]

    # 2. Retrieve public shared report
    get_res = client.get(f"/api/v1/reports/shared/{share_id}")
    assert get_res.status_code == 200
    report_data = get_res.json()
    assert report_data["success"] is True
    assert report_data["is_protected"] is False
    assert report_data["case_data"]["complainant_name"] == "Rajesh Sharma"

def test_password_protected_shared_report():
    payload = {
        "case_id": "SECURE_CASE_138",
        "title": "Confidential Litigation Report",
        "password": "SecretPassword123!",
        "case_data": {"case_caption": "Bank vs Borrower"},
        "analysis_result": {"score": 88}
    }

    # 1. Create password-protected shared report
    res = client.post("/api/v1/reports/share", json=payload)
    assert res.status_code == 200
    share_id = res.json()["share_id"]
    assert res.json()["is_protected"] is True

    # 2. Get without password — must NOT return private analysis data
    get_res = client.get(f"/api/v1/reports/shared/{share_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["is_protected"] is True
    assert "case_data" not in data or data["case_data"] is None

    # 3. Verify with wrong password — must fail
    wrong_pwd_res = client.post(f"/api/v1/reports/shared/{share_id}/verify", json={"password": "WrongPassword"})
    assert wrong_pwd_res.status_code == 401

    # 4. Verify with correct password — must succeed and return report data
    correct_pwd_res = client.post(f"/api/v1/reports/shared/{share_id}/verify", json={"password": "SecretPassword123!"})
    assert correct_pwd_res.status_code == 200
    unlocked_data = correct_pwd_res.json()
    assert unlocked_data["success"] is True
    assert unlocked_data["case_data"]["case_caption"] == "Bank vs Borrower"
