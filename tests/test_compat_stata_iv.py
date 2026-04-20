"""Tests for compat.stata IV wrappers."""

import numpy as np
import pandas as pd
import pytest

from statapy.compat.stata import ivregress_2sls, ivreghdfe
from statapy.estimators import IV2SLS, IVAbsorbingOLS


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
            first=True
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
