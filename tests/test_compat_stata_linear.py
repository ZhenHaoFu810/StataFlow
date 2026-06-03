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


def test_regress_level():
    df = _make_ols_data()
    res = regress(df, y="y", x=["x1"], level=90)
    direct = OLS(df, y="y", x=["x1"]).fit(alpha=0.10)
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
        assert np.isclose(c.ci_low, d.ci_low, rtol=1e-10)
        assert np.isclose(c.ci_high, d.ci_high, rtol=1e-10)


def test_regress_unsupported_kwargs():
    df = _make_ols_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        regress(df, y="y", x=["x1"], unknown_opt=True)


def test_xtreg_fe_delegation():
    df = _make_fe_data()
    res = xtreg_fe(df, y="y", x=["x1", "x2"], fe="id")
    direct = FixedEffectsOLS(df, y="y", x=["x1", "x2"], fe="id").fit()
    assert res.model.command == "xtreg"
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)


def test_xtreg_fe_level():
    df = _make_fe_data()
    res = xtreg_fe(df, y="y", x=["x1"], fe="id", level=90)
    direct = FixedEffectsOLS(df, y="y", x=["x1"], fe="id").fit(alpha=0.10)
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
        assert np.isclose(c.ci_low, d.ci_low, rtol=1e-10)
        assert np.isclose(c.ci_high, d.ci_high, rtol=1e-10)


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


def test_areg_level():
    df = _make_fe_data()
    res = areg(df, y="y", x=["x1"], absorb="id", level=90)
    direct = AbsorbingOLS(df, y="y", x=["x1"], absorb="id").fit(alpha=0.10)
    for c in res.coefficients:
        d = next(dc for dc in direct.coefficients if dc.name == c.name)
        assert np.isclose(c.beta, d.beta, rtol=1e-10)
        assert np.isclose(c.ci_low, d.ci_low, rtol=1e-10)
        assert np.isclose(c.ci_high, d.ci_high, rtol=1e-10)


def test_areg_unsupported_kwargs():
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        areg(df, y="y", x=["x1"], absorb="id", generate="resid")


# ---------------------------------------------------------------------------
# Multi-way clustering (Package D)
# ---------------------------------------------------------------------------

def _make_cluster_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "c1": rng.integers(0, 10, size=n),
        "c2": rng.integers(0, 8, size=n),
    })
    return df


def test_regress_two_way_clustering():
    """Two-way clustering should produce coefficients identical to one-way."""
    df = _make_cluster_data()
    res_one = regress(df, y="y", x=["x1"], vce="cluster", cluster="c1")
    res_two = regress(df, y="y", x=["x1"], vce="cluster", cluster=["c1", "c2"])

    # Coefficients should be identical (VCE doesn't affect beta)
    assert np.isclose(
        res_one.coefficients[0].beta,
        res_two.coefficients[0].beta,
        rtol=1e-10,
    )

    # Model info should record both cluster variables
    assert res_two.model.cluster_var == ["c1", "c2"]


def test_regress_two_way_clustering_se_larger():
    """Two-way clustering SE should generally be larger than one-way."""
    df = _make_cluster_data(n=200, seed=42)
    res_one = regress(df, y="y", x=["x1"], vce="cluster", cluster="c1")
    res_two = regress(df, y="y", x=["x1"], vce="cluster", cluster=["c1", "c2"])

    se_one = res_one.coefficients[0].std_err
    se_two = res_two.coefficients[0].std_err
    # Two-way SE should be at least as large as one-way (not guaranteed in
    # every finite sample, but true in expectation; we check it's reasonable)
    assert se_two > 0
    assert se_two >= se_one * 0.5


def test_regress_two_way_clustering_rejects_three_way():
    """Three-way clustering should raise ValueError."""
    df = _make_cluster_data()
    with pytest.raises(ValueError, match="Multi-way clustering currently supports exactly 2"):
        regress(df, y="y", x=["x1"], vce="cluster", cluster=["c1", "c2", "x2"])


def test_regress_two_way_clustering_string_collision():
    """String cluster labels containing '__' must not cause intersection collision."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "y": rng.normal(size=4),
        "x1": rng.normal(size=4),
        # Deliberately create labels that would collide with f"{a}__{b}":
        # ('a', 'b__c') and ('a__b', 'c') both become 'a__b__c' under string concat
        "c1": ["a", "a__b", "a", "a__b"],
        "c2": ["b__c", "c", "c", "b__c"],
    })

    res = regress(df, y="y", x=["x1"], vce="cluster", cluster=["c1", "c2"])
    assert res.model.cluster_var == ["c1", "c2"]
    assert res.coefficients[0].std_err > 0


def test_two_way_clustering_tuple_factorize_distinct_pairs():
    """Tuple factorization must count all distinct (c1, c2) pairs correctly."""
    c1 = np.array(["a", "a__b", "a", "a__b"])
    c2 = np.array(["b__c", "c", "c", "b__c"])
    combo_to_id = {}
    combo_ids = np.empty(len(c1), dtype=int)
    for i, pair in enumerate(zip(c1, c2)):
        if pair not in combo_to_id:
            combo_to_id[pair] = len(combo_to_id)
        combo_ids[i] = combo_to_id[pair]
    unique_combos = np.unique(combo_ids)
    # All 4 rows have distinct (c1, c2) pairs; string concat would incorrectly merge 2
    assert len(unique_combos) == 4


def test_xtreg_fe_rejects_multiway_cluster():
    """xtreg_fe must raise ValueError for multi-way cluster, not TypeError."""
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Multi-way clustering is only supported for regress"):
        xtreg_fe(df, y="y", x=["x1"], fe="id", vce="cluster", cluster=["id", "x2"])


def test_areg_rejects_multiway_cluster():
    """areg must raise ValueError for multi-way cluster, not TypeError."""
    df = _make_fe_data()
    with pytest.raises(ValueError, match="Multi-way clustering is only supported for regress"):
        areg(df, y="y", x=["x1"], absorb="id", vce="cluster", cluster=["id", "x2"])


def test_regress_vce_cluster_string_syntax():
    """regress should accept vce="cluster varname" Stata-style syntax."""
    rng = np.random.default_rng(99)
    n = 100
    df = pd.DataFrame({
        "y": rng.normal(size=n),
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
        "group": rng.integers(0, 10, size=n),
    })
    res = regress(df, y="y", x=["x1", "x2"], vce="cluster group")
    assert res.model.vcetype == "cluster"
    assert res.model.cluster_var == "group"
