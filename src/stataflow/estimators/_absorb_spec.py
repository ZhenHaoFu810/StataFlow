"""AbsorbSpec dataclass to avoid circular imports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AbsorbSpec:
    """Structured specification for an absorbed fixed-effect group.

    Attributes
    ----------
    var : str
        Categorical variable identifying the FE group.
    slopes : list[str]
        Continuous slope variable names (empty = intercept only).
    has_intercept : bool
        Whether to absorb an intercept (group mean) in addition to slopes.
    """
    var: str
    slopes: list[str]
    has_intercept: bool = True
