from scoring_engine import ScoringEngineV12

def test_calculate_score_basic():
    case_data = {
        "amount": 100000,
        "cheque_proof_available": True,
        "cheque_proof_type": "original",
        "memo_available": True,
        "notice_sent": True,
        "within_30_days": "Yes",
        "debt_proven": True
    }
    concepts = []
    contradictions = []
    evidence = {}
    
    result = ScoringEngineV12.calculate_score_with_trace(case_data, concepts, contradictions, evidence)
    
    # Check that score is high due to having all PILLARS
    assert result["score"] > 60
    assert len(result["trace"]) > 0
    assert len(result["causality_map"]) > 0

def test_calculate_score_fatal_missing_cheque():
    case_data = {
        "amount": 100000,
        "cheque_proof_available": False,
        "memo_available": True,
        "notice_sent": True,
        "within_30_days": "Yes",
        "debt_proven": True
    }
    result = ScoringEngineV12.calculate_score_with_trace(case_data, [], [], {})
    
    # Missing cheque is a fatal error, should result in a low score
    assert result["score"] < 50
    assert any("FATAL ERROR: Primary instrument missing" in t for t in result["trace"])
