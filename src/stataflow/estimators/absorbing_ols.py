"""
AbsorbingOLS estimator - aligned with Stata's areg and reghdfe commands.

Implements linear regression with absorbed categorical fixed effects
using the LSDV (Least Squares Dummy Variable) approach.
Supports single and multiple absorption variables.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist, f as f_dist
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


class AbsorbingOLS:
    """
    Absorbing OLS estimator aligned with Stata's areg / reghdfe.

    Parameters
    ----------
    data : pd.DataFrame
        Input data.
    y : str
        Dependent variable name.
    x : list[str]
        Independent variable names.
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
        x: list[str],
        absorb: str | list[str],
        add_constant: bool = True,
        missing: str = "drop",
        drop_singletons: bool = True,
    ):
        self.data = data
        self.y = y
        self.x = list(x)
        if isinstance(absorb, str):
            self.absorb_vars = [absorb]
            self._reghdfe_mode = False
        else:
            self.absorb_vars = list(absorb)
            self._reghdfe_mode = True
        self.add_constant = add_constant
        self.missing = missing
        self.drop_singletons = drop_singletons

        # Internal state
        self._design_matrix: Optional[np.ndarray] = None
        self._dep_var: Optional[np.ndarray] = None
        self._sample_mask: Optional[list[bool]] = None
        self._coef_names: list[str] = []
        self._collinear_dropped: list[str] = []
        self._absorb_var_levels: list[list] = []
        self._n_input_rows: int = 0
        self._df_a: float = 0.0
        self._cluster_arr: Optional[np.ndarray] = None

        # Fitted state
        self._is_fitted: bool = False
        self._beta_full: Optional[np.ndarray] = None
        self._cov_full: Optional[np.ndarray] = None
        self._T: Optional[np.ndarray] = None
        self._beta_reported: Optional[np.ndarray] = None
        self._cov_reported: Optional[np.ndarray] = None
        self._result: Optional[ResultSchema] = None

    def _drop_singletons(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        """
        Iteratively drop singleton observations across all absorb variables.

        Returns
        -------
        df_filtered : pd.DataFrame
            DataFrame with singletons removed.
        num_dropped : int
            Total number of singleton observations dropped.
        """
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
        """
        Detect and drop collinear columns.

        Returns
        -------
        X_indep : np.ndarray
            Matrix with independent columns only.
        dropped : list[str]
            Names of dropped columns.
        kept_indices : list[int]
            Indices of kept columns in the original matrix.
        """
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
    ) -> tuple[np.ndarray, np.ndarray, list[bool], int]:
        """
        Prepare design matrix and dependent variable.

        Uses LSDV ordering: [constant, dummies_1, dummies_2, ..., x variables]
        so that x variables are dropped if collinear with absorbed dummies.
        """
        all_vars = [self.y] + self.absorb_vars + self.x
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
            self._num_singletons = num_singletons
        else:
            self._num_singletons = 0

        # Save filtered dataframe for postestimation
        self._df = df.copy()

        # Build sample mask that reflects both missing drop and singleton drop
        sample_mask = [idx in df.index for idx in self.data.index]

        y = df[self.y].values.astype(np.float64)
        n = len(y)

        # Extract cluster variable if provided
        cluster_arr = None
        if cluster_var is not None:
            cluster_arr = df[cluster_var].values
        self._cluster_arr = cluster_arr

        # Build x variables
        X_cols = []
        x_names = []
        for var in self.x:
            X_cols.append(df[var].values.astype(np.float64))
            x_names.append(var)
        X = np.column_stack(X_cols) if X_cols else np.zeros((n, 0))

        # Build absorb dummies for each FE variable
        self._absorb_var_levels = []
        dummy_info = []  # list of dicts with start, end, var, levels, num_levels

        matrix_pieces = []
        names = []

        if self.add_constant:
            matrix_pieces.append(np.ones((n, 1)))
            names.append("_cons")

        for fe_idx, var in enumerate(self.absorb_vars):
            absorb_vals = df[var].values
            unique_levels = np.unique(absorb_vals)
            self._absorb_var_levels.append(unique_levels.tolist())
            G = len(unique_levels)

            if not self.add_constant and fe_idx == 0:
                # First FE gets all levels when no constant (no reference level)
                D = np.zeros((n, max(G, 0)))
                dummy_names = [f"__absorb_{var}_{lvl}" for lvl in unique_levels]
                for i, level in enumerate(unique_levels):
                    D[:, i] = (absorb_vals == level).astype(np.float64)
            else:
                D = np.zeros((n, max(G - 1, 0)))
                dummy_names = [f"__absorb_{var}_{lvl}" for lvl in unique_levels[1:]]
                for i, level in enumerate(unique_levels[1:], start=1):
                    D[:, i - 1] = (absorb_vals == level).astype(np.float64)

            if D.shape[1] > 0:
                start = sum(p.shape[1] for p in matrix_pieces)
                matrix_pieces.append(D)
                names.extend(dummy_names)
                dummy_info.append({
                    'start': start,
                    'end': start + D.shape[1],
                    'var': var,
                    'levels': unique_levels.tolist(),
                    'num_levels': G,
                })

        if X.shape[1] > 0:
            x_start = sum(p.shape[1] for p in matrix_pieces)
            matrix_pieces.append(X)
            names.extend(x_names)
        else:
            x_start = sum(p.shape[1] for p in matrix_pieces)

        if matrix_pieces:
            X_full = np.column_stack(matrix_pieces)
        else:
            X_full = np.zeros((n, 0))

        # Detect collinearity
        X_full, dropped, kept_indices = self._detect_collinearity(X_full, names)
        self._collinear_dropped = [d for d in dropped if not d.startswith("__absorb_")]

        # Build mapping from original index to reduced index
        orig_to_reduced = {orig: new for new, orig in enumerate(kept_indices)}

        # Track constant
        constant_idx = 0 if self.add_constant else None
        self._constant_idx_reduced = orig_to_reduced.get(constant_idx, None) if constant_idx is not None else None

        # Track x indices in reduced matrix and build coefficient names
        self._x_indices_in_full = []
        kept_x_names = []
        for orig_idx, var in enumerate(self.x):
            full_idx = x_start + orig_idx
            if full_idx in kept_indices:
                self._x_indices_in_full.append(orig_to_reduced[full_idx])
                kept_x_names.append(var)

        constant_kept = self._constant_idx_reduced is not None
        self._coef_names = kept_x_names + (["_cons"] if constant_kept else [])

        # Track FE dummy indices and compute df_a
        self._fe_dummy_indices_reduced = []
        fe_levels_for_df_a = []

        for info in dummy_info:
            kept = [orig_to_reduced[i] for i in range(info['start'], info['end']) if i in kept_indices]
            self._fe_dummy_indices_reduced.append(kept)
            fe_levels_for_df_a.append(info['num_levels'])

        # Compute df_a
        effective_levels = []
        for i, var in enumerate(self.absorb_vars):
            if cluster_var is not None and var == cluster_var:
                continue  # Nested in cluster: contributes 0
            if i < len(fe_levels_for_df_a):
                effective_levels.append(fe_levels_for_df_a[i])

        self._df_a = float(sum(effective_levels))
        if self._reghdfe_mode:
            # reghdfe convention: subtract 1 for each additional FE beyond the first
            n_fes = len(self.absorb_vars)
            if n_fes > 1:
                self._df_a -= (n_fes - 1)
        else:
            # areg convention: excludes constant from df_a, but only if constant exists
            if self.add_constant:
                self._df_a -= 1

        # Store dummy_info for T matrix construction
        self._dummy_info = dummy_info

        self._design_matrix = X_full
        self._dep_var = y
        self._sample_mask = sample_mask

        return X_full, y, sample_mask, self._n_input_rows

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """
        Fit absorbing OLS model.

        Parameters
        ----------
        vce : str
            Variance-covariance estimator type. "ols" or "cluster" supported.
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

        X_full, y, sample_mask, n_input_rows = self._prepare_data(cluster_var=cluster)
        n = len(y)
        k_full = X_full.shape[1]

        # LSDV estimation
        XtX = X_full.T @ X_full
        Xty = X_full.T @ y
        beta_full = np.linalg.solve(XtX, Xty)

        # Residuals
        y_hat = X_full @ beta_full
        residuals = y - y_hat

        # Sum of squares
        rss = float(np.sum(residuals ** 2))
        y_mean = np.mean(y)
        tss = float(np.sum((y - y_mean) ** 2))

        # R-squared
        r2 = 1.0 - rss / tss if tss > 0 else 0.0

        # Degrees of freedom
        k_x = len([name for name in self._coef_names if name != "_cons"])
        df_model = float(k_x)
        df_a = self._df_a

        # df_resid depends on VCE type
        cluster_count = None
        if vce == "cluster":
            unique_clusters = np.unique(self._cluster_arr)
            cluster_count = len(unique_clusters)
            df_resid = float(cluster_count - 1)
        elif vce == "robust":
            df_resid = float(n - k_full)
        else:
            df_resid = float(n - k_full)

        # RMSE denominator: both areg and reghdfe use N - k_full
        rmse_df = float(n - k_full)
        rmse = np.sqrt(rss / rmse_df) if rmse_df > 0 else 0.0

        # Adjusted R-squared
        if self._reghdfe_mode:
            r2_adj = 1.0 - (rss / rmse_df) / (tss / (n - 1)) if rmse_df > 0 and tss > 0 else 0.0
        else:
            r2_adj = 1.0 - (1.0 - r2) * (n - 1) / rmse_df if rmse_df > 0 else 0.0

        # Variance-covariance matrix on full LSDV coefficients
        if vce == "ols":
            sigma2 = rss / df_resid if df_resid > 0 else 0.0
            cov_full = sigma2 * np.linalg.inv(XtX)
        elif vce == "robust":
            # HC1 robust sandwich on full LSDV coefficients
            XtX_inv = np.linalg.inv(XtX)
            meat = X_full.T @ (X_full * (residuals ** 2)[:, np.newaxis])
            cov_full = XtX_inv @ meat @ XtX_inv
            if n > 1:
                cov_full *= n / (n - 1)
        else:
            # Cluster-robust VCE on full LSDV
            XtX_inv = np.linalg.inv(XtX)
            unique_clusters = np.unique(self._cluster_arr)
            cluster_count = len(unique_clusters)

            meat = np.zeros((k_full, k_full))
            for g in unique_clusters:
                mask_g = self._cluster_arr == g
                X_g = X_full[mask_g]
                e_g = residuals[mask_g]
                Xe_g = X_g.T @ e_g
                meat += np.outer(Xe_g, Xe_g)

            # Small-sample adjustment: exclude parameters from FEs nested in cluster
            nested_params = 0
            for info in self._dummy_info:
                if info['var'] == cluster:
                    nested_params += info['num_levels'] - 1
            k_eff = k_full - nested_params
            n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
            g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
            cov_full = n_adj * g_adj * XtX_inv @ meat @ XtX_inv

        # Build transformation from full LSDV parameters to reported parameters
        # Reported order: [x1, x2, ..., _cons]
        # _cons = constant + sum over FE groups of mean(dummy coefficients for that FE)
        report_dim = k_x + (1 if "_cons" in self._coef_names else 0)
        T = np.zeros((report_dim, k_full))

        # Map x coefficients
        for i, full_idx in enumerate(self._x_indices_in_full):
            T[i, full_idx] = 1.0

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

        # Standard errors
        diag_cov = np.diag(cov_reported)
        diag_cov = np.maximum(diag_cov, 0)
        se = np.sqrt(diag_cov)

        # t-statistics and p-values
        t_stats = beta_reported / se
        p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=df_resid))

        # Confidence intervals
        t_crit = t_dist.ppf(1 - alpha / 2, df=df_resid)
        ci_low = beta_reported - t_crit * se
        ci_high = beta_reported + t_crit * se

        # F-statistic
        rss_r = None
        if self.add_constant and df_model > 0 and rmse_df > 0 and rss > 0:
            if vce == "ols":
                # Incremental F for non-absorbed variables
                restricted_cols = []
                if self._constant_idx_reduced is not None:
                    restricted_cols.append(self._constant_idx_reduced)
                for fe_idx in range(len(self._fe_dummy_indices_reduced)):
                    restricted_cols.extend(self._fe_dummy_indices_reduced[fe_idx])
                if restricted_cols:
                    X_r = X_full[:, restricted_cols]
                    beta_r = np.linalg.solve(X_r.T @ X_r, X_r.T @ y)
                    resid_r = y - X_r @ beta_r
                    rss_r = float(np.sum(resid_r ** 2))
                    mss_incremental = rss_r - rss
                    f_stat = (mss_incremental / df_model) / (rss / rmse_df)
                    f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=rmse_df)
                else:
                    f_stat = None
                    f_pvalue = None
            else:
                # Wald F for cluster VCE
                slope_idx = list(range(k_x))
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

        # Build result object
        result = ResultSchema()
        absorb_var = self.absorb_vars[0] if len(self.absorb_vars) == 1 else None
        result.model = ModelInfo(
            command="reghdfe" if self._reghdfe_mode else "areg",
            estimator_family="absorbing_ols",
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
            rank=k_full,
            rss=rss,
            tss=tss,
            mss=rss_r - rss if rss_r is not None else None,
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
        cmd_name = "reghdfe" if self._reghdfe_mode else "areg"
        result.provenance = ProvenanceInfo(
            source="python",
            stata_version_target="17",
            stata_command=f"{cmd_name} {self.y} {' '.join(self.x)}, absorb({' '.join(self.absorb_vars)})",
        )

        # Store fitted state for postestimation
        self._is_fitted = True
        self._beta_full = beta_full
        self._cov_full = cov_full
        self._T = T
        self._beta_reported = beta_reported
        self._cov_reported = cov_reported
        self._result = result

        return result

    def predict(self, type: str = "xb", newdata: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Generate predictions after fitting."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        if type not in ("xb", "residuals", "d", "xbd", "dresiduals"):
            raise ValueError(
                f"type='{type}' not supported for AbsorbingOLS. "
                "Use 'xb', 'residuals', 'd', 'xbd', or 'dresiduals'."
            )

        if newdata is not None:
            raise NotImplementedError("Out-of-sample prediction for AbsorbingOLS not yet implemented.")

        n = len(self._dep_var)
        xbd = self._design_matrix @ self._beta_full

        if type == "xbd":
            return xbd
        if type == "residuals":
            return self._dep_var - xbd

        # xb uses only reported coefficients (x vars + constant, excluding FEs)
        X_reported_cols = []
        for name in self._coef_names:
            if name == "_cons":
                X_reported_cols.append(np.ones(n))
            elif name in self.x:
                X_reported_cols.append(self._df[name].values.astype(np.float64))
        X_reported = np.column_stack(X_reported_cols) if X_reported_cols else np.zeros((n, 0))
        xb_reported = X_reported @ self._beta_reported

        if type == "xb":
            return xb_reported
        if type == "d":
            return xbd - xb_reported
        if type == "dresiduals":
            return self._dep_var - xb_reported
        return xb_reported  # fallback

    def margins(self, type: str = "dydx") -> SimpleNamespace:
        """Compute marginal effects."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        from stataflow.postestimation import margins_ame_linear, _build_margins_result

        k = len(self._beta_reported)
        effects = margins_ame_linear(self._beta_reported)
        J = np.eye(k)
        return _build_margins_result(
            effects, J, self._cov_reported, self._coef_names, self._result.sample.nobs
        )
