"""Golden dual-run test: margins basic synthetic cases."""

import numpy as np
import pandas as pd
from pathlib import Path
import pytest
import re

from stataflow import OLS, Logit, Probit, Poisson
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_ROOT,
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    parse_stata_log,
    tolerance_close,
)


def _parse_margins_log(log_content: str) -> dict:
    """Parse margins output from Stata log."""
    lines = log_content.splitlines()
    # Find margins table
    start_idx = None
    for i, line in enumerate(lines):
        if "dy/dx   Std. err.      z    P>|z|" in line or "dy/dx   Delta-method Std. err." in line or "dy/dx   std. err.      t    P>|t|" in line:
            start_idx = i
            break

    results = {}
    if start_idx is None:
        return results

    # Look for table delimiter
    delim_idx = None
    for j in range(start_idx, min(start_idx + 10, len(lines))):
        if "---------+" in lines[j] or "------------+" in lines[j]:
            delim_idx = j
            break

    if delim_idx is None:
        return results

    _num = r'(-?\d+\.\d+|-?\.\d+|-?\d+)'
    coef_pattern = re.compile(
        r'^\s+([A-Za-z_][A-Za-z0-9_]*)\s+\|\s+' + _num + r'\s+' + _num + r'\s+' + _num + r'\s+([0-9.]+)'
    )
    for line in lines[delim_idx + 1:]:
        if line.strip() == '' or line.strip().startswith("|") and "+" in line:
            if results:
                break
            continue
        match = coef_pattern.match(line)
        if match:
            results[match.group(1)] = {
                'dy/dx': float(match.group(2)),
                'std_err': float(match.group(3)),
                'z': float(match.group(4)),
                'pvalue': float(match.group(5)),
            }
        else:
            # Try simpler pattern for atmeans
            _num_cap = r'(-?\d+\.\d+|-?\.\d+|-?\d+)'
            simple = re.match(r'^\s+([A-Za-z_][A-Za-z0-9_]*)\s+\|\s+' + _num_cap + r'\s+' + _num_cap, line)
            if simple:
                results[simple.group(1)] = {
                    'dy/dx': float(simple.group(2)),
                    'std_err': float(simple.group(3)),
                }
    return results


def test_margins_ols_basic():
    """OLS margins dydx should equal coefficients."""
    np.random.seed(44)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = 1.0 + 2.0 * x1 + 0.5 * x2 + np.random.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    dta_file = PROJECT_STATA_CASES / "w5_margins_ols_data.dta"
    dta_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off
use "{dta_file}", clear
reg y x1 x2
margins, dydx(*)
matrix b = e(b)
display "B_x1=" b[1,1]
display "B_x2=" b[1,2]
display "MARGINS_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    model = OLS(data=df, y="y", x=["x1", "x2"])
    model.fit()
    py_marg = model.margins(type="dydx")

    assert "_cons" not in py_marg.params, "margins result should not contain _cons"

    stata = _parse_margins_log(stata_result.output_content)
    for name in ["x1", "x2"]:
        assert name in stata, f"Missing Stata margin for {name}"
        passed, msg = tolerance_close(py_marg.params[name], stata[name]["dy/dx"], rtol=1e-5, atol=1e-6, name=f"dydx[{name}]")
        assert passed, msg
        passed, msg = tolerance_close(py_marg.bse[name], stata[name]["std_err"], rtol=1e-4, atol=1e-5, name=f"se[{name}]")
        assert passed, msg


def test_margins_logit_basic():
    """Logit margins dydx and atmeans on synthetic data."""
    np.random.seed(45)
    n = 300
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    pr = 1.0 / (1.0 + np.exp(-(0.5 + x1 - 0.5 * x2)))
    y = (np.random.uniform(0, 1, n) < pr).astype(int)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    dta_file = PROJECT_STATA_CASES / "w5_margins_logit_data.dta"
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off
use "{dta_file}", clear
logit y x1 x2
margins, dydx(*)
margins, dydx(*) atmeans
display "MARGINS_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    model = Logit(data=df, y="y", x=["x1", "x2"])
    model.fit()

    # Split log for dydx and atmeans
    log = stata_result.output_content
    parts = log.split("margins, dydx(*) atmeans")
    assert len(parts) == 2, "Could not split log into dydx and atmeans sections"

    stata_dydx = _parse_margins_log(parts[0])
    stata_atmeans = _parse_margins_log(parts[1])

    py_dydx = model.margins(type="dydx")
    py_atmeans = model.margins(type="atmeans")

    assert "_cons" not in py_dydx.params, "margins dydx result should not contain _cons"
    assert "_cons" not in py_atmeans.params, "margins atmeans result should not contain _cons"

    for name in ["x1", "x2"]:
        if name in stata_dydx:
            passed, msg = tolerance_close(py_dydx.params[name], stata_dydx[name]["dy/dx"], rtol=1e-3, atol=1e-4, name=f"dydx[{name}]")
            assert passed, msg
            passed, msg = tolerance_close(py_dydx.bse[name], stata_dydx[name]["std_err"], rtol=1e-2, atol=1e-3, name=f"se_dydx[{name}]")
            assert passed, msg
        if name in stata_atmeans:
            passed, msg = tolerance_close(py_atmeans.params[name], stata_atmeans[name]["dy/dx"], rtol=1e-3, atol=1e-4, name=f"atmeans[{name}]")
            assert passed, msg
            passed, msg = tolerance_close(py_atmeans.bse[name], stata_atmeans[name]["std_err"], rtol=1e-2, atol=1e-3, name=f"se_atmeans[{name}]")
            assert passed, msg


def test_margins_probit_basic():
    """Probit margins dydx on synthetic data."""
    np.random.seed(46)
    n = 300
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    pr = 1.0 / (1.0 + np.exp(-(0.5 + x1 - 0.5 * x2)))
    y = (np.random.uniform(0, 1, n) < pr).astype(int)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    dta_file = PROJECT_STATA_CASES / "w5_margins_probit_data.dta"
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off
use "{dta_file}", clear
probit y x1 x2
margins, dydx(*)
display "MARGINS_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    model = Probit(data=df, y="y", x=["x1", "x2"])
    model.fit()
    py_marg = model.margins(type="dydx")

    assert "_cons" not in py_marg.params, "margins result should not contain _cons"

    stata = _parse_margins_log(stata_result.output_content)
    for name in ["x1", "x2"]:
        if name in stata:
            passed, msg = tolerance_close(py_marg.params[name], stata[name]["dy/dx"], rtol=1e-3, atol=1e-4, name=f"dydx[{name}]")
            assert passed, msg
            passed, msg = tolerance_close(py_marg.bse[name], stata[name]["std_err"], rtol=1e-2, atol=1e-3, name=f"se[{name}]")
            assert passed, msg


def test_margins_poisson_basic():
    """Poisson margins dydx on synthetic data."""
    np.random.seed(47)
    n = 300
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = np.random.poisson(np.exp(0.2 + 0.3 * x1 + 0.1 * x2))
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    dta_file = PROJECT_STATA_CASES / "w5_margins_poisson_data.dta"
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off
use "{dta_file}", clear
poisson y x1 x2
margins, dydx(*)
display "MARGINS_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    model = Poisson(data=df, y="y", x=["x1", "x2"])
    model.fit()
    py_marg = model.margins(type="dydx")

    assert "_cons" not in py_marg.params, "margins result should not contain _cons"

    stata = _parse_margins_log(stata_result.output_content)
    for name in ["x1", "x2"]:
        if name in stata:
            passed, msg = tolerance_close(py_marg.params[name], stata[name]["dy/dx"], rtol=1e-3, atol=1e-4, name=f"dydx[{name}]")
            assert passed, msg
            passed, msg = tolerance_close(py_marg.bse[name], stata[name]["std_err"], rtol=1e-2, atol=1e-3, name=f"se[{name}]")
            assert passed, msg
