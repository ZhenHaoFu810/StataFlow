"""
Golden test: w8_rdrobust_fuzzy_synthetic
Fuzzy RD on synthetic data with known treatment assignment noise.

Verifies fuzzy RD estimation (with sharpbw) aligns with Stata 17.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow.compat.stata import rdrobust
from tests.golden.test_utils import PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner, tolerance_close

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _generate_fuzzy_rd_data(n=500, seed=12345, jump_y=2.0, jump_t=0.5):
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, size=n)
    # Treatment propensity: jumps at cutoff but with noise
    t_prob = 0.3 + jump_t * (x >= 0.0) + rng.normal(0, 0.1, size=n)
    t_prob = np.clip(t_prob, 0, 1)
    t = (rng.random(n) < t_prob).astype(float)
    y = 5 + 3 * x + jump_y * t + rng.normal(0, 0.5, size=n)
    return pd.DataFrame({"y": y, "x": x, "t": t})


def _run_stata_fuzzy_rd(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "w8_fuzzy_rd_synthetic.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

* Fuzzy RD with sharp bandwidth selection
rdrobust y x, c(0) fuzzy(t sharpbw)

disp "TAU_CL=" scalar(tau_cl)
disp "TAU_BC=" scalar(tau_bc)
disp "SE_CL=" scalar(se_tau_cl)
disp "SE_RB=" scalar(se_tau_rb)
disp "H_L=" scalar(h_l)
disp "H_R=" scalar(h_r)
disp "B_L=" scalar(b_l)
disp "B_R=" scalar(b_r)
disp "N=" e(N)

disp "FUZZY_DONE"
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


class TestW8RDRobustFuzzySynthetic:
    """Golden test for fuzzy RD on synthetic data."""

    @pytest.fixture(scope="class")
    def data(self):
        return _generate_fuzzy_rd_data()

    @pytest.fixture(scope="class")
    def python_result(self, data):
        res = rdrobust(data, y="y", x="x", c=0.0, fuzzy="t", sharpbw=True, bwselect="mserd")
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
    def stata_result(self):
        data = _generate_fuzzy_rd_data()
        return _run_stata_fuzzy_rd(data)

    def test_tau_cl(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['tau_cl'], stata_result['tau_cl'],
            rtol=5e-3, atol=1e-6, name="tau_cl"
        )
        assert passed, msg

    def test_tau_bc(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['tau_bc'], stata_result['tau_bc'],
            rtol=5e-3, atol=1e-6, name="tau_bc"
        )
        assert passed, msg

    def test_se_tau_cl(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['se_tau_cl'], stata_result['se_tau_cl'],
            rtol=5e-2, atol=1e-6, name="se_tau_cl"
        )
        assert passed, msg

    def test_se_tau_rb(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['se_tau_rb'], stata_result['se_tau_rb'],
            rtol=5e-2, atol=1e-6, name="se_tau_rb"
        )
        assert passed, msg

    def test_bandwidths(self, python_result, stata_result):
        for key in ['h_l', 'h_r', 'b_l', 'b_r']:
            passed, msg = tolerance_close(
                python_result[key], stata_result[key],
                rtol=2e-2, atol=1e-6, name=key
            )
            assert passed, msg

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result['nobs'], stata_result['nobs'],
            atol=1, name="nobs"
        )
        assert passed, msg
