from typing import Dict, Any
from datetime import datetime
from utils import parse_date

class CriminalTimelineEngine:
    """
    S.138-Style mathematical timeline tracking for general Criminal Law.
    Handles S.167 Default Bail, S.468 Limitation Bars, and FIR Delay.
    """

    @classmethod
    def analyze_timelines(cls, case_data: Dict) -> Dict[str, Any]:
        """Calculates critical timelines and generates actionable anomalies."""
        anomalies = []
        opportunities = []
        
        incident_date = parse_date(case_data.get("incident_date"))
        fir_date = parse_date(case_data.get("fir_date"))
        arrest_date = parse_date(case_data.get("arrest_date"))
        chargesheet_date = parse_date(case_data.get("chargesheet_date"))
        today = datetime.now()

        # 1. FIR Delay Calculator
        if incident_date and fir_date:
            delay_days = (fir_date - incident_date).days
            if delay_days > 2 and not case_data.get("delay_explanation"):
                anomalies.append({
                    "type": "FIR_DELAY",
                    "severity": "HIGH",
                    "description": f"FIR delayed by {delay_days} days. Supreme Court mandates strict scrutiny of unexplained delays (Thulia Kali v. State of TN).",
                    "tactical_move": "Cross-examine complainant heavily on consultation and afterthought."
                })

        # 2. S.167(2) Default Bail Calculator
        if arrest_date and not chargesheet_date:
            days_in_custody = (today - arrest_date).days
            offense_type = str(case_data.get("offense_type", "")).upper()
            
            # Identify if offense carries death/life/>10 years (90 days) or less (60 days)
            requires_90_days = offense_type in ["302", "304", "376", "395", "409"] or case_data.get("punishment_years", 0) >= 10
            threshold = 90 if requires_90_days else 60
            
            if days_in_custody > threshold:
                opportunities.append({
                    "type": "S167_DEFAULT_BAIL",
                    "severity": "CRITICAL_OPPORTUNITY",
                    "description": f"Accused in custody for {days_in_custody} days (> {threshold} limit) without charge sheet.",
                    "tactical_move": "IMMEDIATELY file S.167(2) CrPC application for indefeasible Default Bail before charge sheet is filed."
                })
            else:
                anomalies.append({
                    "type": "CUSTODY_TRACKER",
                    "severity": "INFO",
                    "description": f"In custody for {days_in_custody} days. Default bail eligible on day {threshold + 1}."
                })

        # 3. S.468 CrPC Limitation Bar
        if incident_date and fir_date:
            punishment_years = case_data.get("punishment_years", 3)
            limit_years = 0
            if punishment_years == 0: # Fine only
                limit_years = 0.5 # 6 months
            elif punishment_years <= 1:
                limit_years = 1
            elif punishment_years <= 3:
                limit_years = 3
                
            if limit_years > 0:
                elapsed_years = (fir_date - incident_date).days / 365.25
                if elapsed_years > limit_years:
                    opportunities.append({
                        "type": "S468_LIMITATION_BAR",
                        "severity": "FATAL_TO_PROSECUTION",
                        "description": f"Cognizance barred u/s 468 CrPC. Complaint filed {elapsed_years:.1f} years post incident (Limit: {limit_years} years).",
                        "tactical_move": "File S.482 Quashing or object at Cognizance stage."
                    })

        return {
            "anomalies": anomalies,
            "opportunities": opportunities,
            "timeline_health": "CRITICAL" if opportunities else ("WARNING" if anomalies else "STABLE")
        }
