import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TelemetryManager:
    """
    Priority 3: Deployment Reliability & Edge Case Tracking
    Captures failures, latency, score drift, and document anomalies to ensure startup maturity.
    """
    LOG_PATH = os.path.join(os.path.dirname(__file__), "telemetry_log.json")

    @classmethod
    def _ensure_log_exists(cls):
        if not os.path.exists(cls.LOG_PATH):
            with open(cls.LOG_PATH, "w") as f:
                json.dump({"events": [], "stats": {"failures": 0, "total_requests": 0, "avg_latency": 0}}, f)

    @classmethod
    def log_event(cls, event_type: str, metadata: Dict[str, Any]):
        cls._ensure_log_exists()
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "metadata": metadata
        }
        
        try:
            with open(cls.LOG_PATH, "r") as f:
                log = json.load(f)
            
            log["events"].append(event)
            log["stats"]["total_requests"] += 1
            if event_type == "ERROR":
                log["stats"]["failures"] += 1
            
            # Keep log size manageable (last 1000 events)
            if len(log["events"]) > 1000:
                log["events"] = log["events"][-1000:]
                
            with open(cls.LOG_PATH, "w") as f:
                json.dump(log, f, indent=2)
        except Exception as e:
            logger.error(f"Telemetry logging failed: {e}")

    @classmethod
    def track_latency(cls, endpoint: str, start_time: float):
        duration = time.time() - start_time
        cls.log_event("LATENCY", {"endpoint": endpoint, "duration_ms": round(duration * 1000, 2)})

    @classmethod
    def track_score_drift(cls, case_id: str, old_score: float, new_score: float, reason: str):
        """Tracks significant changes in case scores to detect logic instability."""
        cls.log_event("SCORE_DRIFT", {
            "case_id": case_id,
            "delta": round(new_score - old_score, 2),
            "reason": reason
        })

    @classmethod
    def get_health_stats(cls) -> Dict[str, Any]:
        cls._ensure_log_exists()
        try:
            with open(cls.LOG_PATH, "r") as f:
                log = json.load(f)
                return log.get("stats", {})
        except:
            return {"status": "ERROR_READING_LOG"}

# Global Instance
telemetry = TelemetryManager()
