"""Postestimation helpers for predict and margins."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm as norm_dist
from types import SimpleNamespace
from typing import Optional


def _build_design_matrix(df: pd.DataFrame, x_vars: list[str], add_constant: bool) -> np.ndarray:
    """Build design matrix from dataframe."""
    cols = [df[v].values.astype(np.float64) for v in x_vars]
    if add_constant:
        cols.append(np.ones(len(df)))
    return np.column_stack(cols)


def predict_xb(beta: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Linear predictor xb = X @ beta."""
    return X @ beta


def predict_residuals(y: np.ndarray, xb: np.ndarray) -> np.ndarray:
    """Residuals = y - xb."""
    return y - xb


def margins_ame_linear(beta: np.ndarray) -> np.ndarray:
    """AME for linear model: just beta."""
    return beta.copy()


def margins_ame_logit(beta: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    AME and Jacobian for logit.

    Returns
    -------
    ame : np.ndarray
        Average marginal effects (K,).
    J : np.ndarray
        Jacobian matrix (K, K).
    """
    xb = X @ beta
    p = 1.0 / (1.0 + np.exp(-xb))
    p = np.clip(p, 1e-15, 1 - 1e-15)
    dp = p * (1.0 - p)
    k = len(beta)
    ame = beta * dp.mean()
    J = np.zeros((k, k))
    for j in range(k):
        J[:, j] = beta * (X[:, j] * dp * (1.0 - 2.0 * p)).mean()
        J[j, j] += dp.mean()
    return ame, J


def margins_mem_logit(beta: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """MEM and Jacobian for logit."""
    xbar = X.mean(axis=0)
    xb_bar = float(xbar @ beta)
    p_bar = 1.0 / (1.0 + np.exp(-xb_bar))
    p_bar = np.clip(p_bar, 1e-15, 1 - 1e-15)
    dp_bar = p_bar * (1.0 - p_bar)
    mem = beta * dp_bar
    k = len(beta)
    J = np.zeros((k, k))
    for j in range(k):
        J[:, j] = beta * xbar[j] * dp_bar * (1.0 - 2.0 * p_bar)
        J[j, j] += dp_bar
    return mem, J


def margins_ame_probit(beta: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """AME and Jacobian for probit."""
    from scipy.stats import norm
    xb = X @ beta
    phi = norm.pdf(xb)
    k = len(beta)
    ame = beta * phi.mean()
    J = np.zeros((k, k))
    for j in range(k):
        J[:, j] = beta * (X[:, j] * phi * (-xb)).mean()
        J[j, j] += phi.mean()
    return ame, J


def margins_mem_probit(beta: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """MEM and Jacobian for probit."""
    from scipy.stats import norm
    xbar = X.mean(axis=0)
    xb_bar = float(xbar @ beta)
    phi_bar = norm.pdf(xb_bar)
    mem = beta * phi_bar
    k = len(beta)
    J = np.zeros((k, k))
    for j in range(k):
        J[:, j] = beta * xbar[j] * phi_bar * (-xb_bar)
        J[j, j] += phi_bar
    return mem, J


def margins_ame_poisson(beta: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """AME and Jacobian for poisson."""
    xb = X @ beta
    mu = np.exp(xb)
    k = len(beta)
    ame = beta * mu.mean()
    J = np.zeros((k, k))
    for j in range(k):
        J[:, j] = beta * (X[:, j] * mu).mean()
        J[j, j] += mu.mean()
    return ame, J


def margins_mem_poisson(beta: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """MEM and Jacobian for poisson."""
    xbar = X.mean(axis=0)
    xb_bar = float(xbar @ beta)
    mu_bar = np.exp(xb_bar)
    mem = beta * mu_bar
    k = len(beta)
    J = np.zeros((k, k))
    for j in range(k):
        J[:, j] = beta * xbar[j] * mu_bar
        J[j, j] += mu_bar
    return mem, J


def _build_margins_result(
    effects: np.ndarray,
    J: np.ndarray,
    cov_beta: np.ndarray,
    coef_names: list[str],
    nobs: int,
) -> SimpleNamespace:
    """Build margins result object with delta-method standard errors.

    Stata's margins, dydx(*) does not report marginal effects for the constant term.
    We drop _cons here if present.
    """
    effects = np.asarray(effects)
    J = np.asarray(J)
    cov_beta = np.asarray(cov_beta)

    names = list(coef_names)
    if "_cons" in names:
        cons_idx = names.index("_cons")
        names.pop(cons_idx)
        effects = np.delete(effects, cons_idx, axis=0)
        J = np.delete(np.delete(J, cons_idx, axis=0), cons_idx, axis=1)
        cov_beta = np.delete(np.delete(cov_beta, cons_idx, axis=0), cons_idx, axis=1)

    V_margins = J @ cov_beta @ J.T
    se = np.sqrt(np.maximum(np.diag(V_margins), 0.0))
    z = effects / se
    pvalues = 2 * (1.0 - norm_dist.cdf(np.abs(z)))
    ci_low = effects - 1.96 * se
    ci_high = effects + 1.96 * se

    return SimpleNamespace(
        params={name: float(effects[i]) for i, name in enumerate(names)},
        bse={name: float(se[i]) for i, name in enumerate(names)},
        tvalues={name: float(z[i]) for i, name in enumerate(names)},
        pvalues={name: float(pvalues[i]) for i, name in enumerate(names)},
        conf_int={name: (float(ci_low[i]), float(ci_high[i])) for i, name in enumerate(names)},
        nobs=nobs,
    )
