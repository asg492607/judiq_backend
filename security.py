# pyrefly: ignore [missing-import]
import jwt
import logging
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

from config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM  = settings.ALGORITHM

class SecurityManager:
    """
    Enterprise Security Manager â€” Handles JWT governance, session integrity,
    and audit log generation.
    """
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=60)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT Token expired.")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT Token.")
            return None

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7) # Default 7 days
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                logger.warning("Invalid token type for refresh.")
                return None
            
            # Create new access token
            user_data = {"sub": payload.get("sub")}
            return SecurityManager.create_access_token(user_data)
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired. User must re-login.")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid refresh token.")
            return None

class AuditLogger:
    """
    Captures every system interaction for institutional accountability.
    """
    @staticmethod
    def log_interaction(user_id: str, case_id: str, action: str, metadata: dict = None):
        def redact_identifier(value: str) -> str:
            if not value or value in {"ANONYMOUS", "PENDING", "THREAT"}:
                return value
            return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": redact_identifier(user_id),
            "case_id": case_id,
            "action": action,
            "metadata": metadata or {}
        }
        if os.getenv("ENABLE_FIREBASE_AUDIT", "false").lower() != "true":
            logger.debug("[AUDIT] Firebase persistence disabled.")
            return

        try:
            import firebase_admin
            from firebase_admin import firestore
            
            if not firebase_admin._apps:
                # Assumes GOOGLE_APPLICATION_CREDENTIALS is set
                firebase_admin.initialize_app()
                
            db = firestore.client()
            db.collection("audit_logs").add(log_entry)
            logger.info("[AUDIT] Interaction persisted to Firebase.")
        except ImportError:
            logger.warning("Firebase audit enabled but firebase_admin is not installed.")
        except Exception as e:
            logger.warning(f"Audit persistence to Firebase skipped/failed: {e}")

class SecurityTelemetry:
    """
    Analyzes incoming payloads for basic threats and anomalies.
    """
    @staticmethod
    def audit_payload(payload: dict) -> list:
        # Stub implementation for threat detection
        threats = []
        # Add basic threat detection if necessary in the future
        return threats
