"""Golden tests for discrete factor-variable changes in GLM margins."""

import re

import numpy as np
import pandas as pd
import pytest

from stataflow import Logit, Poisson, Probit
from stataflow.compat.stata.factor_variables import expand_factor_terms
from tests.golden.test_utils import (
    PROJECT_STATA_CASES,
    PROJECT_STATA_OUTPUT,
    StataRunner,
    tolerance_close,
)


@pytest.fixture(scope="module")
def factor_margins_data() -> pd.DataFrame:
    rng = np.random.default_rng(20260612)
    n = 800
    group = rng.integers(0, 2, n)
    x = rng.normal(size=n)
    probability = 1.0 / (1.0 + np.exp(-(-0.4 + 0.9 * group + 0.55 * x)))
    count_mean = np.exp(0.2 + 0.45 * group + 0.25 * x)
    return pd.DataFrame({
        "y_binary": rng.binomial(1, probability),
        "y_count": rng.poisson(count_mean),
        "g": group,
        "x": x,
    })


@pytest.fixture(scope="module")
def stata_margins(factor_margins_data) -> dict[str, float]:
    data_path = PROJECT_STATA_CASES / "factor_margins_discrete_data.dta"
    factor_margins_data.to_stata(data_path, write_index=False)
    do_file = f'''
clear all
set more off
use "{data_path}", clear

logit y_binary i.g x
margins, dydx(*) post
display "LOGIT_B_G=" _b[1.g]
display "LOGIT_SE_G=" _se[1.g]
display "LOGIT_B_X=" _b[x]
display "LOGIT_SE_X=" _se[x]
logit y_binary i.g x
margins, dydx(*) atmeans post
display "LOGIT_MEM_B_G=" _b[1.g]
display "LOGIT_MEM_SE_G=" _se[1.g]
display "LOGIT_MEM_B_X=" _b[x]
display "LOGIT_MEM_SE_X=" _se[x]

probit y_binary i.g x
margins, dydx(*) post
display "PROBIT_B_G=" _b[1.g]
display "PROBIT_SE_G=" _se[1.g]
display "PROBIT_B_X=" _b[x]
display "PROBIT_SE_X=" _se[x]
probit y_binary i.g x
margins, dydx(*) atmeans post
display "PROBIT_MEM_B_G=" _b[1.g]
display "PROBIT_MEM_SE_G=" _se[1.g]
display "PROBIT_MEM_B_X=" _b[x]
display "PROBIT_MEM_SE_X=" _se[x]

poisson y_count i.g x
margins, dydx(*) post
display "POISSON_B_G=" _b[1.g]
display "POISSON_SE_G=" _se[1.g]
display "POISSON_B_X=" _b[x]
display "POISSON_SE_X=" _se[x]
poisson y_count i.g x
margins, dydx(*) atmeans post
display "POISSON_MEM_B_G=" _b[1.g]
display "POISSON_MEM_SE_G=" _se[1.g]
display "POISSON_MEM_B_X=" _b[x]
display "POISSON_MEM_SE_X=" _se[x]
'''
    result = StataRunner().run_do_file(do_file, output_dir=str(PROJECT_STATA_OUTPUT))
    assert result.exit_code == 0, result.error_message
    assert result.output_content
    values = {
        f"{family}_{mode or 'AME'}_{field}": float(number)
        for family, mode, field, number in re.findall(
            r"(LOGIT|PROBIT|POISSON)_(?:(MEM)_)?(B_G|SE_G|B_X|SE_X)=([-.0-9eE]+)",
            result.output_content,
        )
    }
    assert len(values) == 24
    return values


@pytest.mark.parametrize(
    ("family", "estimator", "dependent", "margins_type", "mode"),
    [
        ("LOGIT", Logit, "y_binary", "dydx", "AME"),
        ("LOGIT", Logit, "y_binary", "atmeans", "MEM"),
        ("PROBIT", Probit, "y_binary", "dydx", "AME"),
        ("PROBIT", Probit, "y_binary", "atmeans", "MEM"),
        ("POISSON", Poisson, "y_count", "dydx", "AME"),
        ("POISSON", Poisson, "y_count", "atmeans", "MEM"),
    ],
)
def test_factor_margins_matches_stata(
    factor_margins_data,
    stata_margins,
    family,
    estimator,
    dependent,
    margins_type,
    mode,
):
    data, columns = expand_factor_terms(
        factor_margins_data,
        ["i.g", "x"],
        screen_vars=[dependent, "g", "x"],
    )
    model = estimator(data, dependent, columns)
    model.fit()
    margins = model.margins(type=margins_type)

    comparisons = [
        (margins.params["1.g"], stata_margins[f"{family}_{mode}_B_G"], "factor effect"),
        (margins.bse["1.g"], stata_margins[f"{family}_{mode}_SE_G"], "factor SE"),
        (margins.params["x"], stata_margins[f"{family}_{mode}_B_X"], "continuous effect"),
        (margins.bse["x"], stata_margins[f"{family}_{mode}_SE_X"], "continuous SE"),
    ]
    for python_value, stata_value, label in comparisons:
        passed, message = tolerance_close(
            python_value,
            stata_value,
            name=f"{family} {label}",
        )
        assert passed, message
