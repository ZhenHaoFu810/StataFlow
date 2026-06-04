"""Tests for compat.stata IV wrappers."""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from stataflow.compat.stata import ivregress_2sls, ivreghdfe
from stataflow.estimators import IV2SLS, IVAbsorbingOLS

PROJECT_ROOT = Path(__file__).parent.parent
CARD_CSV = PROJECT_ROOT / "research" / "data" / "public" / "iv" / "card.csv"


def _make_iv_data(n=100, seed=42):
    rng = np.random.default_rng(seed)
    z = rng.normal(size=n)
    u = rng.normal(size=n)
    x2 = 0.5 * z + u + rng.normal(size=n)
    x1 = rng.normal(size=n)
    y = 1.0 + 2.0 * x1 + 3.0 * x2 + u + rng.normal(size=n)
    df = pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "z1": z,
        "g1": rng.integers(0, 5, size=n),
    })
    return df


def test_ivregress_2sls_delegation():
    df = _make_iv_data()
    res = ivregress_2sls(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"]
    )
    direct = IV2SLS(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"]
    ).fit()
    assert res.model.command == "ivregress 2sls"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_ivregress_2sls_unsupported_kwargs():
    df = _make_iv_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        ivregress_2sls(
            df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
            foo=True
        )


def test_ivreghdfe_delegation():
    df = _make_iv_data()
    res = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1"
    )
    direct = IVAbsorbingOLS(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1"
    ).fit()
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_ivreghdfe_unsupported_kwargs():
    df = _make_iv_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        ivreghdfe(
            df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
            absorb="g1", savefirst=True
        )


def test_ivreghdfe_noconstant_wrapper():
    """Wrapper noconstant=True should set has_constant=False and avoid errors."""
    df = _make_iv_data()
    res_const = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1"
    )
    res_nocons = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1", noconstant=True
    )
    # ivreghdfe with absorb never reports _cons regardless of noconstant,
    # but has_constant metadata should differ
    assert res_const.model.has_constant is True
    assert res_nocons.model.has_constant is False
    # Coefficients should be present and valid in both cases
    assert len(res_nocons.coefficients) > 0
    assert all(c.std_err > 0 for c in res_nocons.coefficients)


def test_ivreghdfe_gmm2s_wrapper():
    """Wrapper should pass through estimator='gmm2s' and return Hansen J."""
    df = _make_iv_data()
    res = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1", estimator="gmm2s"
    )
    assert hasattr(res, "hansen_j")
    assert res.hansen_j_df == 0  # exactly identified


def test_ivreghdfe_liml_wrapper():
    """Wrapper should pass through estimator='liml' and return k-class."""
    df = _make_iv_data()
    res = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1", estimator="liml"
    )
    assert hasattr(res, "liml_k")
    assert res.liml_k > 0


def test_ivreghdfe_liml_fuller_wrapper():
    """Wrapper should pass through fuller parameter."""
    df = _make_iv_data()
    res_fuller = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1", estimator="liml", fuller=1
    )
    res_liml = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1", estimator="liml"
    )
    assert res_fuller.liml_k < res_liml.liml_k


def test_ivreghdfe_liml_kclass_wrapper():
    """Wrapper should pass through user-specified kclass."""
    df = _make_iv_data()
    res = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1", estimator="liml", kclass=0.5
    )
    assert np.isclose(res.liml_k, 0.5)


def test_ivreghdfe_multi_endog_weakiv():
    """Multi-endogenous weakiv diagnostics should return finite values, not NaN."""
    rng = np.random.default_rng(42)
    n = 200
    z1 = rng.normal(size=n)
    z2 = rng.normal(size=n)
    u = rng.normal(size=n)
    x1 = 0.5 * z1 + 0.3 * z2 + u + rng.normal(size=n)
    x2 = 0.3 * z1 + 0.5 * z2 + u + rng.normal(size=n)
    y = 1.0 + 2.0 * x1 + 1.5 * x2 + u + rng.normal(size=n)
    df = pd.DataFrame({
        "y": y, "x1": x1, "x2": x2, "z1": z1, "z2": z2,
        "g1": rng.integers(0, 5, size=n),
    })
    model = IVAbsorbingOLS(
        df, y="y", x_exog=[], x_endog=["x1", "x2"], instruments=["z1", "z2"], absorb="g1"
    )
    result = model.fit(vce="ols")
    assert not np.isnan(result.idstat)
    assert not np.isnan(result.widstat)
    assert result.iddf == 1  # k_excl(2) - k_endog(2) + 1 = 1


def test_ivreghdfe_two_way_cluster_fallback_updates_df_resid():
    """Two-way fallback should use the returned richer cluster count for df_resid."""
    rng = np.random.default_rng(0)
    n = 90
    g1 = np.repeat(np.arange(3), 30)
    g2 = np.tile(np.repeat([0, 1], 15), 3)
    z1 = rng.normal(size=n)
    x1 = rng.normal(size=n)
    u = rng.normal(size=n)
    x2 = 0.8 * z1 + 0.5 * x1 + u
    y = 1.0 + 1.2 * x1 + 0.9 * x2 + u + rng.normal(size=n)
    df = pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "z1": z1,
        "g1": g1,
        "g2": g2,
    })

    result = IVAbsorbingOLS(
        df,
        y="y",
        x_exog=["x1"],
        x_endog=["x2"],
        instruments=["z1"],
        absorb="g1",
    ).fit(vce="cluster", cluster=["g1", "g2"])

    assert result.diagnostics.cluster_count == 3
    assert result.fit.df_resid == 2.0


def test_ivreghdfe_two_way_cluster_fallback_reuses_one_way_first_stage_and_weakiv():
    """Rank-deficient 2-way fallback should match richer 1-way diagnostics."""
    rng = np.random.default_rng(0)
    n = 90
    g1 = np.repeat(np.arange(3), 30)
    g2 = np.tile(np.repeat([0, 1], 15), 3)
    z1 = rng.normal(size=n)
    x1 = rng.normal(size=n)
    u = rng.normal(size=n)
    x2 = 0.8 * z1 + 0.5 * x1 + u
    y = 1.0 + 1.2 * x1 + 0.9 * x2 + u + rng.normal(size=n)
    df = pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "z1": z1,
        "g1": g1,
        "g2": g2,
    })

    model_kwargs = dict(
        data=df,
        y="y",
        x_exog=["x1"],
        x_endog=["x2"],
        instruments=["z1"],
        absorb="g1",
    )
    one_way = IVAbsorbingOLS(**model_kwargs).fit(vce="cluster", cluster="g1", first=True)
    two_way = IVAbsorbingOLS(**model_kwargs).fit(vce="cluster", cluster=["g1", "g2"], first=True)

    assert two_way.diagnostics.cluster_count == one_way.diagnostics.cluster_count == 3
    assert np.isclose(
        two_way.first_stage["x2"]["f_stat"],
        one_way.first_stage["x2"]["f_stat"],
        rtol=1e-10,
    )
    assert np.isclose(two_way.widstat, one_way.widstat, rtol=1e-10)


def test_ivreghdfe_card_cluster_f_stat_matches_stata_small_cluster_path():
    """Card real-data cluster F-stat should stay finite and match Stata's 0.36."""
    df = pd.read_csv(CARD_CSV)
    df["age_group"] = (df["age"] // 5).astype(int)

    model_kwargs = dict(
        data=df,
        y="lwage",
        x_exog=["exper", "expersq", "black", "south", "smsa"],
        x_endog=["educ"],
        instruments=["nearc4"],
        absorb="age_group",
    )
    one_way = IVAbsorbingOLS(**model_kwargs).fit(
        vce="cluster", cluster="age_group", first=True
    )
    two_way = IVAbsorbingOLS(**model_kwargs).fit(
        vce="cluster", cluster=["age_group", "south"], first=True
    )

    assert np.isfinite(one_way.fit.f_stat)
    assert np.isfinite(two_way.fit.f_stat)
    assert np.isclose(one_way.fit.f_stat, 0.36, atol=0.01)
    assert np.isclose(two_way.fit.f_stat, 0.36, atol=0.01)
    assert np.isclose(one_way.fit.f_stat, two_way.fit.f_stat, rtol=1e-10)
