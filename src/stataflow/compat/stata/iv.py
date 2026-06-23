"""Stata IV command wrappers."""

from __future__ import annotations

from typing import Optional

from stataflow.estimators import IV2SLS, IVAbsorbingOLS
from stataflow.compat.stata.factor_variables import (
    expand_factor_terms,
    get_underlying_vars,
    parse_absorb,
    restore_factor_omitted_rows,
)


def ivregress_2sls(
    data,
    y: str,
    x_exog: list[str],
    x_endog: list[str],
    instruments: list[str],
    *,
    vce: str = "ols",
    cluster: Optional[str] = None,
    noconstant: bool = False,
    first: bool = False,
    missing: str = "drop",
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``ivregress 2sls``.

    Maps to :class:`stataflow.estimators.IV2SLS`.
    """
    # Parse Stata-style vce(cluster var) syntax
    if vce is not None and vce.startswith('cluster '):
        cluster = vce.split(' ', 1)[1]
        vce = 'cluster'
    # Map HC subtypes: hc1 is alias for robust; hc2/hc3 not yet implemented
    vce_lower = (vce or "").lower()
    if vce_lower == "hc1":
        vce = "robust"
    elif vce_lower in ("hc2", "hc3"):
        raise NotImplementedError(f"vce({vce}) is not yet supported. Use 'robust' or 'cluster'.")

    for known_unsupported in ("level", "beta", "eform"):
        if known_unsupported in kwargs:
            kwargs.pop(known_unsupported)
            raise NotImplementedError(
                f"'{known_unsupported}' is not yet supported by the ivregress_2sls wrapper."
            )
    for known_unimplemented in ("orthog", "endogtest", "redundant", "partial", "fwl", "wmatrix", "ffirst"):
        if known_unimplemented in kwargs:
            kwargs.pop(known_unimplemented)
            raise NotImplementedError(
                f"'{known_unimplemented}' is not yet supported by the ivreghdfe wrapper."
            )
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    screen_vars = [y]
    for term in x_exog + x_endog + instruments:
        screen_vars.extend(get_underlying_vars(term))
    if cluster is not None:
        screen_vars.append(cluster)
    screen_vars = list(dict.fromkeys(screen_vars))
    data_exog, x_exog_exp = expand_factor_terms(data, x_exog, screen_vars=screen_vars)
    data_endog, x_endog_exp = expand_factor_terms(data_exog, x_endog, screen_vars=screen_vars)
    coefficient_layout = list(data_endog.attrs.get("stataflow_factor_result_layout", []))
    data_inst, instruments_exp = expand_factor_terms(data_endog, instruments, screen_vars=screen_vars)
    data_inst.attrs["stataflow_factor_result_layout"] = coefficient_layout

    model = IV2SLS(
        data=data_inst,
        y=y,
        x_exog=x_exog_exp,
        x_endog=x_endog_exp,
        instruments=instruments_exp,
        add_constant=not noconstant,
        missing=missing,
    )
    return restore_factor_omitted_rows(
        model.fit(vce=vce, cluster=cluster, first=first), data_inst
    )


def ivreghdfe(
    data,
    y: str,
    x_exog: list[str],
    x_endog: list[str],
    instruments: list[str],
    *,
    absorb: str | list[str],
    vce: str = "ols",
    cluster: Optional[str | list[str]] = None,
    missing: str = "drop",
    keepsingletons: bool = False,
    noconstant: bool = False,
    first: bool = False,
    estimator: str = "2sls",
    fuller: float = 0.0,
    kclass: float | None = None,
    **kwargs,
) -> object:
    """
    Stata-compatible wrapper for ``ivreghdfe``.

    Maps to :class:`stataflow.estimators.IVAbsorbingOLS`.

    Parameters
    ----------
    vce : str
        Variance estimator: "ols", "robust", or "cluster".
    cluster : str | list[str], optional
        Cluster variable(s) (required when vce="cluster").
        Supports 1-way or 2-way clustering.
    keepsingletons : bool
        If True, do not drop singleton observations (Stata ``keepsingletons``).
    noconstant : bool
        If True, omit the constant term (Stata ``noconstant``).
    first : bool
        If True, compute and return first-stage diagnostics.
    estimator : str
        Estimator type: "2sls", "gmm2s", or "liml".
    fuller : float
        Fuller adjustment parameter for LIML (default 0).
    kclass : float, optional
        User-specified k-class parameter for LIML.
    """
    for known_unsupported in ("level", "beta", "eform"):
        if known_unsupported in kwargs:
            kwargs.pop(known_unsupported)
            raise NotImplementedError(
                f"'{known_unsupported}' is not yet supported by the ivreghdfe wrapper."
            )
    for known_unimplemented in ("orthog", "endogtest", "redundant", "partial", "fwl", "wmatrix", "ffirst"):
        if known_unimplemented in kwargs:
            kwargs.pop(known_unimplemented)
            raise NotImplementedError(
                f"'{known_unimplemented}' is not yet supported by the ivreghdfe wrapper."
            )
    if kwargs:
        raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")

    # Parse Stata-style vce(cluster var) syntax
    if vce is not None and vce.startswith('cluster '):
        cluster = vce.split(' ', 1)[1]
        vce = 'cluster'
    # Map HC subtypes: hc1 is alias for robust; hc2/hc3 not yet implemented
    vce_lower = (vce or "").lower()
    if vce_lower == "hc1":
        vce = "robust"
    elif vce_lower in ("hc2", "hc3"):
        raise NotImplementedError(f"vce({vce}) is not yet supported. Use 'robust' or 'cluster'.")

    # Support Stata-style space-separated cluster variables
    if isinstance(cluster, str) and ' ' in cluster:
        cluster = [c.strip() for c in cluster.split()]

    absorb_vars = parse_absorb(absorb)
    screen_vars = [y]
    for term in x_exog + x_endog + instruments:
        screen_vars.extend(get_underlying_vars(term))
    if cluster is not None:
        if isinstance(cluster, str):
            screen_vars.append(cluster)
        else:
            screen_vars.extend(cluster)
    for spec in absorb_vars:
        screen_vars.append(spec.var)
        for s in spec.slopes:
            screen_vars.append(s)
    screen_vars = list(dict.fromkeys(screen_vars))
    data_exog, x_exog_exp = expand_factor_terms(data, x_exog, screen_vars=screen_vars)
    data_endog, x_endog_exp = expand_factor_terms(data_exog, x_endog, screen_vars=screen_vars)
    coefficient_layout = list(data_endog.attrs.get("stataflow_factor_result_layout", []))
    data_inst, instruments_exp = expand_factor_terms(data_endog, instruments, screen_vars=screen_vars)
    data_inst.attrs["stataflow_factor_result_layout"] = coefficient_layout

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
    return restore_factor_omitted_rows(
        model.fit(
            vce=vce,
            cluster=cluster,
            first=first,
            estimator=estimator,
            fuller=fuller,
            kclass=kclass,
        ),
        data_inst,
    )
