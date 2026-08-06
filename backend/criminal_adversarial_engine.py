from typing import Dict, List
from adversarial_engine import AdversarialEngine
class CriminalAdversarialEngine(AdversarialEngine):
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
        if cls.VULNERABILITY_MODELS:
            return
        try:
            import json, os
            kb_path = os.path.join(os.path.dirname(__file__), 'criminal_knowledge_base.json')
            with open(kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls.VULNERABILITY_MODELS = data.get("vulnerability_models", {})
        except Exception as e:
            cls.VULNERABILITY_MODELS = {}           
    @classmethod
    def calculate_stage_survivability(cls, severity_score: int, adversarial_risk: float) -> List[Dict]:
        roadmap = []
        current_risk_multiplier = 1.0 - (adversarial_risk * 0.5)
        for stage in cls.PROCEDURAL_STAGES:
            prob = stage["baseline_prob"] * (severity_score / 100.0) * current_risk_multiplier
            if stage["id"] == "cross":
                prob *= 0.65                                                            
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
                "cross_exam_questions": tree.get("cross_exam_questions", []),
                "quashing_ground": tree.get("quashing_ground", ""),
                "survival_probability": f"{int((1.0 - tree.get('probability_collapse', 0.5)) * 100)}%",
                "collapse_risk": f"{int(tree.get('probability_collapse', 0.5) * 100)}%"
            }
        if offense_type:
            matched = False
            for model_key in cls.VULNERABILITY_MODELS.keys():
                if offense_type in model_key or model_key in offense_type:
                    node = _build_node(model_key)
                    if node:
                        analysis_nodes.append(node)
                        matched = True
            if not matched and ("IPC" in offense_type or "BNS" in offense_type):
                node = {
                    "adversarial_vector": f"Procedural Challenge ({offense_type})",
                    "risk": f"Generic evidentiary and procedural vulnerabilities under {offense_type}",
                    "severity": "HIGH",
                    "description": "Standard rigorous cross-examination on factum of incident, ocular inconsistencies, and procedural delays.",
                    "strategic_chain": ["Delay in FIR", "Absence of independent corroboration", "Contradictions in statement"],
                    "rebuttal_tree": {
                        "complainant_counter": "Rely on the consistency of the core narrative and unimpeachable witnesses.",
                        "magistrate_view": "Scrutiny of evidence standard."
                    },
                    "cross_exam_questions": [
                        "Can you explain the exact timeline of the alleged incident?",
                        "Were there any independent witnesses present who were not your relatives?",
                        "Is it not true that this complaint is an afterthought motivated by a civil dispute?"
                    ],
                    "quashing_ground": "No prima facie case made out from the bare reading of the FIR.",
                    "survival_probability": "65%",
                    "collapse_risk": "35%"
                }
                analysis_nodes.append(node)
        if case_data.get("medical_contradicts_ocular"):
            node = _build_node("MEDICAL_OCULAR")
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
        for node in analysis_nodes:
            if node.get("quashing_ground"):
                node["discharge_quashing_strategy"] = f"File S.482 CrPC / S.528 BNSS petition citing: {node['quashing_ground']}."
        return analysis_nodes
    @classmethod
    def audit_case(cls, case_data: Dict, concepts: List[Dict]) -> Dict:
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
