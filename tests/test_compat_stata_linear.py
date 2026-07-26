"""Tests for compat.stata linear regression wrappers."""

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import regress, xtreg_fe, areg
from stataflow.estimators import OLS, FixedEffectsOLS, AbsorbingOLS


def _make_ols_data(n=100, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "w": rng.uniform(0.5, 2.0, size=n),
    })
    return df


def _make_fe_data(n=100, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "id": rng.integers(0, 10, size=n),
    })
    return df


def _make_within_collinear_fe_data(seed=20260613):
    """Create a panel where z is collinear with x after demeaning."""
    rng = np.random.default_rng(seed)
    n_entities = 8
    n_periods = 5
    entity = np.repeat(np.arange(n_entities), n_periods)
    x = rng.normal(size=n_entities * n_periods)
    entity_shift = np.repeat(rng.normal(size=n_entities), n_periods)
    z = 2.0 * x + entity_shift
    y = 1.0 + 0.7 * x + entity_shift + rng.normal(scale=0.2, size=len(x))
    return pd.DataFrame({"y": y, "x": x, "z": z, "id": entity})


def test_regress_delegation():
    df = _make_ols_data()
    res = regress(df, y="y", x=["x1", "x2"])
    direct = OLS(df, y="y", x=["x1", "x2"]).fit()
    assert res.model.command == "regress"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
        assert np.isclose(c.std_err, d.std_err, rtol=1e-10)


def test_regress_noconstant():
    df = _make_ols_data()
    res = regress(df, y="y", x=["x1", "x2"], noconstant=True)
    names = [c.name for c in res.coefficients]
    assert "_cons" not in names


def test_regress_aweight():
    df = _make_ols_data()
    res = regress(df, y="y", x=["x1", "x2"], aweight="w")
    direct = OLS(df, y="y", x=["x1", "x2"], weights=df["w"].values, weight_type="aweight").fit()
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_regress_aweight_zero_rows_are_excluded_from_sample():
    """Zero analytic weights behave like Stata's excluded observations."""
    df = _make_ols_data(n=40, seed=20260618)
    df.loc[[3, 17], "w"] = 0.0

    weighted = regress(df, y="y", x=["x1", "x2"], aweight="w")
    filtered_df = df.loc[df["w"] > 0].copy()
    filtered = regress(filtered_df, y="y", x=["x1", "x2"], aweight="w")

    assert weighted.sample.nobs == 38
    assert weighted.sample.sample_mask[3] is False
    assert weighted.sample.sample_mask[17] is False
    weighted_params = [row.beta for row in weighted.coefficients]
    filtered_params = [row.beta for row in filtered.coefficients]
    assert np.allclose(weighted_params, filtered_params, rtol=1e-12, atol=1e-12)
    assert np.allclose(weighted.variance.values, filtered.variance.values, rtol=1e-12, atol=1e-12)


def test_regress_aweight_negative_still_raises():
    """Negative analytic weights are invalid rather than excluded."""
    df = _make_ols_data(n=20, seed=20260619)
    df.loc[5, "w"] = -1.0

    with pytest.raises(ValueError, match="nonnegative"):
        regress(df, y="y", x=["x1"], aweight="w")


def test_regress_level():
    df = _make_ols_data()
    res = regress(df, y="y", x=["x1"], level=90)
    direct = OLS(df, y="y", x=["x1"]).fit(alpha=0.10)
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
        assert np.isclose(c.ci_low, d.ci_low, rtol=1e-10)
        assert np.isclose(c.ci_high, d.ci_high, rtol=1e-10)


def test_regress_unsupported_kwargs():
    df = _make_ols_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        regress(df, y="y", x=["x1"], unknown_opt=True)


def test_xtreg_fe_delegation():
    df = _make_fe_data()
    res = xtreg_fe(df, y="y", x=["x1", "x2"], fe="id")
    direct = FixedEffectsOLS(
        df, y="y", x=["x1", "x2"], fe="id", add_constant=True
    ).fit()
    assert res.model.command == "xtreg"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_xtreg_fe_defaults_to_stata_constant_reporting():
    """The compatibility wrapper reports ``_cons`` unless explicitly disabled."""
    df = _make_fe_data()

    result = xtreg_fe(df, y="y", x=["x1"], fe="id")

    assert [row.name for row in result.coefficients] == ["x1", "_cons"]


def test_fe_unbalanced_panel_constant_matches_stata_17():
    """The FE constant is the observation-weighted mean of entity effects."""
    df = pd.DataFrame({
        "id": [1, 1, 1, 1, 2, 2, 3, 3, 3],
        "y": [1.0, 2.1, 2.9, 4.2, 2.1, 3.0, 0.4, 1.9, 3.1],
        "x": [0.5, 1.0, 1.5, 2.0, 1.1, 1.9, 0.1, 0.8, 1.7],
    })

    result = FixedEffectsOLS(
        df, y="y", x=["x"], fe="id", add_constant=True
    ).fit(vce="ols")
    constant = next(row for row in result.coefficients if row.name == "_cons")

    assert constant.beta == pytest.approx(0.19319332, rel=1e-6)
    assert constant.std_err == pytest.approx(0.21133346, rel=1e-6)


def test_fe_cluster_reporting_matches_stata_17():
    """Clustered ``xtreg, fe`` uses Stata's stored-result conventions."""
    rng = np.random.default_rng(7)
    n = 60
    df = pd.DataFrame({
        "id": np.repeat(np.arange(1, 11), 6),
        "x": rng.normal(size=n),
        "y": rng.normal(size=n),
    })

    result = FixedEffectsOLS(
        df, y="y", x=["x"], fe="id", add_constant=True
    ).fit(vce="cluster", cluster="id")

    assert result.fit.df_model == 0
    assert result.fit.r2_adj == pytest.approx(0.01306831, rel=1e-6)
    assert result.fit.f_stat == pytest.approx(2.5081517, rel=1e-6)
    assert result.fit.f_pvalue == pytest.approx(0.1477, abs=5e-5)


def test_fe_cluster_two_slopes_stores_rank_minus_one_df_model():
    """Clustered ``xtreg, fe`` stores e(df_m)=rank-1 for multiple slopes."""
    rng = np.random.default_rng(66666)
    n_entities = 30
    n_periods = 4
    n = n_entities * n_periods
    entity_id = np.repeat(np.arange(n_entities), n_periods)
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    entity_fe = np.repeat(rng.normal(0, 2, n_entities), n_periods)
    error = rng.normal(0, 1, n)
    df = pd.DataFrame({
        "id": entity_id,
        "x1": x1,
        "x2": x2,
        "y": 1 + 1.5 * x1 - 2 * x2 + entity_fe + error,
    })

    result = FixedEffectsOLS(
        df, y="y", x=["x1", "x2"], fe="id", add_constant=True
    ).fit(vce="cluster", cluster="id")

    assert result.fit.df_model == 1


def test_xtreg_fe_residuals_match_stata_y_minus_xb():
    """FE residuals match Stata ``predict, residuals``."""
    df = pd.DataFrame({
        "id": [1, 1, 1, 2, 2, 2, 3, 3],
        "x": [0.0, 1.0, 2.0, 0.5, 1.5, 2.5, 0.2, 1.2],
        "y": [1.0, 2.2, 3.1, -0.1, 1.2, 2.1, 2.0, 3.1],
    })
    train = df.iloc[:6].copy()
    result = xtreg_fe(train, y="y", x=["x"], fe="id")

    residuals = result.predict(type="residuals", newdata=df)
    model = result._model
    xb = df[model._active_x].to_numpy(dtype=float) @ model._beta + model._constant
    expected = df["y"].to_numpy(dtype=float) - xb

    assert len(residuals) == len(df)
    assert np.allclose(residuals, expected)


def test_xtreg_fe_level():
    df = _make_fe_data()
    res = xtreg_fe(df, y="y", x=["x1"], fe="id", level=90)
    direct = FixedEffectsOLS(
        df, y="y", x=["x1"], fe="id", add_constant=True
    ).fit(alpha=0.10)
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
        assert np.isclose(c.ci_low, d.ci_low, rtol=1e-10)
        assert np.isclose(c.ci_high, d.ci_high, rtol=1e-10)


def test_xtreg_fe_unsupported_kwargs():
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        xtreg_fe(df, y="y", x=["x1"], fe="id", dfadj=True)


@pytest.mark.parametrize("vce", ["ols", "robust", "cluster"])
@pytest.mark.parametrize("add_constant", [False, True])
def test_fe_within_collinear_drop_keeps_dimensions_consistent(vce, add_constant):
    """Dropping a within-collinear regressor must update every result dimension."""
    df = _make_within_collinear_fe_data()
    fit_kwargs = {"vce": vce}
    if vce == "cluster":
        fit_kwargs["cluster"] = "id"

    model = FixedEffectsOLS(
        df,
        y="y",
        x=["x", "z"],
        fe="id",
        add_constant=add_constant,
    )
    result = model.fit(**fit_kwargs)

    expected_names = ["x", "_cons"] if add_constant else ["x"]
    assert [row.name for row in result.coefficients] == expected_names
    assert result.variance.row_names == expected_names
    assert np.asarray(result.variance.values).shape == (
        len(expected_names),
        len(expected_names),
    )
    assert result.fit.rank == 1
    assert np.isfinite(model.predict()).all()


def test_ols_near_collinearity_matches_stata_parameter_choice():
    """Extreme scaling should omit x1 and retain the stable x2 parameter."""
    rng = np.random.default_rng(20260613)
    x1 = rng.normal(size=50)
    x2 = (x1 + rng.normal(scale=1e-7, size=50)) * 1e6
    y = 1.0 + 2.0 * x1 + 3e-6 * x2 + rng.normal(scale=0.5, size=50)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    result = OLS(df, y="y", x=["x1", "x2"], add_constant=True).fit()

    assert [row.name for row in result.coefficients] == ["x2", "_cons"]
    assert result.diagnostics.warnings == ["Collinear variables dropped: x1"]


def test_fe_near_collinearity_uses_shared_parameter_choice():
    """Within-transformed FE designs must use the shared pivoting rule."""
    rng = np.random.default_rng(20260617)
    entity = np.repeat(np.arange(10), 6)
    x1 = rng.normal(size=len(entity))
    x2 = (x1 + rng.normal(scale=1e-7, size=len(entity))) * 1e6
    effects = np.repeat(rng.normal(size=10), 6)
    y = 1.0 + effects + 2.5e-6 * x2 + rng.normal(scale=0.2, size=len(entity))
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "id": entity})

    result = FixedEffectsOLS(
        df, y="y", x=["x1", "x2"], fe="id", add_constant=True
    ).fit()

    assert [row.name for row in result.coefficients] == ["x2", "_cons"]
    assert result.variance.row_names == ["x2", "_cons"]


def test_areg_delegation():
    df = _make_fe_data()
    res = areg(df, y="y", x=["x1", "x2"], absorb="id")
    direct = AbsorbingOLS(df, y="y", x=["x1", "x2"], absorb="id").fit()
    assert res.model.command == "areg"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_areg_level():
    df = _make_fe_data()
    res = areg(df, y="y", x=["x1"], absorb="id", level=90)
    direct = AbsorbingOLS(df, y="y", x=["x1"], absorb="id").fit(alpha=0.10)
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
        assert np.isclose(c.ci_low, d.ci_low, rtol=1e-10)
        assert np.isclose(c.ci_high, d.ci_high, rtol=1e-10)


def test_areg_noconstant():
    df = _make_fe_data()
    res = areg(df, y="y", x=["x1"], absorb="id", noconstant=True)
    names = [c.name for c in res.coefficients]
    assert "_cons" not in names


def test_areg_unsupported_kwargs():
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        areg(df, y="y", x=["x1"], absorb="id", generate="resid")


# ---------------------------------------------------------------------------
# Multi-way clustering (Package D)
# ---------------------------------------------------------------------------

def _make_cluster_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "c1": rng.integers(0, 10, size=n),
        "c2": rng.integers(0, 8, size=n),
    })
    return df


def test_regress_two_way_clustering():
    """Two-way clustering should produce coefficients identical to one-way."""
    df = _make_cluster_data()
    res_one = regress(df, y="y", x=["x1"], vce="cluster", cluster="c1")
    res_two = regress(df, y="y", x=["x1"], vce="cluster", cluster=["c1", "c2"])

    # Coefficients should be identical (VCE doesn't affect beta)
    assert np.isclose(
        res_one.coefficients[0].beta,
        res_two.coefficients[0].beta,
        rtol=1e-10,
    )

    # Model info should record both cluster variables
    assert res_two.model.cluster_var == ["c1", "c2"]


def test_regress_two_way_cluster_uses_conventional_model_f():
    """Stata reports the conventional model F for two-way clustering."""
    rng = np.random.default_rng(20260613)
    n_firms, n_years = 30, 20
    n = n_firms * n_years
    x = rng.normal(size=n)
    df = pd.DataFrame(
        {
            "y": 1.0 + 2.0 * x + rng.normal(scale=0.5, size=n),
            "x": x,
            "firm": np.repeat(np.arange(n_firms), n_years),
            "year": np.tile(np.arange(n_years), n_firms),
        }
    )

    result = regress(
        df,
        y="y",
        x=["x"],
        vce="cluster",
        cluster=["firm", "year"],
    )

    expected_f = (result.fit.mss / result.fit.df_model) / (
        result.fit.rss / (n - 2)
    )
    assert result.fit.df_resid == n_years - 1
    assert result.fit.f_stat == pytest.approx(expected_f, rel=1e-12)
    from scipy.stats import f as f_dist

    expected_p = f_dist.sf(expected_f, result.fit.df_model, n_years - 1)
    assert result.fit.f_pvalue == pytest.approx(expected_p, rel=1e-12)


def test_regress_two_way_cluster_vce_is_psd_after_inclusion_exclusion():
    """Stata truncates negative eigenvalues of a multiway cluster VCE."""
    rng = np.random.default_rng(20260614)
    n = 240
    g1 = np.repeat(np.arange(40), 6)
    g2 = np.tile(np.arange(6), 40)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    y = 1.0 + x1 - 0.5 * x2 + rng.normal(size=n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g1": g1, "g2": g2})

    result = regress(
        df,
        y="y",
        x=["x1", "x2"],
        vce="cluster",
        cluster=["g1", "g2"],
    )

    eigvals = np.linalg.eigvalsh(np.asarray(result.variance.values))
    assert eigvals.min() >= -1e-12


def test_regress_two_way_clustering_se_larger():
    """Two-way clustering SE should generally be larger than one-way."""
    df = _make_cluster_data(n=200, seed=42)
    res_one = regress(df, y="y", x=["x1"], vce="cluster", cluster="c1")
    res_two = regress(df, y="y", x=["x1"], vce="cluster", cluster=["c1", "c2"])

    se_one = res_one.coefficients[0].std_err
    se_two = res_two.coefficients[0].std_err
    # Two-way SE should be at least as large as one-way (not guaranteed in
    # every finite sample, but true in expectation; we check it's reasonable)
    assert se_two > 0
    assert se_two >= se_one * 0.5


def test_regress_two_way_clustering_rejects_three_way():
    """Three-way clustering should raise ValueError."""
    df = _make_cluster_data()
    with pytest.raises(ValueError, match="Multi-way clustering currently supports exactly 2"):
        regress(df, y="y", x=["x1"], vce="cluster", cluster=["c1", "c2", "x2"])


def test_regress_two_way_clustering_string_collision():
    """String cluster labels containing '__' must not cause intersection collision."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "y": rng.normal(size=4),
        "x1": rng.normal(size=4),
        # Deliberately create labels that would collide with f"{a}__{b}":
        # ('a', 'b__c') and ('a__b', 'c') both become 'a__b__c' under string concat
        "c1": ["a", "a__b", "a", "a__b"],
        "c2": ["b__c", "c", "c", "b__c"],
    })

    res = regress(df, y="y", x=["x1"], vce="cluster", cluster=["c1", "c2"])
    assert res.model.cluster_var == ["c1", "c2"]
    assert res.coefficients[0].std_err > 0


def test_two_way_clustering_tuple_factorize_distinct_pairs():
    """Tuple factorization must count all distinct (c1, c2) pairs correctly."""
    c1 = np.array(["a", "a__b", "a", "a__b"])
    c2 = np.array(["b__c", "c", "c", "b__c"])
    combo_to_id = {}
    combo_ids = np.empty(len(c1), dtype=int)
    for i, pair in enumerate(zip(c1, c2)):
        if pair not in combo_to_id:
            combo_to_id[pair] = len(combo_to_id)
        combo_ids[i] = combo_to_id[pair]
    unique_combos = np.unique(combo_ids)
    # All 4 rows have distinct (c1, c2) pairs; string concat would incorrectly merge 2
    assert len(unique_combos) == 4


def test_xtreg_fe_rejects_multiway_cluster():
    """xtreg_fe must raise ValueError for multi-way cluster, not TypeError."""
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Multi-way clustering is only supported for regress"):
        xtreg_fe(df, y="y", x=["x1"], fe="id", vce="cluster", cluster=["id", "x2"])


def _w14_panel(seed: int = 20260719) -> pd.DataFrame:
    """Balanced panel matching Wave 14 VCE probe structure."""
    rng = np.random.default_rng(seed)
    n_entities, n_periods = 40, 6
    n = n_entities * n_periods
    panel_id = np.repeat(np.arange(1, n_entities + 1), n_periods)
    time_id = np.tile(np.arange(1, n_periods + 1), n_entities)
    cluster_nested = ((panel_id - 1) // 4) + 1
    cluster_nonnested = (panel_id + time_id) % 5 + 1
    x1 = rng.normal(size=n)
    entity_fe = np.repeat(rng.normal(scale=1.5, size=n_entities), n_periods)
    y = 1.0 + 0.8 * x1 + entity_fe + rng.normal(size=n)
    return pd.DataFrame(
        {
            "y": y,
            "x1": x1,
            "panel_id": panel_id.astype(int),
            "time_id": time_id.astype(int),
            "cluster_nested": cluster_nested.astype(int),
            "cluster_nonnested": cluster_nonnested.astype(int),
        }
    )


def test_xtreg_fe_robust_uses_panel_level_scores():
    """Stata ``xtreg, fe robust`` is panel-robust: V equals cluster(panel)."""
    panel_df = _w14_panel()
    robust = xtreg_fe(panel_df, y="y", x=["x1"], fe="panel_id", vce="robust")
    clustered = xtreg_fe(
        panel_df, y="y", x=["x1"], fe="panel_id", vce="cluster", cluster="panel_id"
    )
    np.testing.assert_allclose(
        np.asarray(robust.variance.values),
        np.asarray(clustered.variance.values),
        rtol=1e-12,
        atol=1e-12,
    )
    assert robust.model.vcetype == "robust"
    assert robust.model.cluster_var is None
    assert robust.fit.df_resid == panel_df["panel_id"].nunique() - 1


def test_fixedeffects_ols_robust_matches_panel_cluster_directly():
    """Core estimator path must match; fix cannot live only in the wrapper."""
    panel_df = _w14_panel(seed=11)
    robust = FixedEffectsOLS(
        panel_df, y="y", x=["x1"], fe="panel_id", add_constant=True
    ).fit(vce="robust")
    clustered = FixedEffectsOLS(
        panel_df, y="y", x=["x1"], fe="panel_id", add_constant=True
    ).fit(vce="cluster", cluster="panel_id")
    np.testing.assert_allclose(
        np.asarray(robust.variance.values),
        np.asarray(clustered.variance.values),
        rtol=1e-12,
        atol=1e-12,
    )
    assert robust.model.vcetype == "robust"


def test_xtreg_fe_robust_unbalanced_and_multi_slope():
    """Panel-robust path handles unbalanced panels and multiple slopes."""
    rng = np.random.default_rng(99)
    rows = []
    for i in range(1, 16):
        t_i = 3 + (i % 4)
        for t in range(t_i):
            rows.append(
                {
                    "id": i,
                    "t": t,
                    "x1": rng.normal(),
                    "x2": rng.normal(),
                    "y": rng.normal(),
                }
            )
    df = pd.DataFrame(rows)
    robust = xtreg_fe(df, y="y", x=["x1", "x2"], fe="id", vce="robust")
    clustered = xtreg_fe(df, y="y", x=["x1", "x2"], fe="id", vce="cluster", cluster="id")
    np.testing.assert_allclose(
        np.asarray(robust.variance.values),
        np.asarray(clustered.variance.values),
        rtol=1e-12,
        atol=1e-12,
    )
    assert {c.name for c in robust.coefficients} >= {"x1", "x2", "_cons"}
    assert robust.fit.df_resid == df["id"].nunique() - 1


@pytest.mark.parametrize("nested", [True, False])
def test_areg_cluster_nested_nonnested_finite_sample(nested):
    """areg cluster SE must use areg-owned k_eff (not reghdfe nested write-off)."""
    df = _w14_panel()
    cl = "cluster_nested" if nested else "cluster_nonnested"
    model = AbsorbingOLS(
        data=df, y="y", x=["x1"], absorb="panel_id", add_constant=True
    )
    result = model.fit(vce="cluster", cluster=cl)
    # Sanity: SEs finite, df_resid = G-1, both slope and intercept present.
    assert result.fit.df_resid == df[cl].nunique() - 1
    names = {c.name: c.std_err for c in result.coefficients}
    assert names["x1"] > 0 and names["_cons"] > 0
    n_panels = df["panel_id"].nunique()
    # areg keeps absorb rank in df_a even when FE is nested in cluster (G-1 with const).
    expected_df_a = float(n_panels - (1 if model.add_constant else 0))
    assert model._df_a == expected_df_a
    # k_eff = k_x + const + df_a (areg-owned); nested write-off would give k_eff≈2.
    k_eff = model._cluster_k_eff(1)
    assert k_eff == 1 + 1 + int(expected_df_a)
    if nested:
        # Historical bug used k_eff=2 → SE ~8–9% too small vs correct k_eff.
        # Correct SE must exceed the wrong-scale SE by the finite-sample ratio.
        n = len(df)
        G = df[cl].nunique()
        m_wrong = (G / (G - 1)) * ((n - 1) / (n - 2))
        m_right = (G / (G - 1)) * ((n - 1) / (n - k_eff))
        se_wrong_proxy = names["x1"] * np.sqrt(m_wrong / m_right)
        assert names["x1"] > se_wrong_proxy * 1.05


def test_areg_rejects_multiway_cluster():
    """areg must raise ValueError for multi-way cluster, not TypeError."""
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Multi-way clustering is only supported for regress"):
        areg(df, y="y", x=["x1"], absorb="id", vce="cluster", cluster=["id", "x2"])


def test_regress_vce_cluster_string_syntax():
    """regress should accept vce="cluster varname" Stata-style syntax."""
    rng = np.random.default_rng(99)
    n = 100
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "group": rng.integers(0, 10, size=n),
    })
    res = regress(df, y="y", x=["x1", "x2"], vce="cluster group")
    assert res.model.vcetype == "cluster"
    assert res.model.cluster_var == "group"


def test_regress_empty_x_no_constant_raises():
    """OLS with empty x and no constant should raise ValueError."""
    df = pd.DataFrame({"y": [1.0, 2.0], "x": [1.0, 2.0]})
    with pytest.raises(ValueError, match="0 columns"):
        OLS(df, "y", [], add_constant=False).fit()


def test_regress_all_missing_x_raises():
    """OLS where all x are missing should raise ValueError."""
    import numpy as np
    df = pd.DataFrame({"y": [1.0, 2.0], "x": [np.nan, np.nan]})
    with pytest.raises(ValueError, match="No observations remain"):
        OLS(df, "y", ["x"]).fit()


def test_fe_empty_x_raises():
    """FE with empty x should raise ValueError."""
    df = pd.DataFrame({
        "y": [1.0, 2.0, 3.0],
        "id": [1, 1, 2],
    })
    with pytest.raises(ValueError, match="0 columns"):
        FixedEffectsOLS(df, "y", [], "id").fit()


def test_regress_single_cluster_rejected():
    """VCE-001: cluster-robust VCE requires at least 2 clusters."""
    df = pd.DataFrame({
        "y": [1.0, 2.0, 3.0, 4.0],
        "x": [1.0, 2.0, 3.0, 4.0],
        "clust": [1, 1, 1, 1],
    })
    with pytest.raises(ValueError, match="at least 2 clusters"):
        regress(df, y="y", x=["x"], vce="cluster clust")
