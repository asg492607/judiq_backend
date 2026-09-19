"""
JudiQ AI — Deprecated Firebase Integration Shim
-----------------------------------------------
Firebase has been fully migrated to Supabase (PostgreSQL + Supabase Auth).
This module is retained purely as a backwards-compatible, no-op stub.
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("JudiQ.Firebase")


class FirebaseManager:
    """No-op stub for backwards-compatibility after Supabase migration."""
    _initialized: bool = True
    _firestore_client = None
    _is_available: bool = False

    @classmethod
    def initialize(cls):
        return None

    @classmethod
    def is_configured(cls) -> bool:
        return False

    @classmethod
    def save_user_profile(cls, *args, **kwargs) -> bool:
        return True

    @classmethod
    def get_user_profile(cls, *args, **kwargs) -> Optional[Dict[str, Any]]:
        return None

    @classmethod
    def save_case_analysis(cls, *args, **kwargs) -> bool:
        return True

    @classmethod
    def get_case_analysis(cls, *args, **kwargs) -> Optional[Dict[str, Any]]:
        return None

    @classmethod
    def list_user_cases(cls, *args, **kwargs) -> List[Dict[str, Any]]:
        return []

    @classmethod
    def save_case_version(cls, *args, **kwargs) -> bool:
        return True

    @classmethod
    def get_case_versions(cls, *args, **kwargs) -> List[Dict[str, Any]]:
        return []

    @classmethod
    def get_case_version(cls, *args, **kwargs) -> Optional[Dict[str, Any]]:
        return None
