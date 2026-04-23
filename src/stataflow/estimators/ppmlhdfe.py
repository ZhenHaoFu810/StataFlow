"""
PPMLHDFE estimator - Poisson PML with high-dimensional fixed effects.

Aligned with Stata's ppmlhdfe command.
Uses IRLS within the LSDV framework, reusing AbsorbingOLS data preparation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm as norm_dist
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
from stataflow.estimators.absorbing_ols import AbsorbingOLS


class PPMLHDFE:
    """
    Poisson PML with HDFE absorption.

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
    max_iter : int, default 100
        Maximum IRLS iterations.
    tol : float, default 1e-8
        Convergence tolerance.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y: str,
        x: list[str],
        absorb: str | list[str],
        add_constant: bool = True,
        missing: str = "drop",
        max_iter: int = 100,
        tol: float = 1e-8,
        offset: Optional[str] = None,
        exposure: Optional[str] = None,
    ):
        if offset is not None and exposure is not None:
            raise ValueError("Only one of offset or exposure can be specified.")
        self.data = data
        self.y = y
        self.x = list(x)
        self.absorb_vars = list(absorb) if isinstance(absorb, list) else [absorb]
        self.add_constant = add_constant
        self.missing = missing
        self.max_iter = max_iter
        self.tol = tol
        self.offset_var = offset
        self.exposure_var = exposure

        # Load offset vector (exposure is converted to log offset)
        self._offset_vec: Optional[np.ndarray] = None
        if exposure is not None:
            vals = data[exposure].values.astype(np.float64)
            if np.any(vals <= 0):
                raise ValueError("exposure() must be greater than zero.")
            self._offset_vec = np.log(vals)
        elif offset is not None:
            self._offset_vec = data[offset].values.astype(np.float64)

        # Fitted state
        self._is_fitted: bool = False
        self._gamma: Optional[np.ndarray] = None
        self._mu: Optional[np.ndarray] = None
        self._eta: Optional[np.ndarray] = None
        self._T: Optional[np.ndarray] = None
        self._beta_reported: Optional[np.ndarray] = None
        self._cov_reported: Optional[np.ndarray] = None
        self._result: Optional[ResultSchema] = None

        # Internal AbsorbingOLS handles LSDV matrix construction
        self._abs_ols = AbsorbingOLS(
            data=data,
            y=y,
            x=x,
            absorb=absorb,
            add_constant=add_constant,
            missing=missing,
        )

    def _irls_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        gamma_init: Optional[np.ndarray] = None,
        offset: Optional[np.ndarray] = None,
    ) -> tuple[np.ndarray, np.ndarray, bool]:
        """
        Run IRLS for Poisson PML on LSDV matrix.

        Parameters
        ----------
        gamma_init : np.ndarray, optional
            Initial coefficients. If None, uses OLS of log(y+1) on X.
        offset : np.ndarray, optional
            Offset vector to add to linear predictor.

        Returns
        -------
        gamma : np.ndarray
            LSDV coefficients.
        mu : np.ndarray
            Fitted means.
        converged : bool
        """
        n, k = X.shape
        if gamma_init is not None:
            gamma = gamma_init.copy()
        else:
            # Better starting guess: OLS of log(y+1) on X
            y_log = np.log(y + 1)
            if offset is not None:
                y_log = y_log - offset
            try:
                gamma = np.linalg.lstsq(X, y_log, rcond=None)[0]
            except Exception:
                gamma = np.zeros(k)
        ll_old = -np.inf
        converged = False

        for _ in range(self.max_iter):
            eta = X @ gamma
            if offset is not None:
                eta = eta + offset
            mu = np.exp(np.clip(eta, -700, 700))
            mu = np.clip(mu, 1e-15, 1e12)

            # Working response and weights for Poisson
            z = eta + (y - mu) / mu
            w = mu

            sqrt_w = np.sqrt(w)
            Xw = X * sqrt_w[:, np.newaxis]
            zw = z * sqrt_w

            try:
                gamma_step = np.linalg.solve(Xw.T @ Xw, Xw.T @ zw)
            except np.linalg.LinAlgError:
                gamma_step = np.linalg.lstsq(Xw, zw, rcond=None)[0]

            # Step-halving to ensure log-likelihood increase
            step_size = 1.0
            gamma_new = gamma_step
            for _halve in range(10):
                eta_new = X @ gamma_new
                if offset is not None:
                    eta_new = eta_new + offset
                mu_new = np.exp(np.clip(eta_new, -700, 700))
                mu_new = np.clip(mu_new, 1e-15, 1e12)
                from scipy.special import gammaln
                ll_new = float(np.sum(y * np.log(mu_new) - mu_new - gammaln(y + 1)))
                if ll_new >= ll_old or _halve == 9:
                    break
                step_size *= 0.5
                gamma_new = gamma + step_size * (gamma_step - gamma)
            else:
                gamma_new = gamma_step

            # Log-likelihood (including log(y!) constant for completeness)
            from scipy.special import gammaln
            ll_new = float(np.sum(y * np.log(mu_new) - mu_new - gammaln(y + 1)))

            rel_change = abs(ll_new - ll_old) / (abs(ll_old) + 1.0)
            param_change = np.max(np.abs(gamma_new - gamma))

            if rel_change < self.tol and param_change < self.tol:
                converged = True
                gamma = gamma_new
                break

            gamma = gamma_new
            ll_old = ll_new

        eta = X @ gamma
        if offset is not None:
            eta = eta + offset
        mu = np.exp(np.clip(eta, -700, 700))
        mu = np.clip(mu, 1e-15, 1e12)
        return gamma, mu, converged

    def _build_t_matrix(self, mu: np.ndarray) -> np.ndarray:
        """
        Build T matrix mapping LSDV parameters to reported parameters.

        For PPMLHDFE, the reported constant follows the reghdfe formula:
        b0 = weighted_mean(log(mu), weights=mu) - sum_j weighted_mean(x_j, weights=mu) * b_j
        which is equivalent to gamma_const + weighted_mean(FE_dummies, weights=mu) @ gamma_FE.
        If an offset is present, its weighted mean is subtracted from the constant.
        """
        X_full = self._abs_ols._design_matrix
        k_x = len([name for name in self._abs_ols._coef_names if name != "_cons"])
        report_dim = k_x + (1 if "_cons" in self._abs_ols._coef_names else 0)
        k_full = X_full.shape[1]
        T = np.zeros((report_dim, k_full))

        # Map x coefficients directly
        for i, full_idx in enumerate(self._abs_ols._x_indices_in_full):
            T[i, full_idx] = 1.0

        # Map _cons as weighted linear combination
        if "_cons" in self._abs_ols._coef_names:
            cons_row = report_dim - 1
            w = np.clip(mu, 1e-15, 1e12)
            w = w / w.sum()
            # weighted mean of each column of X_full
            T[cons_row, :] = np.sum(X_full * w[:, np.newaxis], axis=0)
            # subtract weighted means of x variables from their respective positions
            for i, full_idx in enumerate(self._abs_ols._x_indices_in_full):
                mean_xj = np.sum(X_full[:, full_idx] * w)
                T[cons_row, full_idx] -= mean_xj
            # subtract weighted mean of offset if present
            if self._offset_vec is not None:
                T[cons_row, :] -= np.sum(self._offset_vec[self._abs_ols._sample_mask] * w)

        return T

    def _compute_vce(
        self,
        X_full: np.ndarray,
        y: np.ndarray,
        mu: np.ndarray,
        gamma: np.ndarray,
        vce: str,
        cluster_arr: Optional[np.ndarray],
    ) -> tuple[np.ndarray, Optional[int]]:
        """Compute VCE in LSDV space."""
        n, k_full = X_full.shape
        w = np.clip(mu, 1e-15, 1e12)
        sqrt_w = np.sqrt(w)
        Xw = X_full * sqrt_w[:, np.newaxis]

        try:
            XtX_inv = np.linalg.inv(Xw.T @ Xw)
        except np.linalg.LinAlgError:
            XtX_inv = np.linalg.pinv(Xw.T @ Xw)

        cluster_count = None
        residuals = y - mu

        if vce == "ols":
            # Conventional VCE: inverse of expected Hessian (Fisher information)
            cov_full = XtX_inv
        elif vce == "robust":
            # Robust sandwich with N/(N-1) small-sample adjustment
            meat = X_full.T @ (X_full * (residuals ** 2)[:, np.newaxis])
            cov_full = XtX_inv @ meat @ XtX_inv
            if n > 1:
                cov_full *= n / (n - 1)
        elif vce == "cluster":
            unique_clusters = np.unique(cluster_arr)
            cluster_count = len(unique_clusters)
            meat = np.zeros((k_full, k_full))
            for g in unique_clusters:
                mask_g = cluster_arr == g
                X_g = X_full[mask_g]
                r_g = residuals[mask_g]
                score_g = X_g.T @ r_g
                meat += np.outer(score_g, score_g)

            # PPMLHDFE uses vce_asymptotic mode, so only G/(G-1) adjustment applies
            g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
            cov_full = g_adj * XtX_inv @ meat @ XtX_inv
        else:
            raise ValueError(f"vce='{vce}' not supported. Use 'ols' or 'cluster'.")

        return cov_full, cluster_count

    def fit(
        self,
        vce: str = "robust",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """Fit PPMLHDFE model."""
        if vce not in ("ols", "robust", "cluster"):
            raise ValueError(f"vce='{vce}' not supported. Use 'ols', 'robust', or 'cluster'.")
        if vce == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'.")
        if vce not in ("cluster",) and cluster is not None:
            raise ValueError("cluster only used when vce='cluster'.")

        # Prepare LSDV data via AbsorbingOLS
        self._abs_ols._prepare_data(cluster_var=cluster)
        X_full = self._abs_ols._design_matrix.copy()
        y = self._abs_ols._dep_var
        n = len(y)
        k_full = X_full.shape[1]
        cluster_arr = self._abs_ols._cluster_arr

        # Align offset vector with the retained sample
        offset_vec = None
        if self._offset_vec is not None:
            offset_vec = self._offset_vec[self._abs_ols._sample_mask]

        # Standardize x variable columns for numerical stability in IRLS
        x_indices = list(self._abs_ols._x_indices_in_full)
        x_stds = np.ones(len(x_indices))
        x_means = np.zeros(len(x_indices))
        X_std = X_full.copy()
        for idx_pos, col_idx in enumerate(x_indices):
            col = X_std[:, col_idx]
            std = np.std(col)
            if std > 1e-15:
                x_stds[idx_pos] = std
                x_means[idx_pos] = np.mean(col)
                X_std[:, col_idx] = (col - x_means[idx_pos]) / std

        gamma_std, mu, converged = self._irls_fit(X_std, y, offset=offset_vec)

        # Rescale LSDV coefficients back to original x scale
        gamma = gamma_std.copy()
        for idx_pos, col_idx in enumerate(x_indices):
            gamma[col_idx] = gamma_std[col_idx] / x_stds[idx_pos]
        if self._abs_ols._constant_idx_reduced is not None:
            const_idx = self._abs_ols._constant_idx_reduced
            gamma[const_idx] = gamma_std[const_idx] - np.sum(x_means * gamma[x_indices])

        # Recompute mu on original scale to ensure consistency
        eta = X_full @ gamma
        if offset_vec is not None:
            eta = eta + offset_vec
        mu = np.exp(np.clip(eta, -700, 700))
        mu = np.clip(mu, 1e-15, 1e12)

        # Log-likelihood
        from scipy.special import gammaln
        ll_model = float(np.sum(y * np.log(mu) - mu - gammaln(y + 1)))

        # Deviance: 2 * 危 [渭 - y + y * log(y/渭)]  (with 0*log(0) = 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            deviance_terms = (mu - y) + y * np.log(y / mu)
        deviance_terms = np.where(y == 0, mu, deviance_terms)
        deviance = float(2.0 * np.sum(deviance_terms))
        if deviance < 0:
            deviance = 0.0

        # Pseudo log-likelihood of constant-only model
        y_mean = float(np.mean(y))
        ll_0 = float(np.sum(y * np.log(y_mean) - y_mean - gammaln(y + 1)))
        pseudo_r2 = 1.0 - ll_model / ll_0 if ll_0 != 0 else None

        # Degrees of freedom
        k_x = len([name for name in self._abs_ols._coef_names if name != "_cons"])
        df_model = float(k_x)
        df_a = self._abs_ols._df_a

        if vce == "cluster" and cluster_arr is not None:
            unique_clusters = np.unique(cluster_arr)
            cluster_count = len(unique_clusters)
            df_resid = float(cluster_count - 1)
        else:
            cluster_count = None
            df_resid = float(n - k_full)

        # VCE (use original X_full and rescaled gamma)
        cov_full, cluster_count_vce = self._compute_vce(X_full, y, mu, gamma, vce, cluster_arr)
        if cluster_count is None:
            cluster_count = cluster_count_vce

        # Transform to reported parameters
        T = self._build_t_matrix(mu)
        beta_reported = T @ gamma
        cov_reported = T @ cov_full @ T.T

        diag_cov = np.diag(cov_reported)
        diag_cov = np.maximum(diag_cov, 0)
        se = np.sqrt(diag_cov)

        z_stats = beta_reported / se
        p_values = 2 * (1 - norm_dist.cdf(np.abs(z_stats)))
        z_crit = norm_dist.ppf(1 - alpha / 2)
        ci_low = beta_reported - z_crit * se
        ci_high = beta_reported + z_crit * se

        result = ResultSchema()
        result.model = ModelInfo(
            command="ppmlhdfe",
            estimator_family="ppmlhdfe",
            vcetype=vce,
            absorb_vars=self.absorb_vars,
            cluster_var=cluster if vce == "cluster" else None,
            has_constant=self.add_constant,
        )
        result.sample = SampleInfo(
            nobs=n,
            n_input_rows=self._abs_ols._n_input_rows,
            sample_mask=self._abs_ols._sample_mask,
        )
        result.fit = FitInfo(
            df_model=df_model,
            df_resid=df_resid,
            df_a=df_a,
            rank=k_full,
            ll=ll_model,
            deviance=deviance,
            pseudo_r2=pseudo_r2,
        )
        result.coefficients = [
            CoefficientRow(
                name=name,
                beta=float(beta_reported[i]),
                std_err=float(se[i]),
                t_stat=float(z_stats[i]),
                p_value=float(p_values[i]),
                ci_low=float(ci_low[i]),
                ci_high=float(ci_high[i]),
            )
            for i, name in enumerate(self._abs_ols._coef_names)
        ]
        result.variance = VarianceInfo(
            row_names=list(self._abs_ols._coef_names),
            values=cov_reported.tolist(),
        )
        warnings = []
        if self._abs_ols._collinear_dropped:
            warnings.append(f"Collinear variables dropped: {', '.join(self._abs_ols._collinear_dropped)}")
        if getattr(self._abs_ols, '_num_singletons', 0) > 0:
            warnings.append(f"Singleton observations dropped: {self._abs_ols._num_singletons}")
        if not converged:
            warnings.append("IRLS did not converge")
        result.diagnostics = DiagnosticsInfo(
            cluster_count=cluster_count,
            warnings=warnings,
        )
        vce_str = f" vce({vce})" if vce != "robust" else ""
        cluster_str = f" cluster({cluster})" if vce == "cluster" and cluster is not None else ""
        result.provenance = ProvenanceInfo(
            source="python",
            stata_version_target="17",
            stata_command=f"ppmlhdfe {self.y} {' '.join(self.x)}, absorb({' '.join(self.absorb_vars)}){vce_str}{cluster_str}",
        )

        # Store fitted state for postestimation
        self._is_fitted = True
        self._gamma = gamma
        self._mu = mu
        self._eta = eta
        self._T = T
        self._beta_reported = beta_reported
        self._cov_reported = cov_reported
        self._result = result

        return result

    def predict(self, type: str = "xb", newdata: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Generate predictions after fitting."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        if type not in ("xb", "mu", "residuals"):
            raise ValueError(f"type='{type}' not supported for PPMLHDFE. Use 'xb', 'mu', or 'residuals'.")
        if newdata is not None:
            raise NotImplementedError("Out-of-sample prediction for PPMLHDFE not yet implemented.")
        if type == "xb":
            return self._eta
        if type == "mu":
            return self._mu
        # residuals: y - mu
        y = self._abs_ols._dep_var
        return y - self._mu

    def margins(self, type: str = "dydx") -> SimpleNamespace:
        """Compute marginal effects."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        from stataflow.postestimation import (
            margins_ame_poisson, margins_mem_poisson, _build_margins_result,
        )

        # Build X matrix for reported coefficients (x variables + constant)
        X_full = self._abs_ols._design_matrix
        T = self._T
        # We need X in the reported-parameter space: x variables as observed
        k_x = len([name for name in self._abs_ols._coef_names if name != "_cons"])
        has_cons = "_cons" in self._abs_ols._coef_names
        report_dim = k_x + (1 if has_cons else 0)
        # X_reported: original x variables + constant if applicable
        X_rep_cols = []
        for full_idx in self._abs_ols._x_indices_in_full:
            X_rep_cols.append(X_full[:, full_idx])
        if has_cons:
            X_rep_cols.append(np.ones(X_full.shape[0]))
        X_rep = np.column_stack(X_rep_cols) if X_rep_cols else np.zeros((X_full.shape[0], report_dim))

        if type == "dydx":
            effects, J = margins_ame_poisson(self._beta_reported, X_rep)
        else:
            effects, J = margins_mem_poisson(self._beta_reported, X_rep)

        return _build_margins_result(
            effects, J, self._cov_reported, self._abs_ols._coef_names, self._result.sample.nobs
        )
