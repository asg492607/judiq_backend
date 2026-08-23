import pytest
from draft_engine import verify_s138_timeline_for_draft, generate_legal_notice, generate_complaint

def test_verify_s138_timeline_valid():
    case_data = {
        "cheque_date": "2026-01-01",
        "presentation_date": "2026-01-15",
        "dishonour_date": "2026-01-20",
        "notice_date": "2026-02-05",
        "notice_received_date": "2026-02-08",
        "filing_date": "2026-03-01"
    }
    res = verify_s138_timeline_for_draft(case_data)
    assert res["is_cheque_valid"] is True
    assert res["is_notice_valid"] is True
    assert res["is_complaint_timely"] is True
    assert res["is_premature"] is False
    assert res["is_delay"] is False

def test_verify_s138_timeline_notice_delayed():
    case_data = {
        "cheque_date": "2026-01-01",
        "presentation_date": "2026-01-10",
        "dishonour_date": "2026-01-15",
        "notice_date": "2026-03-01",  # 45 days post dishonour (> 30 days)
    }
    res = verify_s138_timeline_for_draft(case_data)
    assert res["is_notice_valid"] is False
    assert len(res["warnings"]) > 0
    
    notice = generate_legal_notice(case_data)
    assert "SECTION 138 NI ACT STATUTORY TIMELINE AUDIT REPORT" in notice
    assert "TIMELINE BREACH - NOTICE DELAYED" in notice

def test_verify_s138_timeline_complaint_delayed():
    case_data = {
        "cheque_date": "2026-01-01",
        "presentation_date": "2026-01-10",
        "dishonour_date": "2026-01-15",
        "notice_date": "2026-01-25",
        "notice_received_date": "2026-01-28",
        "filing_date": "2026-04-15"  # > 45 days post notice service
    }
    res = verify_s138_timeline_for_draft(case_data)
    assert res["is_delay"] is True
    assert res["delay_days"] > 0
    
    complaint = generate_complaint(case_data, concepts=[])
    assert "SECTION 138 NI ACT STATUTORY TIMELINE AUDIT REPORT" in complaint
    assert "Section 142(1)(b)" in complaint
