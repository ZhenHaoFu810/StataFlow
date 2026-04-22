"""
Golden test: a2_factor_logit_basic

Tests Stata factor-variable syntax alignment for ``logit`` with
a continuous-continuous full interaction ``c.x1##c.x2``.
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
from stataflow.compat.stata import logit


def _run_stata(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "a2_factor_test_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

use "$DATA_FILE", clear

logit y_bin c.x1##c.x2

display "E_N=" e(N)
display "E_DF_M=" e(df_m)

display "COEF x1 " _b[x1] " " _se[x1]
display "COEF x2 " _b[x2] " " _se[x2]
display "COEF c.x1#c.x2 " _b[c.x1#c.x2] " " _se[c.x1#c.x2]
display "COEF _cons " _b[_cons] " " _se[_cons]
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_factor(do_content)


class TestA2FactorLogitBasic:
    @pytest.fixture(scope="class")
    def test_data(self):
        return pd.read_stata(PROJECT_STATA_CASES / "a2_factor_test_data.dta")

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return logit(test_data, y="y_bin", x=["c.x1##c.x2"])

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
