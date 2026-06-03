import re
import logging
from typing import List, Dict, Any, Tuple
from kb_manager import kb_manager

logger = logging.getLogger(__name__)

def ensure_list(x):
    if x is None: return []
    if isinstance(x, list): return x
    return [x]

def ensure_number(x, default=0):
    try: return float(x)
    except: return default

NEGATION_WINDOW = 6

def _is_negated(text_tokens: List[str], match_start_idx: int) -> bool:
    """Check if a phrase is negated by looking at preceding words"""
    negators = {
        "no", "not", "without", "never", "cannot", "didn't", "did not", 
        "wasn't", "hasn't", "haven't", "lack", "lacking", "absent", 
        "missing", "none", "neither", "nor", "un", "doesn't"
    }
    window_start = max(0, match_start_idx - NEGATION_WINDOW)
    window = text_tokens[window_start:match_start_idx]
    return any(tok in negators for tok in window)

NEGATION_SENSITIVE_CONCEPTS = {
    "payment_already_made",
    "legally_enforceable_debt",
    "legal_notice_compliance",
    "strong_documentary_evidence",
    "cheque_bounce"
}

class SemanticEngineV12:
    @classmethod
    def analyze_text(cls, text: str) -> Dict[str, Any]:
        """Analyze case description text and extract legal concepts"""
        detected = cls.detect_concepts(text)
        return {
            "concepts_detected": detected,
            "total_confidence": (
                sum(c.get("confidence", 0) for c in detected) / len(detected)
                if detected else 0.0
            ),
            "count": len(detected),
            "method": "SemanticEngineV12_enhanced",
            "text_analyzed": text[:200] + "..." if len(text) > 200 else text,
        }

    @classmethod
    def detect_concepts(cls, text: str) -> List[Dict]:
        """Enhanced concept detection with better pattern matching"""
        if not text:
            return []
        
        text_lower = text.lower()
        tokens = re.findall(r'\w+', text_lower)
        detected = []
        concepts_config = kb_manager.get_legal_concepts()

        for concept, config in concepts_config.items():
            matched_phrases = []
            match_count = 0
            negated_count = 0
            patterns = config.get('patterns', [])

            for pattern in patterns:
                for m in re.finditer(pattern, text_lower, re.IGNORECASE):
                    match_start = len(re.findall(r'\w+', text_lower[:m.start()]))
                    
                    # Check for negation
                    is_negated = False
                    if concept in NEGATION_SENSITIVE_CONCEPTS:
                        is_negated = _is_negated(tokens, match_start)
                    
                    if is_negated:
                        negated_count += 1
                    else:
                        match_count += 1
                        matched_text = m.group(0)
                        if matched_text not in matched_phrases:
                            matched_phrases.append(matched_text)

            if match_count > 0:
                # Enhanced confidence calculation
                pattern_coverage = min(match_count / max(len(patterns), 1), 1.0)
                base_confidence = pattern_coverage * config.get('weight', 1.0)
                
                # Bonus for multiple unique phrase matches
                phrase_diversity_boost = min(len(set(matched_phrases)) * 0.08, 0.25)
                
                # Penalty for negations
                negation_penalty = min(negated_count * 0.18, 0.5)
                
                # Special boost for exact critical phrase matches
                critical_boost = 0.0
                if any(phrase in text_lower for phrase in ["funds insufficient", "signature mismatch", "account closed", "payment stopped"]):
                    if concept in ["cheque_bounce", "dishonour_disputed"]:
                        critical_boost = 0.15
                
                final_confidence = min(
                    max(base_confidence + phrase_diversity_boost + critical_boost - negation_penalty, 0.0), 
                    1.0
                )

                if final_confidence > 0.15:  # Lower threshold for detection
                    detected.append({
                        "concept": concept,
                        "confidence": round(final_confidence, 2),
                        "matched_phrases": list(set(matched_phrases))[:5],
                        "legal_impact": config.get('legal_impact', "N/A")
                    })

        detected.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return detected


class EnhancedSemanticExtractor:
    @staticmethod
    def extract_concepts(text: str, threshold: float = 0.20) -> Dict[str, Any]:
        """Extract concepts with configurable threshold"""
        result = SemanticEngineV12.analyze_text(text)
        concepts = result.get("concepts_detected", [])
        filtered = [c for c in concepts if c.get("confidence", 0) >= threshold]
        return {
            "concepts_detected": filtered,
            "total_confidence": (
                sum(c.get("confidence", 0) for c in filtered) / len(filtered)
                if filtered else 0.0
            ),
            "count": len(filtered),
            "method": "SemanticEngineV12_enhanced_compat",
            "text_analyzed": result.get("text_analyzed", "")
        }

