import pytest
from engine_core import JudiQEngine
from sarfaesi_timeline_engine import SarfaesiTimelineEngine
from sarfaesi_scoring_engine import SarfaesiScoringEngine
from sarfaesi_adversarial_engine import SarfaesiAdversarialEngine
from draft_engine import DraftEngine

def test_sarfaesi_timeline_limitation_compliant():
    case_data = {
        "npa_date": "2026-01-01",
        "notice_13_2_date": "2026-01-15",
        "borrower_representation_date": "2026-02-01",
        "bank_reply_13_3a_date": "2026-02-10",
        "possession_13_4_date": "2026-03-20",
        "sa_filing_date": "2026-04-10"
    }
    limitation = SarfaesiTimelineEngine.check_limitation(case_data)
    assert limitation["status"] == "COMPLIANT"
    assert not limitation["is_barred"]

def test_sarfaesi_timeline_limitation_13_3a_breach():
    # Bank delays reply beyond 15 days (takes 25 days)
    case_data = {
        "npa_date": "2026-01-01",
        "notice_13_2_date": "2026-01-15",
        "borrower_representation_date": "2026-02-01",
        "bank_reply_13_3a_date": "2026-02-26",
        "possession_13_4_date": "2026-03-20"
    }
    limitation = SarfaesiTimelineEngine.check_limitation(case_data)
    assert limitation["status"] == "BREACHED"
    assert limitation["is_barred"]
    assert "SECTION_13_3A_BREACH" in limitation["fatal_defect"]

def test_sarfaesi_scoring_cersai_missing():
    case_data = {
        "case_type": "sarfaesi",
        "perspective": "creditor",
        "cersai_registered": False
    }
    res = SarfaesiScoringEngine.calculate_score(case_data)
    assert res["fatal_defect"] is not None
    assert "NON_REGISTRATION_CERSAI" in res["fatal_defect"]

def test_sarfaesi_scoring_agricultural_land():
    case_data = {
        "case_type": "sarfaesi",
        "perspective": "borrower",
        "is_agricultural_land": True
    }
    res = SarfaesiScoringEngine.calculate_score(case_data)
    assert res["score"] >= 80  # Borrower defense strong due to Section 31(i) exemption

def test_sarfaesi_adversarial_audit():
    case_data = {
        "case_type": "sarfaesi",
        "perspective": "creditor",
        "cersai_registered": False,
        "is_agricultural_land": True
    }
    res = SarfaesiAdversarialEngine.audit_case(case_data)
    assert len(res["risks_and_rebuttals"]) >= 2
    vectors = [r["adversarial_vector"] for r in res["risks_and_rebuttals"]]
    assert any("CERSAI" in v for v in vectors)
    assert any("Agricultural" in v for v in vectors)

def test_judiq_engine_sarfaesi_end_to_end():
    case_data = {
        "case_id": "SARFAESI-2026-TEST",
        "case_type": "sarfaesi",
        "perspective": "creditor",
        "borrower_name": "M/s Alpha Logistics Pvt Ltd",
        "bank_name": "State Bank of India",
        "loan_account_number": "LOAN-998877",
        "outstanding_amount": 15000000.0,
        "npa_date": "2026-01-01",
        "cersai_registered": True,
        "is_agricultural_land": False,
        "description": "Default in commercial loan facility of Rs 1.5 Crores. Account classified as NPA."
    }
    result = JudiQEngine.analyze_case(case_data)
    assert result is not None
    assert "final_score" in result or "score" in result
    assert result.get("draft") is not None
    assert "DEMAND NOTICE UNDER SECTION 13(2)" in result["draft"]
