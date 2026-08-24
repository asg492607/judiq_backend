from typing import Dict, Any, List
from datetime import datetime
from utils import parse_date

class CriminalTimelineEngine:
    """
    Analyzes criminal litigation timelines, FIR delay impact, investigation remand windows,
    default bail eligibility (S.167 CrPC / S.187 BNSS), and statutory limitation periods.
    """

    @classmethod
    def analyze_timelines(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        anomalies = []
        opportunities = []

        incident_date = parse_date(case_data.get("incident_date"))
        fir_date = parse_date(case_data.get("fir_date"))
        arrest_date = parse_date(case_data.get("arrest_date"))
        chargesheet_date = parse_date(case_data.get("chargesheet_date"))
        today = datetime.now()

        # 1. Delay in Lodging FIR Analysis
        if incident_date and fir_date:
            delay_days = (fir_date - incident_date).days
            if delay_days > 2 and not case_data.get("delay_explanation"):
                anomalies.append({
                    "type": "FIR_DELAY",
                    "severity": "HIGH",
                    "description": f"FIR delayed by {delay_days} days without statutory or factual explanation. Supreme Court mandates strict scrutiny of unexplained delays (Thulia Kali v. State of TN).",
                    "tactical_move": "Cross-examine informant heavily on consultations, deliberation, and afterthought."
                })

        # 2. Section 167(2) CrPC / Section 187 BNSS Default Bail Tracker
        days_in_custody = int(case_data.get("days_in_custody") or 0)
        if arrest_date and not chargesheet_date and days_in_custody == 0:
            days_in_custody = (today - arrest_date).days

        if days_in_custody > 0 and not chargesheet_date and not case_data.get("chargesheet_filed"):
            offense_type = str(case_data.get("offense_type", "")).upper()
            punishment_years = int(case_data.get("max_punishment_years") or case_data.get("punishment_years") or 7)

            requires_90_days = any(x in offense_type for x in ["302", "304", "376", "395", "409", "103", "64", "310", "316", "MURDER", "RAPE", "NDPS"]) or punishment_years >= 10
            threshold = 90 if requires_90_days else 60

            if days_in_custody >= threshold:
                opportunities.append({
                    "type": "S167_DEFAULT_BAIL",
                    "severity": "CRITICAL_OPPORTUNITY",
                    "description": f"Accused in custody for {days_in_custody} days (>= {threshold} days statutory threshold) without charge sheet.",
                    "tactical_move": "IMMEDIATELY file S.167(2) CrPC / S.187 BNSS application for indefeasible Default Bail before police file the charge sheet (Ritu Chhabaria v. Union of India, 2023; Bikramjit Singh v. State of Punjab)."
                })
            else:
                anomalies.append({
                    "type": "CUSTODY_TRACKER",
                    "severity": "INFO",
                    "description": f"Accused in custody for {days_in_custody} days. Default bail rights accrue on Day {threshold + 1}."
                })

        # 3. Cognizance Limitation Period Analysis (S.468 CrPC / S.514 BNSS)
        if incident_date and fir_date:
            punishment_years = int(case_data.get("max_punishment_years") or case_data.get("punishment_years") or 3)
            limit_years = 0
            if punishment_years <= 0.5:
                limit_years = 0.5
            elif punishment_years <= 1:
                limit_years = 1
            elif punishment_years <= 3:
                limit_years = 3

            if limit_years > 0:
                elapsed_years = (fir_date - incident_date).days / 365.25
                if elapsed_years > limit_years:
                    opportunities.append({
                        "type": "S504_LIMITATION_BAR",
                        "severity": "FATAL_TO_PROSECUTION",
                        "description": f"Cognizance barred under S.468 CrPC / S.514 BNSS. Complaint filed {elapsed_years:.1f} years post-incident (Statutory Limit: {limit_years} year(s)).",
                        "tactical_move": "File Quashing petition or object to taking of cognizance (State of Punjab v. Sarwan Singh)."
                    })

        return {
            "anomalies": anomalies,
            "opportunities": opportunities,
            "timeline_health": "CRITICAL" if opportunities else ("WARNING" if anomalies else "STABLE")
        }

    @classmethod
    def generate_timeline(cls, case_data: Dict[str, Any]) -> List[str]:
        steps = []
        if case_data.get("incident_date"):
            steps.append(f"Incident Occurred ({case_data['incident_date']}): Date of alleged crime.")
        if case_data.get("fir_date"):
            steps.append(f"FIR Lodged ({case_data['fir_date']}): Police Station {case_data.get('police_station', 'N/A')}.")
        if case_data.get("arrest_date") or case_data.get("days_in_custody"):
            custody_str = f" ({case_data['days_in_custody']} days undergone)" if case_data.get("days_in_custody") else ""
            steps.append(f"Accused in Custody{custody_str}: Remand proceedings initiated u/s 167 CrPC / S.187 BNSS.")
        if case_data.get("chargesheet_date"):
            steps.append(f"Charge Sheet Filed ({case_data['chargesheet_date']}): Investigation completed u/s 173 CrPC / S.193 BNSS.")
        if not steps:
            steps.append("Pre-litigation Stage: Investigation ongoing or complaint pending.")
        return steps

    @classmethod
    def detect_timeline_anomalies(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = cls.analyze_timelines(case_data)
        anomalies = result.get("anomalies", [])
        for opp in result.get("opportunities", []):
            anomalies.append({
                "type": opp["type"],
                "text": opp["description"],
                "severity": opp["severity"]
            })
        return anomalies

    @classmethod
    def check_limitation(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        return cls.check_criminal_limitation(case_data)

    @classmethod
    def check_criminal_limitation(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        incident_date = case_data.get("transaction_date") or case_data.get("incident_date")
        offense_type = str(case_data.get("offense_type", "")).upper()
        punishment_years = int(case_data.get("max_punishment_years") or case_data.get("punishment_years") or 3)

        if not incident_date:
            return {"status": "UNKNOWN", "message": "No incident date provided."}

        incident_dt = parse_date(incident_date)
        if not incident_dt:
            return {"status": "UNKNOWN", "message": "Invalid date format."}

        if punishment_years > 3 or any(x in offense_type for x in ["420", "318", "302", "103", "376", "64", "392", "309", "395", "310", "NDPS", "PMLA"]):
            return {"is_barred": False, "status": "NO_LIMITATION", "message": "Offence carries > 3 years imprisonment. Statutory limitation does not apply."}

        limit_years = 1 if punishment_years <= 1 or any(x in offense_type for x in ["506", "351", "323", "115"]) else 3

        try:
            anniversary = incident_dt.replace(year=incident_dt.year + limit_years)
        except ValueError:
            anniversary = incident_dt.replace(year=incident_dt.year + limit_years, day=28)

        today = datetime.now()
        if today > anniversary:
            return {
                "is_barred": True,
                "status": "TIME_BARRED",
                "message": f"Barred by BNSS S.514 / CrPC S.468. Limitation expired on {anniversary.strftime('%Y-%m-%d')}."
            }

        return {
            "is_barred": False,
            "status": "WITHIN_TIME",
            "message": f"Within limitation period. Expires on {anniversary.strftime('%Y-%m-%d')}."
        }
