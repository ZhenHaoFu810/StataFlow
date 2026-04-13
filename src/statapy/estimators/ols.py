"""
OLS estimator - aligned with Stata's regress command.

Implements ordinary least squares with:
- Sample screening (drop missing)
- Constant term handling
- Collinearity detection
- Result schema output
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional
from statapy.results.result import (
    ResultSchema,
    ModelInfo,
    SampleInfo,
    FitInfo,
    CoefficientRow,
    VarianceInfo,
    DiagnosticsInfo,
    ProvenanceInfo,
)


class OLS:
    """
    Ordinary Least Squares estimator aligned with Stata's regress.
    
    Parameters
    ----------
    data : pd.DataFrame
        Input data.
    y : str
        Dependent variable name.
    x : list[str]
        Independent variable names.
    add_constant : bool, default True
        Whether to add constant term.
    weights : array-like, optional
        Weights (not used in Phase 0).
    weight_type : str, optional
        Weight type (not used in Phase 0).
    missing : str, default "drop"
        Missing value handling. Only "drop" is supported in v1.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y: str,
        x: list[str],
        add_constant: bool = True,
        weights=None,
        weight_type: Optional[str] = None,
        missing: str = "drop",
    ):
        self.data = data
        self.y = y
        self.x = list(x)
        self.add_constant = add_constant
        self.weights = weights
        self.weight_type = weight_type
        self.missing = missing
        
        # Internal state
        self._design_matrix: Optional[np.ndarray] = None
        self._dep_var: Optional[np.ndarray] = None
        self._sample_mask: Optional[np.ndarray] = None
        self._coef_names: list[str] = []
        self._colinear_dropped: list[str] = []

    def _prepare_data(self) -> tuple[np.ndarray, np.ndarray, list[bool]]:
        """
        Prepare design matrix and dependent variable.
        
        Returns
        -------
        X : np.ndarray
            Design matrix (n x k).
        y : np.ndarray
            Dependent variable (n,).
        sample_mask : list[bool]
            Boolean mask of retained observations.
        """
        # Select columns
        all_vars = [self.y] + self.x
        df = self.data[all_vars].copy()
        
        n_input_rows = len(df)
        
        # Drop missing values
        if self.missing == "drop":
            mask = df.notna().all(axis=1)
            df = df[mask]
        else:
            raise ValueError(f"missing='{self.missing}' not supported in v1")
        
        sample_mask = mask.tolist()
        
        # Extract arrays
        y = df[self.y].values.astype(np.float64)
        
        # Build design matrix
        X_cols = []
        self._coef_names = []

        # Add variables first (Stata convention: variables before constant)
        for var in self.x:
            X_cols.append(df[var].values.astype(np.float64))
            self._coef_names.append(var)

        # Add constant at the end (Stata convention)
        if self.add_constant:
            X_cols.append(np.ones(len(df)))
            self._coef_names.append("_cons")
        
        X = np.column_stack(X_cols)
        
        # Detect collinearity
        X, dropped = self._detect_collinearity(X, self._coef_names)
        self._colinear_dropped = dropped
        
        self._design_matrix = X
        self._dep_var = y
        self._sample_mask = sample_mask
        self._n_input_rows = n_input_rows
        
        return X, y, sample_mask

    def _detect_collinearity(
        self, X: np.ndarray, names: list[str]
    ) -> tuple[np.ndarray, list[str]]:
        """
        Detect and drop collinear columns.

        Uses rank check and QR decomposition with pivoting
        to identify linearly dependent columns.
        """
        dropped = []

        if X.shape[1] <= 1:
            return X, dropped

        # Check rank
        rank = np.linalg.matrix_rank(X)

        if rank == X.shape[1]:
            return X, dropped

        # Use QR with pivoting to identify independent columns
        # np.linalg.qr returns (Q, R) - only 2 values, not 3
        Q, R = np.linalg.qr(X, mode='complete')

        # Columns corresponding to near-zero diagonal elements of R are collinear
        tol = 1e-10
        independent = []

        for i in range(X.shape[1]):
            if i < R.shape[0] and abs(R[i, i]) > tol:
                independent.append(i)
            else:
                dropped.append(names[i])

        # Keep only independent columns
        X_indep = X[:, independent]
        self._coef_names = [names[i] for i in independent]

        return X_indep, dropped

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """
        Fit OLS model.
        
        Parameters
        ----------
        vce : str
            Variance-covariance estimator type. Only "ols" supported in Phase 0.
        cluster : str, optional
            Cluster variable (not used in Phase 0).
        alpha : float
            Significance level for confidence intervals.
            
        Returns
        -------
        ResultSchema
            Fitted result object.
        """
        # Prepare data
        X, y, sample_mask = self._prepare_data()
        
        n = len(y)
        k = X.shape[1]
        
        # OLS estimation: beta = (X'X)^{-1} X'y
        XtX = X.T @ X
        Xty = X.T @ y
        beta = np.linalg.solve(XtX, Xty)
        
        # Residuals and fitted values
        y_hat = X @ beta
        residuals = y - y_hat
        
        # Sum of squared residuals
        rss = float(np.sum(residuals ** 2))
        
        # Total sum of squares (around mean if constant, around zero otherwise)
        if self.add_constant:
            y_mean = np.mean(y)
            tss = float(np.sum((y - y_mean) ** 2))
        else:
            tss = float(np.sum(y ** 2))
        
        mss = tss - rss
        
        # R-squared
        r2 = 1.0 - rss / tss if tss > 0 else 0.0
        
        # Degrees of freedom
        # Stata convention: df_model excludes the constant
        # df_model = number of slope parameters (not counting constant)
        df_model = float(k - 1) if self.add_constant else float(k)
        df_resid = float(n - k)
        
        # RMSE
        rmse = np.sqrt(rss / df_resid) if df_resid > 0 else 0.0
        
        # Adjusted R-squared
        r2_adj = 1.0 - (1.0 - r2) * (n - 1) / df_resid if df_resid > 0 else 0.0
        
        # Variance-covariance matrix of coefficients
        sigma2 = rss / df_resid if df_resid > 0 else 0.0
        cov_beta = sigma2 * np.linalg.inv(XtX)
        
        # Standard errors
        se = np.sqrt(np.diag(cov_beta))
        
        # t-statistics and p-values
        t_stats = beta / se
        # Two-tailed p-value
        from scipy.stats import t as t_dist
        p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=df_resid))
        
        # Confidence intervals
        t_crit = t_dist.ppf(1 - alpha / 2, df=df_resid)
        ci_low = beta - t_crit * se
        ci_high = beta + t_crit * se
        
        # F-statistic (only if constant is present)
        # F = (MSS / df_model) / (RSS / df_resid)
        # where df_model excludes the constant
        if self.add_constant and df_model > 0:
            f_stat = (mss / df_model) / (rss / df_resid)
            from scipy.stats import f as f_dist
            f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
        else:
            f_stat = None
            f_pvalue = None
        
        # Build result object
        result = ResultSchema()
        result.model = ModelInfo(
            command="regress",
            estimator_family="ols",
            vcetype=vce,
            weight_type=self.weight_type,
            has_constant=self.add_constant,
        )
        result.sample = SampleInfo(
            nobs=n,
            n_input_rows=self._n_input_rows,
            sample_mask=sample_mask,
        )
        result.fit = FitInfo(
            df_model=df_model,
            df_resid=df_resid,
            rank=k,
            rss=rss,
            tss=tss,
            mss=mss,
            rmse=rmse,
            r2=r2,
            r2_adj=r2_adj,
            f_stat=f_stat,
            f_pvalue=f_pvalue,
        )
        result.coefficients = [
            CoefficientRow(
                name=name,
                beta=float(beta[i]),
                std_err=float(se[i]),
                t_stat=float(t_stats[i]),
                p_value=float(p_values[i]),
                ci_low=float(ci_low[i]),
                ci_high=float(ci_high[i]),
            )
            for i, name in enumerate(self._coef_names)
        ]
        result.variance = VarianceInfo(
            row_names=list(self._coef_names),
            values=cov_beta.tolist(),
        )
        result.diagnostics = DiagnosticsInfo(
            residual_df_correction=None,
            warnings=[
                f"Collinear variables dropped: {', '.join(self._colinear_dropped)}"
            ] if self._colinear_dropped else [],
        )
        result.provenance = ProvenanceInfo(
            source="python",
            stata_version_target="17",
            stata_command=f"regress {self.y} {' '.join(self.x)}",
        )
        
        return result
