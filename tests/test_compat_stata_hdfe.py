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


def test_ppmlhdfe_wrapper_aweight():
    """Wrapper accepts aweight and passes it through."""
    df = _make_ppml_data(n=150, seed=123)
    df["w"] = np.abs(np.random.default_rng(42).normal(1, 0.3, size=len(df)))
    res = ppmlhdfe(df, y="y", x=["x1", "x2"], absorb=["g1", "g2"], aweight="w")
    assert res.model.command == "ppmlhdfe"
    assert len(res.coefficients) > 0


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
