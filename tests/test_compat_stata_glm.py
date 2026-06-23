"""Tests for compat.stata GLM wrappers."""

import warnings

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import logit, probit, poisson
from stataflow.estimators import Logit, Probit, Poisson


def _make_binary_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = 0.5 + 1.0 * x1 - 0.5 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def _make_count_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = 0.5 + 0.3 * x1 - 0.2 * x2
    mu = np.exp(lp)
    y = rng.poisson(mu)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def test_logit_delegation():
    df = _make_binary_data()
    res = logit(df, y="y", x=["x1", "x2"])
    direct = Logit(df, y="y", x=["x1", "x2"]).fit()
    assert res.model.command == "logit"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_logit_noconstant():
    df = _make_binary_data()
    res = logit(df, y="y", x=["x1", "x2"], noconstant=True)
    names = [c.name for c in res.coefficients]
    assert "_cons" not in names


def test_logit_unsupported_kwargs():
    df = _make_binary_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        logit(df, y="y", x=["x1"], foo=True)


@pytest.mark.parametrize("wrapper,data_factory", [
    (logit, _make_binary_data),
    (probit, _make_binary_data),
    (poisson, _make_count_data),
])
def test_stata_glm_wrappers_reject_aweights(wrapper, data_factory):
    """Official Stata GLM commands reject analytic weights with r(101)."""
    df = data_factory()
    df["w"] = 1.0

    with pytest.raises(ValueError, match="aweights not allowed"):
        wrapper(df, y="y", x=["x1"], aweight="w")


def test_logit_wrapper_has_no_postestimation_methods():
    df = _make_binary_data()
    res = logit(df, y="y", x=["x1", "x2"])
    assert hasattr(res, "predict")
    assert not hasattr(res, "margins")


def test_logit_robust_vce_uses_stata_small_sample_adjustment():
    df = _make_binary_data(n=60, seed=123)
    model = Logit(df, y="y", x=["x1", "x2"])
    res = model.fit(vce="robust")

    X = model._design_matrix
    y = model._dep_var
    mu = model._mu
    eta = model._eta
    gprime = model._link_deriv(eta, mu)
    var = model._variance(mu)
    w = np.clip(1.0 / (var * gprime ** 2), 1e-12, 1e12)
    Xw = X * np.sqrt(w)[:, np.newaxis]
    bread = np.linalg.inv(Xw.T @ Xw)
    residuals = y - mu
    meat = (X * residuals[:, np.newaxis]).T @ (X * residuals[:, np.newaxis])
    unadjusted = bread @ meat @ bread
    n_adj = len(y) / (len(y) - 1)

    assert np.allclose(np.asarray(res.variance.values), n_adj * unadjusted, rtol=1e-12, atol=1e-12)


def test_logit_cluster_vce_uses_mle_cluster_adjustment():
    df = _make_binary_data(n=90, seed=321)
    df["group"] = np.repeat(np.arange(15), 6)
    model = Logit(df, y="y", x=["x1", "x2"])
    res = model.fit(vce="cluster", cluster="group")

    X = model._design_matrix
    y = model._dep_var
    mu = model._mu
    eta = model._eta
    groups = df["group"].to_numpy()
    gprime = model._link_deriv(eta, mu)
    var = model._variance(mu)
    w = np.clip(1.0 / (var * gprime ** 2), 1e-12, 1e12)
    Xw = X * np.sqrt(w)[:, np.newaxis]
    bread = np.linalg.inv(Xw.T @ Xw)
    residuals = y - mu
    meat = np.zeros((X.shape[1], X.shape[1]))
    for group in np.unique(groups):
        mask = groups == group
        score_g = X[mask].T @ residuals[mask]
        meat += np.outer(score_g, score_g)
    g_adj = len(np.unique(groups)) / (len(np.unique(groups)) - 1)

    assert np.allclose(np.asarray(res.variance.values), g_adj * bread @ meat @ bread, rtol=1e-12, atol=1e-12)


def test_logit_cluster_keeps_residual_df_and_reports_wald_chi2():
    """Clustered Stata logit stores N-k df and a slope Wald chi-squared."""
    rng = np.random.default_rng(2025061203)
    n = 90
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    result = Logit(df, y="y", x=["x1", "x2"]).fit(vce="robust")

    assert result.fit.df_resid == 87
    assert result.fit.f_stat == pytest.approx(5.6847833, rel=1e-6)


def test_logit_complete_separation_fails_without_numeric_warnings():
    """Complete prediction is diagnosed before unstable IRLS iterations."""
    df = pd.DataFrame({
        "y": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
        "x": [-2.0, -1.0, -0.1, 0.1, 1.0, 2.0],
    })

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(RuntimeError, match="predicts data perfectly"):
            Logit(df, y="y", x=["x"]).fit()

    assert caught == []


def test_probit_delegation():
    df = _make_binary_data()
    res = probit(df, y="y", x=["x1", "x2"])
    direct = Probit(df, y="y", x=["x1", "x2"]).fit()
    assert res.model.command == "probit"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_probit_unsupported_kwargs():
    df = _make_binary_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        probit(df, y="y", x=["x1"], scores=True)


def test_probit_wrapper_has_no_postestimation_methods():
    df = _make_binary_data()
    res = probit(df, y="y", x=["x1", "x2"])
    assert hasattr(res, "predict")
    assert not hasattr(res, "margins")


def test_probit_cluster_vce_uses_mle_cluster_adjustment():
    df = _make_binary_data(n=90, seed=654)
    df["group"] = np.repeat(np.arange(15), 6)
    model = Probit(df, y="y", x=["x1", "x2"])
    res = model.fit(vce="cluster", cluster="group")

    from scipy.stats import norm

    X = model._design_matrix
    y = model._dep_var
    mu = np.clip(model._mu, 1e-15, 1 - 1e-15)
    eta = model._eta
    groups = df["group"].to_numpy()
    beta = model._beta

    def _score(b):
        et = X @ b
        m = np.clip(norm.cdf(et), 1e-15, 1 - 1e-15)
        ph = norm.pdf(et)
        return X.T @ (ph * (y - m) / (m * (1 - m)))

    eps = 1e-7
    H = np.zeros((X.shape[1], X.shape[1]))
    for j in range(X.shape[1]):
        bp = beta.copy()
        bp[j] += eps
        bm = beta.copy()
        bm[j] -= eps
        H[:, j] = (_score(bp) - _score(bm)) / (2 * eps)
    bread = np.linalg.inv(-H)

    phi = norm.pdf(eta)
    meat = np.zeros((X.shape[1], X.shape[1]))
    for group in np.unique(groups):
        mask = groups == group
        score_g = X[mask].T @ (phi[mask] * (y[mask] - mu[mask]) / (mu[mask] * (1 - mu[mask])))
        meat += np.outer(score_g, score_g)
    g_adj = len(np.unique(groups)) / (len(np.unique(groups)) - 1)

    assert np.allclose(np.asarray(res.variance.values), g_adj * bread @ meat @ bread, rtol=1e-12, atol=1e-12)


def test_poisson_delegation():
    df = _make_count_data()
    res = poisson(df, y="y", x=["x1", "x2"])
    direct = Poisson(df, y="y", x=["x1", "x2"]).fit()
    assert res.model.command == "poisson"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_poisson_offset_not_implemented():
    df = _make_count_data()
    df["off"] = np.ones(len(df))
    with pytest.raises(NotImplementedError, match="offset is not yet supported"):
        poisson(df, y="y", x=["x1"], offset="off")


def test_poisson_exposure_not_implemented():
    df = _make_count_data()
    df["exp"] = np.ones(len(df))
    with pytest.raises(NotImplementedError, match="exposure is not yet supported"):
        poisson(df, y="y", x=["x1"], exposure="exp")


def test_poisson_unsupported_kwargs():
    df = _make_count_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        poisson(df, y="y", x=["x1"], foo=True)


def test_poisson_wrapper_has_no_postestimation_methods():
    df = _make_count_data()
    res = poisson(df, y="y", x=["x1", "x2"])
    assert hasattr(res, "predict")
    assert not hasattr(res, "margins")


def test_poisson_robust_vce_uses_stata_small_sample_adjustment():
    df = _make_count_data(n=80, seed=456)
    model = Poisson(df, y="y", x=["x1", "x2"])
    res = model.fit(vce="robust")

    X = model._design_matrix
    y = model._dep_var
    mu = model._mu
    eta = model._eta
    gprime = model._link_deriv(eta, mu)
    var = model._variance(mu)
    w = np.clip(1.0 / (var * gprime ** 2), 1e-12, 1e12)
    Xw = X * np.sqrt(w)[:, np.newaxis]
    bread = np.linalg.inv(Xw.T @ Xw)
    residuals = y - mu
    meat = (X * residuals[:, np.newaxis]).T @ (X * residuals[:, np.newaxis])
    unadjusted = bread @ meat @ bread
    n_adj = len(y) / (len(y) - 1)

    assert np.allclose(np.asarray(res.variance.values), n_adj * unadjusted, rtol=1e-12, atol=1e-12)


def test_poisson_cluster_vce_uses_mle_cluster_adjustment():
    df = _make_count_data(n=90, seed=987)
    df["group"] = np.repeat(np.arange(15), 6)
    model = Poisson(df, y="y", x=["x1", "x2"])
    res = model.fit(vce="cluster", cluster="group")

    X = model._design_matrix
    y = model._dep_var
    mu = model._mu
    eta = model._eta
    groups = df["group"].to_numpy()
    gprime = model._link_deriv(eta, mu)
    var = model._variance(mu)
    w = np.clip(1.0 / (var * gprime ** 2), 1e-12, 1e12)
    Xw = X * np.sqrt(w)[:, np.newaxis]
    bread = np.linalg.inv(Xw.T @ Xw)
    residuals = y - mu
    meat = np.zeros((X.shape[1], X.shape[1]))
    for group in np.unique(groups):
        mask = groups == group
        score_g = X[mask].T @ residuals[mask]
        meat += np.outer(score_g, score_g)
    g_adj = len(np.unique(groups)) / (len(np.unique(groups)) - 1)

    assert np.allclose(np.asarray(res.variance.values), g_adj * bread @ meat @ bread, rtol=1e-12, atol=1e-12)


def test_logit_empty_x_no_constant_raises():
    """Logit with empty x and no constant should raise ValueError."""
    df = pd.DataFrame({"y": [0.0, 1.0], "x": [1.0, 2.0]})
    with pytest.raises(ValueError, match="0 columns"):
        Logit(df, "y", [], add_constant=False).fit()


def test_logit_single_cluster_rejected():
    """VCE-001: single cluster must be rejected for logit."""
    df = pd.DataFrame({
        "y": [0, 1, 0, 1, 0, 1],
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "clust": [1, 1, 1, 1, 1, 1],
    })
    with pytest.raises(ValueError, match="at least 2 clusters"):
        logit(df, y="y", x=["x"], vce="cluster", cluster="clust")


def test_poisson_single_cluster_rejected():
    """VCE-001: single cluster must be rejected for poisson."""
    df = pd.DataFrame({
        "y": [1, 2, 0, 3, 1, 2],
        "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "clust": [1, 1, 1, 1, 1, 1],
    })
    with pytest.raises(ValueError, match="at least 2 clusters"):
        poisson(df, y="y", x=["x"], vce="cluster", cluster="clust")
