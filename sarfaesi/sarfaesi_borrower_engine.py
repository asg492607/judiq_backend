import logging
from typing import Dict, List, Any
from evidence.evidence_intelligence import EvidenceIntelligenceEngine
from procedural.procedural_graph_engine import ProceduralGraphEngine
from citation.citation_verifier import CitationVerifierEngine
from utils import days_between

logger = logging.getLogger(__name__)

class SarfaesiBorrowerEngine:
    """
    Borrower SA Defense Intelligence Engine:
    Answers:
    1. What is the Securitisation Application (SA) readiness score before DRT?
    2. What are the critical grounds for an interim stay/injunction?
    3. What is the strongest legal ground?
    4. What limitation period remains under Section 17(1) (45 days)?
    5. What is the Bank's likely counter-strategy?
    """

    @classmethod
    def evaluate_borrower_position(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        case_data["perspective"] = "borrower"
        proc_graph = ProceduralGraphEngine.build_graph(case_data)
        evidence_gaps = EvidenceIntelligenceEngine.evaluate_evidence_gaps(case_data)
        contradictions = EvidenceIntelligenceEngine.detect_cross_document_contradictions(case_data)

        sa_score = 50
        grounds = []
        critical_grounds = []

        # Ground 1: Agricultural Land Exemption (Section 31(i))
        if case_data.get("is_agricultural_land"):
            sa_score += 35
            g = "Property constitutes Agricultural Land, completely exempt from SARFAESI proceedings U/S 31(i)."
            grounds.append(g)
            critical_grounds.append(g)

        # Ground 2: CERSAI Non-Registration (Section 26D)
        cersai = case_data.get("cersai_registered") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        if not cersai:
            sa_score += 30
            g = "Security interest not registered on CERSAI portal (Section 26D statutory bar on enforcement)."
            grounds.append(g)
            critical_grounds.append(g)

        # Ground 3: Section 13(3A) Objection Reply Breach
        rep_date = case_data.get("borrower_representation_date")
        reply_date = case_data.get("bank_reply_13_3a_date")
        poss_date = case_data.get("possession_13_4_date")
        if rep_date and not reply_date and poss_date:
            sa_score += 25
            g = "Bank took Section 13(4) possession without communicating reasoned decision on Section 13(3A) representation (Mardia Chemicals rule)."
            grounds.append(g)
            critical_grounds.append(g)
        elif rep_date and reply_date:
            d = days_between(rep_date, reply_date)
            if d is not None and d > 15:
                sa_score += 20
                g = f"Bank delayed Section 13(3A) reply to {d} days, breaching mandatory 15-day statutory cap."
                grounds.append(g)

        # Limitation Check under Section 17(1)
        limitation_remaining_days = None
        limitation_status = "COMPLIANT"
        if poss_date:
            from datetime import datetime
            sa_filing = case_data.get("sa_filing_date") or case_data.get("filing_date") or datetime.now().strftime("%Y-%m-%d")
            elapsed = days_between(poss_date, sa_filing)
            if elapsed is not None:
                limitation_remaining_days = max(0, 45 - elapsed)
                if elapsed > 45:
                    sa_score -= 40
                    limitation_status = "EXPIRED"
                    grounds.append(f"WARNING: Section 17 SA limitation expired ({elapsed} days elapsed since Section 13(4) measure).")

        sa_score = max(10, min(95, sa_score))
        strongest_ground = grounds[0] if grounds else "Procedural verification of notice delivery required."

        next_actions = ProceduralGraphEngine.determine_next_best_actions(case_data, {"score": sa_score})
        top_authority = CitationVerifierEngine.verify_citation("Mardia Chemicals Ltd. v. Union of India (2004)")

        return {
            "perspective": "Borrower SA Defense Mode",
            "sa_readiness_score": sa_score,
            "limitation_remaining_days": limitation_remaining_days,
            "limitation_status": limitation_status,
            "total_grounds_identified": len(grounds),
            "critical_grounds_count": len(critical_grounds),
            "strongest_ground": strongest_ground,
            "all_grounds": grounds,
            "evidence_gaps_in_bank_case": evidence_gaps,
            "bank_likely_response": "Bank will raise preliminary objection claiming SA is barred by limitation or that CERSAI registration was completed post-notice.",
            "interim_relief_strategy": "File urgent interim application praying for stay on Section 14 execution / public auction.",
            "next_best_actions": next_actions,
            "primary_authority": top_authority
        }
