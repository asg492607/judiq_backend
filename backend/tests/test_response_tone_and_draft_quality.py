import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from response_builder import ResponseBuilder
from reasoning_engine import ReasoningEngine
from draft_engine import generate_complaint, DraftEngine


def test_response_builder_tone_high_score():
    """Verify high-scoring cases use lawyer-enabling assessment language."""
    engine_result = {
        "final_score": 85,
        "score": 85,
        "verdict": "STRONG CASE",
        "tldr": {"verdict": "STRONG CASE", "core_risk": "None", "top_threat": "None"},
        "strengths": ["All Section 138 ingredients satisfied"],
        "weaknesses": [],
        "suggestions": [{"title": "Verify originals"}],
        "concepts": [],
        "case_data": {"case_type": "138", "amount": 1550000},
        "draft_type": "COMPLAINT"
    }
    case_data = {
        "case_type": "138",
        "amount": 1550000,
        "notice_sent": True
    }
    resp = ResponseBuilder.build_final_response(engine_result, case_data)
    decision = resp.get("decision", {})

    assert "Assessment: Strong case indicators identified" == decision.get("decision_label")
    assert "Proceed Aggressively" not in decision.get("decision_label")
    assert "counsel" in decision.get("detail", "").lower()

    next_steps = decision.get("next_steps", [])
    assert any("Verify originals" in s for s in next_steps)
    assert any("Confirm limitation" in s for s in next_steps)
    assert any("Prepare for advocate review" in s for s in next_steps)

    senior_brief = resp.get("senior_brief", {})
    assert senior_brief.get("predicted_posture") == "Advocate Review Ready"
    assert "Prosecution-Ready" not in senior_brief.get("predicted_posture")


def test_reasoning_engine_finding_tone():
    """Verify reasoning engine does not proclaim case is prosecution-ready."""
    case_data = {
        "case_type": "138",
        "cheque_present": True,
        "cheque_issued": True,
        "dishonour": True,
        "dishonour_reason": "Insufficient Funds",
        "notice_sent": True,
        "debt_proven": True
    }
    interps = ReasoningEngine.interpret_statutes(case_data, [])
    s138 = next((i for i in interps if i["section"] == "138"), None)
    assert s138 is not None
    assert "The case is prosecution-ready." not in s138["finding"]
    assert "Case indicators support advocate review." in s138["finding"]


def test_draft_engine_complaint_quality():
    """Verify complaint draft quality: no duplicate currency, no raw placeholders, proper formatting."""
    case_data = {
        "case_id": "CASE-138-2026-001",
        "complainant_name": "Apex Retail Pvt Ltd",
        "complainant_address": "Nariman Point, Mumbai",
        "complainant_type": "Company",
        "authorized_person_name": "Rahul Verma",
        "accused_name": "Zenith Enterprises",
        "accused_address": "Andheri East, Mumbai",
        "accused_type": "Pvt Ltd/Ltd Company",
        "directors_named": True,
        "director_names": "Suresh Mehta, Director",
        "cheque_number": "123456",
        "cheque_date": "2025-10-01",
        "amount": 1550000,
        "dishonour_date": "2025-10-15",
        "dishonour_reason": "Funds Insufficient",
        "notice_date": "2025-10-20",
        "notice_received_date": "2025-10-25",
        "advocate_name": "Rajesh Sharma",
        "advocate_bar_id": "MAH/1234/2010",
        "court_name": "Metropolitan Magistrate Court, Esplanade Mumbai",
        "payee_bank_city": "Mumbai"
    }

    draft = generate_complaint(case_data, [], tone="standard")

    # 1. Currency duplication check
    assert "Rs. Rs." not in draft
    assert "INR Rs." not in draft
    assert "Rs. 1,550,000/-" in draft

    # 2. Complaint number check
    assert "COMPLAINT NO: _____ /" not in draft
    assert "COMPLAINT NO.: _____ /" not in draft
    assert "[Filing Ref: CASE-138-2026-001]" in draft

    # 3. Contact details check
    assert "________ (Contact Number)" not in draft

    # 4. Advocate signature block check
    assert "__________________, ADVOCATE" not in draft
    assert "RAJESH SHARMA (Enr: MAH/1234/2010), ADVOCATE" in draft

    # 5. Expiration date check (25 Oct 2025 + 15 days = 09 Nov 2025)
    assert "which expired on ________." not in draft
    assert "which expired on 09-11-2025" in draft

    # 6. Corporate entity affidavit phrasing check
    assert "son/daughter/representative of ________, aged about ____ years" not in draft
    assert "Rahul Verma" in draft
    assert "having office at Nariman Point, Mumbai" in draft


def test_draft_engine_individual_fallback_quality():
    """Verify individual complainant draft does not output unsightly blanks when optional fields absent."""
    case_data = {
        "complainant_name": "Amit Shah",
        "complainant_address": "Fort, Mumbai",
        "complainant_type": "Individual",
        "accused_name": "Vikram Malhotra",
        "accused_address": "Bandra, Mumbai",
        "accused_type": "Individual",
        "cheque_number": "654321",
        "cheque_date": "2025-11-01",
        "amount": 50000,
        "dishonour_date": "2025-11-05",
        "dishonour_reason": "Account Closed",
        "court_name": "Metropolitan Magistrate Court, Bandra Mumbai"
    }

    draft = generate_complaint(case_data, [], tone="standard")

    assert "Rs. Rs." not in draft
    assert "Rs. 50,000/-" in draft
    assert "COMPLAINT NO: [To be assigned on filing]" in draft
    assert "__________________, ADVOCATE" not in draft
    assert "[COUNSEL FOR COMPLAINANT]" in draft
    assert "________ (Contact Number)" not in draft
    assert "son/daughter/representative of ________, aged about ____ years" not in draft
    assert "I, Amit Shah, of adult age, residing at Fort, Mumbai" in draft
    assert "which expired upon lapse of the statutory 15-day window" in draft
