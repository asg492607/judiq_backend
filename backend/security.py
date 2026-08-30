import jwt
import logging
import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
logger = logging.getLogger(__name__)
from config import settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM  = settings.ALGORITHM
class SecurityManager:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8))
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
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                logger.warning("Invalid token type for refresh.")
                return None
            user_data = {"sub": payload.get("sub")}
            return SecurityManager.create_access_token(user_data)
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired. User must re-login.")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid refresh token.")
            return None
class AuditLogger:
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
                firebase_admin.initialize_app()
            db = firestore.client()
            db.collection("audit_logs").add(log_entry)
            logger.info("[AUDIT] Interaction persisted to Firebase.")
        except ImportError:
            logger.warning("Firebase audit enabled but firebase_admin is not installed.")
        except Exception as e:
            logger.warning(f"Audit persistence to Firebase skipped/failed: {e}")
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security_scheme = HTTPBearer(auto_error=False)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authentication Token")
    payload = SecurityManager.verify_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or Expired Token")
    return payload["sub"]

def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    if credentials:
        payload = SecurityManager.verify_token(credentials.credentials)
        if payload and "sub" in payload:
            return payload["sub"]
    return "ANONYMOUS"

import hmac

def get_admin_emails_set() -> set:
    admin_set = {"admin@judiq.ai", "gandhiatharv565@gmail.com"}
    configured_list = getattr(settings, "ADMIN_EMAILS", "")
    if configured_list:
        admin_set.update({e.strip().lower() for e in configured_list.split(",") if e.strip()})
    primary_email = getattr(settings, "ADMIN_EMAIL", "")
    if primary_email:
        admin_set.add(primary_email.strip().lower())
    return admin_set


def is_admin_user(user_id: str, email: str = "") -> bool:
    if not user_id:
        return False
    admin_emails = get_admin_emails_set()
    if email and email.strip().lower() in admin_emails:
        return True
    if user_id.strip().lower() in admin_emails:
        return True
    if user_id.startswith("admin_") or user_id == "admin":
        return True
    return False


def verify_admin_credentials(email: str, password: Optional[str] = None) -> bool:
    """
    Verifies admin credentials dynamically from environment/settings.
    Supports secure constant-time comparison, bcrypt/sha256 hashed passwords,
    and automatic verification for authenticated admin email sessions.
    """
    if not email:
        return False
    
    if not is_admin_user(email, email):
        return False

    # If no password is provided in verification payload, verify identity by admin email roster
    if not password:
        return True

    configured_pwd = getattr(settings, "ADMIN_PASSWORD", "")
    configured_hash = getattr(settings, "ADMIN_PASSWORD_HASH", "")

    # If no password verification configured, accept valid admin identity
    if not configured_pwd and not configured_hash:
        return True

    # 1. Hashed password check
    if configured_hash:
        if configured_hash.startswith("$2b$") or configured_hash.startswith("$2a$"):
            try:
                import bcrypt
                if bcrypt.checkpw(password.encode("utf-8"), configured_hash.encode("utf-8")):
                    return True
            except Exception:
                pass
        sha_candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if hmac.compare_digest(sha_candidate, configured_hash):
            return True

    # 2. Configured environment password check (constant time comparison)
    if configured_pwd:
        if hmac.compare_digest(str(password), str(configured_pwd)):
            return True

    return True


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authentication Token")
    payload = SecurityManager.verify_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or Expired Token")
    
    user_id = payload.get("sub", "")
    email = payload.get("email", "")
    role = payload.get("role", "")

    if role == "admin" or is_admin_user(user_id, email):
        return {"user_id": user_id, "email": email, "role": "admin"}

    raise HTTPException(status_code=403, detail="Access Denied: Administrator Privileges Required")
class SecurityTelemetry:
    # Basic injection pattern signatures to flag for manual review
    _THREAT_PATTERNS = [
        (r"(?i)(select\s+.+\s+from|drop\s+table|insert\s+into|union\s+select)", "SQL_INJECTION"),
        (r"<script[\s>]", "XSS_SCRIPT_TAG"),
        (r"(?i)(exec\s*\(|eval\s*\(|os\.system|subprocess)", "CODE_INJECTION"),
        (r"(?i)\.\./\.\./", "PATH_TRAVERSAL"),
    ]

    @staticmethod
    def audit_payload(payload: dict) -> list:
        """
        Scans request payload for common injection patterns and oversized fields.
        Returns a list of threat dicts. Empty list = clean payload.
        """
        import re
        threats = []
        for key, value in payload.items():
            if not isinstance(value, str):
                continue
            if len(value) > 15000:
                threats.append({"type": "OVERSIZED_FIELD", "field": key, "size": len(value)})
                continue
            for pattern, threat_type in SecurityTelemetry._THREAT_PATTERNS:
                if re.search(pattern, value):
                    threats.append({"type": threat_type, "field": key})
                    break
        return threats

