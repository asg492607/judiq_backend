import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_simulate_strategy_endpoint():
    response = client.post(
        "/api/v1/analyze/simulate",
        json={
            "preset": "s138_signature",
            "notice_delay_days": 12,
            "signature_disputed": True,
            "security_cheque": False,
            "evidence_65b": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "survivability_score" in data
    assert "risk_level" in data
    assert "primary_attack_vector" in data
    assert "recommended_counter_strategy" in data
