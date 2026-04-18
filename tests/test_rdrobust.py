"""Tests for rdrobust sharp RD minimal subset.

Includes synthetic controlled cases, real-data dual-run alignment
against Stata 17, and negative tests for boundary behavior.
"""

import math

import numpy as np
import pandas as pd
import pytest

from statapy.compat.stata import rdrobust
from statapy.estimators.rdrobust import RDRobust


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
        "research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta"
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
        "research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta"
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


def test_rdrobust_unsupported_kwargs_rejected():
    df = _make_rd_data(n=200, jump=2.0)
    with pytest.raises(ValueError, match="Unsupported arguments"):
        rdrobust(df, y="y", x="x", c=0.0, h=0.5, fuzzy="treatment")


def test_rdrobust_missing_bandwidth_rejected():
    df = _make_rd_data(n=200, jump=2.0)
    with pytest.raises(NotImplementedError, match="Automatic bandwidth selection"):
        rdrobust(df, y="y", x="x", c=0.0)


def test_rdrobust_fuzzy_rejected_at_estimator():
    df = _make_rd_data(n=200, jump=2.0)
    with pytest.raises(ValueError, match="Unsupported arguments"):
        rdrobust(df, y="y", x="x", c=0.0, h=0.5, fuzzy="treatment")


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
        "research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta"
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
    df = pd.read_stata("stata/output/rdrobust_senate_with_z.dta")
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
    df = pd.read_stata("stata/output/rdrobust_senate_with_z.dta")
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
        "research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta"
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
    with pytest.raises(NotImplementedError, match="bwselect='msetwo' is not supported"):
        rdrobust(df, y="y", x="x", c=0.0, bwselect="msetwo")


def test_rdrobust_resultschema_model_command():
    df = _make_rd_data(n=100, jump=2.0)
    res = rdrobust(df, y="y", x="x", c=0.0, h=0.5)
    assert res.model.command == "rdrobust"
    assert res.provenance.stata_version_target == "17"
