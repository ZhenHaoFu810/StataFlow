"""
C1.8 RD Senate real-data golden test.

Senate election RD: incumbency advantage at 50% vote threshold.
Tests rdrobust with key bandwidth selectors on real data.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner,
    tolerance_close, parse_stata_log_with_precise_coefs,
)
from stataflow import RDRobust

PROJECT_ROOT = Path(__file__).parent.parent.parent
SENATE_DTA = PROJECT_ROOT / "research" / "data" / "public" / "rdrobust_senate_with_z.dta"


def _load_data():
    return pd.read_stata(SENATE_DTA)


def _run_stata(data: pd.DataFrame, bwselect: str) -> dict:
    dta_file = PROJECT_STATA_CASES / f"c1_8_senate_{bwselect}_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off
use "{dta_file}", clear
rdrobust vote margin, bwselect({bwselect})
display "E_N=" e(N)
display "C1_8_SENATE_{bwselect.upper()} completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed ({bwselect}): {result.error_message}")
    return {"ran": True}


class TestC18RDSenate:
    @pytest.fixture(scope="class")
    def data(self):
        return _load_data()

    def test_mserd_runs(self, data):
        r = RDRobust(data=data, y="vote", x="margin", bwselect="mserd")
        res = r.fit()
        assert res.sample.nobs > 0
        assert res.coefficients[0].beta != 0

    def test_msetwo_runs(self, data):
        r = RDRobust(data=data, y="vote", x="margin", bwselect="msetwo")
        res = r.fit()
        assert res.sample.nobs > 0

    def test_msesum_runs(self, data):
        r = RDRobust(data=data, y="vote", x="margin", bwselect="msesum")
        res = r.fit()
        assert res.sample.nobs > 0

    def test_cerrd_runs(self, data):
        r = RDRobust(data=data, y="vote", x="margin", bwselect="cerrd")
        res = r.fit()
        assert res.sample.nobs > 0

    def test_stata_mserd(self, data):
        _run_stata(data, "mserd")

    def test_stata_msetwo(self, data):
        _run_stata(data, "msetwo")
