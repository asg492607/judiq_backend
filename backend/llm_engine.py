"""
JudiQ AI — LLM Engine & Deterministic Reasoning Router
Supports plug-and-play Groq Cloud API inference with seamless fallback to
100% deterministic rule-based Indian legal analytics.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Environment & Groq configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

_groq_client = None
LLM_AVAILABLE = False

if GROQ_API_KEY:
    try:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
        LLM_AVAILABLE = True
        logger.info(f"⚡ Groq LLM Engine activated using model: {GROQ_MODEL}")
    except ImportError:
        logger.warning("⚠️ 'groq' package not installed. Run 'pip install groq'. Falling back to deterministic mode.")
        LLM_AVAILABLE = False
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Groq client: {e}. Falling back to deterministic mode.")
        LLM_AVAILABLE = False
else:
    logger.info("ℹ️ Running in strict 100% Deterministic (Rule-Based) mode. Set GROQ_API_KEY to activate Groq LLM.")


def _invoke_llm(
    prompt: str,
    max_tokens: int = 1000,
    temperature: float = 0.2,
    expect_json: bool = False,
    fallback_value: Any = None,
    system_prompt: Optional[str] = None
) -> Any:
    """
    Invokes Groq API if active; returns fallback_value on any failure or if inactive.
    """
    global _groq_client, LLM_AVAILABLE

    # Check dynamically in case GROQ_API_KEY was set at runtime
    if not LLM_AVAILABLE:
        runtime_key = os.environ.get("GROQ_API_KEY", "").strip()
        if runtime_key and not _groq_client:
            try:
                from groq import Groq
                _groq_client = Groq(api_key=runtime_key)
                LLM_AVAILABLE = True
                logger.info(f"⚡ Groq LLM Engine activated at runtime using model: {GROQ_MODEL}")
            except Exception:
                return fallback_value
        else:
            return fallback_value

    default_system = (
        "You are JudiQ AI, an elite legal intelligence system specialized in Indian Law "
        "(Negotiable Instruments Act, SARFAESI Act, Bharatiya Nyaya Sanhita, CPC, and CrPC). "
        "Provide precise, authoritative legal analysis adhering to Supreme Court of India precedents."
    )

    try:
        messages = [
            {"role": "system", "content": system_prompt or default_system},
            {"role": "user", "content": prompt}
        ]

        kwargs: Dict[str, Any] = {
            "model": GROQ_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if expect_json:
            kwargs["response_format"] = {"type": "json_object"}

        response = _groq_client.chat.completions.create(**kwargs)
        result_text = response.choices[0].message.content.strip()

        if expect_json:
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                logger.warning("Groq response was not valid JSON, returning fallback.")
                return fallback_value

        return result_text
    except Exception as err:
        logger.warning(f"Groq invocation failed ({err}), falling back to deterministic result.")
        return fallback_value


def generate_executive_summary(score: int, weaknesses: List[str], strengths: List[str], case_data: Dict[str, Any]) -> str:
    """
    Generates a strategic litigation assessment executive summary.
    Computes a deterministic baseline and optionally enhances it with Groq LLM if active.
    """
    role = str(case_data.get('client_role', 'Complainant')).title()
    case_type = case_data.get('case_type', 'Cheque Bounce')
    amount = case_data.get("cheque_amount") or case_data.get("amount") or "an unspecified amount"

    if score >= 75:
        verdict = "This case presents a highly favorable strategic posture."
        risk_profile = "The core statutory requirements appear fully satisfied, presenting minimal fatal risks."
    elif score >= 45:
        verdict = "This case presents a moderate strategic posture with actionable vulnerabilities."
        risk_profile = "While primary statutory elements exist, there are evidentiary gaps that opposing counsel will actively target."
    elif score > 0:
        verdict = "This case carries significant litigation risk and low survivability."
        risk_profile = "Critical statutory pillars or evidentiary proofs are currently defective or entirely missing."
    else:
        verdict = "This case is legally unmaintainable in its current configuration."
        risk_profile = "A fatal defect (e.g., limitation expiry, invalid notice amount, or missing corporate officers) mandates immediate strategic reassessment to avoid penalties or malicious prosecution claims."

    deterministic_summary = f"As Counsel for the {role} in this {case_type} matter (Amount: Rs. {amount}), our deterministic audit yields a Case Readiness Score of {score}/100. {verdict}\n\n"
    if strengths and score > 0:
        deterministic_summary += f"Our primary strategic advantages include: {', '.join(strengths[:3])}. "
    if weaknesses:
        deterministic_summary += f"{risk_profile} Immediate attention is required to cure the following defects: {', '.join(weaknesses[:3])}."
    elif score == 0:
        deterministic_summary += f"{risk_profile}"

    deterministic_summary = deterministic_summary.strip()

    if not LLM_AVAILABLE:
        return deterministic_summary

    prompt = (
        f"Enhance this executive case summary for court presentation while strictly preserving all facts, numbers, and score:\n"
        f"Role: {role}, Case Type: {case_type}, Amount: Rs. {amount}, Score: {score}/100\n"
        f"Strengths: {', '.join(strengths)}\n"
        f"Weaknesses: {', '.join(weaknesses)}\n\n"
        f"Draft summary:\n{deterministic_summary}"
    )
    llm_res = _invoke_llm(prompt, max_tokens=600, temperature=0.3, fallback_value=deterministic_summary)
    return llm_res or deterministic_summary


def enhance_legal_draft(base_draft: str, draft_type: str, case_data: Dict[str, Any], tone: str = "Standard") -> str:
    """
    Polishes legal drafts for courtroom presentation.
    In deterministic mode, returns the structured base template.
    With Groq LLM active, refines language for forensic precision.
    """
    if not base_draft:
        return ""

    if not LLM_AVAILABLE:
        return base_draft.strip()

    prompt = (
        f"Refine and enhance the following Indian legal draft ({draft_type}) in a {tone} tone. "
        f"Strictly maintain formal legal terminology, Indian court formatting conventions, "
        f"and all factual data:\n\n{base_draft}"
    )
    enhanced = _invoke_llm(prompt, max_tokens=2500, temperature=0.2, fallback_value=base_draft.strip())
    return enhanced or base_draft.strip()


def extract_fact_graph(text: str) -> Dict[str, Any]:
    """
    Extracts entity-relationship fact topology from case description.
    Uses Groq structured JSON extraction when available; otherwise provides deterministic template.
    """
    fallback = {
        "entities": ["Complainant", "Accused", "Bank"],
        "relationships": [
            {"source": "Complainant", "target": "Accused", "relation": "Disputed Transaction"},
            {"source": "Accused", "target": "Bank", "relation": "Cheque Drawer"}
        ],
        "contradictions": [],
        "timeline_complexity": "Medium"
    }

    if not LLM_AVAILABLE or not text:
        return fallback

    prompt = (
        f"Extract a legal fact graph from the following case narrative. "
        f"Return a JSON object with keys 'entities' (list of strings), "
        f"'relationships' (list of {{source, target, relation}}), "
        f"'contradictions' (list of strings), and 'timeline_complexity' ('Low' | 'Medium' | 'High'):\n\n{text}"
    )
    result = _invoke_llm(prompt, max_tokens=1000, expect_json=True, fallback_value=fallback)
    if isinstance(result, dict) and "entities" in result and "relationships" in result:
        return result
    return fallback


def analyze_precedent_relationships(case_data: Dict[str, Any], precedents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Classifies precedent applicability into BINDING, HIGHLY RELEVANT, or DISTINGUISHABLE.
    """
    if not precedents:
        return []

    for idx, p in enumerate(precedents):
        score = p.get("relevance", 0.0)
        if score >= 0.90:
            p["relationship"] = "BINDING"
            p["llm_reasoning"] = f"Directly applicable landmark judgment establishing strict liability for {p.get('concept', 'this issue')}."
        elif score >= 0.70:
            p["relationship"] = "HIGHLY RELEVANT"
            p["llm_reasoning"] = "Provides strong persuasive authority regarding the statutory interpretation of this specific dispute."
        else:
            p["relationship"] = "DISTINGUISHABLE"
            p["llm_reasoning"] = "Opposing counsel may attempt to distinguish this based on specific factual variances."

    return precedents
