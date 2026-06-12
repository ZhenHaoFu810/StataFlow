"""
Golden test: a2_factor_regress_missing_base

Tests FVAR-001: factor-variable sample screening must drop rows where any
underlying variable is missing before determining categorical base levels.
When g=1 rows have x missing, Stata and Python must both use g=2 as base.
"""

import pytest
import pandas as pd
import numpy as np
from tests.golden.test_utils import (
    PROJECT_STATA_CASES,
    PROJECT_STATA_OUTPUT,
    run_stata_factor,
    tolerance_close,
)
from stataflow.compat.stata import regress


def _run_stata(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "a2_factor_missing_base.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

use "$DATA_FILE", clear

regress y i.g##c.x

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "COEF 3.g " _b[3.g] " " _se[3.g]
display "COEF x " _b[x] " " _se[x]
display "COEF 3.g#c.x " _b[3.g#c.x] " " _se[3.g#c.x]
display "COEF _cons " _b[_cons] " " _se[_cons]
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_factor(do_content)


class TestA2FactorRegressMissingBase:
    @pytest.fixture(scope="class")
    def test_data(self):
        rng = np.random.default_rng(2026)
        df = pd.DataFrame({
            "g": [1, 1, 2, 2, 2, 3, 3, 3],
            "x": [np.nan, np.nan, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        })
        df["y"] = df["y"] + rng.normal(0, 0.5, size=len(df))
        return df

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return regress(test_data, y="y", x=["i.g##c.x"])

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata(test_data)

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

    def test_df_resid(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get("df_resid"), name="df_resid"
        )
        assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        assert len(python_result.coefficients) == len(stata_result.get("coefficients", []))

    def test_coefficients_names(self, python_result, stata_result):
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c["name"] for c in stata_result.get("coefficients", [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef["beta"], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef["std_err"], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg
