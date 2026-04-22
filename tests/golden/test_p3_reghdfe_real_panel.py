"""
Golden test: p3_reghdfe_real_panel - reghdfe on real panel data (wagepan).

Tests that Python AbsorbingOLS matches Stata's reghdfe on Wooldridge wagepan:
- Coefficient estimates
- Cluster-robust standard errors
- R-squared, Adjusted R-squared
- F-statistic, RMSE
- Degrees of freedom (including df_a with cluster nesting)
- Cluster count
"""

import pytest
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    tolerance_close,
    parse_stata_log_with_precise_coefs,
)
from stataflow import AbsorbingOLS
from stataflow.stata_runner import StataRunner

PROJECT_ROOT = Path(__file__).parent.parent.parent
WAGEPAN_CSV = PROJECT_ROOT / "research" / "data" / "public" / "panel" / "wooldridge" / "wagepan.csv"


def _load_test_data() -> pd.DataFrame:
    """Load wagepan dataset."""
    return pd.read_csv(str(WAGEPAN_CSV))


def _run_stata_reghdfe() -> dict:
    """Run Stata reghdfe on wagepan with 2 FEs and cluster."""
    do_template = f'''
clear all
set more off

// Read data
import delimited "{WAGEPAN_CSV}", clear

// Run reghdfe with 2 FEs and cluster
reghdfe lwage educ exper expersq union, absorb(nr year) vce(cluster nr)

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_N_CLUST=" e(N_clust)

// Output precise coefficients and standard errors
display "B_EDUC=" _b[educ]
display "B_EXPER=" _b[exper]
display "B_EXPERSQ=" _b[expersq]
display "B_UNION=" _b[union]
display "B__CONS=" _b[_cons]

display "SE_EDUC=" _se[educ]
display "SE_EXPER=" _se[exper]
display "SE_EXPERSQ=" _se[expersq]
display "SE_UNION=" _se[union]
display "SE__CONS=" _se[_cons]

display "Stata reghdfe on wagepan completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return parse_stata_log_with_precise_coefs(
        result.output_content,
        coef_names=['educ', 'exper', 'expersq', 'union', '_cons']
    )


class TestP3ReghdfeRealPanel:
    """Golden test for p3_reghdfe_real_panel (wagepan)."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Load test data once per class."""
        return _load_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python AbsorbingOLS in reghdfe mode with cluster."""
        model = AbsorbingOLS(
            data=test_data,
            y="lwage",
            x=["educ", "exper", "expersq", "union"],
            absorb=["nr", "year"],
            add_constant=True,
        )
        return model.fit(vce="cluster", cluster="nr")

    @pytest.fixture(scope="class")
    def stata_result(self):
        """Get Stata reghdfe results."""
        return _run_stata_reghdfe()

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
        st_count = stata_result.get('n_clust')
        if st_count is not None:
            passed, msg = tolerance_close(py_count, st_count, name="cluster_count")
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

    def test_coefficients_std_err_cluster(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"cluster_se[{py_coef.name}]"
            )
            assert passed, msg

    def test_vcetype(self, python_result):
        assert python_result.model.vcetype == "cluster"

    def test_cluster_var(self, python_result):
        assert python_result.model.cluster_var == "nr"

    def test_absorb_vars(self, python_result):
        assert python_result.model.absorb_vars == ["nr", "year"]
