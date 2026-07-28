"""Shared value formatting for text and HTML result renderers."""

from __future__ import annotations

import math
from typing import Any


def is_missing(value: Any) -> bool:
    """Return whether a display value is absent or non-finite."""
    if value is None:
        return True
    try:
        return not math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def format_number(value: Any, decimals: int = 6) -> str:
    """Format a numeric value using compact Stata-like conventions."""
    if is_missing(value):
        return "."
    number = float(value)
    magnitude = abs(number)
    if magnitude != 0 and (magnitude < 1e-4 or magnitude >= 1e7):
        return f"{number:.3e}"
    return f"{number:.{decimals}f}"


def format_integer(value: Any) -> str:
    """Format a count or integer-like statistic."""
    if is_missing(value):
        return "."
    return f"{int(float(value)):,}"


def format_pvalue(value: Any) -> str:
    """Format a p-value without turning a small nonzero value into zero."""
    if is_missing(value):
        return "."
    number = float(value)
    if 0 < number < 0.0001:
        return f"{number:.3e}"
    return f"{number:.4f}"


def format_bool(value: bool | None) -> str:
    """Format a tri-state boolean."""
    if value is None:
        return "."
    return "Yes" if value else "No"
