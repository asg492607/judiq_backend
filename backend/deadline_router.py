"""
JudiQ Deadline Tracker & Calendar Export API Router
Exposes statutory deadline calculations, reminder schedules, and standard iCal (.ics) exports.
"""

from fastapi import APIRouter, HTTPException, Path, Body, Response
from typing import Optional, Dict, Any

from deadline_calendar import (
    DeadlineCalendarService,
    DeadlineCalculationRequest,
    DeadlineScheduleReport
)

router = APIRouter()


@router.post("/calculate", response_model=DeadlineScheduleReport, tags=["Deadline Tracker"])
def calculate_statutory_deadlines_endpoint(req: DeadlineCalculationRequest = Body(...)):
    """
    Calculates statutory deadlines across Section 138, SARFAESI, and DRT tracks with 7/14-day alert schedules.
    """
    return DeadlineCalendarService.calculate_deadlines(req)


@router.get("/{case_reference}/calendar.ics", tags=["Deadline Tracker"])
def export_calendar_ics_endpoint(case_reference: str):
    """
    Exports a standard RFC 5545 iCalendar (.ics) file with alerts for Google Calendar / Outlook / Apple Calendar.
    """
    # Sample default timeline for case reference
    req = DeadlineCalculationRequest(
        case_reference=case_reference,
        borrower_or_accused_name="Case Party",
        dispute_type="SECTION_138",
        dishonour_memo_date="2026-08-15",
        notice_received_date="2026-08-25"
    )
    report = DeadlineCalendarService.calculate_deadlines(req)
    ics_text = DeadlineCalendarService.generate_ical_content(case_reference, report.deadlines)

    return Response(
        content=ics_text,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="judiq_deadlines_{case_reference}.ics"'
        }
    )
