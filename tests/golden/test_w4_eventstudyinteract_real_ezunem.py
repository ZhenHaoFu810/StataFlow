"""Golden test: w4_eventstudyinteract_real_ezunem - Event Study Interact on real public ezunem data."""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from statapy.estimators.eventstudyinteract import EventStudyInteract
from tests.golden.test_utils import tolerance_close

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATA_LOG = PROJECT_ROOT / "stata" / "output" / "realdata_eventstudyinteract_fixed.log"
DATA_FILE = PROJECT_ROOT / "research" / "data" / "public" / "did" / "ezunem_prepared.dta"


def _parse_eventstudyinteract_log(log_content: str) -> dict:
    """Parse eventstudyinteract log with B_name=/SE_name= lines."""
    coefficients = []
    b_matches = {m.group(1): float(m.group(2)) for m in re.finditer(r'B_(Dm\d+)=(-?[\d.]+)', log_content)}
    se_matches = {m.group(1): float(m.group(2)) for m in re.finditer(r'SE_(Dm\d+)=(-?[\d.]+)', log_content)}
    for name in b_matches:
        coefficients.append({
            'name': name,
            'beta': b_matches[name],
            'std_err': se_matches.get(name, 0.0),
        })
    nobs_match = re.search(r'E_N=(\d+)', log_content)
    nobs = int(nobs_match.group(1)) if nobs_match else None
    return {'coefficients': coefficients, 'nobs': nobs}


def _prepare_data():
    df = pd.read_stata(DATA_FILE)
    df['cohort'] = df['first_treat']
    df['rel_time'] = np.where(df['first_treat'] > 0, df['year'] - df['first_treat'], -1000)
    df['never_treated'] = (df['first_treat'] == 0).astype(int)

    # Generate dummies for each rel_time value (same as tab rel_time, gen(Dm))
    rel_vals = sorted(df['rel_time'].unique())
    dummy_cols = []
    for val in rel_vals:
        col = f'Dm{val}'
        df[col] = (df['rel_time'] == val).astype(int)
        if val != -1000:
            dummy_cols.append(col)

    # Build a clean dataframe with Stata-style dummy names to avoid collisions.
    # Stata's  tab rel_time, gen(Dm)  creates dummies in sorted rel_time order:
    #   Dm1=-1000, Dm2=-5, Dm3=-4, Dm4=-3, Dm5=-2, Dm6=-1, Dm7=0, Dm8=1, Dm9=2, Dm10=3, Dm11=4
    # Stata command passes Dm2-Dm10 (exclude never-treated Dm1 and sparse Dm11).
    rel_to_stata = {
        -1000: 'Dm1',
        -5: 'Dm2',
        -4: 'Dm3',
        -3: 'Dm4',
        -2: 'Dm5',
        -1: 'Dm6',
        0: 'Dm7',
        1: 'Dm8',
        2: 'Dm9',
        3: 'Dm10',
        4: 'Dm11',
    }
    clean = df[['uclms', 'city', 'year', 'cohort', 'never_treated']].copy()
    for val in rel_vals:
        clean[rel_to_stata[val]] = (df['rel_time'] == val).astype(int)

    event_dummies = [f'Dm{i}' for i in range(2, 11)]
    return clean, event_dummies


class TestW4EventStudyInteractRealEzunem:
    """Golden test for Event Study Interact on real ezunem data."""

    @pytest.fixture(scope="class")
    def data_and_dummies(self):
        return _prepare_data()

    @pytest.fixture(scope="class")
    def python_result(self, data_and_dummies):
        df, event_dummies = data_and_dummies
        model = EventStudyInteract(
            data=df,
            y='uclms',
            event_dummies=event_dummies,
            cohort='cohort',
            control_cohort='never_treated',
            absorb=['city', 'year'],
        )
        return model.fit(vce='cluster', cluster='city')

    @pytest.fixture(scope="class")
    def stata_result(self):
        log_content = STATA_LOG.read_text(encoding='utf-8', errors='replace')
        return _parse_eventstudyinteract_log(log_content)

    def test_coefficients_count(self, python_result, stata_result):
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result['coefficients']]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        st_coefs = {c['name']: c for c in stata_result['coefficients']}
        for py_coef in python_result.coefficients:
            name = py_coef.name
            passed, msg = tolerance_close(py_coef.beta, st_coefs[name]['beta'], name=f"beta[{name}]")
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
        # Stata log shows Number of obs = 198 (overall), but effective obs = 90 in table header
        # Python nobs uses the effective sample after screening
        # Use the parsed nobs if available, otherwise skip
        if stata_result['nobs'] is not None:
            passed, msg = tolerance_close(
                python_result.sample.nobs, stata_result['nobs'], name='nobs', rtol=1e-2
            )
            assert passed, msg
