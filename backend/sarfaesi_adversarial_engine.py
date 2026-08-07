"""
Root shim for backward compatibility. Delegates to sarfaesi package.
"""
from sarfaesi.sarfaesi_adversarial_engine import SarfaesiAdversarialEngine

__all__ = ["SarfaesiAdversarialEngine"]
