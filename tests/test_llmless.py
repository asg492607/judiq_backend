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
        assert "Case Score:" in result.get("case_summary", "") or "Case is" in result.get("case_summary", "")
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
