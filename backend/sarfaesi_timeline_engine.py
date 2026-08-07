"""
Root shim for backward compatibility. Delegates to sarfaesi package.
"""
from sarfaesi.sarfaesi_timeline_engine import SarfaesiTimelineEngine

__all__ = ["SarfaesiTimelineEngine"]
