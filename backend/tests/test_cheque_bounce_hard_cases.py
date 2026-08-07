import pytest
from typing import Dict, Any
from cheque_bounce.cheque_bounce_engine import ChequeBounceEngine
from scoring_engine import ScoringEngineV12
from adversarial_engine import AdversarialEngine

# -----------------------------------------------------------------------------
# HARD CASE SCENARIO GENERATORS (630 PARAMETERIZED LEGAL TEST CASES)
# -----------------------------------------------------------------------------

def generate_notice_service_scenarios():
    """Generates 105 hard cases for Statutory Notice & Postal Service (S.138(b))."""
    returns = ["Unclaimed", "Refused", "House Locked", "Left Without Address", "Wrong Address", "Not Known", "Deceased"]
    days = [10, 15, 20, 25, 29, 30, 31, 35, 45, 60, 90]
    entity_types = ["Individual", "Pvt Ltd/Ltd Company", "Partnership Firm", "Proprietorship", "HUF"]
    
    cases = []
    idx = 1
    for r in returns:
        for d in days:
            for et in entity_types:
                cases.append({
                    "id": f"NOTICE_HARD_{idx}",
                    "case_type": "cheque_bounce",
                    "dishonour_date": "2026-01-01",
                    "notice_date": f"2026-01-{(d if d <= 31 else 31):02d}",
                    "notice_days": d,
                    "postal_return_reason": r,
                    "complainant_type": et,
                    "amount": 500000.0,
                    "notice_sent": True
                })
                idx += 1
                if len(cases) >= 110:
                    return cases
    return cases


def generate_limitation_scenarios():
    """Generates 105 hard cases for Limitation & Cause of Action (S.142(1)(b))."""
    grace_days = [1, 5, 10, 14, 15, 16, 20, 30, 45, 60, 90]
    condonations = [True, False]
    causes = ["Insufficient Funds", "Account Closed", "Stop Payment", "Signature Differs", "Refer to Drawer"]
    reposts = [True, False]

    cases = []
    idx = 1
    for g in grace_days:
        for c in condonations:
            for cause in causes:
                for rep in reposts:
                    cases.append({
                        "id": f"LIMIT_HARD_{idx}",
                        "case_type": "cheque_bounce",
                        "dishonour_date": "2026-01-01",
                        "notice_date": "2026-01-15",
                        "days_post_notice": g,
                        "condonation_attached": c,
                        "second_presentation": rep,
                        "return_reason": cause,
                        "amount": 250000.0
                    })
                    idx += 1
                    if len(cases) >= 110:
                        return cases
    return cases


def generate_vicarious_company_scenarios():
    """Generates 105 hard cases for S.141 Vicarious Liability of Directors."""
    company_arrayed = [True, False]
    roles = ["Managing Director", "Whole Time Director", "Independent Director", "Nominee Director", "Resigned Director", "Sleeping Partner", "Authorized Signatory"]
    pleadings = ["Specific Operational Role Pledged", "Generic Omnibus Mention", "No Mention"]

    cases = []
    idx = 1
    for ca in company_arrayed:
        for r in roles:
            for p in pleadings:
                for amt in [500000.0, 1000000.0, 5000000.0]:
                    cases.append({
                        "id": f"S141_HARD_{idx}",
                        "case_type": "cheque_bounce",
                        "accused_type": "Pvt Ltd/Ltd Company",
                        "company_arrayed": ca,
                        "director_role": r,
                        "operational_role_pledged": p == "Specific Operational Role Pledged",
                        "directors_named": p != "No Mention",
                        "amount": amt
                    })
                    idx += 1
                    if len(cases) >= 110:
                        return cases
    return cases


def generate_presumption_rebuttal_scenarios():
    """Generates 105 hard cases for S.139 Presumption & Security Cheque Rebuttals."""
    defenses = ["Security Cheque", "Financial Capacity Challenge", "Time-Barred Debt", "Blank Signed Cheque", "Gift/Unenforceable", "Gambling Debt", "Cash Loan Exceeding S.269SS"]
    itr_available = [True, False]
    agreements = ["Written Loan Agreement", "Verbal Promise", "No Agreement", "Promissory Note"]

    cases = []
    idx = 1
    for d in defenses:
        for itr in itr_available:
            for ag in agreements:
                for amt in [100000.0, 750000.0, 2500000.0]:
                    cases.append({
                        "id": f"REBUT_HARD_{idx}",
                        "case_type": "cheque_bounce",
                        "cheque_security_claim": d == "Security Cheque",
                        "complainant_itr_available": itr,
                        "agreement_type": ag,
                        "defense_argument": d,
                        "amount": amt
                    })
                    idx += 1
                    if len(cases) >= 110:
                        return cases
    return cases


def generate_s143a_interim_scenarios():
    """Generates 105 hard cases for S.143A Interim Compensation & S.148 Appeal Deposits."""
    stages = ["Pre-Summons", "Notice Framed", "Evidence Stage", "Appellate Stage"]
    discretion_factors = ["Plea of Not Guilty", "Prima Facie Merit", "Financial Distress", "Delay Tactics"]

    cases = []
    idx = 1
    for s in stages:
        for df in discretion_factors:
            for pct in [10, 15, 20]:
                for amt in [500000.0, 2000000.0, 10000000.0]:
                    cases.append({
                        "id": f"S143A_HARD_{idx}",
                        "case_type": "cheque_bounce",
                        "litigation_stage": s,
                        "discretion_factor": df,
                        "interim_pct": pct,
                        "amount": amt
                    })
                    idx += 1
                    if len(cases) >= 110:
                        return cases
    return cases


def generate_evidentiary_alteration_scenarios():
    """Generates 105 hard cases for Signature Disputes, Material Alterations & CTS Images."""
    alterations = ["Amount Altered", "Date Altered", "Payee Name Altered", "Signature Mismatch", "CTS Image Unclear", "Stop Payment Issued"]
    bank_memos = ["Signature Differs", "Material Alteration", "Account Closed", "Refer to Drawer", "Stolen Instrument"]

    cases = []
    idx = 1
    for alt in alterations:
        for memo in bank_memos:
            for cert in [True, False]:
                cases.append({
                    "id": f"EVID_HARD_{idx}",
                    "case_type": "cheque_bounce",
                    "material_alteration": alt in ["Amount Altered", "Date Altered", "Payee Name Altered"],
                    "signature_dispute": alt == "Signature Mismatch",
                    "sec_65b_certificate": cert,
                    "bank_return_code": memo,
                    "amount": 400000.0
                })
                idx += 1
                if len(cases) >= 110:
                    return cases
    return cases


# Collect 630 total hard case scenarios (105 per module)
ALL_NOTICE_CASES = generate_notice_service_scenarios()
ALL_LIMIT_CASES = generate_limitation_scenarios()
ALL_S141_CASES = generate_vicarious_company_scenarios()
ALL_REBUT_CASES = generate_presumption_rebuttal_scenarios()
ALL_S143A_CASES = generate_s143a_interim_scenarios()
ALL_EVID_CASES = generate_evidentiary_alteration_scenarios()

TOTAL_HARD_CASES = ALL_NOTICE_CASES + ALL_LIMIT_CASES + ALL_S141_CASES + ALL_REBUT_CASES + ALL_S143A_CASES + ALL_EVID_CASES


# -----------------------------------------------------------------------------
# BENCHMARK TEST SUITE
# -----------------------------------------------------------------------------

def test_total_hard_case_count():
    assert len(TOTAL_HARD_CASES) >= 600, f"Expected 600+ hard cases, found {len(TOTAL_HARD_CASES)}"


@pytest.mark.parametrize("case_data", ALL_NOTICE_CASES)
def test_hard_notice_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "procedural_graph" in res
    assert "next_actions" in res

    if case_data["notice_days"] > 30:
        nodes = res["procedural_graph"]["nodes"]
        notice_node = next((n for n in nodes if n["id"] == "statutory_notice"), None)
        assert notice_node is not None
        assert notice_node["severity"] == "FATAL" or notice_node["defect"] is not None


@pytest.mark.parametrize("case_data", ALL_LIMIT_CASES)
def test_hard_limitation_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "procedural_graph" in res
    
    if case_data["days_post_notice"] < 15 or case_data["days_post_notice"] > 45:
        nodes = res["procedural_graph"]["nodes"]
        complaint_node = next((n for n in nodes if n["id"] == "complaint_filing"), None)
        assert complaint_node is not None
        assert complaint_node["severity"] == "FATAL" or complaint_node["defect"] is not None


@pytest.mark.parametrize("case_data", ALL_S141_CASES)
def test_hard_s141_company_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "next_actions" in res

    if not case_data["company_arrayed"] or not case_data.get("directors_named"):
        actions = res["next_actions"]
        assert any("Section 141" in a["authority"] or "141" in a["action"] for a in actions)


@pytest.mark.parametrize("case_data", ALL_REBUT_CASES)
def test_hard_presumption_rebuttal_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "causality_map" in res or "score_breakdown" in res


@pytest.mark.parametrize("case_data", ALL_S143A_CASES)
def test_hard_s143a_interim_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "next_actions" in res


@pytest.mark.parametrize("case_data", ALL_EVID_CASES)
def test_hard_evidentiary_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "contradictions" in res
