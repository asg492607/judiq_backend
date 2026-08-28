"""
JudiQ Statutory Deadline Tracker & Calendar Integration Engine
Calculates statutory limitation dates, generates 7/14-day smart alerts,
and exports standard RFC 5545 iCalendar (.ics) files for Google Calendar, Outlook, and Apple Calendar.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta, timezone
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger("JudiQ.DeadlineCalendar")


class StatutoryDeadlineItem(BaseModel):
    deadline_id: str
    case_reference: str
    title: str
    statutory_basis: str
    due_date: str
    days_remaining: int
    urgency_level: str  # "CRITICAL_TODAY", "URGENT_7_DAYS", "UPCOMING_14_DAYS", "SAFE", "EXPIRED_NEEDS_CONDONATION"
    mandatory_action: str
    consequence_of_missing: str
    smart_reminder_dates: List[str]  # e.g. ["2026-09-01 (T-14d)", "2026-09-08 (T-7d)", "2026-09-13 (T-2d)"]


class DeadlineCalculationRequest(BaseModel):
    case_reference: str
    borrower_or_accused_name: str
    dispute_type: str = "SECTION_138"  # "SECTION_138", "SARFAESI", "DRT"
    cheque_date: Optional[str] = None
    dishonour_memo_date: Optional[str] = None
    notice_received_date: Optional[str] = None
    section_13_2_notice_date: Optional[str] = None
    borrower_representation_date: Optional[str] = None
    npa_date: Optional[str] = None


class DeadlineScheduleReport(BaseModel):
    case_reference: str
    borrower_name: str
    dispute_type: str
    deadlines: List[StatutoryDeadlineItem]
    next_immediate_deadline: Optional[StatutoryDeadlineItem]
    ical_export_url: str
    calendar_sync_instructions: str


class DeadlineCalendarService:
    """
    Computes precise statutory deadlines and generates standard iCal (.ics) strings.
    """

    @classmethod
    def parse_iso_date(cls, date_str: Optional[str]) -> Optional[date]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except Exception:
            return None

    @classmethod
    def calculate_deadlines(cls, req: DeadlineCalculationRequest) -> DeadlineScheduleReport:
        today = date.today()
        deadlines: List[StatutoryDeadlineItem] = []

        ref = req.case_reference or "CASE-2026-01"
        name = req.borrower_or_accused_name or "Debtor Party"

        # ---------------------------------------------------------
        # SECTION 138 NI ACT DEADLINES
        # ---------------------------------------------------------
        if req.dispute_type.upper() == "SECTION_138":
            memo_d = cls.parse_iso_date(req.dishonour_memo_date)
            notice_d = cls.parse_iso_date(req.notice_received_date)

            if memo_d:
                # 1. 30-Day Statutory Demand Notice Window (S.138(b))
                due_notice = memo_d + timedelta(days=30)
                diff_n = (due_notice - today).days
                urgency_n = cls._get_urgency(diff_n)

                deadlines.append(StatutoryDeadlineItem(
                    deadline_id=f"{ref}_S138_NOTICE",
                    case_reference=ref,
                    title="Dispatch Section 138(b) Statutory Demand Notice",
                    statutory_basis="Section 138 proviso (b) Negotiable Instruments Act",
                    due_date=due_notice.strftime("%Y-%m-%d"),
                    days_remaining=diff_n,
                    urgency_level=urgency_n,
                    mandatory_action="Dispatch demand notice via Speed Post with AD to all accused addresses.",
                    consequence_of_missing="Fatal statutory bar. S.138 complaint cannot be instituted (Kamlesh Kumar).",
                    smart_reminder_dates=cls._get_reminder_dates(due_notice)
                ))

            if notice_d:
                # 2. 15-Day Cure Period Expiry (S.138(c))
                cure_end = notice_d + timedelta(days=15)
                # 3. 30-Day Complaint Filing Window (S.142(1)(b))
                complaint_due = cure_end + timedelta(days=30)
                diff_c = (complaint_due - today).days
                urgency_c = cls._get_urgency(diff_c)

                deadlines.append(StatutoryDeadlineItem(
                    deadline_id=f"{ref}_S142_FILING",
                    case_reference=ref,
                    title="File Criminal Complaint u/s 142(1)(b) before Magistrate",
                    statutory_basis="Section 142(1)(b) NI Act (1-month limitation from cure expiry)",
                    due_date=complaint_due.strftime("%Y-%m-%d"),
                    days_remaining=diff_c,
                    urgency_level=urgency_c,
                    mandatory_action="File formal complaint with sworn affidavit & S.143A 20% deposit petition.",
                    consequence_of_missing="Limitation expires; requires formal S.142(1)(b) condonation application.",
                    smart_reminder_dates=cls._get_reminder_dates(complaint_due)
                ))

        # ---------------------------------------------------------
        # SARFAESI ACT DEADLINES
        # ---------------------------------------------------------
        elif req.dispute_type.upper() == "SARFAESI":
            s13_2_d = cls.parse_iso_date(req.section_13_2_notice_date)
            rep_d = cls.parse_iso_date(req.borrower_representation_date)

            if s13_2_d:
                # 60-Day Notice Schedule (S.13(2))
                due_60 = s13_2_d + timedelta(days=60)
                diff_60 = (due_60 - today).days
                deadlines.append(StatutoryDeadlineItem(
                    deadline_id=f"{ref}_SARFAESI_60D",
                    case_reference=ref,
                    title="Expiry of Section 13(2) 60-Day Statutory Demand Window",
                    statutory_basis="Section 13(2) & 13(4) SARFAESI Act, 2002",
                    due_date=due_60.strftime("%Y-%m-%d"),
                    days_remaining=diff_60,
                    urgency_level=cls._get_urgency(diff_60),
                    mandatory_action="Authorized Officer can take symbolic/physical possession under S.13(4) or apply to CMM u/s 14.",
                    consequence_of_missing="Enforcement delayed; borrowers may alienate secured assets.",
                    smart_reminder_dates=cls._get_reminder_dates(due_60)
                ))

            if rep_d:
                # 15-Day Bank Reply SLA (S.13(3A))
                due_rep = rep_d + timedelta(days=15)
                diff_rep = (due_rep - today).days
                deadlines.append(StatutoryDeadlineItem(
                    deadline_id=f"{ref}_SARFAESI_13_3A",
                    case_reference=ref,
                    title="Bank Reply to Borrower Objection u/s 13(3A)",
                    statutory_basis="Section 13(3A) SARFAESI Act (Mandatory 15-Day SLA)",
                    due_date=due_rep.strftime("%Y-%m-%d"),
                    days_remaining=diff_rep,
                    urgency_level=cls._get_urgency(diff_rep),
                    mandatory_action="Communicate reasoned decision rejecting borrower objections via registered post.",
                    consequence_of_missing="Fatal procedural defect; vitiates subsequent Section 14 CMM possession orders.",
                    smart_reminder_dates=cls._get_reminder_dates(due_rep)
                ))

        # Sort by due date
        deadlines.sort(key=lambda x: x.due_date)
        next_d = deadlines[0] if deadlines else None

        return DeadlineScheduleReport(
            case_reference=ref,
            borrower_name=name,
            dispute_type=req.dispute_type,
            deadlines=deadlines,
            next_immediate_deadline=next_d,
            ical_export_url=f"/api/v1/deadlines/{ref}/calendar.ics",
            calendar_sync_instructions="Download the .ics file and open it in Google Calendar, Outlook, or Apple Calendar for automatic sync and alerts."
        )

    @classmethod
    def generate_ical_content(cls, case_reference: str, deadlines: List[StatutoryDeadlineItem]) -> str:
        """
        Generates standard RFC 5545 iCalendar file content (.ics).
        """
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//JudiQ AI//Statutory Litigation Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:JudiQ Case Deadlines ({case_reference})",
            "X-WR-TIMEZONE:Asia/Kolkata"
        ]

        now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        for d in deadlines:
            dt = cls.parse_iso_date(d.due_date)
            if not dt:
                continue
            dt_start = dt.strftime("%Y%m%d")
            dt_end = (dt + timedelta(days=1)).strftime("%Y%m%d")

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:judiq-{d.deadline_id}-{dt_start}@judiq.ai",
                f"DTSTAMP:{now_str}",
                f"DTSTART;VALUE=DATE:{dt_start}",
                f"DTEND;VALUE=DATE:{dt_end}",
                f"SUMMARY:[CRITICAL DEADLINE] {d.title}",
                f"DESCRIPTION:{d.mandatory_action}\\n\\nStatutory Basis: {d.statutory_basis}\\nConsequence: {d.consequence_of_missing}",
                f"STATUS:CONFIRMED",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:Reminder: {d.title}",
                "TRIGGER:-P7D",  # 7 days before
                "END:VALARM",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:URGENT: {d.title} due tomorrow",
                "TRIGGER:-P1D",  # 1 day before
                "END:VALARM",
                "END:VEVENT"
            ])

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    @staticmethod
    def _get_urgency(days_diff: int) -> str:
        if days_diff < 0:
            return "EXPIRED_NEEDS_CONDONATION"
        elif days_diff == 0:
            return "CRITICAL_TODAY"
        elif days_diff <= 7:
            return "URGENT_7_DAYS"
        elif days_diff <= 14:
            return "UPCOMING_14_DAYS"
        else:
            return "SAFE"

    @staticmethod
    def _get_reminder_dates(target_date: date) -> List[str]:
        return [
            f"{(target_date - timedelta(days=14)).strftime('%Y-%m-%d')} (T-14d)",
            f"{(target_date - timedelta(days=7)).strftime('%Y-%m-%d')} (T-7d)",
            f"{(target_date - timedelta(days=2)).strftime('%Y-%m-%d')} (T-2d)",
            f"{target_date.strftime('%Y-%m-%d')} (T-0d Due Date)"
        ]
