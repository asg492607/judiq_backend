"""
JudiQ AI Criminal Law Engine Package
===================================
Comprehensive criminal law analytics, statutory rule evaluation,
adversarial stress-testing, bail assessment, quashing viability,
and defense trial strategy. Supports both legacy framework (IPC/CrPC/IEA)
and Bharatiya Nyaya Sanhita framework (BNS/BNSS/BSA).
"""

from criminal.criminal_engine import CriminalEngine
from criminal.criminal_scoring_engine import CriminalScoringEngine
from criminal.criminal_adversarial_engine import CriminalAdversarialEngine
from criminal.criminal_rules_engine import CriminalRulesEngine
from criminal.criminal_timeline_engine import CriminalTimelineEngine
from criminal.criminal_economics_engine import CriminalEconomicsEngine
from criminal.router import router

__all__ = [
    "CriminalEngine",
    "CriminalScoringEngine",
    "CriminalAdversarialEngine",
    "CriminalRulesEngine",
    "CriminalTimelineEngine",
    "CriminalEconomicsEngine",
    "router"
]
