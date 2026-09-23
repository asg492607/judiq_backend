"""
JudiQ AI — LLM Engine & Deterministic Reasoning Router
Supports plug-and-play Groq Cloud API inference with seamless fallback to
100% deterministic rule-based Indian legal analytics.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from dotenv import load_dotenv
    _base_dir = Path(__file__).resolve().parent
    load_dotenv(_base_dir.parent / ".env")
    load_dotenv(_base_dir / ".env")
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Environment & Groq / Gemini configuration
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL     = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash").strip()

_groq_client   = None
_gemini_model  = None
LLM_AVAILABLE  = False
LLM_PROVIDER   = "none"  # "groq" | "gemini" | "none"

# ── Primary: Groq ──────────────────────────────────────────────────────────
if GROQ_API_KEY:
    try:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
        LLM_AVAILABLE = True
        LLM_PROVIDER  = "groq"
        logger.info(f"⚡ Groq LLM Engine activated using model: {GROQ_MODEL}")
    except ImportError:
        logger.warning("⚠️ 'groq' package not installed. Run 'pip install groq'.")
    except Exception as e:
        logger.warning(f"⚠️ Groq init failed: {e}.")

# ── Secondary: Gemini (used when Groq unavailable) ─────────────────────────
if not LLM_AVAILABLE and GEMINI_API_KEY:
    LLM_AVAILABLE = True
    LLM_PROVIDER  = "gemini"
    logger.info(f"⚡ Gemini LLM Engine activated via REST using model: {GEMINI_MODEL}")

if not LLM_AVAILABLE:
    logger.info("ℹ️ Running in 100% Deterministic mode. Set GROQ_API_KEY or GEMINI_API_KEY to activate LLM.")


def _call_gemini_rest(
    prompt: str,
    sys_msg: str,
    max_tokens: int,
    temperature: float,
    expect_json: bool,
    api_key: str,
    model: str,
    inline_data: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """Call Gemini REST API directly using standard urllib with automatic retry and multimodal support."""
    import urllib.request
    import time
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    gen_config: Dict[str, Any] = {
        "maxOutputTokens": max(max_tokens, 2048),
        "temperature": temperature,
    }
    if expect_json:
        gen_config["responseMimeType"] = "application/json"

    parts: List[Dict[str, Any]] = []
    if prompt:
        parts.append({"text": prompt})
    if inline_data and "data" in inline_data and "mime_type" in inline_data:
        parts.append({
            "inlineData": {
                "mimeType": inline_data["mime_type"],
                "data": inline_data["data"]
            }
        })

    payload: Dict[str, Any] = {
        "contents": [{"parts": parts}],
        "generationConfig": gen_config,
    }
    if sys_msg:
        payload["systemInstruction"] = {"parts": [{"text": sys_msg}]}

    data = json.dumps(payload).encode("utf-8")
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                candidates = res.get("candidates", [])
                if candidates:
                    cand_parts = candidates[0].get("content", {}).get("parts", [])
                    for p in cand_parts:
                        if "text" in p and p["text"].strip():
                            return p["text"].strip()
                return None
        except Exception as e:
            if attempt < 1 and ("503" in str(e) or "500" in str(e) or "timeout" in str(e).lower()):
                time.sleep(0.8)
                continue
            raise e
    return None


def _invoke_llm(
    prompt: str,
    max_tokens: int = 1000,
    temperature: float = 0.2,
    expect_json: bool = False,
    fallback_value: Any = None,
    system_prompt: Optional[str] = None,
    inline_data: Optional[Dict[str, str]] = None
) -> Any:
    """
    Routes to the active LLM provider (Groq primary, Gemini secondary).
    If inline_data is present (multimodal image/PDF), routes directly to Gemini.
    Returns fallback_value on any failure or if no LLM is configured.
    """
    global _groq_client, LLM_AVAILABLE, LLM_PROVIDER

    # Dynamic runtime activation for Groq / Gemini
    if not LLM_AVAILABLE:
        runtime_groq = os.environ.get("GROQ_API_KEY", "").strip()
        runtime_gemini = os.environ.get("GEMINI_API_KEY", "").strip()
        if runtime_groq and not _groq_client:
            try:
                from groq import Groq
                _groq_client = Groq(api_key=runtime_groq)
                LLM_AVAILABLE = True
                LLM_PROVIDER  = "groq"
                logger.info("⚡ Groq LLM Engine activated at runtime.")
            except Exception:
                pass
        if not LLM_AVAILABLE and runtime_gemini:
            LLM_AVAILABLE = True
            LLM_PROVIDER  = "gemini"
            logger.info("⚡ Gemini LLM Engine activated at runtime.")
        if not LLM_AVAILABLE:
            return fallback_value

    default_system = (
        "You are JudiQ AI, an elite legal intelligence system specialized in Indian Law "
        "(Negotiable Instruments Act, SARFAESI Act, Bharatiya Nyaya Sanhita, CPC, and CrPC). "
        "Provide precise, authoritative legal analysis adhering to Supreme Court of India precedents."
    )
    sys_msg = system_prompt or default_system

    # ── Groq path (used only if no multimodal inline_data is required) ────────
    if not inline_data and LLM_PROVIDER == "groq" and _groq_client:
        try:
            messages = [
                {"role": "system", "content": sys_msg},
                {"role": "user",   "content": prompt}
            ]
            kwargs: Dict[str, Any] = {
                "model":       GROQ_MODEL,
                "messages":    messages,
                "max_tokens":  max_tokens,
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
            logger.warning(f"Groq invocation failed ({err}), trying Gemini if available.")
            if not os.environ.get("GEMINI_API_KEY"):
                return fallback_value

    # ── Gemini path (direct REST, supports text + multimodal inline_data) ─────
    gemini_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    gemini_model = os.environ.get("GEMINI_MODEL", GEMINI_MODEL).strip()
    if gemini_key:
        try:
            result_text = _call_gemini_rest(
                prompt=prompt,
                sys_msg=sys_msg,
                max_tokens=max_tokens,
                temperature=temperature,
                expect_json=expect_json,
                api_key=gemini_key,
                model=gemini_model,
                inline_data=inline_data,
            )
            if not result_text:
                return fallback_value

            if expect_json:
                clean = result_text.strip()
                if clean.startswith("```"):
                    clean = "\n".join(clean.split("\n")[1:])
                if clean.endswith("```"):
                    clean = clean[:-3]
                try:
                    return json.loads(clean.strip())
                except json.JSONDecodeError:
                    logger.warning("Gemini response was not valid JSON, returning fallback.")
                    return fallback_value
            return result_text
        except Exception as err:
            logger.warning(f"Gemini REST invocation failed ({err}), falling back to deterministic result.")
            return fallback_value

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
