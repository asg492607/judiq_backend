"""
JudiQ AI — LLM Engine & Deterministic Reasoning Router
======================================================
Dual-provider inference (Groq ultra-fast primary + Gemini multi-key multimodal cascade)
with 100% deterministic rule-based Indian legal analytics as the final safety net.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

try:
    from dotenv import load_dotenv
    _base_dir = Path(__file__).resolve().parent
    load_dotenv(_base_dir.parent / ".env")
    load_dotenv(_base_dir / ".env")
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Environment & Provider configuration
GROQ_API_KEY              = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL                = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GEMINI_API_KEY            = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_API_KEY_FALLBACK_1 = os.environ.get("GEMINI_API_KEY_FALLBACK_1", "").strip()
GEMINI_API_KEY_FALLBACK_2 = os.environ.get("GEMINI_API_KEY_FALLBACK_2", "").strip()
GEMINI_MODEL              = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()

# In-memory circuit-breaker / quarantine for permanently failing keys (e.g. 403 Forbidden)
_quarantined_gemini_keys: Set[str] = set()

_groq_client = None
if GROQ_API_KEY:
    try:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("⚡ Groq LLM Engine activated as primary fast-path.")
    except Exception as _g_err:
        logger.debug(f"Groq initialization skipped: {_g_err}")


def get_all_gemini_api_keys() -> List[str]:
    """
    Returns an ordered list of unique Gemini API keys with multi-tier fallback:
    1. GEMINI_API_KEY            (Primary)
    2. GEMINI_API_KEY_FALLBACK_1 (Fallback 1)
    3. GEMINI_API_KEY_FALLBACK_2 (Fallback 2)
    4. Any additional keys in comma-separated GEMINI_API_KEYS env var
    """
    keys: List[str] = []

    for env_var, cached in [
        ("GEMINI_API_KEY",            GEMINI_API_KEY),
        ("GEMINI_API_KEY_FALLBACK_1", GEMINI_API_KEY_FALLBACK_1),
        ("GEMINI_API_KEY_FALLBACK_2", GEMINI_API_KEY_FALLBACK_2),
    ]:
        k = os.environ.get(env_var, cached).strip()
        if k and k not in keys:
            keys.append(k)

    k_list = os.environ.get("GEMINI_API_KEYS", "").strip()
    if k_list:
        for k in k_list.split(","):
            clean_k = k.strip()
            if clean_k and clean_k not in keys:
                keys.append(clean_k)

    return keys


LLM_AVAILABLE = bool(_groq_client or get_all_gemini_api_keys())


def _call_gemini_rest(
    prompt: str,
    sys_msg: str,
    max_tokens: int,
    temperature: float,
    expect_json: bool,
    api_key: str,
    model: str,
    inline_data: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Call Gemini REST API directly via urllib with multimodal support and snappy timeout."""
    import urllib.request

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
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
                "data": inline_data["data"],
            }
        })

    payload: Dict[str, Any] = {
        "contents": [{"parts": parts}],
        "generationConfig": gen_config,
    }
    if sys_msg:
        payload["systemInstruction"] = {"parts": [{"text": sys_msg}]}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    # Snappy 8-second timeout so stalled calls fail fast to fallback keys
    with urllib.request.urlopen(req, timeout=8) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        candidates = res.get("candidates", [])
        if candidates:
            cand_parts = candidates[0].get("content", {}).get("parts", [])
            for p in cand_parts:
                if "text" in p and p["text"].strip():
                    return p["text"].strip()
        return None


def _invoke_llm(
    prompt: str,
    max_tokens: int = 1000,
    temperature: float = 0.2,
    expect_json: bool = False,
    fallback_value: Any = None,
    system_prompt: Optional[str] = None,
    inline_data: Optional[Dict[str, str]] = None,
) -> Any:
    """
    Invokes LLM with dual-engine fallback:
      1. Groq (ultra-fast ~300ms for text extraction)
      2. Gemini cascade (with key quarantine and rapid model fallback)
      3. Deterministic safety net
    """
    global LLM_AVAILABLE, _groq_client

    default_system = (
        "You are JudiQ AI, an elite legal intelligence system specialized in Indian Law "
        "(Negotiable Instruments Act, SARFAESI Act, Bharatiya Nyaya Sanhita, CPC, and CrPC). "
        "Provide precise, authoritative legal analysis adhering to Supreme Court of India precedents."
    )
    sys_msg = system_prompt or default_system

    # Dynamic Groq client initialization if env key was added at runtime
    if not _groq_client and os.environ.get("GROQ_API_KEY", "").strip():
        try:
            from groq import Groq
            _groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", "").strip())
            LLM_AVAILABLE = True
        except Exception:
            pass

    # ── Path 1: Groq fast-path (text-only, ultra-fast 300ms inference) ─────────
    if not inline_data and _groq_client:
        try:
            messages = [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt}
            ]
            kwargs: Dict[str, Any] = {
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": 6.0,
            }
            if expect_json:
                kwargs["response_format"] = {"type": "json_object"}

            resp = _groq_client.chat.completions.create(**kwargs)
            res_content = resp.choices[0].message.content
            if res_content and res_content.strip():
                if expect_json:
                    clean = res_content.strip()
                    if clean.startswith("```"):
                        clean = "\n".join(clean.split("\n")[1:])
                    if clean.endswith("```"):
                        clean = clean[:-3]
                    try:
                        return json.loads(clean.strip())
                    except json.JSONDecodeError:
                        logger.debug("Groq returned non-JSON, falling to Gemini cascade.")
                else:
                    return res_content.strip()
        except Exception as groq_err:
            logger.debug(f"Groq fast-path bypassed ({groq_err}), switching to Gemini cascade.")

    # ── Path 2: Gemini multi-key cascade with key quarantine ─────────────────
    gemini_keys = get_all_gemini_api_keys()
    if not gemini_keys:
        return fallback_value

    configured_model = os.environ.get("GEMINI_MODEL", GEMINI_MODEL).strip()
    # Ensure ONLY real, valid models are called in descending speed order
    candidate_models: List[str] = []
    for m in ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", configured_model]:
        if m and m not in candidate_models and not m.startswith("gemini-3."):
            candidate_models.append(m)
    if not candidate_models:
        candidate_models = ["gemini-2.0-flash", "gemini-1.5-flash"]

    for idx, key in enumerate(gemini_keys):
        # Skip quarantined broken keys (e.g. 403 Forbidden) instantly with 0ms delay
        if key in _quarantined_gemini_keys:
            continue

        for model_name in candidate_models:
            try:
                result_text = _call_gemini_rest(
                    prompt=prompt,
                    sys_msg=sys_msg,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    expect_json=expect_json,
                    api_key=key,
                    model=model_name,
                    inline_data=inline_data,
                )
                if not result_text:
                    continue

                if expect_json:
                    clean = result_text.strip()
                    if clean.startswith("```"):
                        clean = "\n".join(clean.split("\n")[1:])
                    if clean.endswith("```"):
                        clean = clean[:-3]
                    try:
                        return json.loads(clean.strip())
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Gemini key #{idx+1} model '{model_name}' non-JSON, trying next..."
                        )
                        continue

                return result_text

            except Exception as err:
                err_str = str(err)
                # Quarantine permanent 403 Forbidden keys immediately
                if "403" in err_str or "Forbidden" in err_str:
                    _quarantined_gemini_keys.add(key)
                    logger.warning(
                        f"Gemini key #{idx+1} permanently quarantined (403 Forbidden). Bypassing for future calls."
                    )
                    break  # don't test other models on a 403 forbidden key

                logger.debug(f"Gemini key #{idx+1} model '{model_name}' attempt failed: {err}")
                continue

    return fallback_value


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_executive_summary(
    score: int, weaknesses: List[str], strengths: List[str], case_data: Dict[str, Any]
) -> str:
    """
    Generates a strategic litigation assessment executive summary.
    Computes a deterministic baseline and optionally enhances it with LLM.
    """
    role      = str(case_data.get("client_role", "Complainant")).title()
    case_type = case_data.get("case_type", "Cheque Bounce")
    amount    = case_data.get("cheque_amount") or case_data.get("amount") or "an unspecified amount"

    if score >= 75:
        verdict      = "This case presents a highly favorable strategic posture."
        risk_profile = "The core statutory requirements appear fully satisfied, presenting minimal fatal risks."
    elif score >= 45:
        verdict      = "This case presents a moderate strategic posture with actionable vulnerabilities."
        risk_profile = "While primary statutory elements exist, there are evidentiary gaps that opposing counsel will actively target."
    elif score > 0:
        verdict      = "This case carries significant litigation risk and low survivability."
        risk_profile = "Critical statutory pillars or evidentiary proofs are currently defective or entirely missing."
    else:
        verdict      = "This case is legally unmaintainable in its current configuration."
        risk_profile = (
            "A fatal defect (e.g., limitation expiry, invalid notice amount, or missing corporate officers) "
            "mandates immediate strategic reassessment to avoid penalties or malicious prosecution claims."
        )

    deterministic_summary = (
        f"As Counsel for the {role} in this {case_type} matter (Amount: Rs. {amount}), "
        f"our deterministic audit yields a Case Readiness Score of {score}/100. {verdict}\n\n"
    )
    if strengths and score > 0:
        deterministic_summary += f"Our primary strategic advantages include: {', '.join(strengths[:3])}. "
    if weaknesses:
        deterministic_summary += (
            f"{risk_profile} Immediate attention is required to cure the following defects: "
            f"{', '.join(weaknesses[:3])}."
        )
    elif score == 0:
        deterministic_summary += risk_profile

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


def enhance_legal_draft(
    base_draft: str, draft_type: str, case_data: Dict[str, Any], tone: str = "Standard"
) -> str:
    """
    Polishes legal drafts for courtroom presentation.
    In deterministic mode, returns the structured base template.
    With LLM active, refines language for forensic precision.
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
    Uses LLM structured JSON extraction when available; otherwise provides a deterministic template.
    """
    fallback = {
        "entities": ["Complainant", "Accused", "Bank"],
        "relationships": [
            {"source": "Complainant", "target": "Accused", "relation": "Disputed Transaction"},
            {"source": "Accused",     "target": "Bank",    "relation": "Cheque Drawer"},
        ],
        "contradictions": [],
        "timeline_complexity": "Medium",
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


def analyze_precedent_relationships(
    case_data: Dict[str, Any], precedents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Classifies precedent applicability into BINDING, HIGHLY RELEVANT, or DISTINGUISHABLE.
    """
    if not precedents:
        return []

    for p in precedents:
        score = p.get("relevance", 0.0)
        if score >= 0.90:
            p["relationship"]  = "BINDING"
            p["llm_reasoning"] = (
                f"Directly applicable landmark judgment establishing strict liability "
                f"for {p.get('concept', 'this issue')}."
            )
        elif score >= 0.70:
            p["relationship"]  = "HIGHLY RELEVANT"
            p["llm_reasoning"] = (
                "Provides strong persuasive authority regarding the statutory "
                "interpretation of this specific dispute."
            )
        else:
            p["relationship"]  = "DISTINGUISHABLE"
            p["llm_reasoning"] = (
                "Opposing counsel may attempt to distinguish this based on specific factual variances."
            )

    return precedents
