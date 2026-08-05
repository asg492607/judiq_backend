import logging
from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from core.case_registry import case_registry
from sarfaesi.sarfaesi_bank_engine import SarfaesiBankEngine
from sarfaesi.sarfaesi_borrower_engine import SarfaesiBorrowerEngine
from procedural.procedural_graph_engine import ProceduralGraphEngine
from audit.audit_ledger import AuditLedger

logger = logging.getLogger(__name__)

class SarfaesiDomainEngine(BaseDomainEngine):
    """
    Unified SARFAESI & DRT Domain Engine implementation of BaseDomainEngine contract.
    Orchestrates deep Bank Enforcement vs Borrower Defense intelligence.
    """

    @property
    def domain_name(self) -> str:
        return "sarfaesi"

    def analyze(self, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        perspective = str(case_data.get("perspective", "creditor")).lower()
        is_borrower = perspective in ["borrower", "debtor", "applicant"]

        if is_borrower:
            eval_result = SarfaesiBorrowerEngine.evaluate_borrower_position(case_data)
            score = eval_result["sa_readiness_score"]
            verdict = "STRONG SA" if score >= 75 else ("MODERATE SA" if score >= 45 else "WEAK SA")
        else:
            eval_result = SarfaesiBankEngine.evaluate_bank_position(case_data)
            score = eval_result["enforcement_readiness_score"]
            verdict = "ENFORCEMENT READY" if score >= 75 else ("MODERATE RISK" if score >= 45 else "HIGH STAY RISK")

        # Record entry into Audit Ledger
        AuditLedger.record_entry(
            case_id=case_data.get("case_id", "SARFAESI-ANON"),
            finding_id="SARFAESI_EVAL_01",
            finding_text=f"Evaluated SARFAESI posture ({'Borrower SA' if is_borrower else 'Bank Enforcement'}). Score: {score}/100.",
            evidence_relied="Section 13(2) Notice, 13(3A) Reply, 13(4) Possession Notice, CERSAI Status",
            rule_applied="SARFAESI Act 2002 & Enforcement of Security Interest Rules 2002",
            authority=eval_result.get("primary_authority", {}).get("citation", "SARFAESI Act 2002"),
            confidence=0.92,
            verdict=verdict
        )

        return {
            "score": score,
            "final_score": float(score),
            "verdict": verdict,
            "domain": self.domain_name,
            "perspective": eval_result["perspective"],
            "fatal_defect": eval_result.get("fatal_defect"),
            "detailed_assessment": eval_result,
            "procedural_graph": eval_result.get("procedural_graph", {}),
            "next_actions": self.get_next_actions(case_data, eval_result)
        }

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        return ProceduralGraphEngine.build_graph(case_data)

    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        return ProceduralGraphEngine.determine_next_best_actions(case_data, evaluation_result)

# Auto-register engine instance on module load
sarfaesi_engine_instance = SarfaesiDomainEngine()
case_registry.register("sarfaesi", sarfaesi_engine_instance)
case_registry.register("drt", sarfaesi_engine_instance)
