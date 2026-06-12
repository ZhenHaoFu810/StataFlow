"""
Golden test: w7_reghdfe_2way_cluster - reghdfe with 2-way cluster-robust SE (synthetic).

Tests that Python AbsorbingOLS with absorb=[var1, var2] and vce='cluster'
with cluster=[var1, var2] matches Stata's reghdfe two-way clustering:
- Coefficient estimates
- Two-way cluster-robust standard errors
- Cluster count (minimum of the two dimensions)
- F-statistic (Wald test with cluster df)
- Degrees of freedom
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
from stataflow import AbsorbingOLS


def _generate_test_data() -> pd.DataFrame:
    """Generate balanced panel dataset with known seed."""
    np.random.seed(22222)
    n_entities = 30
    n_periods = 4
    n = n_entities * n_periods

    entity_id = np.repeat(np.arange(n_entities), n_periods)
    time_id = np.tile(np.arange(n_periods), n_entities)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    entity_fe = np.repeat(np.random.normal(0, 2, n_entities), n_periods)
    time_fe = np.tile(np.random.normal(0, 1, n_periods), n_entities)
    error = np.random.normal(0, 1, n)
    y = 1 + 1.5 * x1 - 2 * x2 + entity_fe + time_fe + error

    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "entity_id": entity_id,
        "time_id": time_id,
    })


def _run_stata_reghdfe_2way_cluster(data: pd.DataFrame) -> dict:
    """Run Stata reghdfe with 2 FEs and 2-way cluster-robust SE."""
    dta_file = PROJECT_STATA_CASES / "w7_reghdfe_2way_cluster_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

// Read data
use "{dta_file}", clear

// Run reghdfe with 2 FEs and 2-way clustering
reghdfe y x1 x2, absorb(entity_id time_id) vce(cluster entity_id time_id)

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_N_CLUST1=" e(N_clust1)
display "E_N_CLUST2=" e(N_clust2)

// Output precise coefficients and standard errors
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "B__CONS=" _b[_cons]

display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "SE__CONS=" _se[_cons]

display "Stata reghdfe 2way cluster completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return parse_stata_log_with_precise_coefs(result.output_content)


class TestW7Reghdfe2WayCluster:
    """Golden test for w7_reghdfe_2way_cluster."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python AbsorbingOLS in reghdfe mode with 2-way cluster."""
        model = AbsorbingOLS(
            data=test_data,
            y="y",
            x=["x1", "x2"],
            absorb=["entity_id", "time_id"],
            add_constant=True,
        )
        return model.fit(vce="cluster", cluster=["entity_id", "time_id"])

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata reghdfe + 2-way cluster results."""
        return _run_stata_reghdfe_2way_cluster(test_data)

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get('df_model'), name="df_model"
        )
        assert passed, msg

    def test_df_a(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_a, stata_result.get('df_a'), name="df_a"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get('df_resid'), name="df_resid"
        )
        assert passed, msg

    def test_r2(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get('r2'), name="r2"
        )
        assert passed, msg

    def test_r2_adj(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.r2_adj, stata_result.get('r2_adj'), name="r2_adj"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get('f_stat'), name="f_stat"
        )
        assert passed, msg

    def test_cluster_count(self, python_result, stata_result):
        py_count = python_result.diagnostics.cluster_count
        st_count1 = stata_result.get('n_clust1')
        st_count2 = stata_result.get('n_clust2')
        # Python reports minimum cluster count for df; Stata reports both
        if st_count1 is not None and st_count2 is not None:
            st_min = min(st_count1, st_count2)
            passed, msg = tolerance_close(py_count, st_min, name="cluster_count")
            assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        assert len(python_result.coefficients) == len(stata_result.get('coefficients', []))

    def test_coefficients_names(self, python_result, stata_result):
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result.get('coefficients', [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_slope_std_err_2way(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            if py_coef.name == "_cons":
                continue
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"2way_se[{py_coef.name}]"
            )
            assert passed, msg

    def test_constant_std_err_2way(self, python_result, stata_result):
        py_coef = next(c for c in python_result.coefficients if c.name == "_cons")
        st_coef = next(c for c in stata_result.get('coefficients', []) if c['name'] == "_cons")
        passed, msg = tolerance_close(
            py_coef.std_err, st_coef['std_err'], name="2way_se[_cons]"
        )
        assert passed, msg

    def test_vcetype(self, python_result):
        assert python_result.model.vcetype == "cluster"

    def test_cluster_var_list(self, python_result):
        assert python_result.model.cluster_var == ["entity_id", "time_id"]

    def test_absorb_vars(self, python_result):
        assert python_result.model.absorb_vars == ["entity_id", "time_id"]
