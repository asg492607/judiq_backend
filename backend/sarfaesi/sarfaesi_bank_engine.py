import logging
from typing import Dict, List, Any
from evidence.evidence_intelligence import EvidenceIntelligenceEngine
from procedural.procedural_graph_engine import ProceduralGraphEngine
from citation.citation_verifier import CitationVerifierEngine
from utils import days_between

logger = logging.getLogger(__name__)

class SarfaesiBankEngine:
    """
    Law-Firm Grade Secured Creditor / Bank Enforcement Intelligence Engine.
    Evaluates actionable enforcement readiness, stay vulnerabilities, and statutory compliance.
    """

    @classmethod
    def evaluate_bank_position(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        proc_graph = ProceduralGraphEngine.build_graph(case_data)
        evidence_gaps = EvidenceIntelligenceEngine.evaluate_evidence_gaps(case_data)
        contradictions = EvidenceIntelligenceEngine.detect_cross_document_contradictions(case_data)

        readiness_score = 85
        critical_blockers = []
        stay_risk = "LOW"
        authorities = []

        # 1. CERSAI Check (Section 26D)
        cersai = case_data.get("cersai_registered") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        if not cersai:
            readiness_score -= 35
            critical_blockers.append("Security interest not registered on CERSAI portal (Section 26D statutory bar).")
            stay_risk = "CRITICAL"
            authorities.append("Section 26D SARFAESI Act, 2002")

        # 2. Section 13(3A) Reply Check
        rep_date = case_data.get("borrower_representation_date") or case_data.get("borrower_objection")
        reply_date = case_data.get("bank_reply_13_3a_date") or case_data.get("bank_reply_13_3a")
        poss_date = case_data.get("possession_13_4_date")
        if rep_date and not reply_date and poss_date:
            readiness_score -= 35
            critical_blockers.append("Section 13(4) possession taken without communicating reasoned decision on Section 13(3A) objections.")
            stay_risk = "CRITICAL"
            authorities.append("Mardia Chemicals Ltd. v. Union of India (2004) 4 SCC 311")
        elif rep_date and reply_date:
            r_days = days_between(rep_date, reply_date) if (isinstance(rep_date, str) and isinstance(reply_date, str)) else None
            if r_days is not None and r_days > 15:
                readiness_score -= 25
                critical_blockers.append(f"Section 13(3A) reply communicated in {r_days} days (exceeding mandatory 15-day limit).")
                stay_risk = "HIGH"

        # 3. Agricultural Land Exemption (Section 31(i))
        is_agri = case_data.get("is_agricultural_land") or str(case_data.get("agricultural_land", "")).lower() in ["yes", "true", "1"]
        if is_agri:
            readiness_score -= 50
            critical_blockers.append("Mortgaged property is agricultural land, exempt from SARFAESI U/S 31(i).")
            stay_risk = "FATAL"
            authorities.append("ITC Ltd. v. Blue Coast Hotels Ltd. (2018) 15 SCC 99")

        # 4. De Minimis Debt Limit (Section 31(g))
        outstanding = float(case_data.get("outstanding_amount") or case_data.get("debt_amount") or 0.0)
        sanction = float(case_data.get("sanction_amount") or 0.0)
        if outstanding > 0 and outstanding < 100000:
            readiness_score -= 45
            critical_blockers.append("Outstanding debt is less than ₹100,000 statutory minimum U/S 31(g).")
            stay_risk = "FATAL"
        elif sanction > 0 and outstanding > 0 and (outstanding / sanction) < 0.20:
            readiness_score -= 40
            critical_blockers.append("Unpaid debt is less than 20% of principal & interest U/S 31(g).")
            stay_risk = "FATAL"

        # 5. Rule 8(2) Newspaper Publication
        pub_done = case_data.get("newspaper_publication_done") or str(case_data.get("newspaper_pub", "")).lower() in ["yes", "true", "1"]
        if poss_date and not pub_done:
            readiness_score -= 20
            critical_blockers.append("Possession notice not published in 2 newspapers within 7 days under Rule 8(2).")

        # 6. Rule 8(6)/9(1) 30-Day Auction Notice
        auction_notice = case_data.get("auction_notice_date")
        auction_date = case_data.get("auction_date")
        if auction_notice and auction_date:
            a_days = days_between(auction_notice, auction_date) if (isinstance(auction_notice, str) and isinstance(auction_date, str)) else None
            if a_days is not None and a_days < 30:
                readiness_score -= 40
                critical_blockers.append(f"Auction notice period is only {a_days} days (mandatory 30 days under Rule 8(6)/9(1)).")
                stay_risk = "FATAL"
                authorities.append("Mathew Varghese v. M. Amritha Kumar (2014) 5 SCC 610")

        # 7. Active NCLT Moratorium (Section 14 IBC)
        if case_data.get("ibc_moratorium") or str(case_data.get("cirp_active", "")).lower() in ["yes", "true", "1"]:
            readiness_score -= 50
            critical_blockers.append("Active NCLT CIRP Moratorium U/S 14 IBC bars all SARFAESI enforcement.")
            stay_risk = "FATAL"
            authorities.append("Indian Overseas Bank v. RCM Infrastructure Ltd. (2022)")

        readiness_score = max(10, min(95, readiness_score))

        top_authority = CitationVerifierEngine.verify_citation(authorities[0] if authorities else "Mardia Chemicals Ltd. v. Union of India (2004) 4 SCC 311")
        next_actions = ProceduralGraphEngine.determine_next_best_actions(case_data, {"score": readiness_score})

        return {
            "perspective": "Secured Creditor / Bank Enforcement",
            "enforcement_readiness_score": readiness_score,
            "current_procedural_stage": proc_graph.get("current_stage", "Pre-Enforcement"),
            "stay_risk": stay_risk,
            "critical_blockers": critical_blockers,
            "evidence_gaps": evidence_gaps,
            "cross_document_contradictions": contradictions,
            "procedural_graph": proc_graph,
            "next_legally_permissible_action": next_actions[0]["action"] if next_actions else "Maintain statutory compliance posture.",
            "next_actions_checklist": next_actions,
            "primary_authority": top_authority
        }

