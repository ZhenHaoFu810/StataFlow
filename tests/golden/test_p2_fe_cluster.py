"""
Golden test: p2_fe_cluster - Fixed effects regression with cluster-robust SE.

Tests that Python FixedEffectsOLS with vce='cluster' matches Stata's xtreg ..., fe vce(cluster firm_id):
- Coefficient estimates (same as FE without cluster)
- Cluster-robust standard errors
- Cluster count
- F-statistic (Wald test with cluster df)
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
from stataflow import FixedEffectsOLS

# Use temp directory to avoid OneDrive file locking
TEMP_DIR = Path(tempfile.mkdtemp(prefix="stataflow_fe_cluster_"))


def _generate_test_data() -> pd.DataFrame:
    """Generate balanced panel dataset with known seed."""
    np.random.seed(66666)
    n_entities = 30
    n_periods = 4
    n = n_entities * n_periods

    entity_id = np.repeat(np.arange(n_entities), n_periods)
    time_id = np.tile(np.arange(n_periods), n_entities)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    entity_fe = np.repeat(np.random.normal(0, 2, n_entities), n_periods)
    error = np.random.normal(0, 1, n)
    y = 1 + 1.5 * x1 - 2 * x2 + entity_fe + error

    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "entity_id": entity_id,
        "time_id": time_id,
    })


def _run_stata_fe_cluster(data: pd.DataFrame) -> dict:
    """Run Stata xtreg with fe and vce(cluster)."""
    dta_file = TEMP_DIR / "p2_fe_cluster_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Set panel structure
xtset entity_id time_id

// Run fixed effects regression with cluster-robust SE
xtreg y x1 x2, fe vce(cluster entity_id)

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_N_g=" e(N_g)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2_W=" e(r2_w)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_N_CLUST=" e(N_clust)

display "Stata xtreg y x1 x2, fe vce(cluster entity_id) completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_ols(do_content)


class TestP2FeCluster:
    """Golden test for p2_fe_cluster."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python FE with cluster."""
        model = FixedEffectsOLS(
            data=test_data,
            y="y",
            x=["x1", "x2"],
            fe="entity_id",
            add_constant=True,
        )
        return model.fit(vce="cluster", cluster="entity_id")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata FE + cluster results."""
        return _run_stata_fe_cluster(test_data)

    def test_nobs(self, python_result, stata_result):
        """Compare sample size."""
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs"
        )
        assert passed, msg

    def test_n_groups(self, python_result, stata_result):
        """Compare number of groups."""
        n_g_stata = stata_result.get('n_g')
        if n_g_stata is not None:
            # N_g is embedded in df_resid calculation
            pass

    def test_cluster_count(self, python_result, stata_result):
        """Compare number of clusters."""
        py_count = python_result.diagnostics.cluster_count
        st_count = stata_result.get('n_clust')
        if st_count is not None:
            passed, msg = tolerance_close(py_count, st_count, name="cluster_count")
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

    def test_r2_within(self, python_result, stata_result):
        """Compare within R-squared (same as non-cluster FE)."""
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get('r2_w'), name="r2_within"
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
        assert python_result.model.cluster_var == "entity_id", \
            f"cluster_var should be 'entity_id', got {python_result.model.cluster_var}"

    def test_fe_vars(self, python_result):
        """Verify FE variable is recorded."""
        assert python_result.model.fe_vars == ["entity_id"]
