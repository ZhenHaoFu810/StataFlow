"""Tests for compat.stata HDFE wrappers."""

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import reghdfe, ppmlhdfe
from stataflow.estimators import AbsorbingOLS, PPMLHDFE


def _make_hdfe_data(n=100, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "g1": rng.integers(0, 5, size=n),
        "g2": rng.integers(0, 5, size=n),
    })
    return df


def _make_ppml_data(n=100, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.poisson(2.0, size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "g1": rng.integers(0, 5, size=n),
        "g2": rng.integers(0, 5, size=n),
    })
    return df


def test_reghdfe_single_absorb():
    df = _make_hdfe_data()
    res = reghdfe(df, y="y", x=["x1", "x2"], absorb="g1")
    # reghdfe wrapper must enforce reghdfe semantics even for a single absorb variable
    assert res.model.command == "reghdfe"
    # Compare against AbsorbingOLS called with a list (reghdfe mode), not a string (areg mode)
    direct = AbsorbingOLS(df, y="y", x=["x1", "x2"], absorb=["g1"]).fit()
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
    assert np.isclose(res.fit.df_a, direct.fit.df_a, rtol=1e-10)


def test_reghdfe_multi_absorb():
    df = _make_hdfe_data()
    res = reghdfe(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"])
    direct = AbsorbingOLS(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"]).fit()
    assert res.model.command == "reghdfe"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_reghdfe_unsupported_kwargs():
    df = _make_hdfe_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        reghdfe(df, y="y", x=["x1"], absorb="g1", foo="bar")


def test_ppmlhdfe_delegation():
    df = _make_ppml_data()
    res = ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"])
    direct = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"]).fit()
    assert res.model.command == "ppmlhdfe"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_ppmlhdfe_unsupported_kwargs():
    df = _make_ppml_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        ppmlhdfe(df, y="y", x=["x1"], absorb="g1", foo="bar")


def test_ppmlhdfe_wrapper_has_no_postestimation_methods():
    df = _make_ppml_data()
    res = ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"])
    assert hasattr(res, "predict")
    assert not hasattr(res, "margins")


def test_ppmlhdfe_eform_preserves_raw_z_and_p_values():
    df = _make_ppml_data(n=150, seed=123)
    raw = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"]).fit(
        vce="robust"
    )
    eform = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"]).fit(
        vce="robust", eform=True
    )

    for raw_coef, eform_coef in zip(raw.coefficients, eform.coefficients):
        assert np.isclose(eform_coef.beta, np.exp(raw_coef.beta), rtol=1e-10)
        assert np.isclose(
            eform_coef.std_err,
            np.exp(raw_coef.beta) * raw_coef.std_err,
            rtol=1e-10,
        )
        assert np.isclose(eform_coef.t_stat, raw_coef.t_stat, rtol=1e-10)
        assert np.isclose(eform_coef.p_value, raw_coef.p_value, rtol=1e-10)


def test_ppmlhdfe_weighted_matches_unweighted_when_weights_unity():
    """Uniform weights should reproduce the unweighted result."""
    df = _make_ppml_data(n=150, seed=123)
    df["w"] = 1.0
    unweighted = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"]).fit(vce="robust")
    weighted = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"], weights="w").fit(vce="robust")
    for u, w in zip(unweighted.coefficients, weighted.coefficients):
        assert np.isclose(u.beta, w.beta, rtol=1e-10)
        assert np.isclose(u.std_err, w.std_err, rtol=1e-10)
    assert np.isclose(unweighted.fit.ll, weighted.fit.ll, rtol=1e-10)


def test_ppmlhdfe_wrapper_rejects_aweight():
    """The Stata ppmlhdfe command only accepts probability weights."""
    df = _make_ppml_data(n=150, seed=123)
    df["w"] = np.abs(np.random.default_rng(42).normal(1, 0.3, size=len(df)))

    with pytest.raises(ValueError, match="aweights not allowed"):
        ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"], aweight="w")


def test_ppmlhdfe_wrapper_pweight():
    """Probability weights are passed through to the PPML estimator."""
    df = _make_ppml_data(n=150, seed=123)
    df["w"] = np.abs(np.random.default_rng(42).normal(1, 0.3, size=len(df)))
    res = ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"], pweight="w")
    assert res.model.command == "ppmlhdfe"
    assert len(res.coefficients) > 0


def test_ppmlhdfe_xb_excludes_absorbed_effects():
    """Stata's predict, xb contains reported coefficients but no absorbed FE."""
    df = _make_ppml_data(n=150, seed=987)
    model = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"])
    result = model.fit(vce="robust")
    params = {row.name: row.beta for row in result.coefficients}

    expected = (
        df.loc[model._abs_ols._df.index, "x1"].to_numpy() * params["x1"]
        + df.loc[model._abs_ols._df.index, "x2"].to_numpy() * params["x2"]
        + params["_cons"]
    )

    assert np.allclose(model.predict("xb"), expected, rtol=1e-12, atol=1e-12)
    assert not np.allclose(model.predict("xb"), np.log(model.predict("mu")))


def test_ppmlhdfe_weighted_changes_coefficients():
    """Non-uniform weights should generally change point estimates."""
    df = _make_ppml_data(n=200, seed=456)
    df["w"] = np.where(df["x1"] > 0, 2.0, 0.5)
    unweighted = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"]).fit(vce="robust")
    weighted = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"], weights="w").fit(vce="robust")
    # Coefficients should differ (they are not guaranteed to, but very likely with this weight design)
    betas_u = np.array([c.beta for c in unweighted.coefficients])
    betas_w = np.array([c.beta for c in weighted.coefficients])
    assert not np.allclose(betas_u, betas_w, rtol=1e-6)


def test_ppmlhdfe_exposure_rescaling_only_shifts_constant():
    """Changing exposure units must not alter slopes or fitted means."""
    rng = np.random.default_rng(20260613)
    n = 300
    group = rng.integers(0, 20, size=n)
    x = rng.normal(size=n)
    exposure = np.exp(rng.normal(scale=0.5, size=n))
    group_effect = rng.normal(scale=0.25, size=20)
    mu = exposure * np.exp(0.2 + 0.4 * x + group_effect[group])
    df = pd.DataFrame(
        {
            "y": rng.poisson(mu),
            "x": x,
            "group": group,
            "exposure": exposure,
            "exposure_scaled": 7.0 * exposure,
        }
    )

    base_model = PPMLHDFE(
        df, y="y", x=["x"], absorb=["group"], exposure="exposure"
    )
    scaled_model = PPMLHDFE(
        df, y="y", x=["x"], absorb=["group"], exposure="exposure_scaled"
    )
    base = base_model.fit(vce="robust")
    scaled = scaled_model.fit(vce="robust")
    base_params = {row.name: row.beta for row in base.coefficients}
    scaled_params = {row.name: row.beta for row in scaled.coefficients}

    assert np.isclose(base_params["x"], scaled_params["x"], rtol=1e-7, atol=1e-8)
    assert np.isclose(
        scaled_params["_cons"],
        base_params["_cons"] - np.log(7.0),
        rtol=1e-7,
        atol=1e-8,
    )
    assert np.allclose(base_model._mu, scaled_model._mu, rtol=1e-7, atol=1e-8)


def test_ppmlhdfe_default_drops_zero_outcome_fe_groups():
    """The default separation policy must not return a divergent FE solution."""
    rng = np.random.default_rng(20260614)
    group = np.repeat(np.arange(6), 20)
    x = rng.normal(size=len(group))
    mu = np.exp(0.3 + 0.5 * x + np.repeat(rng.normal(scale=0.2, size=6), 20))
    y = rng.poisson(mu)
    y[group == 0] = 0
    df = pd.DataFrame({"y": y, "x": x, "group": group})

    result = PPMLHDFE(df, y="y", x=["x"], absorb=["group"]).fit(vce="robust")

    assert result.sample.nobs == len(df) - 20
    assert any("Separation observations dropped: 20" in w for w in result.diagnostics.warnings)
    assert all(np.isfinite(row.beta) for row in result.coefficients)


def test_ppmlhdfe_nonconvergence_raises_instead_of_returning_result():
    """An exhausted IRLS iteration budget must be a hard estimation failure."""
    df = _make_ppml_data(n=150, seed=20260615)
    model = PPMLHDFE(
        df,
        y="y",
        x=["x1", "x2"],
        absorb=["g1", "g2"],
        separation="none",
        max_iter=1,
    )

    with pytest.raises(RuntimeError, match="IRLS did not converge"):
        model.fit(vce="robust")


def test_ppmlhdfe_single_cluster_rejected():
    """VCE-001: single cluster should raise ValueError, not produce pseudo-exact SEs."""
    df = _make_ppml_data(n=50, seed=99)
    df["cl"] = 1  # all observations in one cluster
    with pytest.raises(ValueError, match="at least 2 clusters"):
        PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["g1"]).fit(
            vce="cluster", cluster="cl"
        )
