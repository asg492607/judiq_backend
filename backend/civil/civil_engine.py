"""
JudiQ AI — Master Civil & Commercial Litigation Domain Engine
Orchestrates institutional-grade evaluation of Civil, Commercial, Order 37,
Specific Performance, and Property disputes under CPC, CCA, SRA, and Limitation Act.
"""

from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from adversarial_engine import AdversarialEngine
from civil.civil_scoring_engine import CivilScoringEngine
from civil.civil_suit_classifier import CivilSuitClassifier
from civil.civil_defence_catalogue import CivilDefenceCatalogue
from civil.injunction_evaluator import InjunctionEvaluator
from civil.specific_performance_engine import SpecificPerformanceEngine
from civil.order37_summary_suit_engine import Order37SummarySuitEngine
from civil.cpc_statutory_rules import CPCStatutoryRules

class CivilEngine(BaseDomainEngine):
    """
    Law-Firm Grade Domain Engine for Civil and Commercial Litigation in India.
    """

    @property
    def domain_name(self) -> str:
        return "civil"

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns dynamic stateful graph of civil suit litigation milestones."""
        return CivilSuitClassifier.build_procedural_graph(case_data)

    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Returns prioritized next best actions for Civil & Commercial litigation."""
        actions = []
        posture = str(case_data.get("party_posture") or case_data.get("perspective") or "plaintiff").lower()
        is_defendant = any(k in posture for k in ["defendant", "respondent"])
        suit_type_key = CivilSuitClassifier.classify(case_data)

        if not is_defendant:
            # Plaintiff Perspective Next Actions
            if case_data.get("urgent_interim_relief_prayed") or case_data.get("order_39_injunction") or case_data.get("urgency_injunction"):
                actions.append({
                    "priority": 1,
                    "action": "File Application for Temporary Injunction under Order XXXIX Rules 1 & 2 CPC",
                    "reason": "Establish 3-prong Golden Triad (Prima Facie Case, Balance of Convenience, Irreparable Injury) to secure immediate status quo.",
                    "authority": "Order XXXIX Rules 1 & 2 CPC (Dalpat Kumar v. Prahlad Singh)"
                })
            elif suit_type_key == "commercial_suit" and not case_data.get("s12a_mediation"):
                actions.append({
                    "priority": 1,
                    "action": "Initiate Section 12A Pre-Institution Mediation (PIMS) before DLSA/SLSA",
                    "reason": "Mandatory condition precedent for commercial suits under Section 12A Commercial Courts Act (Patil Automation).",
                    "authority": "Section 12A Commercial Courts Act, 2015"
                })

            if not case_data.get("plaint_filed"):
                actions.append({
                    "priority": 2,
                    "action": "Draft and Present Plaint with Statement of Truth (Order VI Rule 15A)",
                    "reason": "File before competent commercial/civil court with ad-valorem court fees under Court Fees Act, 1870.",
                    "authority": "Order VII Rule 1 & Order VI Rule 15A CPC"
                })

            if suit_type_key == "specific_performance":
                actions.append({
                    "priority": 2,
                    "action": "Place Certified Proof of Financial Capacity & Tender Notice on Record",
                    "reason": "Satisfy Section 16(c) continuous readiness and willingness mandate (U.N. Krishnamurthy).",
                    "authority": "Section 16(c) Specific Relief Act, 1963"
                })
        else:
            # Defendant Perspective Next Actions
            if evaluation_result and evaluation_result.get("fatal_defect"):
                actions.append({
                    "priority": 1,
                    "action": "File Application for Rejection of Plaint under Order VII Rule 11 CPC",
                    "reason": f"Plaint is barred at threshold: {evaluation_result['fatal_defect']}",
                    "authority": "Order VII Rule 11 CPC (Dahiben v. Arvindbhai Bhanusali)"
                })

            if case_data.get("arbitration_clause_exists"):
                actions.append({
                    "priority": 1,
                    "action": "File Application for Reference to Arbitration under Section 8 Arbitration Act",
                    "reason": "Mandatory application before filing first statement on the substance of the dispute (Booz Allen).",
                    "authority": "Section 8 Arbitration & Conciliation Act, 1996"
                })

            if not case_data.get("written_statement_filed"):
                actions.append({
                    "priority": 1,
                    "action": "Draft and File Written Statement within 30-Day Window (Max 120 Days for Commercial)",
                    "reason": "Strict forfeiture of right to file Written Statement post 120 days in Commercial Division (SCG Contracts).",
                    "authority": "Order VIII Rule 1 CPC Proviso (SCG Contracts)"
                })

        return actions

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        case_data["case_type"] = "civil"
        if concepts is None:
            concepts = case_data.get("concepts", [])
        contradictions = AdversarialEngine.detect_contradictions(case_data, concepts)
        scoring = CivilScoringEngine.calculate_score(case_data, concepts, contradictions)
        
        instance = cls()
        procedural_graph = instance.build_procedural_graph(case_data)
        next_actions = instance.get_next_actions(case_data, scoring)

        return {
            **scoring,
            "domain": "civil",
            "procedural_graph": procedural_graph,
            "next_actions": next_actions,
            "contradictions": contradictions
        }
