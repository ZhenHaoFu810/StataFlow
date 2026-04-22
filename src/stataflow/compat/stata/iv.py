"""Stata IV command wrappers."""

from __future__ import annotations

from typing import Optional

from stataflow.estimators import IV2SLS, IVAbsorbingOLS
from stataflow.compat.stata.factor_variables import expand_factor_terms, parse_absorb


def ivregress_2sls(
    data,
    y: str,
    x_exog: list[str],
    x_endog: list[str],
    instruments: list[str],
    *,
    vce: str = "ols",
    cluster: Optional[str] = None,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``ivregress 2sls``.

    Maps to :class:`stataflow.estimators.IV2SLS`.
    """
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    data_exog, x_exog_exp = expand_factor_terms(data, x_exog)
    data_endog, x_endog_exp = expand_factor_terms(data_exog, x_endog)
    data_inst, instruments_exp = expand_factor_terms(data_endog, instruments)

    model = IV2SLS(
        data=data_inst,
        y=y,
        x_exog=x_exog_exp,
        x_endog=x_endog_exp,
        instruments=instruments_exp,
        missing=missing,
    )
    return model.fit(vce=vce, cluster=cluster)


def ivreghdfe(
    data,
    y: str,
    x_exog: list[str],
    x_endog: list[str],
    instruments: list[str],
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
    Stata-compatible wrapper for ``ivreghdfe``.

    Maps to :class:`stataflow.estimators.IVAbsorbingOLS`.

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

    data_exog, x_exog_exp = expand_factor_terms(data, x_exog)
    data_endog, x_endog_exp = expand_factor_terms(data_exog, x_endog)
    data_inst, instruments_exp = expand_factor_terms(data_endog, instruments)
    absorb_vars = parse_absorb(absorb)

    model = IVAbsorbingOLS(
        data=data_inst,
        y=y,
        x_exog=x_exog_exp,
        x_endog=x_endog_exp,
        instruments=instruments_exp,
        absorb=absorb_vars,
        add_constant=not noconstant,
        missing=missing,
        drop_singletons=not keepsingletons,
    )
    return model.fit(vce=vce, cluster=cluster)
