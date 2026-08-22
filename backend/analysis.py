import json
import hashlib
import logging
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

from engine_core import JudiQEngine
from normalizer import validate_minimum_viability, ValidationError
from session import DatabaseManager
from security import AuditLogger, SecurityTelemetry
from caseroom_logic import CaseroomManager
from limiter import limiter
from jurisdiction_engine import map_jurisdiction
from schemas import EngineResponse

router = APIRouter()
logger = logging.getLogger("JudiQ.Analysis")


class CaseAnalysisRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=10000)
    amount: Optional[float] = 0.0
    cheque_present: Optional[bool] = False
    dishonour_memo: Optional[bool] = False
    notice_sent: Optional[bool] = False
    debt_proven: Optional[bool] = False
    accused_type: Optional[str] = "Individual"
    analysis_mode: Optional[str] = "detailed"
    model_config = ConfigDict(extra="ignore")


# In-memory LRU cache — keyed by (user_id, content_hash) to prevent
# cross-user data leakage. Max 100 entries with FIFO eviction.
ANALYSIS_CACHE: Dict[str, Any] = {}
CACHE_LOCK = threading.Lock()
CACHE_MAX_SIZE = 100


def get_cache_key(user_id: str, data: dict) -> str:
    """Generate a user-scoped cache key to prevent cross-user data leakage."""
    # Strip user_id from the content hash to avoid false misses, but scope by user_id prefix
    data_without_user = {k: v for k, v in data.items() if k not in ("user_id",)}
    dump = json.dumps(data_without_user, sort_keys=True).encode("utf-8")
    content_hash = hashlib.sha256(dump).hexdigest()
    return f"{user_id}:{content_hash}"


def _evict_if_full():
    """Evict oldest entry if cache is at capacity. Must be called under CACHE_LOCK."""
    if len(ANALYSIS_CACHE) >= CACHE_MAX_SIZE:
        oldest_key = next(iter(ANALYSIS_CACHE))
        del ANALYSIS_CACHE[oldest_key]


@router.post(
    "",
    response_model=EngineResponse,
    summary="Analyze Legal Case",
    description="Processes raw case facts through the Timeline, Scoring, and Adversarial engines to generate a comprehensive litigation strategy."
)
@limiter.limit("5/minute")
async def analyze(request_data: Dict[str, Any], request: Request):
    request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    raw_data = request_data
    user_id = raw_data.get("user_id", "ANONYMOUS")
    client_ip = request.client.host if request.client else "unknown"
    AuditLogger.log_interaction(user_id, "PENDING", "START_ANALYSIS", {"ip": client_ip})

    threats = await asyncio.to_thread(SecurityTelemetry.audit_payload, raw_data)
    if threats:
        AuditLogger.log_interaction(user_id, "THREAT", "SECURITY_VIOLATION", {"threats": threats})
        logger.error(f"[{request_id}] Security threats detected: {threats}")
        return JSONResponse(status_code=403, content={"success": False, "error": "Malicious payload detected."})

    # User-scoped cache key prevents cross-user data leakage
    cache_key = get_cache_key(user_id, raw_data)
    with CACHE_LOCK:
        if cache_key in ANALYSIS_CACHE:
            logger.info(f"[{request_id}] Cache hit for request.")
            cached = dict(ANALYSIS_CACHE[cache_key])
            cached["request_id"] = request_id
            return cached

    logger.info(f"[{request_id}] /analyze request received")
    try:
        validate_minimum_viability(raw_data)
    except ValidationError as ve:
        error_msg = getattr(ve, 'message', str(ve))
        field = getattr(ve, 'field', 'unknown')
        logger.warning(f"[{request_id}] Validation failed: {error_msg}")
        return JSONResponse(status_code=422, content={
            "success": False,
            "error": error_msg,
            "error_code": "VALIDATION_ERROR",
            "field": field,
            "user_message": error_msg
        })

    try:
        result = await asyncio.to_thread(JudiQEngine.analyze_case, raw_data)
    except ValidationError as ve:
        error_msg = getattr(ve, 'message', str(ve))
        return JSONResponse(status_code=422, content={
            "success": False,
            "error": error_msg,
            "error_code": "VALIDATION_ERROR",
            "user_message": error_msg
        })
    except RuntimeError as e:
        logger.error(f"[{request_id}] Engine error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_code": "ENGINE_CRASH",
                "user_message": "The AI engine encountered an unexpected error."
            }
        )
    except Exception as e:
        logger.error(f"[{request_id}] Unhandled Engine Exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_code": "INTERNAL_SERVER_ERROR",
                "user_message": "An unexpected server error occurred during analysis."
            }
        )

    try:
        case_data = result.get("case_data", {})
        uid = case_data.get("user_id", "ANONYMOUS")
        cid = case_data.get("case_id", "")
        if uid and cid and uid != "ANONYMOUS":
            await asyncio.to_thread(
                DatabaseManager.save_case,
                cid,
                uid,
                case_data,
                result,
                result.get("score", 0),
                result.get("verdict", "Unknown")
            )
            AuditLogger.log_interaction(user_id, cid, "FINISH_ANALYSIS", {"score": result.get("score")})
            existing_room_id = DatabaseManager.get_caseroom_by_case_id(cid)
            if not existing_room_id:
                CaseroomManager.initialize_caseroom_for_case(cid, uid)
    except Exception as e:
        logger.warning(f"[{request_id}] DB/Caseroom persistence failed (non-fatal): {e}")

    response_body = {"success": True, "request_id": request_id}
    response_body.update(result)
    case_data = result.get("case_data", {})
    cid = case_data.get("case_id", "")

    try:
        response_body["caseroom_id"] = DatabaseManager.get_caseroom_by_case_id(cid) if cid else None
    except Exception as e:
        logger.warning(f"[{request_id}] Caseroom lookup failed (non-fatal): {e}")
        response_body["caseroom_id"] = None

    try:
        response_body["jurisdiction"] = map_jurisdiction(raw_data)
    except (KeyError, ValueError) as je:
        logger.warning(f"Jurisdiction mapping failed: {je}")
        response_body["jurisdiction"] = None

    response_body["data"] = result

    # Single cache write — fixed the previous double-write bug
    with CACHE_LOCK:
        _evict_if_full()
        ANALYSIS_CACHE[cache_key] = dict(response_body)

    return response_body


class SimulationRequest(BaseModel):
    preset: Optional[str] = "s138_signature"
    notice_delay_days: Optional[int] = 12
    signature_disputed: Optional[bool] = False
    security_cheque: Optional[bool] = False
    evidence_65b: Optional[bool] = True


@router.post(
    "/simulate",
    summary="Simulate Cross-Examination Risk & Strategy",
    description="Calculates real-time courtroom survivability score and opposing counsel attack vectors for legal scenarios."
)
async def simulate_strategy(req: SimulationRequest):
    notice_delay = req.notice_delay_days or 0
    sig_disputed = req.signature_disputed
    sec_cheque = req.security_cheque
    e65b = req.evidence_65b

    score = 90
    if notice_delay > 30:
        score -= 55
    elif notice_delay > 25:
        score -= 10

    if sig_disputed:
        score -= 20
    if sec_cheque:
        score -= 15
    if not e65b:
        score -= 25

    score = max(10, min(99, score))

    if score >= 75:
        risk_level = "SAFE"
        status_text = "High Courtroom Survivability"
    elif score >= 50:
        risk_level = "WARNING"
        status_text = "Moderate Risk — Defense Counter Required"
    else:
        risk_level = "DANGER"
        status_text = "Fatal Procedural Vulnerability Detected"

    attack_vector = (
        "Opposing counsel will demand forensic handwriting expert opinion under Sec. 45 Evidence Act."
        if sig_disputed else (
            "Demand notice dispatched past 30-day window under Sec 138(b)."
            if notice_delay > 30 else
            "Opposing counsel will challenge admissibility of electronic records under Sec 65B."
        )
    )
    counter_strategy = (
        "File application for comparison of signatures by State Forensic Science Laboratory."
        if sig_disputed else (
            "Move application under Sec. 142(1)(b) proviso seeking condonation of delay."
            if notice_delay > 30 else
            "Submit Section 65B Electronic Evidence Affidavit from server administrator."
        )
    )
    ratio = "Dashrath Rupsingh Rathod v. State of Maharashtra (2014) — Procedural timeline compliance is strictly mandated under Section 138."

    return {
        "success": True,
        "survivability_score": score,
        "risk_level": risk_level,
        "status_text": status_text,
        "primary_attack_vector": attack_vector,
        "recommended_counter_strategy": counter_strategy,
        "precedent_ratio": ratio,
        "statutory_provisions": ["Sec. 138 NI Act", "Sec. 142 NI Act", "Sec. 45 Evidence Act", "Sec. 65B Evidence Act"]
    }
