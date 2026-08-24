from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from criminal.criminal_adversarial_engine import CriminalAdversarialEngine
from criminal.criminal_scoring_engine import CriminalScoringEngine
from criminal.criminal_timeline_engine import CriminalTimelineEngine
from criminal.criminal_economics_engine import CriminalEconomicsEngine
from criminal.criminal_rules_engine import CriminalRulesEngine

def _is_true(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    if isinstance(val, str):
        val_lower = val.strip().lower()
        return val_lower in ("true", "yes", "1") or val_lower.startswith("yes") or "violation" in val_lower or "unlawful" in val_lower or "missing" in val_lower or "without" in val_lower
    return False

class CriminalEngine(BaseDomainEngine):
    """
    Primary orchestrator for Criminal Law Analytics under both legacy (IPC/CrPC/IEA)
    and modern Bharatiya Nyaya Sanhita (BNS/BNSS/BSA) statutory frameworks.
    Extends BaseDomainEngine for CaseRegistry integration.
    """

    @property
    def domain_name(self) -> str:
        return "criminal"

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns stateful graph of criminal litigation procedural milestones tailored to offense category."""
        offense_type = str(case_data.get("offense_type", "")).upper()
        severity_score = case_data.get("severity_score", 50)
        
        if "NDPS" in offense_type:
            nodes = [
                {"id": "search", "name": "Search & Seizure (S.50 NDPS Personal Search Protocol)", "probability": "90%", "status": "Critical Gate"},
                {"id": "sampling", "name": "Magistrate Sampling (S.52A NDPS Protocol)", "probability": "85%", "status": "Mandatory Safeguard"},
                {"id": "bail_s37", "name": "Special Act Bail Hearing (S.37 Twin Conditions)", "probability": "40%", "status": "Stringent Scrutiny"},
                {"id": "charge", "name": "Discharge / Framing of Charges (Special Court)", "probability": "65%", "status": "Stable"},
                {"id": "trial", "name": "Trial & Chemical Examiner FSL Cross-Examination", "probability": "55%", "status": "Trial Ready"}
            ]
        elif any(x in offense_type for x in ["PMLA", "MONEY LAUNDERING", "ED"]):
            nodes = [
                {"id": "ecir", "name": "ECIR & Summons (S.50 PMLA Statement)", "probability": "85%", "status": "Pre-Trial"},
                {"id": "predicate", "name": "Scheduled Predicate Offense Audit", "probability": "75%", "status": "Core Vulnerability"},
                {"id": "twin_bail", "name": "Regular Bail Hearing (S.45 PMLA vs Art. 21 Delay)", "probability": "60%", "status": "Constitutional Window"},
                {"id": "discharge", "name": "Discharge Application (Want of Proceeds of Crime)", "probability": "50%", "status": "Discharge Stage"},
                {"id": "special_trial", "name": "Special PMLA Court Trial", "probability": "45%", "status": "Complex Financial Trial"}
            ]
        elif any(x in offense_type for x in ["302", "304", "307", "103", "105", "109", "MURDER", "HOMICIDE"]):
            nodes = [
                {"id": "fir_inquest", "name": "FIR & Inquest Report (S.174 CrPC / S.194 BNSS)", "probability": "85%", "status": "Initiation"},
                {"id": "remand_recovery", "name": "Police Custody & S.27 Recovery Memo", "probability": "70%", "status": "Evidentiary"},
                {"id": "committal", "name": "Supply of Copies & Committal to Sessions (S.207/209 CrPC)", "probability": "90%", "status": "Jurisdictional Transfer"},
                {"id": "charge_sessions", "name": "Discharge Argument (S.227 CrPC / S.250 BNSS)", "probability": "40%", "status": "Charge Framing"},
                {"id": "ocular_medical", "name": "Cross-Exam: Eyewitnesses vs Post-Mortem Doctor", "probability": "60%", "status": "Crucial Trial Stage"},
                {"id": "s313_defense", "name": "Statement of Accused (S.313 CrPC) & Defense Evidence", "probability": "75%", "status": "Final Defense"}
            ]
        elif any(x in offense_type for x in ["498A", "420", "406", "85", "318", "316", "CHEATING", "MATRIMONIAL"]):
            nodes = [
                {"id": "notice_41a", "name": "S.41A CrPC / S.35 BNSS Notice & Mediation", "probability": "90%", "status": "Threshold Stage"},
                {"id": "quashing_482", "name": "High Court Quashing (S.482 CrPC / S.528 BNSS - Bhajan Lal)", "probability": "80%", "status": "Prime Remedy"},
                {"id": "bail_antil", "name": "Appearance / Bail under Antil Category A Mandate", "probability": "95%", "status": "Mandatory Relief"},
                {"id": "discharge_mag", "name": "Discharge Application (S.239 CrPC / S.262 BNSS)", "probability": "70%", "status": "Pre-Trial Scrutiny"},
                {"id": "magistrate_trial", "name": "Magistrate Trial / Complainant Cross-Examination", "probability": "60%", "status": "Defense Stance"}
            ]
        else:
            nodes = CriminalAdversarialEngine.calculate_stage_survivability(severity_score, 0.5)

        return {
            "current_stage": case_data.get("procedural_stage", "Investigation / Pre-Trial"),
            "nodes": nodes,
            "total_nodes": len(nodes),
            "completed_nodes": 0
        }

    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Returns prioritized next best actions for criminal litigation."""
        rules = CriminalRulesEngine.evaluate_rules(case_data)
        actions = []
        for r in rules:
            actions.append({
                "priority": 1 if "ABSOLUTE" in r.get("severity", "") or "FATAL" in r.get("status", "") else 2,
                "action": r.get("action", ""),
                "reason": r.get("legal_effect", ""),
                "authority": r.get("rule_name", "")
            })
        if not actions:
            role = case_data.get("client_role", "Accused")
            if role == "Accused":
                actions.append({
                    "priority": 1,
                    "action": "File Section 438 CrPC / Section 484 BNSS Anticipatory Bail Application",
                    "reason": "Protect against custodial detention during ongoing investigation.",
                    "authority": "Section 438 CrPC / Section 484 BNSS"
                })
            else:
                actions.append({
                    "priority": 1,
                    "action": "Ensure Custodial Interrogation and Recovery u/s 27 IEA / S.23 BSA",
                    "reason": "Expedite investigation and recovery of material evidence.",
                    "authority": "Section 27 Evidence Act / Section 23 BSA"
                })
        return actions

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if concepts is None:
            concepts = case_data.get("concepts", [])
        contradictions = CriminalAdversarialEngine.detect_contradictions(case_data, concepts)
        scoring_data = CriminalScoringEngine.calculate_score(case_data, concepts, contradictions)
        strategy = cls.generate_strategy(case_data, concepts, scoring_data["score"], 0.5)

        return {
            **scoring_data,
            "domain": "criminal",
            "strategy": strategy,
            "bail_assessment": strategy.get("bail_assessment"),
            "statutory_rules": strategy.get("statutory_rules"),
            "litigation_map": strategy.get("litigation_map"),
            "timeline_analysis": strategy.get("timeline_analysis"),
            "checkpoints": strategy.get("checkpoints"),
            "contradictions": contradictions
        }

    @staticmethod
    def generate_strategy(case_data: Dict[str, Any], concepts: List[Dict[str, Any]], severity_score: int, adversarial_risk: float = 0.5) -> Dict[str, Any]:
        contradictions = CriminalAdversarialEngine.detect_contradictions(case_data, concepts)
        scoring_data = CriminalScoringEngine.calculate_score(case_data, concepts, contradictions)
        litigation_map = CriminalEngine.generate_litigation_map(case_data, severity_score, concepts)
        bail_assessment = CriminalEngine.assess_bail_probability(case_data, concepts)
        checkpoints = CriminalEngine.get_advocate_checkpoints(severity_score, case_data)
        rules = CriminalRulesEngine.evaluate_rules(case_data)
        economics = CriminalEconomicsEngine.calculate_economics(case_data)
        timeline_analysis = CriminalTimelineEngine.analyze_timelines(case_data)

        strategy_text_parts = [
            f"PRIMARY OBJECTIVE ({litigation_map['client_role']}): {litigation_map['posture']['primary_objective']}",
            "TACTICAL MOVES:\n" + "\n".join(f"- {m}" for m in litigation_map['posture']['tactical_moves']),
            f"BAIL CATEGORY ({bail_assessment['antil_category']}): {bail_assessment['probability']} probability. Rationale: {bail_assessment['strategic_rationale']}"
        ]
        if checkpoints:
            strategy_text_parts.append("ADVOCATE CHECKPOINTS:\n" + "\n".join(f"- {c}" for c in checkpoints))
        if rules:
            strategy_text_parts.append("STATUTORY RULES TRIGGERED:\n" + "\n".join(f"- {r['rule_name']} ({r['severity']}): {r['legal_effect']}" for r in rules))

        litigation_strategy_str = "\n\n".join(strategy_text_parts)

        return {
            "score": scoring_data["score"],
            "verdict": scoring_data["verdict"],
            "score_breakdown": scoring_data["score_breakdown"],
            "causality_map": scoring_data["causality_map"],
            "statutory_rules": rules,
            "litigation_map": litigation_map,
            "litigation_strategy": litigation_strategy_str,
            "roadmap": CriminalEngine().build_procedural_graph(case_data).get("nodes", []),
            "bail_assessment": bail_assessment,
            "economics": economics,
            "timeline_analysis": timeline_analysis,
            "checkpoints": checkpoints
        }

    @staticmethod
    def assess_bail_probability(case_data: Dict[str, Any], concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates Bail Probability structured according to the 4 Categories laid down by
        the Supreme Court of India in Satender Kumar Antil v. CBI (2022) 10 SCC 51.
        """
        offense_type = str(case_data.get("offense_type", "General")).upper()
        punishment_years = int(case_data.get("max_punishment_years") or case_data.get("punishment_years") or 7)
        days_in_custody = int(case_data.get("days_in_custody") or 0)
        chargesheet_filed = _is_true(case_data.get("chargesheet_filed"))

        flight_risk = _is_true(case_data.get("flight_risk"))
        evidence_tampering = _is_true(case_data.get("evidence_tampering_risk"))
        in_custody = days_in_custody > 0 or _is_true(case_data.get("in_custody")) or _is_true(case_data.get("arrested_during_investigation"))

        # Satender Kumar Antil 4-Category Taxonomy
        if any(x in offense_type for x in ["NDPS", "PMLA", "POCSO", "UAPA", "COMPANIES ACT"]):
            category = "Category C (Special Acts with Stringent Bail Provisions)"
            if days_in_custody >= 180 and not chargesheet_filed:
                probability = "HIGH"
                rationale = "Special Act Twin Conditions overridden by Article 21 right to speedy trial due to prolonged undertrial incarceration (Manish Sisodia v. ED, 2024; Union of India v. K.A. Najeeb)."
            elif case_data.get("s50_violation") or case_data.get("s52a_violation"):
                probability = "HIGH"
                rationale = "Fatal procedural violation of statutory search/sampling protocol rebuts prima facie presumption (Vijaysinh Jadeja; Mangilal)."
            else:
                probability = "LOW"
                rationale = "Stringent twin conditions (e.g. S.37 NDPS / S.45 PMLA) require court to be satisfied of absence of guilt."
        elif any(x in offense_type for x in ["302", "304", "376", "395", "103", "64", "310", "MURDER", "RAPE", "TERRORISM"]) or punishment_years > 7:
            category = "Category B (Heinous Offenses: Death / Life / >7 Years Imprisonment)"
            if days_in_custody > 90 and not chargesheet_filed:
                probability = "VERY HIGH"
                rationale = "Indefeasible Right to Default Bail under Section 167(2) CrPC / Section 187 BNSS (90 Days Exceeded Without Chargesheet)."
            elif flight_risk or evidence_tampering:
                probability = "VERY LOW"
                rationale = "Severity of punishment and apprehension of flight/tampering weigh against discretionary bail under S.437/439 CrPC."
            else:
                probability = "MEDIUM"
                rationale = "Merits-based evaluation of circumstantial chain, weapon recovery, and ocular consistency."
        elif any(x in offense_type for x in ["409", "FORGERY", "467", "468", "BANK FRAUD"]):
            category = "Category D (Economic Offenses Not Covered by Special Acts)"
            if not in_custody and not flight_risk:
                probability = "HIGH"
                rationale = "Entire evidence is documentary and in custody of investigating agency; custodial interrogation not warranted per P. Chidambaram v. CBI."
            else:
                probability = "MEDIUM"
                rationale = "Magnitude of financial loss and trail of funds subject to judicial discretion."
        else:
            category = "Category A (Offenses Punishable with <= 7 Years Imprisonment)"
            if not in_custody or not _is_true(case_data.get("arrested_during_investigation")):
                probability = "VERY HIGH"
                rationale = "Covered under Satender Kumar Antil (Category A) & Arnesh Kumar mandate: Bail is mandatory without custodial remand if accused cooperates."
            elif days_in_custody >= 60 and not chargesheet_filed:
                probability = "VERY HIGH"
                rationale = "Indefeasible right to Statutory Default Bail under Section 167(2) CrPC / S.187 BNSS (60 Days Exceeded)."
            else:
                probability = "HIGH"
                rationale = "Bail is the rule, jail is the exception (State of Rajasthan v. Balchand). Triple test satisfied."

        return {
            "probability": probability,
            "antil_category": category,
            "anticipatory_bail_viable": probability in ["HIGH", "VERY HIGH", "MEDIUM"],
            "regular_bail_viable": True,
            "default_bail_triggered": (days_in_custody >= 60 and punishment_years <= 7 and not chargesheet_filed) or (days_in_custody >= 90 and not chargesheet_filed),
            "factors": {
                "flight_risk": flight_risk,
                "evidence_tampering": evidence_tampering,
                "days_in_custody": days_in_custody,
                "punishment_years": punishment_years
            },
            "strategic_rationale": rationale
        }

    @staticmethod
    def generate_litigation_map(case_data: Dict[str, Any], severity_score: int, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        role = case_data.get("client_role", "Accused")
        offense_type = str(case_data.get("offense_type", "")).upper()
        is_civil_dispute = any(x in offense_type for x in ["420", "406", "318", "316", "CHEATING", "FRAUD"]) and _is_true(case_data.get("contract_exists"))
        is_matrimonial = any(x in offense_type for x in ["498A", "85", "DOWRY", "304B"])

        if role == "Accused":
            primary_objective = "Secure Acquittal, Discharge, or S.482 CrPC / S.528 BNSS Quashing"
            tactical_moves = ["File Section 438 CrPC / Section 484 BNSS Anticipatory Bail Application"]
            if is_civil_dispute or is_matrimonial:
                tactical_moves.append("File Section 482 CrPC / Section 528 BNSS Quashing Petition (citing Bhajan Lal parameters for civil dispute / omnibus allegations).")
            else:
                tactical_moves.append("Argue Discharge under Section 227/239 CrPC / Section 250/262 BNSS based on absence of prima facie case.")

            if _is_true(case_data.get("witness_statements_inconsistent")):
                tactical_moves.append("Invoke Section 311 CrPC / Section 348 BNSS to recall witnesses for establishing material contradictions.")
        else:
            primary_objective = "Ensure Custodial Interrogation, Chargesheet, and Conviction"
            tactical_moves = ["Ensure Custodial Interrogation and Recovery u/s 27 IEA / S.23 BSA", "Expedite FSL / Forensic Reports"]
            if _is_true(case_data.get("unnamed_accomplice")):
                tactical_moves.append("File Section 319 CrPC / Section 357 BNSS application to summon additional co-accused not named in chargesheet.")

        return {
            "client_role": role,
            "posture": {"primary_objective": primary_objective, "tactical_moves": tactical_moves},
            "overall_assessment": "High Risk" if severity_score > 70 else "Manageable"
        }

    @staticmethod
    def get_advocate_checkpoints(severity_score: int, case_data: Dict[str, Any]) -> List[str]:
        checkpoints = [
            "MANDATORY: Scrutinize FIR for S.154 CrPC / S.173 BNSS delay. Unexplained delay is fatal to prosecution.",
            "STRATEGIC: Evaluate necessity of S.311 CrPC / S.348 BNSS application for recalling key witnesses."
        ]
        if _is_true(case_data.get("electronic_evidence")):
            checkpoints.append("CRITICAL: Verify mandatory Section 65B IEA / Section 63 BSA certificate filing alongside electronic exhibits.")
        if _is_true(case_data.get("is_public_servant")):
            checkpoints.append("JURISDICTIONAL: Verify compliance with Section 197 CrPC / Section 218 BNSS sanction requirement.")
        return checkpoints
