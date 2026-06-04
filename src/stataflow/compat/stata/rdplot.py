"""Stata-compatible wrapper for rdplot (RD visualization companion)."""

from __future__ import annotations

import warnings

import pandas as pd

from stataflow.estimators.rdplot import RDPlot


def rdplot(
    data: pd.DataFrame,
    y: str,
    x: str,
    c: float = 0.0,
    p: int = 4,
    nbins: tuple[int, int] | int | None = None,
    binselect: str = "esmv",
    kernel: str = "uniform",
    h: float | tuple[float, float] | None = None,
    covs: list[str] | str | None = None,
    **kwargs,
) -> dict:
    """
    Stata-compatible wrapper for RD plot companion command.

    Parameters
    ----------
    data : pd.DataFrame
    y : str
        Outcome variable.
    x : str
        Running variable.
    c : float, default 0.0
        Cutoff.
    p : int, default 4
        Polynomial order for local polynomial fit.
    nbins : tuple[int, int] or int or None
        Manual bin counts (left, right) or single count for both sides.
    binselect : str, default "esmv"
        Bin selection method. Supported: "esmv", "qsmv".
    kernel : str, default "uniform"
        Kernel for local polynomial fit.
    h : float or tuple[float, float] or None
        Bandwidth for polynomial fit. If None, uses data range.
    covs : list[str] or str or None
        Covariate variable name(s).

    Returns
    -------
    dict
        Dictionary with keys:
        - "bins": pd.DataFrame with bin statistics (mean_x, mean_y, se_y, N)
        - "fit": pd.DataFrame with local polynomial fit coordinates
        - "info": dict with metadata (N_l, N_r, J_star_l, J_star_r, etc.)
    """
    if kwargs:
        unsupported = set(kwargs.keys())
        raise ValueError(
            f"Unsupported arguments for rdplot wrapper: {sorted(unsupported)}"
        )

    if covs is not None:
        warnings.warn(
            "covs() option is meant to be used when plotting RDROBUST estimates. "
            "If the option is used for global polynomial fitting, it may deliver "
            "results that are not visually compatible with the local binned means "
            "depicted due to the underlying assumptions used.",
            UserWarning,
            stacklevel=2,
        )

    model = RDPlot(
        data=data,
        y=y,
        x=x,
        c=c,
        p=p,
        nbins=nbins,
        binselect=binselect,
        kernel=kernel,
        h=h,
        covs=covs,
    )
    return model.fit()
