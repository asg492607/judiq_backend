from datetime import datetime
import logging
from typing import List, Dict, Any
from kb_manager import kb_manager

logger = logging.getLogger(__name__)

def ensure_list(x):
    if x is None: return []
    if isinstance(x, list): return x
    return [x]

def ensure_number(x, default=0):
    try: return float(x)
    except: return default

from base_scoring_engine import (
    BaseScoringEngine, PENALTY_COMPANY_DIRECTOR_NOT_NAMED, PENALTY_DIRECTOR_RESIGNED,
    PENALTY_BASALINGAPPA_FATAL, PENALTY_BASALINGAPPA_HIGH, PENALTY_LIMITATION,
    PENALTY_NOTICE_DEFECT, PENALTY_UNVERIFIED_SIGNATURE, PENALTY_MATERIAL_ALTERATION,
    PENALTY_LOW_RELIABILITY_EVIDENCE, PILLAR_CHEQUE_ORIGINAL, PILLAR_CHEQUE_PHOTOCOPY,
    PILLAR_CHEQUE_MISSING, PILLAR_MEMO_PRESENT, PILLAR_MEMO_MISSING, PILLAR_NOTICE_VALID,
    PILLAR_NOTICE_LATE, PILLAR_NOTICE_MISSING, PILLAR_DEBT_PROVEN, PILLAR_DEBT_MISSING,
    STRATEGIC_PRO_COMPLAINANT, STRATEGIC_PRO_ACCUSED, PENALTY_NOTICE_DELIVERY_FAILED
)

class ScoringEngineV12(BaseScoringEngine):
    @classmethod
    def resolve_conflicts(cls, concepts: List[Dict]) -> List[Dict]:
        """Resolve conflicting concepts - keep higher confidence one"""
        concept_names = [c["concept"] for c in concepts]
        resolved = []
        conflicts = [
            ("legally_enforceable_debt", "no_debt_proof"),
            ("legal_notice_compliance", "notice_defect"),
            ("cheque_bounce", "dishonour_disputed")
        ]
        conf_map = {c["concept"]: c["confidence"] for c in concepts}
        blacklisted = set()
        
        for pos, neg in conflicts:
            if pos in concept_names and neg in concept_names:
                if conf_map[pos] > conf_map[neg] + 0.15:
                    blacklisted.add(neg)
                elif conf_map[neg] > conf_map[pos] + 0.15:
                    blacklisted.add(pos)
                else:
                    blacklisted.add(pos)  # Conservative - keep negative
        
        for c in concepts:
            if c["concept"] not in blacklisted:
                resolved.append(c)
        
        return resolved

    @classmethod
    def calculate_score_with_trace(cls, 
                                   case_data: Dict,
                                   concepts: List[Dict],
                                   contradictions: List[Dict],
                                   evidence_assessment: Dict,
                                   raw_input: Dict = None) -> Dict:
        """
        REALISTIC SCORING ENGINE - Produces varied scores based on actual case strength
        Includes Procedural, Evidentiary, and Strategic breakdown with Explicit Causality.
        """
        concepts = cls.resolve_conflicts(ensure_list(concepts))
        
        # --- NEW: CONCEPT INJECTION (Ensures Critical Issues show up in ResponseBuilder) ---
        concept_names = {c["concept"] for c in concepts}
        trace = []
        causality_map = [] 
        uncertainty_messages = []
        low_reliability_evidence = []
        
        # --- V3 ENHANCEMENT: STRICT CALIBRATION (NO JITTER) ---
        base_score = 15
        score = base_score
        trace.append(f"Standard Litigation Baseline: {base_score} points (Strictly Calibrated for Jurisdiction).")
        causality_map.append({"fact": "Litigation Baseline", "impact": base_score, "type": "neutral", "rationale": "Base probability of recovery in Indian courts."})

        # --- V3 ENHANCEMENT: EVIDENCE RELIABILITY ---
        evidence_reliability = cls.calculate_evidence_reliability(case_data)
        for name, data in evidence_reliability.items():
            if data.get("score", 1.0) < 0.5:
                low_reliability_evidence.append(name)
        
        # 0. JUDICIAL TEMPERAMENT (New Strategic Layer)
        judicial_mode = case_data.get("judicial_temperament", "Balanced")
        temperament_impact = 0
        if judicial_mode == "Pro-Complainant":
            temperament_impact = STRATEGIC_PRO_COMPLAINANT
            trace.append(f"Judicial Stance: Pro-Complainant/Strict Enforcement (+{STRATEGIC_PRO_COMPLAINANT} impact).")
        elif judicial_mode == "Pro-Accused":
            temperament_impact = STRATEGIC_PRO_ACCUSED
            trace.append(f"Judicial Stance: Pro-Accused/High Scrutiny ({STRATEGIC_PRO_ACCUSED} impact).")
        score += temperament_impact
        
        amount = ensure_number(case_data.get("amount", 0))
        
        # 1. PILLARS & COMPLIANCE SCORECARD
        cheque = bool(case_data.get('cheque_present'))
        memo = bool(case_data.get('dishonour_memo'))
        notice = bool(case_data.get('notice_sent'))
        debt = bool(case_data.get('debt_proven'))
        
        # PILLAR 1: CHEQUE
        if cheque: 
            cheque_type = case_data.get("cheque_proof_type", "original").lower()
            cheque_points = PILLAR_CHEQUE_ORIGINAL if cheque_type == "original" else PILLAR_CHEQUE_PHOTOCOPY
            score += cheque_points
            trace.append(f"Instrument Admissibility: {cheque_type.title()} instrument verified (+{cheque_points}).")
            causality_map.append({"fact": f"Cheque ({cheque_type})", "impact": cheque_points, "type": "positive", "rationale": "Possession of original instrument is 70% of the battle."})
        else:
            score += PILLAR_CHEQUE_MISSING
            trace.append(f"FATAL ERROR: Primary instrument missing ({PILLAR_CHEQUE_MISSING} impact).")
            causality_map.append({"fact": "Missing Original Cheque", "impact": PILLAR_CHEQUE_MISSING, "type": "negative", "rationale": "S.138 requires the instrument. Photocopies are inadmissible without Section 63(4) BSA."})

        # PILLAR 2: DISHONOUR MEMO
        if memo:
            memo_points = PILLAR_MEMO_PRESENT
            score += memo_points
            trace.append(f"Procedural Proof: Bank return memo authenticated (+{memo_points}).")
            causality_map.append({"fact": "Bank Memo Presence", "impact": memo_points, "type": "positive", "rationale": "Formal proof of dishonour by the banking institution."})
        else:
            score += PILLAR_MEMO_MISSING
            case_data["fatal_defect"] = "Missing Bank Return Memo"
            trace.append(f"CRITICAL GAP: Bank return memo missing ({PILLAR_MEMO_MISSING} impact).")
            causality_map.append({"fact": "Missing Bank Memo", "impact": PILLAR_MEMO_MISSING, "type": "negative", "rationale": "Magistrate cannot take cognizance without a return memo/debit advice."})

        # PILLAR 3: STATUTORY NOTICE
        if notice:
            notice_received_status = str(case_data.get("notice_received", "")).lower()
            if notice_received_status == "no":
                # Override triggered by Notice Delivery OCR/Postal
                score += PENALTY_NOTICE_DELIVERY_FAILED
                case_data["fatal_defect"] = "Invalid Notice Service (Address Not Found)"
                trace.append(f"{PENALTY_NOTICE_DELIVERY_FAILED} PROCEDURAL: Demand Notice tracking failed / address not found.")
                causality_map.append({"fact": "Notice Tracking Failed", "impact": -30, "type": "negative", "rationale": "Invalid service. S.138 cause of action fails if notice is not delivered (unless 'refused')."})
            elif "deemed served" in notice_received_status:
                trace.append("Statutory Compliance: Notice deemed served under S.27 General Clauses Act (Refused/Unclaimed).")
                causality_map.append({"fact": "Deemed Service", "impact": 0, "type": "neutral", "rationale": "Notice was returned with 'Refused' or 'Unclaimed' postal remark, constituting valid service under S.27 General Clauses Act."})

            within_30 = case_data.get("within_30_days", "Yes") == "Yes"
            notice_points = PILLAR_NOTICE_VALID if within_30 else PILLAR_NOTICE_LATE
            score += notice_points
            trace.append(f"Statutory Compliance: S.138(b) Demand Notice served (+{notice_points}).")
            causality_map.append({"fact": "S.138(b) Notice Compliance", "impact": notice_points, "type": "positive", "rationale": "Statutory notice window adhered to. Cause of action established."})
            if not within_30:
                causality_map.append({"fact": "Notice Delay", "impact": -18, "type": "negative", "rationale": "Notice sent beyond 30 days of dishonour. Requires condonation application."})
        else:
            score += PILLAR_NOTICE_MISSING
            case_data["fatal_defect"] = "Mandatory Demand Notice Not Served"
            trace.append(f"FATAL DEFECT: Mandatory demand notice not served ({PILLAR_NOTICE_MISSING} impact).")
            causality_map.append({"fact": "Notice Not Sent", "impact": PILLAR_NOTICE_MISSING, "type": "negative", "rationale": "Mandatory requirement. Complaint is non-maintainable without S.138 notice."})

        # PILLAR 4: DEBT
        compliance_pct = (sum([1 for p in [cheque, memo, notice, debt] if p]) / 4.0) * 100
        if debt:
            debt_points = 19
            if amount > 100000 and not case_data.get("agreement_registered"):
                debt_points -= 9
                trace.append("Evidentiary Risk: High-value agreement lacks registration (-9 impact).")
            score += debt_points
            trace.append(f"Liability Authentication: Enforceable debt proof established (+{debt_points}).")
            causality_map.append({"fact": "Debt Liability Proof", "impact": debt_points, "type": "positive", "rationale": "S.139 requires a legally enforceable debt."})
        else:
            score -= 18
            trace.append("Rebuttal Risk: Presumption u/s 139 is vulnerable due to lack of debt proof (-18 impact).")
            causality_map.append({"fact": "No Liability Proof", "impact": -18, "rationale": "S.139 presumption is rebuttable."})

        # --- V3 ENHANCEMENT: JITTER INJECTION (disabled per strict calibration) ---
        jitter = 0  # Strict calibration mode — no random jitter applied
        score += jitter
        # jitter is 0, no trace entry needed

        # EXPERT AUDITS
        accused_name = str(case_data.get("accused_name", "")).lower()
        is_company = any(x in accused_name for x in ["pvt", "ltd", "corp", "inc", "co.", "company"])
        if is_company:
            if not case_data.get("directors_named"):
                score += PENALTY_COMPANY_DIRECTOR_NOT_NAMED
                trace.append(f"{PENALTY_COMPANY_DIRECTOR_NOT_NAMED} FATAL: S.141 defect - Directors not named.")
                causality_map.append({"fact": "S.141 Defect", "impact": PENALTY_COMPANY_DIRECTOR_NOT_NAMED, "rationale": "Company prosecution fails without naming responsible officers."})
            
            resignation_date = case_data.get("director_resignation_date")
            cheque_date = case_data.get("cheque_date")
            if resignation_date and cheque_date:
                try:
                    res_dt = datetime.fromisoformat(resignation_date) if isinstance(resignation_date, str) else resignation_date
                    chq_dt = datetime.fromisoformat(cheque_date) if isinstance(cheque_date, str) else cheque_date
                    if res_dt < chq_dt:
                        score += PENALTY_DIRECTOR_RESIGNED
                        trace.append(f"{PENALTY_DIRECTOR_RESIGNED} FATAL: Vicarious Liability Gap (Resignation).")
                        causality_map.append({"fact": "Director Resignation", "impact": PENALTY_DIRECTOR_RESIGNED, "rationale": "Director resigned BEFORE instrument issuance. High Malicious Prosecution risk."})
                except: pass

        # Basalingappa & Sushil Kumar Check
        if amount > 500000 and not case_data.get("loan_via_bank") and not case_data.get("complainant_itr_available"):
            score += PENALTY_BASALINGAPPA_FATAL
            max_score_cap = min(max_score_cap, 25)  # Hard cap at 25 for S.269SS fatal violation
            case_data["fatal_defect"] = "Basalingappa Trap: Unaccounted Cash > ₹5L without ITR"
            trace.append(f"{PENALTY_BASALINGAPPA_FATAL} FATAL EVIDENTIARY GAP: ₹5L+ cash loan without ITR.")
            causality_map.append({"fact": "Basalingappa Fatal", "impact": PENALTY_BASALINGAPPA_FATAL, "rationale": "High-value cash loans without source proof trigger immediate presumption collapse."})
            if "unaccounted_cash_loans" not in concept_names:
                concepts.append({"concept": "unaccounted_cash_loans", "confidence": 0.95, "legal_impact": "Fatal evidentiary gap for high-value cash loans per Basalingappa ruling."})

        # Limitation & Notice Defects
        existing_concepts = [c["concept"] for c in concepts]
        if "limitation_issue" in existing_concepts:
            score += PENALTY_LIMITATION
            trace.append(f"{PENALTY_LIMITATION} CRITICAL: Limitation Period delay (S.142 violation)")
            causality_map.append({"fact": "Limitation Delay", "impact": PENALTY_LIMITATION, "rationale": "S.142 is a jurisdictional bar."})
        
        if "notice_defect" in existing_concepts:
            score += PENALTY_NOTICE_DEFECT
            trace.append(f"{PENALTY_NOTICE_DEFECT} CRITICAL: Defective statutory notice")
            causality_map.append({"fact": "Notice Defect", "impact": PENALTY_NOTICE_DEFECT, "rationale": "Statutory notice must be perfect."})
            
        tracking_status = str(case_data.get("notice_delivery_status", "delivered")).lower()
        if "not found" in tracking_status or "returned to sender" in tracking_status:
            score -= 45
            trace.append("-45 CRITICAL: Address Not Found destroys S.27 presumption of service.")
            causality_map.append({"fact": "Invalid Service Address", "impact": -45, "rationale": "Without valid address, deemed service under S.27 General Clauses Act is voided. Highly likely to be dismissed at summoning stage."})

        # Signature & Alteration
        if "signature_dispute" in existing_concepts and not case_data.get("signature_verified_by_bank"):
            score += PENALTY_UNVERIFIED_SIGNATURE
            trace.append(f"{PENALTY_UNVERIFIED_SIGNATURE} CRITICAL: Signature Disputed and Unverified (Anti-Gaming Rule).")
            causality_map.append({"fact": "Unverified Signature Dispute", "impact": PENALTY_UNVERIFIED_SIGNATURE, "type": "negative", "rationale": "Without bank verification or handwriting expert, a signature dispute is a massive vulnerability."})

        if case_data.get("handwriting_different") or "material_alteration" in existing_concepts:
            score += PENALTY_MATERIAL_ALTERATION
            case_data["fatal_defect"] = "FSL Stay (18-24 months) on Handwriting Trap" # Trigger engine_core hard cap
            trace.append(f"{PENALTY_MATERIAL_ALTERATION} FATAL: Material Alteration Trap (S.87) - FSL Stay.")
            causality_map.append({"fact": "Material Alteration (FSL Risk)", "impact": PENALTY_MATERIAL_ALTERATION, "type": "negative", "rationale": "Different inks/handwriting voids the instrument. Triggers S.45 Evidence Act FSL analysis stay."})

        # â”€â”€ CONTRADICTION PROPAGATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for cont in contradictions:
            penalty = cont.get("penalty", 0)
            score += penalty
            trace.append(f"{penalty} Contradiction: {cont['issue']} ({cont['severity']})")
            causality_map.append({
                "fact": cont["issue"],
                "impact": penalty,
                "type": "negative",
                "rationale": cont["detail"]
            })

        if low_reliability_evidence:
            uncertainty_messages.append(f"â€œConfidence reduced because evidence reliability is weak for: {', '.join(low_reliability_evidence)}.â€")

        # Evidence Reliability Penalty Integration
        max_score_cap = 99
        for name, data in evidence_reliability.items():
            if data.get("score", 1.0) < 0.5:
                score += PENALTY_LOW_RELIABILITY_EVIDENCE
                max_score_cap = min(max_score_cap, 65)
                trace.append(f"{PENALTY_LOW_RELIABILITY_EVIDENCE} EVIDENTIARY: Low reliability on critical evidence ({name}). Score capped at 65.")
                causality_map.append({"fact": f"Low Reliability: {name}", "impact": PENALTY_LOW_RELIABILITY_EVIDENCE, "type": "negative", "rationale": data.get("reason", "Evidence format is vulnerable to challenge.")})

        # Document Verification Penalties (OCR Override)
        verification_penalties = case_data.get("verification_penalties", 0)
        if verification_penalties < 0:
            score += verification_penalties
            trace.append(f"{verification_penalties} VERIFICATION: Document Intelligence overridden user claims.")
            causality_map.append({"fact": "Document Verification Failure", "impact": verification_penalties, "type": "negative", "rationale": "OCR layer determined user inputs were unsupported by actual document evidence."})

        # Witness Support Penalty
        witness_status = str(case_data.get("witness_available", "No")).lower()
        if witness_status == "no" or "no" in witness_status:
            witness_penalty = -5
            score += witness_penalty
            trace.append(f"{witness_penalty} EVIDENTIARY: Missing corroborative witness support.")
            causality_map.append({"fact": "No Witness Support", "impact": witness_penalty, "type": "negative", "rationale": "Without independent or corroborating witnesses, the case relies entirely on documentary evidence."})

        # BSA S.63(4) Strict Enforcement
        if case_data.get("communication_records") and not case_data.get("has_bsa_certificate"):
            bsa_penalty = -15
            score += bsa_penalty
            max_score_cap = min(max_score_cap, 75)
            trace.append(f"{bsa_penalty} EVIDENTIARY: Missing S.63(4) BSA Certificate for Digital Evidence.")
            causality_map.append({"fact": "Missing S.63(4) BSA Certificate", "impact": bsa_penalty, "type": "negative", "rationale": "Digital evidence (WhatsApp/Email) is completely inadmissible without certification."})

        # Final Score Cap
        final_score = max(0, min(max_score_cap, score))
        if not cheque or not notice:
            final_score = min(final_score, 30)
            trace.append("! SCORE CAPPED: Fatal statutory defect identified.")

        # --- V3 ENHANCEMENT: PREMIUM ANALYTICAL LAYERS ---
        reliability_matrix = cls.calculate_reliability_matrix(final_score, concepts, case_data)
        self_challenge = cls.calculate_self_challenge(final_score, case_data, concepts)
        similarity_metrics = cls.calculate_case_similarity(final_score, case_data, concepts)
        failure_point = cls.calculate_failure_point(final_score, case_data, concepts)
        senior_brief = cls.generate_senior_brief(final_score, case_data, concepts)
        question_bank = cls.generate_hostile_questions(case_data, concepts)
        remediation_sim = cls.calculate_remediation_sim(case_data)

        # Readiness Score
        cri_components = []
        if cheque: cri_components.append(25)
        if memo: cri_components.append(15)
        if notice: cri_components.append(15)
        if debt: cri_components.append(20)
        if case_data.get("is_authorized"): cri_components.append(15)
        cri_final = max(0, min(100, sum(cri_components)))

        # â”€â”€ EXPLICIT CAUSALITY: Score Delta & Penalty Index â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        potential_score = 99
        causality_delta = []
        for item in causality_map:
            val = item.get("penalty") or item.get("impact") or 0
            causality_delta.append({
                "factor": item["fact"],
                "impact": val,
                "reasoning": item["rationale"]
            })

        # â”€â”€ EXPLICIT CAUSALITY: Factor-Level Scoring â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        explicit_penalties = []
        for item in causality_map:
            explicit_penalties.append(f"{item.get('impact', 0)} because {item['fact']}")

        # â”€â”€ STATISTICAL CALIBRATION LAYER (Empirical Tuning) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Transform expert-weighted heuristics into probabilistically calibrated weights
        # based on synthetic verdict density maps.
        
        calibrated_score = final_score
        calibration_notes = []
        
        # 1. Judicial Sentiment Bias (Synthetic Calibration)
        # S.138 cases have a high conviction rate but high technical acquittal risk
        if final_score > 85:
            calibrated_score = min(98, final_score + 2) # Statutory presumption boost
            calibration_notes.append("Statutory Presumption u/s 139 provides a +2% calibration boost for High-Compliance cases.")
        elif final_score < 40:
            calibrated_score = max(5, final_score - 5) # Fatal technicality penalty
            calibration_notes.append("Technical Dismissal Risk: Heuristic penalty applied for non-maintainability indicators.")
            
        # 2. Confidence Interval Calculation
        # Variance increases as score approaches the 'grey zone' (40-60)
        confidence_variance = 5 if (final_score > 80 or final_score < 30) else 15
        
        # 3. Explicit Risk Propagation (Visible Causal Weights)
        explicit_risk_propagation = []
        for item in causality_map:
            weight_str = f"{item.get('impact', 0)} because {item['fact']}"
            explicit_risk_propagation.append(weight_str)

        return {
            "score": int(calibrated_score),
            "final_score": int(calibrated_score),
            "concepts": concepts, # Pass back the enriched concepts
            "raw_heuristic_score": int(final_score),
            "calibration_metadata": {
                "confidence_interval": [max(0, int(calibrated_score - confidence_variance)), min(100, int(calibrated_score + confidence_variance))],
                "judicial_sentiment": "POSITIVE" if final_score > 70 else ("NEGATIVE" if final_score < 40 else "NEUTRAL"),
                "calibration_notes": calibration_notes
            },
            "causality_map": causality_map,
            "potential_score": potential_score,
            "causality_delta": causality_delta,
            "evidence_reliability": cls.calculate_evidence_reliability(case_data),
            "reliability_matrix": reliability_matrix,
            "self_challenge": self_challenge,
            "case_similarity": similarity_metrics,
            "failure_point": failure_point,
            "senior_brief": senior_brief,
            "explicit_risk_propagation": explicit_risk_propagation,
            "uncertainty_intelligence": uncertainty_messages,
            "judicial_mode": judicial_mode,
            "compliance_pct": int(compliance_pct),
            "cri_score": int(cri_final),
            "remediation_roadmap": [x for x in [
                {"action": "Procure Complainant ITR (Source of Funds)", "delta": 18, "priority": "CRITICAL"} if not case_data.get("complainant_itr_available") else None,
                {"action": "Execute S.63 BSA Certificate for Digital Trails", "delta": 11, "priority": "HIGH"} if case_data.get("communication_records") and not case_data.get("has_bsa_certificate") else None,
                {"action": "Establish Ledger Authentication (S.139 Support)", "delta": 14, "priority": "HIGH"} if not case_data.get("debt_proven") else None,
                {"action": "Register Loan Agreement (Sec 17 Registration Act)", "delta": 9, "priority": "MEDIUM"} if amount > 100000 and not case_data.get("agreement_registered") else None,
                {"action": "Obtain Certified Copy of Return Memo", "delta": 22, "priority": "CRITICAL"} if not case_data.get("dishonour_memo") else None,
            ] if x is not None],
            "top_penalties": sorted(causality_delta, key=lambda x: x["impact"])[:3],
            "breakdown": {
                "procedural": int(max(0, min(100, (sum([1 for p in [cheque, memo, notice] if p])/3.0)*100))),
                "evidentiary": int(max(0, min(100, score))),
                "strategic": int(max(0, min(100, final_score))),
                "readiness": int(cri_final)
            },
            "reasoning_trace": trace,
            "score_breakdown": trace,
            "discretionary_caveats": [
                "JUDICIAL DISCRETION CAVEAT: Magistrates may exercise discretion if bad faith by the accused is evident."
            ],
            "economics": {
                "immediate_settlement": f"â‚¹{int(amount * 0.85):,}",
                "trial_target_3yr": f"â‚¹{int(amount * 1.5):,}",
                "cost_of_delay_per_month": f"â‚¹{int(amount * 0.015):,}",
                "settlement_posture": "AGGRESSIVE" if final_score > 75 else "CONCILIATORY"
            pattern = "Acquittal-Risk (Financial Capacity)"
            match_pct = 81
        elif score < 60:
            pattern = "Procedural Delay (Service/Limitation)"
            match_pct = 65
        else:
            pattern = "Standard Conviction (High Compliance)"
            match_pct = 74

        return {
            "pattern_matched": pattern,
            "similarity_index": f"{match_pct}%",
            "historical_outcome_correlation": "High" if match_pct > 70 else "Moderate"
        }

    @classmethod
    def calculate_failure_point(cls, score: int, case_data: Dict, concepts: List[Dict]) -> str:
        """USER REQUEST 3: CASE WILL BREAK HERE (Enhanced)"""
        # Highest priority failures first
        if not case_data.get("dishonour_memo"): return "Most probable failure point: Cognizance rejection due to missing bank return memo."
        if not case_data.get("notice_sent"): return "Most probable failure point: S.138 maintainability bar at summon stage (No Demand Notice)."
        
        notice_status = str(case_data.get("notice_delivery_status", "")).lower()
        if "not found" in notice_status: return "Most probable failure point: S.138 dismissed at pre-summoning stage due to Invalid Notice Service."
        
        is_cash = not case_data.get("loan_via_bank", True)
        no_itr = not case_data.get("complainant_itr_available", False)
        amount = float(case_data.get("cheque_amount", 0))
        if is_cash and no_itr and amount > 500000:
            return "Most probable failure point: Cross-examination collapse. Defence will trigger Basalingappa 'Financial Capacity' trap due to cash loan >₹5L without ITR."
            
        if "handwriting_different" in case_data and case_data.get("handwriting_different"):
            return "Most probable failure point: Trial delayed 18-24 months by Defence applying for Forensic Science Lab (FSL) ink analysis under S.45 Evidence Act."
            
        if score < 50: return "Most probable failure point: Cross-examination on 'Security Cheque' vs 'Legally Enforceable Liability'."
        return "Most probable failure point: Post-conviction appellate challenge on statutory interpretation."

    @classmethod
    def generate_senior_brief(cls, score: int, case_data: Dict, concepts: List[Dict]) -> Dict:
        """USER REQUEST 4: 1-PAGE SENIOR ADVOCATE BRIEF"""
        return {
            "verdict": "STRONG PROSECUTION" if score > 75 else ("VIABLE WITH RISK" if score > 50 else "DEFECTIVE/HIGH RISK"),
            "biggest_risk": "Financial capacity (Basalingappa)" if score < 60 else "Cross-exam credibility",
            "strongest_defence": "Debt denied / Friendly loan theory" if score > 50 else "Statutory non-compliance",
            "best_strategy": "Aggressive prosecution with S.139 reliance" if score > 70 else "Evidence remediation before filing",
            "predicted_posture": "Adversarial & Confident" if score > 70 else "Defensive/Settlement-oriented",
            "top_actions": [
                "Secure ITR proof",
                "Verify notice tracking",
                "Draft S.143A application"
            ]
        }

    @classmethod
    def generate_hostile_questions(cls, case_data: Dict, concepts: List[Dict]) -> List[str]:
        """Dynamically generates hostile questions based on case vulnerabilities."""
        concept_names = {c["concept"] for c in concepts}
        questions = []
        
        # 1. Financial Capacity (Basalingappa)
        amount = case_data.get("amount") or case_data.get("cheque_amount") or 0
        is_cash = str(case_data.get("loan_via_bank", "Yes")).lower() != "yes"
        if "unaccounted_cash_loans" in concept_names or not case_data.get("complainant_itr_available"):
            if float(amount) > 500000 and is_cash:
                questions.append(f"Given that lending ₹{amount} in cash violates Section 269SS of the Income Tax Act, how can you claim this is a legally enforceable debt?")
                questions.append("Since you have not produced an Income Tax Return or audited balance sheet, isn't it true you did not have the financial capacity to advance such a massive sum?")
            else:
                questions.append("Can you produce documentary evidence (bank statement, ITR, or ledger) proving your source of funds for this alleged cash transaction?")
                questions.append("Why is this alleged loan amount not reflected in your Income Tax Returns for the relevant year?")
            
        # 2. Security Cheque Defence
        if "security_cheque" in concept_names:
            questions.append("Isn't it true that this cheque was handed over as a blank security instrument at the start of the transaction?")
            questions.append("Why did you fill in the date and amount on this cheque without the accused's specific consent?")
            
        # 3. Debt Proof
        if "no_debt_proof" in concept_names:
            questions.append("Where is the written agreement or ledger entry that proves this alleged debt actually existed?")
            questions.append("If this was a business transaction, why was no invoice or receipt ever generated?")
            
        # 4. Signature/Handwriting
        if "signature_dispute" in concept_names or case_data.get("handwriting_different"):
            questions.append("How do you explain the visible variation in ink and handwriting between the signature and the rest of the cheque?")
            
        # 5. Generic but high-impact fallbacks if list is short
        if len(questions) < 5:
            questions.append("Why did you wait until the very end of the statutory notice period to initiate these proceedings?")
            questions.append("Can you produce the original bank tracking report for the legal notice you claim was served?")
            
        # Deduplicate and limit
        return list(dict.fromkeys(questions))[:10]

    @classmethod
    def calculate_remediation_sim(cls, case_data: Dict) -> List[Dict]:
        """USER REQUEST 6: IF THIS FIXED -> RESULT CHANGES"""
        sims = []
        if not case_data.get("complainant_itr_available"):
            sims.append({"gap": "Missing ITR / Source of Funds", "impact": "+18%", "type": "Evidentiary"})
        if not case_data.get("agreement_registered"):
            sims.append({"gap": "Unregistered Loan Agreement", "impact": "+12%", "type": "Legal"})
        if not case_data.get("dishonour_memo"):
            sims.append({"gap": "Original Return Memo missing", "impact": "+45%", "type": "Procedural"})
        if not case_data.get("has_bsa_certificate"):
            sims.append({"gap": "Missing S.63 BSA for WhatsApp", "impact": "+15%", "type": "Admissibility"})
        
        return sims[:3]

