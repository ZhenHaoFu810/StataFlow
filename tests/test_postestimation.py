"""Unit tests for postestimation helpers."""

import numpy as np
import pandas as pd
import pytest
from types import SimpleNamespace

from stataflow.postestimation import (
    estat_summarize,
    estat_ic,
    estat_vce,
    predict_xb,
    predict_residuals,
)


class TestEstatSummarize:
    def test_basic_summary(self):
        data = pd.DataFrame({
            "y": [1.0, 2.0, 3.0, 4.0, 5.0],
            "x1": [2.0, 4.0, 6.0, 8.0, 10.0],
        })
        result = SimpleNamespace(
            sample=SimpleNamespace(mask=pd.Series([True, True, True, True, True])),
            coefficients=[SimpleNamespace(name="x1")],
        )
        summary = estat_summarize(result, data, dep_var="y")
        assert "y" in summary
        assert "x1" in summary
        assert summary["y"]["N"] == 5.0
        assert summary["y"]["mean"] == 3.0

    def test_missing_sample_mask_fallback(self):
        """When result.sample.mask is missing, estat_summarize should use all rows."""
        data = pd.DataFrame({
            "y": [1.0, 2.0, 3.0, 4.0, 5.0],
            "x1": [2.0, 4.0, 6.0, 8.0, 10.0],
        })
        # Result with no sample attribute at all
        result = SimpleNamespace(
            coefficients=[SimpleNamespace(name="x1")],
        )
        summary = estat_summarize(result, data, dep_var="y")
        assert "y" in summary
        assert summary["y"]["N"] == 5.0
        assert summary["y"]["mean"] == 3.0

    def test_sample_attribute_but_no_mask(self):
        """When result.sample exists but has no mask attribute."""
        data = pd.DataFrame({
            "y": [10.0, 20.0, 30.0],
            "x1": [1.0, 2.0, 3.0],
        })
        result = SimpleNamespace(
            sample=SimpleNamespace(),  # no mask
            coefficients=[SimpleNamespace(name="x1")],
        )
        summary = estat_summarize(result, data, dep_var="y")
        assert summary["y"]["N"] == 3.0
        assert summary["y"]["mean"] == 20.0

    def test_mask_filters_rows(self):
        data = pd.DataFrame({
            "y": [1.0, 2.0, 3.0, 4.0, 5.0],
            "x1": [2.0, 4.0, 6.0, 8.0, 10.0],
        })
        mask = pd.Series([True, True, False, False, True])
        result = SimpleNamespace(
            sample=SimpleNamespace(sample_mask=mask),
            coefficients=[SimpleNamespace(name="x1")],
        )
        summary = estat_summarize(result, data, dep_var="y")
        assert summary["y"]["N"] == 3.0
        assert summary["y"]["mean"] == pytest.approx(8.0 / 3.0)

    def test_custom_variables(self):
        data = pd.DataFrame({
            "a": [1.0, 2.0, 3.0],
            "b": [4.0, 5.0, 6.0],
            "c": [7.0, 8.0, 9.0],
        })
        result = SimpleNamespace(
            sample=SimpleNamespace(mask=pd.Series([True, True, True])),
        )
        summary = estat_summarize(result, data, variables=["a", "b"])
        assert "a" in summary
        assert "b" in summary
        assert "c" not in summary

    def test_missing_column_skipped(self):
        data = pd.DataFrame({
            "y": [1.0, 2.0, 3.0],
        })
        result = SimpleNamespace(
            sample=SimpleNamespace(mask=pd.Series([True, True, True])),
            coefficients=[SimpleNamespace(name="missing_var")],
        )
        summary = estat_summarize(result, data, dep_var="y")
        assert "y" in summary
        assert "missing_var" not in summary


class TestEstatIc:
    def test_basic_ic(self):
        result = SimpleNamespace(
            fit=SimpleNamespace(ll=-100.0, df_model=2, has_constant=True),
            sample=SimpleNamespace(nobs=100),
        )
        ic = estat_ic(result)
        assert ic["N"] == 100.0
        assert ic["ll"] == -100.0
        assert ic["k"] == 3.0  # df_model + 1 for constant
        expected_aic = -2.0 * (-100.0) + 2.0 * 3.0
        expected_bic = -2.0 * (-100.0) + 3.0 * np.log(100.0)
        assert ic["aic"] == pytest.approx(expected_aic)
        assert ic["bic"] == pytest.approx(expected_bic)

    def test_no_constant(self):
        result = SimpleNamespace(
            fit=SimpleNamespace(ll=-50.0, df_model=2, has_constant=False),
            sample=SimpleNamespace(nobs=50),
        )
        ic = estat_ic(result)
        assert ic["k"] == 2.0  # df_model + 0

    def test_model_has_constant_fallback(self):
        """When fit.has_constant is missing, fall back to model.has_constant."""
        result = SimpleNamespace(
            fit=SimpleNamespace(ll=-50.0, df_model=2),
            model=SimpleNamespace(has_constant=True),
            sample=SimpleNamespace(nobs=50),
        )
        ic = estat_ic(result)
        assert ic["k"] == 3.0

    def test_missing_ll_returns_empty(self):
        result = SimpleNamespace(
            fit=SimpleNamespace(ll=np.nan, df_model=2),
            sample=SimpleNamespace(nobs=50),
        )
        ic = estat_ic(result)
        assert ic == {}

    def test_no_ll_attribute_returns_empty(self):
        result = SimpleNamespace(
            fit=SimpleNamespace(df_model=2),
            sample=SimpleNamespace(nobs=50),
        )
        ic = estat_ic(result)
        assert ic == {}


class TestEstatVce:
    def test_basic_vce(self):
        result = SimpleNamespace(
            variance=SimpleNamespace(values=np.array([[1.0, 0.5], [0.5, 2.0]])),
        )
        vce = estat_vce(result)
        assert np.allclose(vce, np.array([[1.0, 0.5], [0.5, 2.0]]))

    def test_missing_variance(self):
        result = SimpleNamespace()
        assert estat_vce(result) is None

    def test_missing_values(self):
        result = SimpleNamespace(variance=SimpleNamespace())
        assert estat_vce(result) is None


class TestPredictHelpers:
    def test_predict_xb(self):
        beta = np.array([1.0, 2.0])
        X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        xb = predict_xb(beta, X)
        assert np.allclose(xb, np.array([1.0, 2.0, 3.0]))

    def test_predict_residuals(self):
        y = np.array([1.0, 2.0, 3.0])
        xb = np.array([0.5, 2.0, 2.5])
        resid = predict_residuals(y, xb)
        assert np.allclose(resid, np.array([0.5, 0.0, 0.5]))
