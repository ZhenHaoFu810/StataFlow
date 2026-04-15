"""
Golden test: w2_ivreghdfe_cluster - IV with two FEs and cluster-robust VCE.

Tests ivreghdfe-style 2SLS with two absorb variables and cluster VCE, verifying:
- Coefficient estimates
- Cluster-robust standard errors
- R-squared, Adjusted R-squared
- F-statistic, RMSE
- Degrees of freedom including df_a with nested cluster correction
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    run_stata_ivregress,
    run_python_ivabsorb,
    tolerance_close,
)


def _generate_test_data() -> pd.DataFrame:
    """Generate panel IV test dataset with known seed."""
    np.random.seed(54321)
    n_entities = 30
    n_per_entity = 6
    n = n_entities * n_per_entity

    entity_id = np.repeat(np.arange(n_entities), n_per_entity)
    time_id = np.tile(np.arange(n_per_entity), n_entities)

    z1 = np.random.normal(0, 1, n)
    z2 = np.random.normal(0, 1, n)
    x1 = np.random.normal(2, 1, n)

    # Entity and time FE
    alpha_e = np.repeat(np.random.normal(0, 2, n_entities), n_per_entity)
    gamma_t = np.tile(np.random.normal(0, 1, n_per_entity), n_entities)

    v = np.random.normal(0, 0.8, n)
    x2 = alpha_e + gamma_t + 1.5 * z1 - 0.8 * z2 + 0.3 * x1 + v

    u = np.random.normal(0, 0.8, n) + 0.4 * v
    y = alpha_e + gamma_t + 2 * x1 + 1.5 * x2 + u

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


def _run_stata_ivreghdfe_cluster(data: pd.DataFrame) -> dict:
    """Run Stata ivreghdfe with two FEs and cluster VCE."""
    dta_file = PROJECT_STATA_CASES / "w2_ivreghdfe_cluster_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run ivreghdfe with two FEs and cluster
ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id time_id) vce(cluster entity_id) keepsingletons

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_N_CLUST=" e(N_clust)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" e(F_p)

// Output precise coefficients
display "B_x1=" _b[x1]
display "SE_x1=" _se[x1]
display "B_x2=" _b[x2]
display "SE_x2=" _se[x2]
display "B__cons=" _b[_cons]
display "SE__cons=" _se[_cons]

display "Stata ivreghdfe cluster completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_ivregress(do_content, coef_names=["x2", "x1", "_cons"])


class TestW2IvreghdfeCluster:
    """Golden test for w2_ivreghdfe_cluster."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return run_python_ivabsorb(
            test_data,
            y="y",
            x_exog=["x1"],
            x_endog=["x2"],
            instruments=["z1", "z2"],
            absorb=["entity_id", "time_id"],
            add_constant=True,
            vce="cluster",
            cluster="entity_id",
        )

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_ivreghdfe_cluster(test_data)

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get("nobs"), name="nobs"
        )
        assert passed, msg

    def test_n_clust(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.diagnostics.cluster_count,
            stata_result.get("n_clust"),
            name="n_clust",
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get("df_model"), name="df_model"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get("df_resid"), name="df_resid"
        )
        assert passed, msg

    def test_df_a(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_a, stata_result.get("df_a"), name="df_a"
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
        assert len(python_result.coefficients) == len(
            stata_result.get("coefficients", [])
        )

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
