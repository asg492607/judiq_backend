import pytest
from fastapi.testclient import TestClient
from main import app
from opposing_counsel_intel import OpposingCounselIntelService

client = TestClient(app)


def test_list_opposing_counsel():
    res = client.get("/api/v1/intel/counsel")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total"] >= 3
    names = [c["name"] for c in data["counsel"]]
    assert any("Grover" in n for n in names)
    assert any("Merchant" in n for n in names)
    assert any("Iyer" in n for n in names)


def test_filter_opposing_counsel_by_jurisdiction():
    res = client.get("/api/v1/intel/counsel?jurisdiction=Delhi")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert any("Grover" in c["name"] for c in data["counsel"])


def test_get_counsel_detail():
    res = client.get("/api/v1/intel/counsel/ADV_DEL_DEF_01")
    assert res.status_code == 200
    data = res.json()
    assert data["counsel_id"] == "ADV_DEL_DEF_01"
    assert data["defense_win_rate"] > 60.0
    assert len(data["signature_defense_strategies"]) >= 2
    assert any("Security Cheque" in s["strategy_name"] for s in data["signature_defense_strategies"])
    assert len(data["judge_track_record"]) >= 1


def test_get_counsel_detail_not_found():
    res = client.get("/api/v1/intel/counsel/ADV_NON_EXISTENT")
    assert res.status_code == 404


def test_analyze_counsel_matchup():
    payload = {
        "counsel_id_or_name": "Adv. Rameshwar V. Grover",
        "case_facts": {
            "amount": 2500000.0,
            "cheque_type": "Security",
            "is_corporate": True
        },
        "presiding_judge_or_court": "Tis Hazari Court (Magistrate Special NI Court)",
        "dispute_type": "SECTION_138"
    }
    res = client.post("/api/v1/intel/counsel/analyze-matchup", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["threat_level"] in ["SEVERE", "HIGH", "MODERATE"]
    assert len(data["predicted_top_defenses"]) >= 2
    assert len(data["tactical_road_map"]) >= 3
    assert len(data["recommended_precedents_to_cite"]) >= 2
    assert "Rangappa" in str(data["recommended_precedents_to_cite"])


def test_contribute_counsel_intel():
    payload = {
        "counsel_name": "Adv. Vikram Sethi",
        "bar_council_id": "D/9912/2015",
        "court_jurisdiction": "Patiala House Courts, New Delhi",
        "defense_strategy_observed": "Invokes Section 143A financial hardship objection at notice framing stage",
        "precedent_used": "Noor Mohammed v. Khurram Pasha (2022)",
        "judge_name": "Metropolitan Magistrate NI Court 02",
        "case_outcome": "SETTLED",
        "contributor_designation": "Senior Associate"
    }
    res = client.post("/api/v1/intel/counsel/contribute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "QUEUED_FOR_PEER_VERIFICATION"
    assert "CONTRIB_" in data["contribution_id"]
