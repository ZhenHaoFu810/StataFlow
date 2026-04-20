"""OOS validation runner for RD family.

Datasets:
- rdrobust_senate (new specification: covariates + auto bandwidth)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validation.oos.common import (
    OOSCase,
    STATA_CASES,
    compare_case,
    run_stata_and_parse,
    write_case_report,
    write_family_summary,
)
from statapy.compat.stata import rdrobust


def _load_senate() -> pd.DataFrame:
    return pd.read_stata(
        PROJECT_ROOT / "research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta"
    )


def run_oos_rdrobust_senate_covs() -> dict:
    """RD with covariates on senate data."""
    case = OOSCase(
        case_id="oos_rdrobust_senate_covs",
        family="rd",
        command="rdrobust",
        dataset_key="rdrobust_senate",
        dataset_path="research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta",
        stata_command="rdrobust vote margin, c(0) h(15) covs(termshouse)",
        python_callable="statapy.compat.stata.rdrobust",
        python_kwargs={"y": "vote", "x": "margin", "c": 0, "h": 15.0, "covs": ["termshouse"]},
        description="Sharp RD on senate elections with covariate adjustment.",
    )

    data = _load_senate()
    if "class" in data.columns:
        data = data.rename(columns={"class": "classnum"})
    dta_file = STATA_CASES / "oos_rdrobust_senate.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
rdrobust vote margin, c(0) h(15) covs(termshouse)

display "E_N=" e(N)
display "COEF Conventional " e(tau_cl) " " e(se_tau_cl)
display "COEF Bias-Corrected " e(tau_bc) " " e(se_tau_cl)
display "COEF Robust " e(tau_bc) " " e(se_tau_rb)
"""
    st_result = run_stata_and_parse(do)
    py_result = rdrobust(data, y="vote", x="margin", c=0, h=15.0, covs=["termshouse"])

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


def run_oos_rdrobust_senate_mserd() -> dict:
    """RD with automatic bandwidth selection (stress case)."""
    case = OOSCase(
        case_id="oos_rdrobust_senate_mserd",
        family="rd",
        command="rdrobust",
        dataset_key="rdrobust_senate",
        dataset_path="research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta",
        stata_command="rdrobust vote margin, c(0) bwselect(mserd)",
        python_callable="statapy.compat.stata.rdrobust",
        python_kwargs={"y": "vote", "x": "margin", "c": 0, "bwselect": "mserd"},
        description="Sharp RD with automatic mean-squared-error bandwidth selection.",
        notes="Automatic bandwidth uses documented looser tolerance due to plug-in selector sensitivity.",
    )

    data = _load_senate()
    if "class" in data.columns:
        data = data.rename(columns={"class": "classnum"})
    dta_file = STATA_CASES / "oos_rdrobust_senate.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
rdrobust vote margin, c(0) bwselect(mserd)

display "E_N=" e(N)
display "COEF Conventional " e(tau_cl) " " e(se_tau_cl)
display "COEF Bias-Corrected " e(tau_bc) " " e(se_tau_cl)
display "COEF Robust " e(tau_bc) " " e(se_tau_rb)
"""
    st_result = run_stata_and_parse(do)
    py_result = rdrobust(data, y="vote", x="margin", c=0, bwselect="mserd")

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map, coef_rtol=5e-4, coef_atol=1e-5)
    write_case_report(report)
    return report


if __name__ == "__main__":
    reports = []
    for fn in [run_oos_rdrobust_senate_covs, run_oos_rdrobust_senate_mserd]:
        print(f"Running {fn.__name__} ...")
        try:
            reports.append(fn())
        except Exception as exc:
            print(f"ERROR in {fn.__name__}: {exc}")
            reports.append({
                "case_id": fn.__name__.replace("run_", ""),
                "command": "unknown",
                "dataset_key": "unknown",
                "status": "blocked",
                "error": str(exc),
            })
    write_family_summary("rd", reports)
    print("RD family OOS complete.")
