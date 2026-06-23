"""Stata-compatible wrapper for rdrobust (sharp RD with bandwidth selection and covariates)."""

from __future__ import annotations

import pandas as pd

from stataflow.estimators.rdrobust import RDRobust
from stataflow.results.result import (
    ResultSchema,
)


def rdrobust(
    data: pd.DataFrame,
    y: str,
    x: str,
    c: float = 0.0,
    h: float | tuple[float, float] | None = None,
    b: float | tuple[float, float] | None = None,
    p: int = 1,
    q: int = 2,
    deriv: int = 0,
    kernel: str = "triangular",
    vce: str = "nn",
    nnmatch: int = 3,
    level: int = 95,
    bwselect: str | None = None,
    covs: list[str] | str | None = None,
    covs_drop: bool = True,
    scaleregul: float = 1.0,
    masspoints: str = "adjust",
    bwcheck: int = 0,
    weights: str | None = None,
    fuzzy: str | None = None,
    sharpbw: bool = False,
    cluster: str | None = None,
    **kwargs,
) -> ResultSchema:
    """
    Stata-compatible wrapper for sharp Regression Discontinuity estimation.

    Parameters
    ----------
    data : pd.DataFrame
    y : str
        Outcome variable.
    x : str
        Running variable.
    c : float, default 0.0
        Cutoff.
    h : float or tuple[float, float] or None
        Main bandwidth(s). If provided, overrides bwselect.
    b : float or tuple[float, float] or None
        Bias bandwidth(s). Defaults to h if None.
    p : int, default 1
        Polynomial order for point estimation.
    q : int, default 2
        Polynomial order for bias correction.
    deriv : int, default 0
        Derivative order (only 0 supported).
    kernel : str, default "triangular"
    vce : str, default "nn"
        Variance estimator: "nn", "hc0", "cluster", or "nncluster".
    nnmatch : int, default 3
        Minimum neighbors for nn VCE.
    level : int, default 95
        Confidence level.
    bwselect : str or None
        Bandwidth selector. Supported: "mserd", "msesum", "msetwo",
        "msecomb1", "msecomb2", "cerrd", "cersum", "certwo",
        "cercomb1", "cercomb2". Ignored if h is provided.
    covs : list[str] or str or None
        Covariate variable name(s).
    covs_drop : bool, default True
        Drop collinear covariates.
    scaleregul : float, default 1.0
        Regularization scaling for bandwidth selectors.
    masspoints : str, default "adjust"
        Mass points handling: "adjust", "check", or "off".
    bwcheck : int, default 0
        Minimum unique observations within bandwidth window.
    weights : str or None
        Frequency weight variable name.
    fuzzy : str or None
        Fuzzy RD treatment variable name.
    sharpbw : bool, default False
        Use sharp bandwidth selection for fuzzy RD.
    cluster : str or None
        Cluster variable name for vce="cluster" or vce="nncluster".

    Returns
    -------
    ResultSchema
    """
    if kwargs:
        # Hard-reject unsupported parameters explicitly
        unsupported = set(kwargs.keys())
        raise ValueError(
            f"Unsupported arguments for rdrobust wrapper: {sorted(unsupported)}"
        )

    model = RDRobust(
        data=data,
        y=y,
        x=x,
        c=c,
        h=h,
        b=b,
        p=p,
        q=q,
        deriv=deriv,
        kernel=kernel,
        vce=vce,
        nnmatch=nnmatch,
        level=level,
        bwselect=bwselect,
        covs=covs,
        covs_drop=covs_drop,
        scaleregul=scaleregul,
        masspoints=masspoints,
        bwcheck=bwcheck,
        weights=weights,
        fuzzy=fuzzy,
        sharpbw=sharpbw,
        cluster=cluster,
    )
    return model.fit()
