"""Golden dual-run test: margins on real crime1 data."""

import numpy as np
import pandas as pd
from pathlib import Path
import pytest
import re

from statapy import Poisson
from statapy.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    tolerance_close,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
CRIME1_CSV = PROJECT_ROOT / "research" / "data" / "public" / "count" / "crime1.csv"


def _load_data():
    return pd.read_csv(str(CRIME1_CSV))


def _parse_margins_log(log_content: str) -> dict:
    """Parse margins output from Stata log."""
    lines = log_content.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if "dy/dx   Std. err.      z    P>|z|" in line or "dy/dx   Delta-method Std. err." in line or "dy/dx   std. err.      t    P>|t|" in line:
            start_idx = i
            break

    results = {}
    if start_idx is None:
        return results

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
            _num_cap = r'(-?\d+\.\d+|-?\.\d+|-?\d+)'
            simple = re.match(r'^\s+([A-Za-z_][A-Za-z0-9_]*)\s+\|\s+' + _num_cap + r'\s+' + _num_cap, line)
            if simple:
                results[simple.group(1)] = {
                    'dy/dx': float(simple.group(2)),
                    'std_err': float(simple.group(3)),
                }
    return results


def test_margins_poisson_crime1():
    """Poisson margins dydx and atmeans on crime1 data."""
    df = _load_data()

    dta_file = PROJECT_STATA_CASES / "w5_margins_poisson_crime1_data.dta"
    dta_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off
use "{dta_file}", clear
poisson narr86 pcnv avgsen tottime ptime86 qemp86 inc86 black hispan born60
margins, dydx(*)
margins, dydx(*) atmeans
display "MARGINS_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    model = Poisson(data=df, y="narr86", x=["pcnv", "avgsen", "tottime", "ptime86", "qemp86", "inc86", "black", "hispan", "born60"])
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

    for name in ["pcnv", "avgsen", "tottime", "ptime86", "qemp86", "inc86", "black", "hispan", "born60"]:
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
