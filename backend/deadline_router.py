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


# ── Persistent CMS Deadline Endpoints ─────────────────────────
from session import DatabaseManager
from security import get_current_user_optional
from fastapi import Depends
import uuid

@router.post("/cases/{case_id}/deadlines/calculate", tags=["Deadline Tracker"])
def calculate_and_save_case_deadlines(
    case_id: str,
    user_id: str = Depends(get_current_user_optional)
):
    case = DatabaseManager.cms_get_case(case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    cdata = case.get("financial_data") or {}
    debtor = case.get("debtor_data") or {}

    req = DeadlineCalculationRequest(
        case_reference=case_id,
        borrower_or_accused_name=debtor.get("name", "Borrower/Accused"),
        dispute_type="SARFAESI" if "sarfaesi" in (case.get("case_type") or "").lower() else "SECTION_138",
        dishonour_memo_date=cdata.get("dishonour_date") or cdata.get("memo_date"),
        notice_sent_date=cdata.get("notice_date"),
        notice_received_date=cdata.get("notice_received_date")
    )
    report = DeadlineCalendarService.calculate_deadlines(req)

    # Persist deadlines
    saved = []
    for d in report.deadlines:
        did = f"DLN-{uuid.uuid4().hex[:8].upper()}"
        DatabaseManager.cms_save_deadline(
            deadline_id=did,
            case_id=case_id,
            title=d.title,
            due_date=d.due_date,
            statutory_basis=d.statutory_basis,
            urgency_level=d.urgency_level,
            mandatory_action=d.mandatory_action,
            consequence=d.consequence
        )
        saved.append({"deadline_id": did, "title": d.title, "due_date": d.due_date, "urgency": d.urgency_level})

    return {
        "success": True,
        "case_id": case_id,
        "deadlines_count": len(saved),
        "deadlines": saved
    }

@router.get("/cases/{case_id}/deadlines", tags=["Deadline Tracker"])
def list_case_deadlines(case_id: str):
    return DatabaseManager.cms_list_deadlines(case_id=case_id)

@router.patch("/deadlines/{deadline_id}/complete", tags=["Deadline Tracker"])
def complete_deadline(deadline_id: str):
    res = DatabaseManager.cms_complete_deadline(deadline_id=deadline_id)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail="Failed to mark deadline completed")
    return {"success": True, "deadline_id": deadline_id, "status": "completed"}

@router.get("/deadlines/upcoming", tags=["Deadline Tracker"])
def get_upcoming_deadlines(user_id: str = Depends(get_current_user_optional)):
    actual_user = user_id or "ANONYMOUS"
    return DatabaseManager.cms_list_deadlines(user_id=actual_user, status="pending")

