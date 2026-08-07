"""
Root shim for backward compatibility. Delegates to criminal package.
"""
from criminal.criminal_rules_engine import CriminalRulesEngine

__all__ = ["CriminalRulesEngine"]
