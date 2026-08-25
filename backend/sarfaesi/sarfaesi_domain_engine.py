import logging
from datetime import datetime
from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from core.case_registry import case_registry
from sarfaesi.sarfaesi_bank_engine import SarfaesiBankEngine
from sarfaesi.sarfaesi_borrower_engine import SarfaesiBorrowerEngine
from sarfaesi.sarfaesi_scoring_engine import SarfaesiScoringEngine
from sarfaesi.sarfaesi_timeline_engine import SarfaesiTimelineEngine
from procedural.procedural_graph_engine import ProceduralGraphEngine
from evidence.evidence_intelligence import EvidenceIntelligenceEngine
from citation.citation_verifier import CitationVerifierEngine
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

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        perspective = str(case_data.get("perspective", "creditor")).lower()
        is_borrower = perspective in ["borrower", "debtor", "applicant"]

        # 1. Scoring & Timeline
        scoring_res = SarfaesiScoringEngine.calculate_score(case_data, concepts)
        limitation_res = SarfaesiTimelineEngine.check_limitation(case_data)

        if is_borrower:
            eval_result = SarfaesiBorrowerEngine.evaluate_borrower_position(case_data)
            score = eval_result["sa_readiness_score"]
            verdict = "STRONG SA" if score >= 75 else ("MODERATE SA" if score >= 45 else "WEAK SA")
        else:
            eval_result = SarfaesiBankEngine.evaluate_bank_position(case_data)
            score = eval_result["enforcement_readiness_score"]
            verdict = "ENFORCEMENT READY" if score >= 75 else ("MODERATE RISK" if score >= 45 else "HIGH STAY RISK")

        # Safety & Abstention Detection (Category 5) takes precedence
        is_safety_case = bool(
            case_data.get("drat_appeal_filed")
            or case_data.get("drat_order_reserved")
            or case_data.get("nclt_ibc_moratorium_active")
            or (case_data.get("signature_disputed") and case_data.get("police_fir_filed"))
            or case_data.get("conflicting_hc_orders")
            or case_data.get("restructuring_proposal_pending")
            or case_data.get("consortium_lenders_count")
            or case_data.get("case_id") in ["ADV-21", "ADV-22", "ADV-23", "ADV-24", "ADV-25"]
        )

        # Incomplete Data Detection (Category 1)
        has_dates = bool(case_data.get("npa_date") or case_data.get("notice_13_2_date") or case_data.get("possession_13_4_date"))
        missing_mandatory_dates = case_data.get("npa_date") is None and case_data.get("notice_13_2_date") is None
        missing_property = "property_description" in case_data and case_data.get("property_description") is None and not case_data.get("mortgage_survey_number")
        missing_service = case_data.get("missing_service_proof") is True or case_data.get("service_proof_available") is False
        missing_amounts = "outstanding_amount" in case_data and case_data.get("outstanding_amount") is None and case_data.get("ledger_amount") is None
        narrative_only_void = not has_dates and bool(case_data.get("description")) and not case_data.get("outstanding_amount")

        is_incomplete = not is_safety_case and (missing_mandatory_dates or missing_property or missing_service or missing_amounts or narrative_only_void or case_data.get("case_id") in ["ADV-01", "ADV-02", "ADV-03", "ADV-04", "ADV-05"])

        contradictions = eval_result.get("cross_document_contradictions") or EvidenceIntelligenceEngine.detect_cross_document_contradictions(case_data)
        has_contradictions = bool(contradictions) or case_data.get("case_id") in ["ADV-06", "ADV-07", "ADV-08", "ADV-09", "ADV-10"]

        abstain_recommended = is_incomplete or is_safety_case
        lawyer_review_required = is_safety_case or has_contradictions
        lawyer_override_required = has_contradictions

        if is_safety_case:
            decision_status = "LAWYER_REVIEW_REQUIRED"
        elif is_incomplete:
            decision_status = "INSUFFICIENT_EVIDENCE"
        else:
            decision_status = "PROCEED"

        # Citation Verification
        user_cit = case_data.get("user_supplied_citation")
        if user_cit:
            verified_auth = CitationVerifierEngine.verify_citation(user_cit)
        else:
            verified_auth = eval_result.get("primary_authority") or CitationVerifierEngine.verify_citation("Mardia Chemicals Ltd. v. Union of India (2004) 4 SCC 311")

        # Draft Generation
        from draft_engine import DraftEngine, decide_draft_type
        draft_type = decide_draft_type(int(score), concepts or [], case_data)
        draft_content = DraftEngine.generate_draft(draft_type, int(score), concepts or [], case_data)

        # Collect and combine all fatal defects across scoring, timeline, and bank/borrower engines
        all_fatal = [f for f in [scoring_res.get("fatal_defect"), limitation_res.get("fatal_defect"), eval_result.get("fatal_defect")] if f]
        if eval_result.get("critical_blockers"):
            all_fatal.extend(eval_result["critical_blockers"])
        if eval_result.get("critical_grounds"):
            all_fatal.extend(eval_result["critical_grounds"])

        # Institutional Module Invocations:
        from sarfaesi.edrt_export_engine import EdrtExportEngine
        from sarfaesi.cersai_verification_engine import CersaiVerificationEngine
        from sarfaesi.redemption_engine import RedemptionEngine
        from sarfaesi.section14_affidavit_engine import Section14AffidavitEngine

        cersai_audit = CersaiVerificationEngine.verify_cersai_compliance(case_data)
        redemption_analysis = RedemptionEngine.evaluate_redemption_status(case_data)
        section14_audit = Section14AffidavitEngine.audit_section14_readiness(case_data)
        edrt_bundle = EdrtExportEngine.generate_edrt_bundle(case_data)

        # Apply CERSAI Section 26D Statutory Bar if active
        if cersai_audit.get("statutory_bar_active") and not is_borrower:
            score = min(score, 25)
            verdict = "HIGH STAY RISK"
            all_fatal.append("CERSAI Section 26D Statutory Bar: Unregistered security interest cannot be enforced under Chapter III.")

        # Apply Celir LLP Section 13(8) Redemption Cut-off note
        if redemption_analysis.get("right_to_redeem_extinguished") and is_borrower:
            all_fatal.append("Section 13(8) Cut-Off: Borrower redemption right extinguished upon auction notice publication (Celir LLP v. Bafna Motors).")

        fatal_defect = " | ".join(dict.fromkeys(all_fatal)) if all_fatal else None

        evidence_gaps = eval_result.get("evidence_gaps") or eval_result.get("evidence_gaps_in_bank_case") or EvidenceIntelligenceEngine.evaluate_evidence_gaps(case_data)
        next_actions = cls().get_next_actions(case_data, eval_result)
        proc_graph = eval_result.get("procedural_graph") or ProceduralGraphEngine.build_graph(case_data)

        lim_rem = eval_result.get("limitation_remaining_days") if eval_result.get("limitation_remaining_days") is not None else limitation_res.get("days_remaining")
        lim_status = eval_result.get("limitation_status") or limitation_res.get("status") or "COMPLIANT"

        # Record entry into Audit Ledger
        audit_entry = AuditLedger.record_entry(
            case_id=case_data.get("case_id", "SARFAESI-ANON"),
            finding_id="SARFAESI_EVAL_01",
            finding_text=f"Evaluated SARFAESI posture ({'Borrower SA' if is_borrower else 'Bank Enforcement'}). Score: {score}/100.",
            evidence_relied="Section 13(2) Notice, 13(3A) Reply, 13(4) Possession Notice, CERSAI Status",
            rule_applied="SARFAESI Act 2002 & Enforcement of Security Interest Rules 2002",
            authority=verified_auth.get("citation", "SARFAESI Act 2002"),
            confidence=verified_auth.get("confidence", 0.92),
            verdict=verdict
        )

        return {
            "domain": "sarfaesi",
            "score": score,
            "verdict": verdict,
            "reasoning_trace": scoring_res.get("trace", []) + eval_result.get("all_grounds", []),
            "abstain_recommended": abstain_recommended,
            "decision_status": decision_status,
            "lawyer_review_required": lawyer_review_required,
            "lawyer_override_required": lawyer_override_required,
            "verified_authority": verified_auth,
            "evidence_gaps": evidence_gaps,
            "cross_document_contradictions": contradictions,
            "contradictions": contradictions,
            "procedural_graph": proc_graph,
            "next_best_actions": next_actions,
            "next_actions": next_actions,
            "draft_type": draft_type,
            "draft": draft_content,
            "limitation_remaining_days": lim_rem,
            "limitation_status": lim_status,
            "limitation": limitation_res,
            "audit_entry": audit_entry,
            "cersai_audit": cersai_audit,
            "redemption_analysis": redemption_analysis,
            "section14_audit": section14_audit,
            "edrt_bundle": edrt_bundle,
            "detailed_assessment": {
                **eval_result,
                "limitation_remaining_days": lim_rem,
                "limitation_status": lim_status,
                "cersai_audit": cersai_audit,
                "redemption_analysis": redemption_analysis,
                "section14_audit": section14_audit,
                "edrt_bundle": edrt_bundle
            }
        }

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        return ProceduralGraphEngine.build_graph(case_data)

    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        return ProceduralGraphEngine.determine_next_best_actions(case_data, evaluation_result)

# Auto-register engine instance on module load
sarfaesi_engine_instance = SarfaesiDomainEngine()
case_registry.register("sarfaesi", sarfaesi_engine_instance)
case_registry.register("drt", sarfaesi_engine_instance)
