import pytest
import os
from session import DatabaseManager
from security import SecurityManager, is_admin_user
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    DatabaseManager.init_db()
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_quotas WHERE user_id LIKE 'test_%' OR user_id LIKE 'client_test_%'")
    conn.commit()
    conn.close()

def test_admin_recognition():
    assert is_admin_user("admin@judiq.ai") is True
    assert is_admin_user("gandhiatharv565@gmail.com") is True
    assert is_admin_user("user_12345", "admin@judiq.ai") is True
    assert is_admin_user("random_litigator@lawfirm.com") is False

def test_quota_lifecycle():
    user_id = "test_user_quota_101"
    email = "counsel_rajesh@law.com"

    # 1. Get or create quota
    q = DatabaseManager.get_or_create_user_quota(user_id, email, default_limit=10)
    assert q["user_id"] == user_id
    assert q["monthly_report_limit"] == 10
    assert q["reports_used_this_month"] == 0
    assert q["remaining_reports"] == 10

    # 2. Consume quota
    res1 = DatabaseManager.check_and_consume_report_quota(user_id, email, cost=3)
    assert res1["allowed"] is True
    assert res1["quota"]["reports_used_this_month"] == 3
    assert res1["quota"]["remaining_reports"] == 7

    # 3. Update quota limit via admin method
    ok = DatabaseManager.update_user_quota_allocation(user_id, monthly_limit=20)
    assert ok is True
    q_updated = DatabaseManager.get_or_create_user_quota(user_id)
    assert q_updated["monthly_report_limit"] == 20
    assert q_updated["remaining_reports"] == 17

    # 4. Reset monthly usage
    ok_reset = DatabaseManager.reset_user_monthly_usage(user_id)
    assert ok_reset is True
    q_reset = DatabaseManager.get_or_create_user_quota(user_id)
    assert q_reset["reports_used_this_month"] == 0
    assert q_reset["remaining_reports"] == 20

def test_quota_exhaustion():
    user_id = "test_user_exhaust_202"
    email = "counsel_exhaust@law.com"

    # Set limit to 2
    DatabaseManager.update_user_quota_allocation(user_id, monthly_limit=2, email=email)
    
    # Consume 2
    res1 = DatabaseManager.check_and_consume_report_quota(user_id, email, cost=2)
    assert res1["allowed"] is True

    # Try consuming 1 more -> Quota Exceeded
    res2 = DatabaseManager.check_and_consume_report_quota(user_id, email, cost=1)
    assert res2["allowed"] is False
    assert res2["reason"] == "QUOTA_EXCEEDED"

def test_user_suspension():
    user_id = "test_user_suspended_303"
    DatabaseManager.update_user_quota_allocation(user_id, is_active=False)

    res = DatabaseManager.check_and_consume_report_quota(user_id)
    assert res["allowed"] is False
    assert res["reason"] == "USER_SUSPENDED"

def test_admin_api_endpoints_protection():
    # 1. Non-admin or unauthenticated access to /api/v1/admin/users
    resp_unauth = client.get("/api/v1/admin/users")
    assert resp_unauth.status_code == 401

    # 2. Token for regular user
    user_token = SecurityManager.create_access_token({"sub": "user_regular_404", "email": "regular@law.com", "role": "user"})
    resp_forbidden = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert resp_forbidden.status_code == 403

    # 3. Token for Admin
    admin_token = SecurityManager.create_access_token({"sub": "admin@judiq.ai", "email": "admin@judiq.ai", "role": "admin"})
    resp_admin = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert data["success"] is True
    assert "users" in data

    # 4. Admin allocate quota endpoint
    resp_alloc = client.post("/api/v1/admin/users/allocate", 
                             json={"user_id": "client_test_505", "monthly_limit": 50, "email": "advocate_505@law.com"},
                             headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_alloc.status_code == 200
    assert resp_alloc.json()["success"] is True
    assert resp_alloc.json()["quota"]["monthly_report_limit"] == 50

    # 5. User Quota endpoint
    resp_quota = client.get("/api/v1/user/quota?user_id=client_test_505")
    assert resp_quota.status_code == 200
    assert resp_quota.json()["quota"]["monthly_report_limit"] == 50
