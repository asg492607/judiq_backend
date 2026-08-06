from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseDomainEngine(ABC):
    """
    Abstract base contract for all domain-specific engines in JudiQ AI.
    Provides uniform lifecycle interface for case evaluation, procedural graphing,
    evidence auditing, next-best-action determination, and legal drafting.
    """

    @property
    @abstractmethod
    def domain_name(self) -> str:
        """Returns unique string identifier for the domain (e.g. 'sarfaesi', 'cheque_bounce')."""
        pass

    @abstractmethod
    def analyze(self, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Core evaluation method returning score, defects, verdict, strategy, and reasoning trace."""
        pass

    @abstractmethod
    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns stateful graph of statutory milestones with completion and defect status."""
        pass

    @abstractmethod
    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Returns prioritized, legally permissible next-best-actions for the user."""
        pass
