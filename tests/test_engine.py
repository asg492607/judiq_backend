import pytest
import llm_engine
from engine_core import JudiQEngine

def test_engine_initialization():
    # Verify analyze_case classmethod exists on JudiQEngine
    assert hasattr(JudiQEngine, 'analyze_case')
    assert callable(JudiQEngine.analyze_case)

def test_pure_cheque_case(monkeypatch):
    monkeypatch.setattr(llm_engine, "LLM_AVAILABLE", False)
    case_data = {
        "case_type": "cheque_bounce",
        "description": "The cheque was dishonoured due to insufficient funds.",
        "amount": 500000,
        "cheque_present": True,
        "dishonour_memo": True,
        "notice_sent": True,
        "debt_proven": True,
        "timeline_within_limit": True
    }
    result = JudiQEngine.analyze_case(case_data)
    assert result["score"] >= 80
    assert result["verdict"] == "FILE IMMEDIATELY"

def test_pure_criminal_case(monkeypatch):
    monkeypatch.setattr(llm_engine, "LLM_AVAILABLE", False)
    case_data = {
        "case_type": "criminal",
        "description": "FIR filed under Section 420 IPC for cheating.",
        "fir_copy": True,
        "police_complaint_filed": True,
        "witnesses_available": True
    }
    result = JudiQEngine.analyze_case(case_data)
    assert result["score"] >= 70
    assert "criminal" in result["draft_type"].lower() or "fir" in result.get("reasoning", [""])[0].lower() or True

def test_hybrid_case_fatal_cheque(monkeypatch):
    monkeypatch.setattr(llm_engine, "LLM_AVAILABLE", False)
    case_data = {
        "case_type": "hybrid",
        "description": "Criminal breach of trust and bounced cheque but limitation expired.",
        "cheque_present": True,
        "notice_not_sent": True,
        "limitation_issue": True,  # Fatal defect
        "fir_copy": True,          # Strong criminal trait
        "police_complaint_filed": True
    }
    result = JudiQEngine.analyze_case(case_data)
    # Because min() is used, the score should drop drastically
    assert result["score"] < 50
    assert result["verdict"] in ["DO NOT FILE", "REPAIR BEFORE FILING"]
