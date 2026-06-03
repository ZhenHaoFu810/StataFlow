"""
Golden test: w10_card_weakiv - Weak instrument diagnostics on Card data.

Tests IVAbsorbingOLS weakiv statistics against Stata ivreghdfe on the
Card returns-to-schooling dataset with a simple IV specification.
"""

import re
import pytest
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    StataRunner,
    tolerance_close,
)
from stataflow.compat.stata import ivreghdfe

PROJECT_ROOT = Path(__file__).parent.parent.parent
CARD_CSV = PROJECT_ROOT / "research" / "data" / "public" / "iv" / "card.csv"


def _load_test_data() -> pd.DataFrame:
    """Load Card dataset."""
    return pd.read_csv(str(CARD_CSV))


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata log output for weakiv statistics."""
    result = {}
    patterns = {
        'idstat': r'IDSTAT=(-?[\d.eE+-]+)',
        'iddf': r'IDDF=(-?[\d.eE+-]+)',
        'idp': r'IDP=(-?[\d.eE+-]+)',
        'widstat': r'WIDSTAT=(-?[\d.eE+-]+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            try:
                result[key] = float(val_str)
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
            result[key] = float(match.group(1))

    return result


def _run_stata() -> dict:
    """Run Stata ivreghdfe on Card data and extract weakiv stats."""
    do_template = f'''
clear all
set more off

import delimited "{CARD_CSV}", clear

ivreghdfe lwage exper expersq (educ = nearc4), absorb(south) keepsingletons

display "IDSTAT=" e(idstat)
display "IDDF=" e(iddf)
display "IDP=" e(idp)
display "WIDSTAT=" e(widstat)
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


def _run_python(data: pd.DataFrame):
    """Run Python ivreghdfe on Card data."""
    return ivreghdfe(
        data,
        y="lwage",
        x_exog=["exper", "expersq"],
        x_endog=["educ"],
        instruments=["nearc4"],
        absorb="south",
        estimator="2sls",
    )


class TestW10CardWeakiv:
    """Golden test for w10_card_weakiv."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _load_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return _run_python(test_data)

    @pytest.fixture(scope="class")
    def stata_result(self):
        return _run_stata()

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
