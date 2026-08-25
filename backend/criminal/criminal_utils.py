"""
Shared utility functions for the Criminal Engine package.
Avoids duplication of _is_true / _is_false across multiple modules.
"""
from typing import Any


def _is_true(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    if isinstance(val, str):
        val_lower = val.strip().lower()
        return val_lower in ("true", "yes", "1") or val_lower.startswith("yes") or "violation" in val_lower or "unlawful" in val_lower or "missing" in val_lower or "without" in val_lower
    return False


def _is_false(val: Any) -> bool:
    if isinstance(val, bool):
        return not val
    if isinstance(val, str):
        val_lower = val.strip().lower()
        return val_lower in ("false", "no", "0") or val_lower.startswith("no") or "not applicable" in val_lower or "not arrested" in val_lower
    return False
