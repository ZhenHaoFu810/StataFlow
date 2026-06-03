"""
Golden test: w11_estat_ic - estat ic for ppmlhdfe.

Tests estat_ic() against Stata estat ic output.
"""

import pytest
import numpy as np
import pandas as pd
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
)
from stataflow.estimators.ppmlhdfe import PPMLHDFE
from stataflow.postestimation import estat_ic


def _generate_test_data() -> pd.DataFrame:
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
        "entity_id": entities.astype(np.int64),
        "time_id": times.astype(np.int64),
    })


def _run_stata_estat_ic(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "w11_estat_ic_data.dta"
    data.to_stata(str(dta_file), write_index=False)
    do_template = f'''
clear all
set more off
use "{dta_file}", clear
ppmlhdfe y x1 x2, absorb(entity_id) d
estat ic
matrix S = r(S)
file open out using "{PROJECT_STATA_OUTPUT}/w11_estat_ic_values.txt", write replace
file write out (S[1,1]) " " (S[1,3]) " " (S[1,4]) " " (S[1,5]) " " (S[1,6])
file close out
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")

    txt_file = PROJECT_STATA_OUTPUT / "w11_estat_ic_values.txt"
    with open(txt_file, "r") as f:
        vals = [float(v) for v in f.read().strip().split()]
    return {
        "N": vals[0],
        "ll": vals[1],
        "k": vals[2],
        "aic": vals[3],
        "bic": vals[4],
    }


def _run_python_estat_ic(data: pd.DataFrame):
    model = PPMLHDFE(
        data=data,
        y="y",
        x=["x1", "x2"],
        absorb="entity_id",
        add_constant=True,
    )
    result = model.fit(vce="ols")
    return estat_ic(result)


class TestW11EstatIc:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_ic(self, test_data):
        return _run_python_estat_ic(test_data)

    @pytest.fixture(scope="class")
    def stata_ic(self, test_data):
        return _run_stata_estat_ic(test_data)

    def test_fields_exist(self, python_ic, stata_ic):
        for key in ["N", "ll", "k", "aic", "bic"]:
            assert key in python_ic, f"{key} missing in Python ic"
            assert key in stata_ic, f"{key} missing in Stata ic"

    def test_n_match(self, python_ic, stata_ic):
        assert python_ic["N"] == stata_ic["N"], \
            f"N mismatch: {python_ic['N']} vs {stata_ic['N']}"

    def test_k_match(self, python_ic, stata_ic):
        assert python_ic["k"] == stata_ic["k"], \
            f"k mismatch: {python_ic['k']} vs {stata_ic['k']}"

    def test_ll_match(self, python_ic, stata_ic):
        assert np.allclose(python_ic["ll"], stata_ic["ll"], rtol=1e-6, atol=1e-6), \
            f"ll mismatch: {python_ic['ll']} vs {stata_ic['ll']}"

    def test_aic_match(self, python_ic, stata_ic):
        assert np.allclose(python_ic["aic"], stata_ic["aic"], rtol=1e-6, atol=1e-6), \
            f"aic mismatch: {python_ic['aic']} vs {stata_ic['aic']}"

    def test_bic_match(self, python_ic, stata_ic):
        assert np.allclose(python_ic["bic"], stata_ic["bic"], rtol=1e-6, atol=1e-6), \
            f"bic mismatch: {python_ic['bic']} vs {stata_ic['bic']}"
