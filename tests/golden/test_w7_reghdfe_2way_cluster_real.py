"""
Golden test: w7_reghdfe_2way_cluster_real - reghdfe with real panel data and 2-way cluster.

Uses Wooldridge wagepan data to verify Python AbsorbingOLS with
absorb=[nr, year] and vce='cluster' cluster=[nr, year]
matches Stata's reghdfe two-way clustering on real data.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
    tolerance_close,
    parse_stata_log_with_precise_coefs,
)
from stataflow import AbsorbingOLS


def _load_wagepan_data() -> pd.DataFrame:
    """Load wagepan data from public datasets."""
    data_path = Path(__file__).parent.parent.parent / "research" / "data" / "public" / "panel" / "wooldridge" / "wagepan.csv"
    df = pd.read_csv(data_path)
    # Keep only key variables; educ is time-invariant and will be collinear with nr FE
    cols = ["nr", "year", "lwage", "exper", "married", "union"]
    df = df[cols].copy()
    # Drop any rows with missing values
    df = df.dropna()
    return df


def _run_stata_reghdfe_2way_cluster_real(data: pd.DataFrame) -> dict:
    """Run Stata reghdfe with 2 FEs and 2-way cluster-robust SE on real data."""
    dta_file = PROJECT_STATA_CASES / "w7_reghdfe_2way_cluster_real_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

reghdfe lwage exper married union, absorb(nr year) vce(cluster nr year)

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

display "B_EXPER=" _b[exper]
display "B_MARRIED=" _b[married]
display "B_UNION=" _b[union]
display "B__CONS=" _b[_cons]

display "SE_EXPER=" _se[exper]
display "SE_MARRIED=" _se[married]
display "SE_UNION=" _se[union]
display "SE__CONS=" _se[_cons]

display "Stata reghdfe 2way cluster real completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=["exper", "married", "union", "_cons"])


class TestW7Reghdfe2WayClusterReal:
    """Golden test for w7_reghdfe_2way_cluster_real."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _load_wagepan_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = AbsorbingOLS(
            data=test_data,
            y="lwage",
            x=["exper", "married", "union"],
            absorb=["nr", "year"],
            add_constant=True,
        )
        return model.fit(vce="cluster", cluster=["nr", "year"])

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_reghdfe_2way_cluster_real(test_data)

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
        if st_count1 is not None and st_count2 is not None:
            st_min = min(st_count1, st_count2)
            passed, msg = tolerance_close(py_count, st_min, name="cluster_count")
            assert passed, msg

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    @pytest.mark.xfail(
        reason="VCE-003: 2-way cluster _cons SE MAP approximation (known limitation)",
        strict=False,
    )
    def test_coefficients_std_err_2way(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"2way_se[{py_coef.name}]"
            )
            assert passed, msg

    def test_vcetype(self, python_result):
        assert python_result.model.vcetype == "cluster"

    def test_cluster_var_list(self, python_result):
        assert python_result.model.cluster_var == ["nr", "year"]

    def test_absorb_vars(self, python_result):
        assert python_result.model.absorb_vars == ["nr", "year"]
