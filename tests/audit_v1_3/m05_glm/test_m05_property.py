"""M05 GLM: metamorphic / property tests."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from m05_audit_utils import (
    STATA_CASES,
    glm_stata_do_template,
    run_stata_do,
    python_result_to_dict,
    compare_coefficients,
    save_evidence,
)

from stataflow.estimators import Logit


def _coef_dict(result_dict):
    return {c["name"]: c for c in result_dict["coefficients"]}


def _fit_python(df, y, x, vce="ols", cluster=None):
    return Logit(df, y=y, x=x).fit(vce=vce, cluster=cluster)


def test_p1_row_order_invariance():
    """P1: shuffling rows does not change estimates or VCE."""
    test_id = "P1_row_order_invariance"
    rng = np.random.default_rng(2025061207)
    n = 120
    g = np.repeat(np.arange(1, 21), 6)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g})
    df_shuffled = df.sample(frac=1.0, random_state=2025061207).reset_index(drop=True)

    csv_orig = STATA_CASES / f"{test_id}_orig.csv"
    csv_shuf = STATA_CASES / f"{test_id}_shuf.csv"
    df.to_csv(csv_orig, index=False)
    df_shuffled.to_csv(csv_shuf, index=False)

    st_orig = run_stata_do(glm_stata_do_template(str(csv_orig), "logit y x1 x2, vce(robust)", y_var="y"), f"{test_id}_orig")
    st_shuf = run_stata_do(glm_stata_do_template(str(csv_shuf), "logit y x1 x2, vce(robust)", y_var="y"), f"{test_id}_shuf")

    py_orig = python_result_to_dict(_fit_python(df, "y", ["x1", "x2"], vce="robust"))
    py_shuf = python_result_to_dict(_fit_python(df_shuffled, "y", ["x1", "x2"], vce="robust"))

    comparisons = []
    comparisons.extend(compare_coefficients(py_orig["coefficients"], py_shuf["coefficients"], rtol=1e-12, atol=1e-12))
    comparisons.extend(compare_coefficients(st_orig.get("coefficients", []), st_shuf.get("coefficients", []), rtol=1e-12, atol=1e-12))
    save_evidence(test_id, py_orig, st_orig, comparisons, data=df)
    assert all(p for p, _ in comparisons), "\n".join(m for _, m in comparisons if not _)


def test_p2_scale_transform():
    """P2: scaling a continuous regressor scales its coefficient and VCE inversely."""
    test_id = "P2_scale_transform"
    rng = np.random.default_rng(2025061208)
    n = 150
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    scale = 10.0
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "x1s": x1 * scale})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)
    st_base = run_stata_do(glm_stata_do_template(str(csv), "logit y x1 x2", y_var="y"), f"{test_id}_base")
    st_scaled = run_stata_do(glm_stata_do_template(str(csv), "logit y x1s x2", y_var="y"), f"{test_id}_scaled")

    py_base = python_result_to_dict(_fit_python(df, "y", ["x1", "x2"]))
    py_scaled = python_result_to_dict(_fit_python(df, "y", ["x1s", "x2"]))

    base_coef = _coef_dict(py_base)
    scaled_coef = _coef_dict(py_scaled)
    # Coefficient on scaled x should be 1/scale of original
    assert np.isclose(scaled_coef["x1s"]["beta"] * scale, base_coef["x1"]["beta"], rtol=1e-10)
    # SE should also scale by 1/scale
    assert np.isclose(scaled_coef["x1s"]["std_err"] * scale, base_coef["x1"]["std_err"], rtol=1e-10)
    # x2 and _cons should be unchanged
    assert np.isclose(scaled_coef["x2"]["beta"], base_coef["x2"]["beta"], rtol=1e-10)
    assert np.isclose(scaled_coef["_cons"]["beta"], base_coef["_cons"]["beta"], rtol=1e-10)

    # Stata check: compare transformed scaled coefficients to base
    st_base_coef = _coef_dict({"coefficients": st_base.get("coefficients", [])})
    st_scaled_coef = _coef_dict({"coefficients": st_scaled.get("coefficients", [])})
    comparisons = [
        (np.isclose(st_scaled_coef["x1s"]["beta"] * scale, st_base_coef["x1"]["beta"], rtol=1e-6), "Stata scaled x1 beta inverse-scale"),
        (np.isclose(st_scaled_coef["x1s"]["std_err"] * scale, st_base_coef["x1"]["std_err"], rtol=1e-6), "Stata scaled x1 SE inverse-scale"),
        (np.isclose(st_scaled_coef["x2"]["beta"], st_base_coef["x2"]["beta"], rtol=1e-12), "Stata x2 unchanged"),
        (np.isclose(st_scaled_coef["_cons"]["beta"], st_base_coef["_cons"]["beta"], rtol=1e-12), "Stata _cons unchanged"),
    ]
    save_evidence(test_id, py_base, st_base, comparisons, data=df)
    assert all(p for p, _ in comparisons), "\n".join(m for p, m in comparisons if not p)


def test_p3_redundant_variable():
    """P3: adding a redundant collinear variable should drop it and leave other coefficients unchanged."""
    test_id = "P3_redundant_variable"
    rng = np.random.default_rng(2025061209)
    n = 120
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    x3 = 2.0 * x1
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df_base = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
    df_red = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "x3": x3})

    csv_base = STATA_CASES / f"{test_id}_base.csv"
    csv_red = STATA_CASES / f"{test_id}_red.csv"
    df_base.to_csv(csv_base, index=False)
    df_red.to_csv(csv_red, index=False)

    st_base = run_stata_do(glm_stata_do_template(str(csv_base), "logit y x1 x2", y_var="y"), f"{test_id}_base")
    st_red = run_stata_do(glm_stata_do_template(str(csv_red), "logit y x1 x2 x3", y_var="y"), f"{test_id}_red")

    py_base = python_result_to_dict(_fit_python(df_base, "y", ["x1", "x2"]))
    py_red = python_result_to_dict(_fit_python(df_red, "y", ["x1", "x2", "x3"]))

    # Python should drop x3
    red_names = [c["name"] for c in py_red["coefficients"]]
    assert "x3" not in red_names
    assert py_red.get("dropped_vars") == ["x3"]

    # Remaining coefficients should match base exactly
    comparisons = compare_coefficients(py_base["coefficients"], py_red["coefficients"], rtol=1e-12, atol=1e-12)

    # Stata: x3 should be omitted (name may be prefixed "o.x3" or simply omitted)
    st_red_names = [c["name"] for c in st_red.get("coefficients", [])]
    assert any("x3" in n for n in st_red_names)
    save_evidence(test_id, py_base, st_base, comparisons, data=df_base)
    assert all(p for p, _ in comparisons), "\n".join(m for _, m in comparisons if not _)
