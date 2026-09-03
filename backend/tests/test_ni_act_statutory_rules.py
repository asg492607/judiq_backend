"""
Unit tests for Section 138 NI Act Statutory Rules and Defense Matrix.
"""

import pytest
from cheque_bounce.ni_act_statutory_rules import NIActStatutoryRules
from cheque_bounce.defence_catalogue import Section138DefenceCatalogue
from cheque_bounce.cheque_bounce_engine import ChequeBounceEngine

def test_notice_timeline_valid():
    res = NIActStatutoryRules.evaluate_notice_timeline(15)
    assert res["valid"] is True
    assert res["defect"] is None

def test_notice_timeline_delayed():
    res = NIActStatutoryRules.evaluate_notice_timeline(35)
    assert res["valid"] is False
    assert "35" in res["defect"]
    assert res["fatal"] is True

def test_complaint_timeline_premature():
    res = NIActStatutoryRules.evaluate_complaint_timeline(10)
    assert res["valid"] is False
    assert "prematurely" in res["defect"].lower() or "premature" in res["defect"].lower()

def test_complaint_timeline_delayed():
    res = NIActStatutoryRules.evaluate_complaint_timeline(50)
    assert res["valid"] is False
    assert "delayed by 5 days" in res["defect"]

def test_cheque_validity_rbi_90_days():
    res_valid = NIActStatutoryRules.evaluate_cheque_validity("2026-01-01", "2026-03-01")
    assert res_valid["valid"] is True

    res_stale = NIActStatutoryRules.evaluate_cheque_validity("2026-01-01", "2026-05-15")
    assert res_stale["valid"] is False
    assert res_stale["fatal"] is True
    assert "stale" in res_stale["defect"].lower()

def test_s142_territorial_jurisdiction():
    res = NIActStatutoryRules.evaluate_s142_jurisdiction(payee_branch="Nariman Point, Mumbai", presentation_mode="account_collection")
    assert "Payee's Bank Branch" in res["competent_jurisdiction"]
    assert "Bridgestone India" in res["governing_precedent"]

def test_vicarious_liability_missing_company():
    res = NIActStatutoryRules.evaluate_vicarious_liability("Pvt Ltd", company_arrayed=False, directors_named=True)
    assert res["valid"] is False
    assert "Aneeta Hada" in res["defect"]

def test_interim_compensation_and_appellate_deposit():
    comp = NIActStatutoryRules.calculate_interim_compensation_estimate(500000.0)
    assert comp == 100000.0  # 20% of 5 Lakhs
    app_dep = NIActStatutoryRules.calculate_appellate_deposit_estimate(500000.0)
    assert app_dep == 100000.0  # 20% minimum under Sec 148

def test_defence_catalogue_lookup():
    sec_def = Section138DefenceCatalogue.get_defense_intel("security_cheque")
    assert sec_def["name"] == "Security Cheque Defense"
    assert "Sunil Todi" in sec_def["key_precedent"]

def test_cheque_bounce_engine_full_analysis():
    case = {
        "case_type": "cheque_bounce",
        "cheque_amount": 250000,
        "date_of_dishonour": "2026-05-01",
        "date_of_notice": "2026-05-15",
        "date_of_complaint": "2026-06-10",
        "branch_name": "Fort, Mumbai",
        "is_security_cheque": True
    }
    result = ChequeBounceEngine.analyze(case)
    assert result["domain"] == "cheque_bounce"
    assert result["interim_compensation_estimate"] == 50000.0
    assert result["appellate_deposit_estimate"] == 50000.0
    assert len(result["identified_defenses"]) >= 1
    assert result["identified_defenses"][0]["name"] == "Security Cheque Defense"
    assert "procedural_graph" in result
    assert result["procedural_graph"]["total_nodes"] == 6
    assert "territorial_jurisdiction_rule" in result
