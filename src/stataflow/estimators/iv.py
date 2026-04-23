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
from scipy.stats import t as t_dist, f as f_dist
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

        # Detect collinearity separately in X and Z
        X, dropped_x, kept_x = self._detect_collinearity(X, x_names)
        Z, dropped_z, kept_z = self._detect_collinearity(Z, z_names)
        self._collinear_dropped = dropped_x + dropped_z

        self._coef_names = [x_names[i] for i in kept_x]
        self._inst_names = [z_names[i] for i in kept_z]

        self._design_matrix = X
        self._dep_var = y
        self._sample_mask = sample_mask
        self._n_input_rows = n_input_rows

        return X, Z, y, sample_mask, cluster_arr

    def _detect_collinearity(
        self, X: np.ndarray, names: list[str]
    ) -> tuple[np.ndarray, list[str], list[int]]:
        """Detect and drop collinear columns."""
        dropped = []

        if X.shape[1] <= 1:
            return X, dropped, list(range(X.shape[1]))

        rank = np.linalg.matrix_rank(X)
        if rank == X.shape[1]:
            return X, dropped, list(range(X.shape[1]))

        R = np.linalg.qr(X, mode='r')
        tol = 1e-10
        independent = []

        for i in range(X.shape[1]):
            if i < R.shape[0] and abs(R[i, i]) > tol:
                independent.append(i)
            else:
                dropped.append(names[i])

        X_indep = X[:, independent]
        return X_indep, dropped, independent

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
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
        n = len(y)
        k_x = X.shape[1]
        k_z = Z.shape[1]

        if k_z < k_x:
            raise ValueError(f"Underidentified: need at least {k_x} instruments, have {k_z}")

        # First stage: project X onto Z
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

        # z-statistics and p-values (normal distribution for all VCE in ivregress)
        from scipy.stats import norm
        z_stats = beta / se
        p_values = 2 * (1 - norm.cdf(np.abs(z_stats)))
        z_crit = norm.ppf(1 - alpha / 2)

        # Confidence intervals
        ci_low = beta - z_crit * se
        ci_high = beta + z_crit * se

        # F-statistic: Stata ivregress reports Wald chi2, not F, for all VCE
        f_stat = None
        f_pvalue = None

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
                t_stat=float(z_stats[i]),
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
        """Detect and drop collinear columns."""
        dropped = []
        if X.shape[1] <= 1:
            return X, dropped, list(range(X.shape[1]))
        rank = np.linalg.matrix_rank(X)
        if rank == X.shape[1]:
            return X, dropped, list(range(X.shape[1]))
        R = np.linalg.qr(X, mode='r')
        tol = 1e-10
        independent = []
        for i in range(X.shape[1]):
            if i < R.shape[0] and abs(R[i, i]) > tol:
                independent.append(i)
            else:
                dropped.append(names[i])
        X_indep = X[:, independent]
        return X_indep, dropped, independent

    def _prepare_data(
        self, cluster_var: Optional[str] = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[bool], int]:
        """
        Prepare LSDV matrices for IV 2SLS.

        Uses ordering: [constant, dummies_1, dummies_2, ..., x_exog, x_endog, instruments]
        so that regressors and instruments are dropped if collinear with absorbed dummies.
        """
        all_vars = [self.y] + self.absorb_vars + self.x_exog + self.x_endog + self.instruments
        if cluster_var is not None and cluster_var not in all_vars:
            all_vars.append(cluster_var)

        df = self.data[all_vars].copy()
        self._n_input_rows = len(df)

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

        # Build sample mask
        sample_mask = [idx in df.index for idx in self.data.index]

        y = df[self.y].values.astype(np.float64)
        n = len(y)

        # Extract cluster variable if provided
        cluster_arr = None
        if cluster_var is not None:
            cluster_arr = df[cluster_var].values
        self._cluster_arr = cluster_arr

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
        # ivreghdfe never reports _cons; it is always partialled out
        self._coef_names = kept_x_endog_names + kept_x_exog_names

        # Track FE dummy indices and compute df_a
        self._fe_dummy_indices_reduced = []
        fe_levels_for_df_a = []
        for info in dummy_info:
            kept = [orig_to_reduced[i] for i in range(info['start'], info['end']) if i in kept_indices]
            self._fe_dummy_indices_reduced.append(kept)
            fe_levels_for_df_a.append(info['num_levels'])

        effective_levels = []
        for i, var in enumerate(self.absorb_vars):
            if cluster_var is not None and var == cluster_var:
                continue
            if i < len(fe_levels_for_df_a):
                effective_levels.append(fe_levels_for_df_a[i])

        self._df_a = float(sum(effective_levels))
        if self._reghdfe_mode:
            n_fes = len(self.absorb_vars)
            if n_fes > 1:
                self._df_a -= (n_fes - 1)
        # For areg/ivreghdfe with 1 FE, df_a = G (no -1)

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

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """Fit IV absorbing OLS model."""
        if vce not in ("ols", "robust", "cluster"):
            raise ValueError(f"vce='{vce}' not supported. Use 'ols', 'robust', or 'cluster'.")
        if vce == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'.")
        if vce != "cluster" and cluster is not None:
            raise ValueError("cluster only used when vce='cluster'.")

        X_full, Z_full, y, sample_mask, n_input_rows = self._prepare_data(cluster_var=cluster)
        n = len(y)
        k_x_full = X_full.shape[1]
        k_z_full = Z_full.shape[1]

        if k_z_full < k_x_full:
            raise ValueError(f"Underidentified: need at least {k_x_full} instruments, have {k_z_full}")

        # First stage: project X_full onto Z_full
        ZtZ = Z_full.T @ Z_full
        ZtX = Z_full.T @ X_full
        Pi = np.linalg.solve(ZtZ, ZtX)
        X_proj = Z_full @ Pi

        # Second stage: OLS of y on X_proj
        XtX_proj = X_proj.T @ X_proj
        Xty_proj = X_proj.T @ y
        beta_full = np.linalg.solve(XtX_proj, Xty_proj)

        # Structural residuals (using original X_full)
        residuals = y - X_full @ beta_full
        rss_struct = float(np.sum(residuals ** 2))

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

        # Residualized 2SLS projection for F-stat
        beta_reported_for_f = beta_full[reported_indices]
        X_proj_reported = X_proj[:, reported_indices]
        if W.shape[1] > 0:
            gamma_x = np.linalg.solve(WtW, W.T @ X_proj_reported)
            X_tilde_proj = X_proj_reported - W @ gamma_x
        else:
            X_tilde_proj = X_proj_reported
        rss_2s_resid = float(np.sum((y_resid - X_tilde_proj @ beta_reported_for_f) ** 2))

        # R-squared: Stata uses structural RSS and y_resid TSS
        r2 = 1.0 - rss_struct / tss_resid if tss_resid > 0 else 0.0

        # Degrees of freedom
        df_model = float(k_x_reported)
        df_a = self._df_a

        cluster_count = None
        if vce == "cluster":
            unique_clusters = np.unique(self._cluster_arr)
            cluster_count = len(unique_clusters)
            df_resid = float(cluster_count - 1)
        elif vce == "robust":
            df_resid = float(n - k_x_full)
        else:
            df_resid = float(n - k_x_full)

        # RMSE denominator: n - k_x_reported - df_a (matches Stata ivreghdfe)
        rmse_df = float(n - k_x_reported - df_a)
        rmse = np.sqrt(rss_struct / rmse_df) if rmse_df > 0 else 0.0

        # Adjusted R-squared: ivreghdfe uses TSS_resid / n in denominator
        r2_adj = 1.0 - (rss_struct / rmse_df) / (tss_resid / n) if rmse_df > 0 and tss_resid > 0 else 0.0

        # VCE on full LSDV coefficients
        M_inv = np.linalg.inv(XtX_proj)
        if vce == "ols":
            sigma2 = rss_struct / df_resid if df_resid > 0 else 0.0
            cov_full = sigma2 * M_inv
        elif vce == "robust":
            e_sq = residuals ** 2
            XtOmegaX = (X_proj * e_sq[:, np.newaxis]).T @ X_proj
            cov_full = M_inv @ XtOmegaX @ M_inv
        else:
            meat = np.zeros((k_x_full, k_x_full))
            for g in np.unique(self._cluster_arr):
                mask_g = self._cluster_arr == g
                X_g = X_proj[mask_g]
                e_g = residuals[mask_g]
                Xe_g = X_g.T @ e_g
                meat += np.outer(Xe_g, Xe_g)

            # ivreghdfe small-sample adjustment uses k_eff = k_x_reported + df_a
            k_eff = k_x_reported + df_a
            n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
            g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
            cov_full = n_adj * g_adj * M_inv @ meat @ M_inv

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
                # ivreghdfe hybrid F-stat: numerator uses residualized 2SLS, denominator uses structural RSS
                mss_incremental = tss_resid - rss_2s_resid
                f_stat = (mss_incremental / df_model) / (rss_struct / (n - k_x_full))
                f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=rmse_df)
            else:
                slope_idx = list(range(k_x_reported))
                beta_slopes = beta_reported[slope_idx]
                cov_slopes = cov_reported[np.ix_(slope_idx, slope_idx)]
                try:
                    cov_inv = np.linalg.inv(cov_slopes)
                    wald_stat = float(beta_slopes @ cov_inv @ beta_slopes)
                    f_stat = wald_stat / df_model
                    f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
                except np.linalg.LinAlgError:
                    f_stat = None
                    f_pvalue = None
        else:
            f_stat = None
            f_pvalue = None

        result = ResultSchema()
        absorb_var = self.absorb_vars[0] if len(self.absorb_vars) == 1 else None
        result.model = ModelInfo(
            command="ivreghdfe",
            estimator_family="iv_absorbing_ols",
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
        result.diagnostics = DiagnosticsInfo(
            residual_df_correction=None,
            cluster_count=cluster_count,
            warnings=warnings,
        )
        cmd_name = "ivreghdfe"
        endog_str = ' '.join(self.x_endog)
        exog_str = ' '.join(self.x_exog)
        inst_str = ' '.join(self.instruments)
        result.provenance = ProvenanceInfo(
            source="python",
            stata_version_target="17",
            stata_command=f"{cmd_name} {self.y} {exog_str} ({endog_str} = {inst_str}), absorb({' '.join(self.absorb_vars)})",
        )

        return result

    def predict(self, type: str = "xb") -> np.ndarray:
        """Generate predictions after fitting."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        if type not in ("xb", "residuals", "d", "xbd", "dresiduals"):
            raise ValueError(
                f"type='{type}' not supported for IVAbsorbingOLS. "
                "Use 'xb', 'residuals', 'd', 'xbd', or 'dresiduals'."
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

        if type == "xb":
            return xb_reported
        if type == "d":
            return xbd - xb_reported
        if type == "dresiduals":
            return self._y - xb_reported
        return xb_reported  # fallback
