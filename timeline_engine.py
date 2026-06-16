import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from base_scoring_engine import BaseScoringEngine

logger = logging.getLogger(__name__)

from utils import parse_date, days_between

# Hardcoded major court holidays for demonstration
COURT_HOLIDAYS = [
    "2026-01-26", # Republic Day
    "2026-08-15", # Independence Day
    "2026-10-02"  # Gandhi Jacob
]

class TimelineEngine:
    @staticmethod
    def resolve_notice_service(case_data: Dict[str, Any], notice_dt: datetime) -> Dict[str, Any]:
        """Maps notice delivery states to their legal service effect."""
        delivery_date = case_data.get("notice_delivery_date")
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
        """If limitation ends on a weekend or court holiday, it extends to the next working day."""
        while target_date.weekday() >= 5 or target_date.strftime("%Y-%m-%d") in COURT_HOLIDAYS:
            target_date += timedelta(days=1)
        return target_date

    @staticmethod
    def generate_timeline_data(case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate structured timeline milestones for visualization"""
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
            status = "success" if days_from_cheque and days_from_cheque <= 90 else "error"
            steps.append({"milestone": "Cheque Presented", "date": presentation_date, "status": status, "details": f"Presented to bank. Validity: {days_from_cheque} days."})
            
        if dishonour_date:
            steps.append({"milestone": "Cheque Dishonoured", "date": dishonour_date, "status": "error", "details": f"Reason: {case_data.get('dishonour_reason', 'Funds Insufficient')}"})
            
        if notice_date:
            days_from_dishonour = days_between(dishonour_date, notice_date)
            status = "success" if days_from_dishonour and days_from_dishonour <= 30 else "error"
            steps.append({"milestone": "Notice Dispatched", "date": notice_date, "status": status, "details": f"Statutory notice sent within {days_from_dishonour} days."})
            
        if filing_date:
            steps.append({"milestone": "Complaint Filed", "date": filing_date, "status": "success", "details": "Case entered jurisdictional court."})
            
        return steps

    @staticmethod
    def generate_timeline(case_data: Dict[str, Any]) -> List[str]:
        """Legacy string-based timeline"""
        data = TimelineEngine.generate_timeline_data(case_data)
        return [f"{s['milestone']} ({s['date']}): {s['details']}" for s in data]

    @staticmethod
    def check_limitation(case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if case is within limitation period"""
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
        
        # Calculate notice timing
        notice_gap = days_between(dishonour_date, notice_date)
        if notice_gap and notice_gap > 30:
            return {
                "is_barred": True,
                "days_remaining": 0,
                "status": "NOTICE_LATE",
                "message": f"Notice sent {notice_gap} days after dishonour (exceeds 30-day limit)"
            }
        
        # Calculate limitation
        notice_dt = parse_date(notice_date)
        if notice_dt:
            service_resolution = TimelineEngine.resolve_notice_service(case_data, notice_dt)
            if service_resolution["status"] == "NOTICE_INVALID":
                return {
                    "is_barred": True,
                    "days_remaining": 0,
                    "status": "NOTICE_INVALID",
                    "message": service_resolution["message"],
                    "fatal_defect": service_resolution["fatal_defect"],
                }
            service_dt = service_resolution["service_dt"]
            cause_of_action = service_dt + timedelta(days=15)
            limitation_date = TimelineEngine.adjust_for_holidays(cause_of_action + timedelta(days=30))
            today = datetime.now()
            
            if filing_date:
                filing_dt = parse_date(filing_date)
                if filing_dt:
                    if filing_dt > limitation_date:
                        delay_days = (filing_dt - limitation_date).days
                        return {
                            "is_barred": True,
                            "days_remaining": 0,
                            "delay_days": delay_days,
                            "status": "TIME_BARRED",
                            "message": f"Filed {delay_days} days after limitation period. Condonation of Delay (Section 142(b)) REQUIRED.",
                            "condonation_required": True
                        }
                    else:
                        return {
                            "is_barred": False,
                            "days_remaining": 0,
                            "status": "FILED_IN_TIME",
                            "message": "Complaint filed within the limitation period."
                        }
            
            if today > limitation_date:
                days_over = (today - limitation_date).days
                return {
                    "is_barred": True,
                    "days_remaining": 0,
                    "days_overdue": days_over,
                    "status": "EXPIRED",
                    "message": f"Limitation expired {days_over} days ago. Condonation of Delay REQUIRED.",
                    "condonation_required": True
                }
            else:
                days_left = (limitation_date - today).days
                return {
                    "is_barred": False,
                    "days_remaining": days_left,
                    "limitation_date": limitation_date.strftime("%Y-%m-%d"),
                    "status": "WITHIN_TIME",
                    "message": f"{days_left} days remaining to file complaint"
                }
        
        return {
            "is_barred": False,
            "days_remaining": 30,
            "status": "ASSUMED_VALID",
            "message": "Assumed within limitation (verify dates)"
        }

    @staticmethod
    def check_criminal_limitation(case_data: Dict[str, Any]) -> Dict[str, Any]:
        """BNSS S.504 (formerly CrPC 468) limitation checks for criminal offenses"""
        incident_date = case_data.get("transaction_date") or case_data.get("incident_date")
        offense_type = str(case_data.get("offense_type", "")).upper()
        
        if not incident_date:
            return {"status": "UNKNOWN", "message": "No incident date provided."}
            
        incident_dt = parse_date(incident_date)
        if not incident_dt:
            return {"status": "UNKNOWN", "message": "Invalid date format."}
            
        # Determine limitation based on punishment severity
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
            limit_years = 3 # Default for others
            
        limitation_date = TimelineEngine.adjust_for_holidays(incident_dt.replace(year=incident_dt.year + limit_years))
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
