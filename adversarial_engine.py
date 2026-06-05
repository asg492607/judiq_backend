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
            "name": "Financial Capacity Challenge (Basalingappa Trap)",
            "severity": "HIGH",
            "why_applied": "High-value cash transaction detected without supporting tax/ledger documentation.",
            "risk": "Adverse inference drawn under Basalingappa ruling; presumption of debt collapses if source of funds is not proven.",
            "evidence_needed": "Income Tax Returns, Bank Account ledgers, or audited balance sheets correlating to the loan date.",
            "precedent": "Basalingappa vs. Mudibasappa (2019) 5 SCC 418",
            "chain": [
                "1. Defence challenges Complainant's 'source of funds' under cross-examination.",
                "2. Highlights absence of ITR declarations or corresponding bank withdrawals.",
                "3. Shifts burden to Complainant to conclusively prove financial standing.",
                "4. Presumption under S.139 is rebutted upon standard of 'preponderance of probabilities'."
            ],
            "probability_collapse": 0.75,
            "rebuttal_tree": {
                "defence_evidence": "Cross-examination extracting admission of undocumented cash flow.",
                "complainant_counter": "Produce pre-dated bank statements showing cash withdrawal, or independent witnesses confirming the handover.",
                "burden_shift_effect": "Immediate shift. If Complainant fails to produce ITR/ledgers, acquittal is highly probable.",
                "magistrate_view": "Highly skeptical of high-value cash transactions violating S.269SS of Income Tax Act.",
                "conviction_impact": -35
            }
        },
        "material_alteration": {
            "name": "Material Alteration (S.87) & Forensic Trap",
            "severity": "FATAL",
            "why_applied": "Visible alteration in date/amount or signature dispute rendering instrument suspect.",
            "risk": "Cheque rendered void under S.87 NI Act. High likelihood of Trial Delay due to Forensic (FSL) evaluation.",
            "evidence_needed": "Witness to the execution of the cheque or reliance on S.20 NI Act for inchoate instruments.",
            "precedent": "Bir Singh vs. Mukesh Kumar (2019) 4 SCC 197 & T. Vasanthakumar vs. Vijayakumari",
            "chain": [
                "1. Defence alleges cheque was blank or materially altered without consent.",
                "2. Points to distinct ink/handwriting in date, payee, or amount fields.",
                "3. Files application u/s 45 Indian Evidence Act for FSL handwriting expert.",
                "4. Trial is stayed/delayed by 18-24 months awaiting forensic report."
            ],
            "probability_collapse": 0.85,
            "rebuttal_tree": {
                "defence_evidence": "FSL report showing distinct ink age/stroke velocity, or apparent overwriting.",
                "complainant_counter": "Cite S.20 NI Act: Handing over a signed blank cheque grants implied authority to fill it.",
                "burden_shift_effect": "Trial heavily delayed. If FSL proves forgery of signature, case collapses instantly.",
                "magistrate_view": "Will allow FSL if alteration is blatant; otherwise may rely on presumption.",
                "conviction_impact": -45
            }
        },
        "vicarious_liability": {
            "name": "Vicarious Liability Defect (S.141)",
            "severity": "FATAL",
            "why_applied": "Corporate entity involved but mandatory S.141 averments are missing, or a director resigned prior to the cheque date.",
            "risk": "Complaint may be quashed against individual directors under S.482 CrPC if their active role isn't pleaded or if they validly resigned.",
            "evidence_needed": "MCA Master Data (DIR-12), Board Resolution, or proof of signature.",
            "precedent": "Aneeta Hada vs. Godfather Travels & Tours / Pooja Ravinder Devidasani",
            "chain": [
                "1. Defence argues Company was not impleaded or directors had no active role.",
                "2. Produces certified MCA DIR-12 showing resignation before the cheque was issued.",
                "3. Seeks immediate quashing under S.482 CrPC for lack of specific averments."
            ],
            "probability_collapse": 0.90,
            "rebuttal_tree": {
                "defence_evidence": "Resignation letters & certified MCA Master Data (Form DIR-12).",
                "complainant_counter": "Show 'Director' signature on the cheque, active email chains, or prove DIR-12 was filed retrospectively.",
                "burden_shift_effect": "Fatal defect. Unless Complainant proves active management despite resignation, S.138 fails against that director.",
                "magistrate_view": "Strict adherence to statutory mandatory impleadment and MCA records.",
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
        itr_missing = not case_data.get("complainant_itr_available")
        is_cash_loan = not case_data.get("loan_via_bank", True)
        capacity_threshold = 50000 if is_cash_loan else 200000
        
        if amount >= capacity_threshold and itr_missing:
            node = cls._build_node(cls.VULNERABILITY_MODELS["financial_capacity"], "Financial Capacity Challenge")
            # Dynamic Escalation for Cash traps
            if is_cash_loan and amount > 500000:
                node["severity"] = "FATAL"
                node["collapse_risk"] = "90%"
                node["risk_explained"] = "Massive cash transaction without ITR triggers severe Basalingappa adverse inference and S.269SS IT Act violation."
                node["rebuttal_tree"]["conviction_impact"] = -60
            analysis_nodes.append(node)

        # 3. Material Alteration & Signature Logic
        signature_mismatch = case_data.get("signature_mismatch", False)
        handwriting_different = case_data.get("handwriting_different", False)
        has_alteration_concept = "material_alteration" in concept_names or "signature_dispute" in concept_names
        
        if handwriting_different or signature_mismatch or has_alteration_concept:
            node = cls._build_node(cls.VULNERABILITY_MODELS["material_alteration"], "S.87 Material Alteration / FSL Risk")
            if signature_mismatch:
                node["severity"] = "FATAL"
                node["risk_explained"] = "Signature forgery allegation is fatal if proven by FSL."
            elif handwriting_different and not signature_mismatch:
                node["severity"] = "MODERATE"
                node["collapse_risk"] = "45%"
                node["risk_explained"] = "Different handwriting alone doesn't void cheque (S.20 NI Act implied authority), but invites FSL delay tactics."
                node["rebuttal_tree"]["conviction_impact"] = -25
            analysis_nodes.append(node)

        # 4. Vicarious Liability Logic (S.141)
        # S.141 requires strict averments like "in charge of and responsible for the conduct of the business"
        has_directors = case_data.get("directors_named", False)
        has_s141_averments = case_data.get("s141_averments_present", False)
        resignation_date_str = case_data.get("director_resignation_date")
        cheque_date_str = case_data.get("cheque_date")
        director_signed = case_data.get("director_signed_cheque", False)
        
        if is_company:
            if not has_directors or not has_s141_averments:
                analysis_nodes.append(cls._build_node(cls.VULNERABILITY_MODELS["vicarious_liability"], "S.141 Procedural Defect (Missing Averments)"))
                
            if resignation_date_str and cheque_date_str:
                from datetime import datetime
                def parse_date(d):
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                        try: return datetime.strptime(str(d).strip(), fmt)
                        except: pass
                    return None
                
                r_date = parse_date(resignation_date_str)
                c_date = parse_date(cheque_date_str)
                
                if r_date and c_date and r_date < c_date:
                    node = cls._build_node(cls.VULNERABILITY_MODELS["vicarious_liability"], "S.141 Resignation Trap (MCA Data)")
                    node["severity"] = "FATAL"
                    node["collapse_risk"] = "95%"
                    
                    if director_signed:
                        node["adversarial_vector"] = "S.420 Fraud Conversion (Resigned but Signed)"
                        node["risk_explained"] = "Director resigned before cheque date but still signed the cheque. S.138 might fail, but S.420 IPC (Cheating) is highly viable."
                        node["rebuttal_tree"]["complainant_counter"] = "Amend pleadings to include S.420 IPC and invoke criminal fraud jurisdiction."
                        node["rebuttal_tree"]["conviction_impact"] = -20 # Fraud charge keeps pressure high
                    else:
                        node["risk_explained"] = "Director resigned prior to cheque issuance. High risk of S.482 CrPC quashing for this specific director."
                    
                    analysis_nodes.append(node)

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
        notice_received_raw = str(case_data.get("notice_received", "")).lower()
        reply_received_raw = str(case_data.get("reply_received", "")).lower()
        
        notice_unserved = "not_served" in concept_names or "returned unserved" in notice_received_raw
        admitted_reply = "yes" in reply_received_raw or case_data.get("reply_received") == True
        
        if notice_unserved and admitted_reply:
            contradictions.append({
                "severity": "Material credibility risk",
                "issue": "Notice Service Perjury Risk",
                "detail": "Claiming the demand notice was 'returned unserved' while simultaneously admitting to receiving a 'reply notice' creates a logical impossibility. This exposes the Complainant to perjury risks during cross-examination.",
                "remediation": "Amend pleadings to acknowledge the reply notice and its contents, or clarify if the reply was to a different notice.",
                "penalty": -55
            })
            
        # 2. Debt/Payment Contradiction (Dashrathbhai Trap)
        partial_payment_amount = float(case_data.get("partial_payment_amount") or 0)
        cheque_amount = float(case_data.get("cheque_amount") or 0)
        
        # safely parse notice amount
        notice_amount_raw = case_data.get("notice_content")
        try:
            notice_amount = float(notice_amount_raw) if notice_amount_raw else cheque_amount
        except ValueError:
            notice_amount = cheque_amount
            
        is_partial_payment = str(case_data.get("partial_payment", "")).lower().startswith("yes") or case_data.get("partial_payment_admitted")
        
        if is_partial_payment and partial_payment_amount > 0:
            if notice_amount >= cheque_amount:
                contradictions.append({
                    "severity": "Material credibility risk",
                    "issue": "Dashrathbhai Trap (Invalid Notice Amount)",
                    "detail": f"Partial payment of ₹{partial_payment_amount} was received, but the notice demanded the full cheque amount (₹{notice_amount}). Per Dashrathbhai Trikambhai Patel ruling, the S.138 complaint is NOT maintainable.",
                    "remediation": "This is a fatal defect. The complaint must be withdrawn and filed as a civil recovery suit.",
                    "penalty": -85 # Almost complete collapse
                })
        elif "no_debt_proof" in concept_names and case_data.get("partial_payment_admitted"):
            contradictions.append({
                "severity": "Strategic contradiction",
                "issue": "Liability/Payment Conflict",
                "detail": "Admitting to receiving partial payment while failing to prove the remaining debt balance.",
                "remediation": "Amend pleadings to show the cheque was issued explicitly for the remaining balance.",
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

        # 5. Impossible Timeline (Cheque before Loan)
        cheque_dt = case_data.get("cheque_date")
        loan_dt = case_data.get("transaction_date") or case_data.get("loan_date")
        if cheque_dt and loan_dt:
            from utils import parse_date
            c_date = parse_date(cheque_dt)
            l_date = parse_date(loan_dt)
            if c_date and l_date and c_date < l_date:
                contradictions.append({
                    "severity": "Material credibility risk",
                    "issue": "Impossible Timeline (Cheque Predates Loan)",
                    "detail": f"The cheque is dated {cheque_dt}, but the loan/transaction occurred on {loan_dt}. A cheque cannot be issued in discharge of a debt that did not yet exist.",
                    "remediation": "This is a fatal defect. DO NOT FILE.",
                    "penalty": -95
                })

        # 6. S.141 Resignation Trap
        resignation_date = case_data.get("director_resignation_date")
        if case_data.get("director_signed_cheque") and resignation_date and cheque_dt:
            from utils import parse_date
            r_date = parse_date(resignation_date)
            c_date = parse_date(cheque_dt)
            if r_date and c_date and c_date > r_date:
                contradictions.append({
                    "severity": "Material credibility risk",
                    "issue": "S.141 Resignation Trap (Director Signed After Resigning)",
                    "detail": "The director signed the cheque after their official resignation date. They cannot bind the company, and charging them under S.141 is malicious prosecution.",
                    "remediation": "Fatal defect. DO NOT FILE.",
                    "penalty": -90
                })

        # 7. Multiple Conflicting Notices
        if str(case_data.get("multiple_notices_sent", "")).lower() == "yes":
            contradictions.append({
                "severity": "Material credibility risk",
                "issue": "Multiple Conflicting Statutory Notices",
                "detail": "Sending a second demand notice after the cause of action has crystallized on the first notice voids the S.138 proceedings per Sadanandan Bhadran v. Madhavan Sunil Kumar.",
                "remediation": "Fatal defect. Ensure the complaint is strictly based on the first valid notice.",
                "penalty": -85
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
