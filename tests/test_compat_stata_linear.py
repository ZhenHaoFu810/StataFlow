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


def test_regress_unsupported_kwargs():
    df = _make_ols_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        regress(df, y="y", x=["x1"], beta=True)


def test_xtreg_fe_delegation():
    df = _make_fe_data()
    res = xtreg_fe(df, y="y", x=["x1", "x2"], fe="id")
    direct = FixedEffectsOLS(df, y="y", x=["x1", "x2"], fe="id").fit()
    assert res.model.command == "xtreg"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_xtreg_fe_unsupported_kwargs():
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        xtreg_fe(df, y="y", x=["x1"], fe="id", dfadj=True)


def test_areg_delegation():
    df = _make_fe_data()
    res = areg(df, y="y", x=["x1", "x2"], absorb="id")
    direct = AbsorbingOLS(df, y="y", x=["x1", "x2"], absorb="id").fit()
    assert res.model.command == "areg"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_areg_unsupported_kwargs():
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        areg(df, y="y", x=["x1"], absorb="id", generate="resid")
