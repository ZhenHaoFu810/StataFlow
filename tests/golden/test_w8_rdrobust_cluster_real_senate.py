"""
Golden test: w8_rdrobust_cluster_real_senate
Cluster-robust VCE on real rdrobust_senate.dta.

Verifies vce(cluster) and vce(nncluster) align with Stata 17.
"""

import pytest
import pandas as pd
from pathlib import Path
from stataflow.compat.stata import rdrobust
from tests.golden.test_utils import PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner, tolerance_close

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_FILE = PROJECT_ROOT / "tests" / "data" / "rdrobust_senate.dta"

VCE_METHODS = ["cluster", "nncluster"]


def _run_stata_cluster_rd(data: pd.DataFrame, vce: str) -> dict:
    dta_file = PROJECT_STATA_CASES / "w8_cluster_rd_real_senate.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

rdrobust vote margin, c(0) bwselect(mserd) vce({vce} state)

disp "TAU_CL=" scalar(tau_cl)
disp "TAU_BC=" scalar(tau_bc)
disp "SE_CL=" scalar(se_tau_cl)
disp "SE_RB=" scalar(se_tau_rb)
disp "H_L=" scalar(h_l)
disp "H_R=" scalar(h_r)
disp "N=" e(N)

disp "CLUSTER_{vce.upper()}_DONE"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_cluster_log(result.output_content)


def _parse_cluster_log(log_content: str) -> dict:
    import re
    result = {}
    patterns = {
        'tau_cl': r'TAU_CL=(-?[\d.]+)',
        'tau_bc': r'TAU_BC=(-?[\d.]+)',
        'se_tau_cl': r'SE_CL=(-?[\d.]+)',
        'se_tau_rb': r'SE_RB=(-?[\d.]+)',
        'h_l': r'H_L=(-?[\d.]+)',
        'h_r': r'H_R=(-?[\d.]+)',
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


class TestW8RDRobustClusterRealSenate:
    """Golden test for cluster VCE on real senate data."""

    @pytest.fixture(scope="class")
    def data(self):
        return pd.read_stata(DATA_FILE)

    @pytest.fixture(scope="class")
    def python_results(self, data):
        results = {}
        for vce in VCE_METHODS:
            res = rdrobust(
                data, y="vote", x="margin", c=0.0,
                bwselect="mserd", vce=vce, cluster="state"
            )
            extras = res._rd_extras
            results[vce] = {
                'tau_cl': extras.get('tau_cl'),
                'tau_bc': extras.get('tau_bc'),
                'se_tau_cl': extras.get('se_tau_cl'),
                'se_tau_rb': extras.get('se_tau_rb'),
                'h_l': extras.get('h_l'),
                'h_r': extras.get('h_r'),
                'nobs': res.sample.nobs if hasattr(res, 'sample') and res.sample else None,
            }
        return results

    @pytest.fixture(scope="class")
    def stata_results(self, data):
        results = {}
        for vce in VCE_METHODS:
            results[vce] = _run_stata_cluster_rd(data, vce)
        return results

    def test_tau_cl(self, python_results, stata_results):
        for vce in VCE_METHODS:
            passed, msg = tolerance_close(
                python_results[vce]['tau_cl'], stata_results[vce]['tau_cl'],
                rtol=1e-2, atol=1e-6, name=f"tau_cl[{vce}]"
            )
            assert passed, msg

    def test_tau_bc(self, python_results, stata_results):
        for vce in VCE_METHODS:
            passed, msg = tolerance_close(
                python_results[vce]['tau_bc'], stata_results[vce]['tau_bc'],
                rtol=1e-2, atol=1e-6, name=f"tau_bc[{vce}]"
            )
            assert passed, msg

    def test_se_tau_cl(self, python_results, stata_results):
        for vce in VCE_METHODS:
            passed, msg = tolerance_close(
                python_results[vce]['se_tau_cl'], stata_results[vce]['se_tau_cl'],
                rtol=3e-2, atol=1e-6, name=f"se_tau_cl[{vce}]"
            )
            assert passed, msg

    def test_se_tau_rb(self, python_results, stata_results):
        for vce in VCE_METHODS:
            passed, msg = tolerance_close(
                python_results[vce]['se_tau_rb'], stata_results[vce]['se_tau_rb'],
                rtol=3e-2, atol=1e-6, name=f"se_tau_rb[{vce}]"
            )
            assert passed, msg

    def test_bandwidths(self, python_results, stata_results):
        for vce in VCE_METHODS:
            for key in ['h_l', 'h_r']:
                passed, msg = tolerance_close(
                    python_results[vce][key], stata_results[vce][key],
                    rtol=1e-6, atol=1e-6, name=f"{key}[{vce}]"
                )
                assert passed, msg

    def test_nobs(self, python_results, stata_results):
        for vce in VCE_METHODS:
            passed, msg = tolerance_close(
                python_results[vce]['nobs'], stata_results[vce]['nobs'],
                atol=1, name=f"nobs[{vce}]"
            )
            assert passed, msg
