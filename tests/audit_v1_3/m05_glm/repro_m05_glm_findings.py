"""Minimal standalone reproductions for M05 GLM confirmed findings."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from m05_audit_utils import (
    STATA_CASES,
    glm_stata_do_template,
    run_stata_do,
)

from stataflow.compat.stata import logit
from stataflow.estimators import Logit


def repro_001_aweight_rejected_by_stata():
    """M05-GLM-001: Stata logit/probit/poisson reject [aweight]."""
    print("\n=== M05-GLM-001: aweight rejected by Stata GLM commands ===")
    rng = np.random.default_rng(2025061299)
    n = 100
    x = rng.normal(size=n)
    lp = -0.5 + 0.6 * x
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    w = rng.integers(1, 5, size=n).astype(float)
    df = pd.DataFrame({"y": y, "x": x, "w": w})
    csv = STATA_CASES / "repro_001.csv"
    df.to_csv(csv, index=False)

    st = run_stata_do(glm_stata_do_template(str(csv), "logit y x [aweight=w]", y_var="y"), "repro_001")
    has_stata_coefs = bool(st.get("coefficients"))
    print("Stata returned coefficients:", has_stata_coefs)
    if not has_stata_coefs:
        print("Stata did not produce estimates (expected because aweights are not allowed).")

    # Python accepts aweight and returns a result
    py_res = logit(df, y="y", x=["x"], aweight="w")
    print("Python logit with aweight succeeded; beta =", py_res.coefficients[0].beta)


def repro_002_cluster_df_resid_undefined_in_stata():
    """M05-GLM-002: Python reports df_resid=G-1 for cluster GLM, but Stata has no e(df_r)."""
    print("\n=== M05-GLM-002: cluster df_resid semantics ===")
    rng = np.random.default_rng(2025061201)
    n = 60
    g = np.repeat(np.arange(1, 11), 6)
    x1 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "g": g})
    csv = STATA_CASES / "repro_002.csv"
    df.to_csv(csv, index=False)

    st = run_stata_do(glm_stata_do_template(str(csv), "logit y x1, vce(cluster g)", y_var="y"), "repro_002")
    py_res = Logit(df, y="y", x=["x1"]).fit(vce="cluster", cluster="g")
    print("Stata e(df_r):", st.get("df_resid"))  # we derive n-k because e(df_r) missing
    print("Stata e(N_clust):", st.get("n_clust"))
    print("Python df_resid:", py_res.fit.df_resid)
    print("Python cluster_count:", py_res.diagnostics.cluster_count)


def repro_003_robust_chi2_is_wald_in_stata():
    """M05-GLM-003: Python reports LR chi2; Stata robust/cluster reports Wald chi2."""
    print("\n=== M05-GLM-003: robust/cluster chi2 is Wald in Stata ===")
    rng = np.random.default_rng(2025061203)
    n = 90
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
    csv = STATA_CASES / "repro_003.csv"
    df.to_csv(csv, index=False)

    st_ols = run_stata_do(glm_stata_do_template(str(csv), "logit y x1 x2", y_var="y"), "repro_003_ols")
    st_rob = run_stata_do(glm_stata_do_template(str(csv), "logit y x1 x2, vce(robust)", y_var="y"), "repro_003_rob")
    py_res = Logit(df, y="y", x=["x1", "x2"]).fit(vce="robust")
    print("Stata OLS e(chi2) LR:", st_ols.get("chi2"))
    print("Stata robust e(chi2) Wald:", st_rob.get("chi2"))
    print("Python robust f_stat (LR):", py_res.fit.f_stat)


def repro_004_separation_error_handling():
    """M05-GLM-004: complete separation produces different errors in Python vs Stata."""
    print("\n=== M05-GLM-004: complete separation error handling ===")
    df = pd.DataFrame({
        "y": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
        "x": [-2.0, -1.0, -0.1, 0.1, 1.0, 2.0],
    })
    csv = STATA_CASES / "repro_004.csv"
    df.to_csv(csv, index=False)

    st = run_stata_do(glm_stata_do_template(str(csv), "logit y x", y_var="y"), "repro_004")
    if st.get("coefficients"):
        print("Stata returned coefficients unexpectedly")
    else:
        print("Stata produced no estimates (perfect prediction detected).")

    try:
        py_res = Logit(df, y="y", x=["x"]).fit()
        print("Python succeeded unexpectedly")
    except RuntimeError as exc:
        print("Python error:", exc)


if __name__ == "__main__":
    repro_001_aweight_rejected_by_stata()
    repro_002_cluster_df_resid_undefined_in_stata()
    repro_003_robust_chi2_is_wald_in_stata()
    repro_004_separation_error_handling()
