# pyrefly: ignore [missing-import]
import jwt
import logging
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
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "case_id": case_id,
            "action": action,
            "metadata": metadata or {}
        }
        # Write to Firebase Firestore for audit tracking
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            if not firebase_admin._apps:
                # Assumes GOOGLE_APPLICATION_CREDENTIALS is set
                firebase_admin.initialize_app()
                
            db = firestore.client()
            db.collection("audit_logs").add(log_entry)
            logger.info(f"[AUDIT] Successfully logged to Firebase: {log_entry}")
        except ImportError:
            logger.error("firebase_admin not installed. Audit persistence failed.")
        except Exception as e:
            logger.error(f"Audit persistence to Firebase failed: {e}")

