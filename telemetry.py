import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)
TELEMETRY_FILE = "telemetry.jsonl"

def log_case_execution(case_data, result, duration_ms):
    try:
        telemetry_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "case_type": case_data.get("case_type", "unknown"),
            "score": result.get("score", 0),
            "verdict": result.get("verdict", "Unknown"),
            "risk_level": result.get("risk_level", "Unknown"),
            "duration_ms": duration_ms,
            "has_description": bool(case_data.get("description")),
            "is_fallback": result.get("is_fallback", False)
        }
        
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(telemetry_entry) + "\n")
            
    except Exception as e:
        logger.warning(f"Failed to write telemetry: {e}")
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

@router.post("/error")
async def log_telemetry_error(request: Request):
    try:
        body = await request.json()
        logger.error(f"Frontend Telemetry Error: {body}")
        return {"status": "logged"}
    except Exception as e:
        return {"status": "failed", "reason": str(e)}
