import logging
from typing import Dict, List, Any
from sarfaesi.sarfaesi_model import SarfaesiCaseModel
from evidence.evidence_intelligence import EvidenceIntelligenceEngine
from procedural.procedural_graph_engine import ProceduralGraphEngine
from citation.citation_verifier import CitationVerifierEngine

logger = logging.getLogger(__name__)

class SarfaesiBankEngine:
    """
    Bank Enforcement Intelligence Engine:
    Answers:
    1. Is enforcement currently actionable?
    2. What documents/evidence are missing?
    3. What procedural defect could create a stay?
    4. What must happen before possession/auction?
    5. What is the next deadline & permissible legal action?
    6. What borrower argument is most dangerous?
    """

    @classmethod
    def evaluate_bank_position(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        # Build procedural graph
        proc_graph = ProceduralGraphEngine.build_graph(case_data)
        # Audit evidence gaps
        evidence_gaps = EvidenceIntelligenceEngine.evaluate_evidence_gaps(case_data)
        contradictions = EvidenceIntelligenceEngine.detect_cross_document_contradictions(case_data)

        readiness_score = 85
        critical_blockers = []
        stay_risk = "LOW"

        # Check CERSAI
        cersai = case_data.get("cersai_registered") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        if not cersai:
            readiness_score -= 40
            critical_blockers.append("Security interest not registered on CERSAI portal (Section 26D).")
            stay_risk = "CRITICAL"

        # Check 13(3A) reply
        if case_data.get("borrower_representation_date") and not case_data.get("bank_reply_13_3a_date") and case_data.get("possession_13_4_date"):
            readiness_score -= 35
            critical_blockers.append("Unanswered Section 13(3A) representation prior to taking Section 13(4) possession.")
            stay_risk = "CRITICAL"

        # Check agricultural land
        if case_data.get("is_agricultural_land"):
            readiness_score -= 50
            critical_blockers.append("Mortgaged property is agricultural land, exempt from SARFAESI U/S 31(i).")
            stay_risk = "FATAL"

        readiness_score = max(10, min(95, readiness_score))

        # Authority chain for top risk
        top_authority = CitationVerifierEngine.verify_citation("Mardia Chemicals Ltd. v. Union of India (2004) 4 SCC 311")
        if not cersai:
            top_authority = CitationVerifierEngine.verify_citation("Section 26D SARFAESI Act, 2002")

        next_actions = ProceduralGraphEngine.determine_next_best_actions(case_data, {"score": readiness_score})

        return {
            "perspective": "Secured Creditor / Bank Mode",
            "enforcement_readiness_score": readiness_score,
            "current_procedural_stage": proc_graph["current_stage"],
            "stay_risk": stay_risk,
            "critical_blockers": critical_blockers,
            "evidence_gaps": evidence_gaps,
            "cross_document_contradictions": contradictions,
            "procedural_graph": proc_graph,
            "next_legally_permissible_action": next_actions[0]["action"] if next_actions else "Maintain procedural posture.",
            "next_actions_checklist": next_actions,
            "primary_authority": top_authority
        }
