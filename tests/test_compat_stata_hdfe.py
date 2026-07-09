"""Tests for compat.stata HDFE wrappers."""

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import reghdfe, ppmlhdfe
from stataflow.estimators import AbsorbingOLS, PPMLHDFE
from stataflow.estimators._absorb_spec import AbsorbSpec


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


def test_reghdfe_near_collinearity_uses_shared_parameter_choice():
    """HDFE collinearity screening should use the shared stable pivot rule."""
    rng = np.random.default_rng(20260703)
    n_groups = 8
    n_periods = 10
    n = n_groups * n_periods
    group = np.repeat(np.arange(n_groups), n_periods)
    x1 = rng.normal(size=n)
    x2 = (x1 + rng.normal(scale=1e-7, size=n)) * 1e6
    effects = np.repeat(rng.normal(size=n_groups), n_periods)
    y = 1.0 + effects + 2.0e-6 * x2 + rng.normal(scale=0.2, size=n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": group})

    result = reghdfe(df, y="y", x=["x1", "x2"], absorb="g")

    assert [row.name for row in result.coefficients] == ["x2", "_cons"]
    assert result.variance.row_names == ["x2", "_cons"]
    assert result.diagnostics.warnings == ["Collinear variables dropped: x1"]


def test_reghdfe_nested_fe_cluster_df_a_matches_stata_repro():
    """M03-HDFE-001: FE nested in cluster should not inflate absorbed DoF."""
    rng = np.random.default_rng(303)
    n_firm = 24
    n_time = 4
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    industry = (firm - 1) // 4 + 1
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    eta = rng.normal(0, 1, 6)[industry - 1]
    x = rng.normal(0, 1, n) + 0.2 * eta
    y = 1.0 + 1.5 * x + alpha + eta + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "industry": industry, "y": y, "x": x})

    result = reghdfe(
        df,
        y="y",
        x=["x"],
        absorb=["firm", "year"],
        vce="cluster",
        cluster="industry",
    )

    assert result.fit.df_a == pytest.approx(3.0)
    assert result.fit.df_resid == pytest.approx(5.0)
    assert result.diagnostics.cluster_count == 6
    assert {row.name for row in result.coefficients} == {"x", "_cons"}


def test_absorbing_ols_slope_absorption_df_a_and_cluster_se_match_stata_repro():
    """M03-HDFE-002: absorbed firm slopes should contribute to df_a and VCE."""
    rng = np.random.default_rng(606)
    n_firm = 12
    n_time = 5
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    slope = rng.normal(0, 0.3, n_firm)[firm - 1]
    x = rng.normal(0, 1, n)
    y = 1.0 + 1.0 * x + alpha + slope * year + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "y": y, "x": x})

    result = AbsorbingOLS(
        df,
        y="y",
        x=["x"],
        absorb=[AbsorbSpec(var="firm", slopes=["year"], has_intercept=True)],
        add_constant=True,
        drop_singletons=True,
    ).fit(vce="cluster", cluster="firm")
    x_row = next(row for row in result.coefficients if row.name == "x")

    assert result.fit.df_a == pytest.approx(12.0)
    assert result.fit.df_resid == pytest.approx(11.0)
    assert result.diagnostics.cluster_count == 12
    assert x_row.beta == pytest.approx(0.9442661726360293, rel=1e-12)
    assert x_row.std_err == pytest.approx(0.09394816089718806, rel=1e-12)


def test_reghdfe_disconnected_graph_reports_missing_adjusted_r2_at_zero_df_resid():
    """M03-HDFE-003: saturated disconnected FE graph should not report r2_adj."""
    rng = np.random.default_rng(404)
    rows = []
    for f in [1, 2, 3, 4]:
        years_for_f = [(f % 4) + 1, ((f + 1) % 4) + 1]
        for t in years_for_f:
            rows.append({"firm": f, "year": t})
    df = pd.DataFrame(rows)
    df["x"] = rng.normal(0, 1, len(df))
    alpha = {1: 1.0, 2: 2.0, 3: -1.0, 4: -2.0}
    gamma = {1: 0.5, 2: -0.5, 3: 0.3, 4: -0.3}
    df["y"] = (
        1.0
        + 2.0 * df["x"]
        + df["firm"].map(alpha)
        + df["year"].map(gamma)
        + rng.normal(0, 0.1, len(df))
    )

    result = reghdfe(df, y="y", x=["x"], absorb=["firm", "year"], vce="ols")

    assert result.fit.df_resid == pytest.approx(0.0)
    assert result.fit.r2_adj is None
    assert result.fit.df_a == pytest.approx(7.0)


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


def test_ppmlhdfe_nested_fe_cluster_df_a_matches_stata_repro():
    """M06-PPMLHDFE-007: FE nested in cluster should be redundant in df_a."""
    rng = np.random.default_rng(20260613)
    n_entity = 20
    n_time = 10
    entity_id = np.repeat(np.arange(1, n_entity + 1), n_time)
    time_id = np.tile(np.arange(1, n_time + 1), n_entity)
    n = len(entity_id)
    x1 = rng.normal(0, 1, size=n)
    x2 = rng.normal(0, 1, size=n)
    entity_fe = rng.normal(-0.5, 1.0, size=n_entity)
    time_fe = rng.normal(0, 0.5, size=n_time)
    eta = 0.3 + 0.6 * x1 - 0.4 * x2 + entity_fe[entity_id - 1] + time_fe[time_id - 1]
    rate = np.exp(eta)
    rate[rng.random(n) < 0.15] *= 0.05
    df = pd.DataFrame(
        {
            "entity_id": entity_id,
            "time_id": time_id,
            "x1": x1,
            "x2": x2,
            "y": rng.poisson(rate),
        }
    )

    result = PPMLHDFE(
        df,
        y="y",
        x=["x1", "x2"],
        absorb=["entity_id", "time_id"],
    ).fit(vce="cluster", cluster="entity_id")

    assert result.fit.df_a == pytest.approx(9.0)
    assert result.diagnostics.cluster_count == 19
    assert np.isnan(result.fit.df_resid)


def test_ppmlhdfe_cluster_df_resid_is_missing_like_stata_e_df_r():
    df = _make_ppml_data(n=120, seed=314)
    result = PPMLHDFE(
        df,
        y="y",
        x=["x1", "x2"],
        absorb=["g1"],
    ).fit(vce="cluster", cluster="g1")

    assert result.diagnostics.cluster_count == df["g1"].nunique()
    assert np.isnan(result.fit.df_resid)


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
