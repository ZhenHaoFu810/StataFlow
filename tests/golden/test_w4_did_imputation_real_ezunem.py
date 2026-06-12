"""Golden test: w4_did_imputation_real_ezunem - DID imputation on real public ezunem data."""

import re
import pytest
import pandas as pd
from pathlib import Path
from stataflow.estimators.did_imputation import DIDImputation
from tests.golden.test_utils import StataRunner, tolerance_close

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_STATA_OUTPUT = PROJECT_ROOT / "stata" / "output"
DATA_FILE = PROJECT_ROOT / "research" / "data" / "public" / "did" / "ezunem_prepared_didimp.dta"


def _parse_did_imputation_log(log_content: str) -> dict:
    """Parse DID imputation log with B_name=/SE_name= lines."""
    coefficients = []
    b_matches = {m.group(1): float(m.group(2)) for m in re.finditer(r'B_(\w+)=(-?[\d.]+)', log_content)}
    se_matches = {m.group(1): float(m.group(2)) for m in re.finditer(r'SE_(\w+)=(-?[\d.]+)', log_content)}
    for name in b_matches:
        coefficients.append({
            'name': name,
            'beta': b_matches[name],
            'std_err': se_matches.get(name, 0.0),
        })
    nobs_match = re.search(r'E_N=(\d+)', log_content)
    nobs = int(nobs_match.group(1)) if nobs_match else None
    return {'coefficients': coefficients, 'nobs': nobs}


class TestW4DIDImputationRealEzunem:
    """Golden test for DID imputation on real ezunem data."""

    @pytest.fixture(scope="class")
    def data(self):
        return pd.read_stata(DATA_FILE)

    @pytest.fixture(scope="class")
    def python_result(self, data):
        model = DIDImputation(
            data=data,
            y='uclms',
            id='city',
            time='year',
            first_treat='first_treat',
        )
        return model.fit(cluster='city', allhorizons=True, autosample=True, minn=0)

    @pytest.fixture(scope="class")
    def stata_result(self):
        do_content = '''
clear all
set more off
use "%s", clear
replace first_treat = . if first_treat < 0
did_imputation uclms city year first_treat, cluster(city) allhorizons autosample minn(0)
matrix b = e(b)
matrix V = e(V)
local names : colfullnames b
local i = 1
foreach name of local names {
    display "B_`name'=" b[1, `i']
    display "SE_`name'=" sqrt(V[`i', `i'])
    local ++i
}
display "E_N=" e(N)
display "STATAFLOW_CASE_EVID001_DIDIMP_OK"
exit, clear
''' % (DATA_FILE.as_posix(),)
        runner = StataRunner()
        result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT))
        if result.exit_code != 0:
            raise RuntimeError(f"Stata failed: {result.error_message}")
        if not result.output_content:
            raise RuntimeError("Stata produced no output")
        return _parse_did_imputation_log(result.output_content)

    def test_coefficients_count(self, python_result, stata_result):
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result['coefficients']]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        st_coefs = {c['name']: c for c in stata_result['coefficients']}
        for py_coef in python_result.coefficients:
            name = py_coef.name
            passed, msg = tolerance_close(
                py_coef.beta, st_coefs[name]['beta'], name=f"beta[{name}]", rtol=1e-5, atol=1e-6
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        st_coefs = {c['name']: c for c in stata_result['coefficients']}
        for py_coef in python_result.coefficients:
            name = py_coef.name
            st_se = st_coefs[name]['std_err']
            if st_se == 0:
                continue
            passed, msg = tolerance_close(
                py_coef.std_err, st_se, name=f"std_err[{name}]", rtol=1e-2, atol=1e-2
            )
            assert passed, msg

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.sample.nobs, stata_result['nobs'], name='nobs')
        assert passed, msg

    def test_sample_mask_invariants(self, python_result):
        mask = python_result.sample.sample_mask
        assert len(mask) == python_result.sample.n_input_rows
        assert sum(mask) == python_result.sample.nobs
