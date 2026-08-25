import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from base_scoring_engine import BaseScoringEngine
logger = logging.getLogger(__name__)
from utils import parse_date, days_between
COURT_HOLIDAYS = [
    "2026-01-26",               
    "2026-08-15",                   
    "2026-10-02"                  
]
class TimelineEngine:
    @staticmethod
    def resolve_notice_service(case_data: Dict[str, Any], notice_dt: datetime) -> Dict[str, Any]:
        delivery_date = case_data.get("notice_received_date") or case_data.get("notice_delivery_date")
        normalized = BaseScoringEngine.normalize_notice_service_status(case_data)
        if normalized["bucket"] == "DEEMED_SERVICE":
            return {
                "status": "DEEMED_SERVICE",
                "service_dt": parse_date(delivery_date) or notice_dt,
                "deemed_service": True,
                "message": f"Notice treated as deemed service ({normalized['label']}).",
            }
        if normalized["bucket"] == "FAILED_SERVICE":
            return {
                "status": "NOTICE_INVALID",
                "fatal_defect": f"Delivery failure ('{normalized['label']}') invalidates statutory notice.",
                "message": f"Notice service failed: {normalized['label']}.",
            }
        if normalized["bucket"] == "UNCERTAIN_SERVICE":
            return {
                "status": "NOTICE_INVALID",
                "fatal_defect": f"Ambiguous delivery ('{normalized['label']}') requires fresh service proof.",
                "message": f"Notice delivery remains legally uncertain: {normalized['label']}.",
            }
        if normalized["bucket"] == "VALID_SERVICE":
            return {
                "status": "VALID_SERVICE",
                "service_dt": parse_date(delivery_date) or notice_dt,
                "deemed_service": False,
                "message": "Notice shown as delivered.",
            }
        return {
            "status": "ASSUMED_SERVICE",
            "service_dt": parse_date(delivery_date) or (notice_dt + timedelta(days=30)),
            "deemed_service": True,
            "message": "Delivery proof incomplete; applying conservative deemed-service fallback.",
        }
    @staticmethod
    def adjust_for_holidays(target_date: datetime) -> datetime:
        while target_date.weekday() >= 5 or target_date.strftime("%Y-%m-%d") in COURT_HOLIDAYS:
            target_date += timedelta(days=1)
        return target_date
    @staticmethod
    def generate_timeline_data(case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        steps = []
        transaction_date = case_data.get("transaction_date")
        cheque_date = case_data.get("cheque_date")
        presentation_date = case_data.get("presentation_date")
        dishonour_date = case_data.get("dishonour_date")
        notice_date = case_data.get("notice_date")
        filing_date = case_data.get("filing_date")
        if transaction_date:
            steps.append({"milestone": "Debt Created", "date": transaction_date, "status": "success", "details": "Transaction or debt creation event."})
        if cheque_date:
            steps.append({"milestone": "Cheque Issued", "date": cheque_date, "status": "success", "details": f"Cheque No. {case_data.get('cheque_number', 'N/A')} issued."})
        if presentation_date:
            days_from_cheque = days_between(cheque_date, presentation_date)
            status = "success" if days_from_cheque is not None and 0 <= days_from_cheque <= 92 else "error"
            steps.append({"milestone": "Cheque Presented", "date": presentation_date, "status": status, "details": f"Presented to bank. Validity: {days_from_cheque} days."})
        if dishonour_date:
            steps.append({"milestone": "Cheque Dishonoured", "date": dishonour_date, "status": "error", "details": f"Reason: {case_data.get('dishonour_reason', 'Funds Insufficient')}"})
        if notice_date:
            days_from_dishonour = days_between(dishonour_date, notice_date)
            status = "success" if days_from_dishonour is not None and 0 <= days_from_dishonour <= 30 else "error"
            steps.append({"milestone": "Notice Dispatched", "date": notice_date, "status": status, "details": f"Statutory notice sent within {days_from_dishonour} days."})
        if filing_date:
            steps.append({"milestone": "Complaint Filed", "date": filing_date, "status": "success", "details": "Case entered jurisdictional court."})
        return steps
    @staticmethod
    def generate_timeline(case_data: Dict[str, Any]) -> List[str]:
        data = TimelineEngine.generate_timeline_data(case_data)
        return [f"{s['milestone']} ({s['date']}): {s['details']}" for s in data]
    @staticmethod
    def check_limitation(case_data: Dict[str, Any]) -> Dict[str, Any]:
        dishonour_date = case_data.get("dishonour_date")
        notice_date = case_data.get("notice_date")
        filing_date = case_data.get("filing_date")
        if not all([dishonour_date, notice_date]):
            if case_data.get("limitation_barred") or case_data.get("limitation_issue"):
                return {
                    "is_barred": True,
                    "days_remaining": 0,
                    "status": "TIME_BARRED",
                    "message": "Limitation period expired (explicitly specified by user)."
                }
            return {
                "is_barred": False,
                "days_remaining": None,
                "status": "INCOMPLETE_DATA",
                "message": "Insufficient date information to calculate limitation"
            }
        notice_gap = days_between(dishonour_date, notice_date)
        if notice_gap is not None and notice_gap < 0:
            return {
                "is_barred": True,
                "days_remaining": 0,
                "status": "INVALID_CHRONOLOGY",
                "message": "Notice date cannot be before the dishonour date.",
                "fatal_defect": "Notice predates cheque dishonour."
            }
        if notice_gap is not None and notice_gap > 30:
            return {
                "is_barred": True,
                "days_remaining": 0,
                "status": "NOTICE_LATE",
                "message": f"Notice sent {notice_gap} days after dishonour (exceeds 30-day limit)"
            }
        notice_dt = parse_date(notice_date)
        if notice_dt:
            service_resolution = TimelineEngine.resolve_notice_service(case_data, notice_dt)
            if service_resolution["status"] == "NOTICE_INVALID":
                return {
                    "is_barred": True,
                    "days_remaining": 0,
                    "status": "NOTICE_INVALID",
                    "message": service_resolution["message"],
                    "fatal_defect": service_resolution.get("fatal_defect", "Notice service failed"),
                }
            
            # Strict General Clauses Act Section 9 & Limitation Act Section 4 Date Arithmetic:
            # 1. Day of service (T0) is excluded from computation.
            # 2. Statutory 15-day cure window runs from T0 + 1 day to T0 + 15 days (ending at 23:59:59).
            # 3. Cause of action strictly arises on Day 16 (T0 + 16 days).
            # 4. 30-day limitation period commences on Day 16 and ends on Day 45 (T0 + 45 days).
            service_dt = service_resolution["service_dt"]
            cure_window_start = service_dt + timedelta(days=1)
            cure_window_end = service_dt + timedelta(days=15)
            earliest_filing_date = service_dt + timedelta(days=16)
            statutory_limitation_raw = earliest_filing_date + timedelta(days=29) # Total 30 calendar days (Days 16..45)
            limitation_date = TimelineEngine.adjust_for_holidays(statutory_limitation_raw)
            today = datetime.now().date()
            
            common_meta = {
                "service_date": service_dt.strftime("%Y-%m-%d"),
                "cure_window_start": cure_window_start.strftime("%Y-%m-%d"),
                "cure_window_end": cure_window_end.strftime("%Y-%m-%d"),
                "earliest_filing_date": earliest_filing_date.strftime("%Y-%m-%d"),
                "limitation_expiry_raw": statutory_limitation_raw.strftime("%Y-%m-%d"),
                "limitation_date": limitation_date.strftime("%Y-%m-%d"),
                "holiday_rollover_applied": limitation_date > statutory_limitation_raw
            }

            if filing_date:
                filing_dt = parse_date(filing_date)
                if filing_dt:
                    if filing_dt.date() < earliest_filing_date.date():
                        res = {
                            "is_barred": False,
                            "is_premature": True,
                            "days_remaining": 0,
                            "status": "PREMATURE_FILING",
                            "message": f"Complaint filed on {filing_dt.strftime('%Y-%m-%d')} before the 15-day statutory cure window expired (ends on {cure_window_end.strftime('%Y-%m-%d')}). Mandatory dismissal under Yogendra Pratap Singh vs. Savitri Pandey.",
                            "fatal_defect": "Premature complaint filed before cause of action arose."
                        }
                        res.update(common_meta)
                        return res
                    if filing_dt.date() > limitation_date.date():
                        delay_days = (filing_dt.date() - limitation_date.date()).days
                        res = {
                            "is_barred": True,
                            "days_remaining": 0,
                            "delay_days": delay_days,
                            "status": "TIME_BARRED",
                            "message": f"Filed {delay_days} days after statutory limitation ({limitation_date.strftime('%Y-%m-%d')}). Condonation of Delay application under Section 142(1)(b) MANDATORY.",
                            "condonation_required": True
                        }
                        res.update(common_meta)
                        return res
                    else:
                        res = {
                            "is_barred": False,
                            "days_remaining": (limitation_date.date() - filing_dt.date()).days,
                            "status": "FILED_IN_TIME",
                            "message": "Complaint instituted within statutory limitation period."
                        }
                        res.update(common_meta)
                        return res

            limitation_day = limitation_date.date()
            if today > limitation_day:
                days_over = (today - limitation_day).days
                res = {
                    "is_barred": True,
                    "days_remaining": 0,
                    "days_overdue": days_over,
                    "status": "EXPIRED",
                    "message": f"Statutory limitation expired {days_over} days ago on {limitation_date.strftime('%Y-%m-%d')}. Condonation of Delay (Section 142(1)(b)) REQUIRED.",
                    "condonation_required": True
                }
                res.update(common_meta)
                return res
            else:
                days_left = (limitation_day - today).days
                res = {
                    "is_barred": False,
                    "days_remaining": days_left,
                    "status": "WITHIN_TIME",
                    "message": f"{days_left} days remaining to file complaint (Deadline: {limitation_date.strftime('%Y-%m-%d')})"
                }
                res.update(common_meta)
                return res
        return {
            "is_barred": False,
            "days_remaining": 30,
            "status": "ASSUMED_VALID",
            "message": "Assumed within limitation (verify dates)"
        }
    @staticmethod
    def check_criminal_limitation(case_data: Dict[str, Any]) -> Dict[str, Any]:
        incident_date = case_data.get("transaction_date") or case_data.get("incident_date")
        offense_type = str(case_data.get("offense_type", "")).upper()
        if not incident_date:
            return {"status": "UNKNOWN", "message": "No incident date provided."}
        incident_dt = parse_date(incident_date)
        if not incident_dt:
            return {"status": "UNKNOWN", "message": "Invalid date format."}
        no_limitation_crimes = ["420", "318", "302", "103", "376", "64", "392", "309"]
        one_year_limit_crimes = ["506", "351", "323", "115"]
        three_year_limit_crimes = ["498A", "85", "406", "316"]
        limit_years = 0
        if offense_type in no_limitation_crimes:
            return {"is_barred": False, "status": "NO_LIMITATION", "message": "Offense carries >3 years punishment. No limitation period applies."}
        elif offense_type in one_year_limit_crimes:
            limit_years = 1
        elif offense_type in three_year_limit_crimes:
            limit_years = 3
        else:
            limit_years = 3                     
        try:
            anniversary = incident_dt.replace(year=incident_dt.year + limit_years)
        except ValueError:
            anniversary = incident_dt.replace(year=incident_dt.year + limit_years, day=28)
        limitation_date = TimelineEngine.adjust_for_holidays(anniversary)
        today = datetime.now()
        if today > limitation_date:
            return {
                "is_barred": True,
                "status": "TIME_BARRED",
                "message": f"Barred by BNSS S.504. Limitation expired on {limitation_date.strftime('%Y-%m-%d')}."
            }
        return {
            "is_barred": False,
            "status": "WITHIN_TIME",
            "message": f"Within limitation period. Expires on {limitation_date.strftime('%Y-%m-%d')}."
        }
