"""
Golden test: p3_ppmlhdfe_fit_stats

Tests ppmlhdfe deviance and pseudo-R2 alignment with Stata 17 output.
This specifically covers the Phase B additions to the result object.
"""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow import PPMLHDFE
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    tolerance_close,
)


def _generate_test_data() -> pd.DataFrame:
    """Generate PPMLHDFE fit-stats test dataset with known seed."""
    np.random.seed(54321)
    n_entities = 20
    n_times = 10
    n = n_entities * n_times
    entities = np.repeat(np.arange(n_entities), n_times)
    times = np.tile(np.arange(n_times), n_entities)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    fe = np.random.normal(0, 0.5, n_entities)[entities]
    eta = 0.3 + 0.4 * x1 - 0.3 * x2 + fe
    mu = np.exp(eta)
    y = np.random.poisson(mu)
    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "entity_id": entities,
        "time_id": times,
    })


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata ppmlhdfe log output for fit statistics."""
    result = {}

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_a': r'E_DF_A=([\d]+)',
        'll': r'E_LL=(-?[\d.]+)',
        'deviance': r'E_DEVIANCE=(-?[\d.]+)',
        'pseudo_r2': r'E_R2_P=(-?[\d.]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str == '.' or val_str == '-.':
                continue
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    return result


def _run_stata_ppmlhdfe(data: pd.DataFrame) -> dict:
    """Run Stata ppmlhdfe and extract fit statistics."""
    dta_file = PROJECT_STATA_CASES / "p3_ppmlhdfe_fit_stats_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

ppmlhdfe y x1 x2, absorb(entity_id) vce(robust)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_A=" e(df_a)
display "E_LL=" e(ll)
display "E_DEVIANCE=" e(deviance)
display "E_R2_P=" e(r2_p)

display "Stata ppmlhdfe fit stats completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestP3PpmlhdfeFitStats:
    """Golden test for ppmlhdfe deviance and pseudo-R2."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = PPMLHDFE(
            data=test_data,
            y="y",
            x=["x1", "x2"],
            absorb=["entity_id"],
        )
        return model.fit(vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_ppmlhdfe(test_data)

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get("nobs"), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get("df_model"), name="df_model"
        )
        assert passed, msg

    def test_df_a(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_a, stata_result.get("df_a"), name="df_a"
        )
        assert passed, msg

    def test_ll(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.ll, stata_result.get("ll"), name="ll", rtol=1e-6, atol=1e-6
        )
        assert passed, msg

    def test_deviance(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.deviance,
            stata_result.get("deviance"),
            name="deviance",
            rtol=1e-6,
            atol=1e-6,
        )
        assert passed, msg

    def test_pseudo_r2(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.pseudo_r2,
            stata_result.get("pseudo_r2"),
            name="pseudo_r2",
            rtol=1e-4,
            atol=1e-6,
        )
        assert passed, msg
