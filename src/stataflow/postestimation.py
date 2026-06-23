"""Postestimation helpers for predict, margins, and estat."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm as norm_dist
from types import SimpleNamespace
from typing import Any


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


def estat_summarize(result: Any, data: pd.DataFrame, variables: list[str] | None = None, dep_var: str | None = None) -> dict[str, dict[str, float]]:
    """
    Post-estimation summary statistics aligned with Stata ``estat summarize``.

    Parameters
    ----------
    result : ResultSchema
        Fitted result object with ``sample.sample_mask`` attribute.
    data : pd.DataFrame
        Original dataframe.
    variables : list[str], optional
        Variables to summarize. Defaults to dependent variable + all regressors.
    dep_var : str, optional
        Name of the dependent variable. If provided and not already in variables, prepended.

    Returns
    -------
    dict mapping variable name to {'N', 'mean', 'sd', 'min', 'max'}.
    """
    mask = getattr(getattr(result, "sample", None), "sample_mask", None)
    if mask is None:
        mask = pd.Series(True, index=data.index)

    if variables is None:
        # Extract variable names from coefficients list
        coefs = getattr(result, "coefficients", [])
        variables = [c.name for c in coefs if c.name != "_cons"]

    if dep_var is not None and dep_var not in variables:
        variables = [dep_var] + variables

    summary: dict[str, dict[str, float]] = {}
    for var in variables:
        if var not in data.columns:
            continue
        vals = data.loc[mask, var].dropna()
        if len(vals) == 0:
            continue
        summary[var] = {
            "N": float(len(vals)),
            "mean": float(vals.mean()),
            "sd": float(vals.std(ddof=1)),
            "min": float(vals.min()),
            "max": float(vals.max()),
        }
    return summary


def estat_vce(result: Any) -> np.ndarray | None:
    """
    Return the variance-covariance matrix of reported coefficients.
    Aligned with Stata ``estat vce``.
    """
    variance = getattr(result, "variance", None)
    if variance is None:
        return None
    values = getattr(variance, "values", None)
    if values is None:
        return None
    return np.asarray(values)


def estat_ic(result: Any) -> dict[str, float]:
    """
    Information criteria aligned with Stata ``estat ic``.

    Returns AIC and BIC. For models without log-likelihood, returns empty dict.
    """
    ll = getattr(getattr(result, "fit", None), "ll", None)
    if ll is None or np.isnan(ll):
        return {}

    nobs = getattr(getattr(result, "sample", None), "nobs", 0)
    df_model = getattr(getattr(result, "fit", None), "df_model", 0)
    # Stata counts k = df_model + 1 when constant is present
    # For GLM, df_model already excludes constant; add 1 if has_constant
    has_constant = getattr(getattr(result, "fit", None), "has_constant", None)
    if has_constant is None:
        has_constant = getattr(getattr(result, "model", None), "has_constant", False)
    k = df_model + (1 if has_constant else 0)

    aic = -2.0 * ll + 2.0 * k
    bic = -2.0 * ll + k * np.log(nobs)
    return {
        "N": float(nobs),
        "ll": float(ll),
        "k": float(k),
        "aic": float(aic),
        "bic": float(bic),
    }


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


def apply_discrete_changes(
    beta: np.ndarray,
    X: np.ndarray,
    effects: np.ndarray,
    J: np.ndarray,
    discrete_indices: list[int],
    inverse_link,
    inverse_link_derivative,
    atmeans: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Replace derivative effects with 0-to-1 changes for indicator columns."""
    if not discrete_indices:
        return effects, J

    evaluation = X.mean(axis=0, keepdims=True) if atmeans else X
    effects = effects.copy()
    J = J.copy()
    for index in discrete_indices:
        X0 = evaluation.copy()
        X1 = evaluation.copy()
        X0[:, index] = 0.0
        X1[:, index] = 1.0
        eta0 = X0 @ beta
        eta1 = X1 @ beta
        effects[index] = float(np.mean(inverse_link(eta1) - inverse_link(eta0)))
        gradient = (
            inverse_link_derivative(eta1)[:, np.newaxis] * X1
            - inverse_link_derivative(eta0)[:, np.newaxis] * X0
        )
        J[index, :] = gradient.mean(axis=0)
    return effects, J


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
        # The constant has no marginal effect to report, but uncertainty in
        # its estimate still contributes through the delta-method Jacobian.
        J = np.delete(J, cons_idx, axis=0)

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
