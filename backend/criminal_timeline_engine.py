from typing import Dict, Any, List
from datetime import datetime
from utils import parse_date
class CriminalTimelineEngine:
    @classmethod
    def analyze_timelines(cls, case_data: Dict) -> Dict[str, Any]:
        anomalies = []
        opportunities = []
        incident_date = parse_date(case_data.get("incident_date"))
        fir_date = parse_date(case_data.get("fir_date"))
        arrest_date = parse_date(case_data.get("arrest_date"))
        chargesheet_date = parse_date(case_data.get("chargesheet_date"))
        today = datetime.now()

        if incident_date and fir_date:
            delay_days = (fir_date - incident_date).days
            if delay_days > 2 and not case_data.get("delay_explanation"):
                anomalies.append({
                    "type": "FIR_DELAY",
                    "severity": "HIGH",
                    "description": f"FIR delayed by {delay_days} days. Supreme Court mandates strict scrutiny of unexplained delays (Thulia Kali v. State of TN).",
                    "tactical_move": "Cross-examine complainant heavily on consultation and afterthought."
                })
        if arrest_date and not chargesheet_date:
            days_in_custody = (today - arrest_date).days
            offense_type = str(case_data.get("offense_type", "")).upper()
            requires_90_days = offense_type in ["302", "304", "376", "395", "409"] or case_data.get("punishment_years", 0) >= 10
            threshold = 90 if requires_90_days else 60
            if days_in_custody > threshold:
                opportunities.append({
                    "type": "S167_DEFAULT_BAIL",
                    "severity": "CRITICAL_OPPORTUNITY",
                    "description": f"Accused in custody for {days_in_custody} days (> {threshold} limit) without charge sheet.",
                    "tactical_move": "IMMEDIATELY file S.167(2) CrPC / S.187 BNSS application for indefeasible Default Bail before charge sheet is filed."
                })
            else:
                anomalies.append({
                    "type": "CUSTODY_TRACKER",
                    "severity": "INFO",
                    "description": f"In custody for {days_in_custody} days. Default bail eligible on day {threshold + 1}."
                })
        if incident_date and fir_date:
            punishment_years = case_data.get("punishment_years", 3)
            limit_years = 0
            if punishment_years == 0:
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
                        "description": f"Cognizance barred u/s 468 CrPC / S.504 BNSS. Complaint filed {elapsed_years:.1f} years post incident (Limit: {limit_years} years).",
                        "tactical_move": "File Quashing or object at Cognizance stage."
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
        if case_data.get("arrest_date"):
            steps.append(f"Accused Arrested ({case_data['arrest_date']}): Remand proceedings initiated u/s 167 CrPC.")
        if case_data.get("chargesheet_date"):
            steps.append(f"Charge Sheet Filed ({case_data['chargesheet_date']}): Investigation completed u/s 173 CrPC.")
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
        today = datetime.now()
        if today > anniversary:
            return {
                "is_barred": True,
                "status": "TIME_BARRED",
                "message": f"Barred by BNSS S.504 / CrPC S.468. Limitation expired on {anniversary.strftime('%Y-%m-%d')}."
            }
        return {
            "is_barred": False,
            "status": "WITHIN_TIME",
            "message": f"Within limitation period. Expires on {anniversary.strftime('%Y-%m-%d')}."
        }
