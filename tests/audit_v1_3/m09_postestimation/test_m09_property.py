"""M09 metamorphic / property tests for postestimation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata.linear import regress


class TestP01RowOrderInvariance:
    """P01: shuffling rows does not change OLS prediction statistics."""

    def test_p01(self):
        seed = 202607
        rng = np.random.default_rng(seed)
        N = 80
        df = pd.DataFrame({
            "x1": rng.normal(size=N),
            "x2": rng.normal(size=N),
        })
        df["y"] = 1.0 + 2.0 * df["x1"] - 0.5 * df["x2"] + rng.normal(0.0, 0.5, size=N)

        base = regress(df, "y", ["x1", "x2"])
        base_xb = base.predict(type="xb")

        shuffled = df.sample(frac=1.0, random_state=rng.integers(0, 1 << 31)).reset_index(drop=True)
        rerun = regress(shuffled, "y", ["x1", "x2"])
        rerun_xb = rerun.predict(type="xb")

        assert np.isclose(float(np.mean(base_xb)), float(np.mean(rerun_xb)), rtol=1e-10)
        assert np.isclose(float(np.std(base_xb, ddof=1)), float(np.std(rerun_xb, ddof=1)), rtol=1e-10)
        assert base.sample.nobs == rerun.sample.nobs


class TestP02IrrelevantColumn:
    """P02: adding an unused column does not change predictions."""

    def test_p02(self):
        seed = 202608
        rng = np.random.default_rng(seed)
        N = 80
        df = pd.DataFrame({
            "x1": rng.normal(size=N),
            "x2": rng.normal(size=N),
        })
        df["y"] = 1.0 + 2.0 * df["x1"] - 0.5 * df["x2"] + rng.normal(0.0, 0.5, size=N)

        base = regress(df, "y", ["x1", "x2"])
        base_xb = base.predict(type="xb")

        df_extra = df.copy()
        df_extra["noise"] = rng.normal(size=N)
        rerun = regress(df_extra, "y", ["x1", "x2"])
        rerun_xb = rerun.predict(type="xb")

        assert np.allclose(base_xb, rerun_xb, rtol=1e-10)
        assert base.sample.nobs == rerun.sample.nobs


class TestP03OutcomeScaling:
    """P03: scaling y scales xb and residuals linearly."""

    def test_p03(self):
        seed = 202609
        rng = np.random.default_rng(seed)
        N = 80
        df = pd.DataFrame({
            "x1": rng.normal(size=N),
            "x2": rng.normal(size=N),
        })
        df["y"] = 1.0 + 2.0 * df["x1"] - 0.5 * df["x2"] + rng.normal(0.0, 0.5, size=N)

        base = regress(df, "y", ["x1", "x2"])
        base_xb = base.predict(type="xb")
        base_resid = base.predict(type="residuals")

        scale = 3.0
        df_scaled = df.copy()
        df_scaled["y"] = df_scaled["y"] * scale
        scaled = regress(df_scaled, "y", ["x1", "x2"])
        scaled_xb = scaled.predict(type="xb")
        scaled_resid = scaled.predict(type="residuals")

        assert np.allclose(scaled_xb, base_xb * scale, rtol=1e-10)
        assert np.allclose(scaled_resid, base_resid * scale, rtol=1e-10)
