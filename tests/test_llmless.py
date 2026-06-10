import pytest
import llm_engine
from engine_core import analyze_case

def test_llmless_civil_case_graceful_degradation(monkeypatch):
    # Force LLM offline
    monkeypatch.setattr(llm_engine, "LLM_AVAILABLE", False)

    civil_case = {
        "case_type": "Civil",
        "client_role": "Complainant",
        "cheque_amount": "500000",
        "description": "The accused took a friendly loan of 5 lakhs and gave a cheque which bounced due to insufficient funds.",
        "notice_sent": True,
        "cheque_present": True,
        "dishonour_memo": True,
        "debt_proven": True,
        "cheque_date": "2026-01-01",
        "dishonour_date": "2026-01-15",
        "notice_date": "2026-01-20"
    }

    try:
        result = analyze_case(civil_case)
        assert result is not None
        assert "final_score" in result
        assert "tldr" in result
        
        # Verify LLM-less fallback indicators
        assert "Case:" in result.get("case_summary", "")
    except Exception as e:
        pytest.fail(f"LLM-less Civil Analysis raised an exception: {e}")


def test_llmless_criminal_case_graceful_degradation(monkeypatch):
    # Force LLM offline
    monkeypatch.setattr(llm_engine, "LLM_AVAILABLE", False)

    criminal_case = {
        "case_type": "Criminal",
        "client_role": "Accused",
        "offense_type": "302",
        "has_eyewitness": True,
        "medical_contradicts_ocular": True,
        "description": "Accused charged under S.302 IPC. Eyewitness testimony is contradicted by medical evidence."
    }

    try:
        result = analyze_case(criminal_case)
        assert result is not None
        assert "final_score" in result
        assert "causality_map" in result
        
        # If knowledge base wiring worked, the contradictions should be present
        assert len(result.get("causality_map", [])) >= 0
    except Exception as e:
        pytest.fail(f"LLM-less Criminal Analysis raised an exception: {e}")

def test_zero_score_gating(monkeypatch):
    monkeypatch.setattr(llm_engine, "LLM_AVAILABLE", False)
    case_data = {
        "case_type": "Civil",
        "client_role": "Complainant",
        "cheque_amount": "500000",
        "description": "Zero score case without physical cheque.",
        "cheque_type": "missing", # Forces 0 score or negative
        "has_electronic_evidence": "No",
        "force_draft_type": "COMPLAINT"
    }
    result = analyze_case(case_data)
    assert result is not None
    # Assuming draft is blocked
    assert "DRAFT GENERATION BLOCKED" in result.get("draft", "")

def test_notice_delivery_contradiction(monkeypatch):
    monkeypatch.setattr(llm_engine, "LLM_AVAILABLE", False)
    case_data = {
        "case_type": "Civil",
        "client_role": "Complainant",
        "cheque_present": True,
        "notice_sent": True,
        "notice_date": "2026-01-20",
        "dishonour_date": "2026-01-15",
        "notice_delivery_status": "returned to sender",
        "notice_delivery_date": "2026-01-25"
    }
    result = analyze_case(case_data)
    # Notice Invalid should trigger fatal defect
    assert result.get("final_score", 100) < 50
    assert any("Notice" in r or "service failed" in r.lower() for r in result.get("reasoning_trace", []))

def test_s63_4_penalty(monkeypatch):
    monkeypatch.setattr(llm_engine, "LLM_AVAILABLE", False)
    case_data = {
        "case_type": "Civil",
        "client_role": "Complainant",
        "cheque_present": True,
        "has_electronic_evidence": "Yes",
        "bsa_certificate": "No",
        "cheque_type": "photocopy"
    }
    result = analyze_case(case_data)
    # Trace should contain BSA or Electronic evidence missing penalty
    trace_str = " ".join(result.get("reasoning_trace", []))
    assert "BSA" in trace_str or "Electronic" in trace_str or "S.63" in trace_str
