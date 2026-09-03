"""
JudiQ AI Civil & Commercial Litigation Engine Package
=====================================================
Comprehensive litigation intelligence for Code of Civil Procedure (1908),
Commercial Courts Act (2015), Specific Relief Act (1963), and Limitation Act (1963).
"""

from civil.civil_engine import CivilEngine
from civil.civil_scoring_engine import CivilScoringEngine
from civil.cpc_statutory_rules import CPCStatutoryRules
from civil.civil_suit_classifier import CivilSuitClassifier
from civil.injunction_evaluator import InjunctionEvaluator
from civil.civil_defence_catalogue import CivilDefenceCatalogue
from civil.specific_performance_engine import SpecificPerformanceEngine
from civil.order37_summary_suit_engine import Order37SummarySuitEngine
from civil.civil_statutory_drafter import CivilStatutoryDrafter

__all__ = [
    "CivilEngine",
    "CivilScoringEngine",
    "CPCStatutoryRules",
    "CivilSuitClassifier",
    "InjunctionEvaluator",
    "CivilDefenceCatalogue",
    "SpecificPerformanceEngine",
    "Order37SummarySuitEngine",
    "CivilStatutoryDrafter"
]
