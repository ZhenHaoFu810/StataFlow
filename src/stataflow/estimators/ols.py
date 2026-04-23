"""
OLS estimator - aligned with Stata's regress command.

Implements ordinary least squares with:
- Sample screening (drop missing)
- Constant term handling
- Collinearity detection
- Result schema output
- Analytical weights (aweight)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional
from types import SimpleNamespace
from stataflow.results.result import (
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
        Weights array or Series. Required when weight_type is set.
    weight_type : str, optional
        Weight type. Currently only "aweight" is supported.
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
        self._collinear_dropped: list[str] = []
        self._weights: Optional[np.ndarray] = None

        # Fitted state
        self._is_fitted: bool = False
        self._beta: Optional[np.ndarray] = None
        self._cov_beta: Optional[np.ndarray] = None
        self._result: Optional[ResultSchema] = None

    def _prepare_data(
        self, cluster_var: Optional[str | list[str]] = None
    ) -> tuple[np.ndarray, np.ndarray, list[bool], Optional[np.ndarray | list[np.ndarray]]]:
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
        cluster : np.ndarray, list[np.ndarray], or None
            Cluster variable values (if provided). For multi-way clustering,
            returns a list of cluster arrays.
        """
        # Select columns
        all_vars = [self.y] + self.x
        if cluster_var is not None:
            if isinstance(cluster_var, str):
                if cluster_var not in all_vars:
                    all_vars.append(cluster_var)
            else:
                for cv in cluster_var:
                    if cv not in all_vars:
                        all_vars.append(cv)

        df = self.data[all_vars].copy()

        n_input_rows = len(df)

        # Handle weights: add weight column to missing check if provided
        weight_arr = None
        if self.weight_type is not None:
            if self.weights is None:
                raise ValueError("weights must be provided when weight_type is set")
            if self.weight_type != "aweight":
                raise ValueError(f"weight_type='{self.weight_type}' not supported in v1. Use 'aweight'.")

            # Convert weights to array
            weight_arr = np.asarray(self.weights, dtype=np.float64)
            if len(weight_arr) != n_input_rows:
                raise ValueError(
                    f"weights length ({len(weight_arr)}) must match data length ({n_input_rows})"
                )

            # Add weights to dataframe for missing check
            df["_stataflow_weights"] = weight_arr

        # Drop missing values
        if self.missing == "drop":
            mask = df.notna().all(axis=1)
            df = df[mask]
        else:
            raise ValueError(f"missing='{self.missing}' not supported in v1")

        sample_mask = mask.tolist()

        # Extract arrays
        y = df[self.y].values.astype(np.float64)

        # Extract weights after missing drop
        if weight_arr is not None:
            weight_arr = df["_stataflow_weights"].values.astype(np.float64)
            # Validate weights are positive
            if np.any(weight_arr <= 0):
                raise ValueError("aweight requires all weights > 0")

            # Normalize weights so that sum(w) = N (Stata aweight convention)
            # w* = w * N / sum(w)
            n_after_drop = len(y)
            weight_arr = weight_arr * n_after_drop / np.sum(weight_arr)
            self._weights = weight_arr

        # Extract cluster variable(s) if provided
        cluster_arr = None
        if cluster_var is not None:
            if isinstance(cluster_var, str):
                cluster_arr = df[cluster_var].values
            else:
                cluster_arr = [df[cv].values for cv in cluster_var]

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
        self._collinear_dropped = dropped

        self._design_matrix = X
        self._dep_var = y
        self._sample_mask = sample_mask
        self._n_input_rows = n_input_rows

        return X, y, sample_mask, cluster_arr

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
        cluster: Optional[str | list[str]] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """
        Fit OLS model.

        Parameters
        ----------
        vce : str
            Variance-covariance estimator type.
            - "ols": conventional homoskedastic (default)
            - "robust": HC1 heteroskedasticity-robust (Stata default)
            - "cluster": cluster-robust (requires cluster parameter)
        cluster : str or list[str], optional
            Cluster variable name(s). Single str for one-way clustering;
            list of two str for two-way clustering (required when vce="cluster").
        alpha : float
            Significance level for confidence intervals.

        Returns
        -------
        ResultSchema
            Fitted result object.
        """
        # Validate inputs
        if vce not in ("ols", "robust", "cluster"):
            raise ValueError(f"vce='{vce}' not supported. Use 'ols', 'robust', or 'cluster'.")
        if vce == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'. Pass cluster='...'.")
        if vce != "cluster" and cluster is not None:
            raise ValueError("cluster only used when vce='cluster'.")
        if isinstance(cluster, list) and len(cluster) != 2:
            raise ValueError("Multi-way clustering currently supports exactly 2 cluster variables.")

        # Prepare data
        X, y, sample_mask, cluster_arr = self._prepare_data(cluster_var=cluster)

        n = len(y)
        k = X.shape[1]
        w = self._weights  # Normalized weights (sum = N), or None

        # Estimation
        if w is not None:
            # Weighted least squares (aweight)
            # beta = (X'WX)^{-1} X'Wy
            sqrt_w = np.sqrt(w)
            X_w = X * sqrt_w[:, np.newaxis]
            y_w = y * sqrt_w
            XtX = X_w.T @ X_w
            Xty = X_w.T @ y_w
        else:
            # Ordinary least squares
            XtX = X.T @ X
            Xty = X.T @ y

        beta = np.linalg.solve(XtX, Xty)

        # Residuals and fitted values
        y_hat = X @ beta
        residuals = y - y_hat

        # Sum of squared residuals and total sum of squares
        if w is not None:
            # aweight: use normalized weights for reported statistics
            # Weighted mean of y (using ORIGINAL weights, before normalization)
            # Since weights are already normalized to sum=N, 
            # y_bar_w = sum(w_orig * y) / sum(w_orig) = sum(w_norm * y) / N
            y_bar_w = np.sum(w * y) / n

            # RSS = sum(w* * e^2)
            rss = float(np.sum(w * residuals ** 2))

            # TSS = sum(w* * (y - y_bar_w)^2)
            if self.add_constant:
                tss = float(np.sum(w * (y - y_bar_w) ** 2))
            else:
                tss = float(np.sum(w * y ** 2))
        else:
            rss = float(np.sum(residuals ** 2))
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
        cluster_count = None
        if vce == "ols":
            # Conventional homoskedastic VCE
            # For aweight: sigma2 = sum(w*e^2) / (N-k)
            sigma2 = rss / df_resid if df_resid > 0 else 0.0
            cov_beta = sigma2 * np.linalg.inv(XtX)
        elif vce == "robust":
            # HC1 robust VCE (Stata default)
            # V_robust = (n / (n-k)) * (X'X)^{-1} (X' Omega X) (X'X)^{-1}
            # where Omega = diag(e_1^2, e_2^2, ..., e_n^2)
            # For aweight: uses weighted X'X inverse
            XtX_inv = np.linalg.inv(XtX)

            # Build Omega = diag(residuals^2)
            # X' Omega X = sum_i (x_i * e_i^2 * x_i')
            e_sq = residuals ** 2
            if w is not None:
                # For weighted regression, apply weight adjustment
                # HC1 with weights: n/(n-k) * (X'WX)^{-1} * (X' W Omega W X) * (X'WX)^{-1}
                # where the "meat" accounts for the weighting
                XtOmegaX = (X_w * e_sq[:, np.newaxis]).T @ X_w
            else:
                XtOmegaX = (X * e_sq[:, np.newaxis]).T @ X

            # HC1 degrees-of-freedom adjustment: n / (n - k)
            hc1_adj = float(n) / float(n - k) if n > k else 1.0

            cov_beta = hc1_adj * XtX_inv @ XtOmegaX @ XtX_inv
        elif vce == "cluster":
            # Cluster-robust VCE (Stata default)
            # V_cluster = (N-1)/(N-k) * G/(G-1) * (X'X)^{-1} * Omega_cluster * (X'X)^{-1}
            # where Omega_cluster = sum_g (X_g' * e_g) * (X_g' * e_g)'
            XtX_inv = np.linalg.inv(XtX)

            n_adj = (n - 1) / (n - k) if n > k else 1.0

            if isinstance(cluster_arr, list):
                # Multi-way clustering (Cameron-Gelbach-Miller 2011)
                # V = V_1 + V_2 - V_12
                cluster_counts = []
                V_parts = []
                for c_arr in cluster_arr:
                    unique_clusters = np.unique(c_arr)
                    G = len(unique_clusters)
                    cluster_counts.append(G)
                    meat = np.zeros((k, k))
                    for g in unique_clusters:
                        mask_g = c_arr == g
                        X_g = X_w[mask_g] if w is not None else X[mask_g]
                        e_g = residuals[mask_g]
                        Xe_g = X_g.T @ e_g
                        meat += np.outer(Xe_g, Xe_g)
                    g_adj = G / (G - 1) if G > 1 else 1.0
                    V_i = n_adj * g_adj * XtX_inv @ meat @ XtX_inv
                    V_parts.append(V_i)

                # Intersection clustering V_12
                c1, c2 = cluster_arr[0], cluster_arr[1]
                # Use tuple-based manual factorization to avoid any separator collision
                combo_to_id = {}
                combo_ids = np.empty(len(c1), dtype=int)
                for i, pair in enumerate(zip(c1, c2)):
                    if pair not in combo_to_id:
                        combo_to_id[pair] = len(combo_to_id)
                    combo_ids[i] = combo_to_id[pair]
                unique_combos = np.unique(combo_ids)
                G_12 = len(unique_combos)
                meat_12 = np.zeros((k, k))
                for combo in unique_combos:
                    mask = combo_ids == combo
                    X_g = X_w[mask] if w is not None else X[mask]
                    e_g = residuals[mask]
                    Xe_g = X_g.T @ e_g
                    meat_12 += np.outer(Xe_g, Xe_g)
                g_adj_12 = G_12 / (G_12 - 1) if G_12 > 1 else 1.0
                V_12 = n_adj * g_adj_12 * XtX_inv @ meat_12 @ XtX_inv

                cov_beta = V_parts[0] + V_parts[1] - V_12
                cluster_count = min(cluster_counts)  # for df_resid
            else:
                # One-way clustering
                unique_clusters = np.unique(cluster_arr)
                cluster_count = len(unique_clusters)

                meat = np.zeros((k, k))
                for g in unique_clusters:
                    mask_g = cluster_arr == g
                    X_g = X_w[mask_g] if w is not None else X[mask_g]
                    e_g = residuals[mask_g]
                    Xe_g = X_g.T @ e_g
                    meat += np.outer(Xe_g, Xe_g)

                g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
                cov_beta = n_adj * g_adj * XtX_inv @ meat @ XtX_inv

            # For cluster VCE, df_resid based on number of clusters
            df_resid = float(cluster_count - 1)
        else:
            raise ValueError(f"vce='{vce}' not implemented")

        # Standard errors
        # Ensure diagonal elements are non-negative
        diag_cov = np.diag(cov_beta)
        diag_cov = np.maximum(diag_cov, 0)  # Clip negative values to 0
        se = np.sqrt(diag_cov)

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
        if self.add_constant and df_model > 0:
            if vce == "ols":
                # Conventional F-statistic
                f_stat = (mss / df_model) / (rss / df_resid)
                from scipy.stats import f as f_dist
                f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
            elif vce == "robust":
                # Wald F-statistic for robust VCE
                # F = (1/df_model) * 尾' * V_rob^{-1} * 尾
                # where 尾 excludes the constant term
                # Find index of constant (if present)
                const_idx = self._coef_names.index("_cons") if "_cons" in self._coef_names else -1

                # Get slope coefficients (exclude constant)
                if const_idx >= 0:
                    slope_idx = [i for i in range(k) if i != const_idx]
                else:
                    slope_idx = list(range(k))

                beta_slopes = beta[slope_idx]
                cov_slopes = cov_beta[np.ix_(slope_idx, slope_idx)]

                # Wald statistic: 尾' * V^{-1} * 尾
                try:
                    cov_inv = np.linalg.inv(cov_slopes)
                    wald_stat = float(beta_slopes @ cov_inv @ beta_slopes)
                    # F = Wald / df_model
                    f_stat = wald_stat / df_model
                    from scipy.stats import f as f_dist
                    f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
                except np.linalg.LinAlgError:
                    # Covariance matrix is singular
                    f_stat = None
                    f_pvalue = None
            elif vce == "cluster":
                # Wald F-statistic for cluster VCE (same formula as robust)
                const_idx = self._coef_names.index("_cons") if "_cons" in self._coef_names else -1

                if const_idx >= 0:
                    slope_idx = [i for i in range(k) if i != const_idx]
                else:
                    slope_idx = list(range(k))

                beta_slopes = beta[slope_idx]
                cov_slopes = cov_beta[np.ix_(slope_idx, slope_idx)]

                try:
                    cov_inv = np.linalg.inv(cov_slopes)
                    wald_stat = float(beta_slopes @ cov_inv @ beta_slopes)
                    f_stat = wald_stat / df_model
                    from scipy.stats import f as f_dist
                    f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
                except np.linalg.LinAlgError:
                    f_stat = None
                    f_pvalue = None
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
            cluster_var=cluster if vce == "cluster" else None,
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
            cluster_count=cluster_count,
            warnings=[
                f"Collinear variables dropped: {', '.join(self._collinear_dropped)}"
            ] if self._collinear_dropped else [],
        )
        result.provenance = ProvenanceInfo(
            source="python",
            stata_version_target="17",
            stata_command=f"regress {self.y} {' '.join(self.x)}",
        )

        # Store fitted state for postestimation
        self._is_fitted = True
        self._beta = beta
        self._cov_beta = cov_beta
        self._result = result

        return result

    def predict(self, type: str = "xb", newdata: Optional[pd.DataFrame] = None) -> np.ndarray:
        """
        Generate predictions after fitting.

        Parameters
        ----------
        type : str
            Prediction type. "xb" or "residuals".
        newdata : pd.DataFrame, optional
            New data for out-of-sample prediction. If None, uses fitted sample.

        Returns
        -------
        np.ndarray
            Prediction vector.
        """
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        if type not in ("xb", "residuals"):
            raise ValueError(f"type='{type}' not supported for OLS. Use 'xb' or 'residuals'.")

        if newdata is not None:
            df = newdata[self.x].copy()
            if self.add_constant:
                df["_cons"] = 1.0
            X = df.values.astype(np.float64)
            # Align coefficients to columns (account for collinearity drops in fit)
            beta = np.zeros(X.shape[1])
            for i, name in enumerate((self.x + ["_cons"]) if self.add_constant else self.x):
                # If variable was dropped due to collinearity, coefficient remains 0
                if name in self._coef_names:
                    beta[i] = self._beta[self._coef_names.index(name)]
            xb = X @ beta
            if type == "residuals":
                y = newdata[self.y].values.astype(np.float64)
                return y - xb
            return xb
        else:
            xb = self._design_matrix @ self._beta
            if type == "residuals":
                return self._dep_var - xb
            return xb

    def margins(self, type: str = "dydx") -> SimpleNamespace:
        """
        Compute marginal effects for linear model.

        Parameters
        ----------
        type : str
            "dydx" for average marginal effect (equal to coefficients),
            "atmeans" for marginal effect at means (also equal to coefficients).

        Returns
        -------
        SimpleNamespace
            Margins result object.
        """
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        from stataflow.postestimation import margins_ame_linear, _build_margins_result

        effects = margins_ame_linear(self._beta)
        k = len(self._beta)
        J = np.eye(k)
        return _build_margins_result(
            effects, J, self._cov_beta, self._coef_names, self._result.sample.nobs
        )
