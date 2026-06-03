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
    cluster: Optional[str | list[str]] = None,
    aweight: Optional[str] = None,
    noconstant: bool = False,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``regress``.

    Maps to :class:`stataflow.estimators.OLS`.
    """
    # Parse Stata-style vce(cluster var) syntax
    if vce is not None and vce.startswith("cluster "):
        cluster = vce.split(" ", 1)[1]
        vce = "cluster"

    # Handle known Stata options
    alpha = 0.05
    if "level" in kwargs:
        level = kwargs.pop("level")
        alpha = 1.0 - level / 100.0
    for known_unsupported in ("beta", "eform"):
        if known_unsupported in kwargs:
            kwargs.pop(known_unsupported)
            raise NotImplementedError(
                f"'{known_unsupported}' is not yet supported by the regress wrapper."
            )
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
    return model.fit(vce=vce, cluster=cluster, alpha=alpha)


def xtreg_fe(
    data,
    y: str,
    x: list[str],
    *,
    fe: str,
    vce: str = "ols",
    cluster: Optional[str | list[str]] = None,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``xtreg, fe``.

    Maps to :class:`stataflow.estimators.FixedEffectsOLS`.
    """
    if vce is not None and vce.startswith("cluster "):
        cluster = vce.split(" ", 1)[1]
        vce = "cluster"

    alpha = 0.05
    if "level" in kwargs:
        level = kwargs.pop("level")
        alpha = 1.0 - level / 100.0
    for known_unsupported in ("beta", "eform"):
        if known_unsupported in kwargs:
            kwargs.pop(known_unsupported)
            raise NotImplementedError(
                f"'{known_unsupported}' is not yet supported by the xtreg_fe wrapper."
            )
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")
    if isinstance(cluster, list):
        raise ValueError(
            "Multi-way clustering is only supported for regress. "
            "xtreg_fe currently supports a single cluster variable (str)."
        )

    data_expanded, x_expanded = expand_factor_terms(data, x)

    model = FixedEffectsOLS(
        data=data_expanded,
        y=y,
        x=x_expanded,
        fe=fe,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster, alpha=alpha)


def areg(
    data,
    y: str,
    x: list[str],
    *,
    absorb: str,
    vce: str = "ols",
    cluster: Optional[str | list[str]] = None,
    noconstant: bool = False,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``areg``.

    Maps to :class:`stataflow.estimators.AbsorbingOLS` with a single
    absorption variable.
    """
    if vce is not None and vce.startswith("cluster "):
        cluster = vce.split(" ", 1)[1]
        vce = "cluster"

    alpha = 0.05
    if "level" in kwargs:
        level = kwargs.pop("level")
        alpha = 1.0 - level / 100.0
    for known_unsupported in ("beta", "eform"):
        if known_unsupported in kwargs:
            kwargs.pop(known_unsupported)
            raise NotImplementedError(
                f"'{known_unsupported}' is not yet supported by the areg wrapper."
            )
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")
    if isinstance(cluster, list):
        raise ValueError(
            "Multi-way clustering is only supported for regress. "
            "areg currently supports a single cluster variable (str)."
        )

    data_expanded, x_expanded = expand_factor_terms(data, x)
    absorb_parsed = parse_absorb(absorb)
    if len(absorb_parsed) > 1:
        raise ValueError("areg supports only a single absorb variable")

    model = AbsorbingOLS(
        data=data_expanded,
        y=y,
        x=x_expanded,
        absorb=absorb_parsed[0],
        add_constant=not noconstant,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster, alpha=alpha)
