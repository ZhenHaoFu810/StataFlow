"""
Golden test: v1_xtreg_fe_real_grunfeld - Fixed-effects regression on Grunfeld panel.

Real-data validation using the classic Grunfeld investment panel.
"""

import re
from pathlib import Path

import pandas as pd
import pytest

from stataflow.compat.stata import xtreg_fe
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_CASES,
    PROJECT_STATA_OUTPUT,
    tolerance_close,
)


def _load_data() -> pd.DataFrame:
    return pd.read_csv(Path("research/data/public/panel/grunfeld.csv"))


def _parse_stata_log(log_content: str) -> dict:
    result = {}
    e_patterns = {
        "nobs": r"E_N=([\d]+)",
        "df_model": r"E_DF_M=([\d]+)",
        "df_resid": r"E_DF_R=([\d]+)",
        "r2_w": r"E_R2_W=([\d.]+)",
        "rmse": r"E_RMSE=([\d.]+)",
        "f_stat": r"E_F=([\d.]+)",
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith("."):
                val_str = "0" + val_str
            result[key] = float(val_str)

    coefficients = []
    b_matches = {k.lower(): v for k, v in re.findall(r"B_(\w+)=(-?[\d.]+)", log_content)}
    se_matches = {k.lower(): v for k, v in re.findall(r"SE_(\w+)=(-?[\d.]+)", log_content)}
    for name in ["value", "capital"]:
        if name in b_matches and name in se_matches:
            coefficients.append(
                {
                    "name": name,
                    "beta": float(b_matches[name]),
                    "std_err": float(se_matches[name]),
                }
            )
    result["coefficients"] = coefficients
    return result


def _run_stata_xtreg(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "v1_xtreg_fe_real_grunfeld_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f"""
clear all
set more off

use "{dta_file}", clear
xtset firm year
xtreg inv value capital, fe

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2_W=" e(r2_w)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "B_value=" _b[value]
display "SE_value=" _se[value]
display "B_capital=" _b[capital]
display "SE_capital=" _se[capital]
"""

    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")
    return _parse_stata_log(result.output_content)


class TestV1XtregFeRealGrunfeld:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _load_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return xtreg_fe(test_data, y="inv", x=["value", "capital"], fe="firm", vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_xtreg(test_data)

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.sample.nobs, stata_result["nobs"], name="nobs")
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.fit.df_model, stata_result["df_model"], name="df_model")
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.fit.df_resid, stata_result["df_resid"], name="df_resid")
        assert passed, msg

    def test_r2_within(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.fit.r2, stata_result["r2_w"], name="r2_w")
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.fit.rmse, stata_result["rmse"], name="rmse")
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.fit.f_stat, stata_result["f_stat"], name="f_stat")
        assert passed, msg

    def test_coefficient_names(self, python_result, stata_result):
        py_names = [coef.name for coef in python_result.coefficients]
        st_names = [coef["name"] for coef in stata_result["coefficients"]]
        assert py_names == st_names

    def test_coefficients(self, python_result, stata_result):
        for py_coef, st_coef in zip(python_result.coefficients, stata_result["coefficients"]):
            passed, msg = tolerance_close(py_coef.beta, st_coef["beta"], name=f"beta[{py_coef.name}]")
            assert passed, msg

    def test_standard_errors(self, python_result, stata_result):
        for py_coef, st_coef in zip(python_result.coefficients, stata_result["coefficients"]):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef["std_err"], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg
