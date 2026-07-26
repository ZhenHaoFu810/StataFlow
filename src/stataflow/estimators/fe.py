"""
FixedEffectsOLS estimator - aligned with Stata's xtreg, fe command.

Implements fixed effects (within) regression for panel data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional
from types import SimpleNamespace
from scipy.stats import t as t_dist, f as f_dist
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


class FixedEffectsOLS:
    """
    Fixed Effects (Within) estimator aligned with Stata's xtreg, fe.

    Parameters
    ----------
    data : pd.DataFrame
        Panel data.
    y : str
        Dependent variable name.
    x : list[str]
        Independent variable names (time-varying).
    fe : str
        Fixed effect variable name (entity identifier).
    add_constant : bool, default False
        Whether to report a constant (grand mean of entity effects).
        Default False to avoid confusion with within transformation.
    weights : array-like, optional
        Not supported in v1.
    weight_type : str, optional
        Not supported in v1.
    missing : str, default "drop"
        Missing value handling. Only "drop" is supported in v1.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y: str,
        x: list[str],
        fe: str,
        add_constant: bool = False,
        weights=None,
        weight_type: Optional[str] = None,
        missing: str = "drop",
    ):
        self.data = data
        self.y = y
        self.x = list(x)
        self.fe = fe
        self.add_constant = add_constant
        self.weights = weights
        self.weight_type = weight_type
        self.missing = missing

        if weight_type is not None:
            raise ValueError(f"weight_type='{weight_type}' not supported for FE in v1")
        if weights is not None:
            raise ValueError("weights not supported for FE in v1")

        # Internal state
        self._coef_names: list[str] = []
        self._active_x: list[str] = []
        self._n_entities: int = 0
        self._n_input_rows: int = 0

        # Fitted state
        self._is_fitted: bool = False
        self._beta: Optional[np.ndarray] = None
        self._cov_beta: Optional[np.ndarray] = None
        self._result: Optional[ResultSchema] = None
        self._df_clean: Optional[pd.DataFrame] = None
        self._entity_effects: Optional[pd.Series] = None
        self._constant: float = 0.0
        self._y_w: Optional[np.ndarray] = None
        self._X_w: Optional[np.ndarray] = None

    def _prepare_data(self, cluster_var: Optional[str] = None) -> tuple[
        pd.DataFrame, np.ndarray, np.ndarray, list[bool], Optional[np.ndarray]
    ]:
        """
        Prepare data and apply within transformation.

        Returns
        -------
        df_clean : pd.DataFrame
            Cleaned data after missing drop.
        y_w : np.ndarray
            Within-transformed dependent variable.
        X_w : np.ndarray
            Within-transformed design matrix (no constant).
        sample_mask : list[bool]
            Boolean mask of retained observations.
        cluster_arr : np.ndarray or None
            Cluster variable values (if provided).
        """
        # Select columns
        all_vars = [self.y, self.fe] + self.x
        if cluster_var is not None and cluster_var not in all_vars:
            all_vars.append(cluster_var)

        df = self.data[all_vars].copy()
        self._n_input_rows = len(df)

        # Drop missing values
        if self.missing == "drop":
            mask = df.notna().all(axis=1)
            df = df[mask]
        else:
            raise ValueError(f"missing='{self.missing}' not supported in v1")

        sample_mask = mask.tolist()
        self._n_entities = df[self.fe].nunique()

        # Extract arrays
        y = df[self.y].values.astype(np.float64)
        df[self.fe].values

        # Extract cluster variable if provided
        cluster_arr = None
        if cluster_var is not None:
            cluster_arr = df[cluster_var].values

        # Build design matrix (raw, before within transformation)
        X_cols = []
        self._coef_names = []
        for var in self.x:
            X_cols.append(df[var].values.astype(np.float64))
            self._coef_names.append(var)

        X = np.column_stack(X_cols) if X_cols else np.zeros((len(df), 0))

        # Within transformation (demean by entity)
        df_temp = df.copy()
        df_temp['_y'] = y
        for i, var in enumerate(self.x):
            df_temp[f'_X_{i}'] = X[:, i]

        # Entity means
        entity_means = df_temp.groupby(self.fe).transform('mean')

        # Demean
        y_w = y - entity_means['_y'].values
        if len(self.x) > 0:
            X_w = np.column_stack([
                X[:, i] - entity_means[f'_X_{i}'].values
                for i in range(len(self.x))
            ])
        else:
            X_w = np.zeros((len(y_w), 0))

        if len(y_w) == 0:
            raise ValueError("No observations remain after sample screening (all rows have missing values).")
        if X_w.shape[1] == 0:
            raise ValueError("Design matrix has 0 columns after sample screening. No regressors available.")

        return df, y_w, X_w, sample_mask, cluster_arr

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """
        Fit fixed effects model.

        Parameters
        ----------
        vce : str
            Variance-covariance estimator type.
            - "ols": conventional homoskedastic (default)
            - "cluster": cluster-robust (requires cluster parameter)
        cluster : str, optional
            Cluster variable name (required when vce="cluster").
        alpha : float
            Significance level for confidence intervals.

        Returns
        -------
        ResultSchema
            Fitted result object.
        """
        # Validate inputs
        if vce not in ("ols", "robust", "cluster"):
            raise ValueError(f"vce='{vce}' not supported for FE. Use 'ols', 'robust', or 'cluster'.")
        if vce == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'. Pass cluster='...'.")
        if vce not in ("cluster", "robust") and cluster is not None:
            raise ValueError("cluster only used when vce='cluster' or vce='robust'.")

        # Prepare data and apply within transformation
        df_clean, y_w, X_w, sample_mask, cluster_arr = self._prepare_data(cluster_var=cluster)
        self._df_clean = df_clean
        self._y_w = y_w
        self._X_w = X_w

        n = len(y_w)  # N after drop
        G = self._n_entities  # Number of groups
        k = X_w.shape[1]  # Number of slope parameters

        # Stata xtreg, fe robust is panel-robust: same meat/multiplier as
        # cluster(panel_id). Keep reported vcetype="robust" (not cluster).
        panel_robust = vce == "robust"
        vce_eff = "cluster" if (vce == "cluster" or panel_robust) else vce
        if panel_robust:
            cluster_arr = df_clean[self.fe].to_numpy()

        # Detect within-collinearity (group-invariant variables become collinear)
        from stataflow.estimators._vce_utils import detect_collinear_columns
        X_w, dropped_cols, kept_indices = detect_collinear_columns(X_w, self._coef_names)
        if dropped_cols:
            self._coef_names = [self._coef_names[i] for i in kept_indices]
        if X_w.shape[1] == 0:
            raise ValueError("All regressors are collinear after within transformation")
        k = X_w.shape[1]
        self._active_x = list(self._coef_names)
        self._X_w = X_w

        # OLS on within-transformed data
        XtX = X_w.T @ X_w
        Xty = X_w.T @ y_w
        beta = np.linalg.solve(XtX, Xty)

        # Residuals and fitted values (on within-transformed scale)
        y_hat_w = X_w @ beta
        residuals_w = y_w - y_hat_w

        # Sum of squared residuals (from within regression)
        rss = float(np.sum(residuals_w ** 2))

        # Total sum of squares (within): sum of (y_w)^2
        tss_w = float(np.sum(y_w ** 2))
        mss_w = tss_w - rss

        # Within R-squared
        r2 = 1.0 - rss / tss_w if tss_w > 0 else 0.0

        # Degrees of freedom (Stata xtreg, fe convention)
        # For non-cluster FE: df_model = k + (G - 1), df_resid = N - G - k
        # For FE + cluster / panel-robust: e(df_m) as rank-1 style; df_resid = G_clust-1
        if vce_eff == "cluster":
            df_model_fe = float(max(k - 1, 0))
        else:
            df_model_fe = float(k + (G - 1))
        df_resid_fe = float(n - G - k)

        # RMSE
        if vce_eff == "cluster":
            # For FE + cluster, RMSE uses (N - k - 1) denominator (Stata convention)
            rmse = np.sqrt(rss / (n - k - 1)) if (n - k - 1) > 0 else 0.0
        else:
            rmse = np.sqrt(rss / df_resid_fe) if df_resid_fe > 0 else 0.0

        # Adjusted within R-squared. Clustered / panel-robust xtreg uses N-k-1.
        r2_adj_denominator = (n - k - 1) if vce_eff == "cluster" else df_resid_fe
        r2_adj = (
            1.0 - (1.0 - r2) * (n - 1) / r2_adj_denominator
            if r2_adj_denominator > 0
            else 0.0
        )

        # Variance-covariance matrix
        cluster_count = None
        sigma_e2 = rss / df_resid_fe if df_resid_fe > 0 else 0.0

        if vce_eff == "ols":
            # Conventional homoskedastic VCE
            cov_beta = sigma_e2 * np.linalg.inv(XtX)
        elif vce_eff == "cluster":
            # Cluster-robust / panel-robust VCE (Stata xtreg, fe robust ≡ cluster panel)
            XtX_inv = np.linalg.inv(XtX)

            from stataflow.estimators._vce_utils import compute_cluster_meat
            meat, cluster_count = compute_cluster_meat(X_w, residuals_w, cluster_arr)

            # Stata xtreg, fe vce(cluster) uses: G/(G-1) * (N-1)/(N-k-1)
            n_adj = (n - 1) / (n - k - 1) if n > k + 1 else 1.0
            g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
            cov_beta = n_adj * g_adj * XtX_inv @ meat @ XtX_inv

            df_resid_fe = float(cluster_count - 1)
            rmse = np.sqrt(rss / (n - k - 1)) if (n - k - 1) > 0 else 0.0
        else:
            raise ValueError(f"Internal VCE path error: vce_eff={vce_eff!r}")

        # Standard errors
        diag_cov = np.diag(cov_beta)
        diag_cov = np.maximum(diag_cov, 0)
        se = np.sqrt(diag_cov)

        # t-statistics and p-values
        t_stats = beta / se
        p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=df_resid_fe))

        # Confidence intervals
        t_crit = t_dist.ppf(1 - alpha / 2, df=df_resid_fe)
        ci_low = beta - t_crit * se
        ci_high = beta + t_crit * se

        # F-statistic: F(k, df_resid) testing all slope coefficients = 0
        if k > 0 and df_resid_fe > 0:
            if vce_eff == "ols":
                if rss == 0:
                    f_stat = float("inf")
                    f_pvalue = 0.0
                else:
                    f_stat = (mss_w / k) / (rss / df_resid_fe)
                    f_pvalue = 1 - f_dist.cdf(
                        f_stat, dfn=df_model_fe, dfd=df_resid_fe
                    )
            else:
                # Wald F for cluster / panel-robust
                try:
                    cov_inv = np.linalg.inv(cov_beta)
                    wald_stat = float(beta @ cov_inv @ beta)
                    f_stat = wald_stat / k
                    f_pvalue = 1 - f_dist.cdf(f_stat, dfn=k, dfd=df_resid_fe)
                except np.linalg.LinAlgError:
                    f_stat = None
                    f_pvalue = None
        else:
            f_stat = None
            f_pvalue = None

        # Build coefficient rows
        # Optionally add _cons (grand mean of entity effects)
        coef_rows = []
        for i, name in enumerate(self._coef_names):
            coef_rows.append(CoefficientRow(
                name=name,
                beta=float(beta[i]),
                std_err=float(se[i]),
                t_stat=float(t_stats[i]),
                p_value=float(p_values[i]),
                ci_low=float(ci_low[i]),
                ci_high=float(ci_high[i]),
            ))

        # Recover entity effects for postestimation
        entity_means = df_clean.groupby(self.fe)[[self.y] + self._coef_names].mean()
        alpha_i = entity_means[self.y].values - entity_means[self._coef_names].values @ beta
        self._entity_effects = pd.Series(alpha_i, index=entity_means.index)

        # Add constant (grand mean) if requested
        cov_beta_cons = None
        if self.add_constant:
            # Stata reports ybar - xbar*b, which is the observation-weighted
            # mean of the recovered entity effects on unbalanced panels.
            grand_mean = float(
                df_clean[self.y].mean()
                - df_clean[self._coef_names].mean().to_numpy() @ beta
            )
            self._constant = grand_mean

            # Build LSDV design matrix for consistent VCE expansion
            unique_entities = df_clean[self.fe].unique()
            G = len(unique_entities)
            D = np.zeros((n, G))
            for j, entity in enumerate(unique_entities):
                D[df_clean[self.fe].values == entity, j] = 1

            X_full = np.column_stack([df_clean[self._coef_names].values, D])
            y_orig = df_clean[self.y].values.astype(np.float64)
            beta_full = np.linalg.solve(X_full.T @ X_full, X_full.T @ y_orig)
            residuals_full = y_orig - X_full @ beta_full
            XtX_inv_full = np.linalg.inv(X_full.T @ X_full)

            if vce_eff == "cluster":
                from stataflow.estimators._vce_utils import compute_cluster_meat
                meat_full, cluster_count_for_lsdv = compute_cluster_meat(
                    X_full, residuals_full, cluster_arr
                )
                n_adj_lsdv = (n - 1) / (n - k - 1) if n > k + 1 else 1.0
                g_adj_lsdv = (
                    cluster_count_for_lsdv / (cluster_count_for_lsdv - 1)
                    if cluster_count_for_lsdv > 1
                    else 1.0
                )
                V_full = n_adj_lsdv * g_adj_lsdv * XtX_inv_full @ meat_full @ XtX_inv_full
            else:
                sigma2_full = np.sum(residuals_full ** 2) / (n - G - k) if (n - G - k) > 0 else 0.0
                V_full = sigma2_full * XtX_inv_full

            # Extract Var(grand_mean) and Cov(beta_slopes, grand_mean)
            V_alpha = V_full[k:, k:]
            entity_weights = np.array([
                np.mean(df_clean[self.fe].to_numpy() == entity)
                for entity in unique_entities
            ])
            var_grand_mean = float(entity_weights @ V_alpha @ entity_weights)
            se_grand_mean = np.sqrt(max(var_grand_mean, 0))
            Cov_beta_alpha = V_full[:k, k:]
            cov_beta_cons = Cov_beta_alpha @ entity_weights

            t_stat_grand = grand_mean / se_grand_mean
            p_value_grand = 2 * (1 - t_dist.cdf(np.abs(t_stat_grand), df=df_resid_fe))
            ci_low_grand = grand_mean - t_crit * se_grand_mean
            ci_high_grand = grand_mean + t_crit * se_grand_mean

            coef_rows.append(CoefficientRow(
                name="_cons",
                beta=grand_mean,
                std_err=se_grand_mean,
                t_stat=t_stat_grand,
                p_value=p_value_grand,
                ci_low=ci_low_grand,
                ci_high=ci_high_grand,
            ))

        # Expand VCE to include _cons if present
        if self.add_constant and cov_beta_cons is not None:
            k_ext = k + 1
            new_cov = np.zeros((k_ext, k_ext))
            new_cov[:k, :k] = cov_beta
            new_cov[:k, k] = cov_beta_cons
            new_cov[k, :k] = cov_beta_cons
            new_cov[k, k] = var_grand_mean
            cov_beta = new_cov
            self._coef_names = self._coef_names + ["_cons"]

        # Build result object
        result = ResultSchema()
        result.model = ModelInfo(
            command="xtreg",
            estimator_family="fe",
            # Report user-facing VCE label: robust stays "robust" even though
            # the sandwich is panel-clustered (Stata xtreg, fe robust contract).
            vcetype=vce,
            weight_type=self.weight_type,
            fe_vars=[self.fe],
            has_constant=self.add_constant,
            cluster_var=cluster if vce == "cluster" else None,
        )
        result.sample = SampleInfo(
            nobs=n,
            n_input_rows=self._n_input_rows,
            sample_mask=sample_mask,
        )
        result.fit = FitInfo(
            df_model=df_model_fe,
            df_resid=df_resid_fe,
            rank=k,  # Only slope parameters
            rss=rss,
            tss=tss_w,
            mss=mss_w,
            rmse=rmse,
            r2=r2,
            r2_adj=r2_adj,
            f_stat=f_stat,
            f_pvalue=f_pvalue,
        )
        result.coefficients = coef_rows
        result.variance = VarianceInfo(
            row_names=list(self._coef_names),
            values=cov_beta.tolist(),
        )
        result.diagnostics = DiagnosticsInfo(
            residual_df_correction="within",
            cluster_count=cluster_count,
            warnings=[],
        )
        result.provenance = ProvenanceInfo(
            source="python",
            stata_version_target="17",
            stata_command=f"xtreg {self.y} {' '.join(self.x)}, fe",
        )

        # Store fitted state for postestimation
        self._is_fitted = True
        self._beta = beta
        self._cov_beta = cov_beta
        self._result = result
        result._model = self

        result.validate()
        return result

    def predict(self, type: str = "xb", newdata: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Generate predictions after fitting.

        Matches Stata's xtreg, fe semantics:
        - predict, xb returns x*b + _cons (grand mean of entity effects)
        - predict, residuals returns y - xb
        """
        if not self._is_fitted:
            raise ValueError("Model has not been fitted. Call fit() first.")
        if type not in ("xb", "residuals"):
            raise ValueError(f"type='{type}' not supported for FE. Use 'xb' or 'residuals'.")

        grand_mean = self._constant

        if newdata is not None:
            required_cols = (
                [self.y] + self._active_x
                if type == "residuals"
                else self._active_x
            )
            df = newdata[required_cols].copy()
            mask = df.notna().all(axis=1)
            if not mask.all():
                # Stata-compatible: drop missing and predict on complete cases
                df = df[mask]
            X = df[self._active_x].values.astype(np.float64)
            xb = X @ self._beta + (grand_mean if self.add_constant else 0.0)
            if type == "residuals":
                y = df[self.y].values.astype(np.float64)
                return y - xb
            return xb
        else:
            xb = self._df_clean[self._active_x].values.astype(np.float64) @ self._beta
            xb = xb + (grand_mean if self.add_constant else 0.0)
            if type == "xb":
                return xb
            else:
                y = self._df_clean[self.y].values.astype(np.float64)
                return y - xb

    def margins(self, type: str = "dydx") -> SimpleNamespace:
        """Compute marginal effects."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted. Call fit() first.")
        from stataflow.postestimation import margins_ame_linear, _build_margins_result

        effects = margins_ame_linear(self._beta)
        k = len(self._beta)
        J = np.eye(k)
        return _build_margins_result(
            effects, J, self._cov_beta, self._coef_names, self._result.sample.nobs
        )
