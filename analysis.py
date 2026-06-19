# pyrefly: ignore [missing-import]
import logging
import sqlite3
import asyncio
from datetime import datetime
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from config import settings
from engine_core import JudiQEngine
from normalizer import normalize_input, validate_minimum_viability, ValidationError
from session import DatabaseManager
from security import AuditLogger, SecurityTelemetry
from caseroom_logic import CaseroomManager
from limiter import limiter

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
    
    class Config:
        extra = "ignore"

ANALYSIS_CACHE = {}

def get_cache_key(data: dict):
    import json
    import hashlib
    dump = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.md5(dump).hexdigest()

from schemas import EngineResponse

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
    
    # 1. Audit Log
    client_ip = request.client.host if request.client else "unknown"
    AuditLogger.log_interaction(user_id, "PENDING", "START_ANALYSIS", {"ip": client_ip})

    # 2. Security Telemetry
    threats = SecurityTelemetry.audit_payload(raw_data)
    if threats:
        AuditLogger.log_interaction(user_id, "THREAT", "SECURITY_VIOLATION", {"threats": threats})
        logger.error(f"[{request_id}] Security threats detected: {threats}")
        return JSONResponse(status_code=403, content={"success": False, "error": "Malicious payload detected."})

    # 3. Caching
    cache_key = get_cache_key(raw_data)
    if cache_key in ANALYSIS_CACHE:
        logger.info(f"[{request_id}] Cache hit for request.")
        cached = dict(ANALYSIS_CACHE[cache_key])
        cached["request_id"] = request_id
        return cached

    logger.info(f"[{request_id}] /analyze request received")

    # 4. Minimum viability gate
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

    # 5. Engine execution
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

    # 6. Persist
    try:
        case_data = result.get("case_data", {})
        uid = case_data.get("user_id", "ANONYMOUS")
        cid = case_data.get("case_id", "")
        
        # Always cache the result regardless of user authentication
        if len(ANALYSIS_CACHE) >= 100:
            oldest_key = next(iter(ANALYSIS_CACHE))
            del ANALYSIS_CACHE[oldest_key]
        ANALYSIS_CACHE[cache_key] = result
        
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
            
            # Auto-initialize Caseroom
            existing_room_id = DatabaseManager.get_caseroom_by_case_id(cid)
            if not existing_room_id:
                CaseroomManager.initialize_caseroom_for_case(cid, uid)
    except Exception as e:
        logger.warning(f"[{request_id}] DB/Caseroom persistence failed (non-fatal): {e}")

    # 7. Build response
    response_body = {"success": True, "request_id": request_id}
    response_body.update(result)
    
    # Include Caseroom ID
    case_data = result.get("case_data", {})
    cid = case_data.get("case_id", "")
    try:
        response_body["caseroom_id"] = DatabaseManager.get_caseroom_by_case_id(cid) if cid else None
    except Exception as e:
        logger.warning(f"[{request_id}] Caseroom lookup failed (non-fatal): {e}")
        response_body["caseroom_id"] = None

    # Jurisdiction Mapping
    try:
        from jurisdiction_engine import map_jurisdiction
        response_body["jurisdiction"] = map_jurisdiction(raw_data)
    except (KeyError, ValueError) as je:
        logger.warning(f"Jurisdiction mapping failed: {je}")
        response_body["jurisdiction"] = None

    response_body["data"] = result
    if len(ANALYSIS_CACHE) >= 100:
        oldest_key = next(iter(ANALYSIS_CACHE))
        del ANALYSIS_CACHE[oldest_key]
    ANALYSIS_CACHE[cache_key] = dict(response_body)
    return response_body

