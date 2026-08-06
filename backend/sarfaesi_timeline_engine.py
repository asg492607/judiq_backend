import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from utils import parse_date, days_between

logger = logging.getLogger(__name__)

class SarfaesiTimelineEngine:
    @staticmethod
    def generate_timeline_data(case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        steps = []
        npa_date = case_data.get("npa_date")
        notice_13_2_date = case_data.get("notice_13_2_date")
        borrower_rep_date = case_data.get("borrower_representation_date")
        bank_reply_date = case_data.get("bank_reply_13_3a_date")
        possession_date = case_data.get("possession_13_4_date")
        auction_date = case_data.get("auction_notice_date")
        sa_filing_date = case_data.get("sa_filing_date")

        if npa_date:
            steps.append({
                "milestone": "NPA Classification",
                "date": npa_date,
                "status": "warning",
                "details": "Account classified as Non-Performing Asset by Lender."
            })

        if notice_13_2_date:
            days_from_npa = days_between(npa_date, notice_13_2_date) if npa_date else None
            steps.append({
                "milestone": "Section 13(2) Demand Notice",
                "date": notice_13_2_date,
                "status": "success",
                "details": f"60-day demand notice issued to borrower/guarantors. ({days_from_npa or 'N/A'} days post-NPA)"
            })

        if borrower_rep_date:
            days_from_13_2 = days_between(notice_13_2_date, borrower_rep_date) if notice_13_2_date else None
            status = "success" if days_from_13_2 is not None and days_from_13_2 <= 60 else "info"
            steps.append({
                "milestone": "Borrower Representation U/S 13(3A)",
                "date": borrower_rep_date,
                "status": status,
                "details": f"Borrower submitted objections within {days_from_13_2 or 'N/A'} days."
            })

        if bank_reply_date:
            days_to_reply = days_between(borrower_rep_date, bank_reply_date) if borrower_rep_date else None
            is_valid_reply = days_to_reply is not None and days_to_reply <= 15
            steps.append({
                "milestone": "Bank Reasoned Reply U/S 13(3A)",
                "date": bank_reply_date,
                "status": "success" if is_valid_reply else "error",
                "details": f"Bank communicated decision in {days_to_reply or 'N/A'} days (Mandatory statutory cap: 15 days)."
            })

        if possession_date:
            days_from_13_2 = days_between(notice_13_2_date, possession_date) if notice_13_2_date else None
            status = "success" if days_from_13_2 is not None and days_from_13_2 >= 60 else "error"
            steps.append({
                "milestone": "Section 13(4) Possession Measure",
                "date": possession_date,
                "status": status,
                "details": f"Secured Creditor took symbolic/physical possession. ({days_from_13_2 or 'N/A'} days post-Notice)"
            })

        if auction_date:
            days_from_possession = days_between(possession_date, auction_date) if possession_date else None
            steps.append({
                "milestone": "Rule 8(6)/9(1) Sale Auction Notice",
                "date": auction_date,
                "status": "info",
                "details": f"Public auction notice published. 30-day notice period mandated."
            })

        if sa_filing_date:
            days_from_measure = days_between(possession_date, sa_filing_date) if possession_date else None
            is_timely = days_from_measure is not None and days_from_measure <= 45
            steps.append({
                "milestone": "Section 17 DRT Securitisation Application",
                "date": sa_filing_date,
                "status": "success" if is_timely else "error",
                "details": f"Application filed before DRT within {days_from_measure or 'N/A'} days (Limitation: 45 days)."
            })

        return steps

    @staticmethod
    def generate_timeline(case_data: Dict[str, Any]) -> List[str]:
        data = SarfaesiTimelineEngine.generate_timeline_data(case_data)
        return [f"{s['milestone']} ({s['date']}): {s['details']}" for s in data]

    @staticmethod
    def check_limitation(case_data: Dict[str, Any]) -> Dict[str, Any]:
        notice_13_2 = case_data.get("notice_13_2_date")
        borrower_rep = case_data.get("borrower_representation_date")
        bank_reply = case_data.get("bank_reply_13_3a_date")
        possession_date = case_data.get("possession_13_4_date")
        sa_filing = case_data.get("sa_filing_date")

        issues = []
        is_barred = False
        fatal_defect = None

        # Check 1: Section 13(2) 60-day mandatory waiting period before 13(4) possession
        if notice_13_2 and possession_date:
            days_wait = days_between(notice_13_2, possession_date)
            if days_wait is not None and days_wait < 60:
                is_barred = True
                fatal_defect = f"PREMATURE_POSSESSION: Section 13(4) action taken in {days_wait} days, breaching 60-day mandatory cure period U/S 13(2)."
                issues.append(fatal_defect)

        # Check 2: Section 13(3A) 15-day bank reply requirement
        if borrower_rep and bank_reply:
            reply_days = days_between(borrower_rep, bank_reply)
            if reply_days is not None and reply_days > 15:
                is_barred = True
                fatal_defect = f"SECTION_13_3A_BREACH: Bank delayed reasoned reply to {reply_days} days (statutory maximum is 15 days as per Mardia Chemicals rule)."
                issues.append(fatal_defect)
        elif borrower_rep and possession_date and not bank_reply:
            is_barred = True
            fatal_defect = "MISSING_13_3A_REPLY: Bank took Section 13(4) possession without communicating reasoned decision on borrower's Section 13(3A) objections."
            issues.append(fatal_defect)

        # Check 3: Section 17 DRT Securitisation Application 45-day limitation
        if possession_date and sa_filing:
            sa_days = days_between(possession_date, sa_filing)
            if sa_days is not None and sa_days > 45:
                is_barred = True
                fatal_defect = f"SA_LIMITATION_EXPIRED: Securitisation Application filed in DRT after {sa_days} days (exceeding strict 45-day statutory limit U/S 17(1))."
                issues.append(fatal_defect)

        status = "COMPLIANT"
        if is_barred:
            status = "EXPIRED" if (fatal_defect and "EXPIRED" in fatal_defect) else "BREACHED"

        return {
            "is_barred": is_barred,
            "status": status,
            "fatal_defect": fatal_defect,
            "issues": issues,
            "message": fatal_defect if fatal_defect else "All statutory timelines under SARFAESI Act compliant."
        }
