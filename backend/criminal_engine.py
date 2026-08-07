"""
Root shim for backward compatibility. Delegates to criminal package.
"""
from criminal.criminal_engine import CriminalEngine

__all__ = ["CriminalEngine"]
