import logging
from typing import Dict, Type, Optional, List
from core.base_domain_engine import BaseDomainEngine

logger = logging.getLogger(__name__)

class CaseRegistry:
    """
    Central Registry pattern managing domain engine registrations and routing.
    Eliminates ad-hoc if/elif branching in central orchestrators.
    """

    def __init__(self):
        self._engines: Dict[str, BaseDomainEngine] = {}

    def register(self, domain_key: str, engine_instance: BaseDomainEngine) -> None:
        key = domain_key.lower().strip()
        self._engines[key] = engine_instance
        logger.info(f"[CASE_REGISTRY] Registered domain engine '{engine_instance.domain_name}' under key '{key}'.")

    def get(self, case_type: str) -> Optional[BaseDomainEngine]:
        key = (case_type or "").lower().strip()
        if key in self._engines:
            return self._engines[key]
        # Fallback aliases
        if key in ("cheque bounce", "cheque_bounce", "ni_act", "section_138"):
            return self._engines.get("cheque_bounce")
        if key in ("sarfaesi", "drt", "securitisation"):
            return self._engines.get("sarfaesi")
        return None

    def list_registered_domains(self) -> List[str]:
        return list(self._engines.keys())

case_registry = CaseRegistry()
