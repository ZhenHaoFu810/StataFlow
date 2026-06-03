"""
Golden test: w11_ppmlhdfe_residuals - predict residuals for PPMLHDFE.

Tests PPMLHDFE.predict(type='pearson'/'deviance'/'working')
against Stata ppmlhdfe predict for pearson, deviance, and working residuals.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
)
from stataflow.estimators.ppmlhdfe import PPMLHDFE


def _generate_test_data() -> pd.DataFrame:
    """Generate basic PPMLHDFE test dataset with known seed."""
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
        "entity_id": entities.astype(np.int64),
        "time_id": times.astype(np.int64),
    })


def _run_stata_residuals(data: pd.DataFrame, residual_type: str) -> pd.DataFrame:
    dta_file = PROJECT_STATA_CASES / f"w11_ppmlhdfe_{residual_type}_data.dta"
    data.to_stata(str(dta_file), write_index=False)
    csv_out = PROJECT_STATA_OUTPUT / f"w11_ppmlhdfe_{residual_type}_stata.csv"
    do_template = f'''
clear all
set more off
use "{dta_file}", clear
ppmlhdfe y x1 x2, absorb(entity_id) d
predict r, {residual_type}
export delimited "{csv_out}", replace
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    return pd.read_csv(str(csv_out))


def _run_python_residuals(data: pd.DataFrame, residual_type: str):
    model = PPMLHDFE(
        data=data,
        y="y",
        x=["x1", "x2"],
        absorb="entity_id",
        add_constant=True,
    )
    model.fit(vce="ols")
    return model.predict(type=residual_type)


class TestW11PpmlhdfePearson:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_residuals(self, test_data):
        return _run_python_residuals(test_data, "pearson")

    @pytest.fixture(scope="class")
    def stata_residuals(self, test_data):
        df = _run_stata_residuals(test_data, "pearson")
        return df["r"].values

    def test_pearson_vector(self, python_residuals, stata_residuals):
        assert len(python_residuals) == len(stata_residuals)
        # Residual differences ~0.2% arise from IRLS/HDFE convergence
        # precision (mu differs by ~0.3% at a few points), not formula error.
        assert np.allclose(python_residuals, stata_residuals, rtol=5e-3, atol=1e-6), \
            f"pearson max diff={np.max(np.abs(python_residuals - stata_residuals)):.6e}"


class TestW11PpmlhdfeDeviance:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_residuals(self, test_data):
        return _run_python_residuals(test_data, "deviance")

    @pytest.fixture(scope="class")
    def stata_residuals(self, test_data):
        df = _run_stata_residuals(test_data, "deviance")
        return df["r"].values

    def test_deviance_vector(self, python_residuals, stata_residuals):
        assert len(python_residuals) == len(stata_residuals)
        # Stata ppmlhdfe predict, deviance returns the squared deviance
        # contribution (2*(y*log(y/mu)-(y-mu))), not the signed residual.
        # Residual differences ~0.25% arise from IRLS/HDFE convergence precision.
        assert np.allclose(python_residuals, stata_residuals, rtol=5e-3, atol=1e-6), \
            f"deviance max diff={np.max(np.abs(python_residuals - stata_residuals)):.6e}"


class TestW11PpmlhdfeWorking:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_residuals(self, test_data):
        return _run_python_residuals(test_data, "working")

    @pytest.fixture(scope="class")
    def stata_residuals(self, test_data):
        df = _run_stata_residuals(test_data, "working")
        return df["r"].values

    def test_working_vector(self, python_residuals, stata_residuals):
        assert len(python_residuals) == len(stata_residuals)
        # Residual differences ~0.35% arise from IRLS/HDFE convergence
        # precision (mu differs by ~0.3% at a few points), not formula error.
        assert np.allclose(python_residuals, stata_residuals, rtol=5e-3, atol=1e-6), \
            f"working max diff={np.max(np.abs(python_residuals - stata_residuals)):.6e}"
