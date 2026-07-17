from typing import Dict, List
class CriminalRulesEngine:
    @classmethod
    def evaluate_rules(cls, case_data: Dict) -> List[Dict]:
        triggered_rules = []
        age_at_incident = case_data.get("age_at_incident")
        if age_at_incident:
            try:
                age = int(age_at_incident)
                if age < 18:
                    triggered_rules.append({
                        "rule_name": "Juvenile Justice Act (Claim of Juvenility)",
                        "severity": "ABSOLUTE BAR",
                        "status": "FATAL TO TRIAL JURISDICTION",
                        "description": f"Accused was {age} years old at the time of the incident.",
                        "legal_effect": "The regular criminal court has ZERO jurisdiction. The trial must be immediately transferred to the Juvenile Justice Board (JJB). Maximum punishment cannot exceed 3 years in a special home.",
                        "action": "File an application under S.94 of the JJ Act for age determination (Ossification test/Matriculation certificate)."
                    })
            except ValueError:
                pass
        if case_data.get("is_public_servant") and not case_data.get("sanction_obtained"):
            triggered_rules.append({
                "rule_name": "S.197 CrPC / S.19 PC Act (Want of Sanction)",
                "severity": "ABSOLUTE BAR",
                "status": "COGNIZANCE VOID",
                "description": "Accused is a public servant acting in discharge of official duties, but no prior government sanction was obtained.",
                "legal_effect": "Taking cognizance of the offence is strictly barred by law. The entire proceeding is null and void ab initio.",
                "action": "File an application for discharge or S.482 Quashing citing lack of valid sanction."
            })
        max_punishment = case_data.get("max_punishment_years")
        arrested_during_investigation = case_data.get("arrested_during_investigation")
        cooperated_with_io = case_data.get("cooperated_with_io")
        if max_punishment is not None and arrested_during_investigation is not None:
            try:
                punishment = int(max_punishment)
                if punishment <= 7 and not arrested_during_investigation:
                    condition_met = "cooperated" if cooperated_with_io else "must demonstrate cooperation"
                    triggered_rules.append({
                        "rule_name": "Satender Kumar Antil Guidelines (Category A)",
                        "severity": "SUPREME COURT DIRECTIVE",
                        "status": "MANDATORY BAIL",
                        "description": f"Offence is punishable up to {punishment} years. Accused was not arrested during investigation and {condition_met}.",
                        "legal_effect": "Under Category A of the Antil Guidelines, the Magistrate must accept appearance without taking the accused into physical custody, and bail should be granted as a matter of right.",
                        "action": "Submit a bail application citing 'Satender Kumar Antil vs CBI' Category A guidelines on the first date of appearance."
                    })
            except ValueError:
                pass
        limitation_years = case_data.get("limitation_years_passed")
        if limitation_years is not None and max_punishment is not None:
            try:
                punishment = int(max_punishment)
                years_passed = float(limitation_years)
                barred = False
                bar_limit = 0
                if punishment <= 1 and years_passed > 1:
                    barred = True
                    bar_limit = 1
                elif punishment <= 3 and years_passed > 3:
                    barred = True
                    bar_limit = 3
                if barred:
                    triggered_rules.append({
                        "rule_name": "S.468 CrPC (Bar of Limitation)",
                        "severity": "ABSOLUTE BAR",
                        "status": "COGNIZANCE BARRED",
                        "description": f"Offence is punishable up to {punishment} years, meaning the limitation period is {bar_limit} year(s). However, {years_passed} years have passed.",
                        "legal_effect": "The Court is legally barred from taking cognizance of the offence post the limitation period.",
                        "action": "File for immediate discharge citing S.468 CrPC limitation."
                    })
            except ValueError:
                pass
        return triggered_rules
