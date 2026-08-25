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
        if key in ("cheque bounce", "cheque_bounce", "ni_act", "section_138", "138 ni act"):
            return self._engines.get("cheque_bounce")
        if key in ("sarfaesi", "drt", "securitisation"):
            return self._engines.get("sarfaesi")
        if key in ("criminal", "ipc", "bns", "crpc", "bnss"):
            return self._engines.get("criminal")
        if key in ("civil", "cpc", "commercial"):
            return self._engines.get("civil")
        if key in ("composite", "multi_track", "multitrack", "composite_recovery", "unified_npa", "unified", "all"):
            return self._engines.get("composite")
        return None

    def list_registered_domains(self) -> List[str]:
        return list(self._engines.keys())

case_registry = CaseRegistry()

# Initialize built-in domain engines
try:
    from criminal.criminal_engine import CriminalEngine
    case_registry.register("criminal", CriminalEngine())
except Exception as _e:
    logger.warning(f"Could not auto-register CriminalEngine: {_e}")

try:
    from sarfaesi.sarfaesi_domain_engine import SarfaesiDomainEngine
    case_registry.register("sarfaesi", SarfaesiDomainEngine())
except Exception as _e:
    logger.warning(f"Could not auto-register SarfaesiDomainEngine: {_e}")

try:
    from cheque_bounce.cheque_bounce_engine import ChequeBounceEngine
    case_registry.register("cheque_bounce", ChequeBounceEngine())
except Exception as _e:
    logger.warning(f"Could not auto-register ChequeBounceEngine: {_e}")

try:
    from civil.civil_engine import CivilEngine
    case_registry.register("civil", CivilEngine())
except Exception as _e:
    logger.warning(f"Could not auto-register CivilEngine: {_e}")

try:
    from composite.unified_multitrack_engine import UnifiedMultiTrackEngine
    case_registry.register("composite", UnifiedMultiTrackEngine())
except Exception as _e:
    logger.warning(f"Could not auto-register UnifiedMultiTrackEngine: {_e}")

