"""M06 PPMLHDFE synthetic dual-run audit tests (S1-S8).

Each test generates a new DGP, runs the equivalent command in Stata 17,
fits the Python estimator, performs field-level comparison, saves evidence,
and asserts that the comparison passes.
"""

from __future__ import annotations

import numpy as np
import pytest

from stataflow.estimators import PPMLHDFE
from stataflow.compat.stata import ppmlhdfe as ppmlhdfe_wrapper

from .m06_dgp import (
    dgp_s1_small_panel,
    dgp_s2_two_way_fe,
    dgp_s3_missing_screen,
    dgp_s4_collinear_within_fe,
    dgp_s5_separation_fe,
    dgp_s6_cluster_singleton,
    dgp_s7_weights_offset,
    dgp_s8_eform_predict,
)
from .m06_audit_utils import (
    run_stata_ppmlhdfe,
    compare_python_to_stata,
    save_evidence,
    tolerance_close,
)


def _fit_python(
    df,
    y: str,
    x: list[str],
    absorb,
    vce: str = "robust",
    cluster=None,
    offset: str | None = None,
    exposure: str | None = None,
    separation: str | None = "fe",
    weights: str | None = None,
    eform: bool = False,
):
    """Helper to construct and fit a PPMLHDFE model."""
    model = PPMLHDFE(
        data=df,
        y=y,
        x=x,
        absorb=absorb,
        offset=offset,
        exposure=exposure,
        separation=separation,
        weights=weights,
    )
    return model.fit(vce=vce, cluster=cluster, eform=eform)


def _compute_wald_chi2(py_result) -> float:
    """Compute Wald chi2 for all non-constant coefficients."""
    names = [c.name for c in py_result.coefficients]
    idx = [i for i, n in enumerate(names) if n != "_cons"]
    if not idx:
        return 0.0
    beta = np.array([py_result.coefficients[i].beta for i in idx])
    v = np.array(py_result.variance.values)
    v_sub = v[np.ix_(idx, idx)]
    try:
        inv = np.linalg.inv(v_sub)
    except np.linalg.LinAlgError:
        inv = np.linalg.pinv(v_sub)
    return float(beta @ inv @ beta)


# ---------------------------------------------------------------------------
# S1: small panel with robust VCE
# ---------------------------------------------------------------------------
def test_s1_small_panel_robust():
    df = dgp_s1_small_panel()
    y_var = "y"
    x_vars = ["x1", "x2"]
    absorb_vars = ["entity_id"]
    coef_names = x_vars + ["_cons"]

    st = run_stata_ppmlhdfe(
        df,
        command=f"ppmlhdfe {y_var} {' '.join(x_vars)}, absorb({' '.join(absorb_vars)}) vce(robust)",
        y_var=y_var,
        prefix="S1_SMALL_PANEL_OLS_ROBUST",
        coef_names=coef_names,
    )
    py = _fit_python(df, y_var, x_vars, absorb_vars, vce="robust")
    py.fit.chi2 = _compute_wald_chi2(py)

    fields = ["nobs", "df_model", "df_a", "ll", "deviance", "pseudo_r2", "chi2"]
    diffs = compare_python_to_stata(py, st, fields=fields, compare_vce=True)
    save_evidence("S1_SMALL_PANEL_OLS_ROBUST", py, st, diffs)
    assert diffs["passed"], "\n".join(diffs["messages"])


# ---------------------------------------------------------------------------
# S2: two-way FE with robust VCE
# ---------------------------------------------------------------------------
def test_s2_two_way_fe_robust():
    df = dgp_s2_two_way_fe()
    y_var = "y"
    x_vars = ["x1", "x2"]
    absorb_vars = ["entity_id", "time_id"]
    coef_names = x_vars + ["_cons"]

    st = run_stata_ppmlhdfe(
        df,
        command=(
            f"ppmlhdfe {y_var} {' '.join(x_vars)}, "
            f"absorb({' '.join(absorb_vars)}) vce(robust)"
        ),
        y_var=y_var,
        prefix="S2_TWO_WAY_FE_ROBUST",
        coef_names=coef_names,
    )
    py = _fit_python(df, y_var, x_vars, absorb_vars, vce="robust")
    py.fit.chi2 = _compute_wald_chi2(py)

    fields = ["nobs", "df_model", "df_a", "ll", "deviance", "pseudo_r2", "chi2"]
    diffs = compare_python_to_stata(py, st, fields=fields, compare_vce=True)
    save_evidence("S2_TWO_WAY_FE_ROBUST", py, st, diffs)
    assert diffs["passed"], "\n".join(diffs["messages"])


# ---------------------------------------------------------------------------
# S3: missing value sample screening
# ---------------------------------------------------------------------------
def test_s3_missing_sample_screening():
    df = dgp_s3_missing_screen()
    y_var = "y"
    x_vars = ["x1", "x2"]
    absorb_vars = ["entity_id", "time_id"]
    cluster_var = "cl"
    coef_names = x_vars + ["_cons"]

    # Disable separation so the comparison isolates missing-value screening.
    st = run_stata_ppmlhdfe(
        df,
        command=(
            f"ppmlhdfe {y_var} {' '.join(x_vars)}, "
            f"absorb({' '.join(absorb_vars)}) vce(cluster {cluster_var})"
        ),
        y_var=y_var,
        prefix="S3_MISSING_SAMPLE_SCREENING",
        coef_names=coef_names,
    )
    py = _fit_python(
        df, y_var, x_vars, absorb_vars, vce="cluster", cluster=cluster_var
    )

    # Stata GLM does not return e(df_r); derive a comparable residual df from cluster count
    if "n_clust" in st and st["n_clust"] is not None:
        st["df_resid"] = st["n_clust"] - 1

    assert py.sample.nobs == int(st.get("nobs", -1))
    assert sum(py.sample.sample_mask) == py.sample.nobs
    assert len(py.sample.sample_mask) == py.sample.n_input_rows

    fields = ["nobs", "df_model", "df_a", "df_resid", "n_clust", "ll", "deviance", "pseudo_r2"]
    diffs = compare_python_to_stata(py, st, fields=fields, compare_vce=True)
    save_evidence("S3_MISSING_SAMPLE_SCREENING", py, st, diffs)
    assert diffs["passed"], "\n".join(diffs["messages"])


# ---------------------------------------------------------------------------
# S4: collinear variable within FE
# ---------------------------------------------------------------------------
def test_s4_collinear_within_fe():
    df = dgp_s4_collinear_within_fe()
    y_var = "y"
    x_vars = ["x1", "x_const"]
    absorb_vars = ["entity_id"]
    coef_names = ["x1", "_cons"]  # x_const should be omitted

    st = run_stata_ppmlhdfe(
        df,
        command=f"ppmlhdfe {y_var} {' '.join(x_vars)}, absorb({' '.join(absorb_vars)}) vce(robust)",
        y_var=y_var,
        prefix="S4_COLLINEAR_WITHIN_FE",
        coef_names=coef_names,
    )
    py = _fit_python(df, y_var, x_vars, absorb_vars, vce="robust")

    # Confirm x_const was dropped in Python
    py_names = [c.name for c in py.coefficients]
    assert "x_const" not in py_names
    assert "x1" in py_names

    fields = ["nobs", "df_model", "df_a", "ll", "deviance", "pseudo_r2"]
    # Stata e(V) indexing changes when a regressor is omitted, so compare
    # coefficients/SE only for this collinearity test.
    diffs = compare_python_to_stata(py, st, fields=fields, compare_vce=False)
    save_evidence("S4_COLLINEAR_WITHIN_FE", py, st, diffs)
    assert diffs["passed"], "\n".join(diffs["messages"])


# ---------------------------------------------------------------------------
# S5: FE-triggered separation
# ---------------------------------------------------------------------------
def test_s5_separation_fe():
    df = dgp_s5_separation_fe()
    y_var = "y"
    x_vars = ["x1", "x2"]
    absorb_vars = ["entity_id"]
    coef_names = x_vars + ["_cons"]

    # Stata default separation (fe simplex relu)
    st_default = run_stata_ppmlhdfe(
        df,
        command=f"ppmlhdfe {y_var} {' '.join(x_vars)}, absorb({' '.join(absorb_vars)}) vce(robust)",
        y_var=y_var,
        prefix="S5_SEPARATION_FE_DEFAULT",
        coef_names=coef_names,
    )
    # Stata separation(none)
    st_none = run_stata_ppmlhdfe(
        df,
        command=(
            f"ppmlhdfe {y_var} {' '.join(x_vars)}, "
            f"absorb({' '.join(absorb_vars)}) vce(robust) separation(none)"
        ),
        y_var=y_var,
        prefix="S5_SEPARATION_FE_NONE",
        coef_names=coef_names,
    )

    # Python separation="fe" should align with Stata default (both drop y=0 FE groups)
    py_fe = _fit_python(
        df, y_var, x_vars, absorb_vars, vce="robust", separation="fe"
    )
    # Explicit Python separation="none" aligns with Stata separation(none).
    py_none = _fit_python(
        df, y_var, x_vars, absorb_vars, vce="robust", separation="none"
    )

    fields = ["nobs", "df_model", "df_a", "ll", "deviance", "pseudo_r2"]

    diffs_fe = compare_python_to_stata(py_fe, st_default, fields=fields, compare_vce=True)
    save_evidence("S5_SEPARATION_FE_DEFAULT", py_fe, st_default, diffs_fe)

    diffs_none = compare_python_to_stata(py_none, st_none, fields=fields, compare_vce=True)
    save_evidence("S5_SEPARATION_FE_NONE", py_none, st_none, diffs_none)

    # We assert each comparison separately; any failure becomes documented evidence.
    assert diffs_fe["passed"], "\n".join(diffs_fe["messages"])
    assert diffs_none["passed"], "\n".join(diffs_none["messages"])


# ---------------------------------------------------------------------------
# S6: cluster-robust with singleton drop
# ---------------------------------------------------------------------------
def test_s6_cluster_singleton():
    df = dgp_s6_cluster_singleton()
    y_var = "y"
    x_vars = ["x1", "x2"]
    absorb_vars = ["entity_id"]
    cluster_var = "cl"
    coef_names = x_vars + ["_cons"]

    st = run_stata_ppmlhdfe(
        df,
        command=(
            f"ppmlhdfe {y_var} {' '.join(x_vars)}, "
            f"absorb({' '.join(absorb_vars)}) vce(cluster {cluster_var})"
        ),
        y_var=y_var,
        prefix="S6_CLUSTER_SINGLETON",
        coef_names=coef_names,
    )
    py = _fit_python(
        df, y_var, x_vars, absorb_vars, vce="cluster", cluster=cluster_var
    )

    if "n_clust" in st and st["n_clust"] is not None:
        st["df_resid"] = st["n_clust"] - 1

    fields = ["nobs", "df_model", "df_a", "df_resid", "n_clust", "ll", "deviance", "pseudo_r2"]
    # ppmlhdfe's clustered singleton path retains a small numerical residue
    # from its alternating-projection solve; core point estimates remain close.
    diffs = compare_python_to_stata(
        py,
        st,
        fields=fields,
        compare_vce=True,
        coefficient_rtol=2e-5,
        vce_rtol=2e-5,
    )
    save_evidence("S6_CLUSTER_SINGLETON", py, st, diffs)
    assert diffs["passed"], "\n".join(diffs["messages"])


# ---------------------------------------------------------------------------
# S7: aweight/pweight and offset
# ---------------------------------------------------------------------------
def test_s7_weights_offset():
    df = dgp_s7_weights_offset()
    y_var = "y"
    x_vars = ["x1", "x2"]
    absorb_vars = ["entity_id"]
    coef_names = x_vars + ["_cons"]

    # Stata ppmlhdfe accepts only pweight; Python maps weights to aweight internally.
    st = run_stata_ppmlhdfe(
        df,
        command=(
            f"ppmlhdfe {y_var} {' '.join(x_vars)} [pweight=w], "
            f"absorb({' '.join(absorb_vars)}) offset(off) vce(robust)"
        ),
        y_var=y_var,
        prefix="S7_WEIGHTS_OFFSET",
        coef_names=coef_names,
    )
    py = _fit_python(
        df,
        y_var,
        x_vars,
        absorb_vars,
        vce="robust",
        offset="off",
        weights="w",
    )

    fields = ["nobs", "df_model", "df_a", "ll", "deviance", "pseudo_r2"]
    diffs = compare_python_to_stata(py, st, fields=fields, compare_vce=True)
    save_evidence("S7_WEIGHTS_OFFSET", py, st, diffs)
    assert diffs["passed"], "\n".join(diffs["messages"])


# ---------------------------------------------------------------------------
# S8: eform and predict types
# ---------------------------------------------------------------------------
def test_s8_eform_predict():
    df = dgp_s8_eform_predict()
    y_var = "y"
    x_vars = ["x1", "x2"]
    absorb_vars = ["entity_id"]
    coef_names = x_vars + ["_cons"]
    predict_types = ["xb", "mu", "residuals", "pearson", "deviance"]

    # Stata must include the 'd' option for predict mu/pearson/deviance
    st = run_stata_ppmlhdfe(
        df,
        command=(
            f"ppmlhdfe {y_var} {' '.join(x_vars)}, "
            f"absorb({' '.join(absorb_vars)}) vce(robust) d"
        ),
        y_var=y_var,
        prefix="S8_EFORM_PREDICT",
        coef_names=coef_names,
        predict_types=predict_types,
    )

    # Raw-scale Python fit to compare with raw Stata coefficients
    py_raw = _fit_python(df, y_var, x_vars, absorb_vars, vce="robust", eform=False)
    fields = ["nobs", "df_model", "df_a", "ll", "deviance", "pseudo_r2"]
    diffs_raw = compare_python_to_stata(py_raw, st, fields=fields, compare_vce=True)
    save_evidence("S8_EFORM_PREDICT_RAW", py_raw, st, diffs_raw)

    # Eform comparison: compute expected eform from raw Stata coefficients
    st_coefs = {c["name"]: c for c in st.get("coefficients", [])}
    expected_eform = {}
    for name, c in st_coefs.items():
        beta = c["beta"]
        se = c["std_err"]
        expected_eform[name] = {
            "beta": np.exp(beta),
            "std_err": np.exp(beta) * se,
            "t_stat": beta / se if se > 0 else float("nan"),
        }

    py_eform = _fit_python(df, y_var, x_vars, absorb_vars, vce="robust", eform=True)
    eform_diffs = {"passed": True, "messages": [], "field_results": {}}
    for py_coef in py_eform.coefficients:
        name = py_coef.name
        exp = expected_eform.get(name)
        if exp is None:
            eform_diffs["passed"] = False
            eform_diffs["messages"].append(f"eform missing expected coefficient {name}")
            continue
        for metric in ["beta", "std_err", "t_stat"]:
            py_val = getattr(py_coef, metric)
            st_val = exp[metric]
            passed, msg = tolerance_close(py_val, st_val, name=f"eform.{name}.{metric}")
            eform_diffs["field_results"][f"eform.{name}.{metric}"] = {"passed": passed, "message": msg}
            if not passed:
                eform_diffs["passed"] = False
            eform_diffs["messages"].append(msg)
    save_evidence("S8_EFORM_PREDICT_EFORM", py_eform, st, eform_diffs)

    # Predict summaries are already compared by compare_python_to_stata using the raw fit
    predict_diffs = compare_python_to_stata(
        py_raw,
        st,
        fields=fields,
        compare_vce=False,
        predict_types=predict_types,
        # Stata's saved HDFE contribution is approximate even when e(ll) and
        # e(deviance) have converged; its own predicted deviance does not sum
        # exactly to e(deviance). Keep strict tolerances for all core fields.
        predict_rtol=3e-3,
        predict_atol=1e-3,
    )
    save_evidence("S8_EFORM_PREDICT_PREDICT", py_raw, st, predict_diffs)

    # Assert on all three sub-comparisons
    assert diffs_raw["passed"], "\n".join(diffs_raw["messages"])
    assert eform_diffs["passed"], "\n".join(eform_diffs["messages"])
    assert predict_diffs["passed"], "\n".join(predict_diffs["messages"])
