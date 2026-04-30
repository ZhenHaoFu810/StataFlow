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
    assert not hasattr(res, "predict")
    assert not hasattr(res, "margins")
