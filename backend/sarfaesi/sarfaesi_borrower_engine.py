import logging
from typing import Dict, List, Any
from evidence.evidence_intelligence import EvidenceIntelligenceEngine
from procedural.procedural_graph_engine import ProceduralGraphEngine
from citation.citation_verifier import CitationVerifierEngine
from utils import days_between

logger = logging.getLogger(__name__)

class SarfaesiBorrowerEngine:
    """
    Law-Firm Grade Borrower Securitisation Application (SA) Defense Engine.
    Evaluates DRT stay probability, statutory defense grounds, Section 17 limitation, and Section 18 DRAT pre-deposit.
    """

    @classmethod
    def evaluate_borrower_position(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        case_data["perspective"] = "borrower"
        proc_graph = ProceduralGraphEngine.build_graph(case_data)
        evidence_gaps = EvidenceIntelligenceEngine.evaluate_evidence_gaps(case_data)
        contradictions = EvidenceIntelligenceEngine.detect_cross_document_contradictions(case_data)

        sa_score = 45
        grounds = []
        critical_grounds = []

        # Ground 1: Agricultural Land Exemption (Section 31(i))
        if case_data.get("is_agricultural_land") or str(case_data.get("agricultural_land", "")).lower() in ["yes", "true", "1"]:
            sa_score += 45
            g = "Property constitutes Agricultural Land, completely exempt from SARFAESI U/S 31(i) (ITC v. Blue Coast Hotels)."
            grounds.append(g)
            critical_grounds.append(g)

        # Ground 2: CERSAI Non-Registration (Section 26D)
        cersai = case_data.get("cersai_registered") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        if not cersai:
            sa_score += 35
            g = "Security interest not registered on CERSAI portal (Section 26D statutory prohibition)."
            grounds.append(g)
            critical_grounds.append(g)

        # Ground 3: Section 13(3A) Objection Reply Breach
        rep_date = case_data.get("borrower_representation_date") or case_data.get("borrower_objection")
        reply_date = case_data.get("bank_reply_13_3a_date") or case_data.get("bank_reply_13_3a")
        poss_date = case_data.get("possession_13_4_date")
        if rep_date and not reply_date and poss_date:
            sa_score += 35
            g = "Bank took Section 13(4) possession without communicating reasoned decision on Section 13(3A) objections (Mardia Chemicals rule)."
            grounds.append(g)
            critical_grounds.append(g)
        elif rep_date and reply_date:
            d = days_between(rep_date, reply_date) if (isinstance(rep_date, str) and isinstance(reply_date, str)) else None
            if d is not None and d > 15:
                sa_score += 25
                g = f"Bank delayed Section 13(3A) reply to {d} days, breaching mandatory 15-day statutory cap."
                grounds.append(g)

        # Ground 4: Rule 8(6)/9(1) Short Auction Notice (<30 Days)
        auction_notice = case_data.get("auction_notice_date")
        auction_date = case_data.get("auction_date")
        if auction_notice and auction_date:
            a_days = days_between(auction_notice, auction_date) if (isinstance(auction_notice, str) and isinstance(auction_date, str)) else None
            if a_days is not None and a_days < 30:
                sa_score += 40
                g = f"Auction sale notice breaches 30-day requirement ({a_days} days provided; Mathew Varghese v. M. Amritha Kumar)."
                grounds.append(g)
                critical_grounds.append(g)

        # Ground 5: Active IBC Moratorium
        if case_data.get("ibc_moratorium") or str(case_data.get("cirp_active", "")).lower() in ["yes", "true", "1"]:
            sa_score += 45
            g = "Active NCLT CIRP Moratorium U/S 14 IBC bars all SARFAESI enforcement measures."
            grounds.append(g)
            critical_grounds.append(g)

        # Limitation Check under Section 17(1) (45 Days)
        limitation_remaining_days = None
        limitation_status = "COMPLIANT"
        if poss_date:
            from datetime import datetime
            sa_filing = case_data.get("sa_filing_date") or case_data.get("filing_date") or datetime.now().strftime("%Y-%m-%d")
            elapsed = days_between(poss_date, sa_filing) if (isinstance(poss_date, str) and isinstance(sa_filing, str)) else None
            if elapsed is not None:
                limitation_remaining_days = max(0, 45 - elapsed)
                if elapsed > 45:
                    sa_score -= 40
                    limitation_status = "EXPIRED"
                    grounds.append(f"WARNING: Section 17 SA limitation expired ({elapsed} days elapsed since Section 13(4) measure).")

        sa_score = max(10, min(95, sa_score))
        strongest_ground = grounds[0] if grounds else "Procedural verification of notice delivery & CERSAI registration required."

        # Section 18 DRAT Pre-Deposit Calculation
        debt = float(case_data.get("outstanding_amount") or case_data.get("debt_amount") or 0.0)

        next_actions = ProceduralGraphEngine.determine_next_best_actions(case_data, {"score": sa_score})
        top_authority = CitationVerifierEngine.verify_citation("Mardia Chemicals Ltd. v. Union of India (2004) 4 SCC 311")

        return {
            "perspective": "Borrower SA Defense Mode",
            "sa_readiness_score": sa_score,
            "limitation_remaining_days": limitation_remaining_days,
            "limitation_status": limitation_status,
            "total_grounds_identified": len(grounds),
            "critical_grounds_count": len(critical_grounds),
            "strongest_ground": strongest_ground,
            "all_grounds": grounds,
            "drat_pre_deposit": {
                "debt_amount": debt,
                "standard_50_percent": 0.50 * debt,
                "minimum_25_percent": 0.25 * debt,
                "authority": "Section 18(1) SARFAESI Act, 2002"
            },
            "evidence_gaps_in_bank_case": evidence_gaps,
            "bank_likely_response": "Bank will raise preliminary objections asserting statutory compliance or post-notice CERSAI registration.",
            "interim_relief_strategy": "File urgent stay application praying for ad-interim stay on Section 14 execution / e-auction sale.",
            "next_best_actions": next_actions,
            "primary_authority": top_authority
        }

