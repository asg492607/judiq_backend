import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

from utils import parse_date, days_between

class TimelineEngine:
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
            cause_of_action = notice_dt + timedelta(days=15)
            limitation_date = cause_of_action + timedelta(days=30)
            today = datetime.now()
            
            if filing_date:
                filing_dt = parse_date(filing_date)
                if filing_dt and filing_dt > limitation_date:
                    delay_days = (filing_dt - limitation_date).days
                    return {
                        "is_barred": True,
                        "days_remaining": 0,
                        "delay_days": delay_days,
                        "status": "TIME_BARRED",
                        "message": f"Filed {delay_days} days after limitation period. Condonation of Delay (Section 142(b)) REQUIRED.",
                        "condonation_required": True
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
