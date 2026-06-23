"""Standalone minimal reproductions of confirmed M06 PPMLHDFE audit findings.

Run from the project root with:
    python tests/audit_v1_3/m06_ppmlhdfe/repro_m06_ppmlhdfe_findings.py

The script executes small Stata 17 commands and prints Python/Stata values
side-by-side. It does not modify product code under src/stataflow/.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from stataflow.estimators import PPMLHDFE
from stataflow.compat.stata import ppmlhdfe as ppmlhdfe_wrapper

from .m06_dgp import dgp_s5_separation_fe, dgp_s7_weights_offset
from .m06_audit_utils import (
    run_stata_ppmlhdfe,
    compare_python_to_stata,
    save_evidence,
    M06_EVIDENCE,
    STATA_OUTPUT,
    StataRunner,
    _clean_stata_log,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


# ---------------------------------------------------------------------------
# Finding A: Stata ppmlhdfe rejects aweight (and iweight)
# ---------------------------------------------------------------------------
def repro_aweight_rejected() -> dict:
    """Show that Stata ppmlhdfe returns r(101) on [aweight=...]."""
    _print_header("A. Stata ppmlhdfe rejects aweight/iweight")
    df = dgp_s7_weights_offset(seed=20260618)
    df = df[["y", "x1", "x2", "entity_id", "w"]].head(30).copy()
    df.to_csv(STATA_OUTPUT / "repro_aweight.csv", index=False)

    do = '''clear all
set more off
import delimited "''' + (STATA_OUTPUT / "repro_aweight.csv").as_posix() + '''", varnames(1) clear
capture noisily ppmlhdfe y x1 x2 [aweight=w], absorb(entity_id) vce(robust)
if _rc {
    display "AWEIGHT_RC=" _rc
}
capture noisily ppmlhdfe y x1 x2 [iweight=w], absorb(entity_id) vce(robust)
if _rc {
    display "IWEIGHT_RC=" _rc
}
display "DONE"
'''
    runner = StataRunner()
    res = runner.run_do_file(do, output_dir=str(STATA_OUTPUT))
    cleaned = _clean_stata_log(res.output_content or "")
    print("Stata log excerpt:")
    for line in cleaned.splitlines():
        if "weight" in line.lower() or "r(" in line or "rc=" in line or "ppmlhdfe" in line:
            print(" ", line)

    evidence = {
        "finding": "A_WeightSyntaxRejected",
        "stata_exit_code": res.exit_code,
        "stata_log_excerpt": cleaned,
        "note": "Stata ppmlhdfe accepts only pweight; aweight/iweight give r(101).",
    }
    out_dir = M06_EVIDENCE / "minimal-reproductions"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "A_WeightSyntaxRejected.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


# ---------------------------------------------------------------------------
# Finding B: Python separation=None vs Stata default separation sample diff
# ---------------------------------------------------------------------------
def repro_separation_sample_diff() -> dict:
    """Reproduce the sample-size mismatch caused by separation handling."""
    _print_header("B. Separation sample difference")
    df = dgp_s5_separation_fe(seed=20260616)
    x_vars = ["x1", "x2"]

    # Stata default separation
    st_default = run_stata_ppmlhdfe(
        df,
        command=f"ppmlhdfe y {' '.join(x_vars)}, absorb(entity_id) vce(robust)",
        y_var="y",
        prefix="REPRO_SEP_DEFAULT",
        coef_names=x_vars + ["_cons"],
    )

    # Python separation="fe"
    py_fe = PPMLHDFE(
        data=df, y="y", x=x_vars, absorb=["entity_id"], separation="fe"
    ).fit(vce="robust")

    # Python separation=None (will likely fail to converge; catch values)
    py_none_info = {}
    try:
        py_none = PPMLHDFE(
            data=df, y="y", x=x_vars, absorb=["entity_id"], separation=None
        ).fit(vce="robust")
        py_none_info = {
            "nobs": py_none.sample.nobs,
            "ll": py_none.fit.ll,
            "converged": True,
            "x1_beta": next(c.beta for c in py_none.coefficients if c.name == "x1"),
        }
    except Exception as exc:
        py_none_info = {"error": str(exc), "converged": False}

    print(f"Stata default separation       nobs={st_default.get('nobs')}")
    print(f"Python separation='fe'         nobs={py_fe.sample.nobs}")
    print(f"Python separation=None         info={py_none_info}")

    evidence = {
        "finding": "B_SeparationSampleDifference",
        "stata_default_nobs": st_default.get("nobs"),
        "python_separation_fe_nobs": py_fe.sample.nobs,
        "python_separation_none": py_none_info,
        "note": "Stata default drops more observations than Python separation='fe'. Python separation=None does not handle separation and can diverge.",
    }
    out_dir = M06_EVIDENCE / "minimal-reproductions"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "B_SeparationSampleDifference.json").write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    return evidence


# ---------------------------------------------------------------------------
# Finding C: Robust SE residual numerical difference
# ---------------------------------------------------------------------------
def repro_robust_se_residual() -> dict:
    """Check whether a ~1e-5 robust SE residual remains in S1."""
    _print_header("C. Robust SE residual (~1e-5)")
    df = dgp_s7_weights_offset(seed=20260618)  # use a clean weighted design to look at SE diff
    x_vars = ["x1", "x2"]
    st = run_stata_ppmlhdfe(
        df,
        command=f"ppmlhdfe y {' '.join(x_vars)}, absorb(entity_id) vce(robust) separation(none)",
        y_var="y",
        prefix="REPRO_ROBUST_SE",
        coef_names=x_vars + ["_cons"],
    )
    py = PPMLHDFE(data=df, y="y", x=x_vars, absorb=["entity_id"], separation=None).fit(vce="robust")

    st_coefs = {c["name"]: c for c in st.get("coefficients", [])}
    max_rel = 0.0
    max_name = ""
    for c in py.coefficients:
        st_c = st_coefs.get(c.name)
        if st_c is None:
            continue
        rel = abs(c.std_err - st_c["std_err"]) / max(abs(st_c["std_err"]), 1e-15)
        print(f"  {c.name}: Python SE={c.std_err:.12g}, Stata SE={st_c['std_err']:.12g}, rel={rel:.2e}")
        if rel > max_rel:
            max_rel = rel
            max_name = c.name

    evidence = {
        "finding": "C_RobustSEResidual",
        "max_relative_se_diff": max_rel,
        "max_diff_coef": max_name,
        "note": "Residual robust SE differences are typically < 1e-5 on clean designs but can exceed tolerance when FE and cluster interact.",
    }
    out_dir = M06_EVIDENCE / "minimal-reproductions"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "C_RobustSEResidual.json").write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    return evidence


# ---------------------------------------------------------------------------
# Finding D: df_resid semantic difference under cluster VCE
# ---------------------------------------------------------------------------
def repro_df_resid_semantic() -> dict:
    """Show that Stata ppmlhdfe does not return e(df_r) under cluster VCE."""
    _print_header("D. df_resid semantic difference under cluster VCE")
    df = dgp_s7_weights_offset(seed=20260618)
    x_vars = ["x1", "x2"]
    # Make a cluster variable independent of entity
    df["cl"] = np.random.default_rng(20260625).integers(1, 21, size=len(df))
    st = run_stata_ppmlhdfe(
        df,
        command=f"ppmlhdfe y {' '.join(x_vars)}, absorb(entity_id) vce(cluster cl) separation(none)",
        y_var="y",
        prefix="REPRO_DF_RESID",
        coef_names=x_vars + ["_cons"],
    )
    py = PPMLHDFE(data=df, y="y", x=x_vars, absorb=["entity_id"], separation=None).fit(
        vce="cluster", cluster="cl"
    )

    print(f"Stata e(df_r)        = {st.get('df_resid')}")
    print(f"Stata e(N_clust)     = {st.get('n_clust')}")
    print(f"Python df_resid      = {py.fit.df_resid}")
    print(f"Python cluster_count = {py.diagnostics.cluster_count}")

    evidence = {
        "finding": "D_DfResidSemantic",
        "stata_e_df_r": st.get("df_resid"),
        "stata_n_clust": st.get("n_clust"),
        "python_df_resid": py.fit.df_resid,
        "python_cluster_count": py.diagnostics.cluster_count,
        "note": "Stata GLM/ppmlhdfe does not define e(df_r); Python uses G-1.",
    }
    out_dir = M06_EVIDENCE / "minimal-reproductions"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "D_DfResidSemantic.json").write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    return evidence


if __name__ == "__main__":
    repro_aweight_rejected()
    repro_separation_sample_diff()
    repro_robust_se_residual()
    repro_df_resid_semantic()
    print("\nAll minimal reproductions completed; evidence saved under", M06_EVIDENCE / "minimal-reproductions")
