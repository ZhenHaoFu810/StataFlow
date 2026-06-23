"""M08 synthetic dual-run tests (S1-S7) for RD audit v1.3.

All designs use new random seeds, sample structures, and parameter values that
do not reuse existing `tests/golden/` or `tests/test_rdrobust.py` DGPs.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from stataflow import RDRobust
from stataflow.compat.stata import rdrobust, rdplot
from tests.audit_v1_3.m08_rd.m08_audit_utils import (
    rdrobust_stata_do,
    rdplot_stata_do,
    run_stata_rd,
    compare_python_to_stata,
    save_evidence,
)


# ---------------------------------------------------------------------------
# DGP helpers (new seeds / designs)
# ---------------------------------------------------------------------------


def _make_s1_hand_checkable(seed: int = 2026062001) -> pd.DataFrame:
    """S1: tiny sample where a local-linear fit can be hand-checked.

    12 observations, 6 on each side of c=0, with x spaced at +/- 0.1 increments
    and y equal to a linear function plus a known jump of 3.0.  Using a
    uniform kernel with h=0.5 includes all observations, so the conventional
    local-linear estimate equals the difference in side-specific OLS intercepts.
    """
    rng = np.random.default_rng(seed)
    x_l = -np.arange(1, 7) * 0.1
    x_r = np.arange(1, 7) * 0.1
    x = np.concatenate([x_l, x_r])
    # Linear baseline y = 1 + 2*x, jump = 3 for x >= 0, tiny noise for stability
    y_l = 1.0 + 2.0 * x_l + rng.normal(0, 0.001, size=len(x_l))
    y_r = 4.0 + 2.0 * x_r + rng.normal(0, 0.001, size=len(x_r))
    y = np.concatenate([y_l, y_r])
    return pd.DataFrame({"y": y, "x": x})


def _make_s2_standard(seed: int = 2026062002, n: int = 600) -> pd.DataFrame:
    """S2: standard sharp RD with homogeneous treatment effect."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1.5, 1.5, size=n)
    y0 = 0.5 + 1.2 * x - 0.4 * x**2
    treat = (x >= 0.0).astype(float)
    y = y0 + 2.5 * treat + rng.normal(0, 0.6, size=n)
    return pd.DataFrame({"y": y, "x": x})


def _make_s3_covariates(seed: int = 2026062003, n: int = 600) -> pd.DataFrame:
    """S3: sharp RD with a strong covariate correlated with outcome."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1.5, 1.5, size=n)
    z = 0.3 * x + rng.normal(0, 0.5, size=n)
    treat = (x >= 0.0).astype(float)
    y = 0.5 + 1.2 * x - 0.4 * x**2 + 2.5 * treat + 0.9 * z + rng.normal(0, 0.6, size=n)
    return pd.DataFrame({"y": y, "x": x, "z": z})


def _make_s4_cluster(seed: int = 2026062004, n: int = 400) -> pd.DataFrame:
    """S4: cluster-robust VCE with cluster-level shocks."""
    rng = np.random.default_rng(seed)
    n_clust = 40
    cluster_ids = np.repeat(np.arange(1, n_clust + 1), n // n_clust)[:n]
    x = rng.uniform(-1.5, 1.5, size=n)
    treat = (x >= 0.0).astype(float)
    clust_shock = np.repeat(rng.normal(0, 0.8, n_clust), n // n_clust)[:n]
    y = 0.5 + 1.2 * x + 2.5 * treat + clust_shock + rng.normal(0, 0.4, size=n)
    return pd.DataFrame({"y": y, "x": x, "g": cluster_ids})


def _make_s5_bwselect(seed: int = 2026062005, n: int = 600) -> pd.DataFrame:
    """S5: bandwidth selection with asymmetric density."""
    rng = np.random.default_rng(seed)
    # More mass on the left side
    x_l = rng.uniform(-1.5, 0.0, size=int(n * 0.65))
    x_r = rng.uniform(0.0, 1.5, size=int(n * 0.35))
    x = np.concatenate([x_l, x_r])
    treat = (x >= 0.0).astype(float)
    y = 0.5 + 1.2 * x - 0.3 * x**2 + 2.5 * treat + rng.normal(0, 0.6, size=len(x))
    return pd.DataFrame({"y": y, "x": x})


def _make_s6_stress(seed: int = 2026062006, n: int = 500) -> pd.DataFrame:
    """S6: numerical stress — extreme outcome scale and sparse near cutoff."""
    rng = np.random.default_rng(seed)
    # Sparse near cutoff: only 5% of obs within [-0.05, 0.05]
    x_dense = rng.uniform(-1.2, -0.05, size=int(n * 0.475))
    x_sparse = rng.uniform(-0.05, 0.05, size=int(n * 0.05))
    x_dense_r = rng.uniform(0.05, 1.2, size=int(n * 0.475))
    x = np.concatenate([x_dense, x_sparse, x_dense_r])
    treat = (x >= 0.0).astype(float)
    # Extreme scale
    y = 1e4 * (0.5 + 1.2 * x + 2.5 * treat) + rng.normal(0, 1e3, size=len(x))
    return pd.DataFrame({"y": y, "x": x})


def _make_s7_rdplot(seed: int = 2026062007, n: int = 500) -> pd.DataFrame:
    """S7: quadratic DGP for rdplot bin-count comparison."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, size=n)
    y = 2.0 + 1.5 * x + 0.5 * x**2 + rng.normal(0, 0.5, size=n)
    return pd.DataFrame({"y": y, "x": x})


# ---------------------------------------------------------------------------
# Synthetic dual-run tests
# ---------------------------------------------------------------------------


class TestM08S1HandCheckable:
    """S1: small hand-checkable sample with uniform kernel and full bandwidth."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s1_hand_checkable()

    def test_s1(self, data):
        prefix = "S1_HAND_CHECKABLE"
        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, h=0.5, kernel="uniform")
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(data, y="y", x="x", c=0.0, h=0.5, kernel="uniform")
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "h_l", "h_r"],
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])
        # Known jump is approximately 3.0
        assert 2.5 < py._rd_extras["tau_cl"] < 3.5


class TestM08S2StandardSharpRD:
    """S2: standard sharp RD with homogeneous treatment effect."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s2_standard()

    def test_s2(self, data):
        prefix = "S2_STANDARD_SHARP_RD"
        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, bwselect="mserd")
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(data, y="y", x="x", c=0.0, bwselect="mserd")
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "h_l", "h_r", "b_l", "b_r"],
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])
        assert 1.8 < py._rd_extras["tau_cl"] < 3.2


class TestM08S3Covariates:
    """S3: covariate-adjusted sharp RD."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s3_covariates()

    def test_s3(self, data):
        prefix = "S3_COVARIATES"
        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, bwselect="mserd", covs="z")
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(data, y="y", x="x", c=0.0, bwselect="mserd", covs="z")
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "h_l", "h_r"],
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM08S4ClusterVCE:
    """S4: cluster-robust VCE."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s4_cluster()

    def test_s4(self, data):
        prefix = "S4_CLUSTER_VCE"
        do = rdrobust_stata_do(
            "{dta}", "y", "x", c=0.0, bwselect="mserd", vce="cluster", cluster="g"
        )
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(
            data, y="y", x="x", c=0.0, bwselect="mserd", vce="cluster", cluster="g"
        )
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "h_l", "h_r"],
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM08S5UserBandwidth:
    """S5: user-specified bandwidth (asymmetric) and CER selector."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s5_bwselect()

    def test_s5a_explicit_asymmetric_h(self, data):
        prefix = "S5A_EXPLICIT_ASYMMETRIC_H"
        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, h=(0.9, 1.3), kernel="epanechnikov")
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(data, y="y", x="x", c=0.0, h=(0.9, 1.3), kernel="epanechnikov")
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_h_l", "n_h_r", "h_l", "h_r"],
            bandwidth_rtol=1e-6,
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])

    def test_s5b_cer_selector(self, data):
        prefix = "S5B_CER_SELECTOR"
        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, bwselect="certwo")
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(data, y="y", x="x", c=0.0, bwselect="certwo")
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_h_l", "n_h_r", "h_l", "h_r", "b_l", "b_r"],
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM08S6NumericalStress:
    """S6: numerical stress with extreme scale and sparse data near cutoff."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s6_stress()

    def test_s6(self, data):
        prefix = "S6_NUMERICAL_STRESS"
        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, h=0.35, kernel="triangular")
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(data, y="y", x="x", c=0.0, h=0.35, kernel="triangular")
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_h_l", "n_h_r", "h_l", "h_r"],
            bandwidth_rtol=1e-6,
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])
        assert math.isfinite(py._rd_extras["tau_cl"])


class TestM08S7RDPlot:
    """S7: rdplot bin selection on quadratic DGP."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s7_rdplot()

    def test_s7_esmv(self, data):
        prefix = "S7_RDPLOT_ESMV"
        do = rdplot_stata_do("{dta}", "y", "x", c=0.0, binselect="esmv")
        st = run_stata_rd(data, prefix, do)
        py = rdplot(data, y="y", x="x", c=0.0, binselect="esmv")
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["n_l", "n_r", "j_star_l", "j_star_r"],
            compare_sample_mask=False,
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])

    def test_s7_qsmv(self, data):
        prefix = "S7_RDPLOT_QSMV"
        do = rdplot_stata_do("{dta}", "y", "x", c=0.0, binselect="qsmv")
        st = run_stata_rd(data, prefix, do)
        py = rdplot(data, y="y", x="x", c=0.0, binselect="qsmv")
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["n_l", "n_r", "j_star_l", "j_star_r"],
            compare_sample_mask=False,
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])
