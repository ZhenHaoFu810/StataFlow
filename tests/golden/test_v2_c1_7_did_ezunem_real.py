"""
C1.7 DID policy eval real-data golden test.

ezunem: staggered minimum wage adoption (22 cities x 9 years).
Tests did_imputation + csdid on real data with controls and pretrends.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner,
    tolerance_close, parse_stata_log_with_precise_coefs,
)
from stataflow import DIDImputation

PROJECT_ROOT = Path(__file__).parent.parent.parent
EZUNEM_DTA = PROJECT_ROOT / "research" / "data" / "public" / "did" / "ezunem_prepared.dta"


def _load_data():
    return pd.read_stata(EZUNEM_DTA)


def _run_stata(data: pd.DataFrame, spec: str) -> dict:
    dta_file = PROJECT_STATA_CASES / f"c1_7_ezunem_{spec}_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    if spec == "basic":
        cmd = "did_imputation uclms cityid year first_treat, autosample"
    elif spec == "controls":
        cmd = "did_imputation uclms cityid year first_treat, autosample controls(c1 c2 c3)"
    else:
        cmd = "did_imputation uclms cityid year first_treat, autosample pretrends(3)"

    do_template = f'''
clear all
set more off
use "{dta_file}", clear
{cmd}
display "E_N=" e(N)
display "Stata C1_7_{spec.upper()} completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed ({spec}): {result.error_message}")
    return {"ran": True}


class TestC17DIDEzunem:
    @pytest.fixture(scope="class")
    def data(self):
        return _load_data()

    def test_basic_runs(self, data):
        """DID imputation basic specification runs without error."""
        r = DIDImputation(data=data, y="uclms", id="city", time="year",
                          first_treat="first_treat").fit(autosample=True)
        assert r.sample.nobs > 0
        assert len(r.coefficients) > 0

    def test_controls_runs(self, data):
        """DID imputation with controls."""
        r = DIDImputation(data=data, y="uclms", id="city", time="year",
                          first_treat="first_treat").fit(autosample=True,
                          controls=["c1", "c2", "c3"])
        assert r.sample.nobs > 0

    def test_pretrends_runs(self, data):
        """DID imputation with pretrends."""
        r = DIDImputation(data=data, y="uclms", id="city", time="year",
                          first_treat="first_treat").fit(autosample=True, pretrends=3)
        assert r.sample.nobs > 0

    def test_stata_dual_basic(self, data):
        """Stata did_imputation basic runs."""
        _run_stata(data, "basic")

    def test_stata_dual_controls(self, data):
        """Stata did_imputation with controls runs."""
        _run_stata(data, "controls")

    def test_stata_dual_pretrends(self, data):
        """Stata did_imputation with pretrends runs."""
        _run_stata(data, "pretrends")
