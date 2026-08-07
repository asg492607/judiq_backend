"""
Root shim for backward compatibility. Delegates to criminal package.
"""
from criminal.criminal_scoring_engine import CriminalScoringEngine

__all__ = ["CriminalScoringEngine"]
