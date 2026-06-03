"""
Golden test: w8_rdrobust_fuzzy_real_senate
Fuzzy RD on real rdrobust_senate.dta with constructed fuzzy treatment.

Constructs a fuzzy treatment variable based on margin with noise,
then verifies fuzzy RD estimation aligns with Stata 17.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow.compat.stata import rdrobust
from tests.golden.test_utils import PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner, tolerance_close

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_FILE = PROJECT_ROOT / "tests" / "data" / "rdrobust_senate.dta"


def _load_senate_with_fuzzy():
    df = pd.read_stata(DATA_FILE)
    rng = np.random.default_rng(42)
    # Fuzzy treatment: based on margin with noise
    margin = df["margin"].to_numpy(dtype=float)
    t_prob = 0.5 + 0.4 * (margin >= 0.0) + rng.normal(0, 0.05, size=len(df))
    t_prob = np.clip(t_prob, 0, 1)
    df["fuzzy_treat"] = (rng.random(len(df)) < t_prob).astype(float)
    return df


def _run_stata_fuzzy_rd_real(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "w8_fuzzy_rd_real_senate.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

rdrobust vote margin, c(0) fuzzy(fuzzy_treat sharpbw)

disp "TAU_CL=" scalar(tau_cl)
disp "TAU_BC=" scalar(tau_bc)
disp "SE_CL=" scalar(se_tau_cl)
disp "SE_RB=" scalar(se_tau_rb)
disp "H_L=" scalar(h_l)
disp "H_R=" scalar(h_r)
disp "B_L=" scalar(b_l)
disp "B_R=" scalar(b_r)
disp "N=" e(N)

disp "FUZZY_REAL_DONE"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_fuzzy_log(result.output_content)


def _parse_fuzzy_log(log_content: str) -> dict:
    import re
    result = {}
    patterns = {
        'tau_cl': r'TAU_CL=(-?[\d.]+)',
        'tau_bc': r'TAU_BC=(-?[\d.]+)',
        'se_tau_cl': r'SE_CL=(-?[\d.]+)',
        'se_tau_rb': r'SE_RB=(-?[\d.]+)',
        'h_l': r'H_L=(-?[\d.]+)',
        'h_r': r'H_R=(-?[\d.]+)',
        'b_l': r'B_L=(-?[\d.]+)',
        'b_r': r'B_R=(-?[\d.]+)',
        'nobs': r'N=([\d]+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)
    return result


class TestW8RDRobustFuzzyRealSenate:
    """Golden test for fuzzy RD on real senate data."""

    @pytest.fixture(scope="class")
    def data(self):
        return _load_senate_with_fuzzy()

    @pytest.fixture(scope="class")
    def python_result(self, data):
        res = rdrobust(data, y="vote", x="margin", c=0.0, fuzzy="fuzzy_treat", sharpbw=True, bwselect="mserd")
        extras = res._rd_extras
        return {
            'tau_cl': extras.get('tau_cl'),
            'tau_bc': extras.get('tau_bc'),
            'se_tau_cl': extras.get('se_tau_cl'),
            'se_tau_rb': extras.get('se_tau_rb'),
            'h_l': extras.get('h_l'),
            'h_r': extras.get('h_r'),
            'b_l': extras.get('b_l'),
            'b_r': extras.get('b_r'),
            'nobs': res.sample.nobs if hasattr(res, 'sample') and res.sample else None,
        }

    @pytest.fixture(scope="class")
    def stata_result(self, data):
        return _run_stata_fuzzy_rd_real(data)

    def test_tau_cl(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['tau_cl'], stata_result['tau_cl'],
            rtol=5e-4, atol=1e-6, name="tau_cl"
        )
        assert passed, msg

    def test_tau_bc(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['tau_bc'], stata_result['tau_bc'],
            rtol=5e-4, atol=1e-6, name="tau_bc"
        )
        assert passed, msg

    def test_se_tau_cl(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['se_tau_cl'], stata_result['se_tau_cl'],
            rtol=5e-4, atol=1e-6, name="se_tau_cl"
        )
        assert passed, msg

    def test_se_tau_rb(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['se_tau_rb'], stata_result['se_tau_rb'],
            rtol=5e-4, atol=1e-6, name="se_tau_rb"
        )
        assert passed, msg

    def test_bandwidths(self, python_result, stata_result):
        for key in ['h_l', 'h_r', 'b_l', 'b_r']:
            passed, msg = tolerance_close(
                python_result[key], stata_result[key],
                rtol=5e-4, atol=1e-6, name=key
            )
            assert passed, msg

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['nobs'], stata_result['nobs'],
            atol=1, name="nobs"
        )
        assert passed, msg
