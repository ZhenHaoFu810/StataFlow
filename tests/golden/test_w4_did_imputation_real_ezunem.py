"""Golden test: w4_did_imputation_real_ezunem - DID imputation on real public ezunem data."""

import re
import pytest
import pandas as pd
from pathlib import Path
from stataflow.estimators.did_imputation import DIDImputation
from tests.golden.test_utils import tolerance_close

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATA_LOG = PROJECT_ROOT / "stata" / "output" / "realdata_did_imputation_ezunem.log"
DATA_FILE = PROJECT_ROOT / "research" / "data" / "public" / "did" / "ezunem_prepared.dta"


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
        return model.fit(cluster='city', allhorizons=True, autosample=True)

    @pytest.fixture(scope="class")
    def stata_result(self):
        log_content = STATA_LOG.read_text(encoding='utf-8', errors='replace')
        return _parse_did_imputation_log(log_content)

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
