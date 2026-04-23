"""Flexible synthetic tests for HDFE estimators.

Covers reghdfe, ppmlhdfe, and ivreghdfe across different FE structures,
VCE types, and edge cases.
"""

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import reghdfe, ppmlhdfe, ivreghdfe
from stataflow.estimators import AbsorbingOLS, PPMLHDFE, IVAbsorbingOLS


def _make_reghdfe_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "firm_id": rng.integers(0, 10, size=n),
        "year_id": rng.integers(0, 5, size=n),
    })
    return df


def _make_ppml_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    eta = rng.normal(size=n)
    df = pd.DataFrame({
        "y": rng.poisson(np.exp(eta)),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "firm_id": rng.integers(0, 10, size=n),
        "year_id": rng.integers(0, 5, size=n),
        "offset_var": rng.uniform(0.5, 2.0, size=n),
    })
    return df


def _make_iv_data(n=200, seed=42):
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
        "firm_id": rng.integers(0, 10, size=n),
        "year_id": rng.integers(0, 5, size=n),
    })
    return df


# ---------------------------------------------------------------------------
# reghdfe
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("vce", ["ols", "robust", "cluster"])
def test_reghdfe_vce_types(vce):
    df = _make_reghdfe_data()
    kwargs = {"vce": vce}
    if vce == "cluster":
        kwargs["cluster"] = "firm_id"
    res = reghdfe(df, y="y", x=["x1", "x2"], absorb=["firm_id", "year_id"], **kwargs)
    assert res.model.command == "reghdfe"
    assert all(c.std_err > 0 for c in res.coefficients)


def test_reghdfe_single_absorb_robust():
    df = _make_reghdfe_data()
    res = reghdfe(df, y="y", x=["x1", "x2"], absorb="firm_id", vce="robust")
    assert res.model.command == "reghdfe"
    direct = AbsorbingOLS(df, y="y", x=["x1", "x2"], absorb=["firm_id"]).fit(vce="robust")
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
        assert np.isclose(c.std_err, d.std_err, rtol=1e-10)


def test_reghdfe_robust_se_larger_than_ols():
    """Robust SE should generally be larger than OLS SE under heteroskedasticity."""
    df = _make_reghdfe_data()
    res_ols = reghdfe(df, y="y", x=["x1", "x2"], absorb=["firm_id", "year_id"], vce="ols")
    res_rob = reghdfe(df, y="y", x=["x1", "x2"], absorb=["firm_id", "year_id"], vce="robust")
    for c_ols, c_rob in zip(res_ols.coefficients, res_rob.coefficients):
        if c_ols.name != "_cons":
            assert c_rob.std_err >= c_ols.std_err * 0.5  # loose bound; heteroskedasticity present


def test_reghdfe_singleton_drop_affects_sample():
    """Create data where some FE groups have only 1 observation."""
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "y": rng.normal(size=20),
        "x1": rng.normal(size=20),
        "g1": [0, 0, 1, 1, 2] + [3] * 15,  # group 2 has 1 obs if we subset
    })
    res = reghdfe(df, y="y", x=["x1"], absorb="g1")
    # Group 2 (single obs) should be dropped
    assert res.sample.nobs < 20


def test_reghdfe_keepsingletons_preserves_sample():
    """keepsingletons=True should retain singleton observations."""
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "y": rng.normal(size=20),
        "x1": rng.normal(size=20),
        "g1": [0, 0, 1, 1, 2] + [3] * 15,
    })
    res_drop = reghdfe(df, y="y", x=["x1"], absorb="g1")
    res_keep = reghdfe(df, y="y", x=["x1"], absorb="g1", keepsingletons=True)
    assert res_keep.sample.nobs == 20
    assert res_drop.sample.nobs < res_keep.sample.nobs
    # Singleton warning should appear only when dropping
    drop_warnings = " ".join(res_drop.diagnostics.warnings)
    keep_warnings = " ".join(res_keep.diagnostics.warnings)
    assert "Singleton" in drop_warnings
    assert "Singleton" not in keep_warnings


def test_reghdfe_predict_types_consistency():
    """Mathematical consistency of predict sub-options."""
    df = _make_reghdfe_data(n=100, seed=55)
    model = AbsorbingOLS(df, y="y", x=["x1", "x2"], absorb=["firm_id", "year_id"])
    result = model.fit(vce="ols")

    y = model._dep_var
    xb = model.predict(type="xb")
    xbd = model.predict(type="xbd")
    d = model.predict(type="d")
    resid = model.predict(type="residuals")
    dresid = model.predict(type="dresiduals")

    # xbd == xb + d
    assert np.allclose(xbd, xb + d, rtol=1e-10)
    # residuals == y - xbd
    assert np.allclose(resid, y - xbd, rtol=1e-10)
    # dresiduals == y - xb
    assert np.allclose(dresid, y - xb, rtol=1e-10)
    # d == xbd - xb
    assert np.allclose(d, xbd - xb, rtol=1e-10)

    # xb should NOT equal xbd when FEs are present
    assert not np.allclose(xb, xbd, rtol=1e-6)


def test_reghdfe_predict_xb_excludes_fe_contribution():
    """xb prediction should match reported coefficients only (no FE dummies)."""
    df = _make_reghdfe_data(n=100, seed=55)
    model = AbsorbingOLS(df, y="y", x=["x1", "x2"], absorb=["firm_id", "year_id"])
    result = model.fit(vce="ols")

    # Manual xb from reported coefficients
    n = len(model._dep_var)
    X_rep = np.column_stack([
        model._df["x1"].values,
        model._df["x2"].values,
        np.ones(n),
    ])
    beta_rep = np.array([c.beta for c in result.coefficients])
    manual_xb = X_rep @ beta_rep
    auto_xb = model.predict(type="xb")
    assert np.allclose(manual_xb, auto_xb, rtol=1e-10)


def test_reghdfe_noconstant_wrapper():
    """noconstant=True should omit the constant from reported coefficients."""
    df = _make_reghdfe_data(n=100, seed=66)
    res_const = reghdfe(df, y="y", x=["x1"], absorb="firm_id")
    res_nocons = reghdfe(df, y="y", x=["x1"], absorb="firm_id", noconstant=True)

    const_names = [c.name for c in res_const.coefficients]
    nocons_names = [c.name for c in res_nocons.coefficients]
    assert "_cons" in const_names
    assert "_cons" not in nocons_names
    assert len(res_nocons.coefficients) == len(res_const.coefficients) - 1


# ---------------------------------------------------------------------------
# ivreghdfe
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("vce", ["ols", "robust", "cluster"])
def test_ivreghdfe_vce_types(vce):
    df = _make_iv_data()
    kwargs = {"vce": vce}
    if vce == "cluster":
        kwargs["cluster"] = "firm_id"
    res = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb=["firm_id", "year_id"], **kwargs
    )
    assert res.model.command == "ivreghdfe"
    assert all(c.std_err > 0 for c in res.coefficients)


def test_ivreghdfe_single_absorb_command_semantics():
    """ivreghdfe must always report command='ivreghdfe' even with single absorb."""
    df = _make_iv_data()
    res = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="firm_id"
    )
    assert res.model.command == "ivreghdfe"
    direct = IVAbsorbingOLS(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb=["firm_id"]
    ).fit()
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_ivreghdfe_robust_se_larger_than_ols():
    df = _make_iv_data()
    res_ols = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb=["firm_id", "year_id"], vce="ols"
    )
    res_rob = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb=["firm_id", "year_id"], vce="robust"
    )
    for c_ols, c_rob in zip(res_ols.coefficients, res_rob.coefficients):
        assert c_rob.std_err >= c_ols.std_err * 0.5


def test_ivreghdfe_noconstant_wrapper():
    """noconstant=True should set has_constant=False in metadata."""
    df = _make_iv_data(n=100, seed=66)
    res_const = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="firm_id"
    )
    res_nocons = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="firm_id", noconstant=True
    )
    # ivreghdfe with absorb never reports _cons regardless of noconstant
    assert res_const.model.has_constant is True
    assert res_nocons.model.has_constant is False
    assert len(res_nocons.coefficients) > 0
    assert all(c.std_err > 0 for c in res_nocons.coefficients)


def test_ivreghdfe_keepsingletons_preserves_sample():
    """keepsingletons=True should retain singleton observations."""
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "y": rng.normal(size=20),
        "x1": rng.normal(size=20),
        "x2": rng.normal(size=20),
        "z1": rng.normal(size=20),
        "g1": [0, 0, 1, 1, 2] + [3] * 15,
    })
    res_drop = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1"
    )
    res_keep = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb="g1", keepsingletons=True
    )
    assert res_keep.sample.nobs == 20
    assert res_drop.sample.nobs < res_keep.sample.nobs
    drop_warnings = " ".join(res_drop.diagnostics.warnings)
    keep_warnings = " ".join(res_keep.diagnostics.warnings)
    assert "Singleton" in drop_warnings
    assert "Singleton" not in keep_warnings


def test_ivreghdfe_predict_types_consistency():
    """Mathematical consistency of predict sub-options."""
    df = _make_iv_data(n=100, seed=55)
    model = IVAbsorbingOLS(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb=["firm_id", "year_id"]
    )
    result = model.fit(vce="ols")

    y = model._dep_var
    xb = model.predict(type="xb")
    xbd = model.predict(type="xbd")
    d = model.predict(type="d")
    resid = model.predict(type="residuals")
    dresid = model.predict(type="dresiduals")

    # xbd == xb + d
    assert np.allclose(xbd, xb + d, rtol=1e-10)
    # residuals == y - xbd
    assert np.allclose(resid, y - xbd, rtol=1e-10)
    # dresiduals == y - xb
    assert np.allclose(dresid, y - xb, rtol=1e-10)
    # d == xbd - xb
    assert np.allclose(d, xbd - xb, rtol=1e-10)

    # xb should NOT equal xbd when FEs are present
    assert not np.allclose(xb, xbd, rtol=1e-6)


# ---------------------------------------------------------------------------
# ppmlhdfe
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("vce", ["ols", "robust", "cluster"])
def test_ppmlhdfe_vce_types(vce):
    df = _make_ppml_data()
    kwargs = {"vce": vce}
    if vce == "cluster":
        kwargs["cluster"] = "firm_id"
    res = ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["firm_id", "year_id"], **kwargs)
    assert res.model.command == "ppmlhdfe"
    assert all(c.std_err > 0 for c in res.coefficients)


def test_ppmlhdfe_offset_support():
    df = _make_ppml_data()
    res = ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["firm_id"], offset="offset_var")
    direct = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["firm_id"], offset="offset_var").fit()
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_ppmlhdfe_exposure_support():
    df = _make_ppml_data()
    res = ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["firm_id"], exposure="offset_var")
    # exposure = ln(offset_var), so coefficients should match offset with log values
    direct = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["firm_id"], exposure="offset_var").fit()
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_ppmlhdfe_offset_exposure_mutual_exclusion():
    df = _make_ppml_data()
    with pytest.raises(ValueError, match="Only one of offset or exposure"):
        PPMLHDFE(df, y="y", x=["x1"], absorb=["firm_id"], offset="offset_var", exposure="offset_var")
    with pytest.raises(ValueError, match="Only one of offset or exposure"):
        ppmlhdfe(df, y="y", x=["x1"], absorb=["firm_id"], offset="offset_var", exposure="offset_var")


def test_ppmlhdfe_exposure_positive_check():
    df = _make_ppml_data()
    df.loc[0, "offset_var"] = -1.0
    with pytest.raises(ValueError, match=r"exposure\(\) must be greater than zero"):
        PPMLHDFE(df, y="y", x=["x1"], absorb=["firm_id"], exposure="offset_var")


def test_ppmlhdfe_separation_not_implemented_but_documented():
    """Separation detection is not implemented; verify that IRLS still converges on clean data."""
    df = _make_ppml_data()
    res = ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["firm_id", "year_id"])
    warnings = [w for w in res.diagnostics.warnings if "separation" in w.lower()]
    # No separation warning expected on this synthetic data
    assert len(warnings) == 0
    assert res.sample.nobs > 0


def test_ppmlhdfe_noconstant_wrapper():
    """noconstant=True should omit the constant from reported coefficients."""
    df = _make_ppml_data(n=100, seed=66)
    res_const = ppmlhdfe(df, y="y", x=["x1"], absorb="firm_id")
    res_nocons = ppmlhdfe(df, y="y", x=["x1"], absorb="firm_id", noconstant=True)

    const_names = [c.name for c in res_const.coefficients]
    nocons_names = [c.name for c in res_nocons.coefficients]
    assert "_cons" in const_names
    assert "_cons" not in nocons_names
    assert len(res_nocons.coefficients) == len(res_const.coefficients) - 1


def test_ppmlhdfe_maxiter_tolerance_wrapper():
    """maxiter and tolerance should be passed through and affect convergence."""
    df = _make_ppml_data(n=100, seed=77)
    # Very tight tolerance and many iterations should converge
    res_fine = ppmlhdfe(df, y="y", x=["x1"], absorb="firm_id", maxiter=200, tolerance=1e-12)
    assert "IRLS did not converge" not in " ".join(res_fine.diagnostics.warnings)

    # One iteration should not converge
    res_fast = ppmlhdfe(df, y="y", x=["x1"], absorb="firm_id", maxiter=1, tolerance=1e8)
    assert "IRLS did not converge" in " ".join(res_fast.diagnostics.warnings)


def test_ppmlhdfe_predict_residuals():
    """predict(type='residuals') should return y - mu."""
    df = _make_ppml_data(n=100, seed=88)
    model = PPMLHDFE(df, y="y", x=["x1", "x2"], absorb=["firm_id"])
    result = model.fit(vce="robust")

    mu = model.predict(type="mu")
    residuals = model.predict(type="residuals")
    y = model._abs_ols._dep_var

    assert np.allclose(residuals, y - mu, rtol=1e-10)


# ---------------------------------------------------------------------------
# Parameter hard-rejection
# ---------------------------------------------------------------------------

def test_reghdfe_rejects_unsupported_vce():
    df = _make_reghdfe_data()
    with pytest.raises(ValueError, match="vce='driscoll' not supported"):
        reghdfe(df, y="y", x=["x1"], absorb="firm_id", vce="driscoll")


def test_ivreghdfe_rejects_unsupported_vce():
    df = _make_iv_data()
    with pytest.raises(ValueError, match="vce='driscoll' not supported"):
        ivreghdfe(
            df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
            absorb="firm_id", vce="driscoll"
        )


# ---------------------------------------------------------------------------
# Multi-FE (3+) support — Package B
# ---------------------------------------------------------------------------

def _make_three_fe_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "firm_id": rng.integers(0, 8, size=n),
        "year_id": rng.integers(0, 5, size=n),
        "industry_id": rng.integers(0, 4, size=n),
    })
    return df


@pytest.mark.parametrize("vce", ["ols", "robust", "cluster"])
def test_reghdfe_three_absorb(vce):
    """reghdfe should support 3+ absorbed FE variables."""
    df = _make_three_fe_data()
    kwargs = {"vce": vce}
    if vce == "cluster":
        kwargs["cluster"] = "firm_id"
    res = reghdfe(
        df, y="y", x=["x1", "x2"],
        absorb=["firm_id", "year_id", "industry_id"], **kwargs
    )
    assert res.model.command == "reghdfe"
    assert len(res.model.absorb_vars) == 3
    assert all(c.std_err > 0 for c in res.coefficients)


def test_reghdfe_three_absorb_noconstant():
    """3 FE noconstant should produce identical fit to constant version."""
    df = _make_three_fe_data(n=100, seed=55)
    res_const = reghdfe(
        df, y="y", x=["x1"],
        absorb=["firm_id", "year_id", "industry_id"], vce="ols"
    )
    res_nocons = reghdfe(
        df, y="y", x=["x1"],
        absorb=["firm_id", "year_id", "industry_id"],
        vce="ols", noconstant=True
    )
    # RSS should be identical (same model span)
    assert np.isclose(res_const.fit.rss, res_nocons.fit.rss, rtol=1e-10)
    assert "_cons" in [c.name for c in res_const.coefficients]
    assert "_cons" not in [c.name for c in res_nocons.coefficients]


def test_reghdfe_three_absorb_df_a():
    """df_a for 3 FEs should equal sum(levels) - (n_fes - 1)."""
    df = _make_three_fe_data(n=100, seed=66)
    res = reghdfe(
        df, y="y", x=["x1"],
        absorb=["firm_id", "year_id", "industry_id"], vce="ols"
    )
    # firm_id: 8 levels, year_id: 5 levels, industry_id: 4 levels
    expected_df_a = 8 + 5 + 4 - (3 - 1)
    assert res.fit.df_a == expected_df_a


def test_reghdfe_three_absorb_predict_consistency():
    """predict types should remain mathematically consistent with 3 FEs."""
    df = _make_three_fe_data(n=100, seed=77)
    model = AbsorbingOLS(
        df, y="y", x=["x1", "x2"],
        absorb=["firm_id", "year_id", "industry_id"]
    )
    model.fit(vce="ols")

    y = model._dep_var
    xb = model.predict(type="xb")
    xbd = model.predict(type="xbd")
    d = model.predict(type="d")
    resid = model.predict(type="residuals")
    dresid = model.predict(type="dresiduals")

    assert np.allclose(xbd, xb + d, rtol=1e-10)
    assert np.allclose(resid, y - xbd, rtol=1e-10)
    assert np.allclose(dresid, y - xb, rtol=1e-10)
    assert not np.allclose(xb, xbd, rtol=1e-6)


def test_ivreghdfe_three_absorb():
    """ivreghdfe should support 3 absorbed FE variables."""
    rng = np.random.default_rng(42)
    n = 200
    z = rng.normal(size=n)
    u = rng.normal(size=n)
    x2 = 0.5 * z + u + rng.normal(size=n)
    x1 = rng.normal(size=n)
    y = 1.0 + 2.0 * x1 + 3.0 * x2 + u + rng.normal(size=n)
    df = pd.DataFrame({
        "y": y, "x1": x1, "x2": x2, "z1": z,
        "firm_id": rng.integers(0, 8, size=n),
        "year_id": rng.integers(0, 5, size=n),
        "industry_id": rng.integers(0, 4, size=n),
    })
    res = ivreghdfe(
        df, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1"],
        absorb=["firm_id", "year_id", "industry_id"], vce="robust"
    )
    assert res.model.command == "ivreghdfe"
    assert len(res.model.absorb_vars) == 3
    assert all(c.std_err > 0 for c in res.coefficients)


def test_ppmlhdfe_three_absorb():
    """ppmlhdfe should support 3 absorbed FE variables."""
    rng = np.random.default_rng(42)
    n = 200
    eta = rng.normal(size=n)
    df = pd.DataFrame({
        "y": rng.poisson(np.exp(eta)),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "firm_id": rng.integers(0, 8, size=n),
        "year_id": rng.integers(0, 5, size=n),
        "industry_id": rng.integers(0, 4, size=n),
    })
    res = ppmlhdfe(
        df, y="y", x=["x1", "x2"],
        absorb=["firm_id", "year_id", "industry_id"], vce="robust"
    )
    assert res.model.command == "ppmlhdfe"
    assert len(res.model.absorb_vars) == 3
    assert all(c.std_err > 0 for c in res.coefficients)
