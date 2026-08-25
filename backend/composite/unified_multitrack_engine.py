import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.base_domain_engine import BaseDomainEngine
from sarfaesi.sarfaesi_domain_engine import SarfaesiDomainEngine
from cheque_bounce.cheque_bounce_engine import ChequeBounceEngine
from criminal.criminal_engine import CriminalEngine
from citation.citation_verifier import CitationVerifierEngine
from audit.audit_ledger import AuditLedger

logger = logging.getLogger(__name__)

class UnifiedMultiTrackEngine(BaseDomainEngine):
    """
    Unified Multi-Track Legal Domain Engine.
    Executes simultaneous concurrent analysis across:
      - Track 1: SARFAESI Act, 2002 & DRT Recovery
      - Track 2: Section 138 Negotiable Instruments Act, 1881 (Cheque Bounce)
      - Track 3: Criminal Law (BNS 318/316 / IPC 420/406 & BNSS / CrPC)
    
    Provides cross-track synergy analysis, limitation tracking, multi-remedy procedural graphs,
    and consolidated litigation strategy for a single loan account / defaulting borrower.
    """

    @property
    def domain_name(self) -> str:
        return "composite"

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes unified 360-degree legal analysis across SARFAESI, Sec 138, and Criminal tracks.
        """
        logger.info(f"[UNIFIED_MULTITRACK] Initiating composite evaluation for case: {case_data.get('case_id', 'ANON')}")
        
        # 1. Execute Track 1: SARFAESI Evaluation
        sarfaesi_res: Dict[str, Any] = {}
        try:
            sarfaesi_engine = SarfaesiDomainEngine()
            sarfaesi_res = sarfaesi_engine.analyze(case_data, concepts)
        except Exception as e:
            logger.error(f"[UNIFIED_MULTITRACK] SARFAESI track error: {e}", exc_info=True)
            sarfaesi_res = {"score": 50, "verdict": "SARFAESI EVALUATION ERROR", "fatal_defect": str(e)}

        # 2. Execute Track 2: Cheque Bounce (Section 138 NI Act) Evaluation
        cb_res: Dict[str, Any] = {}
        try:
            cb_engine = ChequeBounceEngine()
            cb_res = cb_engine.analyze(case_data, concepts)
        except Exception as e:
            logger.error(f"[UNIFIED_MULTITRACK] Cheque bounce track error: {e}", exc_info=True)
            cb_res = {"score": 50, "verdict": "SEC 138 EVALUATION ERROR", "fatal_defect": str(e)}

        # 3. Execute Track 3: Criminal (BNS/IPC) Evaluation
        criminal_res: Dict[str, Any] = {}
        try:
            criminal_engine = CriminalEngine()
            criminal_res = criminal_engine.analyze(case_data, concepts)
        except Exception as e:
            logger.error(f"[UNIFIED_MULTITRACK] Criminal track error: {e}", exc_info=True)
            criminal_res = {"score": 50, "verdict": "CRIMINAL EVALUATION ERROR", "fatal_defect": str(e)}

        # 4. Cross-Track Strategic Synergies & Conflict Detection
        cross_track_matrix = cls._evaluate_cross_track_synergies(case_data, sarfaesi_res, cb_res, criminal_res)

        # 5. Composite Weighted Score Calculation
        sarfaesi_score = float(sarfaesi_res.get("score") or sarfaesi_res.get("enforcement_readiness_score") or 50.0)
        cb_score = float(cb_res.get("score") or cb_res.get("final_score") or 50.0)
        crim_score = float(criminal_res.get("score") or criminal_res.get("prosecution_viability_score") or 50.0)

        # Weights: 40% SARFAESI (Asset realization), 35% Sec 138 (Speedy penal pressure), 25% Criminal (Leverage/Punitive)
        composite_score = round((sarfaesi_score * 0.40) + (cb_score * 0.35) + (crim_score * 0.25), 1)

        # 6. Consolidated Procedural Graph & Next Actions
        procedural_graph = cls.build_procedural_graph(case_data)
        next_actions = cls.get_next_actions(case_data, {
            "composite_score": composite_score,
            "sarfaesi": sarfaesi_res,
            "cheque_bounce": cb_res,
            "criminal": criminal_res,
            "cross_track_matrix": cross_track_matrix
        })

        # 7. Collect Fatal Defects across all 3 tracks
        all_defects = []
        for track_name, res in [("SARFAESI", sarfaesi_res), ("Section 138", cb_res), ("Criminal", criminal_res)]:
            d = res.get("fatal_defect")
            if d:
                all_defects.append(f"[{track_name}] {d}")
        
        composite_fatal_defect = " | ".join(all_defects) if all_defects else None

        # 8. Unified Citation Authorities
        unified_citations = []
        mardia = CitationVerifierEngine.verify_citation("Mardia Chemicals Ltd. v. Union of India (2004) 4 SCC 311")
        sri_krishna = CitationVerifierEngine.verify_citation("M/s Sri Krishna Agencies v. State of A.P. (2009) 1 SCC 69")
        transcore = CitationVerifierEngine.verify_citation("Transcore v. Union of India (2008) 1 SCC 125")
        
        for cit in [transcore, sri_krishna, mardia]:
            if cit.get("status") == "VERIFIED":
                unified_citations.append(cit)

        # 9. Draft Generation Package
        drafts_package = {
            "sarfaesi_draft": sarfaesi_res.get("draft") or sarfaesi_res.get("draft_document"),
            "section_138_draft": cb_res.get("draft") or cb_res.get("draft_document"),
            "criminal_draft": criminal_res.get("draft") or criminal_res.get("draft_document")
        }

        # 10. Audit Ledger Record
        AuditLedger.record_entry(
            case_id=case_data.get("case_id", "ANON-MULTITRACK"),
            finding_id="MULTITRACK-001",
            finding_text=f"Multi-track analysis completed with Composite Score {composite_score}/100. Tracks evaluated: SARFAESI, Sec 138, Criminal.",
            evidence_relied="Multi-track concurrent statutory evaluation",
            rule_applied="Parallel remedies under Transcore v. UOI (2008) & Sri Krishna Agencies (2009)",
            authority="Transcore v. Union of India (2008) 1 SCC 125",
            confidence=0.98,
            verdict="STRONG MULTI-TRACK" if composite_score >= 70 else ("VIABLE MULTI-TRACK" if composite_score >= 45 else "HIGH RISK / VULNERABLE")
        )

        return {
            "domain": "composite",
            "score": composite_score,
            "final_score": composite_score,
            "verdict": "STRONG MULTI-TRACK POSITION" if composite_score >= 70 else ("MODERATE COMPOSITE READINESS" if composite_score >= 45 else "HIGH MULTI-TRACK RISK"),
            "fatal_defect": composite_fatal_defect,
            "tracks": {
                "sarfaesi": {
                    "score": sarfaesi_score,
                    "verdict": sarfaesi_res.get("verdict"),
                    "fatal_defect": sarfaesi_res.get("fatal_defect"),
                    "key_findings": sarfaesi_res.get("reasoning_trace") or sarfaesi_res.get("findings", [])
                },
                "cheque_bounce_138": {
                    "score": cb_score,
                    "verdict": cb_res.get("verdict"),
                    "fatal_defect": cb_res.get("fatal_defect"),
                    "key_findings": cb_res.get("reasoning_trace") or cb_res.get("findings", [])
                },
                "criminal_bns_ipc": {
                    "score": crim_score,
                    "verdict": criminal_res.get("verdict"),
                    "fatal_defect": criminal_res.get("fatal_defect"),
                    "key_findings": criminal_res.get("reasoning_trace") or criminal_res.get("findings", [])
                }
            },
            "cross_track_matrix": cross_track_matrix,
            "procedural_graph": procedural_graph,
            "next_best_actions": next_actions,
            "citations": unified_citations,
            "drafts_package": drafts_package,
            "decision_status": "PROCEED" if not composite_fatal_defect else "LAWYER_REVIEW_REQUIRED"
        }

    @classmethod
    def _evaluate_cross_track_synergies(cls, case_data: Dict[str, Any], sarfaesi_res: Dict[str, Any], cb_res: Dict[str, Any], criminal_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates cross-track legal interactions, maintainability, stay risks, and strategic leverage.
        """
        synergies = []
        risks = []
        tactical_recommendations = []

        # 1. Maintainability of parallel actions (Transcore / Sri Krishna Agencies)
        synergies.append({
            "principle": "Parallel Maintainability of Civil Recovery & Criminal Prosecution",
            "statutory_basis": "Transcore v. UOI (2008) & M/s Sri Krishna Agencies v. State of A.P. (2009)",
            "impact": "POSITIVE: Pendency of SARFAESI proceedings or DRT Securitisation Applications cannot be used by the borrower to stay or quash Section 138 NI Act or Criminal proceedings."
        })

        # 2. Section 143A Interim Compensation vs SARFAESI Asset Realization
        if case_data.get("dishonour_memo") or case_data.get("date_of_dishonour"):
            synergies.append({
                "principle": "Early Cash Flow through Section 143A NI Act (20% Interim Deposit)",
                "statutory_basis": "Section 143A Negotiable Instruments Act, 1881",
                "impact": "LEVERAGE: While SARFAESI physical possession via CMM/DM u/s 14 takes 60-120 days, filing a Sec 143A application in the Magistrate Court can secure a 20% interim cash deposit within 60 days of plea framing."
            })

        # 3. Double Recovery Accounting Safeguard
        risks.append({
            "risk_title": "Appropriation of Asset Auction Proceeds in 138/Criminal Trial",
            "statutory_basis": "D. Purushotama Reddy v. K. Sateesh (2008) 8 SCC 505",
            "mitigation": "MANDATORY SAFEGUARD: Any sums recovered via SARFAESI auction must be promptly credited to the loan account and formally placed on judicial record in the 138 court to prevent claims of double compensation."
        })

        # 4. Purely Civil Dispute vs Section 482 Quashing Risk
        is_fraud_alleged = bool(case_data.get("offense_type") or case_data.get("entrustment_proven") or case_data.get("alienation_of_hypothecated_assets"))
        if not is_fraud_alleged and criminal_res.get("score", 0) < 50:
            risks.append({
                "risk_title": "Section 482 CrPC / Section 528 BNSS Quashing Risk (Bhajan Lal Doctrine)",
                "statutory_basis": "State of Haryana v. Bhajan Lal (1992) & S.W. Palanitkar (2002)",
                "mitigation": "Ensure criminal complaint specifies deceit/fraudulent intention at inception or specific misappropriation of hypothecated stocks. Mere breach of loan contract is liable to be quashed as civil dispute."
            })
        else:
            synergies.append({
                "principle": "High-Pressure Criminal Deterrence on Concealed/Alienated Assets",
                "statutory_basis": "Section 318(4) BNS / Section 420 IPC & Section 316 BNS / Section 406 IPC",
                "impact": "MAXIMUM LEVERAGE: Allegations of dishonest alienation of hypothecated goods provide substantive grounds for immediate police investigation under S.156(3) BNSS."
            })

        # 5. Strategic Tactical Roadmap
        tactical_recommendations = [
            "1. Issue Section 13(2) SARFAESI 60-day Demand Notice immediately to start the statutory recovery clock.",
            "2. Ensure Section 138 Statutory Notice is served within 30 days of Cheque Return Memo.",
            "3. If Section 13(3A) borrower representation is received, mandatorily reply within 15 days to preserve Section 13(4) validity.",
            "4. File Section 142 Criminal Complaint upon expiry of the 15-day 138 notice cure window, immediately moving Section 143A application.",
            "5. Apply under Section 14 SARFAESI to the DM/CMM for physical possession of mortgaged collateral."
        ]

        return {
            "synergies": synergies,
            "risks": risks,
            "tactical_recommendations": tactical_recommendations,
            "overall_parallel_viability": "HIGH" if len(risks) <= 1 else "REQUIRES_CAUTION"
        }

    @classmethod
    def build_procedural_graph(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a comprehensive, unified procedural milestone graph across all 3 tracks.
        """
        sarfaesi_nodes = SarfaesiDomainEngine().build_procedural_graph(case_data).get("nodes", [])
        cb_nodes = ChequeBounceEngine().build_procedural_graph(case_data).get("nodes", [])
        crim_nodes = CriminalEngine().build_procedural_graph(case_data).get("nodes", [])

        # Format tracks cleanly
        track_map = {
            "Track 1 (SARFAESI Act)": sarfaesi_nodes,
            "Track 2 (Section 138 NI Act)": cb_nodes,
            "Track 3 (Criminal BNS/IPC)": crim_nodes
        }

        master_nodes = []
        for track_title, nodes in track_map.items():
            for n in nodes:
                node_copy = dict(n)
                node_copy["track"] = track_title
                master_nodes.append(node_copy)

        return {
            "current_stage": "Unified Multi-Track Enforcement & Prosecution",
            "total_milestones": len(master_nodes),
            "tracks": track_map,
            "nodes": master_nodes
        }

    @classmethod
    def get_next_actions(cls, case_data: Dict[str, Any], evaluation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Aggregates and prioritizes next best actions across SARFAESI, 138, and Criminal tracks by urgency.
        """
        actions = [
            {
                "priority": "CRITICAL (Statutory 30-Day Window)",
                "track": "Section 138 NI Act",
                "action": "Serve Section 138 Statutory Legal Demand Notice within 30 days of Cheque Return Memo.",
                "deadline_days": 30,
                "authority": "Section 138(b) Negotiable Instruments Act, 1881"
            },
            {
                "priority": "HIGH (Statutory 60-Day Window)",
                "track": "SARFAESI Act",
                "action": "Issue Section 13(2) 60-Day Demand Notice and verify CERSAI charge registration under Section 26D.",
                "deadline_days": 60,
                "authority": "Section 13(2) & 26D SARFAESI Act, 2002"
            },
            {
                "priority": "HIGH (Statutory 15-Day Window)",
                "track": "SARFAESI Act",
                "action": "Dispose of borrower representation under Section 13(3A) with reasoned order within 15 days.",
                "deadline_days": 15,
                "authority": "Section 13(3A) SARFAESI Act, 2002 & Mardia Chemicals"
            },
            {
                "priority": "MEDIUM (Substantive Relief)",
                "track": "Section 138 NI Act",
                "action": "Move application for 20% interim compensation under Section 143A upon framing of notice/plea.",
                "deadline_days": 60,
                "authority": "Section 143A Negotiable Instruments Act, 1881"
            },
            {
                "priority": "STRATEGIC (Asset Recovery)",
                "track": "SARFAESI Act",
                "action": "File Section 14 application before DM/CMM with statutory 9-point affidavit for physical possession.",
                "deadline_days": 90,
                "authority": "Section 14 SARFAESI Act & NKGSB Co-op Bank v. Subir Chakravarty"
            },
            {
                "priority": "PUNITIVE (Fraud Deterrence)",
                "track": "Criminal (BNS/IPC)",
                "action": "If hypothecated security is missing/diverted, file Section 156(3) BNSS application for FIR registration.",
                "deadline_days": 45,
                "authority": "Section 318(4) & 316 BNS / Sections 420 & 406 IPC"
            }
        ]
        return actions
