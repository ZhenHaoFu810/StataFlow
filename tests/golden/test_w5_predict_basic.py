"""Golden dual-run test: predict basic synthetic cases."""

import numpy as np
import pandas as pd
from pathlib import Path
import pytest

from stataflow import OLS, Logit
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_ROOT,
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    parse_stata_log,
    tolerance_close,
)


def test_predict_ols_basic():
    """OLS predict xb and residuals on synthetic data."""
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = 1.0 + 2.0 * x1 + 0.5 * x2 + np.random.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    dta_file = PROJECT_STATA_CASES / "w5_predict_ols_data.dta"
    dta_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off
use "{dta_file}", clear
reg y x1 x2
predict xb_ols, xb
predict resid_ols, residuals
summarize xb_ols resid_ols, detail
list y xb_ols resid_ols in 1/10
matrix b = e(b)
display "B_cons=" b[1,3]
display "B_x1=" b[1,1]
display "B_x2=" b[1,2]
display "E_N=" e(N)
display "PREDICT_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    # Run Python
    model = OLS(data=df, y="y", x=["x1", "x2"])
    model.fit()
    py_xb = model.predict(type="xb")
    py_resid = model.predict(type="residuals")

    # Compare first 10 observations
    log = stata_result.output_content
    # Parse first 10 rows from list output
    lines = log.splitlines()
    st_xb = []
    st_resid = []
    in_list = False
    import re
    row_pattern = re.compile(r'^\s*\d+\.\s*\|\s*\S+\s+([-\d.]+)\s+([-\d.]+)\s*\|')
    for line in lines:
        if "xb_ols" in line and "resid_ols" in line:
            in_list = True
            continue
        if in_list:
            m = row_pattern.match(line)
            if m:
                st_xb.append(float(m.group(1)))
                st_resid.append(float(m.group(2)))
            if len(st_xb) >= 10:
                break

    assert len(st_xb) == 10, f"Could not parse Stata predictions, got {len(st_xb)} rows"

    for i in range(10):
        passed, msg = tolerance_close(py_xb[i], st_xb[i], rtol=1e-5, atol=1e-6, name=f"xb[{i}]")
        assert passed, msg
        passed, msg = tolerance_close(py_resid[i], st_resid[i], rtol=1e-5, atol=1e-6, name=f"resid[{i}]")
        assert passed, msg


def test_predict_logit_basic():
    """Logit predict xb and pr on synthetic data."""
    np.random.seed(43)
    n = 200
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    pr = 1.0 / (1.0 + np.exp(-(0.5 + x1 - 0.5 * x2)))
    y = (np.random.uniform(0, 1, n) < pr).astype(int)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    dta_file = PROJECT_STATA_CASES / "w5_predict_logit_data.dta"
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off
use "{dta_file}", clear
logit y x1 x2
predict xb_logit, xb
predict pr_logit, pr
list y xb_logit pr_logit in 1/10
matrix b = e(b)
display "B_cons=" b[1,3]
display "E_N=" e(N)
display "PREDICT_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    model = Logit(data=df, y="y", x=["x1", "x2"])
    model.fit()
    py_xb = model.predict(type="xb")
    py_pr = model.predict(type="pr")

    log = stata_result.output_content
    lines = log.splitlines()
    st_xb = []
    st_pr = []
    in_list = False
    import re
    row_pattern = re.compile(r'^\s*\d+\.\s*\|\s*\S+\s+([-\d.]+)\s+([-\d.]+)\s*\|')
    for line in lines:
        if "xb_logit" in line and "pr_logit" in line:
            in_list = True
            continue
        if in_list:
            m = row_pattern.match(line)
            if m:
                st_xb.append(float(m.group(1)))
                st_pr.append(float(m.group(2)))
            if len(st_xb) >= 10:
                break

    assert len(st_xb) == 10, f"Could not parse Stata predictions, got {len(st_xb)} rows"

    for i in range(10):
        passed, msg = tolerance_close(py_xb[i], st_xb[i], rtol=1e-5, atol=1e-6, name=f"xb[{i}]")
        assert passed, msg
        passed, msg = tolerance_close(py_pr[i], st_pr[i], rtol=1e-5, atol=1e-6, name=f"pr[{i}]")
        assert passed, msg
