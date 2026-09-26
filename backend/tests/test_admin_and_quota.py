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
    assert is_admin_user("aixynztechnologies") is True
    assert is_admin_user("aixynztechnologies@gmail.com") is True
    assert is_admin_user("user_12345", "aixynztechnologies@judiq.ai") is True
    assert is_admin_user("admin@judiq.ai") is True
    assert is_admin_user("admin") is True
    assert is_admin_user("user_custom", role="admin") is True
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
    admin_token = SecurityManager.create_access_token({"sub": "aixynztechnologies", "email": "aixynztechnologies@judiq.ai", "role": "admin"})
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

def test_admin_password_verification():
    # 1. Correct email and correct password
    resp_ok = client.post("/api/v1/admin/auth/verify", json={"email": "aixynztechnologies", "password": "asg@492607"})
    assert resp_ok.status_code == 200
    data_ok = resp_ok.json()
    assert data_ok["success"] is True
    assert data_ok["is_admin"] is True
    assert "token" in data_ok

    # 2. Correct email and wrong password
    resp_wrong = client.post("/api/v1/admin/auth/verify", json={"email": "aixynztechnologies", "password": "wrong_password"})
    assert resp_wrong.status_code == 200
    assert resp_wrong.json()["success"] is False
    assert resp_wrong.json()["is_admin"] is False

    # 3. Non-admin email
    resp_non_admin = client.post("/api/v1/admin/auth/verify", json={"email": "unauthorized@law.com", "password": "asg@492607"})
    assert resp_non_admin.status_code == 200
    assert resp_non_admin.json()["success"] is False

def test_subscription_validity_dates():
    # 1. Standard user quota contains starting and ending dates
    user_id = "test_sub_validity_701"
    email = "counsel_validity@law.com"
    q = DatabaseManager.get_or_create_user_quota(user_id, email, default_limit=10)
    assert "subscription_start_date" in q
    assert "subscription_end_date" in q
    assert q["subscription_start_date"] is not None
    assert q["subscription_end_date"] is not None
    assert q["days_remaining"] >= 28

    # 2. Admin user validity is Lifetime
    admin_q = DatabaseManager.get_or_create_user_quota("test_admin_sub", "aixynztechnologies@judiq.ai", role="admin")
    assert admin_q["subscription_end_date"] == "Lifetime"
    assert admin_q["is_lifetime"] is True
    assert admin_q["days_remaining"] == -1

    # 3. Submitting subscription plan sets starting and ending dates
    sub_res = DatabaseManager.submit_subscription_plan(
        user_id=user_id,
        email=email,
        selected_modules=["s138"],
        monthly_price_inr=999.0,
        requested_quota=25,
        status="ACTIVE",
        plan_name="Standard Monthly Plan"
    )
    assert sub_res["subscription_start_date"] is not None
    assert sub_res["subscription_end_date"] is not None
    assert sub_res["days_remaining"] >= 28

    # 4. User quota API endpoint returns subscription validity dates
    resp = client.get(f"/api/v1/user/quota?user_id={user_id}&email={email}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "subscription_start_date" in data["quota"]
    assert "subscription_end_date" in data["quota"]
    assert data["quota"]["subscription_start_date"] is not None
    assert data["quota"]["subscription_end_date"] is not None


