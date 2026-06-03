"""
Golden test: w10_weakiv_test - Weak instrument diagnostics with synthetic data.

Tests IVAbsorbingOLS weakiv statistics against Stata ivreghdfe for:
- OLS VCE: Anderson canon. corr. LM + Cragg-Donald Wald F
- Robust VCE: Kleibergen-Paap rk LM + Kleibergen-Paap rk Wald F
- Cluster VCE: Kleibergen-Paap rk LM (cluster) + Kleibergen-Paap rk Wald F (cluster)
- Stock-Yogo critical values (all VCE types)

Data generated in Python and passed to Stata via .dta to ensure identical samples.
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
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        'entity_id': (np.arange(n) % 20).astype(np.int64),
        'z1': np.random.normal(size=n),
        'z2': np.random.normal(size=n),
        'x1': np.random.normal(size=n),
        'v': np.random.normal(size=n),
    })
    df['x2'] = 0.5 * df['z1'] + 0.3 * df['z2'] + 0.2 * df['x1'] + df['v']
    df['u'] = np.random.normal(size=n) + 0.3 * df['v']
    df['y'] = 1 + 2 * df['x1'] + 1.5 * df['x2'] + df['u']
    return df


def _run_stata_weakiv(data: pd.DataFrame, vce: str) -> dict:
    """Run Stata ivreghdfe and extract weakiv statistics."""
    dta_file = PROJECT_STATA_CASES / "w10_weakiv_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    vce_clause = f"vce({vce})" if vce != "ols" else ""
    do_template = f'''
clear all
set more off

use "{dta_file}", clear

ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) keepsingletons {vce_clause}

display "IDSTAT=" e(idstat)
display "IDDF=" e(iddf)
display "IDP=" e(idp)
display "WIDSTAT=" e(widstat)
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")

    log_content = result.output_content or ""
    stata_result = {}
    patterns = {
        'idstat': r'IDSTAT=(-?[\d.eE+-]+)',
        'iddf': r'IDDF=(-?[\d.eE+-]+)',
        'idp': r'IDP=(-?[\d.eE+-]+)',
        'widstat': r'WIDSTAT=(-?[\d.eE+-]+)',
        'sy_10pct': r'SY10=(-?[\d.eE+-]+)',
        'sy_15pct': r'SY15=(-?[\d.eE+-]+)',
        'sy_20pct': r'SY20=(-?[\d.eE+-]+)',
        'sy_25pct': r'SY25=(-?[\d.eE+-]+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            try:
                stata_result[key] = float(val_str)
            except ValueError:
                pass

    # Parse Stock-Yogo critical values from printed table
    sy_patterns = {
        'sy_10pct': r'10% maximal IV size\s+([\d.]+)',
        'sy_15pct': r'15% maximal IV size\s+([\d.]+)',
        'sy_20pct': r'20% maximal IV size\s+([\d.]+)',
        'sy_25pct': r'25% maximal IV size\s+([\d.]+)',
    }
    for key, pattern in sy_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            stata_result[key] = float(match.group(1))

    return stata_result


def _run_python_weakiv(data: pd.DataFrame, vce: str, cluster: str | None = None):
    """Run Python IVAbsorbingOLS and return result."""
    model = IVAbsorbingOLS(
        data=data,
        y="y",
        x_exog=["x1"],
        x_endog=["x2"],
        instruments=["z1", "z2"],
        absorb="entity_id",
        add_constant=True,
    )
    return model.fit(vce=vce, cluster=cluster, estimator="2sls")


class TestW10WeakivOLS:
    """Golden test for weakiv under OLS VCE."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return _run_python_weakiv(test_data, vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_weakiv(test_data, vce="ols")

    def test_idstat(self, python_result, stata_result):
        st = stata_result.get("idstat")
        assert st is not None, "Stata idstat not parsed"
        passed, msg = tolerance_close(python_result.idstat, st, name="idstat", rtol=1e-4)
        assert passed, msg

    def test_widstat(self, python_result, stata_result):
        st = stata_result.get("widstat")
        assert st is not None, "Stata widstat not parsed"
        passed, msg = tolerance_close(python_result.widstat, st, name="widstat", rtol=1e-4)
        assert passed, msg

    def test_iddf(self, python_result, stata_result):
        assert python_result.iddf == int(stata_result.get("iddf", -1))

    def test_idp(self, python_result, stata_result):
        st = stata_result.get("idp")
        assert st is not None
        passed, msg = tolerance_close(python_result.idp, st, name="idp", rtol=1e-4)
        assert passed, msg

    def test_sy_critical_values(self, python_result, stata_result):
        for key in ["sy_10pct", "sy_15pct", "sy_20pct", "sy_25pct"]:
            st = stata_result.get(key)
            assert st is not None, f"Stata {key} not parsed"
            py = getattr(python_result, key)
            passed, msg = tolerance_close(py, st, name=key, rtol=1e-4)
            assert passed, msg


class TestW10WeakivRobust:
    """Golden test for weakiv under robust VCE."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return _run_python_weakiv(test_data, vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_weakiv(test_data, vce="robust")

    def test_idstat(self, python_result, stata_result):
        st = stata_result.get("idstat")
        assert st is not None
        passed, msg = tolerance_close(python_result.idstat, st, name="idstat", rtol=1e-4)
        assert passed, msg

    def test_widstat(self, python_result, stata_result):
        st = stata_result.get("widstat")
        assert st is not None
        passed, msg = tolerance_close(python_result.widstat, st, name="widstat", rtol=1e-4)
        assert passed, msg

    def test_iddf(self, python_result, stata_result):
        assert python_result.iddf == int(stata_result.get("iddf", -1))

    def test_sy_critical_values(self, python_result, stata_result):
        for key in ["sy_10pct", "sy_15pct", "sy_20pct", "sy_25pct"]:
            st = stata_result.get(key)
            assert st is not None
            py = getattr(python_result, key)
            passed, msg = tolerance_close(py, st, name=key, rtol=1e-4)
            assert passed, msg


class TestW10WeakivCluster:
    """Golden test for weakiv under cluster VCE."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return _run_python_weakiv(test_data, vce="cluster", cluster="entity_id")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_weakiv(test_data, vce="cluster entity_id")

    def test_idstat(self, python_result, stata_result):
        st = stata_result.get("idstat")
        assert st is not None
        passed, msg = tolerance_close(python_result.idstat, st, name="idstat", rtol=1e-4)
        assert passed, msg

    def test_widstat(self, python_result, stata_result):
        st = stata_result.get("widstat")
        assert st is not None
        passed, msg = tolerance_close(python_result.widstat, st, name="widstat", rtol=1e-4)
        assert passed, msg

    def test_iddf(self, python_result, stata_result):
        assert python_result.iddf == int(stata_result.get("iddf", -1))

    def test_sy_critical_values(self, python_result, stata_result):
        for key in ["sy_10pct", "sy_15pct", "sy_20pct", "sy_25pct"]:
            st = stata_result.get(key)
            assert st is not None
            py = getattr(python_result, key)
            passed, msg = tolerance_close(py, st, name=key, rtol=1e-4)
            assert passed, msg
