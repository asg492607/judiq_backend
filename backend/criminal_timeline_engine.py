"""
Root shim for backward compatibility. Delegates to criminal package.
"""
from criminal.criminal_timeline_engine import CriminalTimelineEngine

__all__ = ["CriminalTimelineEngine"]
