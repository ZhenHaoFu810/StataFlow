"""M06 PPMLHDFE metamorphic / property audit tests (P1-P3)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow.estimators import PPMLHDFE

from .m06_dgp import dgp_s2_two_way_fe
from .m06_audit_utils import (
    run_stata_ppmlhdfe,
    compare_python_to_stata,
    save_evidence,
    tolerance_close,
)


def _fit_py(df, x_vars, vce="robust", cluster=None):
    return PPMLHDFE(
        data=df,
        y="y",
        x=x_vars,
        absorb=["entity_id", "time_id"],
        separation="fe",
    ).fit(vce=vce, cluster=cluster)


def _run_stata(df, x_vars, prefix, vce="robust", cluster=None, predict_types=None):
    if vce == "cluster" and cluster is not None:
        cmd = f"ppmlhdfe y {' '.join(x_vars)}, absorb(entity_id time_id) vce(cluster {cluster})"
    else:
        cmd = f"ppmlhdfe y {' '.join(x_vars)}, absorb(entity_id time_id) vce(robust)"
    return run_stata_ppmlhdfe(
        df,
        command=cmd,
        y_var="y",
        prefix=prefix,
        coef_names=x_vars + ["_cons"],
        predict_types=predict_types,
    )


def _compare_coefs(py_result, st_result, prefix: str) -> dict:
    """Simple coefficient/SE comparison returning a diff dict."""
    diffs = {"passed": True, "messages": [], "field_results": {}}
    st_coefs = {c["name"]: c for c in st_result.get("coefficients", [])}
    for py_coef in py_result.coefficients:
        name = py_coef.name
        st_coef = st_coefs.get(name)
        if st_coef is None:
            diffs["passed"] = False
            diffs["messages"].append(f"{prefix}: Stata missing {name}")
            continue
        for metric in ["beta", "std_err", "t_stat", "p_value"]:
            py_val = getattr(py_coef, metric)
            st_val = st_coef.get("std_err" if metric == "std_err" else metric)
            if metric == "t_stat":
                st_val = st_coef.get("z_stat")
            passed, msg = tolerance_close(py_val, st_val, name=f"{prefix}.{name}.{metric}")
            diffs["field_results"][f"{prefix}.{name}.{metric}"] = {"passed": passed, "message": msg}
            if not passed:
                diffs["passed"] = False
            diffs["messages"].append(msg)
    return diffs


# ---------------------------------------------------------------------------
# P1: row-order invariance
# ---------------------------------------------------------------------------
def test_p1_row_order_invariance():
    df_base = dgp_s2_two_way_fe(seed=20260620)
    x_vars = ["x1", "x2"]

    # Python on original and shuffled rows
    rng = np.random.default_rng(20260621)
    shuffled_idx = rng.permutation(len(df_base))
    df_shuf = df_base.iloc[shuffled_idx].reset_index(drop=True)

    py_orig = _fit_py(df_base, x_vars)
    py_shuf = _fit_py(df_shuf, x_vars)

    for c_o, c_s in zip(py_orig.coefficients, py_shuf.coefficients):
        assert c_o.name == c_s.name
        assert np.isclose(c_o.beta, c_s.beta, rtol=1e-10, atol=1e-10)
        assert np.isclose(c_o.std_err, c_s.std_err, rtol=1e-10, atol=1e-10)

    # Align the shuffled sample mask back to original row order
    aligned_mask = np.empty(len(df_base), dtype=bool)
    aligned_mask[shuffled_idx] = np.array(py_shuf.sample.sample_mask)
    assert aligned_mask.tolist() == list(py_orig.sample.sample_mask)

    # Stata on original and shuffled
    st_orig = _run_stata(df_base, x_vars, "P1_ROW_ORDER_ORIG")
    st_shuf = _run_stata(df_shuf, x_vars, "P1_ROW_ORDER_SHUF")

    diffs_orig = _compare_coefs(py_orig, st_orig, "orig")
    diffs_shuf = _compare_coefs(py_shuf, st_shuf, "shuf")
    save_evidence("P1_ROW_ORDER_INVARIANCE_ORIG", py_orig, st_orig, diffs_orig)
    save_evidence("P1_ROW_ORDER_INVARIANCE_SHUF", py_shuf, st_shuf, diffs_shuf)

    # Stata coefficients should also be invariant (up to numerical noise)
    for c_o, c_s in zip(st_orig["coefficients"], st_shuf["coefficients"]):
        passed, msg = tolerance_close(c_o["beta"], c_s["beta"], name=f"stata_invariance.{c_o['name']}.beta")
        assert passed, msg
        passed, msg = tolerance_close(c_o["std_err"], c_s["std_err"], name=f"stata_invariance.{c_o['name']}.se")
        assert passed, msg

    assert diffs_orig["passed"], "\n".join(diffs_orig["messages"])
    assert diffs_shuf["passed"], "\n".join(diffs_shuf["messages"])


# ---------------------------------------------------------------------------
# P2: irrelevant-column invariance
# ---------------------------------------------------------------------------
def test_p2_irrelevant_column_invariance():
    df_base = dgp_s2_two_way_fe(seed=20260622)
    x_vars = ["x1", "x2"]

    rng = np.random.default_rng(20260623)
    df_noise = df_base.copy()
    df_noise["noise"] = rng.normal(size=len(df_base))

    py_orig = _fit_py(df_base, x_vars)
    py_noise = _fit_py(df_noise, x_vars)

    for c_o, c_n in zip(py_orig.coefficients, py_noise.coefficients):
        assert c_o.name == c_n.name
        assert np.isclose(c_o.beta, c_n.beta, rtol=1e-10, atol=1e-10)
        assert np.isclose(c_o.std_err, c_n.std_err, rtol=1e-10, atol=1e-10)

    st_orig = _run_stata(df_base, x_vars, "P2_IRREL_ORIG")
    st_noise = _run_stata(df_noise, x_vars, "P2_IRREL_NOISE")

    diffs_orig = _compare_coefs(py_orig, st_orig, "orig")
    diffs_noise = _compare_coefs(py_noise, st_noise, "noise")
    save_evidence("P2_IRRELEVANT_COLUMN_ORIG", py_orig, st_orig, diffs_orig)
    save_evidence("P2_IRRELEVANT_COLUMN_NOISE", py_noise, st_noise, diffs_noise)

    # Irrelevant column must not change Stata results
    for c_o, c_n in zip(st_orig["coefficients"], st_noise["coefficients"]):
        passed, msg = tolerance_close(c_o["beta"], c_n["beta"], name=f"stata_irrel.{c_o['name']}.beta")
        assert passed, msg
        passed, msg = tolerance_close(c_o["std_err"], c_n["std_err"], name=f"stata_irrel.{c_o['name']}.se")
        assert passed, msg

    assert diffs_orig["passed"], "\n".join(diffs_orig["messages"])
    assert diffs_noise["passed"], "\n".join(diffs_noise["messages"])


# ---------------------------------------------------------------------------
# P3: scale transformation
# ---------------------------------------------------------------------------
def test_p3_scale_transformation():
    df_base = dgp_s2_two_way_fe(seed=20260624)
    x_vars = ["x1", "x2"]

    df_scale = df_base.copy()
    df_scale["x1"] = df_scale["x1"] * 10.0

    py_orig = _fit_py(df_base, x_vars)
    py_scale = _fit_py(df_scale, x_vars)

    # x1 coefficient and SE should scale by 1/10; constant unchanged
    orig = {c.name: c for c in py_orig.coefficients}
    scale = {c.name: c for c in py_scale.coefficients}
    assert np.isclose(scale["x1"].beta, orig["x1"].beta / 10.0, rtol=1e-8)
    assert np.isclose(scale["x1"].std_err, orig["x1"].std_err / 10.0, rtol=1e-8)
    assert np.isclose(scale["_cons"].beta, orig["_cons"].beta, rtol=1e-8)
    assert np.isclose(scale["_cons"].std_err, orig["_cons"].std_err, rtol=1e-8)

    st_orig = _run_stata(df_base, x_vars, "P3_SCALE_ORIG")
    st_scale = _run_stata(df_scale, ["x1", "x2"], "P3_SCALE_SCALED")

    diffs_orig = _compare_coefs(py_orig, st_orig, "orig")
    diffs_scale = _compare_coefs(py_scale, st_scale, "scaled")
    save_evidence("P3_SCALE_TRANSFORMATION_ORIG", py_orig, st_orig, diffs_orig)
    save_evidence("P3_SCALE_TRANSFORMATION_SCALED", py_scale, st_scale, diffs_scale)

    # Verify Stata also satisfies the scale property
    st_orig_coefs = {c["name"]: c for c in st_orig["coefficients"]}
    st_scale_coefs = {c["name"]: c for c in st_scale["coefficients"]}
    passed, msg = tolerance_close(
        st_scale_coefs["x1"]["beta"], st_orig_coefs["x1"]["beta"] / 10.0,
        name="stata_scale.x1.beta"
    )
    assert passed, msg
    passed, msg = tolerance_close(
        st_scale_coefs["x1"]["std_err"], st_orig_coefs["x1"]["std_err"] / 10.0,
        name="stata_scale.x1.se"
    )
    assert passed, msg
    passed, msg = tolerance_close(
        st_scale_coefs["_cons"]["beta"], st_orig_coefs["_cons"]["beta"],
        name="stata_scale._cons.beta"
    )
    assert passed, msg

    assert diffs_orig["passed"], "\n".join(diffs_orig["messages"])
    assert diffs_scale["passed"], "\n".join(diffs_scale["messages"])
