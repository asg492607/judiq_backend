from typing import Dict, List, Any

class CriminalAdversarialEngine:
    """
    Simulates courtroom dynamics, tactical rebuttal chains, and stage-wise 
    procedural survivability for general criminal law matters.
    """

    PROCEDURAL_STAGES = [
        {"id": "bail", "name": "Bail Hearing (S.437/439)", "baseline_prob": 0.60},
        {"id": "cognizance", "name": "Cognizance/Summoning", "baseline_prob": 0.85},
        {"id": "charge", "name": "Argument on Charge (Discharge)", "baseline_prob": 0.75},
        {"id": "chief", "name": "Prosecution Evidence (Chief)", "baseline_prob": 0.80},
        {"id": "cross", "name": "Cross-Examination of Witnesses", "baseline_prob": 0.45},
        {"id": "s313", "name": "Statement of Accused (S.313)", "baseline_prob": 0.90},
        {"id": "defense", "name": "Defense Evidence", "baseline_prob": 0.60},
        {"id": "final", "name": "Final Arguments", "baseline_prob": 0.50}
    ]

    VULNERABILITY_MODELS = {}

    @classmethod
    def load_knowledge_base(cls):
        """Loads the massive vulnerability ruleset from JSON."""
        if cls.VULNERABILITY_MODELS:
            return
        try:
            import json, os
            kb_path = os.path.join(os.path.dirname(__file__), 'criminal_knowledge_base.json')
            with open(kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls.VULNERABILITY_MODELS = data.get("vulnerability_models", {})
        except Exception as e:
            cls.VULNERABILITY_MODELS = {} # Failsafe

    @classmethod
    def calculate_stage_survivability(cls, severity_score: int, adversarial_risk: float) -> List[Dict]:
        """Calculates quantified probability of surviving each stage of the criminal trial."""
        roadmap = []
        current_risk_multiplier = 1.0 - (adversarial_risk * 0.5)
        
        for stage in cls.PROCEDURAL_STAGES:
            prob = stage["baseline_prob"] * (severity_score / 100.0) * current_risk_multiplier
            
            if stage["id"] == "cross":
                prob *= 0.65 # Cross-examination is the ultimate test in criminal trials
                
            roadmap.append({
                "stage": stage["name"],
                "probability": f"{int(max(5, min(95, prob * 100)))}%",
                "status": "Vulnerable" if prob < 0.40 else ("Stable" if prob > 0.65 else "Caution"),
                "risk_factor": "Cross-exam fumble" if stage["id"] == "cross" else "Procedural/Evidentiary bar"
            })
            current_risk_multiplier *= 0.95
            
        return roadmap

    @classmethod
    def detect_contradictions(cls, case_data: Dict, concepts: List[Dict]) -> List[Dict]:
        """Detects mutually exclusive facts or procedural lapses in criminal narratives."""
        contradictions = []
        concept_names = [c["concept"] for c in concepts]
        
        if "fir_delay" in concept_names and not case_data.get("delay_explanation"):
            contradictions.append({
                "severity": "Material credibility risk",
                "issue": "Unexplained FIR Delay",
                "detail": "Delay in lodging FIR without explanation opens the prosecution to charges of fabrication.",
                "remediation": "File a supplementary statement detailing reasons for delay (e.g., medical treatment, fear).",
                "penalty": -30
            })

        if case_data.get("electronic_evidence") and not case_data.get("s65b_certificate"):
            contradictions.append({
                "severity": "Fatal Procedural Defect",
                "issue": "Missing S.65B Certificate",
                "detail": "Relying on digital evidence without the mandatory certificate renders it inadmissible.",
                "remediation": "Procure and file the S.65B certificate immediately before the trial commences.",
                "penalty": -50
            })
            
        offense_type = str(case_data.get("offense_type", "")).upper()
        if offense_type == "420" and case_data.get("contract_exists") and case_data.get("partial_performance_done"):
            contradictions.append({
                "severity": "Strategic contradiction",
                "issue": "Civil Dispute Profile in S.420",
                "detail": "Admitting to partial performance of a contract negates the 'inception of fraud' required for S.420 IPC.",
                "remediation": "Argue that the partial performance was merely a smokescreen to induce further funds.",
                "penalty": -40
            })

        return contradictions

    @classmethod
    def simulate_strategic_stress_test(cls, case_data: Dict, concepts: List[Dict]) -> List[Dict]:
        """Deep modeling of potential defence theories from the JSON knowledge base."""
        cls.load_knowledge_base()
        analysis_nodes = []
        offense_type = str(case_data.get("offense_type", "")).upper()
        concept_names = [c["concept"] for c in concepts]

        def _build_node(model_key: str):
            tree = cls.VULNERABILITY_MODELS.get(model_key)
            if not tree: return None
            return {
                "adversarial_vector": tree["name"],
                "risk": tree["name"],
                "severity": tree.get("severity", "HIGH"),
                "description": tree.get("risk", ""),
                "strategic_chain": tree.get("chain", []),
                "rebuttal_tree": tree.get("rebuttal_tree", {}),
                "survival_probability": f"{int((1.0 - tree.get('probability_collapse', 0.5)) * 100)}%",
                "collapse_risk": f"{int(tree.get('probability_collapse', 0.5) * 100)}%"
            }

        if offense_type == "420" and case_data.get("contract_exists"):
            node = _build_node("IPC_420")
            if node: analysis_nodes.append(node)
            
        if offense_type == "406" and not case_data.get("entrustment_proven"):
            node = _build_node("IPC_406")
            if node: analysis_nodes.append(node)

        if offense_type == "498A" and case_data.get("relatives_implicated"):
            node = _build_node("IPC_498A")
            if node: analysis_nodes.append(node)

        if offense_type == "302" and case_data.get("sudden_provocation"):
            node = _build_node("IPC_302")
            if node: analysis_nodes.append(node)

        if offense_type == "376" and case_data.get("prior_relationship"):
            node = _build_node("IPC_376")
            if node: analysis_nodes.append(node)

        if case_data.get("ndps_case") and case_data.get("personal_search_done"):
            node = _build_node("NDPS_S50")
            if node: analysis_nodes.append(node)

        if offense_type == "307" and case_data.get("superficial_injuries"):
            node = _build_node("IPC_307")
            if node: analysis_nodes.append(node)

        if offense_type in ["326", "324"] and case_data.get("injury_dispute"):
            node = _build_node("IPC_326")
            if node: analysis_nodes.append(node)

        if offense_type in ["468", "471", "467"] and not case_data.get("fsl_report_positive"):
            node = _build_node("IPC_468")
            if node: analysis_nodes.append(node)

        if case_data.get("conspiracy_charged") and not case_data.get("direct_communication_proven"):
            node = _build_node("IPC_120B")
            if node: analysis_nodes.append(node)

        if case_data.get("pmla_case") and case_data.get("predicate_quashed"):
            node = _build_node("PMLA_PREDICATE")
            if node: analysis_nodes.append(node)

        if case_data.get("medical_contradicts_ocular"):
            node = _build_node("MEDICAL_OCULAR")
            if node: analysis_nodes.append(node)

        if case_data.get("ndps_case") and case_data.get("commercial_quantity"):
            node = _build_node("NDPS_S37")
            if node: analysis_nodes.append(node)

        if case_data.get("pc_act_case") and case_data.get("trap_witness_hostile"):
            node = _build_node("PC_ACT_TRAP")
            if node: analysis_nodes.append(node)

        if case_data.get("pocso_case") and case_data.get("age_dispute"):
            node = _build_node("POCSO_AGE")
            if node: analysis_nodes.append(node)

        if case_data.get("s161_s164_contradiction"):
            node = _build_node("CRPC_161_164")
            if node: analysis_nodes.append(node)

        if case_data.get("fir_delay_unexplained"):
            node = _build_node("CRPC_154")
            if node: analysis_nodes.append(node)

        if case_data.get("default_bail_window"):
            node = _build_node("CRPC_167")
            if node: analysis_nodes.append(node)

        if offense_type in ["378", "379", "THEFT"] and case_data.get("claim_of_right"):
            node = _build_node("IPC_378")
            if node: analysis_nodes.append(node)

        if offense_type in ["390", "392", "ROBBERY"] and case_data.get("no_imminent_fear"):
            node = _build_node("IPC_390")
            if node: analysis_nodes.append(node)

        if offense_type in ["441", "448", "TRESPASS"] and case_data.get("civil_possession_dispute"):
            node = _build_node("IPC_441")
            if node: analysis_nodes.append(node)

        if case_data.get("confession_to_police") and not case_data.get("discovery_of_fact"):
            node = _build_node("IEA_25")
            if node: analysis_nodes.append(node)

        if case_data.get("dying_declaration") and case_data.get("unfit_state"):
            node = _build_node("IEA_32")
            if node: analysis_nodes.append(node)

        if case_data.get("cyber_crime") and case_data.get("no_hash_value"):
            node = _build_node("IT_66")
            if node: analysis_nodes.append(node)

        if case_data.get("arms_recovery") and not case_data.get("conscious_possession"):
            node = _build_node("ARMS_25")
            if node: analysis_nodes.append(node)

        if case_data.get("framing_of_charge") and case_data.get("no_prima_facie_case"):
            node = _build_node("CRPC_227")
            if node: analysis_nodes.append(node)

        if case_data.get("quashing_petition") and case_data.get("civil_dispute_cloak"):
            node = _build_node("CRPC_482")
            if node: analysis_nodes.append(node)

        if case_data.get("accused_outside_jurisdiction") and not case_data.get("s202_inquiry_done"):
            node = _build_node("CRPC_200")
            if node: analysis_nodes.append(node)

        if case_data.get("witness_recall") and case_data.get("filling_lacunae"):
            node = _build_node("CRPC_311")
            if node: analysis_nodes.append(node)

        if case_data.get("incriminating_evidence_used") and not case_data.get("put_to_accused_in_313"):
            node = _build_node("CRPC_313")
            if node: analysis_nodes.append(node)

        if case_data.get("summoning_additional_accused") and case_data.get("vague_evidence"):
            node = _build_node("CRPC_319")
            if node: analysis_nodes.append(node)

        if offense_type in ["191", "193", "PERJURY"] and case_data.get("private_complaint"):
            node = _build_node("IPC_193")
            if node: analysis_nodes.append(node)

        if offense_type in ["499", "500", "DEFAMATION"] and case_data.get("good_faith_exception"):
            node = _build_node("IPC_499")
            if node: analysis_nodes.append(node)

        if case_data.get("appeal_filed") and case_data.get("seek_suspension_sentence"):
            node = _build_node("CRPC_389")
            if node: analysis_nodes.append(node)

        if offense_type == "304A" and case_data.get("no_proximate_cause"):
            node = _build_node("IPC_304A")
            if node: analysis_nodes.append(node)

        if offense_type == "354" and case_data.get("no_sexual_intent"):
            node = _build_node("IPC_354")
            if node: analysis_nodes.append(node)

        if offense_type == "304B" and not case_data.get("soon_before_death_nexus"):
            node = _build_node("IPC_304B")
            if node: analysis_nodes.append(node)

        if offense_type == "494" and not case_data.get("essential_ceremonies_proven"):
            node = _build_node("IPC_494")
            if node: analysis_nodes.append(node)

        if offense_type == "149" and case_data.get("mere_bystander"):
            node = _build_node("IPC_149")
            if node: analysis_nodes.append(node)

        if case_data.get("dowry_death_presumption_triggered") and case_data.get("rebuttal_evidence"):
            node = _build_node("IEA_113B")
            if node: analysis_nodes.append(node)

        if case_data.get("evidence_withheld_by_prosecution"):
            node = _build_node("IEA_114")
            if node: analysis_nodes.append(node)

        if case_data.get("uapa_case") and case_data.get("seek_bail"):
            node = _build_node("UAPA_43D")
            if node: analysis_nodes.append(node)

        return analysis_nodes

    @classmethod
    def audit_case(cls, case_data: Dict, concepts: List[Dict]) -> Dict:
        """Central audit method for the criminal orchestrator."""
        cls.load_knowledge_base()
        contradictions = cls.detect_contradictions(case_data, concepts)
        analysis_nodes = cls.simulate_strategic_stress_test(case_data, concepts)
        
        base_risk = 0.20
        for node in analysis_nodes:
            try:
                dest_prob = float(node["collapse_risk"].strip('%')) / 100.0
                base_risk += (dest_prob * 0.3)
            except: base_risk += 0.1
            
        for c in contradictions:
            if "Fatal" in c["severity"]:
                base_risk += 0.4
            elif "Material" in c["severity"]:
                base_risk += 0.2
            else:
                base_risk += 0.1
                
        return {
            "risks_and_rebuttals": analysis_nodes,
            "contradictions": contradictions, 
            "adversarial_risk": min(0.95, base_risk)
        }
