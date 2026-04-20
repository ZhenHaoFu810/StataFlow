"""Stata HDFE command wrappers."""

from __future__ import annotations

from typing import Optional

from stataflow.estimators import AbsorbingOLS, PPMLHDFE
from stataflow.compat.stata.factor_variables import expand_factor_terms, parse_absorb


def reghdfe(
    data,
    y: str,
    x: list[str],
    *,
    absorb: str | list[str],
    vce: str = "ols",
    cluster: Optional[str] = None,
    missing: str = "drop",
    keepsingletons: bool = False,
    noconstant: bool = False,
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``reghdfe``.

    Maps to :class:`stataflow.estimators.AbsorbingOLS`.

    Parameters
    ----------
    vce : str
        Variance estimator: "ols", "robust", or "cluster".
    cluster : str, optional
        Cluster variable (required when vce="cluster").
    keepsingletons : bool
        If True, do not drop singleton observations (Stata ``keepsingletons``).
    noconstant : bool
        If True, omit the constant term (Stata ``noconstant``).
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_expanded, x_expanded = expand_factor_terms(data, x)
    absorb_vars = parse_absorb(absorb)

    model = AbsorbingOLS(
        data=data_expanded,
        y=y,
        x=x_expanded,
        absorb=absorb_vars,
        add_constant=not noconstant,
        missing=missing,
        drop_singletons=not keepsingletons,
    )
    return model.fit(vce=vce, cluster=cluster)


def ppmlhdfe(
    data,
    y: str,
    x: list[str],
    *,
    absorb: str | list[str],
    vce: str = "robust",
    cluster: Optional[str] = None,
    missing: str = "drop",
    offset: Optional[str] = None,
    exposure: Optional[str] = None,
    noconstant: bool = False,
    maxiter: int = 100,
    tolerance: float = 1e-8,
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``ppmlhdfe``.

    Maps to :class:`stataflow.estimators.PPMLHDFE`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_expanded, x_expanded = expand_factor_terms(data, x)
    absorb_vars = parse_absorb(absorb)

    model = PPMLHDFE(
        data=data_expanded,
        y=y,
        x=x_expanded,
        absorb=absorb_vars,
        add_constant=not noconstant,
        missing=missing,
        offset=offset,
        exposure=exposure,
        max_iter=maxiter,
        tol=tolerance,
    )
    return model.fit(vce=vce, cluster=cluster)
