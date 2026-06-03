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
    cluster: Optional[str | list[str]] = None,
    missing: str = "drop",
    keepsingletons: bool = False,
    noconstant: bool = False,
    savefe: bool = False,
    timevar: Optional[str] = None,
    technique: Optional[str] = None,
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``reghdfe``.

    Maps to :class:`stataflow.estimators.AbsorbingOLS`.

    Parameters
    ----------
    vce : str
        Variance estimator: "ols", "robust", "cluster", or "dkraay".
    cluster : str | list[str], optional
        Cluster variable(s) (required when vce="cluster").
        Supports 1-way or 2-way clustering.
    timevar : str, optional
        Time variable name (required when vce="dkraay").
    keepsingletons : bool
        If True, do not drop singleton observations (Stata ``keepsingletons``).
    noconstant : bool
        If True, omit the constant term (Stata ``noconstant``).
    technique : str, optional
        Solver technique: "auto", "map", or "lsdv".  Defaults to "auto".
    """
    # Parse Stata-style vce(cluster var) syntax
    if vce is not None and vce.startswith('cluster '):
        cluster = vce.split(' ', 1)[1]
        vce = 'cluster'

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
        technique=technique if technique is not None else "auto",
    )
    return model.fit(vce=vce, cluster=cluster, savefe=savefe, timevar=timevar)


def ppmlhdfe(
    data,
    y: str,
    x: list[str],
    *,
    absorb: str | list[str],
    vce: str = "robust",
    cluster: Optional[str | list[str]] = None,
    missing: str = "drop",
    offset: Optional[str] = None,
    exposure: Optional[str] = None,
    noconstant: bool = False,
    maxiter: int = 100,
    tolerance: float = 1e-8,
    eform: bool = False,
    separation: Optional[str] = None,
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
        separation=separation,
    )
    return model.fit(vce=vce, cluster=cluster, eform=eform)
