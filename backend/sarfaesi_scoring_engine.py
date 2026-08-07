"""
Root shim for backward compatibility. Delegates to sarfaesi package.
"""
from sarfaesi.sarfaesi_scoring_engine import SarfaesiScoringEngine

__all__ = ["SarfaesiScoringEngine"]
