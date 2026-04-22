"""
Golden test: a2_factor_ppmlhdfe_basic

Tests Stata factor-variable syntax alignment for ``ppmlhdfe`` with
a categorical-continuous full interaction ``i.g##c.x1`` and two
absorbed fixed effects.
"""

import numpy as np
import pytest
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    run_stata_factor,
    tolerance_close,
)
from stataflow.compat.stata import ppmlhdfe


def _make_data(n=400, seed=123):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "x1": rng.normal(0, 1, size=n),
        "g": rng.choice([1, 2, 3], size=n),
        "firm": rng.choice(range(10), size=n),
        "year": rng.choice(range(5), size=n),
    })
    # DGP for Poisson
    df["g_2"] = (df["g"] == 2).astype(float)
    df["g_3"] = (df["g"] == 3).astype(float)
    ln_mu = (
        0.5
        + 0.3 * df["x1"]
        + 0.4 * df["g_2"]
        - 0.2 * df["g_3"]
        + 0.15 * df["g_2"] * df["x1"]
        - 0.1 * df["g_3"] * df["x1"]
    )
    mu = np.exp(ln_mu)
    df["y"] = rng.poisson(mu).astype(float)
    # Ensure no zeros to avoid edge-case separation issues in this test
    df["y"] = df["y"].clip(lower=1.0)
    return df


def _run_stata(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "a2_factor_ppmlhdfe_test_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

use "$DATA_FILE", clear

ppmlhdfe y i.g##c.x1, absorb(firm year)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)

display "COEF 2.g " _b[2.g] " " _se[2.g]
display "COEF 3.g " _b[3.g] " " _se[3.g]
display "COEF x1 " _b[x1] " " _se[x1]
display "COEF 2.g#c.x1 " _b[2.g#c.x1] " " _se[2.g#c.x1]
display "COEF 3.g#c.x1 " _b[3.g#c.x1] " " _se[3.g#c.x1]
display "COEF _cons " _b[_cons] " " _se[_cons]
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_factor(do_content)


class TestA2FactorPpmlhdfeBasic:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _make_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return ppmlhdfe(
            test_data,
            y="y",
            x=["i.g##c.x1"],
            absorb="firm year",
        )

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
