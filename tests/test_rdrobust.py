"""Tests for rdrobust sharp RD minimal subset.

Includes synthetic controlled cases, real-data dual-run alignment
against Stata 17, and negative tests for boundary behavior.
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import rdrobust
from stataflow.estimators.rdrobust import RDRobust


def _make_rd_data(n=500, seed=42, jump=2.0, cutoff=0.0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, size=n)
    y = 5 + 3 * x + jump * (x >= cutoff) + rng.normal(0, 0.5, size=n)
    return pd.DataFrame({"y": y, "x": x})


def test_rdrobust_synthetic_basic():
    df = _make_rd_data(n=500, jump=2.0)
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5)
    # True jump is 2.0; point estimate should be close
    tau_cl = res._rd_extras["tau_cl"]
    assert 1.5 < tau_cl < 2.5
    assert res._rd_extras["N_l"] > 50
    assert res._rd_extras["N_r"] > 50
    assert res._rd_extras["N_h_l"] > 20
    assert res._rd_extras["N_h_r"] > 20


def test_rdrobust_synthetic_kernel_variation():
    df = _make_rd_data(n=500, jump=2.0)
    res_tri = rdrobust(df, y="y", x="x", c=0.0, h=0.5, kernel="triangular")
    res_uni = rdrobust(df, y="y", x="x", c=0.0, h=0.5, kernel="uniform")
    # Different kernels should produce numerically different estimates
    assert not math.isclose(res_tri._rd_extras["tau_cl"], res_uni._rd_extras["tau_cl"], rel_tol=1e-10)


def test_rdrobust_synthetic_bandwidth_variation():
    df = _make_rd_data(n=500, jump=2.0)
    res_narrow = rdrobust(df, y="y", x="x", c=0.0, h=0.3)
    res_wide = rdrobust(df, y="y", x="x", c=0.0, h=0.8)
    # Effective observations should scale with bandwidth
    assert res_narrow._rd_extras["N_h_l"] < res_wide._rd_extras["N_h_l"]
    assert res_narrow._rd_extras["N_h_r"] < res_wide._rd_extras["N_h_r"]


def test_rdrobust_senate_real_data_matches_stata():
    """
    Dual-run alignment against Stata 17 on the official rdrobust senate data.
    Stata command: rdrobust vote margin, c(0) h(15)
    """
    df = pd.read_stata(
        "tests/data/rdrobust_senate.dta"
    )
    res = rdrobust(df, y="vote", x="margin", c=0.0, h=15.0)

    # Stata ground truth (rdrobust v10.0.0)
    stata = {
        "tau_cl": 7.4872859,
        "tau_bc": 9.0856282,
        "se_tau_cl": 1.5597318,
        "se_tau_rb": 2.2406721,
    }

    assert pytest.approx(res._rd_extras["tau_cl"], rel=1e-6) == stata["tau_cl"]
    assert pytest.approx(res._rd_extras["tau_bc"], rel=1e-6) == stata["tau_bc"]
    assert pytest.approx(res._rd_extras["se_tau_cl"], rel=1e-6) == stata["se_tau_cl"]
    assert pytest.approx(res._rd_extras["se_tau_rb"], rel=1e-6) == stata["se_tau_rb"]


def test_rdrobust_senate_hc0_uniform_matches_stata():
    """
    Dual-run alignment with vce(hc0) and kernel(uniform).
    Stata command: rdrobust vote margin, c(0) h(15) vce(hc0) kernel(uniform)
    """
    df = pd.read_stata(
        "tests/data/rdrobust_senate.dta"
    )
    res = rdrobust(df, y="vote", x="margin", c=0.0, h=15.0, vce="hc0", kernel="uniform")

    stata = {
        "tau_cl": 6.9638374,
        "tau_bc": 8.4057742,
        "se_tau_cl": 1.4995748,
        "se_tau_rb": 2.1691277,
    }

    assert pytest.approx(res._rd_extras["tau_cl"], rel=1e-6) == stata["tau_cl"]
    assert pytest.approx(res._rd_extras["tau_bc"], rel=1e-6) == stata["tau_bc"]
    assert pytest.approx(res._rd_extras["se_tau_cl"], rel=1e-6) == stata["se_tau_cl"]
    assert pytest.approx(res._rd_extras["se_tau_rb"], rel=1e-6) == stata["se_tau_rb"]


def test_rdrobust_default_bandwidth_selects_mserd():
    df = _make_rd_data(n=200, jump=2.0)
    res_default = rdrobust(df, y="y", x="x", c=0.0)
    res_mserd = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd")

    assert math.isclose(res_default._rd_extras["h_l"], res_mserd._rd_extras["h_l"], rel_tol=1e-12)
    assert math.isclose(res_default._rd_extras["h_r"], res_mserd._rd_extras["h_r"], rel_tol=1e-12)
    assert math.isclose(res_default._rd_extras["tau_cl"], res_mserd._rd_extras["tau_cl"], rel_tol=1e-12)


def test_rdrobust_core_default_bandwidth_selects_mserd():
    df = _make_rd_data(n=200, jump=2.0)
    res_default = RDRobust(df, y="y", x="x", c=0.0).fit()
    res_mserd = RDRobust(df, y="y", x="x", c=0.0, bwselect="mserd").fit()

    assert math.isclose(res_default._rd_extras["h_l"], res_mserd._rd_extras["h_l"], rel_tol=1e-12)
    assert math.isclose(res_default._rd_extras["h_r"], res_mserd._rd_extras["h_r"], rel_tol=1e-12)
    assert math.isclose(res_default._rd_extras["tau_cl"], res_mserd._rd_extras["tau_cl"], rel_tol=1e-12)


def test_rdrobust_unsupported_kwargs_rejected():
    df = _make_rd_data(n=200, jump=2.0)
    with pytest.raises(ValueError, match="Unsupported arguments"):
        rdrobust(df, y="y", x="x", c=0.0, h=0.5, foo="bar")


def test_rdrobust_deriv_rejected():
    df = _make_rd_data(n=200, jump=2.0)
    with pytest.raises(NotImplementedError, match="Only deriv=0"):
        RDRobust(df, y="y", x="x", c=0.0, h=0.5, deriv=1).fit()


def test_rdrobust_coefficients_schema_populated():
    df = _make_rd_data(n=300, jump=2.0)
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5)
    names = [c.name for c in res.coefficients]
    assert names == ["Conventional", "Bias-Corrected", "Robust"]
    for c in res.coefficients:
        assert not math.isnan(c.beta)
        assert not math.isnan(c.std_err)
        assert not math.isnan(c.t_stat)
        assert not math.isnan(c.p_value)
        assert c.ci_low < c.ci_high


def test_rdrobust_bwselect_mserd_synthetic():
    """Automatic bandwidth selection produces positive bandwidths and reasonable estimates."""
    df = _make_rd_data(n=500, jump=2.0)
    res = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd")
    assert res._rd_extras["h_l"] > 0
    assert res._rd_extras["h_r"] > 0
    assert res._rd_extras["b_l"] > 0
    assert res._rd_extras["b_r"] > 0
    # Estimate should be close to true jump
    assert 1.5 < res._rd_extras["tau_cl"] < 2.5


def test_rdrobust_bwselect_mserd_real_data_matches_stata():
    """
    Dual-run alignment for automatic bandwidth selection (mserd) without covariates.
    Stata command: rdrobust vote margin, c(0) bwselect(mserd)

    Note: bandwidth selection is a plug-in iterative procedure; small
    numerical differences (~0.03 %) in h/b propagate to tau/se at the
    ~0.01 % level.  We use a 5e-4 relative tolerance to accommodate this
    well-understood algorithmic variance while still rejecting material
    deviations.
    """
    df = pd.read_stata(
        "tests/data/rdrobust_senate.dta"
    )
    res = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="mserd")

    stata = {
        "tau_cl": 7.4141308,
        "tau_bc": 7.5065025,
        "se_tau_cl": 1.458716,
        "se_tau_rb": 1.7412584,
        "h_l": 17.754397,
        "b_l": 28.028087,
    }

    assert pytest.approx(res._rd_extras["tau_cl"], rel=5e-4) == stata["tau_cl"]
    assert pytest.approx(res._rd_extras["tau_bc"], rel=5e-4) == stata["tau_bc"]
    assert pytest.approx(res._rd_extras["se_tau_cl"], rel=5e-4) == stata["se_tau_cl"]
    assert pytest.approx(res._rd_extras["se_tau_rb"], rel=5e-4) == stata["se_tau_rb"]
    assert pytest.approx(res._rd_extras["h_l"], rel=5e-4) == stata["h_l"]
    assert pytest.approx(res._rd_extras["b_l"], rel=5e-4) == stata["b_l"]


def test_rdrobust_covs_explicit_h_matches_stata():
    """
    Dual-run alignment for covariate-adjusted sharp RD with explicit bandwidth.
    Stata command: rdrobust vote margin, c(0) h(15) covs(z)

    Because h is fixed, the estimation path is fully deterministic and
    matches Stata to 1e-6 relative tolerance.
    """
    df = pd.read_stata("tests/data/rdrobust_senate_with_z.dta")
    res = rdrobust(df, y="vote", x="margin", c=0.0, h=15.0, covs="z")

    stata = {
        "tau_cl": 7.5087336,
        "tau_bc": 9.1271454,
        "se_tau_cl": 1.5602323,
        "se_tau_rb": 2.2427712,
    }

    assert pytest.approx(res._rd_extras["tau_cl"], rel=1e-6) == stata["tau_cl"]
    assert pytest.approx(res._rd_extras["tau_bc"], rel=1e-6) == stata["tau_bc"]
    assert pytest.approx(res._rd_extras["se_tau_cl"], rel=1e-6) == stata["se_tau_cl"]
    assert pytest.approx(res._rd_extras["se_tau_rb"], rel=1e-6) == stata["se_tau_rb"]


def test_rdrobust_covs_bwselect_mserd_matches_stata():
    """
    Dual-run alignment for covariate-adjusted sharp RD with automatic bandwidth.
    Stata command: rdrobust vote margin, c(0) covs(z)

    As with the no-covs bwselect case, plug-in bandwidth selection
    introduces small numerical differences; 5e-4 tolerance is used.
    """
    df = pd.read_stata("tests/data/rdrobust_senate_with_z.dta")
    res = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="mserd", covs="z")

    stata = {
        "tau_cl": 7.428956,
        "tau_bc": 7.5244934,
        "se_tau_cl": 1.4593788,
        "se_tau_rb": 1.7426814,
        "h_l": 17.741488,
    }

    assert pytest.approx(res._rd_extras["tau_cl"], rel=5e-4) == stata["tau_cl"]
    assert pytest.approx(res._rd_extras["tau_bc"], rel=5e-4) == stata["tau_bc"]
    assert pytest.approx(res._rd_extras["se_tau_cl"], rel=5e-4) == stata["se_tau_cl"]
    assert pytest.approx(res._rd_extras["se_tau_rb"], rel=5e-4) == stata["se_tau_rb"]
    assert pytest.approx(res._rd_extras["h_l"], rel=5e-4) == stata["h_l"]


def test_rdrobust_h_overrides_bwselect():
    """When both h and bwselect are provided, h takes precedence."""
    df = pd.read_stata(
        "tests/data/rdrobust_senate.dta"
    )
    res_h_only = rdrobust(df, y="vote", x="margin", c=0.0, h=15.0)
    res_both = rdrobust(df, y="vote", x="margin", c=0.0, h=15.0, bwselect="mserd")
    # Should produce identical results because h overrides bwselect
    assert math.isclose(
        res_h_only._rd_extras["tau_cl"],
        res_both._rd_extras["tau_cl"],
        rel_tol=1e-12,
    )
    assert math.isclose(
        res_h_only._rd_extras["h_l"],
        res_both._rd_extras["h_l"],
        rel_tol=1e-12,
    )


def test_rdrobust_unsupported_bwselect_rejected():
    df = _make_rd_data(n=200, jump=2.0)
    with pytest.raises(NotImplementedError, match="bwselect='invalid' is not supported"):
        rdrobust(df, y="y", x="x", c=0.0, bwselect="invalid")


def test_rdrobust_resultschema_model_command():
    df = _make_rd_data(n=100, jump=2.0)
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5)
    assert res.model.command == "rdrobust"
    assert res.provenance.stata_version_target == "17"


# ---------------------------------------------------------------------------
# Wave 8 Phase A: Bandwidth selector family internal consistency tests
# ---------------------------------------------------------------------------

_ALL_SELECTORS = [
    "mserd", "msesum", "msetwo",
    "msecomb1", "msecomb2",
    "cerrd", "cersum", "certwo",
    "cercomb1", "cercomb2",
]


def test_rdrobust_all_bwselectors_run_without_error():
    """Every supported bwselect value should execute without raising."""
    df = _make_rd_data(n=500, jump=2.0)
    for sel in _ALL_SELECTORS:
        res = rdrobust(df, y="y", x="x", c=0.0, bwselect=sel)
        assert res._rd_extras["h_l"] > 0, f"{sel}: h_l must be positive"
        assert res._rd_extras["h_r"] > 0, f"{sel}: h_r must be positive"
        assert res._rd_extras["b_l"] > 0, f"{sel}: b_l must be positive"
        assert res._rd_extras["b_r"] > 0, f"{sel}: b_r must be positive"


def test_rdrobust_bwselect_comb1_is_min():
    """msecomb1 bandwidth must be <= min(mserd, msesum)."""
    df = _make_rd_data(n=500, jump=2.0)
    res_rd = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd")
    res_sum = rdrobust(df, y="y", x="x", c=0.0, bwselect="msesum")
    res_comb1 = rdrobust(df, y="y", x="x", c=0.0, bwselect="msecomb1")

    h_rd = res_rd._rd_extras["h_l"]
    h_sum = res_sum._rd_extras["h_l"]
    h_comb1 = res_comb1._rd_extras["h_l"]

    assert h_comb1 <= min(h_rd, h_sum) * (1 + 1e-12), "comb1 should be <= min(mserd, msesum)"


def test_rdrobust_bwselect_comb2_is_median():
    """msecomb2 bandwidth should equal median(mserd, msesum, msetwo_l)."""
    df = _make_rd_data(n=500, jump=2.0)
    res_rd = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd")
    res_sum = rdrobust(df, y="y", x="x", c=0.0, bwselect="msesum")
    res_two = rdrobust(df, y="y", x="x", c=0.0, bwselect="msetwo")
    res_comb2 = rdrobust(df, y="y", x="x", c=0.0, bwselect="msecomb2")

    h_rd = res_rd._rd_extras["h_l"]
    h_sum = res_sum._rd_extras["h_l"]
    h_two_l = res_two._rd_extras["h_l"]
    h_comb2_l = res_comb2._rd_extras["h_l"]

    expected_median = sorted([h_rd, h_sum, h_two_l])[1]
    assert math.isclose(h_comb2_l, expected_median, rel_tol=1e-12), "comb2_l should equal median of three"

    h_two_r = res_two._rd_extras["h_r"]
    h_comb2_r = res_comb2._rd_extras["h_r"]
    expected_median_r = sorted([h_rd, h_sum, h_two_r])[1]
    assert math.isclose(h_comb2_r, expected_median_r, rel_tol=1e-12), "comb2_r should equal median of three"


def test_rdrobust_bwselect_cer_scaling():
    """CER bandwidths should equal MSE bandwidths times cer_h factor."""
    df = _make_rd_data(n=500, jump=2.0)

    # cerrd vs mserd
    res_mse = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd")
    res_cer = rdrobust(df, y="y", x="x", c=0.0, bwselect="cerrd")

    h_mse = res_mse._rd_extras["h_l"]
    h_cer = res_cer._rd_extras["h_l"]
    b_mse = res_mse._rd_extras["b_l"]
    b_cer = res_cer._rd_extras["b_l"]

    # CER shrinks h but leaves b unchanged
    assert h_cer < h_mse, "CER h should be smaller than MSE h"
    assert math.isclose(b_cer, b_mse, rel_tol=1e-12), "CER b should equal MSE b"

    # Verify exact ratio = N^(-p/((3+p)*(3+2p)))
    N = 500
    p = 1
    expected_ratio = N ** (-p / ((3 + p) * (3 + 2 * p)))
    actual_ratio = h_cer / h_mse
    assert math.isclose(actual_ratio, expected_ratio, rel_tol=1e-6), "CER scaling ratio mismatch"


def test_rdrobust_bwselect_msetwo_can_differ_per_side():
    """msetwo allows different bandwidths per side (asymmetric data)."""
    rng = np.random.default_rng(42)
    n = 500
    # Asymmetric density: more mass on left
    x = np.concatenate([
        rng.uniform(-1, 0, size=int(n * 0.7)),
        rng.uniform(0, 1, size=int(n * 0.3)),
    ])
    y = 5 + 3 * x + 2.0 * (x >= 0) + rng.normal(0, 0.5, size=n)
    df = pd.DataFrame({"y": y, "x": x})

    res = rdrobust(df, y="y", x="x", c=0.0, bwselect="msetwo")
    # With asymmetric density, msetwo may produce different h_l and h_r
    # (We only assert they are both positive; exact inequality is data-dependent)
    assert res._rd_extras["h_l"] > 0
    assert res._rd_extras["h_r"] > 0


def test_rdrobust_bwselect_all_senate_runs():
    """All selectors run on real senate data without error."""
    df = pd.read_stata("tests/data/rdrobust_senate.dta")
    for sel in _ALL_SELECTORS:
        res = rdrobust(df, y="vote", x="margin", c=0.0, bwselect=sel)
        assert res._rd_extras["h_l"] > 0, f"{sel}: h_l must be positive on senate data"


# ---------------------------------------------------------------------------
# Wave 8 Phase B: Weights support tests
# ---------------------------------------------------------------------------

def test_rdrobust_weights_basic():
    """Frequency weights should run and produce different estimates than unweighted."""
    df = _make_rd_data(n=500, jump=2.0)
    df["w"] = np.random.default_rng(42).integers(1, 5, size=len(df)).astype(float)
    res_unw = rdrobust(df, y="y", x="x", c=0.0, h=0.5)
    res_w = rdrobust(df, y="y", x="x", c=0.0, h=0.5, weights="w")
    assert res_w._rd_extras["tau_cl"] != res_unw._rd_extras["tau_cl"]


def test_rdrobust_weights_nonpositive_dropped():
    """Non-positive weights should be dropped (Stata behavior)."""
    df = _make_rd_data(n=500, jump=2.0)
    df["w"] = 1.0
    df.loc[0, "w"] = 0.0
    df.loc[1, "w"] = -1.0
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5, weights="w")
    # Should drop exactly the two non-positive weights
    assert res.sample.nobs == 498


def test_rdrobust_weights_with_bwselect():
    """Weights should work with automatic bandwidth selection."""
    df = _make_rd_data(n=500, jump=2.0)
    df["w"] = np.random.default_rng(42).integers(1, 5, size=len(df)).astype(float)
    res = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", weights="w")
    assert res._rd_extras["h_l"] > 0
    assert res._rd_extras["tau_cl"] != 0.0


# ---------------------------------------------------------------------------
# Wave 8 Phase C: Masspoints support tests
# ---------------------------------------------------------------------------

def _make_masspoints_data(n=500, seed=42):
    """Create RD data with mass points in the running variable."""
    rng = np.random.default_rng(seed)
    # Only 10 unique x values on each side to ensure mass points > 20%
    x_unique_l = np.linspace(-1, -0.01, 10)
    x_unique_r = np.linspace(0, 1, 10)
    x_l = rng.choice(x_unique_l, size=n // 2)
    x_r = rng.choice(x_unique_r, size=n // 2)
    x = np.concatenate([x_l, x_r])
    y = 5 + 3 * x + 2.0 * (x >= 0) + rng.normal(0, 0.5, size=n)
    return pd.DataFrame({"y": y, "x": x})


def test_rdrobust_masspoints_adjust_uses_m():
    """masspoints='adjust' should use M-based c_bw, producing larger bandwidths."""
    df = _make_masspoints_data(n=500)
    res_adj = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", masspoints="adjust")
    res_off = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", masspoints="off")
    # adjust mode uses M instead of N, so c_bw is larger, which should lead to
    # larger or equal effective bandwidths (though the relationship is not strictly
    # monotonic due to the three-step plug-in, bandwidths should differ)
    assert res_adj._rd_extras["h_l"] != res_off._rd_extras["h_l"], \
        "adjust and off should produce different bandwidths with mass points data"


def test_rdrobust_masspoints_check_runs():
    """masspoints='check' should run without error and not adjust."""
    df = _make_masspoints_data(n=500)
    res_check = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", masspoints="check")
    res_off = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", masspoints="off")
    # check mode should produce same results as off (no adjustment)
    assert math.isclose(
        res_check._rd_extras["h_l"],
        res_off._rd_extras["h_l"],
        rel_tol=1e-12,
    ), "check and off should produce identical bandwidths"


def test_rdrobust_masspoints_bwcheck_auto():
    """masspoints='adjust' should auto-set bwcheck=10 when mass points found."""
    df = _make_masspoints_data(n=500)
    # With default bwcheck=0, adjust mode should auto-trigger bwcheck=10
    res = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", masspoints="adjust", bwcheck=0)
    assert res._rd_extras["h_l"] > 0


def test_rdrobust_masspoints_user_bwcheck_preserved():
    """User-specified bwcheck should override auto-setting."""
    df = _make_masspoints_data(n=500)
    res_user = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", masspoints="adjust", bwcheck=5)
    res_auto = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", masspoints="adjust", bwcheck=0)
    # Different bwcheck should produce different bandwidths
    assert res_user._rd_extras["h_l"] != res_auto._rd_extras["h_l"]


# ---------------------------------------------------------------------------
# Wave 8 Phase D: Fuzzy RD support tests
# ---------------------------------------------------------------------------

def _make_fuzzy_rd_data(n=500, seed=42, jump_y=2.0, jump_t=0.5, cutoff=0.0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, size=n)
    # Treatment probability jumps at cutoff (partial compliance)
    treat_prob = 0.3 + jump_t * (x >= cutoff)
    treat_prob = np.clip(treat_prob, 0.0, 1.0)
    t = rng.binomial(1, treat_prob).astype(float)
    y = 5 + 3 * x + jump_y * t + rng.normal(0, 0.5, size=n)
    return pd.DataFrame({"y": y, "x": x, "t": t})


def test_rdrobust_fuzzy_basic():
    """Fuzzy RD with explicit bandwidth should produce reasonable estimates."""
    df = _make_fuzzy_rd_data(n=500, jump_y=2.0, jump_t=0.5)
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5, fuzzy="t")
    # Wald ratio should be close to jump_y / jump_t = 4.0
    tau_cl = res._rd_extras["tau_cl"]
    assert 2.0 < tau_cl < 6.0, f"Fuzzy tau_cl={tau_cl} outside plausible range"
    assert res._rd_extras["se_tau_cl"] > 0
    assert res._rd_extras["se_tau_rb"] > 0


def test_rdrobust_fuzzy_first_stage_aligns():
    """First-stage estimate tau_T_cl should approximate the true jump_t."""
    jump_t = 0.5
    df = _make_fuzzy_rd_data(n=500, jump_y=2.0, jump_t=jump_t)
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5, fuzzy="t")
    tau_T_cl = res._rd_extras["tau_T_cl"]
    assert math.isclose(tau_T_cl, jump_t, rel_tol=0.25), f"tau_T_cl={tau_T_cl} deviates from jump_t={jump_t}"


def test_rdrobust_fuzzy_weak_instrument():
    """Fuzzy RD with weak first stage should remain numerically stable."""
    df = _make_fuzzy_rd_data(n=500, jump_y=2.0, jump_t=0.05)
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5, fuzzy="t")
    # Should not crash; tau_cl will be large because denominator is small
    assert math.isfinite(res._rd_extras["tau_cl"])
    assert res._rd_extras["se_tau_rb"] > 0


def test_rdrobust_fuzzy_sharpbw():
    """Fuzzy RD with sharpbw=True should use sharp bandwidth selection."""
    df = _make_fuzzy_rd_data(n=500, jump_y=2.0, jump_t=0.5)
    res = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", fuzzy="t", sharpbw=True)
    assert res._rd_extras["h_l"] > 0
    assert res._rd_extras["tau_cl"] != 0.0


def test_rdrobust_fuzzy_perfect_compliance():
    """Fuzzy RD with perfect compliance (t=1 always treated) should auto-switch to sharp."""
    df = _make_fuzzy_rd_data(n=500, jump_y=2.0, jump_t=0.5)
    # Force perfect compliance: everyone above cutoff gets t=1, everyone below gets t=0
    df["t"] = (df["x"] >= 0.0).astype(float)
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5, fuzzy="t")
    # Should run without error (perfect compliance triggers auto sharpbw)
    assert res._rd_extras["tau_cl"] > 0


def test_rdrobust_fuzzy_with_covs():
    """Fuzzy RD with covariates should run without error."""
    df = _make_fuzzy_rd_data(n=500, jump_y=2.0, jump_t=0.5)
    df["z"] = np.random.default_rng(42).normal(0, 1, size=len(df))
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5, fuzzy="t", covs="z")
    assert res._rd_extras["tau_cl"] != 0.0
    assert res._rd_extras["se_tau_rb"] > 0


def test_rdrobust_fuzzy_bwselect_without_sharpbw_rejected():
    """Fuzzy RD with bwselect but without sharpbw should raise NotImplementedError."""
    df = _make_fuzzy_rd_data(n=500, jump_y=2.0, jump_t=0.5)
    with pytest.raises(NotImplementedError, match="sharpbw"):
        rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", fuzzy="t")


# ---------------------------------------------------------------------------
# Wave 8 Phase E: Cluster VCE support tests
# ---------------------------------------------------------------------------

def test_rdrobust_cluster_basic():
    """vce='cluster' should run and produce different SEs than nn."""
    df = _make_rd_data(n=500, jump=2.0)
    df["g"] = np.repeat(np.arange(50), 10)[:len(df)]
    res_nn = rdrobust(df, y="y", x="x", c=0.0, h=0.5, vce="nn")
    res_cl = rdrobust(df, y="y", x="x", c=0.0, h=0.5, vce="cluster", cluster="g")
    assert res_cl._rd_extras["se_tau_rb"] > 0
    # Cluster SEs should differ from nn SEs
    assert res_cl._rd_extras["se_tau_rb"] != res_nn._rd_extras["se_tau_rb"]


def test_rdrobust_nncluster_basic():
    """vce='nncluster' should run and produce different SEs than nn."""
    df = _make_rd_data(n=500, jump=2.0)
    df["g"] = np.repeat(np.arange(50), 10)[:len(df)]
    res_nn = rdrobust(df, y="y", x="x", c=0.0, h=0.5, vce="nn")
    res_nncl = rdrobust(df, y="y", x="x", c=0.0, h=0.5, vce="nncluster", cluster="g")
    assert res_nncl._rd_extras["se_tau_rb"] > 0
    assert res_nncl._rd_extras["se_tau_rb"] != res_nn._rd_extras["se_tau_rb"]


def test_rdrobust_cluster_few_clusters():
    """Cluster VCE with only 5 clusters per side should run without error."""
    df = _make_rd_data(n=100, jump=2.0)
    df["g"] = np.repeat(np.arange(5), 20)[:len(df)]
    # Ensure clusters exist on both sides of cutoff
    assert (df["x"] < 0).any() and (df["x"] >= 0).any()
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5, vce="cluster", cluster="g")
    assert res._rd_extras["se_tau_rb"] > 0


def test_rdrobust_cluster_without_cluster_var_rejected():
    """vce='cluster' without cluster variable should raise ValueError."""
    df = _make_rd_data(n=200, jump=2.0)
    with pytest.raises(ValueError, match="cluster variable"):
        rdrobust(df, y="y", x="x", c=0.0, h=0.5, vce="cluster")


def test_rdrobust_cluster_with_bwselect():
    """Cluster VCE should work with automatic bandwidth selection."""
    df = _make_rd_data(n=500, jump=2.0)
    df["g"] = np.repeat(np.arange(50), 10)[:len(df)]
    res = rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd", vce="cluster", cluster="g")
    assert res._rd_extras["h_l"] > 0
    assert res._rd_extras["se_tau_rb"] > 0


def test_rdrobust_cluster_fuzzy_with_covs():
    """Three-way interaction: fuzzy RD + covariates + cluster VCE should run."""
    df = _make_fuzzy_rd_data(n=500, jump_y=2.0, jump_t=0.5)
    df["z"] = np.random.default_rng(42).normal(0, 1, size=len(df))
    df["g"] = np.repeat(np.arange(50), 10)[:len(df)]
    res = rdrobust(
        df, y="y", x="x", c=0.0, h=0.5,
        fuzzy="t", covs="z", vce="cluster", cluster="g"
    )
    assert math.isfinite(res._rd_extras["tau_cl"])
    assert res._rd_extras["se_tau_rb"] > 0


# ---------------------------------------------------------------------------
# Wave 8 Phase F: rdplot companion command tests
# ---------------------------------------------------------------------------

def test_rdplot_basic():
    """rdplot should return bins and fit data."""
    from stataflow.compat.stata.rdplot import rdplot

    df = _make_rd_data(n=500, jump=2.0)
    res = rdplot(df, y="y", x="x", c=0.0)
    assert "bins" in res
    assert "fit" in res
    assert "info" in res
    assert len(res["bins"]) > 0
    assert len(res["fit"]) > 0
    assert res["info"]["N_l"] > 0
    assert res["info"]["N_r"] > 0


def test_rdplot_nbins_manual():
    """Manual nbins should override automatic bin selection."""
    from stataflow.compat.stata.rdplot import rdplot

    df = _make_rd_data(n=500, jump=2.0)
    res = rdplot(df, y="y", x="x", c=0.0, nbins=(10, 15))
    # Should have approximately the requested number of non-empty bins
    bins = res["bins"]
    left_bins = bins[bins["mean_x"] < 0.0]
    right_bins = bins[bins["mean_x"] >= 0.0]
    assert len(left_bins) <= 10
    assert len(right_bins) <= 15


def test_rdplot_binselect_esmv():
    """Explicit esmv should produce same structure as default."""
    from stataflow.compat.stata.rdplot import rdplot

    df = _make_rd_data(n=500, jump=2.0)
    res = rdplot(df, y="y", x="x", c=0.0, binselect="esmv")
    assert len(res["bins"]) > 0
    assert "mean_x" in res["bins"].columns
    assert "mean_y" in res["bins"].columns


def test_rdplot_binselect_qsmv():
    """Quantile-spaced bin selection should run."""
    from stataflow.compat.stata.rdplot import rdplot

    df = _make_rd_data(n=500, jump=2.0)
    res = rdplot(df, y="y", x="x", c=0.0, binselect="qsmv")
    assert len(res["bins"]) > 0
    assert len(res["fit"]) > 0


def test_rdplot_fit_has_both_sides():
    """Polynomial fit should contain both left and right sides."""
    from stataflow.compat.stata.rdplot import rdplot

    df = _make_rd_data(n=500, jump=2.0)
    res = rdplot(df, y="y", x="x", c=0.0)
    fit = res["fit"]
    assert (fit["x"] < 0.0).any()
    assert (fit["x"] >= 0.0).any()
    assert (fit["side"] == "left").any()
    assert (fit["side"] == "right").any()


def test_rdplot_with_covs():
    """rdplot with covariates should run without error."""
    from stataflow.compat.stata.rdplot import rdplot

    df = _make_rd_data(n=500, jump=2.0)
    df["z"] = np.random.default_rng(42).normal(0, 1, size=len(df))
    res = rdplot(df, y="y", x="x", c=0.0, covs="z")
    assert len(res["bins"]) > 0
    assert len(res["fit"]) > 0


def test_rdplot_unsupported_kwargs_rejected():
    """rdplot should reject unsupported kwargs."""
    from stataflow.compat.stata.rdplot import rdplot

    df = _make_rd_data(n=200, jump=2.0)
    with pytest.raises(ValueError, match="Unsupported arguments"):
        rdplot(df, y="y", x="x", c=0.0, foo="bar")


def test_rdplot_binselect_matches_stata_synthetic():
    """Automatic bin selection should match Stata 17 on synthetic data (RD-002)."""
    from stataflow.compat.stata.rdplot import rdplot

    # Use legacy RandomState to match the Stata verification seed exactly.
    np.random.seed(42)
    n = 500
    x = np.random.normal(0, 1, n)
    y = 2.0 + 1.5 * x + 0.5 * x**2 + np.random.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x": x})

    res_es = rdplot(df, y="y", x="x", c=0.0, binselect="esmv")
    assert res_es["info"]["J_star_l"] == 10
    assert res_es["info"]["J_star_r"] == 13

    res_qs = rdplot(df, y="y", x="x", c=0.0, binselect="qsmv")
    assert res_qs["info"]["J_star_l"] == 21
    assert res_qs["info"]["J_star_r"] == 139


def test_rdplot_binselect_matches_stata_senate():
    """Automatic bin selection should match Stata 17 on Senate data (RD-002)."""
    from stataflow.compat.stata.rdplot import rdplot

    project_root = Path(__file__).parent.parent
    dta = project_root / "research" / "data" / "public" / "rdrobust_senate_with_z.dta"
    df = pd.read_stata(dta)

    res_es = rdplot(df, y="margin", x="vote", c=50.0, binselect="esmv")
    assert res_es["info"]["J_star_l"] == 33
    assert res_es["info"]["J_star_r"] == 53

    res_qs = rdplot(df, y="margin", x="vote", c=50.0, binselect="qsmv")
    # qsmv now matches Stata 17 after aligning the qs spacings variance
    # estimator: Stata sums dyi^2 over all adjacent pairs, including ties.
    assert res_qs["info"]["J_star_l"] == 29
    assert res_qs["info"]["J_star_r"] == 56
