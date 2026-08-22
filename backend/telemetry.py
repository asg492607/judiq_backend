import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter()

# Use an absolute path relative to this file so it works correctly
# regardless of the current working directory (e.g. inside Docker)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TELEMETRY_FILE = os.path.join(_BASE_DIR, "telemetry.jsonl")


def log_case_execution(case_data: dict, result: dict, duration_ms: float) -> None:
    """
    Appends a single telemetry entry to a local JSONL file.
    Non-blocking: failures are logged as warnings and silently swallowed
    so telemetry never impacts the main analysis path.
    """
    try:
        telemetry_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
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


@router.post("/error", tags=["Telemetry"])
async def log_telemetry_error(request: Request):
    """
    Receives frontend error reports and logs them server-side.
    The endpoint intentionally accepts any JSON body so it never
    blocks the client's error reporting flow.
    """
    try:
        body = await request.json()
        # Truncate oversized payloads to prevent log flooding
        if isinstance(body, dict):
            body = {k: str(v)[:500] for k, v in list(body.items())[:20]}
        logger.error(f"Frontend Telemetry Error: {body}")
        return {"status": "logged"}
    except Exception as e:
        logger.warning(f"Failed to parse telemetry error payload: {e}")
        return {"status": "failed", "reason": str(e)}
