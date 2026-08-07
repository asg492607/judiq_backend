"""
Root shim for backward compatibility. Delegates to criminal package.
"""
from criminal.criminal_economics_engine import CriminalEconomicsEngine

__all__ = ["CriminalEconomicsEngine"]
