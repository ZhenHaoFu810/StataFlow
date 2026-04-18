"""
Golden test: a2_factor_regress_basic

Tests Stata factor-variable syntax alignment for ``regress`` with
a categorical-continuous full interaction ``i.g##c.x1``.
"""

import pytest
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    run_stata_factor,
    tolerance_close,
)
from statapy.compat.stata import regress


def _run_stata(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "a2_factor_test_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

use "$DATA_FILE", clear

regress y i.g##c.x1

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "COEF 2.g " _b[2.g] " " _se[2.g]
display "COEF 3.g " _b[3.g] " " _se[3.g]
display "COEF x1 " _b[x1] " " _se[x1]
display "COEF 2.g#c.x1 " _b[2.g#c.x1] " " _se[2.g#c.x1]
display "COEF 3.g#c.x1 " _b[3.g#c.x1] " " _se[3.g#c.x1]
display "COEF _cons " _b[_cons] " " _se[_cons]
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_factor(do_content)


class TestA2FactorRegressBasic:
    @pytest.fixture(scope="class")
    def test_data(self):
        return pd.read_stata(PROJECT_STATA_CASES / "a2_factor_test_data.dta")

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return regress(test_data, y="y", x=["i.g##c.x1"])

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

    def test_r2(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get("r2"), name="r2"
        )
        assert passed, msg

    def test_r2_adj(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.r2_adj, stata_result.get("r2_adj"), name="r2_adj"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get("rmse"), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get("f_stat"), name="f_stat"
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
