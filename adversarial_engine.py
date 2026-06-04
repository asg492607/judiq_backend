from typing import Dict, List, Any
class AdversarialEngine:
    """
    Institutional-Grade Adversarial Engine — Simulates courtroom dynamics, tactical rebuttal chains,
    and stage-wise procedural survivability mapping.
    """

    # Stage-wise Survivability Baseline (Procedural roadmap)
    PROCEDURAL_STAGES = [
        {"id": "summoning", "name": "Summoning Stage", "baseline_prob": 0.95},
        {"id": "framing", "name": "Notice/Framing of Charge", "baseline_prob": 0.85},
        {"id": "evidence", "name": "Complainant Evidence", "baseline_prob": 0.70},
        {"id": "cross_exam", "name": "Cross-Examination", "baseline_prob": 0.60},
        {"id": "final", "name": "Final Arguments", "baseline_prob": 0.55},
        {"id": "appeal", "name": "Appeal Sustainability", "baseline_prob": 0.45}
    ]

    # Vulnerability Models (Formerly Attack Trees) - Structured for Explainability
    VULNERABILITY_MODELS = {
        "security_cheque": {
            "name": "Security Cheque Rebuttal",
            "severity": "CRITICAL",
            "why_applied": "Debt is either denied or documentation is missing/verbal.",
            "risk": "Accused may rebut the S.139 presumption by showing the instrument was not for a 'crystallized' debt.",
            "evidence_needed": "Invoices, ledger entries, or delivery challans dated PRIOR to the cheque date.",
            "precedent": "Sampelly Satyanarayana Rao vs. Indian Renewable Energy Development Agency Ltd.",
            "chain": [
                "1. Defence admits signature but denies 'existing liability'.",
                "2. Argues cheque was given as 'blank security' for a future transaction.",
                "3. Shifting burden: Complainant must now prove crystallization of debt."
            ],
            "probability_collapse": 0.55,
            "rebuttal_tree": {
                "defence_evidence": "Lack of invoices / Post-dated nature of instrument.",
                "complainant_counter": "Produce ledger entries showing 'crystallized debt' on cheque date.",
                "burden_shift_effect": "Immediate shift if no documentary proof of debt exists.",
                "magistrate_view": "Likely to stay proceedings for further evidence.",
                "conviction_impact": -25
            }
        },
        "financial_capacity": {
            "name": "Financial Capacity Challenge",
            "severity": "HIGH",
            "why_applied": "High-value transaction (>₹2L) detected without ITR or source proof.",
            "risk": "Accused may challenge the Complainant's 'source of funds', leading to adverse inference under Basalingappa.",
            "evidence_needed": "Income Tax Returns, Bank Statements, or proof of liquid savings.",
            "precedent": "Basalingappa vs. Mudibasappa (2019) 5 SCC 418",
            "chain": [
                "1. Defence challenges Complainant's 'source of funds'.",
                "2. Questions how such a large amount was available in cash.",
                "3. Adverse inference drawn due to non-production of ITR."
            ],
            "probability_collapse": 0.68,
            "rebuttal_tree": {
                "defence_evidence": "ITR history / Bank balance of Complainant.",
                "complainant_counter": "Argue 'friendly loan' from savings; cite 'Rangappa v. Mohan'.",
                "burden_shift_effect": "Shifts to Complainant to prove financial standing.",
                "magistrate_view": "Highly skeptical of high-value cash transactions without ITR.",
                "conviction_impact": -35
            }
        },
        "material_alteration": {
            "name": "Material Alteration (S.87)",
            "severity": "FATAL",
            "why_applied": "Different ink or handwriting patterns detected in cheque metadata.",
            "risk": "Instrument may be rendered void under Section 87 of NI Act if 'consent' for completion is not proven.",
            "evidence_needed": "Authorized signatory declaration or witness to cheque completion.",
            "precedent": "Bir Singh vs. Mukesh Kumar (2019) 4 SCC 197",
            "chain": [
                "1. Defence alleges cheque was 'completed' by Complainant without consent.",
                "2. Points to different ink/handwriting in date/amount fields.",
                "3. Requests Forensic (FSL) examination of handwriting."
            ],
            "probability_collapse": 0.82,
            "rebuttal_tree": {
                "defence_evidence": "Visual inspection of ink/handwriting variation.",
                "complainant_counter": "Cite 'Bir Singh v. Mukesh Kumar' - authority to fill blank cheque.",
                "burden_shift_effect": "High risk of trial stay for FSL report.",
                "magistrate_view": "Extreme caution if alteration is visible to naked eye.",
                "conviction_impact": -45
            }
        },
        "vicarious_liability": {
            "name": "Vicarious Liability Defect (S.141)",
            "severity": "FATAL",
            "why_applied": "Corporate entity involved but mandatory S.141 averments are missing.",
            "risk": "Complaint may be quashed against individual directors if the Company is not impleaded or roles aren't specified.",
            "evidence_needed": "MCA Master Data, Board Resolution, or Signatory Proof.",
            "precedent": "Aneeta Hada vs. Godfather Travels & Tours (P) Ltd.",
            "chain": [
                "1. Defence argues Company was not impleaded or directors had no role.",
                "2. Seeks quashing under S.482 CrPC for lack of specific averments.",
                "3. Argues 'Director' is not 'in charge of and responsible to' the company."
            ],
            "probability_collapse": 0.90,
            "rebuttal_tree": {
                "defence_evidence": "Resignation letters / MCA records.",
                "complainant_counter": "Show 'Director' signature on the cheque or active role in debt.",
                "burden_shift_effect": "Fatal defect if Company is not a party.",
                "magistrate_view": "Strict adherence to statutory mandatory impleadment.",
                "conviction_impact": -50
            }
        }
    }

    @classmethod
    def calculate_stage_survivability(cls, score: int, adversarial_risk: float) -> List[Dict]:
        """Calculates quantified probability of surviving each stage of litigation."""
        roadmap = []
        current_risk_multiplier = 1.0 - (adversarial_risk * 0.7) # Aggressive risk weighting
        
        for stage in cls.PROCEDURAL_STAGES:
            prob = stage["baseline_prob"] * (score / 100.0) * current_risk_multiplier
            
            if stage["id"] == "cross_exam":
                prob *= 0.75 # Heaviest collapse point
                
            roadmap.append({
                "stage": stage["name"],
                "probability": f"{int(max(2, min(98, prob * 100)))}%",
                "status": "Vulnerable" if prob < 0.45 else ("Stable" if prob > 0.7 else "Caution"),
                "risk_factor": "Cross-exam fumble" if stage["id"] == "cross_exam" else "Procedural bar"
            })
            current_risk_multiplier *= 0.92
            
        return roadmap

    @classmethod
    def simulate_strategic_stress_test(cls, case_data: Dict, concepts: List[Dict]) -> List[Dict]:
        """Deep modeling of potential defence theories and rebuttal chains."""
        analysis_nodes = []
        concept_names = {c["concept"] for c in concepts}
        amount = float(case_data.get("amount") or 0)
        accused_name = str(case_data.get("accused_name", "")).lower()
        is_company = any(x in accused_name for x in ["pvt", "ltd", "corp", "inc", "co.", "company"])

        # 1. Security Cheque Logic
        if not case_data.get("debt_proven") or "security_cheque" in concept_names:
            analysis_nodes.append(cls._build_node(cls.VULNERABILITY_MODELS["security_cheque"], "Security Cheque Defence Theory"))

        # 2. Financial Capacity Logic
        if amount > 150000 and not case_data.get("complainant_itr_available"):
            analysis_nodes.append(cls._build_node(cls.VULNERABILITY_MODELS["financial_capacity"], "Financial Capacity Challenge"))

        # 3. Material Alteration Logic
        if case_data.get("handwriting_different") or "material_alteration" in concept_names:
            analysis_nodes.append(cls._build_node(cls.VULNERABILITY_MODELS["material_alteration"], "S.87 Material Alteration Risk"))

        # 4. Vicarious Liability Logic
        if is_company and not case_data.get("directors_named"):
            analysis_nodes.append(cls._build_node(cls.VULNERABILITY_MODELS["vicarious_liability"], "S.141 Procedural Defect"))

        return analysis_nodes

    @classmethod
    def _build_node(cls, tree: Dict, vector_name: str) -> Dict:
        return {
            "adversarial_vector": vector_name,
            "risk": vector_name, # Fallback for script.js
            "severity": tree.get("severity", "HIGH"),
            "description": tree.get("risk", ""), # map 'risk' field from model to 'description'
            "strategic_chain": tree["chain"],
            "rebuttal_tree": tree["rebuttal_tree"],
            "why_applied": tree.get("why_applied", ""),
            "risk_explained": tree.get("risk", ""),
            "evidence_needed": tree.get("evidence_needed", ""),
            "precedent_anchor": tree.get("precedent", ""),
            "survival_probability": f"{int((1.0 - tree['probability_collapse']) * 100)}%",
            "collapse_risk": f"{int(tree['probability_collapse'] * 100)}%",
            "courtroom_implications": {
                "defence_position": f"The defence will likely argue that the {vector_name.lower()} invalidates the claim.",
                "witness_scrutiny_level": "HIGH" if tree["probability_collapse"] > 0.6 else "MEDIUM",
                "narrative_conflict": "Defence will highlight inconsistencies between the demand notice and oral testimony."
            }
        }

    @classmethod
    def detect_contradictions(cls, case_data: Dict, concepts: List[Dict]) -> List[Dict]:
        """
        Contradiction Engine v2: Detects mutually exclusive facts with severity propagation.
        Severities: 
        - Minor inconsistency: Subtle variations in narrative.
        - Strategic contradiction: Tactical opening for the defence.
        - Material credibility risk: Significant threat to the cause of action.
        """
        contradictions = []
        concept_names = [c["concept"] for c in concepts]
        
        # 1. Notice/Service Contradiction
        if "notice_not_served" in concept_names and case_data.get("reply_received"):
            contradictions.append({
                "severity": "Material credibility risk",
                "issue": "Notice Service Inconsistency",
                "detail": "Claiming non-service while admitting a reply notice creates a logical impossibility that may lead to summary dismissal.",
                "remediation": "Amend pleadings to acknowledge the reply notice and its contents.",
                "penalty": -45
            })
            
        # 2. Debt/Payment Contradiction
        if "no_debt_proof" in concept_names and case_data.get("partial_payment_admitted"):
            contradictions.append({
                "severity": "Material credibility risk",
                "issue": "Liability/Payment Conflict",
                "detail": "Admitting to receiving partial payment while failing to prove the remaining debt balance is fatal. If the cheque amount is larger than the actual due amount post-payment, S.138 is not maintainable (Dashrathbhai Trikambhai Patel ruling).",
                "remediation": "Amend pleadings to show the cheque was issued explicitly for the remaining balance, or withdraw and file a civil recovery suit.",
                "penalty": -40
            })

        # 3. Director/Role Contradiction
        if "s141_defect" in concept_names and case_data.get("director_signed_cheque"):
            contradictions.append({
                "severity": "Material credibility risk",
                "issue": "Vicarious Liability Conflict",
                "detail": "Denying a director's role when they are the signatory is a fatal procedural error u/s 141.",
                "remediation": "Re-align S.141 averments to focus on the signatory director's active management role.",
                "penalty": -50
            })

        # 4. Handwriting/Blank Cheque Contradiction
        if case_data.get("handwriting_different") and case_data.get("cheque_issued_at_office"):
             contradictions.append({
                "severity": "Minor inconsistency",
                "issue": "Execution Context Variation",
                "detail": "Varying handwriting on a cheque issued in a professional office setting suggests a security instrument rather than a completed debt payment.",
                "remediation": "Clarify that the instrument was completed by an authorized representative under instructions.",
                "penalty": -10
            })

        # 4. Semantic NLP-based Combinations (New)
        # Instead of strict hardcoding, dynamically detect semantic overlaps 
        # where two concepts have high conflict confidence.
        for i, c1 in enumerate(concepts):
            for j, c2 in enumerate(concepts):
                if i >= j: continue
                # Example semantic rule: if concept 1 implies validity and concept 2 implies invalidity
                # (This relies on NLP scoring from semantic_engine passing 'polarity' or 'conflict_weight')
                if c1.get("polarity", 1) * c2.get("polarity", 1) < 0 and c1.get("confidence", 0) > 0.7 and c2.get("confidence", 0) > 0.7:
                    contradictions.append({
                        "severity": "Strategic contradiction",
                        "issue": f"Semantic Conflict: {c1['concept']} vs {c2['concept']}",
                        "detail": f"NLP engine detected a high-confidence semantic conflict between {c1['concept']} and {c2['concept']}.",
                        "remediation": "Clarify the narrative to reconcile these opposing concepts.",
                        "penalty": -20
                    })

        # --- V3 ENHANCEMENT: CREDIBILITY COLLAPSE SIMULATION ---
        for c in contradictions:
            c["collapse_simulation"] = cls.simulate_credibility_collapse(c)

        return contradictions

    @classmethod
    def simulate_credibility_collapse(cls, contradiction: Dict) -> Dict:
        """
        Simulates how the defense exploits a specific contradiction in court.
        """
        severity = contradiction["severity"]
        issue = contradiction["issue"]
        
        attack_patterns = {
            "Material credibility risk": {
                "defense_exploit": "Argue fundamental falsity of the complainant's narrative. Seek immediate acquittal.",
                "cross_exam_impact": "Complainant may be unable to reconcile contradictory statements under pressure.",
                "survivability_impact": -0.45
            },
            "Strategic contradiction": {
                "defense_exploit": "Introduce reasonable doubt regarding the specific transaction. Target S.139 presumption.",
                "cross_exam_impact": "Forcing admissions that erode the statutory presumption of liability.",
                "survivability_impact": -0.18
            },
            "Minor inconsistency": {
                "defense_exploit": "Suggest lack of professional record-keeping to marginalize the complainant's reliability.",
                "cross_exam_impact": "Expose memory gaps or procedural lapses during cross-examination.",
                "survivability_impact": -0.05
            }
        }
        
        pattern = attack_patterns.get(severity, attack_patterns["Minor inconsistency"])
        return {
            "adversarial_vector": f"Exploiting {issue}",
            "defence_strategy": pattern["defense_exploit"],
            "cross_exam_prediction": pattern["cross_exam_impact"],
            "quantitative_impact": f"{int(pattern['survivability_impact'] * 100)}%"
        }

    @classmethod
    def run_strategic_audit(cls, case_data: Dict, concepts: List[Dict]) -> List[Dict]:
        """
        Aggressively audits the Complainant's case for vulnerabilities.
        """
        vulnerabilities = []
        contradictions = cls.detect_contradictions(case_data, concepts)
        
        for c in contradictions:
            vulnerabilities.append({
                "target": c["issue"],
                "risk": f"Adversarial exploit of {c['severity'].lower()}",
                "opposing_argument": f"The complainant's narrative is inconsistent regarding {c['issue']}, suggesting a lack of bona fide debt.",
                "risk_level": "CRITICAL" if "Material" in c["severity"] else "HIGH"
            })
            
        # Audit assumptions
        if not case_data.get("loan_via_bank") and float(case_data.get("amount") or 0) > 50000:
            vulnerabilities.append({
                "target": "Loan Transaction Verification",
                "risk": "Violation of S.269SS Income Tax Act",
                "opposing_argument": "This cash transaction violates anti-money laundering statutes and lacks banking verification.",
                "risk_level": "CRITICAL"
            })
            
        if not case_data.get("itr_available"):
            vulnerabilities.append({
                "target": "Financial Capacity Verification",
                "risk": "Basalingappa Inference Risk",
                "opposing_argument": "The complainant has failed to document the financial capacity to advance the alleged amount.",
                "risk_level": "HIGH"
            })
            
        return vulnerabilities

    @classmethod
    def simulate_witness_pressure(cls, case_data: Dict, adversarial_risk: float) -> Dict:
        """
        Simulates psychological pressure on the witness during cross-examination.
        Addresses USER REQUEST 4.
        """
        risk_level = "CRITICAL" if adversarial_risk > 0.6 else ("HIGH" if adversarial_risk > 0.4 else "MODERATE")
        
        stability = 100 - (adversarial_risk * 100)
        
        return {
            "witness_stability_index": f"{int(stability)}%",
            "pressure_points": [
                "Source of funds interrogation (High stress)",
                "Chronology verification (Consistency risk)",
                "Notice demand vs. Actual debt reconciliation"
            ],
            "breakdown_risk": "VERY HIGH" if stability < 40 else ("HIGH" if stability < 60 else "LOW"),
            "fatigue_simulation": "Rapid degradation expected after 2 hours of cross-exam."
        }

    @classmethod
    def map_evidence_dependencies(cls, case_data: Dict) -> List[Dict]:
        """
        Evidence Dependency Mapping: Visualizes how one evidentiary lack affects others.
        Example: No ITR -> Financial capacity weak -> Basalingappa attack stronger -> Cross-exam survivability reduced
        """
        dependencies = []
        amount = float(case_data.get("amount") or 0)
        
        if not case_data.get("complainant_itr_available") and amount > 200000:
            dependencies.append({
                "trigger": "No ITR",
                "chain": [
                    "Financial capacity weak",
                    "Basalingappa attack stronger",
                    "Cross-exam survivability reduced"
                ],
                "impact_score": -35
            })

        if not case_data.get("debt_proven"):
            dependencies.append({
                "trigger": "No Ledger/Contract",
                "chain": [
                    "Presumption u/s 139 weakened",
                    "Security Cheque defense gains traction",
                    "Burden shifts to Complainant prematurely"
                ],
                "impact_score": -25
            })

        if case_data.get("handwriting_different"):
            dependencies.append({
                "trigger": "Handwriting Variation",
                "chain": [
                    "S.87 Material Alteration risk",
                    "FSL Examination demand likely",
                    "Trial duration extends by 18-24 months"
                ],
                "impact_score": -20
            })

        return dependencies

    @classmethod
    def detect_timeline_anomalies(cls, case_data: Dict) -> List[Dict]:
        """
        Timeline Anomaly Detector: Detects suspicious or impossible chronologies.
        Addresses Point 7 (Timeline Anomaly Detector) of the cognitive maturity audit.
        """
        anomalies = []
        from datetime import datetime
        
        def to_date(d_str):
            if not d_str: return None
            if isinstance(d_str, datetime): return d_str
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try: return datetime.strptime(str(d_str).strip(), fmt)
                except: continue
            return None

        cheque_date = to_date(case_data.get("cheque_date"))
        dishonour_date = to_date(case_data.get("dishonour_date"))
        notice_date = to_date(case_data.get("notice_date"))
        filing_date = to_date(case_data.get("filing_date"))

        # 1. Notice before Dishonour
        if notice_date and dishonour_date and notice_date < dishonour_date:
            anomalies.append({
                "type": "IMPOSSIBLE_SEQUENCE",
                "text": "Notice date is before bank dishonour date. This is a jurisdictional fatal flaw.",
                "severity": "CRITICAL"
            })

        # 2. Filing before Notice period expiry
        if filing_date and notice_date:
            days_diff = (filing_date - notice_date).days
            if days_diff < 15:
                anomalies.append({
                    "type": "PREMATURE_CHRONOLOGY",
                    "text": f"Filing occurred only {days_diff} days after notice. S.138 requires 15 days cure period.",
                    "severity": "CRITICAL"
                })

        # 3. Post-dated Cheque Issue
        # (Assuming we have a 'loan_date')
        loan_date = to_date(case_data.get("loan_date"))
        if loan_date and cheque_date and cheque_date < loan_date:
            anomalies.append({
                "type": "SUSPICIOUS_CHRONOLOGY",
                "text": "Cheque date is prior to the alleged loan date. Causal story is inconsistent.",
                "severity": "HIGH"
            })

        return anomalies

    @classmethod
    def audit_case(cls, case_data: Dict, concepts: List[Dict]) -> Dict:
        """Central audit method for the orchestrator."""
        analysis_nodes = cls.simulate_strategic_stress_test(case_data, concepts)
        
        # Dynamic risk calculation based on active nodes
        base_risk = 0.15
        for node in analysis_nodes:
            # Extract probability from string "82%"
            try:
                dest_prob = float(node["collapse_risk"].strip('%')) / 100.0
                base_risk += (dest_prob * 0.3)
            except: base_risk += 0.1
            
        contradictions = cls.detect_contradictions(case_data, concepts)
            
        return {
            "risks_and_rebuttals": analysis_nodes,
            "contradictions": contradictions, 
            "adversarial_risk": min(0.95, base_risk)
        }

    @classmethod
    def calculate_adversarial_risk(cls, battle_nodes: List[Dict]) -> float:
        if not battle_nodes: return 0.1
        risk = 0.2
        for node in battle_nodes:
            risk += 0.15
        return min(0.9, risk)
