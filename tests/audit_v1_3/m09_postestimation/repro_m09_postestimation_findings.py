"""Standalone reproduction of M09 postestimation confirmed findings.

Run from the project root:
    python tests/audit_v1_3/m09_postestimation/repro_m09_postestimation_findings.py

The script prints a short summary and writes evidence JSON for:
- M09-FE-001: FixedEffectsOLS.predict(type='xb') omits entity fixed effects.
- M09-POST-002: GLM margins treat a binary regressor as continuous, while
  Stata margins, dydx() reports a different (likely discrete-change) value.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from stataflow.compat.stata.linear import xtreg_fe
from stataflow.compat.stata.glm import logit
from m09_audit_utils import (
    data_hash,
    run_stata_do,
    save_evidence,
)


def _repro_fe_001() -> dict:
    seed = 202602
    rng = np.random.default_rng(seed)
    N = 80
    n_groups = 8
    df = pd.DataFrame({
        "id": np.repeat(np.arange(n_groups), N // n_groups),
        "x": rng.normal(size=N),
    })
    group_effects = rng.normal(0.0, 1.0, size=n_groups)
    df["y"] = group_effects[df["id"].values] + 1.5 * df["x"] + rng.normal(0.0, 0.3, size=N)

    result = xtreg_fe(df.iloc[:60].copy(), "y", ["x"], fe="id")
    py_xb_in = result.predict(type="xb", newdata=df.iloc[:60])

    do = """clear all
set more off
use "{dta}", clear
xtset id
xtreg y x if _n<=60, fe
predict xb_s, xb
quietly summarize xb_s if !missing(xb_s) & _n<=60
display "P_XB_IN_MEAN=" r(mean)
display "P_XB_IN_SD=" r(sd)
display "M09_OK_FE001"
"""
    st = run_stata_do(df, "REPRO_FE001", do)
    s = st["scalars"]

    evidence = {
        "finding": "M09-FE-001",
        "seed": seed,
        "data_hash": data_hash(df),
        "python": {
            "xb_in_mean": float(np.mean(py_xb_in)),
            "xb_in_sd": float(np.std(py_xb_in, ddof=1)),
        },
        "stata": {
            "log_path": st["log_path"],
            "xb_in_mean": s.get("P_XB_IN_MEAN"),
            "xb_in_sd": s.get("P_XB_IN_SD"),
        },
    }
    save_evidence("REPRO_FE001", evidence)
    return evidence


def _repro_post_002() -> dict:
    seed = 202604
    rng = np.random.default_rng(seed)
    N = 200
    df = pd.DataFrame({
        "x1": rng.normal(size=N),
        "x2": rng.integers(0, 2, size=N).astype(float),
    })
    eta = -1.0 + 0.8 * df["x1"] - 1.2 * df["x2"]
    df["y"] = (eta + rng.logistic(size=N) > 0).astype(float)

    result = logit(df, "y", ["x1", "x2"])
    margins = result._model.margins("dydx")
    py_ame_x2 = margins.params["x2"]
    py_se_x2 = margins.bse["x2"]

    do = """clear all
set more off
use "{dta}", clear
logit y x1 x2
quietly margins, dydx(x2)
display "M_x2=" r(b)[1,1]
display "SE_x2=" sqrt(r(V)[1,1])
display "M09_OK_POST002"
"""
    st = run_stata_do(df, "REPRO_POST002", do)
    s = st["scalars"]

    evidence = {
        "finding": "M09-POST-002",
        "seed": seed,
        "data_hash": data_hash(df),
        "python": {
            "margins_x2": py_ame_x2,
            "se_x2": py_se_x2,
        },
        "stata": {
            "log_path": st["log_path"],
            "margins_x2": s.get("M_x2"),
            "se_x2": s.get("SE_x2"),
        },
    }
    save_evidence("REPRO_POST002", evidence)
    return evidence


def main() -> None:
    fe_evidence = _repro_fe_001()
    post_evidence = _repro_post_002()

    print("M09 Postestimation findings reproduction")
    print("=" * 50)
    print(f"M09-FE-001:")
    print(f"  Python xb.mean = {fe_evidence['python']['xb_in_mean']:.8f}")
    print(f"  Stata  xb.mean = {fe_evidence['stata']['xb_in_mean']}")
    print(f"M09-POST-002:")
    print(f"  Python margins(x2) = {post_evidence['python']['margins_x2']:.8f}")
    print(f"  Stata  margins(x2) = {post_evidence['stata']['margins_x2']}")
    print(f"Evidence saved under docs/audit/modular-revalidation-v1.3/M09-postestimation/evidence/")


if __name__ == "__main__":
    main()
