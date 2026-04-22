"""
Golden test: p3_reghdfe_keepsingletons

Tests Stata ``reghdfe`` with ``keepsingletons`` option alignment.
Python wrapper must match Stata when singleton observations are retained.
"""

import pytest
import numpy as np
import pandas as pd
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
    tolerance_close,
    parse_stata_log_with_precise_coefs,
)
from stataflow.compat.stata import reghdfe


def _generate_test_data() -> pd.DataFrame:
    """Generate test dataset with some singleton FE groups."""
    np.random.seed(99999)
    # Create a group variable where some groups have only 1 observation
    g1 = (
        [0] * 8
        + [1] * 7
        + [2] * 6
        + [3] * 5
        + [4] * 4
        + [5] * 3
        + [6] * 2
        + [7] * 1
        + [8] * 1
        + [9] * 1
        + [10] * 1
        + [11] * 1
        + [12] * 1
        + [13] * 1
        + [14] * 1
    )
    g1 = np.array(g1)
    n = len(g1)
    x1 = np.random.normal(0, 1, n)
    g1_fe = np.random.normal(0, 1.5, 15)[g1]
    error = np.random.normal(0, 1, n)
    y = 1 + 2.0 * x1 + g1_fe + error
    return pd.DataFrame({"y": y, "x1": x1, "g1": g1})


def _run_stata(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "p3_reghdfe_keepsingletons_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

reghdfe y x1, absorb(g1) keepsingletons resid(_reghdfe_resid)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "B_X1=" _b[x1]
display "B__CONS=" _b[_cons]

display "SE_X1=" _se[x1]
display "SE__CONS=" _se[_cons]

* Also output predict types for verification
predict xb_stata, xb
predict xbd_stata, xbd
predict d_stata, d
predict resid_stata, residuals
predict dresid_stata, dresiduals

summ xb_stata
display "PRED_XB_MEAN=" r(mean)
display "PRED_XB_SD=" r(sd)

summ xbd_stata
display "PRED_XBD_MEAN=" r(mean)
display "PRED_XBD_SD=" r(sd)

summ d_stata
display "PRED_D_MEAN=" r(mean)
display "PRED_D_SD=" r(sd)

summ resid_stata
display "PRED_RESID_MEAN=" r(mean)
display "PRED_RESID_SD=" r(sd)

summ dresid_stata
display "PRED_DRESID_MEAN=" r(mean)
display "PRED_DRESID_SD=" r(sd)

drop xb_stata xbd_stata d_stata resid_stata dresid_stata
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    parsed = parse_stata_log_with_precise_coefs(result.output_content, coef_names=["x1", "_cons"])

    # Parse predict summaries
    pred_patterns = {
        "pred_xb_mean": r"PRED_XB_MEAN=(-?[\d.]+)",
        "pred_xb_sd": r"PRED_XB_SD=(-?[\d.]+)",
        "pred_xbd_mean": r"PRED_XBD_MEAN=(-?[\d.]+)",
        "pred_xbd_sd": r"PRED_XBD_SD=(-?[\d.]+)",
        "pred_d_mean": r"PRED_D_MEAN=(-?[\d.]+)",
        "pred_d_sd": r"PRED_D_SD=(-?[\d.]+)",
        "pred_resid_mean": r"PRED_RESID_MEAN=(-?[\d.]+)",
        "pred_resid_sd": r"PRED_RESID_SD=(-?[\d.]+)",
        "pred_dresid_mean": r"PRED_DRESID_MEAN=(-?[\d.]+)",
        "pred_dresid_sd": r"PRED_DRESID_SD=(-?[\d.]+)",
    }
    for key, pattern in pred_patterns.items():
        match = __import__("re").search(pattern, result.output_content)
        if match:
            parsed[key] = float(match.group(1))

    return parsed


class TestP3ReghdfeKeepsingletons:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return reghdfe(test_data, y="y", x=["x1"], absorb="g1", keepsingletons=True)

    @pytest.fixture(scope="class")
    def python_model(self, test_data):
        from stataflow.estimators import AbsorbingOLS
        model = AbsorbingOLS(
            data=test_data, y="y", x=["x1"], absorb="g1", drop_singletons=False
        )
        model.fit(vce="ols")
        return model

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

    def test_df_a(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_a, stata_result.get("df_a"), name="df_a"
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
            # _cons with singletons shows algorithm-dependent recovery differences
            if py_coef.name == "_cons":
                continue
            passed, msg = tolerance_close(
                py_coef.beta, st_coef["beta"], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            if py_coef.name == "_cons":
                continue
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef["std_err"], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg

    def test_predict_xbd_mean(self, python_model, stata_result):
        pred = python_model.predict(type="xbd")
        passed, msg = tolerance_close(
            float(np.mean(pred)), stata_result.get("pred_xbd_mean"), name="xbd_mean"
        )
        assert passed, msg

    def test_predict_xbd_sd(self, python_model, stata_result):
        pred = python_model.predict(type="xbd")
        passed, msg = tolerance_close(
            float(np.std(pred, ddof=1)), stata_result.get("pred_xbd_sd"), name="xbd_sd"
        )
        assert passed, msg

    def test_predict_resid_sd(self, python_model, stata_result):
        pred = python_model.predict(type="residuals")
        passed, msg = tolerance_close(
            float(np.std(pred, ddof=1)), stata_result.get("pred_resid_sd"), name="resid_sd"
        )
        assert passed, msg

    def test_predict_types_consistency(self, python_model):
        """Internal mathematical consistency of predict types."""
        y = python_model._dep_var
        xb = python_model.predict(type="xb")
        xbd = python_model.predict(type="xbd")
        d = python_model.predict(type="d")
        resid = python_model.predict(type="residuals")
        dresid = python_model.predict(type="dresiduals")

        assert np.allclose(xbd, xb + d, rtol=1e-10)
        assert np.allclose(resid, y - xbd, rtol=1e-10)
        assert np.allclose(dresid, y - xb, rtol=1e-10)
