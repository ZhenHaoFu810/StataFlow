"""Tests for Stata factor-variable parser and wrapper integration.

Covers:
- parser unit tests for c., i., #, ##
- absorb string parsing
- explicit rejection of unsupported syntax
- equivalence against manually-constructed design matrices
- absorbed-FE collinearity behavior (main effects dropped, interactions kept)
"""

import numpy as np
import pandas as pd
import pytest

from statapy.compat.stata.factor_variables import (
    expand_factor_terms,
    parse_absorb,
    _expand_single_term,
)
from statapy.compat.stata import regress, reghdfe, logit, ivreghdfe, ppmlhdfe


# ---------------------------------------------------------------------------
# Parser unit tests
# ---------------------------------------------------------------------------

def test_parse_absorb_list():
    assert parse_absorb(["firm", "year"]) == ["firm", "year"]


def test_parse_absorb_string():
    assert parse_absorb("firm year") == ["firm", "year"]
    assert parse_absorb("firm") == ["firm"]


def test_expand_bare_and_continuous_equivalent():
    df = pd.DataFrame({"x1": [1.0, 2.0, 3.0]})
    _, cols_bare = expand_factor_terms(df, ["x1"])
    _, cols_c = expand_factor_terms(df, ["c.x1"])
    assert cols_bare == ["x1"]
    assert cols_c == ["x1"]


def test_expand_indicator_omits_base():
    df = pd.DataFrame({"g": ["A", "B", "C", "A", "B"]})
    df_out, cols = expand_factor_terms(df, ["i.g"])
    assert cols == ["B.g", "C.g"]
    assert df_out["B.g"].tolist() == [0.0, 1.0, 0.0, 0.0, 1.0]
    assert df_out["C.g"].tolist() == [0.0, 0.0, 1.0, 0.0, 0.0]


def test_expand_continuous_interaction_only():
    df = pd.DataFrame({"x1": [1.0, 2.0, 3.0], "x2": [2.0, 0.0, 1.0]})
    df_out, cols = expand_factor_terms(df, ["c.x1#c.x2"])
    assert cols == ["c.x1#c.x2"]
    assert df_out["c.x1#c.x2"].tolist() == [2.0, 0.0, 3.0]


def test_expand_continuous_full_interaction():
    df = pd.DataFrame({"x1": [1.0, 2.0, 3.0], "x2": [2.0, 0.0, 1.0]})
    df_out, cols = expand_factor_terms(df, ["c.x1##c.x2"])
    assert cols == ["x1", "x2", "c.x1#c.x2"]


def test_expand_categorical_interaction_only():
    df = pd.DataFrame({"g1": ["a", "b", "a"], "g2": ["x", "x", "y"]})
    df_out, cols = expand_factor_terms(df, ["i.g1#i.g2"])
    # base for g1='a', g2='x' -> only b#y remains
    assert cols == ["b.g1#y.g2"]
    assert df_out["b.g1#y.g2"].tolist() == [0.0, 0.0, 0.0]


def test_expand_categorical_full_interaction():
    df = pd.DataFrame({"g1": ["a", "b", "a"], "g2": ["x", "x", "y"]})
    df_out, cols = expand_factor_terms(df, ["i.g1##i.g2"])
    assert "b.g1" in cols
    assert "y.g2" in cols
    assert "b.g1#y.g2" in cols
    # Order: main effects first, then interaction
    assert cols == ["b.g1", "y.g2", "b.g1#y.g2"]


def test_expand_categorical_continuous_interaction_only():
    df = pd.DataFrame({"g": ["a", "b", "a"], "x": [1.0, 2.0, 3.0]})
    df_out, cols = expand_factor_terms(df, ["i.g#c.x"])
    assert cols == ["b.g#c.x"]
    assert df_out["b.g#c.x"].tolist() == [0.0, 2.0, 0.0]


def test_expand_categorical_continuous_full_interaction():
    df = pd.DataFrame({"g": ["a", "b", "a"], "x": [1.0, 2.0, 3.0]})
    df_out, cols = expand_factor_terms(df, ["i.g##c.x"])
    assert cols == ["b.g", "x", "b.g#c.x"]


def test_expand_mixed_order_interaction_symmetric():
    """c.x#i.g must be equivalent to i.g#c.x in column names and values."""
    df = pd.DataFrame({"g": ["a", "b", "a"], "x": [1.0, 2.0, 3.0]})
    df_ig, cols_ig = expand_factor_terms(df.copy(), ["i.g#c.x"])
    df_ci, cols_ci = expand_factor_terms(df.copy(), ["c.x#i.g"])
    assert cols_ig == cols_ci
    for col in cols_ig:
        assert df_ig[col].tolist() == df_ci[col].tolist()


def test_expand_mixed_order_full_interaction_symmetric():
    """c.x##i.g must be equivalent to i.g##c.x in column names and values."""
    df = pd.DataFrame({"g": ["a", "b", "a"], "x": [1.0, 2.0, 3.0]})
    df_ig, cols_ig = expand_factor_terms(df.copy(), ["i.g##c.x"])
    df_ci, cols_ci = expand_factor_terms(df.copy(), ["c.x##i.g"])
    assert cols_ig == cols_ci
    for col in cols_ig:
        assert df_ig[col].tolist() == df_ci[col].tolist()


def test_expand_bare_continuous_interaction_only():
    """x1#x2 must be equivalent to c.x1#c.x2."""
    df = pd.DataFrame({"x1": [1.0, 2.0, 3.0], "x2": [2.0, 0.0, 1.0]})
    df_bare, cols_bare = expand_factor_terms(df.copy(), ["x1#x2"])
    df_exp, cols_exp = expand_factor_terms(df.copy(), ["c.x1#c.x2"])
    assert cols_bare == cols_exp
    for col in cols_bare:
        assert df_bare[col].tolist() == df_exp[col].tolist()


def test_expand_bare_continuous_full_interaction():
    """x1##x2 must be equivalent to c.x1##c.x2."""
    df = pd.DataFrame({"x1": [1.0, 2.0, 3.0], "x2": [2.0, 0.0, 1.0]})
    df_bare, cols_bare = expand_factor_terms(df.copy(), ["x1##x2"])
    df_exp, cols_exp = expand_factor_terms(df.copy(), ["c.x1##c.x2"])
    assert cols_bare == cols_exp
    for col in cols_bare:
        assert df_bare[col].tolist() == df_exp[col].tolist()


def test_expand_mixed_bare_explicit_continuous():
    """x1#c.x2 and c.x1#x2 must both be equivalent to c.x1#c.x2."""
    df = pd.DataFrame({"x1": [1.0, 2.0, 3.0], "x2": [2.0, 0.0, 1.0]})
    df_b1, cols_b1 = expand_factor_terms(df.copy(), ["x1#c.x2"])
    df_b2, cols_b2 = expand_factor_terms(df.copy(), ["c.x1#x2"])
    df_exp, cols_exp = expand_factor_terms(df.copy(), ["c.x1#c.x2"])
    assert cols_b1 == cols_exp
    assert cols_b2 == cols_exp
    for col in cols_exp:
        assert df_b1[col].tolist() == df_exp[col].tolist()
        assert df_b2[col].tolist() == df_exp[col].tolist()


def test_expand_mixed_bare_explicit_continuous_double():
    """x1##c.x2 and c.x1##x2 must both be equivalent to c.x1##c.x2."""
    df = pd.DataFrame({"x1": [1.0, 2.0, 3.0], "x2": [2.0, 0.0, 1.0]})
    df_b1, cols_b1 = expand_factor_terms(df.copy(), ["x1##c.x2"])
    df_b2, cols_b2 = expand_factor_terms(df.copy(), ["c.x1##x2"])
    df_exp, cols_exp = expand_factor_terms(df.copy(), ["c.x1##c.x2"])
    assert cols_b1 == cols_exp
    assert cols_b2 == cols_exp
    for col in cols_exp:
        assert df_b1[col].tolist() == df_exp[col].tolist()
        assert df_b2[col].tolist() == df_exp[col].tolist()


def test_expand_bare_categorical_full_interaction():
    """x1##i.g must be equivalent to c.x1##i.g."""
    df = pd.DataFrame({"g": ["a", "b", "a"], "x1": [1.0, 2.0, 3.0]})
    df_bare, cols_bare = expand_factor_terms(df.copy(), ["x1##i.g"])
    df_exp, cols_exp = expand_factor_terms(df.copy(), ["c.x1##i.g"])
    assert cols_bare == cols_exp
    for col in cols_bare:
        assert df_bare[col].tolist() == df_exp[col].tolist()


def test_expand_mixed_varlist():
    df = pd.DataFrame({"x1": [1.0, 2.0], "x2": [3.0, 4.0], "g": ["a", "b"]})
    df_out, cols = expand_factor_terms(df, ["x1", "c.x1#c.x2", "i.g"])
    assert cols == ["x1", "c.x1#c.x2", "b.g"]


def test_reject_time_series_operator():
    df = pd.DataFrame({"x": [1.0, 2.0]})
    with pytest.raises(ValueError, match="time-series operators"):
        expand_factor_terms(df, ["L.x"])


def test_reject_bare_base_indicator():
    df = pd.DataFrame({"g": ["a", "b"]})
    with pytest.raises(ValueError, match="base indicators"):
        expand_factor_terms(df, ["ib.g"])


def test_expand_explicit_base_ib():
    df = pd.DataFrame({"g": ["A", "B", "C", "A", "B"]})
    df_out, cols = expand_factor_terms(df, ["ib2.g"])
    # base = B (2nd sorted level), so A and C remain
    assert cols == ["A.g", "C.g"]
    assert df_out["A.g"].tolist() == [1.0, 0.0, 0.0, 1.0, 0.0]
    assert df_out["C.g"].tolist() == [0.0, 0.0, 1.0, 0.0, 0.0]


def test_expand_explicit_base_b():
    df = pd.DataFrame({"g": ["A", "B", "C", "A", "B"]})
    df_out, cols = expand_factor_terms(df, ["b2.g"])
    # b2.g is synonymous with ib2.g
    assert cols == ["A.g", "C.g"]


def test_expand_explicit_base_numeric():
    df = pd.DataFrame({"g": [1, 2, 3, 1, 2]})
    df_out, cols = expand_factor_terms(df, ["ib2.g"])
    # base = 2 (exact match), so 1 and 3 remain
    assert cols == ["1.g", "3.g"]
    assert df_out["1.g"].tolist() == [1.0, 0.0, 0.0, 1.0, 0.0]
    assert df_out["3.g"].tolist() == [0.0, 0.0, 1.0, 0.0, 0.0]


def test_expand_omit_level():
    df = pd.DataFrame({"g": ["A", "B", "C", "A", "B"]})
    df_out, cols = expand_factor_terms(df, ["o2.g"])
    # default base = A, omit B, so only C remains
    assert cols == ["C.g"]
    assert df_out["C.g"].tolist() == [0.0, 0.0, 1.0, 0.0, 0.0]


def test_expand_omit_level_numeric():
    df = pd.DataFrame({"g": [1, 2, 3, 1, 2]})
    df_out, cols = expand_factor_terms(df, ["o2.g"])
    # default base = 1, omit 2, so only 3 remains
    assert cols == ["3.g"]
    assert df_out["3.g"].tolist() == [0.0, 0.0, 1.0, 0.0, 0.0]


def test_reject_nonexistent_base_level():
    df = pd.DataFrame({"g": [1, 3, 3, 1]})
    with pytest.raises(ValueError, match="Specified level 2 not found"):
        expand_factor_terms(df, ["ib2.g"])


def test_reject_nonexistent_omitted_level():
    df = pd.DataFrame({"g": [1, 3, 3, 1]})
    with pytest.raises(ValueError, match="Specified level 2 not found"):
        expand_factor_terms(df, ["o2.g"])


def test_reject_three_way_interaction():
    df = pd.DataFrame({"x1": [1.0, 2.0], "x2": [3.0, 4.0], "x3": [5.0, 6.0]})
    with pytest.raises(ValueError, match="Unsupported factor term structure"):
        expand_factor_terms(df, ["c.x1#c.x2#c.x3"])


# ---------------------------------------------------------------------------
# Wrapper equivalence tests (factor syntax vs manually-constructed columns)
# ---------------------------------------------------------------------------

def _make_interaction_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "y": rng.normal(0, 1, size=n),
        "x1": rng.normal(0, 1, size=n),
        "x2": rng.normal(0, 1, size=n),
        "g": rng.choice(["A", "B", "C"], size=n),
        "firm": rng.choice(range(10), size=n),
        "year": rng.choice(range(5), size=n),
    })
    df["x1_x2"] = df["x1"] * df["x2"]
    df["g_B"] = (df["g"] == "B").astype(float)
    df["g_C"] = (df["g"] == "C").astype(float)
    df["g_B_x1"] = df["g_B"] * df["x1"]
    df["g_C_x1"] = df["g_C"] * df["x1"]
    return df


def test_regress_continuous_interaction_equals_manual():
    df = _make_interaction_data()
    res_factor = regress(df, y="y", x=["c.x1#c.x2"])
    res_manual = regress(df, y="y", x=["x1_x2"])
    assert pytest.approx(res_factor.coefficients[0].beta, rel=1e-10) == res_manual.coefficients[0].beta
    assert pytest.approx(res_factor.coefficients[0].std_err, rel=1e-10) == res_manual.coefficients[0].std_err


def test_regress_continuous_full_interaction_equals_manual():
    df = _make_interaction_data()
    res_factor = regress(df, y="y", x=["c.x1##c.x2"])
    res_manual = regress(df, y="y", x=["x1", "x2", "x1_x2"])
    for i in range(3):
        assert pytest.approx(res_factor.coefficients[i].beta, rel=1e-10) == res_manual.coefficients[i].beta
        assert pytest.approx(res_factor.coefficients[i].std_err, rel=1e-10) == res_manual.coefficients[i].std_err


def test_regress_categorical_continuous_full_interaction_equals_manual():
    df = _make_interaction_data()
    res_factor = regress(df, y="y", x=["i.g##c.x1"])
    res_manual = regress(df, y="y", x=["g_B", "g_C", "x1", "g_B_x1", "g_C_x1"])
    for i in range(5):
        assert pytest.approx(res_factor.coefficients[i].beta, rel=1e-10) == res_manual.coefficients[i].beta
        assert pytest.approx(res_factor.coefficients[i].std_err, rel=1e-10) == res_manual.coefficients[i].std_err


def test_reghdfe_absorb_space_separated_string():
    df = _make_interaction_data()
    res = reghdfe(df, y="y", x=["x1"], absorb="firm year")
    assert res.model.command == "reghdfe"
    # Basic sanity: should have coefficients
    assert len(res.coefficients) >= 1


def test_reghdfe_bare_continuous_full_interaction_equals_manual():
    """reghdfe with x1##x2 must match manual columns."""
    df = _make_interaction_data()
    res_factor = reghdfe(df, y="y", x=["x1##x2"], absorb="firm year")
    res_manual = reghdfe(df, y="y", x=["x1", "x2", "x1_x2"], absorb="firm year")
    py_names = [c.name for c in res_factor.coefficients]
    mn_names = [c.name for c in res_manual.coefficients]
    assert len(py_names) == len(mn_names)
    for pyc, mnc in zip(res_factor.coefficients, res_manual.coefficients):
        assert pytest.approx(pyc.beta, rel=1e-10) == mnc.beta
        assert pytest.approx(pyc.std_err, rel=1e-10) == mnc.std_err


def test_reghdfe_factor_interaction_with_absorb_main_effect_dropped():
    """
    In Stata: reghdfe y i.g##c.x1, absorb(g)
    The main-effect dummies for g are fully absorbed, but the interaction
    term (variation within g) should remain identifiable.
    """
    df = _make_interaction_data()
    # Use a clean 2-level group that is also the absorb variable
    df["absorb_g"] = df["g"]
    res = reghdfe(df, y="y", x=["i.g##c.x1"], absorb="absorb_g")
    # g:B main effect should be dropped (collinear with absorb_g FE)
    # x1 main effect should be kept
    # g:B#c.x1 interaction should be kept
    names = [c.name for c in res.coefficients]
    assert "B.g" not in names
    assert "x1" in names
    assert "B.g#c.x1" in names


def test_regress_explicit_base_full_interaction_equals_manual():
    """regress with ib2.g##c.x1 must match manually-constructed base-2 dummies."""
    df = _make_interaction_data()
    # g values are A, B, C; ib2.g -> base=B, so A and C remain
    df["g_A"] = (df["g"] == "A").astype(float)
    df["g_C"] = (df["g"] == "C").astype(float)
    df["g_A_x1"] = df["g_A"] * df["x1"]
    df["g_C_x1"] = df["g_C"] * df["x1"]
    res_factor = regress(df, y="y", x=["ib2.g##c.x1"])
    res_manual = regress(df, y="y", x=["g_A", "g_C", "x1", "g_A_x1", "g_C_x1"])
    py_names = [c.name for c in res_factor.coefficients]
    mn_names = [c.name for c in res_manual.coefficients]
    assert len(py_names) == len(mn_names)
    for pyc, mnc in zip(res_factor.coefficients, res_manual.coefficients):
        assert pytest.approx(pyc.beta, rel=1e-10) == mnc.beta
        assert pytest.approx(pyc.std_err, rel=1e-10) == mnc.std_err


def test_reghdfe_explicit_base_full_interaction_equals_manual():
    """reghdfe with ib2.g##c.x1 must match manually-constructed base-2 dummies."""
    df = _make_interaction_data()
    df["g_A"] = (df["g"] == "A").astype(float)
    df["g_C"] = (df["g"] == "C").astype(float)
    df["g_A_x1"] = df["g_A"] * df["x1"]
    df["g_C_x1"] = df["g_C"] * df["x1"]
    res_factor = reghdfe(df, y="y", x=["ib2.g##c.x1"], absorb="firm year")
    res_manual = reghdfe(df, y="y", x=["g_A", "g_C", "x1", "g_A_x1", "g_C_x1"], absorb="firm year")
    py_names = [c.name for c in res_factor.coefficients]
    mn_names = [c.name for c in res_manual.coefficients]
    assert len(py_names) == len(mn_names)
    for pyc, mnc in zip(res_factor.coefficients, res_manual.coefficients):
        assert pytest.approx(pyc.beta, rel=1e-10) == mnc.beta
        assert pytest.approx(pyc.std_err, rel=1e-10) == mnc.std_err


def test_logit_factor_syntax_runs_and_matches_manual():
    rng = np.random.default_rng(99)
    n = 200
    df = pd.DataFrame({
        "y": rng.binomial(1, 0.5, size=n),
        "x1": rng.normal(0, 1, size=n),
        "x2": rng.normal(0, 1, size=n),
    })
    df["x1_x2"] = df["x1"] * df["x2"]
    res_factor = logit(df, y="y", x=["c.x1##c.x2"])
    res_manual = logit(df, y="y", x=["x1", "x2", "x1_x2"])
    for i in range(3):
        assert pytest.approx(res_factor.coefficients[i].beta, rel=1e-10) == res_manual.coefficients[i].beta
        assert pytest.approx(res_factor.coefficients[i].std_err, rel=1e-10) == res_manual.coefficients[i].std_err


def test_reghdfe_mixed_order_factor_equals_manual():
    """reghdfe with c.x1##i.g should match manual dummy + interaction columns."""
    df = _make_interaction_data()
    res_factor = reghdfe(df, y="y", x=["c.x1##i.g"], absorb="firm year")
    res_manual = reghdfe(df, y="y", x=["g_B", "g_C", "x1", "g_B_x1", "g_C_x1"], absorb="firm year")
    py_names = [c.name for c in res_factor.coefficients]
    mn_names = [c.name for c in res_manual.coefficients]
    assert len(py_names) == len(mn_names)
    for pyc, mnc in zip(res_factor.coefficients, res_manual.coefficients):
        assert pytest.approx(pyc.beta, rel=1e-10) == mnc.beta
        assert pytest.approx(pyc.std_err, rel=1e-10) == mnc.std_err


def test_ivreghdfe_factor_syntax_equals_manual():
    """ivreghdfe with factor term in x_exog should match manual columns."""
    rng = np.random.default_rng(42)
    n = 300
    df = pd.DataFrame({
        "y": rng.normal(0, 1, size=n),
        "x1": rng.normal(0, 1, size=n),
        "x_endog": rng.normal(0, 1, size=n),
        "z1": rng.normal(0, 1, size=n),
        "z2": rng.normal(0, 1, size=n),
        "g": rng.choice(["A", "B", "C"], size=n),
        "firm": rng.choice(range(10), size=n),
        "year": rng.choice(range(5), size=n),
    })
    df["g_B"] = (df["g"] == "B").astype(float)
    df["g_C"] = (df["g"] == "C").astype(float)
    df["g_B_x1"] = df["g_B"] * df["x1"]
    df["g_C_x1"] = df["g_C"] * df["x1"]
    res_factor = ivreghdfe(
        df, y="y", x_exog=["c.x1##i.g"], x_endog=["x_endog"],
        instruments=["z1", "z2"], absorb="firm year"
    )
    res_manual = ivreghdfe(
        df, y="y", x_exog=["g_B", "g_C", "x1", "g_B_x1", "g_C_x1"], x_endog=["x_endog"],
        instruments=["z1", "z2"], absorb="firm year"
    )
    py_names = [c.name for c in res_factor.coefficients]
    mn_names = [c.name for c in res_manual.coefficients]
    assert len(py_names) == len(mn_names)
    for pyc, mnc in zip(res_factor.coefficients, res_manual.coefficients):
        assert pytest.approx(pyc.beta, rel=1e-10) == mnc.beta
        assert pytest.approx(pyc.std_err, rel=1e-10) == mnc.std_err


def test_ppmlhdfe_factor_syntax_equals_manual():
    """ppmlhdfe with i.g##c.x1 should match manual dummy + interaction columns."""
    rng = np.random.default_rng(123)
    n = 300
    df = pd.DataFrame({
        "y": rng.poisson(2, size=n).astype(float) + 0.1,
        "x1": rng.normal(0, 1, size=n),
        "g": rng.choice(["A", "B", "C"], size=n),
        "exporter": rng.choice(range(8), size=n),
        "importer": rng.choice(range(6), size=n),
    })
    df["g_B"] = (df["g"] == "B").astype(float)
    df["g_C"] = (df["g"] == "C").astype(float)
    df["g_B_x1"] = df["g_B"] * df["x1"]
    df["g_C_x1"] = df["g_C"] * df["x1"]
    res_factor = ppmlhdfe(
        df, y="y", x=["i.g##c.x1"], absorb="exporter importer"
    )
    res_manual = ppmlhdfe(
        df, y="y", x=["g_B", "g_C", "x1", "g_B_x1", "g_C_x1"], absorb="exporter importer"
    )
    py_names = [c.name for c in res_factor.coefficients]
    mn_names = [c.name for c in res_manual.coefficients]
    assert len(py_names) == len(mn_names)
    for pyc, mnc in zip(res_factor.coefficients, res_manual.coefficients):
        assert pytest.approx(pyc.beta, rel=1e-10) == mnc.beta
        assert pytest.approx(pyc.std_err, rel=1e-10) == mnc.std_err
