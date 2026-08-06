import logging
from typing import Dict, List, Optional
logger = logging.getLogger(__name__)
JUDICIAL_DATABASE = {
    "courts": {
        "JMFC Pune": {
            "court_id": "MH-PUN-JMFC",
            "avg_disposal_days": 420,
            "settlement_rate_pct": 38,
            "conviction_rate_pct": 62,
            "common_objections": ["Notice Defects", "Jurisdiction Questions", "Evidence Gaps"],
            "avg_bail_grant_days": 14,
            "cheque_bounce_pendency": "HIGH",
            "region": "Pune, Maharashtra"
        },
        "JMFC Mumbai": {
            "court_id": "MH-MUM-JMFC",
            "avg_disposal_days": 680,
            "settlement_rate_pct": 45,
            "conviction_rate_pct": 55,
            "common_objections": ["S.141 Averment", "Financial Capacity", "Service of Notice"],
            "avg_bail_grant_days": 21,
            "cheque_bounce_pendency": "VERY HIGH",
            "region": "Mumbai, Maharashtra"
        },
        "Sessions Court Nagpur": {
            "court_id": "MH-NAG-SC",
            "avg_disposal_days": 540,
            "settlement_rate_pct": 32,
            "conviction_rate_pct": 58,
            "common_objections": ["Witness Credibility", "Chargesheet Gaps", "Bail Conditions"],
            "avg_bail_grant_days": 18,
            "cheque_bounce_pendency": "MODERATE",
            "region": "Nagpur, Maharashtra"
        },
        "High Court of Bombay": {
            "court_id": "MH-HC",
            "avg_disposal_days": 900,
            "settlement_rate_pct": 29,
            "conviction_rate_pct": 71,
            "common_objections": ["Maintainability", "Premature Filing", "Jurisdictional Errors"],
            "avg_bail_grant_days": 30,
            "cheque_bounce_pendency": "LOW",
            "region": "Mumbai, Maharashtra"
        },
        "Special POCSO Court, Pune": {
            "court_id": "MH-PUN-POCSO",
            "avg_disposal_days": 365,
            "settlement_rate_pct": 8,
            "conviction_rate_pct": 74,
            "common_objections": ["Medical Report Quality", "164-Statement Consistency"],
            "avg_bail_grant_days": 45,
            "cheque_bounce_pendency": "N/A",
            "region": "Pune, Maharashtra"
        }
    },
    "judges": {
        "Judge Mehta (Pune JMFC)": {
            "judge_id": "MH-J-001",
            "bail_grant_rate_pct": 73,
            "conviction_rate_pct": 61,
            "avg_hearing_duration_min": 18,
            "strictness_score": 6.2,
            "known_for": "Strong on notice compliance; lenient on first-time offenders",
            "common_questions": [
                "How was the notice delivered and do you have proof?",
                "Is the cheque the original or a photocopy?",
                "What was the exact purpose of the loan?"
            ],
            "temperament": "Balanced"
        },
        "Judge Sharma (Mumbai JMFC)": {
            "judge_id": "MH-J-002",
            "bail_grant_rate_pct": 48,
            "conviction_rate_pct": 71,
            "avg_hearing_duration_min": 12,
            "strictness_score": 8.1,
            "known_for": "Very strict on S.141; dismisses cases with weak notice service",
            "common_questions": [
                "Have all directors been named in the complaint?",
                "Was there a formal written agreement for this loan?",
                "Why did you accept the cheque if no written agreement exists?"
            ],
            "temperament": "Pro-Complainant"
        },
        "Judge Patil (Sessions Court Nagpur)": {
            "judge_id": "MH-J-003",
            "bail_grant_rate_pct": 62,
            "conviction_rate_pct": 58,
            "avg_hearing_duration_min": 25,
            "strictness_score": 5.5,
            "known_for": "Fair; looks for custodial necessity before denying bail",
            "common_questions": [
                "Is custodial interrogation genuinely required?",
                "Has the investigation been completed?",
                "What is the flight risk of the accused?"
            ],
            "temperament": "Balanced"
        }
    }
}
class JudicialIntelligenceEngine:
    def get_court_analytics(self, court_name: str) -> Dict:
        courts = JUDICIAL_DATABASE["courts"]
        if court_name in courts:
            return courts[court_name]
        for name, data in courts.items():
            if court_name and (name.lower() in court_name.lower() or court_name.lower() in name.lower()):
                return data
        return self._default_court_analytics(court_name)
    def get_judge_profile(self, judge_name: str) -> Optional[Dict]:
        judges = JUDICIAL_DATABASE["judges"]
        if judge_name in judges:
            return judges[judge_name]
        for name, data in judges.items():
            if judge_name and (judge_name.lower() in name.lower()):
                return data
        return None
    def calculate_judicial_multiplier(self, theoretical_score: float, case_data: Dict) -> Dict:
        court_name = case_data.get("court_name", "")
        judge_name = case_data.get("judge_name", "")
        judicial_temperament = case_data.get("judicial_temperament", "Balanced")
        court = self.get_court_analytics(court_name)
        judge = self.get_judge_profile(judge_name)
        multiplier = 1.0
        adjustments = []
        if court:
            settle_rate = court.get("settlement_rate_pct", 38)
            if settle_rate > 40:
                multiplier *= 0.97
                adjustments.append(f"Court has high settlement rate ({settle_rate}%) — slightly reduces conviction probability")
            elif settle_rate < 30:
                multiplier *= 1.03
                adjustments.append(f"Court has low settlement rate ({settle_rate}%) — increases conviction probability")
        if judge:
            strictness = judge.get("strictness_score", 5.5)
            if strictness > 7.5:
                multiplier *= 0.94
                adjustments.append(f"Judge {judge_name} has high strictness score ({strictness}/10) — expect aggressive scrutiny")
            elif strictness < 5.0:
                multiplier *= 1.04
                adjustments.append(f"Judge {judge_name} is relatively lenient (strictness {strictness}/10)")
        if judicial_temperament == "Pro-Complainant":
            multiplier *= 1.06
            adjustments.append("Court mood: Pro-Complainant — complainant arguments get more favourable reception")
        elif judicial_temperament == "Skeptical":
            multiplier *= 0.92
            adjustments.append("Court mood: Skeptical — expect rigorous examination of all claims")
        adjusted_score = round(min(99, max(5, theoretical_score * multiplier)), 1)
        return {
            "theoretical_score": theoretical_score,
            "judicial_multiplier": round(multiplier, 3),
            "adjusted_score": adjusted_score,
            "score_delta": round(adjusted_score - theoretical_score, 1),
            "adjustments": adjustments,
            "court_analytics": court,
            "judge_profile": judge
        }
    def generate_judge_challenge_predictions(self, case_data: Dict, score: float) -> List[str]:
        questions = []
        court_name = case_data.get("court_name", "")
        judge_name = case_data.get("judge_name", "")
        judge = self.get_judge_profile(judge_name)
        court = self.get_court_analytics(court_name)
        if judge:
            questions.extend(judge.get("common_questions", []))
        if court:
            for objection in court.get("common_objections", [])[:2]:
                questions.append(f"Court frequently flags: {objection}. Be prepared to address this.")
        if not case_data.get("notice_sent") or case_data.get("notice_received") == "Returned Unserved":
            questions.append("How was the legal notice served? Do you have proof of delivery?")
        if case_data.get("accused_type") in ["Pvt Ltd/Ltd Company", "Partnership Firm"] and not case_data.get("directors_named"):
            questions.append("Have all responsible directors been made accused? S.141 requires the company and its officers to be jointly prosecuted.")
        if not case_data.get("agreement_documents") or case_data.get("agreement_type") == "No Formal Agreement":
            questions.append("What is the documentary proof of the underlying debt or transaction?")
        if score < 55:
            questions.append("Given the weakness of the evidence, why should this court take cognizance?")
        return questions[:6]                
    def generate_judicial_intelligence_report(self, case_data: Dict, theoretical_score: float) -> Dict:
        court_name = case_data.get("court_name", "Not specified")
        court = self.get_court_analytics(court_name)
        multiplier_result = self.calculate_judicial_multiplier(theoretical_score, case_data)
        challenge_predictions = self.generate_judge_challenge_predictions(case_data, theoretical_score)
        report = {
            "court_name": court_name,
            "judicial_multiplier": multiplier_result,
            "judge_challenge_predictions": challenge_predictions,
            "court_stats": {
                "avg_disposal_months": round(court.get("avg_disposal_days", 540) / 30, 1) if court else None,
                "settlement_rate": f"{court.get('settlement_rate_pct', 'N/A')}%" if court else "N/A",
                "conviction_rate": f"{court.get('conviction_rate_pct', 'N/A')}%" if court else "N/A",
                "avg_bail_grant_days": court.get("avg_bail_grant_days", "N/A") if court else "N/A",
                "common_court_objections": court.get("common_objections", []) if court else []
            },
            "adjusted_survivability_score": multiplier_result.get("adjusted_score", theoretical_score),
            "recommendation": self._generate_recommendation(multiplier_result, court)
        }
        logger.info(f"[JudicialEngine] Report generated for court: {court_name}")
        return report
    def _generate_recommendation(self, multiplier: Dict, court: Optional[Dict]) -> str:
        delta = multiplier.get("score_delta", 0)
        adj = multiplier.get("adjusted_score", 50)
        if delta < -5:
            return f"CAUTION: This court/judge is empirically more difficult than average. Your theoretical score of {multiplier.get('theoretical_score')} is adjusted DOWN to {adj}. Strengthen evidence before filing."
        elif delta > 5:
            return f"ADVANTAGE: This court/judge is empirically more favourable. Your score is adjusted UP to {adj}. Consider aggressive prosecution posture."
        else:
            return f"NEUTRAL: This court behaves close to the theoretical model. Adjusted score: {adj}."
    def _default_court_analytics(self, court_name: str) -> Dict:
        return {
            "court_id": "UNKNOWN",
            "avg_disposal_days": 540,
            "settlement_rate_pct": 35,
            "conviction_rate_pct": 60,
            "common_objections": ["Evidence Gaps", "Procedural Compliance", "Notice Issues"],
            "avg_bail_grant_days": 21,
            "region": court_name or "Not specified",
            "note": "Analytics estimated — court not in database. Add to judicial_database for exact data."
        }
judicial_engine = JudicialIntelligenceEngine()
