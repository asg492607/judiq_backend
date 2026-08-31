import uuid
from datetime import datetime
from session import DatabaseManager
import logging

logger = logging.getLogger("judiq.audit")

class AuditService:
    @staticmethod
    def log(user_id: str, action: str, entity_type: str = None, entity_id: str = None,
            case_id: str = None, before_state: dict = None, after_state: dict = None,
            ip_address: str = None, user_agent: str = None, note: str = None) -> bool:
        """
        Record an immutable audit log entry into audit_log_v2.
        """
        try:
            log_id = f"LOG-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            return DatabaseManager.cms_log_audit(
                log_id=log_id,
                user_id=user_id or "ANONYMOUS",
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                case_id=case_id,
                before_state=before_state,
                after_state=after_state,
                ip_address=ip_address,
                user_agent=user_agent,
                note=note
            )
        except Exception as e:
            logger.error(f"AuditService failed to log action '{action}': {e}")
            return False

    @staticmethod
    def get_case_trail(case_id: str, limit: int = 100):
        return DatabaseManager.cms_get_audit_trail(case_id=case_id, limit=limit)

    @staticmethod
    def get_user_trail(user_id: str, limit: int = 100):
        return DatabaseManager.cms_get_audit_trail(user_id=user_id, limit=limit)

    @staticmethod
    def get_recent_trail(limit: int = 100):
        return DatabaseManager.cms_get_audit_trail(limit=limit)
