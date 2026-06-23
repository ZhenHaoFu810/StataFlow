"""
IV estimators - aligned with Stata's ivregress 2sls and ivreghdfe commands.

Implements two-stage least squares (2SLS) with:
- Sample screening (drop missing)
- Constant term handling
- Collinearity detection
- Conventional, robust, and cluster-robust VCE
- Result schema output
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.linalg
from scipy.stats import t as t_dist, f as f_dist, chi2
from typing import Optional
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


class IV2SLS:
    """
    Two-Stage Least Squares estimator aligned with Stata's ivregress 2sls.

    Parameters
    ----------
    data : pd.DataFrame
        Input data.
    y : str
        Dependent variable name.
    x_exog : list[str]
        Exogenous regressor names (included instruments).
    x_endog : list[str]
        Endogenous regressor names.
    instruments : list[str]
        Excluded instrument names.
    add_constant : bool, default True
        Whether to add constant term.
    missing : str, default "drop"
        Missing value handling. Only "drop" is supported.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y: str,
        x_exog: list[str],
        x_endog: list[str],
        instruments: list[str],
        add_constant: bool = True,
        missing: str = "drop",
    ):
        self.data = data
        self.y = y
        self.x_exog = list(x_exog)
        self.x_endog = list(x_endog)
        self.instruments = list(instruments)
        self.add_constant = add_constant
        self.missing = missing

        # Internal state
        self._design_matrix: Optional[np.ndarray] = None
        self._dep_var: Optional[np.ndarray] = None
        self._sample_mask: Optional[list[bool]] = None
        self._coef_names: list[str] = []
        self._collinear_dropped: list[str] = []
        self._n_input_rows: int = 0
        self._cluster_arr: Optional[np.ndarray] = None

    def _prepare_data(
        self, cluster_var: Optional[str] = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[bool], Optional[np.ndarray]]:
        """
        Prepare design matrices and dependent variable for 2SLS.

        Returns
        -------
        X : np.ndarray
            Regressor matrix (n x k_x).
        Z : np.ndarray
            Instrument matrix (n x k_z).
        y : np.ndarray
            Dependent variable (n,).
        sample_mask : list[bool]
            Boolean mask of retained observations.
        cluster_arr : np.ndarray or None
            Cluster variable values (if provided).
        """
        all_vars = [self.y] + self.x_exog + self.x_endog + self.instruments
        if cluster_var is not None and cluster_var not in all_vars:
            all_vars.append(cluster_var)

        df = self.data[all_vars].copy()
        n_input_rows = len(df)

        # Drop missing values
        if self.missing == "drop":
            mask = df.notna().all(axis=1)
            df = df[mask]
        else:
            raise ValueError(f"missing='{self.missing}' not supported")

        sample_mask = mask.tolist()

        y = df[self.y].values.astype(np.float64)

        # Extract cluster variable if provided
        cluster_arr = None
        if cluster_var is not None:
            cluster_arr = df[cluster_var].values

        # Build regressor matrix X = [x_endog, x_exog, constant]
        x_names = []
        X_cols = []
        for var in self.x_endog:
            X_cols.append(df[var].values.astype(np.float64))
            x_names.append(var)
        for var in self.x_exog:
            X_cols.append(df[var].values.astype(np.float64))
            x_names.append(var)
        if self.add_constant:
            X_cols.append(np.ones(len(df)))
            x_names.append("_cons")
        X = np.column_stack(X_cols) if X_cols else np.zeros((len(df), 0))

        # Build instrument matrix Z = [instruments, x_exog, constant]
        z_names = []
        Z_cols = []
        for var in self.instruments:
            Z_cols.append(df[var].values.astype(np.float64))
            z_names.append(var)
        for var in self.x_exog:
            Z_cols.append(df[var].values.astype(np.float64))
            z_names.append(var)
        if self.add_constant:
            Z_cols.append(np.ones(len(df)))
            z_names.append("_cons")
        Z = np.column_stack(Z_cols) if Z_cols else np.zeros((len(df), 0))

        # Detect collinearity in X first, then in the combined [X, instruments] matrix
        # to catch instruments that are collinear with X regressors (IV-04).
        X, dropped_x, kept_x = self._detect_collinearity(X, x_names)
        self._coef_names = [x_names[i] for i in kept_x]

        # Build unique instrument columns (those not already in X)
        inst_only_names = []
        inst_only_cols = []
        for var in self.instruments:
            if var not in x_names:
                inst_only_names.append(var)
                inst_only_cols.append(df[var].values.astype(np.float64))
        if inst_only_cols:
            inst_only = np.column_stack(inst_only_cols)
            xz = np.column_stack([X, inst_only])
            xz_names = self._coef_names + inst_only_names
            _, dropped_xz, kept_xz = self._detect_collinearity(xz, xz_names)
            # Kept X columns are the ones in kept_xz that are < X.shape[1]
            # Kept instruments are the ones in kept_xz that are >= X.shape[1]
            kept_inst_names = [xz_names[i] for i in kept_xz if i >= X.shape[1]]
        else:
            kept_inst_names = []

        # Z keeps: x_exog (same as X), constant (same as X), and kept instruments
        kept_z = []
        for i, name in enumerate(z_names):
            if name in self._coef_names:
                kept_z.append(i)
            elif name in kept_inst_names:
                kept_z.append(i)

        dropped_z = [z_names[i] for i in range(len(z_names)) if i not in kept_z]
        self._collinear_dropped = dropped_x + dropped_z
        self._inst_names = [z_names[i] for i in kept_z]

        # Filter Z to remove collinear columns before returning
        if kept_z:
            Z = Z[:, kept_z]

        self._design_matrix = X
        self._dep_var = y
        self._sample_mask = sample_mask
        self._n_input_rows = n_input_rows

        return X, Z, y, sample_mask, cluster_arr

    def _detect_collinearity(
        self, X: np.ndarray, names: list[str]
    ) -> tuple[np.ndarray, list[str], list[int]]:
        from stataflow.estimators._vce_utils import detect_collinear_columns
        return detect_collinear_columns(X, names)

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
        first: bool = False,
    ) -> ResultSchema:
        """
        Fit 2SLS model.

        Parameters
        ----------
        vce : str
            Variance-covariance estimator type: "ols", "robust", or "cluster".
        cluster : str, optional
            Cluster variable name (required when vce="cluster").
        alpha : float
            Significance level for confidence intervals.
        first : bool
            If True, compute and attach first-stage F-statistics.

        Returns
        -------
        ResultSchema
            Fitted result object.
        """
        if vce not in ("ols", "robust", "cluster"):
            raise ValueError(f"vce='{vce}' not supported. Use 'ols', 'robust', or 'cluster'.")
        if vce == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'.")
        if vce != "cluster" and cluster is not None:
            raise ValueError("cluster only used when vce='cluster'.")

        X, Z, y, sample_mask, cluster_arr = self._prepare_data(cluster_var=cluster)
        if len(y) == 0:
            raise ValueError("No observations remain after sample screening (all rows have missing values).")
        if X.shape[1] == 0:
            raise ValueError("Design matrix has 0 columns after sample screening. No regressors available.")
        n = len(y)
        k_x = X.shape[1]
        k_z = Z.shape[1]

        if k_z < k_x:
            raise ValueError(f"Underidentified: need at least {k_x} instruments, have {k_z}")

        #        # First stage: project X onto Z
        ZtZ = Z.T @ Z
        ZtX = Z.T @ X
        Pi = np.linalg.solve(ZtZ, ZtX)
        X_proj = Z @ Pi

        # Second stage: OLS of y on X_proj
        XtX_proj = X_proj.T @ X_proj
        Xty_proj = X_proj.T @ y
        beta = np.linalg.solve(XtX_proj, Xty_proj)

        # Structural residuals (using original X, not projected)
        residuals = y - X @ beta

        # TSS
        if self.add_constant:
            y_mean = np.mean(y)
            tss = float(np.sum((y - y_mean) ** 2))
        else:
            tss = float(np.sum(y ** 2))

        # Structural RSS (for R虏, RMSE, and VCE)
        rss = float(np.sum(residuals ** 2))
        mss = tss - rss

        # Degrees of freedom
        df_model = float(k_x - 1) if self.add_constant else float(k_x)

        # Stata ivregress 2sls uses asymptotic z-stats for all VCE types
        df_resid = None
        df_stat = float('inf')  # normal distribution

        # R-squared (Stata uses structural residuals for ivregress)
        r2 = 1.0 - rss / tss if tss > 0 else 0.0

        # RMSE (from structural residuals)
        # Stata ivregress uses N for RMSE in 2SLS, not N-k
        rmse = np.sqrt(rss / n) if n > 0 else 0.0

        # Adjusted R-squared: Stata uses n-k for adj R2 even though RMSE uses n
        df_adj_r2 = float(n - k_x)
        r2_adj = 1.0 - (1.0 - r2) * (n - 1) / df_adj_r2 if df_adj_r2 > 0 else 0.0

        # Variance-covariance matrix
        cluster_count = None
        M_inv = np.linalg.inv(XtX_proj)

        if vce == "ols":
            # Stata conventional VCE for 2SLS uses sigma2 = rss / n (no small-sample correction)
            sigma2 = rss / n if n > 0 else 0.0
            cov_beta = sigma2 * M_inv
        elif vce == "robust":
            # ivregress 2sls, vce(robust) does NOT apply HC1 small-sample correction
            e_sq = residuals ** 2
            XtOmegaX = (X_proj * e_sq[:, np.newaxis]).T @ X_proj
            cov_beta = M_inv @ XtOmegaX @ M_inv
        else:  # cluster
            unique_clusters = np.unique(cluster_arr)
            cluster_count = len(unique_clusters)
            if cluster_count <= 1:
                raise ValueError(
                    f"cluster-robust VCE requires at least 2 clusters, found {cluster_count}"
                )

            meat = np.zeros((k_x, k_x))
            for g in unique_clusters:
                mask_g = cluster_arr == g
                X_g = X_proj[mask_g]
                e_g = residuals[mask_g]
                Xe_g = X_g.T @ e_g
                meat += np.outer(Xe_g, Xe_g)

            # ivregress 2sls, vce(cluster) does NOT apply n_adj or g_adj
            cov_beta = M_inv @ meat @ M_inv

        # Standard errors
        diag_cov = np.diag(cov_beta)
        diag_cov = np.maximum(diag_cov, 0)
        se = np.sqrt(diag_cov)

        # Statistics and inference
        if vce == "ols":
            from scipy.stats import t as t_dist, f as f_dist
            df_resid = n - k_x
            stats = beta / se
            p_values = 2 * (1 - t_dist.cdf(np.abs(stats), df=df_resid))
            crit = t_dist.ppf(1 - alpha / 2, df=df_resid)
            # F-statistic for vce=ols
            if self.add_constant and k_x > 1 and df_resid > 0 and rss > 0:
                f_stat = (mss / df_model) / (rss / df_resid)
                f_pvalue = float(1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid))
            else:
                f_stat = None
                f_pvalue = None
        else:
            from scipy.stats import norm
            stats = beta / se
            p_values = 2 * (1 - norm.cdf(np.abs(stats)))
            crit = norm.ppf(1 - alpha / 2)
            f_stat = None
            f_pvalue = None

        # Confidence intervals
        ci_low = beta - crit * se
        ci_high = beta + crit * se

        # First-stage statistics and overidentification test
        extra_stats = {}
        first_stage: dict[str, dict] = {}
        if first:
            from scipy.stats import f as f_dist
            # Number of excluded instruments
            k_excl = len(self.instruments)
            # Use coef_names to locate variables after collinearity drops
            exog_kept = [name for name in self.x_exog if name in self._coef_names]
            endog_kept = [name for name in self.x_endog if name in self._coef_names]
            k_exog = len(exog_kept)
            # Endogenous variable indices in X (after constant if present)
            endog_start = k_exog + (1 if self.add_constant else 0)
            for j, endog_name in enumerate(endog_kept):
                endog_idx = self._coef_names.index(endog_name)
                x_j = X[:, endog_idx]
                x_hat_j = X_proj[:, endog_idx]
                # First-stage regression of x_j on Z
                beta_fs = np.linalg.solve(ZtZ, Z.T @ x_j)
                resid_fs = x_j - Z @ beta_fs
                RSS_full = float(np.sum(resid_fs ** 2))
                TSS = float(np.sum((x_j - np.mean(x_j)) ** 2))
                R2 = 1.0 - RSS_full / TSS if TSS > 0 else 0.0
                # Restricted model: x_j on exogenous vars (and constant)
                if k_exog > 0 or self.add_constant:
                    W_cols = []
                    if self.add_constant:
                        W_cols.append(np.ones(n))
                    for exog_name in exog_kept:
                        idx = self._coef_names.index(exog_name)
                        W_cols.append(X[:, idx])
                    W = np.column_stack(W_cols)
                    beta_r = np.linalg.solve(W.T @ W, W.T @ x_j)
                    resid_r = x_j - W @ beta_r
                else:
                    resid_r = x_j
                RSS_r = float(np.sum(resid_r ** 2))
                R2_r = 1.0 - RSS_r / TSS if TSS > 0 else 0.0
                partial_R2 = (R2 - R2_r) / (1.0 - R2_r) if R2_r < 1.0 else 0.0
                # Shea partial R2
                if len(endog_kept) == 1:
                    shea_R2 = partial_R2
                else:
                    var_x_hat = np.var(x_hat_j, ddof=0)
                    var_x = np.var(x_j, ddof=0)
                    shea_R2 = (var_x_hat / var_x) * partial_R2 if var_x > 0 else 0.0
                q = k_excl
                df_denom = n - Z.shape[1]
                f_stat = None
                f_pvalue = None
                if q > 0 and df_denom > 0 and RSS_full > 0:
                    f_stat = ((RSS_r - RSS_full) / q) / (RSS_full / df_denom)
                    f_pvalue = float(1 - f_dist.cdf(f_stat, dfn=q, dfd=df_denom))
                first_stage[endog_name] = {
                    "r2": R2,
                    "partial_r2": partial_R2,
                    "shea_r2": shea_R2,
                    "f_stat": f_stat,
                    "f_pvalue": f_pvalue,
                    "df": q,
                    "df_r": df_denom,
                }

        # Overidentification test (Sargan/Hansen J)
        k_excl = len(self.instruments)
        k_endog = len(self.x_endog)
        if k_excl > k_endog:
            from scipy.stats import chi2
            j_df = k_excl - k_endog
            # Regression of residuals on instruments
            beta_ez = np.linalg.solve(ZtZ, Z.T @ residuals)
            resid_ez = residuals - Z @ beta_ez
            rss_ez = float(np.sum(resid_ez ** 2))
            tss_e = float(np.sum(residuals ** 2))
            if tss_e > 0:
                if vce == "ols":
                    # Sargan statistic: n * R^2 from residual regression
                    r2_sargan = 1.0 - rss_ez / tss_e
                    sargan = float(n * r2_sargan)
                    p_sargan = float(1 - chi2.cdf(sargan, df=j_df))
                    extra_stats["sargan"] = sargan
                    extra_stats["sargan_df"] = j_df
                    extra_stats["sargan_p"] = p_sargan
                else:
                    # Hansen J (robust/cluster): u'Z (Z'Z)^{-1} Z'u
                    Zu = Z.T @ residuals
                    try:
                        hansen_j = float(Zu @ np.linalg.solve(ZtZ, Zu))
                        p_hansen = float(1 - chi2.cdf(hansen_j, df=j_df))
                        extra_stats["hansen_j"] = hansen_j
                        extra_stats["hansen_j_df"] = j_df
                        extra_stats["hansen_j_p"] = p_hansen
                    except np.linalg.LinAlgError:
                        extra_stats["hansen_j"] = np.nan
                        extra_stats["hansen_j_df"] = j_df
                        extra_stats["hansen_j_p"] = np.nan

        # Build result object
        result = ResultSchema()
        result.model = ModelInfo(
            command="ivregress 2sls",
            estimator_family="iv_2sls",
            vcetype=vce,
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
            rank=k_x,
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
                t_stat=float(stats[i]),
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
            stata_command=f"ivregress 2sls {self.y} {' '.join(self.x_exog)} ({' '.join(self.x_endog)} = {' '.join(self.instruments)})",
        )
        result._model = self

        # Attach first-stage statistics
        if first:
            result.first_stage = first_stage
        for key, value in extra_stats.items():
            setattr(result, key, value)

        result.validate()
        return result


class IVAbsorbingOLS:
    """
    IV with absorbed fixed effects - aligned with Stata's ivreghdfe.

    Parameters
    ----------
    data : pd.DataFrame
        Input data.
    y : str
        Dependent variable name.
    x_exog : list[str]
        Exogenous regressor names.
    x_endog : list[str]
        Endogenous regressor names.
    instruments : list[str]
        Excluded instrument names.
    absorb : str | list[str]
        Categorical variable(s) to absorb. Multiple variables are supported.
    add_constant : bool, default True
        Whether to include a constant term.
    missing : str, default "drop"
        Missing value handling. Only "drop" is supported.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y: str,
        x_exog: list[str],
        x_endog: list[str],
        instruments: list[str],
        absorb: str | list[str],
        add_constant: bool = True,
        missing: str = "drop",
        drop_singletons: bool = True,
    ):
        self.data = data
        self.y = y
        self.x_exog = list(x_exog)
        self.x_endog = list(x_endog)
        self.instruments = list(instruments)
        from stataflow.estimators._absorb_spec import AbsorbSpec
        if isinstance(absorb, list) and len(absorb) > 0 and isinstance(absorb[0], AbsorbSpec):
            self.absorb_vars = [spec.var for spec in absorb]
        else:
            self.absorb_vars = [absorb] if isinstance(absorb, str) else list(absorb)
        self._reghdfe_mode = True  # ivreghdfe semantics regardless of absorb count
        self.add_constant = add_constant
        self.missing = missing
        self.drop_singletons = drop_singletons

        # Internal state
        self._is_fitted: bool = False
        self._design_matrix: Optional[np.ndarray] = None
        self._dep_var: Optional[np.ndarray] = None
        self._sample_mask: Optional[list[bool]] = None
        self._coef_names: list[str] = []
        self._collinear_dropped: list[str] = []
        self._absorb_var_levels: list[list] = []
        self._n_input_rows: int = 0
        self._df_a: float = 0.0
        self._cluster_arr: Optional[np.ndarray] = None
        self._beta_full: Optional[np.ndarray] = None
        self._beta_reported: Optional[np.ndarray] = None
        self._cov_reported: Optional[np.ndarray] = None
        self._fe_dummy_indices_reduced: list[list[int]] = []
        self._dummy_info: list[dict] = []
        self._constant_idx_reduced: Optional[int] = None
        self._x_exog_indices_in_full: list[int] = []
        self._x_endog_indices_in_full: list[int] = []
        self._x_endog_start: int = 0
        self._inst_start: int = 0

    def _drop_singletons(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        """Iteratively drop singleton observations across all absorb variables."""
        num_dropped = 0
        changed = True
        while changed:
            changed = False
            for var in self.absorb_vars:
                counts = df[var].value_counts()
                singletons = counts[counts == 1].index.tolist()
                if singletons:
                    mask = ~df[var].isin(singletons)
                    n_before = len(df)
                    df = df[mask].copy()
                    n_after = len(df)
                    num_dropped += (n_before - n_after)
                    changed = True
        return df, num_dropped

    def _detect_collinearity(
        self, X: np.ndarray, names: list[str]
    ) -> tuple[np.ndarray, list[str], list[int]]:
        from stataflow.estimators._vce_utils import detect_collinear_columns
        return detect_collinear_columns(X, names)

    # _compute_cluster_meat, _fix_psd, _fix_psd_reghdfe: imported from _vce_utils (ADR-0004).

    def _compute_multiway_cluster_vce(
        self,
        X_proj: np.ndarray,
        residuals: np.ndarray,
        M_inv: np.ndarray,
        k_eff: int,
        n: int,
    ) -> tuple[np.ndarray, int]:
        """Compute 2-way cluster-robust VCE via inclusion-exclusion.

        Thin wrapper that passes pre-computed k_eff (k_x_reported + df_a).
        """
        from stataflow.estimators._vce_utils import compute_multiway_cluster_vce
        return compute_multiway_cluster_vce(
            X_proj, residuals, M_inv, self._cluster_arrs, k_eff, n,
        )

    def _prepare_data(
        self, cluster_vars: Optional[list[str]] = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[bool], int]:
        """
        Prepare LSDV matrices for IV 2SLS.

        Uses ordering: [constant, dummies_1, dummies_2, ..., x_exog, x_endog, instruments]
        so that regressors and instruments are dropped if collinear with absorbed dummies.
        """
        all_vars = [self.y] + self.absorb_vars + self.x_exog + self.x_endog + self.instruments
        cluster_var_list = cluster_vars or []
        for cv in cluster_var_list:
            if cv not in all_vars:
                all_vars.append(cv)

        df = self.data[all_vars].copy()
        self._n_input_rows = len(df)

        # Add a unique row identifier to track observations through drops
        df["_stataflow_row_id"] = np.arange(len(df))

        # Drop missing values
        if self.missing == "drop":
            mask = df.notna().all(axis=1)
            df = df[mask]
        else:
            raise ValueError(f"missing='{self.missing}' not supported")

        # Iterative singleton drop
        if self.drop_singletons:
            df, num_singletons = self._drop_singletons(df)
        else:
            num_singletons = 0
        self._num_singletons = num_singletons

        # Build sample mask using unique row ids (immune to duplicate index labels)
        kept_ids = set(df["_stataflow_row_id"].values)
        sample_mask = [i in kept_ids for i in range(self._n_input_rows)]

        # Drop helper column from further processing
        df = df.drop(columns=["_stataflow_row_id"])

        y = df[self.y].values.astype(np.float64)
        n = len(y)

        # Extract cluster variables if provided
        self._cluster_arrs = []
        self._cluster_vars = []
        for cv in cluster_var_list:
            self._cluster_arrs.append(df[cv].values)
            self._cluster_vars.append(cv)
        # Backward compat
        self._cluster_arr = self._cluster_arrs[0] if self._cluster_arrs else None

        # Build x_exog columns
        x_exog_cols = []
        x_exog_names = []
        for var in self.x_exog:
            x_exog_cols.append(df[var].values.astype(np.float64))
            x_exog_names.append(var)
        X_exog = np.column_stack(x_exog_cols) if x_exog_cols else np.zeros((n, 0))

        # Build x_endog columns
        x_endog_cols = []
        x_endog_names = []
        for var in self.x_endog:
            x_endog_cols.append(df[var].values.astype(np.float64))
            x_endog_names.append(var)
        X_endog = np.column_stack(x_endog_cols) if x_endog_cols else np.zeros((n, 0))

        # Build instrument columns
        inst_cols = []
        inst_names = []
        for var in self.instruments:
            inst_cols.append(df[var].values.astype(np.float64))
            inst_names.append(var)
        Z_excl = np.column_stack(inst_cols) if inst_cols else np.zeros((n, 0))

        # Build absorb dummies
        self._absorb_var_levels = []
        dummy_info = []
        matrix_pieces = []
        names = []

        if self.add_constant:
            matrix_pieces.append(np.ones((n, 1)))
            names.append("_cons")

        for var in self.absorb_vars:
            absorb_vals = df[var].values
            unique_levels = np.unique(absorb_vals)
            self._absorb_var_levels.append(unique_levels.tolist())
            G = len(unique_levels)

            D = np.zeros((n, max(G - 1, 0)))
            for i, level in enumerate(unique_levels[1:], start=1):
                D[:, i - 1] = (absorb_vals == level).astype(np.float64)

            if D.shape[1] > 0:
                start = sum(p.shape[1] for p in matrix_pieces)
                matrix_pieces.append(D)
                dummy_names = [f"__absorb_{var}_{lvl}" for lvl in unique_levels[1:]]
                names.extend(dummy_names)
                dummy_info.append({
                    'start': start,
                    'end': start + D.shape[1],
                    'var': var,
                    'levels': unique_levels.tolist(),
                    'num_levels': G,
                })

        # Track starts for x_exog, x_endog, instruments
        fe_end = sum(p.shape[1] for p in matrix_pieces)

        if X_exog.shape[1] > 0:
            x_exog_start = fe_end
            matrix_pieces.append(X_exog)
            names.extend(x_exog_names)
            fe_end += X_exog.shape[1]
        else:
            x_exog_start = fe_end

        if X_endog.shape[1] > 0:
            x_endog_start = fe_end
            matrix_pieces.append(X_endog)
            names.extend(x_endog_names)
            fe_end += X_endog.shape[1]
        else:
            x_endog_start = fe_end

        if Z_excl.shape[1] > 0:
            inst_start = fe_end
            matrix_pieces.append(Z_excl)
            names.extend(inst_names)
        else:
            inst_start = fe_end

        if matrix_pieces:
            full_matrix = np.column_stack(matrix_pieces)
        else:
            full_matrix = np.zeros((n, 0))

        # Detect collinearity on full matrix
        full_matrix, dropped, kept_indices = self._detect_collinearity(full_matrix, names)
        self._collinear_dropped = [d for d in dropped if not d.startswith("__absorb_")]

        orig_to_reduced = {orig: new for new, orig in enumerate(kept_indices)}

        # Track constant
        constant_idx = 0 if self.add_constant else None
        self._constant_idx_reduced = orig_to_reduced.get(constant_idx, None) if constant_idx is not None else None

        # Track x_exog indices
        self._x_exog_indices_in_full = []
        kept_x_exog_names = []
        for orig_idx, var in enumerate(self.x_exog):
            full_idx = x_exog_start + orig_idx
            if full_idx in kept_indices:
                self._x_exog_indices_in_full.append(orig_to_reduced[full_idx])
                kept_x_exog_names.append(var)

        # Track x_endog indices
        self._x_endog_indices_in_full = []
        kept_x_endog_names = []
        for orig_idx, var in enumerate(self.x_endog):
            full_idx = x_endog_start + orig_idx
            if full_idx in kept_indices:
                self._x_endog_indices_in_full.append(orig_to_reduced[full_idx])
                kept_x_endog_names.append(var)

        constant_kept = self._constant_idx_reduced is not None
        self._has_effective_fe = any(
            df[var].nunique(dropna=False) > 1 for var in self.absorb_vars
        )
        report_constant = constant_kept and not self._has_effective_fe
        self._coef_names = (
            kept_x_endog_names
            + kept_x_exog_names
            + (["_cons"] if report_constant else [])
        )

        # Track FE dummy indices and compute df_a
        self._fe_dummy_indices_reduced = []
        fe_levels_for_df_a = []
        for info in dummy_info:
            kept = [orig_to_reduced[i] for i in range(info['start'], info['end']) if i in kept_indices]
            self._fe_dummy_indices_reduced.append(kept)
            fe_levels_for_df_a.append(info['num_levels'])

        effective_levels = []
        for i, var in enumerate(self.absorb_vars):
            if self._cluster_vars and var in self._cluster_vars:
                continue
            if i < len(fe_levels_for_df_a):
                effective_levels.append(fe_levels_for_df_a[i])

        self._df_a = float(sum(effective_levels))
        if self._reghdfe_mode:
            n_fes = len(self.absorb_vars)
            if n_fes > 1:
                self._df_a -= (n_fes - 1)
        # For areg/ivreghdfe with 1 FE, df_a = G (no -1)
        self._df_a = max(0.0, self._df_a)

        self._dummy_info = dummy_info

        # Build X_full and Z_full from kept columns
        # After collinearity detection, use reduced indices (0..len(kept_indices)-1)
        # X_full = [constant, kept dummies, kept x_exog, kept x_endog]
        x_full_cols = []
        for idx in kept_indices:
            if idx < inst_start:  # Everything before instruments
                x_full_cols.append(orig_to_reduced[idx])
        X_full = full_matrix[:, x_full_cols] if x_full_cols else np.zeros((n, 0))

        # Z_full = [constant, kept dummies, kept x_exog, kept instruments]
        z_full_cols = []
        for idx in kept_indices:
            if idx < x_endog_start:  # constant + dummies + x_exog
                z_full_cols.append(orig_to_reduced[idx])
            elif idx >= inst_start:  # instruments
                z_full_cols.append(orig_to_reduced[idx])
        Z_full = full_matrix[:, z_full_cols] if z_full_cols else np.zeros((n, 0))

        self._design_matrix = X_full
        self._dep_var = y
        self._sample_mask = sample_mask
        self._df = df

        return X_full, Z_full, y, sample_mask, self._n_input_rows

    def _compute_weakiv_stats(
        self,
        X_full: np.ndarray,
        Z_full: np.ndarray,
        y: np.ndarray,
        vce: str,
        n: int,
        cluster_count: int | None,
        estimator: str,
        fuller: float = 0.0,
    ) -> dict:
        """
        Compute weak instrument diagnostics.

        Returns dict with keys: idstat, iddf, idp, widstat,
        sy_10pct, sy_15pct, sy_20pct, sy_25pct.
        """
        from stataflow.estimators._stock_yogo import stock_yogo_critical_values

        k_endog = len(self._x_endog_indices_in_full)
        w_cols_count_in_z = (
            (1 if self._constant_idx_reduced is not None else 0)
            + sum(len(idx) for idx in self._fe_dummy_indices_reduced)
            + len(self._x_exog_indices_in_full)
        )
        k_excl = Z_full.shape[1] - w_cols_count_in_z

        if k_endog == 0 or k_excl == 0 or k_excl < k_endog:
            return {}

        # W = constant + FE dummies (all non-reported columns in X_full)
        reported_indices = self._x_endog_indices_in_full + self._x_exog_indices_in_full
        W_cols = [i for i in range(X_full.shape[1]) if i not in reported_indices]
        W = X_full[:, W_cols] if W_cols else np.zeros((n, 0))

        # Extract endogenous, included exogenous, excluded instruments
        X_endog = X_full[:, self._x_endog_indices_in_full]
        X_exog = X_full[:, self._x_exog_indices_in_full]
        Z_excl = Z_full[:, w_cols_count_in_z:]

        # Residualize by W
        def _residize(A: np.ndarray) -> np.ndarray:
            if W.shape[1] > 0:
                gamma = np.linalg.solve(W.T @ W, W.T @ A)
                return A - W @ gamma
            return A.copy()

        X_endog_r = _residize(X_endog)
        X_exog_r = _residize(X_exog)
        Z_excl_r = _residize(Z_excl)

        # Partial out included exogenous from endogenous and excluded instruments
        if X_exog_r.shape[1] > 0:
            XeXe = X_exog_r.T @ X_exog_r
            beta_endog = np.linalg.solve(XeXe, X_exog_r.T @ X_endog_r)
            beta_excl = np.linalg.solve(XeXe, X_exog_r.T @ Z_excl_r)
            X_endog_p = X_endog_r - X_exog_r @ beta_endog
            Z_excl_p = Z_excl_r - X_exog_r @ beta_excl
        else:
            X_endog_p = X_endog_r
            Z_excl_p = Z_excl_r

        # Compute LM (underidentification test)
        idstat: float = np.nan
        if k_endog == 1:
            x_p = X_endog_p[:, 0]
            z_p = Z_excl_p

            # Restricted model residual: x_p on included exogenous only
            if X_exog_r.shape[1] > 0:
                beta_u = np.linalg.lstsq(X_exog_r, x_p, rcond=None)[0]
                u = x_p - X_exog_r @ beta_u
            else:
                u = x_p.copy()

            if vce == "ols":
                # OLS of x_p on z_p (no constant)
                ZtZ = z_p.T @ z_p
                Ztx = z_p.T @ x_p
                beta_fs = np.linalg.solve(ZtZ, Ztx)
                u_ols = x_p - z_p @ beta_fs
                # Canonical correlation LM (uncentered)
                tss = float(np.sum(x_p ** 2))
                rss = float(np.sum(u_ols ** 2))
                r_cc_sq = 1.0 - rss / tss if tss > 0 else 0.0
                idstat = float(n * r_cc_sq)
            elif vce == "robust":
                zu = z_p * u[:, np.newaxis]
                meat = zu.T @ zu
                Zu = z_p.T @ u
                try:
                    idstat = float(Zu @ np.linalg.inv(meat) @ Zu)
                except np.linalg.LinAlgError:
                    idstat = np.nan
            else:  # cluster
                zu = z_p * u[:, np.newaxis]
                if len(self._cluster_arrs) == 1:
                    meat_cluster = np.zeros((k_excl, k_excl))
                    for g in np.unique(self._cluster_arrs[0]):
                        mask = self._cluster_arrs[0] == g
                        zu_g = zu[mask].sum(axis=0)
                        meat_cluster += np.outer(zu_g, zu_g)
                else:
                    from stataflow.estimators._vce_utils import compute_cluster_meat
                    meats = []
                    Gs = []
                    for ca in self._cluster_arrs:
                        m, G = compute_cluster_meat(z_p, u, ca)
                        meats.append(m)
                        Gs.append(G)
                    if min(Gs) < 3:
                        meat_cluster = meats[int(np.argmax(Gs))]
                    else:
                        seen = {}
                        interaction = np.empty(len(self._cluster_arrs[0]), dtype=int)
                        idx = 0
                        for i, (a, b) in enumerate(zip(self._cluster_arrs[0], self._cluster_arrs[1])):
                            key = (a, b)
                            if key not in seen:
                                seen[key] = idx
                                idx += 1
                            interaction[i] = seen[key]
                        m12, _ = compute_cluster_meat(z_p, u, interaction)
                        meat_cluster = meats[0] + meats[1] - m12
                Zu = z_p.T @ u
                try:
                    idstat = float(Zu @ np.linalg.inv(meat_cluster) @ Zu)
                except np.linalg.LinAlgError:
                    idstat = np.nan
        else:
            # Multiple endogenous: Anderson canonical correlation LM / Cragg-Donald F
            # Compute canonical correlations between X_endog_p and Z_excl_p
            ZtZ_p = Z_excl_p.T @ Z_excl_p
            ZtX_p = Z_excl_p.T @ X_endog_p
            XtX_p = X_endog_p.T @ X_endog_p
            try:
                A = np.linalg.solve(ZtZ_p, ZtX_p)
                B = np.linalg.solve(XtX_p, ZtX_p.T)
                M = A @ B
                eigenvalues = np.linalg.eigvals(M)
                lambda_sq = np.clip(np.real(eigenvalues), 0, 1)
                min_lambda_sq = float(np.min(lambda_sq))
            except np.linalg.LinAlgError:
                min_lambda_sq = 0.0

            if vce == "ols":
                idstat = n * min_lambda_sq
            elif vce == "robust":
                # Multivariate score test (Kleibergen-Paap rk LM approximation)
                U = X_endog_p
                score = Z_excl_p.T @ U
                score_vec = score.ravel(order="F")
                k_total = k_excl * k_endog
                Omega = np.zeros((k_total, k_total))
                for i in range(n):
                    s_i = np.outer(U[i, :], Z_excl_p[i, :]).ravel(order="F")
                    Omega += np.outer(s_i, s_i)
                try:
                    Omega_inv = np.linalg.inv(Omega)
                    idstat = float(score_vec @ Omega_inv @ score_vec)
                except np.linalg.LinAlgError:
                    idstat = np.nan
            else:  # cluster
                U = X_endog_p
                score = Z_excl_p.T @ U
                score_vec = score.ravel(order="F")
                k_total = k_excl * k_endog
                Omega = np.zeros((k_total, k_total))
                if len(self._cluster_arrs) == 1:
                    for g in np.unique(self._cluster_arrs[0]):
                        mask = self._cluster_arrs[0] == g
                        s_g = np.zeros(k_total)
                        for idx in np.where(mask)[0]:
                            s_g += np.outer(U[idx, :], Z_excl_p[idx, :]).ravel(order="F")
                        Omega += np.outer(s_g, s_g)
                else:
                    from stataflow.estimators._vce_utils import compute_cluster_meat
                    for j in range(k_endog):
                        u_j = U[:, j]
                        meats_j = []
                        for ca in self._cluster_arrs:
                            m, _ = compute_cluster_meat(Z_excl_p, u_j, ca)
                            meats_j.append(m)
                        interaction = np.array([
                            f"{a}__{b}" for a, b in zip(self._cluster_arrs[0], self._cluster_arrs[1])
                        ])
                        m12, _ = compute_cluster_meat(Z_excl_p, u_j, interaction)
                        meat_j = meats_j[0] + meats_j[1] - m12
                        # Place in block diagonal of Omega
                        # This is a simplification; full multivariate cluster is complex
                        block_start = j * k_excl
                        Omega[block_start:block_start+k_excl, block_start:block_start+k_excl] += meat_j
                try:
                    Omega_inv = np.linalg.inv(Omega)
                    idstat = float(score_vec @ Omega_inv @ score_vec)
                except np.linalg.LinAlgError:
                    idstat = np.nan

        # Compute Wald F (weak identification test) via first-stage F-test
        widstat: float = np.nan
        if k_endog == 1:
            x_j = X_endog[:, 0]
            ZtZ = Z_full.T @ Z_full
            Ztx = Z_full.T @ x_j
            beta_fs_full = np.linalg.solve(ZtZ, Ztx)
            resid_fs = x_j - Z_full @ beta_fs_full
            q = k_excl

            if vce == "ols":
                RSS_full = float(np.sum(resid_fs ** 2))
                TSS = float(np.sum((x_j - np.mean(x_j)) ** 2))
                # Restricted model: x_j on W_z (included instruments only)
                W_z = Z_full[:, :w_cols_count_in_z]
                if W_z.shape[1] > 0:
                    gamma = np.linalg.solve(W_z.T @ W_z, W_z.T @ x_j)
                    resid_r = x_j - W_z @ gamma
                else:
                    resid_r = x_j
                RSS_r = float(np.sum(resid_r ** 2))
                if q > 0 and RSS_full > 0:
                    widstat = float(((RSS_r - RSS_full) / q) / (RSS_full / (n - Z_full.shape[1])))
            else:
                delta = beta_fs_full[w_cols_count_in_z:]
                ZtZ_inv = np.linalg.inv(ZtZ)
                if vce == "robust":
                    e_sq = resid_fs ** 2
                    meat = (Z_full * e_sq[:, np.newaxis]).T @ Z_full
                    VCE = ZtZ_inv @ meat @ ZtZ_inv
                else:  # cluster
                    k_z = Z_full.shape[1]
                    if len(self._cluster_arrs) == 1:
                        meat = np.zeros((k_z, k_z))
                        for g in np.unique(self._cluster_arrs[0]):
                            mask = self._cluster_arrs[0] == g
                            Z_g = Z_full[mask]
                            e_g = resid_fs[mask]
                            Ze_g = Z_g.T @ e_g
                            meat += np.outer(Ze_g, Ze_g)
                        cc = len(np.unique(self._cluster_arrs[0]))
                        g_adj = cc / (cc - 1) if cc > 1 else 1.0
                        VCE = g_adj * ZtZ_inv @ meat @ ZtZ_inv
                    else:
                        from stataflow.estimators._vce_utils import compute_multiway_cluster_vce
                        VCE, _ = compute_multiway_cluster_vce(
                            Z_full,
                            resid_fs,
                            ZtZ_inv,
                            self._cluster_arrs,
                            k_eff=0,
                            n=n,
                            small_sample_adjust=False,
                        )

                VCE_z = VCE[w_cols_count_in_z:, w_cols_count_in_z:]
                delta_z = delta
                try:
                    VCE_z_inv = np.linalg.inv(VCE_z)
                    wald = float(delta_z @ VCE_z_inv @ delta_z)
                    if vce == "robust":
                        iv1_ct = (
                            (1 if self._constant_idx_reduced is not None else 0)
                            + len(self._x_exog_indices_in_full)
                            + k_excl
                        )
                        dofminus = (
                            w_cols_count_in_z
                            - (1 if self._constant_idx_reduced is not None else 0)
                            - len(self._x_exog_indices_in_full)
                        )
                        widstat = wald / n * (n - iv1_ct - dofminus) / q
                    else:  # cluster
                        if self._has_effective_fe:
                            # ivreghdfe calls ivreg2 on residualized, no-constant
                            # data and passes the non-nested absorbed df separately.
                            iv1_ct = len(self._x_exog_indices_in_full) + k_excl
                            dofminus = self._df_a
                        else:
                            iv1_ct = (
                                (1 if self._constant_idx_reduced is not None else 0)
                                + len(self._x_exog_indices_in_full)
                                + k_excl
                            )
                            dofminus = 0.0
                        widstat = wald / (n - 1) * (n - iv1_ct - dofminus) / q
                except np.linalg.LinAlgError:
                    widstat = np.nan
        else:
            # Multi-endogenous: Kleibergen-Paap rk Wald F (Wald approximation)
            q = max(1, k_excl - k_endog + 1)
            chi2_total = 0.0
            for j in range(k_endog):
                x_j = X_endog[:, j]
                ZtZ = Z_full.T @ Z_full
                Ztx = Z_full.T @ x_j
                beta_fs_full = np.linalg.solve(ZtZ, Ztx)
                resid_fs = x_j - Z_full @ beta_fs_full
                delta = beta_fs_full[w_cols_count_in_z:]

                ZtZ_inv = np.linalg.inv(ZtZ)
                if vce == "ols":
                    sigma2 = float(np.sum(resid_fs ** 2)) / (n - Z_full.shape[1]) if n > Z_full.shape[1] else 0.0
                    VCE = sigma2 * ZtZ_inv
                elif vce == "robust":
                    e_sq = resid_fs ** 2
                    meat = (Z_full * e_sq[:, np.newaxis]).T @ Z_full
                    VCE = ZtZ_inv @ meat @ ZtZ_inv
                else:  # cluster
                    k_z = Z_full.shape[1]
                    if len(self._cluster_arrs) == 1:
                        meat = np.zeros((k_z, k_z))
                        for g in np.unique(self._cluster_arrs[0]):
                            mask = self._cluster_arrs[0] == g
                            Z_g = Z_full[mask]
                            e_g = resid_fs[mask]
                            Ze_g = Z_g.T @ e_g
                            meat += np.outer(Ze_g, Ze_g)
                        cc = len(np.unique(self._cluster_arrs[0]))
                        g_adj = cc / (cc - 1) if cc > 1 else 1.0
                        VCE = g_adj * ZtZ_inv @ meat @ ZtZ_inv
                    else:
                        from stataflow.estimators._vce_utils import compute_multiway_cluster_vce
                        VCE, _ = compute_multiway_cluster_vce(
                            Z_full,
                            resid_fs,
                            ZtZ_inv,
                            self._cluster_arrs,
                            k_eff=0,
                            n=n,
                            small_sample_adjust=False,
                        )

                VCE_z = VCE[w_cols_count_in_z:, w_cols_count_in_z:]
                try:
                    VCE_z_inv = np.linalg.inv(VCE_z)
                    chi2_j = float(delta @ VCE_z_inv @ delta)
                    chi2_total += chi2_j
                except np.linalg.LinAlgError:
                    chi2_total = np.nan
                    break

            if not np.isnan(chi2_total):
                iv1_ct = (
                    (1 if self._constant_idx_reduced is not None else 0)
                    + len(self._x_exog_indices_in_full)
                    + k_excl
                )
                if vce == "ols":
                    widstat = chi2_total / n * (n - iv1_ct) / q
                elif vce == "robust":
                    dofminus = (
                        w_cols_count_in_z
                        - (1 if self._constant_idx_reduced is not None else 0)
                        - len(self._x_exog_indices_in_full)
                    )
                    widstat = chi2_total / n * (n - iv1_ct - dofminus) / q
                else:  # cluster
                    widstat = chi2_total / (n - 1) * (n - iv1_ct) / q

        # Stock-Yogo critical values
        model_sy = "liml" if estimator == "liml" else "2sls"
        sy = stock_yogo_critical_values(
            model=model_sy,
            nendog=k_endog,
            k2=k_excl,
            fuller=fuller,
        )

        iddf = max(1, k_excl - k_endog + 1)
        idp = float(1 - chi2.cdf(idstat, df=iddf)) if not np.isnan(idstat) else np.nan

        return {
            "idstat": idstat,
            "iddf": iddf,
            "idp": idp,
            "widstat": widstat,
            "sy_10pct": sy["10%"],
            "sy_15pct": sy["15%"],
            "sy_20pct": sy["20%"],
            "sy_25pct": sy["25%"],
        }

    def _fit_2sls(
        self, X_full, Z_full, X_proj, y, y_resid, W, WtW,
        reported_indices, vce, n, k_x_full, df_resid, k_eff,
    ):
        """Second-stage OLS on projected X (2SLS) with VCE."""
        XtX_proj = X_proj.T @ X_proj
        Xty_proj = X_proj.T @ y
        beta_full = np.linalg.solve(XtX_proj, Xty_proj)
        residuals = y - X_full @ beta_full
        rss_struct = float(np.sum(residuals ** 2))

        # Residualized projection for F-stat
        beta_reported_for_f = beta_full[reported_indices]
        X_proj_reported = X_proj[:, reported_indices]
        if W.shape[1] > 0:
            gamma_x = np.linalg.solve(WtW, W.T @ X_proj_reported)
            X_tilde_proj = X_proj_reported - W @ gamma_x
        else:
            X_tilde_proj = X_proj_reported
        rss_2s_resid = float(np.sum((y_resid - X_tilde_proj @ beta_reported_for_f) ** 2))

        # VCE
        M_inv = np.linalg.inv(XtX_proj)
        cluster_count = None
        if vce == "ols":
            sigma2 = rss_struct / df_resid if df_resid > 0 else 0.0
            cov_full = sigma2 * M_inv
        elif vce == "robust":
            e_sq = residuals ** 2
            XtOmegaX = (X_proj * e_sq[:, np.newaxis]).T @ X_proj
            cov_full = M_inv @ XtOmegaX @ M_inv
        else:
            if len(self._cluster_arrs) == 1:
                from stataflow.estimators._vce_utils import compute_cluster_meat
                meat, cluster_count = compute_cluster_meat(
                    X_proj, residuals, self._cluster_arrs[0]
                )
                if cluster_count <= 1:
                    raise ValueError(
                        f"cluster-robust VCE requires at least 2 clusters, found {cluster_count}"
                    )
                g_adj = cluster_count / (cluster_count - 1)
                n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
                cov_full = n_adj * g_adj * M_inv @ meat @ M_inv
            else:
                cov_full, cluster_count = self._compute_multiway_cluster_vce(
                    X_proj, residuals, M_inv, k_eff, n
                )

        return beta_full, residuals, cov_full, rss_struct, rss_2s_resid, cluster_count

    def _fit_gmm2s(
        self,
        X_full: np.ndarray,
        Z_full: np.ndarray,
        y: np.ndarray,
        vce: str,
        n: int,
        k_x_full: int,
        k_x_reported: int,
        df_resid: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
        """Two-step efficient GMM estimator."""
        N = n
        ZtZ = Z_full.T @ Z_full
        ZtX = Z_full.T @ X_full

        # Step 1: Initial 2SLS for residuals
        Pi = np.linalg.solve(ZtZ, ZtX)
        X_proj = Z_full @ Pi
        XtX_proj = X_proj.T @ X_proj
        Xty_proj = X_proj.T @ y
        beta_1s = np.linalg.solve(XtX_proj, Xty_proj)
        e_1s = y - X_full @ beta_1s

        # Step 2: Compute omega (moment condition covariance)
        # Use uncorrected omega for GMM weights; apply small-sample corrections to V if needed
        if vce == "ols":
            sigmasq = np.sum(e_1s ** 2) / N
            QZZ = ZtZ / N
            omega = sigmasq * QZZ
        elif vce == "robust":
            Ze = Z_full * e_1s[:, np.newaxis]
            omega = Ze.T @ Ze / N
        else:  # cluster
            if len(self._cluster_arrs) == 1:
                from stataflow.estimators._vce_utils import compute_cluster_meat
                meat, _ = compute_cluster_meat(Z_full, e_1s, self._cluster_arrs[0])
                omega = meat / N
            else:
                from stataflow.estimators._vce_utils import compute_cluster_meat
                meats = []
                for ca in self._cluster_arrs:
                    meat, _ = compute_cluster_meat(Z_full, e_1s, ca)
                    meats.append(meat)
                # Safe interaction encoding (same as _vce_utils.compute_multiway_cluster_vce)
                seen = {}
                interaction = np.empty(len(self._cluster_arrs[0]), dtype=int)
                idx = 0
                for i, (a, b) in enumerate(zip(self._cluster_arrs[0], self._cluster_arrs[1])):
                    key = (a, b)
                    if key not in seen:
                        seen[key] = idx
                        idx += 1
                    interaction[i] = seen[key]
                meat_12, _ = compute_cluster_meat(Z_full, e_1s, interaction)
                omega_meat = meats[0] + meats[1] - meat_12
                omega = omega_meat / N

        # Force symmetry before inversion
        omega = (omega + omega.T) / 2.0
        try:
            cond_omega = np.linalg.cond(omega)
            if cond_omega > 1e12 or not np.isfinite(cond_omega):
                raise np.linalg.LinAlgError("ill-conditioned omega")
            W = np.linalg.inv(omega)
        except np.linalg.LinAlgError:
            # Singular / ill-conditioned omega arises when Z_full includes FE
            # dummies that are collinear with the cluster variable(s).
            # ivreghdfe residualizes FEs before ivreg2, so the moment
            # conditions only involve structural instruments.  We replicate
            # that by partialing out W = [constant, FE dummies] and running
            # GMM on residualized data.
            return self._fit_gmm2s_residualized(
                X_full, Z_full, y, vce, n, k_x_full, k_x_reported, df_resid
            )

        # Step 3: Efficient GMM
        QXZ = ZtX.T / N
        QZy = Z_full.T @ y / N
        Q = QXZ @ W @ QXZ.T
        Q = (Q + Q.T) / 2.0
        beta_gmm = np.linalg.solve(Q, QXZ @ W @ QZy)

        # Step 4: VCE (efficient weights simplified form)
        V = np.linalg.inv(Q) / N
        V = (V + V.T) / 2.0

        # Small-sample correction for ols VCE: Stata applies df_resid adjustment
        if vce == "ols" and df_resid > 0:
            V = V * (N / df_resid)
            V = (V + V.T) / 2.0
        elif vce == "cluster":
            # Small-sample adjustment matching Stata ivreg2 gmm2s cluster:
            # G/(G-1) * (N-1)/(N-L) where L = number of instruments
            if len(self._cluster_arrs) == 1:
                G = len(np.unique(self._cluster_arrs[0]))
            else:
                G = min(len(np.unique(ca)) for ca in self._cluster_arrs)
            L = Z_full.shape[1]
            g_adj = G / (G - 1) if G > 1 else 1.0
            n_adj = (N - 1) / (N - L) if N > L else 1.0
            V = V * g_adj * n_adj
            V = (V + V.T) / 2.0

        # Step 5: Hansen J overidentification test (uses uncorrected omega)
        e_2s = y - X_full @ beta_gmm
        gbar = Z_full.T @ e_2s / N
        J = float(N * gbar.T @ W @ gbar)
        j_df = Z_full.shape[1] - k_x_full

        return beta_gmm, e_2s, V, {"hansen_j": J, "hansen_j_df": j_df}

    def _fit_gmm2s_residualized(
        self,
        X_full: np.ndarray,
        Z_full: np.ndarray,
        y: np.ndarray,
        vce: str,
        n: int,
        k_x_full: int,
        k_x_reported: int,
        df_resid: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
        """GMM on FE-residualized data; used as fallback when omega is singular."""
        N = n

        reported_indices = self._x_endog_indices_in_full + self._x_exog_indices_in_full
        W_cols = [i for i in range(k_x_full) if i not in reported_indices]
        W = X_full[:, W_cols] if W_cols else np.zeros((N, 0))
        X_reported = X_full[:, reported_indices]

        w_cols_count_in_z = (
            (1 if self._constant_idx_reduced is not None else 0)
            + sum(len(idx) for idx in self._fe_dummy_indices_reduced)
            + len(self._x_exog_indices_in_full)
        )
        z_structural_start = w_cols_count_in_z - len(self._x_exog_indices_in_full)
        if z_structural_start < Z_full.shape[1]:
            Z_structural = Z_full[:, z_structural_start:]
        else:
            Z_structural = np.zeros((N, 0))

        def _resid(M: np.ndarray) -> np.ndarray:
            if W.shape[1] == 0:
                return M
            return M - W @ np.linalg.solve(W.T @ W, W.T @ M)

        y_r = _resid(y.reshape(-1, 1)).flatten()
        X_r = _resid(X_reported)
        Z_r = _resid(Z_structural)

        # Initial 2SLS on residualized data
        ZtZ = Z_r.T @ Z_r
        ZtX = Z_r.T @ X_r
        Pi = np.linalg.solve(ZtZ, ZtX)
        X_proj = Z_r @ Pi
        beta_1s = np.linalg.solve(X_proj.T @ X_proj, X_proj.T @ y_r)
        e_1s = y_r - X_r @ beta_1s

        # Omega
        if vce == "ols":
            sigmasq = np.sum(e_1s ** 2) / N
            omega = sigmasq * ZtZ / N
        elif vce == "robust":
            Ze = Z_r * e_1s[:, np.newaxis]
            omega = Ze.T @ Ze / N
        else:  # cluster
            if len(self._cluster_arrs) == 1:
                from stataflow.estimators._vce_utils import compute_cluster_meat
                meat, _ = compute_cluster_meat(Z_r, e_1s, self._cluster_arrs[0])
                omega = meat / N
            else:
                from stataflow.estimators._vce_utils import compute_cluster_meat
                meats = []
                for ca in self._cluster_arrs:
                    meat, _ = compute_cluster_meat(Z_r, e_1s, ca)
                    meats.append(meat)
                # Safe interaction encoding (same as _vce_utils.compute_multiway_cluster_vce)
                seen = {}
                interaction = np.empty(len(self._cluster_arrs[0]), dtype=int)
                idx = 0
                for i, (a, b) in enumerate(zip(self._cluster_arrs[0], self._cluster_arrs[1])):
                    key = (a, b)
                    if key not in seen:
                        seen[key] = idx
                        idx += 1
                    interaction[i] = seen[key]
                meat_12, _ = compute_cluster_meat(Z_r, e_1s, interaction)
                omega_meat = meats[0] + meats[1] - meat_12
                omega = omega_meat / N

        omega = (omega + omega.T) / 2.0
        W_omega = np.linalg.inv(omega)

        # Efficient GMM
        QXZ = ZtX.T / N
        QZy = Z_r.T @ y_r / N
        Q = QXZ @ W_omega @ QXZ.T
        Q = (Q + Q.T) / 2.0
        beta_gmm_reported = np.linalg.solve(Q, QXZ @ W_omega @ QZy)

        # VCE
        V_reported = np.linalg.inv(Q) / N
        V_reported = (V_reported + V_reported.T) / 2.0
        if vce == "ols" and df_resid > 0:
            V_reported = V_reported * (N / df_resid)
            V_reported = (V_reported + V_reported.T) / 2.0
        elif vce == "cluster":
            # Small-sample adjustment matching Stata ivreg2 gmm2s cluster:
            # G/(G-1) * (N-1)/(N-L) where L = number of instruments
            if len(self._cluster_arrs) == 1:
                G = len(np.unique(self._cluster_arrs[0]))
            else:
                G = min(len(np.unique(ca)) for ca in self._cluster_arrs)
            L = Z_r.shape[1]
            g_adj = G / (G - 1) if G > 1 else 1.0
            n_adj = (N - 1) / (N - L) if N > L else 1.0
            V_reported = V_reported * g_adj * n_adj
            V_reported = (V_reported + V_reported.T) / 2.0

        # Reconstruct full beta, full VCE, and full residuals
        beta_gmm = np.zeros(k_x_full)
        V_full = np.zeros((k_x_full, k_x_full))
        for i, idx in enumerate(reported_indices):
            beta_gmm[idx] = beta_gmm_reported[i]
            for j, jdx in enumerate(reported_indices):
                V_full[idx, jdx] = V_reported[i, j]
        e_full = y - X_full @ beta_gmm

        # Hansen J
        gbar = Z_r.T @ e_full / N
        J = float(N * gbar.T @ W_omega @ gbar)
        j_df = Z_r.shape[1] - X_r.shape[1]

        return beta_gmm, e_full, V_full, {"hansen_j": J, "hansen_j_df": j_df}

    def _fit_liml(
        self,
        X_full: np.ndarray,
        Z_full: np.ndarray,
        y: np.ndarray,
        vce: str,
        n: int,
        k_x_full: int,
        k_x_reported: int,
        fuller: float,
        kclass: float | None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
        """LIML and k-class estimator."""
        N = n
        ZtZ = Z_full.T @ Z_full
        ZtZ_inv = np.linalg.inv(ZtZ)

        # Y matrix: [y, X_endo]
        if self._x_endog_indices_in_full:
            X_endo = X_full[:, self._x_endog_indices_in_full]
            Y = np.column_stack([y, X_endo])
        else:
            Y = y.reshape(-1, 1)

        # Z2 = included instruments (constant + dummies + x_exog)
        w_cols_count_in_z = (
            (1 if self._constant_idx_reduced is not None else 0)
            + sum(len(idx) for idx in self._fe_dummy_indices_reduced)
            + len(self._x_exog_indices_in_full)
        )
        Z2 = Z_full[:, :w_cols_count_in_z] if w_cols_count_in_z > 0 else None

        # W and W1 (residual matrices)
        W_mat = Y.T @ Y - Y.T @ Z_full @ ZtZ_inv @ Z_full.T @ Y

        if Z2 is not None and Z2.shape[1] > 0:
            Z2tZ2 = Z2.T @ Z2
            Z2tZ2_inv = np.linalg.inv(Z2tZ2)
            W1 = Y.T @ Y - Y.T @ Z2 @ Z2tZ2_inv @ Z2.T @ Y
        else:
            W1 = Y.T @ Y

        # lambda = min eigenvalue of W^{-1/2} * W1 * W^{-1/2}
        eigvals_w, eigvecs_w = np.linalg.eigh(W_mat)
        eigvals_w = np.maximum(eigvals_w, 1e-15)
        W_inv_sqrt = eigvecs_w @ np.diag(1.0 / np.sqrt(eigvals_w)) @ eigvecs_w.T
        evals = scipy.linalg.eigvalsh(W_inv_sqrt @ W1 @ W_inv_sqrt)
        lambda_ = float(np.min(evals))

        # Exactly identified => lambda = 1
        if Z_full.shape[1] == k_x_full:
            lambda_ = 1.0

        # k-class parameter
        if kclass is not None:
            k = float(kclass)
        elif fuller > 0:
            # ivreg2 Fuller adjustment uses N - L where L = number of
            # structural instruments (x_exog + excluded instruments) in the
            # residualized model, not the LSDV Z_full dimension.
            L = (
                len(self._x_exog_indices_in_full)
                + (Z_full.shape[1] - w_cols_count_in_z)
            )
            k = lambda_ - fuller / (n - L)
        else:
            k = lambda_

        # Estimate beta using Q-matrices
        QXX = X_full.T @ X_full / N
        QXZ = X_full.T @ Z_full / N
        QXy = X_full.T @ y / N
        QZy = Z_full.T @ y / N
        QZZ = ZtZ / N
        QZZ_inv = np.linalg.inv(QZZ)

        aux = QXZ @ QZZ_inv @ QXZ.T
        Qh = (1.0 - k) * QXX + k * aux
        Qh = (Qh + Qh.T) / 2.0
        aux2 = QXZ @ QZZ_inv @ QZy
        beta_liml = np.linalg.solve(Qh, (1.0 - k) * QXy + k * aux2)

        residuals = y - X_full @ beta_liml

        # VCE
        if vce == "ols":
            rss = float(np.sum(residuals ** 2))
            sigma2 = rss / n if n > 0 else 0.0
            V = sigma2 * np.linalg.inv(Qh) / N
        else:
            # Compute omega using LIML residuals
            if vce == "robust":
                Ze = Z_full * residuals[:, np.newaxis]
                omega = Ze.T @ Ze / N
            else:  # cluster
                if len(self._cluster_arrs) == 1:
                    from stataflow.estimators._vce_utils import compute_cluster_meat
                    meat, _ = compute_cluster_meat(Z_full, residuals, self._cluster_arrs[0])
                    omega = meat / N
                else:
                    from stataflow.estimators._vce_utils import compute_cluster_meat
                    meats = []
                    for ca in self._cluster_arrs:
                        meat, _ = compute_cluster_meat(Z_full, residuals, ca)
                        meats.append(meat)
                    interaction = np.array([
                        f"{a}__{b}" for a, b in zip(self._cluster_arrs[0], self._cluster_arrs[1])
                    ])
                    meat_12, _ = compute_cluster_meat(Z_full, residuals, interaction)
                    omega_meat = meats[0] + meats[1] - meat_12
                    omega = omega_meat / N

            omega = (omega + omega.T) / 2.0

            # coviv empty (default): V = 1/N * aux9' * omega * aux9
            aux5 = np.linalg.solve(Qh, QXZ)   # K x L
            aux9 = np.linalg.solve(QZZ, aux5.T)  # L x K
            V = aux9.T @ omega @ aux9 / N
            V = (V + V.T) / 2.0

            # Small-sample correction for cluster VCE
            if vce == "cluster":
                if len(self._cluster_arrs) == 1:
                    G = len(np.unique(self._cluster_arrs[0]))
                else:
                    G = min(len(np.unique(ca)) for ca in self._cluster_arrs)
                g_adj = G / (G - 1) if G > 1 else 1.0
                V = V * g_adj
                V = (V + V.T) / 2.0

        return beta_liml, residuals, V, {"liml_lambda": lambda_, "liml_k": k}

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str | list[str]] = None,
        alpha: float = 0.05,
        first: bool = False,
        estimator: str = "2sls",
        fuller: float = 0.0,
        kclass: float | None = None,
    ) -> ResultSchema:
        """Fit IV absorbing OLS model."""
        if estimator not in ("2sls", "gmm2s", "liml"):
            raise ValueError(f"estimator='{estimator}' not supported. Use '2sls', 'gmm2s', or 'liml'.")
        if fuller != 0 and estimator != "liml":
            raise ValueError("fuller only valid with estimator='liml'.")
        if kclass is not None and estimator != "liml":
            raise ValueError("kclass only valid with estimator='liml'.")
        if vce not in ("ols", "robust", "cluster"):
            raise ValueError(f"vce='{vce}' not supported. Use 'ols', 'robust', or 'cluster'.")
        if vce == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'.")
        if vce != "cluster" and cluster is not None:
            raise ValueError("cluster only used when vce='cluster'.")
        if vce == "cluster" and isinstance(cluster, list) and len(cluster) > 2:
            raise ValueError("Only 1-way and 2-way clustering are supported.")

        cluster_vars = [cluster] if isinstance(cluster, str) else cluster
        X_full, Z_full, y, sample_mask, n_input_rows = self._prepare_data(cluster_vars=cluster_vars)
        if len(y) == 0:
            raise ValueError("No observations remain after sample screening (all rows have missing values).")
        if X_full.shape[1] == 0:
            raise ValueError("Design matrix has 0 columns after sample screening. No regressors available.")
        n = len(y)
        k_x_full = X_full.shape[1]
        k_z_full = Z_full.shape[1]

        if k_z_full < k_x_full:
            raise ValueError(f"Underidentified: need at least {k_x_full} instruments, have {k_z_full}")

        #        # First stage: project X_full onto Z_full (needed for all estimators)
        ZtZ = Z_full.T @ Z_full
        ZtX = Z_full.T @ X_full
        Pi = np.linalg.solve(ZtZ, ZtX)
        X_proj = Z_full @ Pi

        # Reported coefficient indices
        reported_indices = self._x_endog_indices_in_full + self._x_exog_indices_in_full
        k_x_reported = len(reported_indices)

        # Build W = [constant, FE dummies] (all columns except reported x vars)
        W_cols = [i for i in range(k_x_full) if i not in reported_indices]
        W = X_full[:, W_cols] if W_cols else np.zeros((n, 0))

        # y after partialling out FEs + constant
        if W.shape[1] > 0:
            WtW = W.T @ W
            gamma_y = np.linalg.solve(WtW, W.T @ y)
            y_resid = y - W @ gamma_y
        else:
            y_resid = y
        tss_resid = float(np.sum((y_resid - np.mean(y_resid)) ** 2))

        # Degrees of freedom (estimator-independent)
        df_model = float(k_x_reported)
        df_a = self._df_a
        cluster_count = None
        if vce == "cluster":
            if len(self._cluster_arrs) == 1:
                unique_clusters = np.unique(self._cluster_arrs[0])
                cluster_count = len(unique_clusters)
            else:
                cluster_count = min(len(np.unique(ca)) for ca in self._cluster_arrs)
            df_resid = float(cluster_count - 1)
        elif vce == "robust":
            df_resid = float(n - k_x_full)
        else:
            df_resid = float(n - k_x_full)
        k_eff = k_x_reported + df_a

        # Estimator-specific coefficient and VCE
        extra_stats: dict = {}
        if estimator == "2sls":
            beta_full, residuals, cov_full, rss_struct, rss_2s_resid, cluster_count = \
                self._fit_2sls(X_full, Z_full, X_proj, y, y_resid, W, WtW,
                               reported_indices, vce, n, k_x_full, df_resid, k_eff)
        elif estimator == "gmm2s":
            beta_full, residuals, cov_full, extra_stats = self._fit_gmm2s(
                X_full, Z_full, y, vce, n, k_x_full, k_x_reported, df_resid
            )
            rss_struct = float(np.sum(residuals ** 2))

            # Residualized projection for F-stat (use 2SLS X_proj)
            beta_reported_for_f = beta_full[reported_indices]
            X_proj_reported = X_proj[:, reported_indices]
            if W.shape[1] > 0:
                gamma_x = np.linalg.solve(WtW, W.T @ X_proj_reported)
                X_tilde_proj = X_proj_reported - W @ gamma_x
            else:
                X_tilde_proj = X_proj_reported
            rss_2s_resid = float(np.sum((y_resid - X_tilde_proj @ beta_reported_for_f) ** 2))
        else:  # liml
            beta_full, residuals, cov_full, extra_stats = self._fit_liml(
                X_full, Z_full, y, vce, n, k_x_full, k_x_reported, fuller, kclass
            )
            rss_struct = float(np.sum(residuals ** 2))

            # Residualized projection for F-stat (use 2SLS X_proj)
            beta_reported_for_f = beta_full[reported_indices]
            X_proj_reported = X_proj[:, reported_indices]
            if W.shape[1] > 0:
                gamma_x = np.linalg.solve(WtW, W.T @ X_proj_reported)
                X_tilde_proj = X_proj_reported - W @ gamma_x
            else:
                X_tilde_proj = X_proj_reported
            rss_2s_resid = float(np.sum((y_resid - X_tilde_proj @ beta_reported_for_f) ** 2))

        if vce == "cluster" and cluster_count is not None:
            df_resid = float(cluster_count - 1)

        # Weak instrument diagnostics
        weakiv_stats = self._compute_weakiv_stats(
            X_full, Z_full, y, vce, n, cluster_count, estimator, fuller
        )
        extra_stats.update(weakiv_stats)

        # R-squared: Stata uses structural RSS and y_resid TSS
        r2 = 1.0 - rss_struct / tss_resid if tss_resid > 0 else 0.0

        # RMSE denominator: n - k_x_reported - df_a (matches Stata ivreghdfe)
        # When cluster VCE and all FEs are nested (df_a=0), Stata still subtracts
        # the partialled-out constant from the RMSE denominator.
        if not self._has_effective_fe:
            rmse_df = float(n)
        elif vce == "cluster" and df_a == 0 and self.add_constant:
            rmse_df = float(n - k_x_reported - 1)
        else:
            rmse_df = float(n - k_x_reported - df_a)
        rmse = np.sqrt(rss_struct / rmse_df) if rmse_df > 0 else 0.0

        if not self._has_effective_fe:
            # ivreg2 reports root MSE using RSS/N, but adjusted R2 retains
            # the conventional (N-k, N-1) correction.
            adj_df = n - k_x_full
            r2_adj = (
                1.0 - (rss_struct / adj_df) / (tss_resid / (n - 1))
                if adj_df > 0 and n > 1 and tss_resid > 0
                else 0.0
            )
        else:
            # ivreghdfe uses the absorbed-model residual denominator.
            r2_adj = 1.0 - (rss_struct / rmse_df) / (tss_resid / n) if rmse_df > 0 and tss_resid > 0 else 0.0

        # T matrix: map full LSDV -> reported coefficients
        report_dim = k_x_reported + (1 if "_cons" in self._coef_names else 0)
        T = np.zeros((report_dim, k_x_full))

        # Map x_endog coefficients
        for i, full_idx in enumerate(self._x_endog_indices_in_full):
            T[i, full_idx] = 1.0

        # Map x_exog coefficients
        offset = len(self._x_endog_indices_in_full)
        for i, full_idx in enumerate(self._x_exog_indices_in_full):
            T[offset + i, full_idx] = 1.0

        # Map _cons as linear combination
        if "_cons" in self._coef_names:
            cons_row = report_dim - 1
            if self._constant_idx_reduced is not None:
                T[cons_row, self._constant_idx_reduced] = 1.0
            for fe_idx, info in enumerate(self._dummy_info):
                G_total = info['num_levels']
                for dcol in self._fe_dummy_indices_reduced[fe_idx]:
                    T[cons_row, dcol] += 1.0 / G_total

        beta_reported = T @ beta_full
        cov_reported = T @ cov_full @ T.T

        # For multi-way clustering, cov_reported can be non-PSD due to
        # inclusion-exclusion. Apply reghdfe-style PSD fix (preserve slopes).
        if vce == "cluster" and len(self._cluster_arrs) > 1:
            from stataflow.estimators._vce_utils import fix_psd_reghdfe
            constant_index = (
                self._coef_names.index("_cons") if "_cons" in self._coef_names else None
            )
            cov_reported = fix_psd_reghdfe(
                cov_reported,
                constant_index=constant_index,
            )

        # Save internal state for post-estimation
        self._is_fitted = True
        self._beta_full = beta_full
        self._beta_reported = beta_reported
        self._cov_reported = cov_reported
        self._T = T
        self._x_proj = X_proj
        self._W = W
        self._y = y
        self._tss_resid = tss_resid
        self._rss_struct = rss_struct

        # First stage diagnostics
        first_stage: dict[str, dict] = {}
        if first:
            w_cols_count_in_z = (
                (1 if self._constant_idx_reduced is not None else 0)
                + sum(len(idx) for idx in self._fe_dummy_indices_reduced)
                + len(self._x_exog_indices_in_full)
            )
            num_inst = k_z_full - w_cols_count_in_z
            W_z = Z_full[:, :w_cols_count_in_z] if w_cols_count_in_z > 0 else np.zeros((n, 0))
            endog_names = self._coef_names[:len(self._x_endog_indices_in_full)]

            for j, j_idx in enumerate(self._x_endog_indices_in_full):
                x_j = X_full[:, j_idx]
                x_hat_j = X_proj[:, j_idx]
                resid_fs = x_j - x_hat_j
                RSS_full = float(np.sum(resid_fs ** 2))
                TSS = float(np.sum((x_j - np.mean(x_j)) ** 2))
                R2 = 1.0 - RSS_full / TSS if TSS > 0 else 0.0

                # Restricted model: x_j on W (included exogenous only)
                if W_z.shape[1] > 0:
                    gamma = np.linalg.solve(W_z.T @ W_z, W_z.T @ x_j)
                    resid_r = x_j - W_z @ gamma
                else:
                    resid_r = x_j
                RSS_r = float(np.sum(resid_r ** 2))
                R2_r = 1.0 - RSS_r / TSS if TSS > 0 else 0.0

                partial_R2 = (R2 - R2_r) / (1.0 - R2_r) if R2_r < 1.0 else 0.0

                # Shea partial R2: for single endogenous variable, Stata's ivreghdfe
                # sets shea_r2 = partial_r2. For multiple endogenous variables, a more
                # complex adjustment is needed (not yet implemented).
                if len(self._x_endog_indices_in_full) == 1:
                    shea_R2 = partial_R2
                else:
                    var_x_hat = np.var(x_hat_j, ddof=0)
                    var_x = np.var(x_j, ddof=0)
                    shea_R2 = (var_x_hat / var_x) * partial_R2 if var_x > 0 else 0.0

                # F-statistic
                q = num_inst
                f_stat = None
                f_pvalue = None
                if q > 0 and RSS_full > 0:
                    if vce == "ols":
                        f_stat = ((RSS_r - RSS_full) / q) / (RSS_full / (n - k_z_full))
                        f_pvalue = float(1 - f_dist.cdf(f_stat, dfn=q, dfd=n - k_z_full))
                    else:
                        delta = Pi[:, j_idx]
                        ZtZ_inv = np.linalg.inv(ZtZ)
                        if vce == "robust":
                            e_sq = resid_fs ** 2
                            meat = (Z_full * e_sq[:, np.newaxis]).T @ Z_full
                            VCE = ZtZ_inv @ meat @ ZtZ_inv
                        else:  # cluster
                            if len(self._cluster_arrs) == 1:
                                meat = np.zeros((k_z_full, k_z_full))
                                for g in np.unique(self._cluster_arrs[0]):
                                    mask_g = self._cluster_arrs[0] == g
                                    Z_g = Z_full[mask_g]
                                    e_g = resid_fs[mask_g]
                                    Ze_g = Z_g.T @ e_g
                                    meat += np.outer(Ze_g, Ze_g)
                                cc = len(np.unique(self._cluster_arrs[0]))
                                g_adj = cc / (cc - 1) if cc > 1 else 1.0
                                VCE = g_adj * ZtZ_inv @ meat @ ZtZ_inv
                            else:
                                # 2-way clustering for first-stage
                                from stataflow.estimators._vce_utils import compute_multiway_cluster_vce
                                VCE, _ = compute_multiway_cluster_vce(
                                    Z_full,
                                    resid_fs,
                                    ZtZ_inv,
                                    self._cluster_arrs,
                                    k_eff=0,
                                    n=n,
                                    small_sample_adjust=False,
                                )

                        VCE_z = VCE[w_cols_count_in_z:, w_cols_count_in_z:]
                        delta_z = delta[w_cols_count_in_z:]
                        try:
                            VCE_z_inv = np.linalg.inv(VCE_z)
                            wald = float(delta_z @ VCE_z_inv @ delta_z)
                            f_stat = wald / q
                            # NEW-IV-03: cluster VCE first-stage F uses G-1 df, not chi2
                            if vce == "cluster" and cluster_count is not None and cluster_count > 1:
                                f_pvalue = float(1 - f_dist.cdf(f_stat, dfn=q, dfd=cluster_count - 1))
                            else:
                                f_pvalue = float(1 - chi2.cdf(wald, df=q))
                        except np.linalg.LinAlgError:
                            pass

                first_stage[endog_names[j]] = {
                    "r2": R2,
                    "partial_r2": partial_R2,
                    "shea_r2": shea_R2,
                    "f_stat": f_stat,
                    "f_pvalue": f_pvalue,
                    "df": q,
                    "df_r": n - k_z_full,
                }

        diag_cov = np.diag(cov_reported)
        diag_cov = np.maximum(diag_cov, 0)
        se = np.sqrt(diag_cov)

        t_stats = beta_reported / se
        p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=df_resid))

        t_crit = t_dist.ppf(1 - alpha / 2, df=df_resid)
        ci_low = beta_reported - t_crit * se
        ci_high = beta_reported + t_crit * se

        # F-statistic
        if self.add_constant and df_model > 0 and rmse_df > 0 and rss_struct > 0:
            if vce == "ols":
                if estimator == "liml":
                    # ivreg2 posts the LIML covariance, forms the Wald chi2,
                    # then rescales it by df_r/N for the reported F statistic.
                    beta_slopes = beta_reported[:k_x_reported]
                    cov_slopes = cov_reported[:k_x_reported, :k_x_reported]
                    wald_stat = float(
                        beta_slopes @ np.linalg.solve(cov_slopes, beta_slopes)
                    )
                    f_stat = wald_stat / df_model * df_resid / n
                else:
                    # ivreghdfe hybrid F-stat: numerator uses residualized
                    # 2SLS, denominator uses structural RSS.
                    mss_incremental = tss_resid - rss_2s_resid
                    f_stat = (mss_incremental / df_model) / (rss_struct / (n - k_x_full))
                f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
            else:
                slope_idx = list(range(k_x_reported))
                beta_slopes = beta_reported[slope_idx]
                cov_slopes = cov_reported[np.ix_(slope_idx, slope_idx)]
                try:
                    # Guard against ill-conditioned cov_slopes (NEW-IV-02).
                    # In the small-cluster Card real-data path, Stata's
                    # ivreghdfe still reports F(df_model, df_resid) but the
                    # implied Wald scaling behaves as if singular covariance
                    # directions are dropped before forming the model F.
                    cond = np.linalg.cond(cov_slopes)
                    if cond > 1e12 or not np.isfinite(cond):
                        cov_inv = np.linalg.pinv(cov_slopes, rcond=1e-12)
                        wald_df = float(max(np.linalg.matrix_rank(cov_slopes), 1))
                    else:
                        cov_inv = np.linalg.inv(cov_slopes)
                        wald_df = df_model
                    wald_stat = float(beta_slopes @ cov_inv @ beta_slopes)
                    f_stat = wald_stat / wald_df
                    if vce == "robust" and not self._has_effective_fe:
                        # ivreg2 posts HC0 coefficient VCE but reports the
                        # model Wald F with its small-sample df_r/N scaling.
                        f_stat *= df_resid / n
                    f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
                except (np.linalg.LinAlgError, ValueError):
                    f_stat = None
                    f_pvalue = None
        else:
            f_stat = None
            f_pvalue = None

        result = ResultSchema()
        absorb_var = self.absorb_vars[0] if len(self.absorb_vars) == 1 else None
        estimator_family = f"iv_absorbing_ols_{estimator}"
        result.model = ModelInfo(
            command="ivreghdfe",
            estimator_family=estimator_family,
            vcetype=vce,
            absorb_var=absorb_var,
            absorb_vars=self.absorb_vars,
            cluster_var=cluster if vce == "cluster" else None,
            has_constant=self.add_constant,
        )
        result.sample = SampleInfo(
            nobs=n,
            n_input_rows=n_input_rows,
            sample_mask=sample_mask,
        )
        result.fit = FitInfo(
            df_model=df_model,
            df_resid=df_resid,
            df_a=df_a,
            rank=k_x_full,
            rss=rss_struct,
            tss=tss_resid,
            mss=tss_resid - rss_struct,
            rmse=rmse,
            r2=r2,
            r2_adj=r2_adj,
            f_stat=f_stat,
            f_pvalue=f_pvalue,
        )
        result.coefficients = [
            CoefficientRow(
                name=name,
                beta=float(beta_reported[i]),
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
            values=cov_reported.tolist(),
        )
        warnings = []
        if self._collinear_dropped:
            warnings.append(f"Collinear variables dropped: {', '.join(self._collinear_dropped)}")
        if getattr(self, '_num_singletons', 0) > 0:
            warnings.append(f"Singleton observations dropped: {self._num_singletons}")
        # Weak instrument warning
        widstat = extra_stats.get("widstat", np.nan)
        sy_10pct = extra_stats.get("sy_10pct", np.nan)
        if not np.isnan(widstat) and not np.isnan(sy_10pct) and widstat < sy_10pct:
            warnings.append(
                f"Weak instrument test: F = {widstat:.2f} < Stock-Yogo 10% critical value ({sy_10pct:.2f}). "
                f"Instruments may be weak."
            )
        result.diagnostics = DiagnosticsInfo(
            residual_df_correction=None,
            cluster_count=cluster_count,
            widstat=None if np.isnan(widstat) else float(widstat),
            idstat=None if np.isnan(extra_stats.get("idstat", np.nan)) else float(extra_stats["idstat"]),
            iddf=None if np.isnan(extra_stats.get("iddf", np.nan)) else float(extra_stats["iddf"]),
            idp=None if np.isnan(extra_stats.get("idp", np.nan)) else float(extra_stats["idp"]),
            hansen_j=None if np.isnan(extra_stats.get("hansen_j", np.nan)) else float(extra_stats["hansen_j"]),
            hansen_j_df=None if np.isnan(extra_stats.get("hansen_j_df", np.nan)) else float(extra_stats["hansen_j_df"]),
            hansen_j_pvalue=None if np.isnan(extra_stats.get("hansen_j_p", np.nan)) else float(extra_stats["hansen_j_p"]),
            warnings=warnings,
        )
        cmd_name = "ivreghdfe"
        endog_str = ' '.join(self.x_endog)
        exog_str = ' '.join(self.x_exog)
        inst_str = ' '.join(self.instruments)
        opt_parts = [f"absorb({' '.join(self.absorb_vars)})"]
        if estimator == "gmm2s":
            opt_parts.append("gmm2s")
        elif estimator == "liml":
            opt_parts.append("liml")
            if fuller > 0:
                opt_parts.append(f"fuller({int(fuller)})")
            if kclass is not None:
                opt_parts.append(f"kclass({kclass})")
        stata_cmd = f"{cmd_name} {self.y} {exog_str} ({endog_str} = {inst_str}), {' '.join(opt_parts)}"
        result.provenance = ProvenanceInfo(
            source="python",
            stata_version_target="17",
            stata_command=stata_cmd,
        )
        if first:
            result.first_stage = first_stage

        # Attach estimator-specific diagnostics without changing ResultSchema
        for key, value in extra_stats.items():
            setattr(result, key, value)
        result._model = self

        result.validate()
        return result

    def predict(self, type: str = "xb") -> np.ndarray:
        """Generate predictions after fitting."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        if type not in ("xb", "residuals", "d", "xbd", "dresiduals", "stdp"):
            raise ValueError(
                f"type='{type}' not supported for IVAbsorbingOLS. "
                "Use 'xb', 'residuals', 'd', 'xbd', 'dresiduals', or 'stdp'."
            )

        n = len(self._y)
        # xbd = full design matrix @ full beta (includes constant + FEs + reported x)
        xbd = self._design_matrix @ self._beta_full

        if type == "xbd":
            return xbd
        if type == "residuals":
            return self._y - xbd

        # xb uses only reported coefficients (x_endog + x_exog + constant, excluding FEs)
        X_reported_cols = []
        for name in self._coef_names:
            if name == "_cons":
                X_reported_cols.append(np.ones(n))
            elif name in self._df.columns:
                X_reported_cols.append(self._df[name].values.astype(np.float64))
        X_reported = np.column_stack(X_reported_cols) if X_reported_cols else np.zeros((n, 0))
        xb_reported = X_reported @ self._beta_reported

        if type == "stdp":
            if self._cov_reported is None:
                raise ValueError("VCE matrix not available. Call fit() first.")
            var = np.sum((X_reported @ self._cov_reported) * X_reported, axis=1)
            return np.sqrt(np.maximum(var, 0))
        if type == "xb":
            return xb_reported
        if type == "d":
            return xbd - xb_reported
        if type == "dresiduals":
            return self._y - xb_reported
        return xb_reported  # fallback
