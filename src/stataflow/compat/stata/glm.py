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
    aweight: Optional[str] = None,
    noconstant: bool = False,
    or_: bool = False,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``logit``.

    Maps to :class:`stataflow.estimators.Logit`.

    Parameters
    ----------
    or_ : bool
        Report odds ratios (``eform`` alias for logit).
    """
    eform = or_
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_expanded, x_expanded = expand_factor_terms(data, x)

    weights = data[aweight].values if aweight is not None else None
    model = Logit(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
        weights=weights,
    )
    return model.fit(vce=vce, cluster=cluster, eform=eform)


def probit(
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
    Stata-compatible wrapper for ``probit``.

    Maps to :class:`stataflow.estimators.Probit`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_expanded, x_expanded = expand_factor_terms(data, x)

    weights = data[aweight].values if aweight is not None else None
    model = Probit(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
        weights=weights,
    )
    return model.fit(vce=vce, cluster=cluster)


def poisson(
    data,
    y: str,
    x: list[str],
    *,
    vce: str = "ols",
    cluster: Optional[str] = None,
    aweight: Optional[str] = None,
    noconstant: bool = False,
    exposure: Optional[str] = None,
    offset: Optional[str] = None,
    irr: bool = False,
    eform: bool = False,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``poisson``.

    Maps to :class:`stataflow.estimators.Poisson`.

    Parameters
    ----------
    irr : bool
        Report incidence-rate ratios (``eform`` alias).
    eform : bool
        Report exponentiated coefficients.
    """
    eform = eform or irr
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    if exposure is not None:
        raise NotImplementedError("exposure is not yet supported in stataflow.poisson")
    if offset is not None:
        raise NotImplementedError("offset is not yet supported in stataflow.poisson")

    data_expanded, x_expanded = expand_factor_terms(data, x)

    weights = data[aweight].values if aweight is not None else None
    model = Poisson(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
        weights=weights,
    )
    return model.fit(vce=vce, cluster=cluster, eform=eform)
