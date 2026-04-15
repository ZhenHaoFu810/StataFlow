"""
Golden test: p0_min_ols_auto - Python vs Stata dual-run comparison.

Tests that Python OLS implementation matches Stata's regress output
at the field level.

Uses log file parsing (same as run_dual_test.py) instead of hand-written
Stata JSON export, which was causing JSONDecodeError.
"""

import re
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from statapy import OLS
from statapy.stata_runner import StataRunner
from statapy.results import ResultSchema

# Project paths - all outputs stay in project directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_STATA_OUTPUT = PROJECT_ROOT / "stata" / "output"
PROJECT_STATA_CASES = PROJECT_ROOT / "stata" / "cases"

# Ensure output directory exists
PROJECT_STATA_OUTPUT.mkdir(parents=True, exist_ok=True)
TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_p0_"))


def _generate_test_data() -> pd.DataFrame:
    """Generate test dataset with known seed."""
    np.random.seed(12345)
    n = 100

    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = 1 + 2 * x1 + 3 * x2 + np.random.normal(0, 1, n)

    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def _parse_stata_log(log_content: str) -> dict:
    """
    Parse Stata log file to extract regression results.
    Uses e() display values for precision.
    """
    result = {}

    # Parse precise e() values
    # Note: Stata displays numbers < 1 as ".9318" not "0.9318"
    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'r2_adj': r'E_R2_A=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
        'f_pvalue': r'E_F_P=([\d.]+)',
        'rss': r'E_RSS=([\d.]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            # Stata shows ".9318" for numbers < 1, add leading zero
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    # Extract coefficients from coefficient table
    coef_pattern = r'^\s+(\w+)\s+\|\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)'
    coefficients = []

    coef_section = False
    for line in log_content.split('\n'):
        if '-------------+----------------------------------------------------------------' in line:
            coef_section = True
            continue
        if coef_section and line.strip() == '':
            coef_section = False
            continue
        if coef_section:
            match = re.match(coef_pattern, line)
            if match:
                name = match.group(1)
                beta = float(match.group(2))
                std_err = float(match.group(3))
                coefficients.append({
                    'name': name,
                    'beta': beta,
                    'std_err': std_err,
                })

    result['coefficients'] = coefficients
    return result


def _run_stata_ols(data: pd.DataFrame) -> dict:
    """Run Stata regress and return parsed results."""
    runner = StataRunner()

    # Save data to a unique temp file to avoid OneDrive/Windows file locking
    dta_file = TEMP_DIR / "p0_golden_test_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    # Create .do file
    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression
regress y x1 x2

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

display "Stata regress completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))

    output_dir = str(PROJECT_STATA_OUTPUT)
    result = runner.run_do_file(do_content, output_dir=output_dir)

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")

    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


def _tolerance_close(a, b, rtol=1e-6, atol=1e-8, name="value"):
    """Check if two values are within tolerance."""
    if a is None or b is None:
        return a == b, f"{name}: Python={a}, Stata={b}"

    diff = abs(a - b)
    rel_diff = diff / (abs(b) + 1e-15)

    passed = diff < atol or rel_diff < rtol
    msg = (
        f"{name}: Python={a:.15f}, Stata={b:.15f}, "
        f"abs_diff={diff:.2e}, rel_diff={rel_diff:.2e}, "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return passed, msg


class TestP0MinOlsAuto:
    """Golden test for p0_min_ols_auto."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python OLS."""
        model = OLS(
            data=test_data,
            y="y",
            x=["x1", "x2"],
            add_constant=True,
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata results via log parsing."""
        return _run_stata_ols(test_data)

    def test_sample_nobs(self, python_result, stata_result):
        """Compare sample size."""
        passed, msg = _tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        """Compare model degrees of freedom."""
        passed, msg = _tolerance_close(
            python_result.fit.df_model, stata_result.get('df_model'), name="df_model"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        """Compare residual degrees of freedom."""
        passed, msg = _tolerance_close(
            python_result.fit.df_resid, stata_result.get('df_resid'), name="df_resid"
        )
        assert passed, msg

    def test_r2(self, python_result, stata_result):
        """Compare R-squared."""
        passed, msg = _tolerance_close(
            python_result.fit.r2, stata_result.get('r2'), name="r2"
        )
        assert passed, msg

    def test_r2_adj(self, python_result, stata_result):
        """Compare Adjusted R-squared."""
        passed, msg = _tolerance_close(
            python_result.fit.r2_adj, stata_result.get('r2_adj'), name="r2_adj"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        """Compare RMSE."""
        passed, msg = _tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        """Compare F-statistic."""
        passed, msg = _tolerance_close(
            python_result.fit.f_stat, stata_result.get('f_stat'), name="f_stat"
        )
        assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        """Compare number of coefficients."""
        assert len(python_result.coefficients) == len(stata_result.get('coefficients', []))

    def test_coefficients_names(self, python_result, stata_result):
        """Compare coefficient names (order matters)."""
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result.get('coefficients', [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        """Compare coefficient estimates."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = _tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        """Compare standard errors."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = _tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg

    def test_covariance_matrix_not_empty(self, python_result, stata_result):
        """Verify covariance matrix is populated."""
        py_cov = python_result.variance.values
        assert len(py_cov) > 0, "Covariance matrix is empty"
        assert len(py_cov[0]) > 0, "Covariance matrix has no columns"
