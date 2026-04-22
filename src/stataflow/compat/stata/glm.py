"""Stata GLM command wrappers."""

from __future__ import annotations

from typing import Optional

from stataflow.estimators import Logit, Probit, Poisson
from stataflow.compat.stata.factor_variables import expand_factor_terms


def logit(
    data,
    y: str,
    x: list[str],
    *,
    vce: str = "ols",
    cluster: Optional[str] = None,
    noconstant: bool = False,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``logit``.

    Maps to :class:`stataflow.estimators.Logit`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_expanded, x_expanded = expand_factor_terms(data, x)

    model = Logit(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster)


def probit(
    data,
    y: str,
    x: list[str],
    *,
    vce: str = "ols",
    cluster: Optional[str] = None,
    noconstant: bool = False,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``probit``.

    Maps to :class:`stataflow.estimators.Probit`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_expanded, x_expanded = expand_factor_terms(data, x)

    model = Probit(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster)


def poisson(
    data,
    y: str,
    x: list[str],
    *,
    vce: str = "ols",
    cluster: Optional[str] = None,
    noconstant: bool = False,
    exposure: Optional[str] = None,
    offset: Optional[str] = None,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``poisson``.

    Maps to :class:`stataflow.estimators.Poisson`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    if exposure is not None:
        raise NotImplementedError("exposure is not yet supported in stataflow.poisson")
    if offset is not None:
        raise NotImplementedError("offset is not yet supported in stataflow.poisson")

    data_expanded, x_expanded = expand_factor_terms(data, x)

    model = Poisson(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster)
