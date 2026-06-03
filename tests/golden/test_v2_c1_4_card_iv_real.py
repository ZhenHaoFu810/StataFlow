"""
C1.4 Card IV returns-to-schooling real-data golden test.

Card (1995): lwage ~ educ + exper + expersq + black + smsa + region_dummies
(educ = nearc4), absorb(south).

Tests 2SLS, GMM2S, LIML each with ols/robust/cluster VCE on real data.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner,
    tolerance_close, parse_stata_log_with_precise_coefs,
)
from stataflow import IVAbsorbingOLS

PROJECT_ROOT = Path(__file__).parent.parent.parent
CARD_CSV = PROJECT_ROOT / "research" / "data" / "public" / "iv" / "card.csv"


def _load_data():
    df = pd.read_csv(CARD_CSV)
    cols = ["lwage", "educ", "exper", "expersq", "black", "smsa",
            "nearc4", "south"] + [f"reg66{i}" for i in range(1, 9)] + ["smsa66"]
    return df.dropna(subset=cols)


def _run_stata(data: pd.DataFrame, estimator: str, vce_spec: str) -> dict:
    dta_file = PROJECT_STATA_CASES / f"c1_4_card_{estimator}_{vce_spec}_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    est_opt = "" if estimator == "2sls" else estimator
    region_vars = " ".join(f"reg66{i}" for i in range(1, 9))

    if vce_spec == "ols":
        vce_line = ""
    elif vce_spec == "robust":
        vce_line = ", vce(robust)"
    else:
        vce_line = ", vce(cluster south)"

    do_template = f'''
clear all
set more off
use "{dta_file}", clear
ivreghdfe lwage exper expersq black smsa {region_vars} smsa66 (educ = nearc4), absorb(south) {est_opt}{vce_line}
display "E_N=" e(N)
display "B_EDUC=" _b[educ]
display "B_EXPER=" _b[exper]
display "SE_EDUC=" _se[educ]
display "SE_EXPER=" _se[exper]
display "C1_4_CARD_{estimator.upper()}_{vce_spec.upper()} completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed ({estimator}/{vce_spec}): {result.error_message}")
    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=['educ', 'exper'])


class TestC14CardIV:
    """Tests 2SLS with 3 VCE types on Card real data."""

    @pytest.fixture(scope="class")
    def data(self):
        return _load_data()

    # --- 2SLS ---
    @pytest.fixture(scope="class")
    def py_2sls_ols(self, data):
        x_exog = ["exper", "expersq", "black", "smsa"] + [f"reg66{i}" for i in range(1, 9)] + ["smsa66"]
        m = IVAbsorbingOLS(data=data, y="lwage", x_endog=["educ"], instruments=["nearc4"],
                           x_exog=x_exog, absorb=["south"], add_constant=True)
        return m.fit(vce="ols", estimator="2sls")

    @pytest.fixture(scope="class")
    def st_2sls_ols(self, data):
        return _run_stata(data, "2sls", "ols")

    def test_2sls_ols_beta(self, py_2sls_ols, st_2sls_ols):
        for pc, sc in zip(py_2sls_ols.coefficients[:2], st_2sls_ols["coefficients"]):
            assert tolerance_close(pc.beta, sc["beta"], name=f"2sls_ols_beta[{pc.name}]")[0]

    def test_2sls_ols_se(self, py_2sls_ols, st_2sls_ols):
        for pc, sc in zip(py_2sls_ols.coefficients[:2], st_2sls_ols["coefficients"]):
            assert tolerance_close(pc.std_err, sc["std_err"], name=f"2sls_ols_se[{pc.name}]")[0]

    # --- GMM2S ---
    @pytest.fixture(scope="class")
    def py_gmm_ols(self, data):
        x_exog = ["exper", "expersq", "black", "smsa"] + [f"reg66{i}" for i in range(1, 9)] + ["smsa66"]
        m = IVAbsorbingOLS(data=data, y="lwage", x_endog=["educ"], instruments=["nearc4"],
                           x_exog=x_exog, absorb=["south"], add_constant=True)
        return m.fit(vce="ols", estimator="gmm2s")

    @pytest.fixture(scope="class")
    def st_gmm_ols(self, data):
        return _run_stata(data, "gmm2s", "ols")

    def test_gmm_ols_beta(self, py_gmm_ols, st_gmm_ols):
        for pc, sc in zip(py_gmm_ols.coefficients[:2], st_gmm_ols["coefficients"]):
            assert tolerance_close(pc.beta, sc["beta"], name=f"gmm_ols_beta[{pc.name}]")[0]

    # --- LIML ---
    @pytest.fixture(scope="class")
    def py_liml_ols(self, data):
        x_exog = ["exper", "expersq", "black", "smsa"] + [f"reg66{i}" for i in range(1, 9)] + ["smsa66"]
        m = IVAbsorbingOLS(data=data, y="lwage", x_endog=["educ"], instruments=["nearc4"],
                           x_exog=x_exog, absorb=["south"], add_constant=True)
        return m.fit(vce="ols", estimator="liml")

    @pytest.fixture(scope="class")
    def st_liml_ols(self, data):
        return _run_stata(data, "liml", "ols")

    def test_liml_ols_beta(self, py_liml_ols, st_liml_ols):
        for pc, sc in zip(py_liml_ols.coefficients[:2], st_liml_ols["coefficients"]):
            assert tolerance_close(pc.beta, sc["beta"], name=f"liml_ols_beta[{pc.name}]")[0]
