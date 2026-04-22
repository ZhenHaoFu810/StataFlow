"""Golden dual-run test: predict on real Mroz data."""

import numpy as np
import pandas as pd
from pathlib import Path
import pytest
import re

from stataflow import Logit
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    tolerance_close,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MROZ_CSV = PROJECT_ROOT / "research" / "data" / "public" / "binary" / "mroz.csv"


def _load_data():
    return pd.read_csv(str(MROZ_CSV))


def test_predict_logit_mroz():
    """Logit predict xb and pr on Mroz data."""
    df = _load_data()

    dta_file = PROJECT_STATA_CASES / "w5_predict_logit_mroz_data.dta"
    dta_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off
use "{dta_file}", clear
logit inlf nwifeinc educ exper expersq age kidslt6 kidsge6
predict xb_logit, xb
predict pr_logit, pr
list inlf xb_logit pr_logit in 1/10
display "PREDICT_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    # Run Python
    model = Logit(data=df, y="inlf", x=["nwifeinc", "educ", "exper", "expersq", "age", "kidslt6", "kidsge6"])
    model.fit()
    py_xb = model.predict(type="xb")
    py_pr = model.predict(type="pr")

    # Parse first 10 rows from Stata list output
    log = stata_result.output_content
    lines = log.splitlines()
    st_xb = []
    st_pr = []
    in_list = False
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
