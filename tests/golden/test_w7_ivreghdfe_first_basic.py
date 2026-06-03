"""
Golden test: w7_ivreghdfe_first_basic - First-stage diagnostics with single absorbed FE.

Tests ivreghdfe-style 2SLS first-stage diagnostics with one absorb variable,
verifying:
- First-stage F-statistic of excluded instruments
- First-stage R-squared, partial R-squared, Shea R-squared
- Structure of result.first_stage
"""

import pytest
import numpy as np
import pandas as pd
import re
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
    tolerance_close,
)
from stataflow.estimators.iv import IVAbsorbingOLS


def _generate_test_data() -> pd.DataFrame:
    """Generate panel IV test dataset with known seed."""
    np.random.seed(54321)
    n_entities = 40
    n_per_entity = 5
    n = n_entities * n_per_entity

    entity_id = np.repeat(np.arange(n_entities), n_per_entity)
    time_id = np.tile(np.arange(n_per_entity), n_entities)

    z1 = np.random.normal(0, 1, n)
    z2 = np.random.normal(0, 1, n)
    x1 = np.random.normal(2, 1, n)

    alpha_e = np.repeat(np.random.normal(0, 2, n_entities), n_per_entity)
    v = np.random.normal(0, 0.8, n)
    x2 = alpha_e + 1.5 * z1 - 0.8 * z2 + 0.3 * x1 + v

    u = np.random.normal(0, 0.8, n) + 0.4 * v
    y = alpha_e + 2 * x1 + 1.5 * x2 + u

    return pd.DataFrame(
        {
            "y": y,
            "x1": x1,
            "x2": x2,
            "z1": z1,
            "z2": z2,
            "entity_id": entity_id,
            "time_id": time_id,
        }
    )


def _run_stata_ivreghdfe_first(data: pd.DataFrame) -> dict:
    """Run Stata ivreghdfe with first-stage diagnostics."""
    dta_file = PROJECT_STATA_CASES / "w7_ivreghdfe_first_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) keepsingletons first

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" e(F_p)

// First-stage diagnostics from e(first) matrix
// Row indices: 1=rmse, 2=sheapr2, 3=pr2, 4=F, 5=df, 6=df_r, 7=pvalue
display "FS_SHEAR2=" e(first)[2,1]
display "FS_PR2=" e(first)[3,1]
display "FS_F=" e(first)[4,1]
display "FS_DF=" e(first)[5,1]
display "FS_DFR=" e(first)[6,1]
display "FS_PVAL=" e(first)[7,1]
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")

    log_content = result.output_content or ""

    # Parse main regression results
    stata_result = {}
    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'df_a': r'E_DF_A=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'r2_adj': r'E_R2_A=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
        'f_pvalue': r'E_F_P=([\d.]+)',
    }
    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            stata_result[key] = float(val_str)

    # Parse first-stage diagnostics from display outputs
    fs_patterns = {
        'first_shea_r2': r'FS_SHEAR2=(-?[\d.eE+-]+)',
        'first_pr2': r'FS_PR2=(-?[\d.eE+-]+)',
        'first_f': r'FS_F=(-?[\d.eE+-]+)',
        'first_df': r'FS_DF=(-?[\d.eE+-]+)',
        'first_df_r': r'FS_DFR=(-?[\d.eE+-]+)',
        'first_pval': r'FS_PVAL=(-?[\d.eE+-]+)',
    }
    for key, pattern in fs_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            try:
                stata_result[key] = float(val_str)
            except ValueError:
                pass

    return stata_result


def _run_python_ivreghdfe_first(data: pd.DataFrame):
    """Run Python IVAbsorbingOLS with first-stage diagnostics."""
    model = IVAbsorbingOLS(
        data=data,
        y="y",
        x_exog=["x1"],
        x_endog=["x2"],
        instruments=["z1", "z2"],
        absorb=["entity_id"],
        add_constant=True,
    )
    return model.fit(vce="ols", first=True)


class TestW7IvreghdfeFirstBasic:
    """Golden test for w7_ivreghdfe_first_basic."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return _run_python_ivreghdfe_first(test_data)

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_ivreghdfe_first(test_data)

    def test_first_stage_exists(self, python_result):
        assert hasattr(python_result, "first_stage")
        assert "x2" in python_result.first_stage

    def test_first_stage_f_stat(self, python_result, stata_result):
        py_f = python_result.first_stage["x2"]["f_stat"]
        st_f = stata_result.get("first_f")
        assert st_f is not None, "Stata first-stage F not parsed"
        passed, msg = tolerance_close(py_f, st_f, name="first_stage_f_stat")
        assert passed, msg

    def test_first_stage_shea_r2(self, python_result, stata_result):
        py_r2 = python_result.first_stage["x2"]["shea_r2"]
        st_r2 = stata_result.get("first_shea_r2")
        assert st_r2 is not None, "Stata Shea R2 not parsed"
        passed, msg = tolerance_close(py_r2, st_r2, name="first_stage_shea_r2")
        assert passed, msg

    def test_first_stage_partial_r2(self, python_result, stata_result):
        py_r2 = python_result.first_stage["x2"]["partial_r2"]
        st_r2 = stata_result.get("first_pr2")
        assert st_r2 is not None, "Stata partial R2 not parsed"
        passed, msg = tolerance_close(py_r2, st_r2, name="first_stage_partial_r2")
        assert passed, msg

    def test_first_stage_df(self, python_result, stata_result):
        py_df = python_result.first_stage["x2"]["df"]
        py_df_r = python_result.first_stage["x2"]["df_r"]
        st_df = stata_result.get("first_df")
        st_df_r = stata_result.get("first_df_r")
        assert st_df is not None and st_df_r is not None
        assert py_df == st_df, f"df mismatch: Python={py_df}, Stata={st_df}"
        assert py_df_r == st_df_r, f"df_r mismatch: Python={py_df_r}, Stata={st_df_r}"

    def test_first_stage_f_pvalue_small(self, python_result):
        pval = python_result.first_stage["x2"]["f_pvalue"]
        assert pval is not None
        assert pval < 0.01, f"First-stage F p-value should be small: {pval}"

    def test_second_stage_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get("nobs"), name="nobs"
        )
        assert passed, msg

    def test_second_stage_f_stat(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get("f_stat"), name="f_stat"
        )
        assert passed, msg

    def test_second_stage_r2(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get("r2"), name="r2"
        )
        assert passed, msg
