"""
Golden test: w3_ppmlhdfe_cluster - PPMLHDFE with cluster-robust VCE.

Tests ppmlhdfe with single FE and cluster-robust standard errors,
verifying:
- Coefficient estimates
- Cluster-robust standard errors
- Cluster count
- Degrees of freedom (df_model, df_a, df_resid)
"""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow import PPMLHDFE
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    tolerance_close,
)


def _generate_test_data() -> pd.DataFrame:
    """Generate PPMLHDFE cluster test dataset with known seed."""
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
        "entity_id": entities,
        "time_id": times,
    })


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata ppmlhdfe log output."""
    result = {}

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_a': r'E_DF_A=([\d]+)',
        'clusters': r'E_CLUSTERS=([\d]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str == '.' or val_str == '-.':
                continue
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    coefficients = []
    b_matches = {k.lower(): v for k, v in re.findall(r'B_(\w+)=(-?[\d.]+)', log_content)}
    se_matches = {k.lower(): v for k, v in re.findall(r'SE_(\w+)=(-?[\d.]+)', log_content)}

    for name in ['x1', 'x2', '_cons']:
        if name in b_matches and name in se_matches:
            coefficients.append({
                'name': name,
                'beta': float(b_matches[name]),
                'std_err': float(se_matches[name]),
            })

    result['coefficients'] = coefficients
    return result


def _run_stata_ppmlhdfe(data: pd.DataFrame) -> dict:
    """Run Stata ppmlhdfe for cluster test."""
    dta_file = PROJECT_STATA_CASES / "w3_ppmlhdfe_cluster_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

ppmlhdfe y x1 x2, absorb(entity_id) vce(cluster entity_id)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_A=" e(df_a)
display "E_CLUSTERS=" e(N_clust)

display "B_x1=" _b[x1]
display "SE_x1=" _se[x1]
display "B_x2=" _b[x2]
display "SE_x2=" _se[x2]
display "B__cons=" _b[_cons]
display "SE__cons=" _se[_cons]

display "Stata ppmlhdfe cluster completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestW3PpmlhdfeCluster:
    """Golden test for w3_ppmlhdfe_cluster."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = PPMLHDFE(
            data=test_data,
            y="y",
            x=["x1", "x2"],
            absorb=["entity_id"],
            add_constant=True,
        )
        return model.fit(vce="cluster", cluster="entity_id")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_ppmlhdfe(test_data)

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

    def test_cluster_count(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.diagnostics.cluster_count,
            stata_result.get("clusters"),
            name="cluster_count",
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

    def test_absorb_vars(self, python_result):
        assert python_result.model.absorb_vars == ["entity_id"]
