import pytest
from fastapi.testclient import TestClient
from main import app
from opposing_counsel_intel import OpposingCounselIntelService, OpposingCounselProfile, DefenseStrategy

client = TestClient(app)


def setup_module():
    # Register a verified test profile dynamically
    test_profile = OpposingCounselProfile(
        counsel_id="ADV_TEST_01",
        name="Counsel Chamber Delhi",
        bar_council_id="BAR/DEL/TEST/01",
        primary_jurisdiction="Delhi High Court & Tis Hazari Courts",
        practice_areas=["Section 138 NI Act Defense"],
        defense_win_rate=65.0,
        signature_defense_strategies=[
            DefenseStrategy(
                strategy_name="Security Cheque Misuse Defense",
                frequency_percentage=80,
                precedent_relied="Sunil Todi v. State of Gujarat (2021)",
                typical_trigger="Security cheques",
                effectiveness_rating="HIGH",
                prosecution_counter_tactic="Prove debt crystallized prior to presentation."
            )
        ]
    )
    OpposingCounselIntelService.register_counsel_profile(test_profile)


def test_list_opposing_counsel():
    res = client.get("/api/v1/intel/counsel")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "counsel" in data


def test_filter_opposing_counsel_by_jurisdiction():
    res = client.get("/api/v1/intel/counsel?jurisdiction=Delhi")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True


def test_get_counsel_detail():
    res = client.get("/api/v1/intel/counsel/ADV_TEST_01")
    assert res.status_code == 200
    data = res.json()
    assert data["counsel_id"] == "ADV_TEST_01"
    assert data["defense_win_rate"] == 65.0
    assert len(data["signature_defense_strategies"]) >= 1


def test_get_counsel_detail_not_found():
    res = client.get("/api/v1/intel/counsel/ADV_NON_EXISTENT")
    assert res.status_code == 404


def test_analyze_counsel_matchup():
    payload = {
        "counsel_id_or_name": "Counsel Chamber Delhi",
        "case_facts": {
            "amount": 2500000.0,
            "cheque_type": "Security",
            "is_corporate": True
        },
        "presiding_judge_or_court": "Metropolitan Magistrate Special NI Court",
        "dispute_type": "SECTION_138"
    }
    res = client.post("/api/v1/intel/counsel/analyze-matchup", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["threat_level"] in ["SEVERE", "HIGH", "MODERATE", "LOW"]
    assert len(data["predicted_top_defenses"]) >= 1
    assert len(data["tactical_road_map"]) >= 3
    assert len(data["recommended_precedents_to_cite"]) >= 2
    assert "Rangappa" in str(data["recommended_precedents_to_cite"])


def test_contribute_counsel_intel():
    payload = {
        "counsel_name": "Senior Defense Advocate",
        "bar_council_id": "BAR/TEST/2026",
        "court_jurisdiction": "City Civil and Sessions Court",
        "defense_strategy_observed": "Invokes Section 143A financial hardship objection at notice framing stage",
        "precedent_used": "Noor Mohammed v. Khurram Pasha (2022)",
        "case_outcome": "SETTLED",
        "contributor_designation": "Advocate"
    }
    res = client.post("/api/v1/intel/counsel/contribute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "REGISTERED_IN_COMMUNITY_INTEL"
