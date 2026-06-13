"""Tests for factor-aware GLM margins."""

import numpy as np
import pandas as pd
import pytest

from stataflow import Logit
from stataflow.compat.stata.factor_variables import expand_factor_terms


def _binary_data() -> pd.DataFrame:
    rng = np.random.default_rng(20260612)
    n = 400
    group = rng.integers(0, 2, n)
    x = rng.normal(size=n)
    probability = 1.0 / (1.0 + np.exp(-(-0.4 + 0.9 * group + 0.55 * x)))
    return pd.DataFrame({"y": rng.binomial(1, probability), "g": group, "x": x})


def test_factor_expansion_marks_simple_indicators_as_discrete():
    data, columns = expand_factor_terms(_binary_data(), ["i.g", "x"])

    assert columns == ["1.g", "x"]
    assert data.attrs["stataflow_discrete_columns"] == ["1.g"]
    assert not data.attrs["stataflow_unsupported_factor_margins"]


def test_glm_margins_rejects_factor_interactions():
    data, columns = expand_factor_terms(_binary_data(), ["i.g##c.x"])
    model = Logit(data, "y", columns)
    model.fit()

    with pytest.raises(NotImplementedError, match="factor-variable interactions"):
        model.margins()


def test_glm_margins_rejects_unknown_type():
    data, columns = expand_factor_terms(_binary_data(), ["i.g", "x"])
    model = Logit(data, "y", columns)
    model.fit()

    with pytest.raises(ValueError, match="dydx.*atmeans"):
        model.margins(type="invalid")
