"""Shared DID treatment-time unit validation (Wave 14 / AUDIT-015 / ISSUE-013).

Rejects relative cohort encodings paired with calendar time without rejecting
valid future cohorts or skipped calendar periods that Stata accepts.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def validate_treatment_time_units(
    time: pd.Series | np.ndarray,
    first_treat: pd.Series | np.ndarray,
    *,
    never_is_missing: bool = True,
    command: str = "did_imputation",
) -> None:
    """Raise ``ValueError`` when treatment and time are on incompatible scales.

    Parameters
    ----------
    time
        Observed calendar or period index values.
    first_treat
        Cohort / first-treatment variable. For ``did_imputation``, never-treated
        units are missing; for ``csdid``, never-treated units are coded 0.
    never_is_missing
        If True, finite values identify treated cohorts. If False (CSDID),
        values ``> 0`` identify treated cohorts.
    command
        Command name for error messages.
    """
    t = pd.to_numeric(pd.Series(time), errors="coerce").to_numpy(dtype=float)
    c = pd.to_numeric(pd.Series(first_treat), errors="coerce").to_numpy(dtype=float)

    t_ok = t[np.isfinite(t)]
    if t_ok.size == 0:
        raise ValueError(f"{command}: no finite values in time variable")

    if never_is_missing:
        treated = c[np.isfinite(c)]
    else:
        treated = c[np.isfinite(c) & (c > 0)]

    if treated.size == 0:
        raise ValueError(
            f"{command}: no treated cohorts found in first_treat/gvar "
            f"(after applying never-treated coding). "
            f"Observed time range is [{float(np.min(t_ok))}, {float(np.max(t_ok))}]."
        )

    t_min = float(np.min(t_ok))
    t_max = float(np.max(t_ok))
    c_min = float(np.min(treated))
    c_max = float(np.max(treated))
    time_span = t_max - t_min
    looks_calendar_time = abs(t_min) >= 50.0

    # A single valid calendar cohort must not hide a relative-period value.
    # Allow nearby pre-sample calendar cohorts, but reject values separated
    # from the observed support by far more than the panel span.
    if looks_calendar_time:
        scale_gap = max(2.0 * max(time_span, 1.0), 10.0)
        incompatible = treated < (t_min - scale_gap)
        if np.any(incompatible):
            bad_min = float(np.min(treated[incompatible]))
            bad_max = float(np.max(treated[incompatible]))
            raise ValueError(
                f"{command}: first_treat/gvar appears to use different units than time "
                f"(incompatible cohorts in [{bad_min:g}, {bad_max:g}], time in "
                f"[{t_min:g}, {t_max:g}]). Use the same units as time "
                f"(e.g. calendar year of first treatment, not relative event time)."
            )

    # Relative cohort + calendar time: all treated cohorts strictly below the
    # observed time floor, while cohorts look like small event-time indices
    # relative to the time support (AUDIT-015 / ISSUE-013).
    # Valid future cohorts have c_max > t_max or c_max >= t_min with calendar scale.
    if c_max < t_min:
        looks_relative = (time_span >= 0) and (c_max <= max(time_span, 1.0) * 2.0 + 1.0)
        # Also catch calendar time with large absolute levels (years).
        if looks_relative and looks_calendar_time:
            raise ValueError(
                f"{command}: first_treat/gvar appears to use different units than time "
                f"(treated cohorts in [{c_min:g}, {c_max:g}], time in "
                f"[{t_min:g}, {t_max:g}]). Use the same units as time "
                f"(e.g. calendar year of first treatment, not relative event time)."
            )
        # Pure relative panel (time starts near 0) with future-only cohorts is OK
        # only when time is also on a small relative scale.
        if looks_relative and not looks_calendar_time and c_max < t_min:
            # e.g. time 10..20 and cohort 5 is still scale mismatch
            if t_min > c_max + max(time_span, 1.0):
                raise ValueError(
                    f"{command}: first_treat/gvar appears to use different units than time "
                    f"(treated cohorts in [{c_min:g}, {c_max:g}], time in "
                    f"[{t_min:g}, {t_max:g}]). Use the same units as time."
                )


def assert_nonempty_did_fit(
    *,
    nobs: int,
    coefficients: list,
    command: str = "did_imputation",
    att_dict: Optional[dict] = None,
    require_effects: bool = True,
) -> None:
    """Reject zero-information successful fits (Wave 14 Task 6 / AC3).

    A successful fit must have positive estimation-sample ``nobs`` and a nonempty
    finite effect surface: either a nonempty ``att_dict`` (CSDID group-time ATT)
    or a nonempty coefficient list with at least one finite beta
    (``did_imputation``). True-null zero betas are allowed; empty surfaces are not.

    Scale-mismatch coding is handled by :func:`validate_treatment_time_units`.
    """
    if nobs is None or nobs <= 0:
        raise ValueError(
            f"{command}: estimation produced N=0; check sample screening and "
            f"treatment-time coding (first_treat/gvar must use the same units as time)."
        )
    if not require_effects:
        return
    if att_dict is not None:
        if not att_dict:
            raise ValueError(
                f"{command}: estimation produced no group-time ATT cells. "
                f"Check that first_treat/gvar uses the same units as time and that "
                f"at least one post-treatment cell is estimable."
            )
        # Require at least one finite ATT value in the surface.
        finite_att = False
        for val in att_dict.values():
            beta = val[0] if isinstance(val, (tuple, list)) else val
            if np.isfinite(beta):
                finite_att = True
                break
        if not finite_att:
            raise ValueError(
                f"{command}: estimation produced no finite group-time ATT values."
            )
        return
    if not coefficients:
        raise ValueError(
            f"{command}: estimation produced no coefficients. "
            f"Check treatment-time coding and that treated post-periods exist."
        )
    finite = [row for row in coefficients if np.isfinite(getattr(row, "beta", np.nan))]
    if not finite:
        raise ValueError(
            f"{command}: all coefficients are non-finite. "
            f"Check treatment-time coding (same units as time)."
        )
