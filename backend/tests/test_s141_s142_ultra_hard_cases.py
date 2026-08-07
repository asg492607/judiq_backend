import pytest
from typing import Dict, Any
from cheque_bounce.cheque_bounce_engine import ChequeBounceEngine
from scoring_engine import ScoringEngineV12
from adversarial_engine import AdversarialEngine

# -----------------------------------------------------------------------------
# ULTRA-HARD S.141 & S.142 LEGAL SCENARIO GENERATORS (630 TOUGHEST CASES)
# -----------------------------------------------------------------------------

def generate_ultra_hard_s141_company_scenarios():
    """Generates 105 ultra-hard cases for Section 141 Vicarious Liability."""
    entity_types = ["Pvt Ltd", "Public Ltd", "LLP", "Partnership Firm", "Proprietorship", "HUF", "Trust", "Society"]
    roles = [
        "Managing Director", "Whole Time Director", "Independent Director", 
        "Nominee Director", "Resigned Director (Pre-Issuance)", "Resigned Director (Post-Issuance)",
        "Sleeping Partner", "Active Partner", "Karta", "Trustee", "Authorized Signatory"
    ]
    pleadings = ["Specific Role Pledged", "Generic Mention", "No Mention"]
    ibc_active = [True, False]

    cases = []
    idx = 1
    for et in entity_types:
        for r in roles:
            for p in pleadings:
                for ibc in ibc_active:
                    cases.append({
                        "id": f"S141_ULTRA_{idx}",
                        "case_type": "cheque_bounce",
                        "accused_type": et,
                        "company_arrayed": et not in ["Proprietorship"],
                        "director_role": r,
                        "resigned_dir12_available": "Resigned" in r,
                        "operational_role_pledged": p == "Specific Role Pledged",
                        "directors_named": p != "No Mention",
                        "ibc_cirp_active": ibc,
                        "amount": 10000000.0
                    })
                    idx += 1
                    if len(cases) >= 105:
                        return cases
    return cases


def generate_ultra_hard_s142_limitation_scenarios():
    """Generates 105 ultra-hard cases for S.142 Limitation, Cause of Action & Condonation."""
    filing_days_post_notice = [1, 5, 14, 15, 16, 30, 45, 46, 60, 90, 180, 365]
    condonation_applied = [True, False]
    condonation_reasons = ["Medical Emergency", "Covid Pandemic", "Postal Delay", "Illness of Counsel", "No Reason"]
    complainant_status = ["Original Payee", "Power of Attorney Holder", "Legal Heir of Deceased Payee"]

    cases = []
    idx = 1
    for f_day in filing_days_post_notice:
        for ca in condonation_applied:
            for cr in condonation_reasons:
                for cs in complainant_status:
                    cases.append({
                        "id": f"S142_ULTRA_{idx}",
                        "case_type": "cheque_bounce",
                        "dishonour_date": "2026-01-01",
                        "notice_date": "2026-01-15",
                        "days_post_notice": f_day,
                        "condonation_attached": ca,
                        "condonation_reason": cr,
                        "complainant_status": cs,
                        "amount": 3500000.0
                    })
                    idx += 1
                    if len(cases) >= 105:
                        return cases
    return cases


def generate_ultra_hard_notice_service_scenarios():
    """Generates 105 ultra-hard cases for S.138(b) Postal Service & Notice Defects."""
    service_statuses = ["Unclaimed", "Refused", "House Locked", "Left Address", "Wrong Office Address", "Deceased"]
    notice_dispatch_days = [5, 15, 29, 30, 31, 40, 60]
    demand_contents = ["Cheque Amount Only", "Cheque Amount + Interest", "Unquantified Damages Included", "Excess Demand"]

    cases = []
    idx = 1
    for ss in service_statuses:
        for ndd in notice_dispatch_days:
            for dc in demand_contents:
                cases.append({
                    "id": f"NOTICE_ULTRA_{idx}",
                    "case_type": "cheque_bounce",
                    "dishonour_date": "2026-01-01",
                    "notice_days": ndd,
                    "postal_return_reason": ss,
                    "demand_content": dc,
                    "excess_demand": dc in ["Unquantified Damages Included", "Excess Demand"],
                    "notice_sent": True,
                    "amount": 5000000.0
                })
                idx += 1
                if len(cases) >= 105:
                    return cases
    return cases


def generate_ultra_hard_s143a_s148_scenarios():
    """Generates 105 ultra-hard cases for S.143A & S.148 Interim Deposit Applications."""
    stages = ["Pre-Trial", "Notice Framed u/s 251 CrPC", "Complainant Evidence", "Section 313 Statement", "Appeal before Sessions Court"]
    discretion_factors = ["Plea of Not Guilty", "Prima Facie Frivolous Defense", "Financial Distress", "Delay Tactics"]
    interim_percentages = [0, 10, 15, 20, 25]

    cases = []
    idx = 1
    for st in stages:
        for df in discretion_factors:
            for pct in interim_percentages:
                cases.append({
                    "id": f"S143A_ULTRA_{idx}",
                    "case_type": "cheque_bounce",
                    "litigation_stage": st,
                    "discretion_factor": df,
                    "interim_pct_claimed": pct,
                    "amount": 15000000.0
                })
                idx += 1
                if len(cases) >= 105:
                    return cases
    return cases


def generate_ultra_hard_s147_compounding_scenarios():
    """Generates 105 ultra-hard cases for S.147 Compounding & Damodar Prabhu Graded Costs."""
    compounding_stages = ["Trial Court", "Sessions Court Appeal", "High Court Revision/S.482", "Supreme Court SLP"]
    settlement_modes = ["Full Cash Payment", "Instalment Post-Dated Cheques", "Mediation Settlement Agreement"]
    default_occurred = [True, False]
    amounts = [500000.0, 2000000.0, 5000000.0, 10000000.0, 50000000.0]

    cases = []
    idx = 1
    for cs in compounding_stages:
        for sm in settlement_modes:
            for do in default_occurred:
                for amt in amounts:
                    cases.append({
                        "id": f"S147_ULTRA_{idx}",
                        "case_type": "cheque_bounce",
                        "compounding_stage": cs,
                        "settlement_mode": sm,
                        "mediation_default": do,
                        "amount": amt
                    })
                    idx += 1
                    if len(cases) >= 105:
                        return cases
    return cases


def generate_ultra_hard_presumption_evidentiary_scenarios():
    """Generates 105 ultra-hard cases for S.139 Presumptions, Security Cheque & S.87 Material Alteration."""
    defenses = [
        "Security Cheque (Sripati Singh)", "Complainant Financial Capacity (Basalingappa)",
        "Blank Signed Cheque (Bir Singh)", "Time-Barred Debt", "Material Alteration u/s 87",
        "Stop Payment Instructions", "Stolen Instrument / Extortion"
    ]
    itr_proof = [True, False]
    sec_65b_cert = [True, False]
    amounts = [100000.0, 500000.0, 2500000.0, 10000000.0]

    cases = []
    idx = 1
    for d in defenses:
        for itr in itr_proof:
            for cert in sec_65b_cert:
                for amt in amounts:
                    cases.append({
                        "id": f"EVID_ULTRA_{idx}",
                        "case_type": "cheque_bounce",
                        "defense_type": d,
                        "material_alteration": d == "Material Alteration u/s 87",
                        "cheque_security_claim": "Security Cheque" in d,
                        "complainant_itr_available": itr,
                        "sec_65b_certificate": cert,
                        "amount": amt
                    })
                    idx += 1
                    if len(cases) >= 105:
                        return cases
    return cases


# Collect 630 total ultra-hard case scenarios (105 per module)
ALL_S141_ULTRA_CASES = generate_ultra_hard_s141_company_scenarios()
ALL_S142_ULTRA_CASES = generate_ultra_hard_s142_limitation_scenarios()
ALL_NOTICE_ULTRA_CASES = generate_ultra_hard_notice_service_scenarios()
ALL_S143A_ULTRA_CASES = generate_ultra_hard_s143a_s148_scenarios()
ALL_S147_ULTRA_CASES = generate_ultra_hard_s147_compounding_scenarios()
ALL_EVID_ULTRA_CASES = generate_ultra_hard_presumption_evidentiary_scenarios()

TOTAL_ULTRA_HARD_CASES = (
    ALL_S141_ULTRA_CASES + ALL_S142_ULTRA_CASES + ALL_NOTICE_ULTRA_CASES +
    ALL_S143A_ULTRA_CASES + ALL_S147_ULTRA_CASES + ALL_EVID_ULTRA_CASES
)


# -----------------------------------------------------------------------------
# BENCHMARK TEST SUITE
# -----------------------------------------------------------------------------

def test_total_ultra_hard_case_count():
    assert len(TOTAL_ULTRA_HARD_CASES) >= 600, f"Expected 600+ ultra-hard cases, found {len(TOTAL_ULTRA_HARD_CASES)}"


@pytest.mark.parametrize("case_data", ALL_S141_ULTRA_CASES)
def test_ultra_hard_s141_company_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "next_actions" in res

    if not case_data["company_arrayed"] or not case_data.get("directors_named"):
        actions = res["next_actions"]
        assert any("Section 141" in a["authority"] or "141" in a["action"] for a in actions)


@pytest.mark.parametrize("case_data", ALL_S142_ULTRA_CASES)
def test_ultra_hard_s142_limitation_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "procedural_graph" in res

    if case_data["days_post_notice"] < 15 or case_data["days_post_notice"] > 45:
        nodes = res["procedural_graph"]["nodes"]
        complaint_node = next((n for n in nodes if n["id"] == "complaint_filing"), None)
        assert complaint_node is not None
        assert complaint_node["severity"] == "FATAL" or complaint_node["defect"] is not None


@pytest.mark.parametrize("case_data", ALL_NOTICE_ULTRA_CASES)
def test_ultra_hard_notice_service_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "procedural_graph" in res

    if case_data["notice_days"] > 30:
        nodes = res["procedural_graph"]["nodes"]
        notice_node = next((n for n in nodes if n["id"] == "statutory_notice"), None)
        assert notice_node is not None
        assert notice_node["severity"] == "FATAL" or notice_node["defect"] is not None


@pytest.mark.parametrize("case_data", ALL_S143A_ULTRA_CASES)
def test_ultra_hard_s143a_interim_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "next_actions" in res


@pytest.mark.parametrize("case_data", ALL_S147_ULTRA_CASES)
def test_ultra_hard_s147_compounding_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res


@pytest.mark.parametrize("case_data", ALL_EVID_ULTRA_CASES)
def test_ultra_hard_presumption_evidentiary_scenarios(case_data: Dict[str, Any]):
    res = ChequeBounceEngine.analyze(case_data)
    assert "score" in res
    assert "contradictions" in res
