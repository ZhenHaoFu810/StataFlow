"""Stata GLM command wrappers."""

from __future__ import annotations

from typing import Optional

from stataflow.estimators import Logit, Probit, Poisson
from stataflow.compat.stata.factor_variables import (
    expand_factor_terms,
    get_underlying_vars,
    restore_factor_omitted_rows,
)


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
    if aweight is not None:
        raise ValueError("aweights not allowed by Stata's logit command")
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    screen_vars = [y]
    for term in x:
        screen_vars.extend(get_underlying_vars(term))
    if cluster is not None:
        screen_vars.append(cluster)
    data_expanded, x_expanded = expand_factor_terms(data, x, screen_vars=list(dict.fromkeys(screen_vars)))

    model = Logit(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
    )
    return restore_factor_omitted_rows(
        model.fit(vce=vce, cluster=cluster, eform=eform), data_expanded
    )


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
    if aweight is not None:
        raise ValueError("aweights not allowed by Stata's probit command")
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    screen_vars = [y]
    for term in x:
        screen_vars.extend(get_underlying_vars(term))
    if cluster is not None:
        screen_vars.append(cluster)
    data_expanded, x_expanded = expand_factor_terms(data, x, screen_vars=list(dict.fromkeys(screen_vars)))

    model = Probit(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
    )
    return restore_factor_omitted_rows(
        model.fit(vce=vce, cluster=cluster), data_expanded
    )


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
    if aweight is not None:
        raise ValueError("aweights not allowed by Stata's poisson command")
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    if exposure is not None:
        raise NotImplementedError("exposure is not yet supported in stataflow.poisson")
    if offset is not None:
        raise NotImplementedError("offset is not yet supported in stataflow.poisson")

    screen_vars = [y]
    for term in x:
        screen_vars.extend(get_underlying_vars(term))
    if cluster is not None:
        screen_vars.append(cluster)
    data_expanded, x_expanded = expand_factor_terms(data, x, screen_vars=list(dict.fromkeys(screen_vars)))

    model = Poisson(
        data=data_expanded,
        y=y,
        x=x_expanded,
        add_constant=not noconstant,
        missing=missing,
    )
    return restore_factor_omitted_rows(
        model.fit(vce=vce, cluster=cluster, eform=eform), data_expanded
    )
