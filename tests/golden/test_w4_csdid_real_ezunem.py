"""Golden test: w4_csdid_real_ezunem - CSDID on real public ezunem data."""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow.estimators.csdid import CSDID
from tests.golden.test_utils import tolerance_close

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATA_LOG = PROJECT_ROOT / "stata" / "output" / "realdata_csdid.log"
DATA_FILE = PROJECT_ROOT / "research" / "data" / "public" / "did" / "ezunem_prepared.dta"


def _parse_csdid_event_study_log(log_content: str) -> dict:
    """Parse event-study coefficients from csdid_estat event log."""
    lines = log_content.splitlines()
    # Find the Event Study section
    start_idx = None
    for i, line in enumerate(lines):
        if "Event Study:Dynamic effects" in line:
            start_idx = i
            break
    if start_idx is None:
        raise ValueError("Event Study section not found in log")

    # Find the coefficient table delimiter after the start
    delim_idx = None
    for i in range(start_idx, len(lines)):
        if "-------------+----------------------------------------------------------------" in lines[i]:
            delim_idx = i
            break
    if delim_idx is None:
        raise ValueError("Coefficient table delimiter not found")

    coef_pattern = re.compile(
        r'^\s+([A-Za-z_][A-Za-z0-9_]*)\s+\|\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)'
    )
    coefficients = []
    for line in lines[delim_idx + 1 :]:
        if line.strip() == '':
            break
        match = coef_pattern.match(line)
        if match:
            coefficients.append({
                'name': match.group(1),
                'beta': float(match.group(2)),
                'std_err': float(match.group(3)),
            })

    # Also parse nobs if available
    nobs_match = re.search(r'E_N=(\d+)', log_content)
    nobs = int(nobs_match.group(1)) if nobs_match else None

    return {'coefficients': coefficients, 'nobs': nobs}


class TestW4CSDIDRealEzunem:
    """Golden test for CSDID on real ezunem data."""

    @pytest.fixture(scope="class")
    def data(self):
        return pd.read_stata(DATA_FILE)

    @pytest.fixture(scope="class")
    def python_result(self, data):
        model = CSDID(
            data=data,
            y='uclms',
            id='city',
            time='year',
            first_treat='first_treat',
        )
        model.fit(method='reg', vce='cluster', cluster='city')
        return model.estat_event()

    @pytest.fixture(scope="class")
    def stata_result(self):
        log_content = STATA_LOG.read_text(encoding='utf-8', errors='replace')
        return _parse_csdid_event_study_log(log_content)

    def test_coefficients_count(self, python_result, stata_result):
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result['coefficients']]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        py_coef_map = {c.name: c.beta for c in python_result.coefficients}
        for st_coef in stata_result['coefficients']:
            name = st_coef['name']
            py_beta = py_coef_map[name]
            passed, msg = tolerance_close(py_beta, st_coef['beta'], name=f"beta[{name}]")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        py_se_map = {c.name: c.std_err for c in python_result.coefficients}
        for st_coef in stata_result['coefficients']:
            name = st_coef['name']
            py_se = py_se_map[name]
            if st_coef['std_err'] == 0:
                continue
            passed, msg = tolerance_close(
                py_se, st_coef['std_err'], name=f"std_err[{name}]", rtol=1e-5, atol=1e-3
            )
            assert passed, msg

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.sample.nobs, stata_result['nobs'], name='nobs')
        assert passed, msg

    def test_sample_mask_nobs_consistency(self, python_result):
        assert len(python_result.sample.sample_mask) == python_result.sample.n_input_rows
        assert sum(python_result.sample.sample_mask) == python_result.sample.nobs
