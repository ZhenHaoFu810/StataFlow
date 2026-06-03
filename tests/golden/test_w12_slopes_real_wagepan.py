"""
Golden test: w12_slopes_real_wagepan - slope absorption on real wagepan data.

Tests `absorb(nr##c.year)` on Wooldridge wagepan panel (545 firms, T=8, N=4360).

Uses `union` and `hours` as regressors since they vary independently of year
within firms. `exper` is NOT usable here because exper = firm_base + year within
each firm, making it perfectly collinear with the absorbed nr##c.year terms.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
    tolerance_close,
    parse_stata_log_with_precise_coefs,
)
from stataflow import AbsorbingOLS

PROJECT_ROOT = Path(__file__).parent.parent.parent
WAGEPAN_CSV = PROJECT_ROOT / "research" / "data" / "public" / "panel" / "wooldridge" / "wagepan.csv"


def _load_data() -> pd.DataFrame:
    df = pd.read_csv(str(WAGEPAN_CSV))
    df = df.dropna(subset=["lwage", "union", "hours", "nr", "year"])
    return df


def _run_stata(data: pd.DataFrame) -> dict:
    """Run Stata reghdfe with slope absorption on wagepan."""
    dta_file = PROJECT_STATA_CASES / "w12_slopes_real_wagepan_data.dta"
    dta_file.parent.mkdir(parents=True, exist_ok=True)
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

reghdfe lwage union hours, absorb(nr##c.year) keepsingletons

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)

display "B_UNION=" _b[union]
display "B_HOURS=" _b[hours]
display "B__CONS=" _b[_cons]
display "SE_UNION=" _se[union]
display "SE_HOURS=" _se[hours]
display "SE__CONS=" _se[_cons]

display "Stata slopes wagepan completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=['union', 'hours', '_cons'])


class TestW12SlopesRealWagepan:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _load_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = AbsorbingOLS(
            data=test_data,
            y="lwage",
            x=["union", "hours"],
            absorb="nr##c.year",
            add_constant=True,
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata(test_data)

    def test_sample_size(self, python_result, stata_result):
        assert python_result.sample.nobs == stata_result.get('nobs'), (
            f"Sample size mismatch: {python_result.sample.nobs} vs {stata_result.get('nobs')}"
        )

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg
