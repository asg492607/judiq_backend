import pytest
from banking.multi_track_orchestrator import (
    MultiTrackOrchestrator,
    evaluate_multi_track_recovery,
    MultiTrackEvaluationRequest,
)
from utils import parse_date, days_between


def test_multi_track_orchestrator_calculation():
    orchestrator = MultiTrackOrchestrator()
    facts = {
        "borrower_name": "Apex Infra Ltd",
        "loan_account_no": "APEX-9988-CORP",
        "default_amount": 55_00_000,
        "is_wilful_defaulter": True,
        "asset_types": ["commercial_property", "movable_plant"],
        "security_perfection_status": "perfected_cbe",
        "has_cheque_bounce": True,
        "is_corporate_debtor": True,
    }

    report = orchestrator.orchestrate_recovery_strategy(facts)

    assert report.borrower_name == "Apex Infra Ltd"
    assert report.default_amount == 55_00_000
    assert report.optimal_primary_track is not None
    assert isinstance(report.optimal_primary_track, str)
    assert len(report.tracks) == 5
    assert "track_1_s138" in report.tracks
    assert "track_2_sarfaesi" in report.tracks
    assert isinstance(report.recommended_concurrent_tracks, list)
    assert len(report.recommended_sequence) > 0


def test_evaluate_multi_track_recovery_model_dump():
    req = MultiTrackEvaluationRequest(
        borrower_name="Zenith Trading Co",
        loan_account_no="ZENITH-1122",
        default_amount=25_00_000,
        is_wilful_defaulter=False,
    )
    report = evaluate_multi_track_recovery(req)

    assert report.borrower_name == "Zenith Trading Co"
    assert report.default_amount == 25_00_000
    assert report.optimal_primary_track is not None


def test_utils_date_helpers():
    d1 = "2026-01-01"
    d2 = "2026-01-31"
    assert parse_date(d1) is not None
    assert parse_date(d2) is not None
    assert days_between(d1, d2) == 30
