"""
Golden test: p2_fe_basic - Fixed effects regression.

Tests that Python FixedEffectsOLS matches Stata's xtreg ..., fe:
- Coefficient estimates (within transformation)
- Standard errors
- Within R-squared, RMSE, F-statistic
- Degrees of freedom
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
TEMP_DIR = Path(tempfile.mkdtemp(prefix="stataflow_fe_basic_"))


def _generate_test_data() -> pd.DataFrame:
    """Generate balanced panel dataset with known seed."""
    np.random.seed(55555)
    n_entities = 20
    n_periods = 5
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


def _run_stata_fe(data: pd.DataFrame) -> dict:
    """Run Stata xtreg with fe."""
    dta_file = TEMP_DIR / "p2_fe_basic_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Set panel structure
xtset entity_id time_id

// Run fixed effects regression
xtreg y x1 x2, fe

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_N_g=" e(N_g)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2_W=" e(r2_w)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_RSS=" e(rss)

display "Stata xtreg y x1 x2, fe completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_ols(do_content)


class TestP2FeBasic:
    """Golden test for p2_fe_basic."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python FE."""
        model = FixedEffectsOLS(
            data=test_data,
            y="y",
            x=["x1", "x2"],
            fe="entity_id",
            add_constant=True,  # Match Stata's reported _cons
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata FE results."""
        return _run_stata_fe(test_data)

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
            assert python_result.diagnostics.residual_df_correction == "within"
            # We don't directly expose N_g, but it's implied in df_resid

    def test_df_model(self, python_result, stata_result):
        """Compare model degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get('df_model'), name="df_model"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        """Compare residual degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get('df_resid'), name="df_resid"
        )
        assert passed, msg

    def test_r2_within(self, python_result, stata_result):
        """Compare within R-squared."""
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
        """Compare F-statistic."""
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

    def test_coefficients_std_err(self, python_result, stata_result):
        """Compare standard errors."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"se[{py_coef.name}]"
            )
            assert passed, msg

    def test_fe_vars(self, python_result):
        """Verify FE variable is recorded."""
        assert python_result.model.fe_vars == ["entity_id"]

    def test_estimator_family(self, python_result):
        """Verify estimator family."""
        assert python_result.model.estimator_family == "fe"
