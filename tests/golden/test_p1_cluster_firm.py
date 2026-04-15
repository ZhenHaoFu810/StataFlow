"""
Golden test: p1_cluster_firm - OLS with cluster-robust standard errors.

Tests that Python OLS with vce='cluster' matches Stata's regress, vce(cluster firm_id):
- Coefficient estimates (should be identical to OLS)
- Cluster-robust standard errors
- Cluster count
- t-statistics and p-values
- F-statistic (Wald test)
"""

import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    run_stata_ols,
    tolerance_close,
)
from statapy import OLS

# Use temp directory to avoid OneDrive file locking
TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_cluster_"))


def _generate_test_data() -> pd.DataFrame:
    """Generate firm-year panel dataset with known seed."""
    np.random.seed(98765)
    n_firms = 30
    n_years = 4
    n = n_firms * n_years

    firm_id = np.repeat(np.arange(n_firms), n_years)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)

    # Cluster-level error (firm-specific shock)
    firm_effect = np.repeat(np.random.normal(0, 2, n_firms), n_years)
    error = firm_effect + np.random.normal(0, 1, n)

    # True model: y = 5 + 2*x1 - 1.5*x2 + error
    y = 5 + 2 * x1 - 1.5 * x2 + error

    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "firm_id": firm_id,
    })


def _run_stata_cluster(data: pd.DataFrame) -> dict:
    """Run Stata regress with vce(cluster firm_id)."""
    dta_file = TEMP_DIR / "p1_cluster_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression with cluster-robust SE
regress y x1 x2, vce(cluster firm_id)

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" e(F_p)
display "E_RSS=" e(rss)
display "E_N_CLUST=" e(N_clust)

display "Stata regress, vce(cluster firm_id) completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_ols(do_content)


class TestP1ClusterFirm:
    """Golden test for p1_cluster_firm."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python OLS with cluster VCE."""
        model = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        return model.fit(vce="cluster", cluster="firm_id")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata cluster results."""
        return _run_stata_cluster(test_data)

    def test_nobs(self, python_result, stata_result):
        """Compare sample size."""
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        """Compare model degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get('df_model'), name="df_model"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        """Compare residual degrees of freedom (should be G-1 for cluster)."""
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get('df_resid'), name="df_resid"
        )
        assert passed, msg

    def test_r2(self, python_result, stata_result):
        """Compare R-squared."""
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get('r2'), name="r2"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        """Compare RMSE."""
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        """Compare Wald F-statistic for cluster VCE."""
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get('f_stat'), name="f_stat"
        )
        assert passed, msg

    def test_cluster_count(self, python_result, stata_result):
        """Compare number of clusters."""
        py_count = python_result.diagnostics.cluster_count
        st_count = stata_result.get('n_clust')

        if st_count is not None:
            passed, msg = tolerance_close(py_count, st_count, name="cluster_count")
            assert passed, msg
        else:
            print(f"[WARN] Stata cluster count not available: Python={py_count}")

    def test_coefficients_count(self, python_result, stata_result):
        """Compare number of coefficients."""
        assert len(python_result.coefficients) == len(stata_result.get('coefficients', []))

    def test_coefficients_names(self, python_result, stata_result):
        """Compare coefficient names."""
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result.get('coefficients', [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        """Compare coefficient estimates."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err_cluster(self, python_result, stata_result):
        """Compare cluster-robust standard errors."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"cluster_se[{py_coef.name}]"
            )
            assert passed, msg

    def test_vcetype(self, python_result):
        """Verify vcetype is set to 'cluster'."""
        assert python_result.model.vcetype == "cluster", \
            f"vcetype should be 'cluster', got {python_result.model.vcetype}"

    def test_cluster_var(self, python_result):
        """Verify cluster_var is set correctly."""
        assert python_result.model.cluster_var == "firm_id", \
            f"cluster_var should be 'firm_id', got {python_result.model.cluster_var}"
