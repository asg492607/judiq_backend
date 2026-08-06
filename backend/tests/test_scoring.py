"""
tests/test_scoring.py
----------------------
Unit tests for ScoringEngineV12.calculate_score_with_trace().

Design decisions:
- Fixtures provide canonical strong/weak case dicts, reused across tests.
- All assertions target the public contract: specific keys, numeric types,
  and score ranges. Never assert on reasoning_trace string content.
- test_fatal_defect_not_catastrophic validates that the engine applies a
  *multiplier penalty* (score * 0.6) rather than hard-zeroing the score
  when a fatal defect exists but other pillars are strong.
"""
import pytest
from scoring_engine import ScoringEngineV12


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def strong_case_data():
    """All four S.138 NI Act pillars present — maximises positive contribution."""
    return {
        "case_type": "cheque_bounce",
        "client_role": "Complainant",
        "cheque_present": True,
        "cheque_proof_type": "original",
        "dishonour_memo": True,
        "notice_sent": True,
        "within_30_days": "Yes",
        "debt_proven": True,
        "cheque_amount": "300000",
        "loan_via_bank": True,
        "complainant_itr_available": True,
        "payee_bank_city": "Mumbai",
        "notice_delivery_status": "delivered",
    }


@pytest.fixture
def weak_case_data():
    """Cheque missing — triggers the primary fatal-defect path."""
    return {
        "case_type": "cheque_bounce",
        "client_role": "Complainant",
        "cheque_present": False,
        "dishonour_memo": True,
        "notice_sent": True,
        "within_30_days": "Yes",
        "debt_proven": True,
        "cheque_amount": "100000",
    }


# ---------------------------------------------------------------------------
# Output contract: required keys and types
# ---------------------------------------------------------------------------

def test_score_output_keys(strong_case_data):
    """
    calculate_score_with_trace must return all documented top-level keys
    with the correct types.

    Note: 'verdict' is NOT part of the scoring engine's output contract —
    it is constructed by ResponseBuilder from the score value. We only
    assert keys that ScoringEngineV12 actually returns.
    """
    result = ScoringEngineV12.calculate_score_with_trace(
        strong_case_data, [], [], {}
    )

    # Core numeric output
    assert "score" in result
    assert "final_score" in result
    assert isinstance(result["score"], (int, float))
    assert isinstance(result["final_score"], (int, float))

    # Traceability outputs
    assert "reasoning_trace" in result
    assert isinstance(result["reasoning_trace"], list)

    # Causality graph
    assert "causality_map" in result
    assert isinstance(result["causality_map"], list)


# ---------------------------------------------------------------------------
# Score value ranges
# ---------------------------------------------------------------------------

def test_strong_case_scores_high(strong_case_data):
    """All pillars present → score should be at or above the 60-point threshold."""
    result = ScoringEngineV12.calculate_score_with_trace(
        strong_case_data, [], [], {}
    )
    assert result["score"] >= 60, (
        f"Expected score >= 60 for a strong case, got {result['score']}"
    )


def test_missing_cheque_scores_low(weak_case_data):
    """Missing primary instrument should drive score below 50."""
    result = ScoringEngineV12.calculate_score_with_trace(
        weak_case_data, [], [], {}
    )
    assert result["score"] < 50, (
        f"Expected score < 50 when cheque is missing, got {result['score']}"
    )


def test_score_within_bounds(strong_case_data, weak_case_data):
    """Scores must always be clamped to [0, 100] regardless of input."""
    for label, case in [("strong", strong_case_data), ("weak", weak_case_data)]:
        result = ScoringEngineV12.calculate_score_with_trace(case, [], [], {})
        score = result["score"]
        assert 0 <= score <= 100, (
            f"Score out of [0, 100] bounds for {label} case: {score}"
        )


# ---------------------------------------------------------------------------
# Penalty model: fatal defect applies a multiplier, not a hard zero
# ---------------------------------------------------------------------------

def test_fatal_defect_not_catastrophic():
    """
    When the cheque is missing but all other pillars are strong, the engine
    applies a 40% penalty multiplier (score * 0.6) rather than zeroing.
    The resulting score must be > 0.
    """
    case_data = {
        "case_type": "cheque_bounce",
        "cheque_present": False,      # triggers fatal-defect penalty path
        "dishonour_memo": True,
        "notice_sent": True,
        "within_30_days": "Yes",
        "debt_proven": True,
        "cheque_amount": "150000",
        "loan_via_bank": True,
        "complainant_itr_available": True,
        "notice_delivery_status": "delivered",
    }
    result = ScoringEngineV12.calculate_score_with_trace(case_data, [], [], {})
    assert result["score"] > 0, (
        f"Score must not be zero even with a fatal defect; got {result['score']}"
    )


def test_flat_wizard_normalization():
    """
    Test that flat options sent by the frontend wizard are correctly
    normalized to the expected format and scoring inputs.
    """
    from normalizer import normalize_input
    
    flat_wizard_data = {
        "case_id": "TEST-WIZ-01",
        "case_type": "Cheque Bounce",
        "client_role": "Complainant",
        "complainant_authorized": "Yes - Original",
        "original_cheque": "Yes - Original",
        "bank_memo_received": "Yes",
        "notice_sent": "Yes",
        "agreement_type": "Written Agreement",
        "supporting_documents": "Yes - All Documents",
        "debt_acknowledgment": "Yes - Written",
        "itr_available": "Yes",
        "loan_via_bank": "Yes",
        "debt_amount": 500000.0,
    }
    
    normalized = normalize_input(flat_wizard_data)
    
    # Assert correct normalization
    assert normalized["cheque_present"] is True
    assert normalized["dishonour_memo"] is True
    assert normalized["notice_sent"] is True
    assert normalized["debt_proven"] is True
    assert normalized["is_authorized"] is True
    assert normalized["complainant_itr_available"] is True
    assert normalized["loan_via_bank"] is True
    assert "written" in normalized["debt_proof_type"].lower()
    
    # Run through the scoring engine
    result = ScoringEngineV12.calculate_score_with_trace(normalized, [], [], {})
    assert result["score"] >= 60, f"Expected high score for complete case, got {result['score']}"

