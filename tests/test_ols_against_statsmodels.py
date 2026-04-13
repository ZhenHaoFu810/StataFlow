"""
OLS implementation test - verify against statsmodels.

Since Stata MP is a GUI application on this system, we use statsmodels
as a reference implementation to validate our OLS code.
Stata dual-run tests are preserved and can be run manually when
Stata batch execution is available.
"""

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from statapy import OLS


@pytest.fixture
def test_data():
    """Generate test data."""
    np.random.seed(12345)
    n = 100
    
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = 1 + 2 * x1 + 3 * x2 + np.random.normal(0, 1, n)
    
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def _run_statsmodels(data):
    """Run OLS using statsmodels as reference."""
    y = data["y"]
    X = sm.add_constant(data[["x1", "x2"]])
    
    model = sm.OLS(y, X).fit()
    return model


class TestOLSAgainstStatsmodels:
    """Validate OLS implementation against statsmodels."""

    def test_coefficients_beta(self, test_data):
        """Compare coefficient estimates."""
        # Our implementation
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        # Statsmodels
        sm_result = _run_statsmodels(test_data)
        
        # Map our coefficient names to statsmodels names
        name_map = {"_cons": "const"}
        
        # Compare
        for coef in result.coefficients:
            sm_name = name_map.get(coef.name, coef.name)
            sm_beta = sm_result.params[sm_name]
            assert np.isclose(coef.beta, sm_beta, rtol=1e-10), \
                f"Beta mismatch for {coef.name}: ours={coef.beta}, sm={sm_beta}"

    def test_coefficients_std_err(self, test_data):
        """Compare standard errors."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        sm_result = _run_statsmodels(test_data)
        
        name_map = {"_cons": "const"}
        
        for coef in result.coefficients:
            sm_name = name_map.get(coef.name, coef.name)
            sm_se = sm_result.bse[sm_name]
            assert np.isclose(coef.std_err, sm_se, rtol=1e-10), \
                f"SE mismatch for {coef.name}: ours={coef.std_err}, sm={sm_se}"

    def test_r2(self, test_data):
        """Compare R-squared."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        sm_result = _run_statsmodels(test_data)
        
        assert np.isclose(result.fit.r2, sm_result.rsquared, rtol=1e-10), \
            f"R2 mismatch: ours={result.fit.r2}, sm={sm_result.rsquared}"

    def test_r2_adj(self, test_data):
        """Compare Adjusted R-squared."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        sm_result = _run_statsmodels(test_data)
        
        assert np.isclose(result.fit.r2_adj, sm_result.rsquared_adj, rtol=1e-10), \
            f"R2_adj mismatch: ours={result.fit.r2_adj}, sm={sm_result.rsquared_adj}"

    def test_nobs(self, test_data):
        """Compare sample size."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        sm_result = _run_statsmodels(test_data)
        
        assert result.sample.nobs == sm_result.nobs

    def test_df_model(self, test_data):
        """Compare model degrees of freedom."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        sm_result = _run_statsmodels(test_data)
        
        # Both Stata and statsmodels define df_model as number of slope parameters
        # (excluding the constant), so they should match directly
        assert np.isclose(result.fit.df_model, sm_result.df_model, rtol=1e-10)

    def test_df_resid(self, test_data):
        """Compare residual degrees of freedom."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        sm_result = _run_statsmodels(test_data)
        
        assert np.isclose(result.fit.df_resid, sm_result.df_resid, rtol=1e-10)

    def test_f_stat(self, test_data):
        """Compare F-statistic."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        sm_result = _run_statsmodels(test_data)
        
        assert np.isclose(result.fit.f_stat, sm_result.fvalue, rtol=1e-10), \
            f"F-stat mismatch: ours={result.fit.f_stat}, sm={sm_result.fvalue}"

    def test_rmse(self, test_data):
        """Compare RMSE."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")
        
        sm_result = _run_statsmodels(test_data)
        
        assert np.isclose(result.fit.rmse, sm_result.mse_resid**0.5, rtol=1e-10), \
            f"RMSE mismatch: ours={result.fit.rmse}, sm={sm_result.mse_resid**0.5}"

    def test_covariance_matrix(self, test_data):
        """Compare covariance matrix values."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")

        sm_result = _run_statsmodels(test_data)
        sm_cov = sm_result.cov_params()

        # Map coefficient names between our order and statsmodels order
        # We use: x1, x2, _cons
        # statsmodels uses: const, x1, x2
        name_map = {"_cons": "const"}
        our_names = result.variance.row_names
        sm_names = [name_map.get(n, n) for n in our_names]

        # Reorder statsmodels covariance matrix to match our order
        sm_order = [list(sm_result.params.index).index(n) for n in sm_names]
        sm_cov_reordered = sm_cov.iloc[sm_order, sm_order].values

        # Compare covariance matrices
        our_cov = np.array(result.variance.values)

        assert np.allclose(our_cov, sm_cov_reordered, rtol=1e-10), \
            f"Covariance matrix mismatch\nOur order: {our_names}\nSM order: {sm_names}"

    def test_coefficient_order(self, test_data):
        """Verify coefficient order matches Stata convention."""
        ols = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        result = ols.fit(vce="ols")

        names = [c.name for c in result.coefficients]
        # Stata puts variables first, then _cons at the end
        assert names == ["x1", "x2", "_cons"], f"Order wrong: {names}"
