import pytest
from fastapi.testclient import TestClient
from session import DatabaseManager
from security import SecurityManager
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    DatabaseManager.init_db()

def test_deployment_alert_database_crud():
    # 1. Verify seeded or retrieved deployment alert
    alert = DatabaseManager.get_deployment_alert()
    assert alert is not None
    assert alert["id"] == "primary_deployment_alert"
    assert "version_tag" in alert
    assert "scheduled_time" in alert

    # 2. Update deployment alert
    updated = DatabaseManager.set_deployment_alert(
        title="Scheduled Core System Upgrade v2.5.0",
        message="JudIQ AI is upgrading its statutory validation engines. Please save all work.",
        alert_type="VERSION_RELEASE",
        version_tag="v2.5.0",
        scheduled_time="Sunday, 28 Sep 2026, 02:00 AM IST",
        estimated_duration="30 minutes",
        affected_services="Draft Studio, AI Analysis Engine & Cloud Sync",
        is_active=True
    )
    assert updated is not None
    assert updated["title"] == "Scheduled Core System Upgrade v2.5.0"
    assert updated["alert_type"] == "VERSION_RELEASE"
    assert updated["version_tag"] == "v2.5.0"
    assert updated["scheduled_time"] == "Sunday, 28 Sep 2026, 02:00 AM IST"
    assert updated["estimated_duration"] == "30 minutes"
    assert updated["is_active"] is True

    # 3. Toggle deployment alert to inactive
    toggled_off = DatabaseManager.toggle_deployment_alert(is_active=False)
    assert toggled_off is not None
    assert toggled_off["is_active"] is False

    # 4. Toggle back to active
    toggled_on = DatabaseManager.toggle_deployment_alert(is_active=True)
    assert toggled_on is not None
    assert toggled_on["is_active"] is True


def test_public_deployment_alert_api():
    # The public endpoint should be accessible without any credentials
    response = client.get("/api/v1/system/deployment-alert")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "alert" in data
    assert data["alert"]["id"] == "primary_deployment_alert"


def test_admin_deployment_alert_endpoints_authorization():
    # 1. Unauthenticated post should be rejected
    payload = {
        "title": "Unauthorized Alert Attempt",
        "message": "This should fail",
        "alert_type": "CRITICAL_WARNING",
        "version_tag": "v2.5.1",
        "scheduled_time": "Now",
        "estimated_duration": "10 minutes",
        "affected_services": "All",
        "is_active": True
    }
    unauth_resp = client.post("/api/v1/admin/system/deployment-alert", json=payload)
    assert unauth_resp.status_code in [401, 403]

    # 2. Authenticated non-admin user should also be rejected
    user_token = SecurityManager.create_access_token(data={"sub": "advocate_sharma", "email": "advocate_sharma@law.com", "role": "citizen"})
    forbidden_resp = client.post(
        "/api/v1/admin/system/deployment-alert",
        headers={"Authorization": f"Bearer {user_token}"},
        json=payload
    )
    assert forbidden_resp.status_code == 403

    # 3. Authenticated admin should successfully configure the alert
    admin_token = SecurityManager.create_access_token(data={"sub": "aixynztechnologies@gmail.com", "email": "aixynztechnologies@gmail.com", "role": "admin"})
    admin_resp = client.post(
        "/api/v1/admin/system/deployment-alert",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "JudIQ AI v2.5.0 Production Deployment",
            "message": "Scheduled core engine rollout. Please download pending exports before 02:00 AM IST.",
            "alert_type": "DEPLOYMENT",
            "version_tag": "v2.5.0",
            "scheduled_time": "Sunday, 28 Sep 2026, 02:00 AM IST",
            "estimated_duration": "25 minutes",
            "affected_services": "Draft Studio, AI Analysis Engine & Cloud Sync",
            "is_active": True
        }
    )
    assert admin_resp.status_code == 200
    res_data = admin_resp.json()
    assert res_data["success"] is True
    assert res_data["alert"]["version_tag"] == "v2.5.0"
    assert res_data["alert"]["title"] == "JudIQ AI v2.5.0 Production Deployment"

    # 4. Toggle via admin endpoint
    toggle_resp = client.post(
        "/api/v1/admin/system/deployment-alert/toggle",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": False}
    )
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["alert"]["is_active"] is False

    # 5. Public endpoint reflects the updated inactive status
    pub_resp = client.get("/api/v1/system/deployment-alert")
    assert pub_resp.status_code == 200
    assert pub_resp.json()["alert"]["is_active"] is False

    # Re-enable so the alert banner is active for live deployment
    re_enable = client.post(
        "/api/v1/admin/system/deployment-alert/toggle",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": True}
    )
    assert re_enable.status_code == 200
    assert re_enable.json()["alert"]["is_active"] is True
