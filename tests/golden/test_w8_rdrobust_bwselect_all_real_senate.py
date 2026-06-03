"""
Golden test: w8_rdrobust_bwselect_all_real_senate
All bandwidth selectors on rdrobust_senate.dta real data.

Verifies that every supported bwselect value produces results aligned
with Stata 17 rdrobust on the Senate election dataset.
"""

import pytest
import pandas as pd
from pathlib import Path
from stataflow.compat.stata import rdrobust
from tests.golden.test_utils import PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner, tolerance_close

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_FILE = PROJECT_ROOT / "tests" / "data" / "rdrobust_senate.dta"

# All bandwidth selectors supported by the Python implementation
BWSELECTORS = [
    "mserd", "msesum", "msetwo",
    "msecomb1", "msecomb2",
    "cerrd", "cersum", "certwo",
    "cercomb1", "cercomb2",
]


def _run_stata_rdrobust_bwselectors() -> dict:
    """Run Stata rdrobust with all bandwidth selectors on senate data."""
    data = pd.read_stata(DATA_FILE)
    dta_file = PROJECT_STATA_CASES / "w8_rdrobust_senate_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_lines = [
        'clear all',
        'set more off',
        f'use "{dta_file}", clear',
    ]

    for sel in BWSELECTORS:
        do_lines.append(f'')
        do_lines.append(f'rdrobust vote margin, c(0) bwselect({sel})')
        do_lines.append(f'disp "SEL_{sel}_TAU_CL=" scalar(tau_cl)')
        do_lines.append(f'disp "SEL_{sel}_TAU_BC=" scalar(tau_bc)')
        do_lines.append(f'disp "SEL_{sel}_SE_CL=" scalar(se_tau_cl)')
        do_lines.append(f'disp "SEL_{sel}_SE_RB=" scalar(se_tau_rb)')
        do_lines.append(f'disp "SEL_{sel}_H_L=" scalar(h_l)')
        do_lines.append(f'disp "SEL_{sel}_H_R=" scalar(h_r)')
        do_lines.append(f'disp "SEL_{sel}_B_L=" scalar(b_l)')
        do_lines.append(f'disp "SEL_{sel}_B_R=" scalar(b_r)')
        do_lines.append(f'disp "SEL_{sel}_N=" e(N)')

    do_lines.append('')
    do_lines.append('disp "BWSELECT_DONE"')

    do_template = '\n'.join(do_lines)
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_bwselect_log(result.output_content)


def _parse_bwselect_log(log_content: str) -> dict:
    """Parse Stata log with bandwidth selector results."""
    import re
    results = {}
    for sel in BWSELECTORS:
        entry = {}
        patterns = {
            'tau_cl': rf'SEL_{sel}_TAU_CL=(-?[\d.]+)',
            'tau_bc': rf'SEL_{sel}_TAU_BC=(-?[\d.]+)',
            'se_tau_cl': rf'SEL_{sel}_SE_CL=(-?[\d.]+)',
            'se_tau_rb': rf'SEL_{sel}_SE_RB=(-?[\d.]+)',
            'h_l': rf'SEL_{sel}_H_L=(-?[\d.]+)',
            'h_r': rf'SEL_{sel}_H_R=(-?[\d.]+)',
            'b_l': rf'SEL_{sel}_B_L=(-?[\d.]+)',
            'b_r': rf'SEL_{sel}_B_R=(-?[\d.]+)',
            'nobs': rf'SEL_{sel}_N=([\d]+)',
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, log_content)
            if match:
                val_str = match.group(1)
                if val_str.startswith('.'):
                    val_str = '0' + val_str
                entry[key] = float(val_str)
        results[sel] = entry
    return results


class TestW8RDRobustBWSelectAllRealSenate:
    """Golden test for all bandwidth selectors on real senate data."""

    @pytest.fixture(scope="class")
    def data(self):
        return pd.read_stata(DATA_FILE)

    @pytest.fixture(scope="class")
    def python_results(self, data):
        results = {}
        for sel in BWSELECTORS:
            res = rdrobust(data, y="vote", x="margin", c=0.0, bwselect=sel)
            extras = res._rd_extras
            results[sel] = {
                'tau_cl': extras.get('tau_cl'),
                'tau_bc': extras.get('tau_bc'),
                'se_tau_cl': extras.get('se_tau_cl'),
                'se_tau_rb': extras.get('se_tau_rb'),
                'h_l': extras.get('h_l'),
                'h_r': extras.get('h_r'),
                'b_l': extras.get('b_l'),
                'b_r': extras.get('b_r'),
                'nobs': extras.get('N'),
            }
        return results

    @pytest.fixture(scope="class")
    def stata_results(self):
        return _run_stata_rdrobust_bwselectors()

    def test_all_selectors_present(self, python_results, stata_results):
        for sel in BWSELECTORS:
            assert sel in stata_results, f"Missing Stata result for {sel}"
            assert sel in python_results, f"Missing Python result for {sel}"

    def test_tau_cl(self, python_results, stata_results):
        for sel in BWSELECTORS:
            py_val = python_results[sel]['tau_cl']
            st_val = stata_results[sel].get('tau_cl')
            if py_val is None or st_val is None:
                continue
            passed, msg = tolerance_close(py_val, st_val, rtol=5e-3, atol=1e-6, name=f"tau_cl[{sel}]")
            assert passed, msg

    def test_tau_bc(self, python_results, stata_results):
        for sel in BWSELECTORS:
            py_val = python_results[sel]['tau_bc']
            st_val = stata_results[sel].get('tau_bc')
            if py_val is None or st_val is None:
                continue
            passed, msg = tolerance_close(py_val, st_val, rtol=5e-3, atol=1e-6, name=f"tau_bc[{sel}]")
            assert passed, msg

    def test_se_tau_cl(self, python_results, stata_results):
        for sel in BWSELECTORS:
            py_val = python_results[sel]['se_tau_cl']
            st_val = stata_results[sel].get('se_tau_cl')
            if py_val is None or st_val is None:
                continue
            passed, msg = tolerance_close(py_val, st_val, rtol=5e-3, atol=1e-6, name=f"se_tau_cl[{sel}]")
            assert passed, msg

    def test_se_tau_rb(self, python_results, stata_results):
        for sel in BWSELECTORS:
            py_val = python_results[sel]['se_tau_rb']
            st_val = stata_results[sel].get('se_tau_rb')
            if py_val is None or st_val is None:
                continue
            passed, msg = tolerance_close(py_val, st_val, rtol=5e-3, atol=1e-6, name=f"se_tau_rb[{sel}]")
            assert passed, msg

    def test_bandwidth_h(self, python_results, stata_results):
        for sel in BWSELECTORS:
            for side in ['h_l', 'h_r']:
                py_val = python_results[sel][side]
                st_val = stata_results[sel].get(side)
                if py_val is None or st_val is None:
                    continue
                passed, msg = tolerance_close(py_val, st_val, rtol=1e-2, atol=1e-6, name=f"{side}[{sel}]")
                assert passed, msg

    def test_bandwidth_b(self, python_results, stata_results):
        for sel in BWSELECTORS:
            for side in ['b_l', 'b_r']:
                py_val = python_results[sel][side]
                st_val = stata_results[sel].get(side)
                if py_val is None or st_val is None:
                    continue
                passed, msg = tolerance_close(py_val, st_val, rtol=1e-2, atol=1e-6, name=f"{side}[{sel}]")
                assert passed, msg

    def test_nobs(self, python_results, stata_results):
        for sel in BWSELECTORS:
            py_val = python_results[sel]['nobs']
            st_val = stata_results[sel].get('nobs')
            if py_val is None or st_val is None:
                continue
            passed, msg = tolerance_close(py_val, st_val, atol=1, name=f"nobs[{sel}]")
            assert passed, msg
