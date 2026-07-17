from typing import List, Dict
from kb_manager import kb_manager
def ensure_list(x):
    if x is None: return []
    if isinstance(x, list): return x
    return [x]
def ensure_number(x, default=0):
    try: return float(x)
    except (TypeError, ValueError): return default
DEFENCE_ONLY_NEGATIVE_CONCEPTS = {
    "security_cheque", "signature_dispute", "signature_disputed", "no_debt_proof",
    "notice_not_sent", "notice_defect", "limitation_issue", "cheque_misuse",
    "no_agreement", "cheque_validity_issue", "payment_already_made", "dishonour_disputed",
    "financial_capacity_risk"
}
POSITIVE_CONCEPTS_NO_DEFENCE = {
    "cheque_bounce", "legal_notice_compliance", "legally_enforceable_debt",
    "strong_documentary_evidence"
}
class DefenceEngineV12:
    @classmethod
    def generate_ranked_defences(cls,
                                 concepts: List[Dict],
                                 case_data: Dict,
                                 case_strength: float) -> List[Dict]:
        """
        Generate realistic defence strategies with accurate success probabilities
        Logic:
        - High case strength (75+): Defences have low probability (10-30%)
        - Medium strength (40-74): Defences moderate probability (25-55%)
        - Low strength (<40): Defences high probability (45-85%)
        - Confidence matters: Higher concept confidence = higher defence success chance
        """
        defences = []
        weights = kb_manager.get_defence_legal_weights()
        templates = kb_manager.get_defence_templates()
        seen = set()
        for concept_det in ensure_list(concepts):
            if not isinstance(concept_det, dict):
                continue
            concept = concept_det.get("concept", "unknown")
            confidence = ensure_number(concept_det.get("confidence", 0))
            if concept in POSITIVE_CONCEPTS_NO_DEFENCE:
                continue
            if concept not in DEFENCE_ONLY_NEGATIVE_CONCEPTS:
                continue
            if concept not in templates or concept in seen:
                continue
            if confidence < 0.20:
                continue
            seen.add(concept)
            legal_weight = weights.get(concept, 0.75)
            arg, reb, basis = templates[concept]
            base_prob = confidence * legal_weight * 100
            if case_strength >= 75:
                strength_multiplier = 0.3  
            elif case_strength >= 60:
                strength_multiplier = 0.5
            elif case_strength >= 45:
                strength_multiplier = 0.75
            elif case_strength >= 30:
                strength_multiplier = 1.0
            else:
                strength_multiplier = 1.25  
            concept_modifiers = {
                "notice_defect": 1.3,  
                "notice_not_sent": 1.4,  
                "limitation_issue": 1.35,  
                "no_debt_proof": 1.2,  
                "signature_dispute": 0.85,  
                "security_cheque": 0.9,  
                "payment_already_made": 1.1,  
                "cheque_misuse": 0.8,  
                "no_agreement": 1.15,  
                "financial_capacity_risk": 1.25, 
            }
            concept_mod = concept_modifiers.get(concept, 1.0)
            prob = int(base_prob * strength_multiplier * concept_mod)
            prob = max(8, min(88, prob))
            if prob >= 65:
                strength = "HIGH"
            elif prob >= 35:
                strength = "MEDIUM"
            else:
                strength = "LOW"
            defences.append({
                "argument": arg,
                "strength": strength,
                "success_probability": prob,
                "trigger_reason": f"{concept.replace('_', ' ')} detected (confidence: {confidence:.0%})",
                "rebuttal": reb,
                "legal_basis": basis,
                "concept": concept,
                "confidence": confidence
            })
        defences.sort(key=lambda x: x['success_probability'], reverse=True)
        return defences[:5]
