"""Stata linear regression command wrappers."""

from __future__ import annotations

from typing import Optional

from stataflow.estimators import OLS, FixedEffectsOLS, AbsorbingOLS
from stataflow.compat.stata.factor_variables import expand_factor_terms, parse_absorb


def regress(
    data,
    y: str,
    x: list[str],
    *,
    vce: str = "ols",
    cluster: Optional[str] = None,
    aweight: Optional[str] = None,
    noconstant: bool = False,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``regress``.

    Maps to :class:`stataflow.estimators.OLS`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    weight_type = None
    weights = None
    if aweight is not None:
        weight_type = "aweight"
        weights = data[aweight].values

    data_expanded, x_expanded = expand_factor_terms(data, x)

    model = OLS(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        weights=weights,
        weight_type=weight_type,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster)


def xtreg_fe(
    data,
    y: str,
    x: list[str],
    *,
    fe: str,
    vce: str = "ols",
    cluster: Optional[str] = None,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``xtreg, fe``.

    Maps to :class:`stataflow.estimators.FixedEffectsOLS`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_expanded, x_expanded = expand_factor_terms(data, x)

    model = FixedEffectsOLS(
        data=data_expanded,
        y=y,
        x=x_expanded,
        fe=fe,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster)


def areg(
    data,
    y: str,
    x: list[str],
    *,
    absorb: str,
    vce: str = "ols",
    cluster: Optional[str] = None,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``areg``.

    Maps to :class:`stataflow.estimators.AbsorbingOLS` with a single
    absorption variable.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_expanded, x_expanded = expand_factor_terms(data, x)
    absorb_parsed = parse_absorb(absorb)
    if len(absorb_parsed) > 1:
        raise ValueError("areg supports only a single absorb variable")

    model = AbsorbingOLS(
        data=data_expanded,
        y=y,
        x=x_expanded,
        absorb=absorb_parsed[0],
        add_constant=True,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster)
