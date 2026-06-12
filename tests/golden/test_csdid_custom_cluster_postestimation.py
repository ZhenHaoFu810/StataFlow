"""Golden validation for CSDID postestimation with a custom cluster level."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import csdid
from tests.golden.test_utils import StataRunner, tolerance_close


PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_STATA_OUTPUT = PROJECT_ROOT / "stata" / "output"


def _make_data(seed: int = 812) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_units = 240
    n_periods = 7
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = np.repeat(rng.choice([0, 2, 3], size=n_units), n_periods)
    treated = (times >= first_treat).astype(float)
    treated[first_treat == 0] = 0.0
    return pd.DataFrame({
        "id": units,
        "time": times,
        "y": 1.0 + 2.0 * treated + rng.normal(size=len(units)),
        "first_treat": first_treat,
        "region": units // 6,
    })


def _section(log: str, name: str) -> str:
    match = re.search(
        rf"STATAFLOW_{name}_BEGIN(.*?)STATAFLOW_{name}_END",
        log,
        flags=re.DOTALL,
    )
    if not match:
        raise AssertionError(f"Missing Stata output section: {name}")
    return match.group(1)


def _parse_table(section: str, labels: list[str]) -> dict[str, tuple[float, float]]:
    results = {}
    for label in labels:
        match = re.search(
            rf"^\s*{re.escape(label)}\s*\|\s*([-+.\dEe]+)\s+([-+.\dEe]+)",
            section,
            flags=re.MULTILINE,
        )
        if not match:
            raise AssertionError(f"Missing Stata coefficient row: {label}")
        results[label] = (float(match.group(1)), float(match.group(2)))
    return results


@pytest.fixture(scope="module")
def comparison():
    data = _make_data()
    dta_path = PROJECT_STATA_OUTPUT / "csdid_custom_cluster_postestimation.dta"
    data.to_stata(dta_path, write_index=False)

    do_content = f'''
clear all
set more off
use "{dta_path.as_posix()}", clear
csdid y, ivar(id) time(time) gvar(first_treat) method(reg) cluster(region)
foreach agg in simple group calendar event {{
    display "STATAFLOW_`agg'_BEGIN"
    csdid_estat `agg'
    display "STATAFLOW_`agg'_END"
}}
display "STATAFLOW_pretrend_BEGIN"
csdid_estat pretrend
display "PRETREND_CHI2=" r(chi2)
display "PRETREND_P=" r(pchi2)
display "PRETREND_DF=" r(df)
display "STATAFLOW_pretrend_END"
exit, clear
'''
    stata_run = StataRunner().run_do_file(
        do_content,
        output_dir=str(PROJECT_STATA_OUTPUT),
    )
    assert stata_run.exit_code == 0, stata_run.error_message
    assert stata_run.output_content

    model = csdid(
        data,
        y="y",
        id="id",
        time="time",
        first_treat="first_treat",
        cluster="region",
    )
    return model, stata_run.output_content


@pytest.mark.parametrize(
    ("aggtype", "stata_labels"),
    [
        ("simple", ["ATT"]),
        ("group", ["G2", "G3"]),
        ("calendar", ["T2", "T3", "T4", "T5", "T6"]),
        ("event", ["Pre_avg", "Post_avg", "Tm2", "Tm1", "Tp0", "Tp1", "Tp2", "Tp3", "Tp4"]),
    ],
)
def test_postestimation_coefficients_and_standard_errors(comparison, aggtype, stata_labels):
    model, log = comparison
    python_result = model.estat(aggtype)
    stata_result = _parse_table(_section(log, aggtype), stata_labels)

    assert len(python_result.coefficients) == len(stata_labels)
    for coefficient, label in zip(python_result.coefficients, stata_labels):
        stata_beta, stata_se = stata_result[label]
        passed, message = tolerance_close(
            coefficient.beta,
            stata_beta,
            name=f"{aggtype}.beta[{coefficient.name}]",
        )
        assert passed, message
        passed, message = tolerance_close(
            coefficient.std_err,
            stata_se,
            name=f"{aggtype}.se[{coefficient.name}]",
        )
        assert passed, message


def test_pretrend_joint_test(comparison):
    model, log = comparison
    python_result = model.estat("pretrend")
    section = _section(log, "pretrend")

    stata_chi2 = float(re.search(r"PRETREND_CHI2=\s*([-+.\dEe]+)", section).group(1))
    stata_p = float(re.search(r"PRETREND_P=\s*([-+.\dEe]+)", section).group(1))
    stata_df = float(re.search(r"PRETREND_DF=\s*([-+.\dEe]+)", section).group(1))

    assert tolerance_close(python_result.fit.f_stat, stata_chi2, name="pretrend.chi2")[0]
    assert tolerance_close(python_result.fit.f_pvalue, stata_p, name="pretrend.p")[0]
    assert python_result.fit.df_model == stata_df
