"""
Golden test: w10_gmm2s_overid - GMM2S with overidentification.

Tests ivreghdfe-style GMM2S estimator with one absorbed FE,
verifying coefficients, SEs, t-stats, and Hansen J statistic.
"""

import pytest
import numpy as np
import pandas as pd
import re
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
    tolerance_close,
)
from stataflow.estimators.iv import IVAbsorbingOLS


def _generate_test_data() -> pd.DataFrame:
    """Generate panel IV test dataset with known seed."""
    np.random.seed(54321)
    n_entities = 40
    n_per_entity = 5
    n = n_entities * n_per_entity

    entity_id = np.repeat(np.arange(n_entities), n_per_entity)
    time_id = np.tile(np.arange(n_per_entity), n_entities)

    z1 = np.random.normal(0, 1, n)
    z2 = np.random.normal(0, 1, n)
    x1 = np.random.normal(2, 1, n)

    alpha_e = np.repeat(np.random.normal(0, 2, n_entities), n_per_entity)
    v = np.random.normal(0, 0.8, n)
    x2 = alpha_e + 1.5 * z1 - 0.8 * z2 + 0.3 * x1 + v

    u = np.random.normal(0, 0.8, n) + 0.4 * v
    y = alpha_e + 2 * x1 + 1.5 * x2 + u

    return pd.DataFrame(
        {
            "y": y,
            "x1": x1,
            "x2": x2,
            "z1": z1,
            "z2": z2,
            "entity_id": entity_id,
            "time_id": time_id,
        }
    )


def _run_stata(data: pd.DataFrame) -> dict:
    """Run Stata ivreghdfe with gmm2s."""
    dta_file = PROJECT_STATA_CASES / "w10_gmm2s_overid_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) keepsingletons gmm2s

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_J=" e(j)
display "E_JDF=" e(jdf)

matrix b = e(b)
matrix V = e(V)
local names : colfullnames(b)
forvalues i = 1/`=colsof(b)' {{
    local name : word `i' of `names'
    display "B_`name'=" b[1,`i']
    display "SE_`name'=" sqrt(V[`i',`i'])
}}
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")

    log_content = result.output_content or ""
    stata_result = {}

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
        'hansen_j': r'E_J=([\d.]+)',
        'hansen_j_df': r'E_JDF=([\d]+)',
    }
    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            stata_result[key] = float(val_str)

    coefficients = []
    for match in re.finditer(r'B_(\w+)=(-?[\d.eE+-]+)', log_content):
        name = match.group(1)
        beta = float(match.group(2))
        se_match = re.search(rf'SE_{name}=(-?[\d.eE+-]+)', log_content)
        if se_match:
            coefficients.append({
                'name': name,
                'beta': beta,
                'std_err': float(se_match.group(1)),
            })
    stata_result['coefficients'] = coefficients

    return stata_result


def _run_python(data: pd.DataFrame):
    """Run Python IVAbsorbingOLS with gmm2s."""
    model = IVAbsorbingOLS(
        data=data,
        y="y",
        x_exog=["x1"],
        x_endog=["x2"],
        instruments=["z1", "z2"],
        absorb=["entity_id"],
        add_constant=True,
    )
    return model.fit(vce="ols", estimator="gmm2s")


class TestW10Gmm2sOverid:
    """Golden test for w10_gmm2s_overid."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return _run_python(test_data)

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata(test_data)

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get("nobs"), name="nobs"
        )
        assert passed, msg

    def test_coefficients_beta(self, python_result, stata_result):
        py_coefs = {c.name: c.beta for c in python_result.coefficients}
        st_coefs = {c['name']: c['beta'] for c in stata_result.get('coefficients', [])}
        assert set(py_coefs.keys()) == set(st_coefs.keys()), f"Coef name mismatch: Python={set(py_coefs.keys())}, Stata={set(st_coefs.keys())}"
        for name in py_coefs:
            passed, msg = tolerance_close(py_coefs[name], st_coefs[name], name=f"beta_{name}")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        py_coefs = {c.name: c.std_err for c in python_result.coefficients}
        st_coefs = {c['name']: c['std_err'] for c in stata_result.get('coefficients', [])}
        for name in py_coefs:
            passed, msg = tolerance_close(py_coefs[name], st_coefs[name], name=f"se_{name}")
            assert passed, msg

    def test_hansen_j(self, python_result, stata_result):
        py_j = getattr(python_result, 'hansen_j', None)
        st_j = stata_result.get('hansen_j')
        assert py_j is not None, "Python Hansen J not computed"
        assert st_j is not None, "Stata Hansen J not parsed"
        passed, msg = tolerance_close(py_j, st_j, name="hansen_j", rtol=1e-4)
        assert passed, msg

    def test_hansen_j_df(self, python_result, stata_result):
        py_jdf = getattr(python_result, 'hansen_j_df', None)
        st_jdf = stata_result.get('hansen_j_df')
        assert py_jdf is not None
        assert st_jdf is not None
        assert py_jdf == st_jdf, f"Hansen J df mismatch: Python={py_jdf}, Stata={st_jdf}"

    def test_r2(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get("r2"), name="r2"
        )
        assert passed, msg
