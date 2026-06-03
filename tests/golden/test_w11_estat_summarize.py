"""
Golden test: w11_estat_summarize - estat summarize for reghdfe.

Tests estat_summarize() against Stata estat summarize output.
"""

import pytest
import numpy as np
import pandas as pd
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
)
from stataflow.estimators.absorbing_ols import AbsorbingOLS
from stataflow.postestimation import estat_summarize


def _generate_test_data() -> pd.DataFrame:
    np.random.seed(54321)
    n_entities = 30
    n_per_entity = 6
    n = n_entities * n_per_entity
    entity_id = np.repeat(np.arange(n_entities), n_per_entity)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    alpha = np.repeat(np.random.normal(0, 1.5, n_entities), n_per_entity)
    y = alpha + 1.0 + 2.0 * x1 - 0.5 * x2 + np.random.normal(0, 0.5, n)
    return pd.DataFrame({
        "entity_id": entity_id.astype(np.int64),
        "x1": x1,
        "x2": x2,
        "y": y,
    })


def _run_stata_estat_summarize(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "w11_estat_summarize_data.dta"
    data.to_stata(str(dta_file), write_index=False)
    csv_out = PROJECT_STATA_OUTPUT / "w11_estat_summarize_stata.csv"
    do_template = f'''
clear all
set more off
use "{dta_file}", clear
reghdfe y x1 x2, absorb(entity_id)
estat summarize

* Extract return values for each variable
foreach var in y x1 x2 {{
    summarize `var' if e(sample)
    file open out using "{PROJECT_STATA_OUTPUT}/w11_estat_summarize_`var'.txt", write replace
    file write out (r(N)) " " (r(mean)) " " (r(sd)) " " (r(min)) " " (r(max))
    file close out
}}
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")

    stata_summary = {}
    for var in ["y", "x1", "x2"]:
        txt_file = PROJECT_STATA_OUTPUT / f"w11_estat_summarize_{var}.txt"
        with open(txt_file, "r") as f:
            vals = [float(v) for v in f.read().strip().split()]
        stata_summary[var] = {
            "N": vals[0],
            "mean": vals[1],
            "sd": vals[2],
            "min": vals[3],
            "max": vals[4],
        }
    return stata_summary


def _run_python_estat_summarize(data: pd.DataFrame):
    model = AbsorbingOLS(data, y="y", x=["x1", "x2"], absorb="entity_id", add_constant=True)
    result = model.fit(vce="ols")
    return estat_summarize(result, data, dep_var="y")


class TestW11EstatSummarize:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_summary(self, test_data):
        return _run_python_estat_summarize(test_data)

    @pytest.fixture(scope="class")
    def stata_summary(self, test_data):
        return _run_stata_estat_summarize(test_data)

    def test_fields_exist(self, python_summary, stata_summary):
        for var in ["y", "x1", "x2"]:
            assert var in python_summary, f"{var} missing in Python summary"
            assert var in stata_summary, f"{var} missing in Stata summary"

    def test_n_match(self, python_summary, stata_summary):
        for var in ["y", "x1", "x2"]:
            assert python_summary[var]["N"] == stata_summary[var]["N"], \
                f"{var} N mismatch: {python_summary[var]['N']} vs {stata_summary[var]['N']}"

    def test_mean_match(self, python_summary, stata_summary):
        for var in ["y", "x1", "x2"]:
            assert np.allclose(python_summary[var]["mean"], stata_summary[var]["mean"], rtol=1e-6, atol=1e-10), \
                f"{var} mean mismatch: {python_summary[var]['mean']} vs {stata_summary[var]['mean']}"

    def test_sd_match(self, python_summary, stata_summary):
        for var in ["y", "x1", "x2"]:
            assert np.allclose(python_summary[var]["sd"], stata_summary[var]["sd"], rtol=1e-6, atol=1e-10), \
                f"{var} sd mismatch: {python_summary[var]['sd']} vs {stata_summary[var]['sd']}"

    def test_min_match(self, python_summary, stata_summary):
        for var in ["y", "x1", "x2"]:
            assert np.allclose(python_summary[var]["min"], stata_summary[var]["min"], rtol=1e-6, atol=1e-10), \
                f"{var} min mismatch: {python_summary[var]['min']} vs {stata_summary[var]['min']}"

    def test_max_match(self, python_summary, stata_summary):
        for var in ["y", "x1", "x2"]:
            assert np.allclose(python_summary[var]["max"], stata_summary[var]["max"], rtol=1e-6, atol=1e-10), \
                f"{var} max mismatch: {python_summary[var]['max']} vs {stata_summary[var]['max']}"
