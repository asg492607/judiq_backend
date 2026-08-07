"""
Root shim for backward compatibility. Delegates to criminal package.
"""
from criminal.criminal_adversarial_engine import CriminalAdversarialEngine

__all__ = ["CriminalAdversarialEngine"]
