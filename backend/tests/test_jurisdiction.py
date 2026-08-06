"""
tests/test_jurisdiction.py
---------------------------
Unit tests for jurisdiction_engine.py.

Legal context (Section 142(2) NI Act, 2015 amendment):
- Complaint must be filed at the payee's bank branch location (PRIMARY).
- Fallback: drawer's bank location, then accused's city.
- Wrong court triggers an INVALID status → score deduction via apply_jurisdiction_guards().

Design decisions:
- Tests are pure unit tests — no engine pipeline, no LLM patching needed.
- Each test is small and independent; functions are called directly.
- apply_jurisdiction_guards tests use simple dicts; the function signature
  is (jurisdiction_info: dict, concepts: list, final_score: float) → float.
"""
from jurisdiction_engine import map_jurisdiction, get_court_tier, apply_jurisdiction_guards


# ---------------------------------------------------------------------------
# map_jurisdiction — RESOLVED path
# ---------------------------------------------------------------------------

def test_resolved_with_payee_bank_city():
    """
    Providing payee_bank_city is the canonical S.142(2) case.
    Result must be RESOLVED with HIGH confidence and include recommended_court.
    """
    case_data = {"payee_bank_city": "Mumbai"}
    result = map_jurisdiction(case_data)

    assert result["status"] == "RESOLVED"
    assert result["confidence"] == "HIGH"
    assert "recommended_court" in result
    assert result["recommended_court"]  # non-empty


# ---------------------------------------------------------------------------
# get_court_tier — metro vs non-metro
# ---------------------------------------------------------------------------

def test_metro_city_court_tier():
    """Mumbai is in METRO_CITIES → Metropolitan Magistrate Court."""
    tier = get_court_tier("Mumbai")
    assert tier == "Metropolitan Magistrate Court"


def test_non_metro_court_tier():
    """Nashik is NOT in METRO_CITIES → JMFC."""
    tier = get_court_tier("Nashik")
    assert tier == "Judicial Magistrate First Class (JMFC)"


# ---------------------------------------------------------------------------
# map_jurisdiction — INVALID path (court_name mismatch)
# ---------------------------------------------------------------------------

def test_invalid_jurisdiction_penalty():
    """
    When the supplied court_name doesn't match the correct city (Mumbai),
    the engine must return INVALID status to trigger a fatal defect.
    """
    case_data = {
        "payee_bank_city": "Mumbai",
        "court_name": "District Court Delhi",  # Wrong city
    }
    result = map_jurisdiction(case_data)

    assert result["status"] == "INVALID", (
        f"Expected INVALID jurisdiction, got: {result}"
    )


# ---------------------------------------------------------------------------
# map_jurisdiction — INSUFFICIENT_DATA path
# ---------------------------------------------------------------------------

def test_insufficient_data_no_city():
    """
    An empty case dict has no city information at all.
    Result must be INSUFFICIENT_DATA.
    """
    result = map_jurisdiction({})
    assert result["status"] == "INSUFFICIENT_DATA"


# ---------------------------------------------------------------------------
# apply_jurisdiction_guards — score adjustment
# ---------------------------------------------------------------------------

def test_apply_guards_deducts_score():
    """
    INVALID jurisdiction triggers a -35 point penalty.
    Returned score must be strictly less than the input and >= 0.
    """
    adjusted = apply_jurisdiction_guards(
        {"status": "INVALID"},
        [],          # concepts list (guards may append to it)
        80.0,
    )
    assert adjusted < 80
    assert adjusted >= 0


def test_apply_guards_no_change_when_resolved():
    """
    RESOLVED jurisdiction must pass the score through unchanged.
    """
    adjusted = apply_jurisdiction_guards(
        {"status": "RESOLVED", "confidence": "HIGH"},
        [],
        80.0,
    )
    assert adjusted == 80.0
