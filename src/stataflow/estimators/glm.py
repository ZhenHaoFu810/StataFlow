"""
GLM estimators - Logit, Probit, and Poisson aligned with Stata's official commands.

Implements MLE via IRLS (Iteratively Reweighted Least Squares) / Fisher scoring
with convergence criteria matched to Stata 17.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm as norm_dist, chi2 as chi2_dist
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


class GLMBase:
    """
    Base class for GLM estimators (Logit, Probit, Poisson).

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
    missing : str, default "drop"
        Missing value handling. Only "drop" is supported.
    max_iter : int, default 100
        Maximum IRLS iterations.
    tol : float, default 1e-8
        Convergence tolerance for log-likelihood relative change.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y: str,
        x: list[str],
        add_constant: bool = True,
        missing: str = "drop",
        max_iter: int = 100,
        tol: float = 1e-8,
    ):
        self.data = data
        self.y = y
        self.x = list(x)
        self.add_constant = add_constant
        self.missing = missing
        self.max_iter = max_iter
        self.tol = tol

        self._design_matrix: Optional[np.ndarray] = None
        self._dep_var: Optional[np.ndarray] = None
        self._sample_mask: Optional[list[bool]] = None
        self._coef_names: list[str] = []
        self._collinear_dropped: list[str] = []
        self._n_input_rows: int = 0

        # Fitted state
        self._is_fitted: bool = False
        self._beta: Optional[np.ndarray] = None
        self._cov_beta: Optional[np.ndarray] = None
        self._mu: Optional[np.ndarray] = None
        self._eta: Optional[np.ndarray] = None
        self._result: Optional[ResultSchema] = None

    def _link_inv(self, eta: np.ndarray) -> np.ndarray:
        """Inverse link function: mu = g^{-1}(eta)."""
        raise NotImplementedError

    def _link_deriv(self, eta: np.ndarray, mu: np.ndarray) -> np.ndarray:
        """Derivative of link wrt mu: g'(mu)."""
        raise NotImplementedError

    def _variance(self, mu: np.ndarray) -> np.ndarray:
        """Variance function V(mu)."""
        raise NotImplementedError

    def _loglik(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Log-likelihood for a single observation (summed)."""
        raise NotImplementedError

    def _deviance(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Deviance (optional, used by Poisson)."""
        raise NotImplementedError

    def _null_loglik(self, y: np.ndarray) -> float:
        """Log-likelihood of the null model (intercept only)."""
        raise NotImplementedError

    def _prepare_data(self, cluster_var: Optional[str] = None) -> tuple[np.ndarray, np.ndarray, list[bool], Optional[np.ndarray]]:
        """Prepare design matrix and dependent variable."""
        all_vars = [self.y] + self.x
        if cluster_var is not None and cluster_var not in all_vars:
            all_vars.append(cluster_var)

        df = self.data[all_vars].copy()
        n_input_rows = len(df)

        if self.missing == "drop":
            mask = df.notna().all(axis=1)
            df = df[mask]
        else:
            raise ValueError(f"missing='{self.missing}' not supported")

        sample_mask = mask.tolist()
        y = df[self.y].values.astype(np.float64)

        cluster_arr = None
        if cluster_var is not None:
            cluster_arr = df[cluster_var].values

        X_cols = []
        self._coef_names = []
        for var in self.x:
            X_cols.append(df[var].values.astype(np.float64))
            self._coef_names.append(var)

        if self.add_constant:
            X_cols.append(np.ones(len(df)))
            self._coef_names.append("_cons")

        X = np.column_stack(X_cols)
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
        from stataflow.estimators._vce_utils import detect_collinear_columns
        X_indep, dropped, kept = detect_collinear_columns(X, names)
        self._coef_names = [names[i] for i in kept]
        return X_indep, dropped

    def _irls_fit(self, X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
        """
        Run IRLS to estimate coefficients.

        Returns
        -------
        beta : np.ndarray
            Estimated coefficients.
        mu : np.ndarray
            Fitted means.
        eta : np.ndarray
            Linear predictors.
        converged : bool
            Whether the algorithm converged.
        """
        n, k = X.shape
        beta = np.zeros(k)

        ll_old = -np.inf
        converged = False

        for _ in range(self.max_iter):
            eta = X @ beta
            mu = self._link_inv(eta)

            # Working weights: w = 1 / (V(mu) * g'(mu)^2)
            gprime = self._link_deriv(eta, mu)
            var = self._variance(mu)
            w = 1.0 / (var * gprime ** 2)
            w = np.clip(w, 1e-12, 1e12)

            # Working response: z = eta + (y - mu) * g'(mu)
            z = eta + (y - mu) * gprime

            # Weighted least squares
            sqrt_w = np.sqrt(w)
            Xw = X * sqrt_w[:, np.newaxis]
            zw = z * sqrt_w

            try:
                beta_new = np.linalg.solve(Xw.T @ Xw, Xw.T @ zw)
            except np.linalg.LinAlgError:
                beta_new = np.linalg.lstsq(Xw, zw, rcond=None)[0]

            ll_new = self._loglik(y, mu)

            # Convergence check
            rel_change = abs(ll_new - ll_old) / (abs(ll_old) + 1.0)
            param_change = np.max(np.abs(beta_new - beta))

            if rel_change < self.tol and param_change < self.tol:
                converged = True
                beta = beta_new
                break

            beta = beta_new
            ll_old = ll_new

        eta = X @ beta
        mu = self._link_inv(eta)
        return beta, mu, eta, converged

    def _compute_vce(
        self,
        X: np.ndarray,
        y: np.ndarray,
        mu: np.ndarray,
        eta: np.ndarray,
        beta: np.ndarray,
        vce: str,
        cluster_arr: Optional[np.ndarray],
    ) -> tuple[np.ndarray, Optional[int]]:
        """Compute variance-covariance matrix."""
        n, k = X.shape
        gprime = self._link_deriv(eta, mu)
        var = self._variance(mu)
        w = 1.0 / (var * gprime ** 2)
        w = np.clip(w, 1e-12, 1e12)

        sqrt_w = np.sqrt(w)
        Xw = X * sqrt_w[:, np.newaxis]
        XtX_inv = np.linalg.inv(Xw.T @ Xw)

        cluster_count = None

        if vce == "ols":
            cov_beta = XtX_inv
        elif vce == "robust":
            # Sandwich: meat = X' diag((y-mu)^2) X
            residuals = y - mu
            meat = (X * residuals[:, np.newaxis]).T @ (X * residuals[:, np.newaxis])
            cov_beta = XtX_inv @ meat @ XtX_inv
        elif vce == "cluster":
            residuals = y - mu
            from stataflow.estimators._vce_utils import compute_cluster_meat
            meat, cluster_count = compute_cluster_meat(X, residuals, cluster_arr)
            n_adj = (n - 1) / (n - k) if n > k else 1.0
            g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
            cov_beta = n_adj * g_adj * XtX_inv @ meat @ XtX_inv
        else:
            raise ValueError(f"vce='{vce}' not supported")

        return cov_beta, cluster_count

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """Fit GLM model."""
        if vce not in ("ols", "robust", "cluster"):
            raise ValueError(f"vce='{vce}' not supported. Use 'ols', 'robust', or 'cluster'.")
        if vce == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'.")
        if vce != "cluster" and cluster is not None:
            raise ValueError("cluster only used when vce='cluster'.")

        X, y, sample_mask, cluster_arr = self._prepare_data(cluster_var=cluster)
        n = len(y)
        k = X.shape[1]

        beta, mu, eta, converged = self._irls_fit(X, y)

        ll_model = self._loglik(y, mu)
        ll_null = self._null_loglik(y)
        pseudo_r2 = 1.0 - ll_model / ll_null if ll_null != 0 else None

        df_model = float(k - 1) if self.add_constant else float(k)
        df_resid = float(n - k)

        if vce == "cluster" and cluster_arr is not None:
            unique_clusters = np.unique(cluster_arr)
            cluster_count = len(unique_clusters)
            df_resid = float(cluster_count - 1)
        else:
            cluster_count = None

        cov_beta, cluster_count_vce = self._compute_vce(X, y, mu, eta, beta, vce, cluster_arr)
        if cluster_count is None:
            cluster_count = cluster_count_vce

        diag_cov = np.diag(cov_beta)
        diag_cov = np.maximum(diag_cov, 0)
        se = np.sqrt(diag_cov)

        z_stats = beta / se
        p_values = 2 * (1 - norm_dist.cdf(np.abs(z_stats)))
        z_crit = norm_dist.ppf(1 - alpha / 2)
        ci_low = beta - z_crit * se
        ci_high = beta + z_crit * se

        # LR chi2
        chi2 = 2.0 * (ll_model - ll_null)
        chi2_pvalue = 1.0 - chi2_dist.cdf(chi2, df=df_model) if df_model > 0 else None

        # Deviance
        try:
            deviance = self._deviance(y, mu)
        except NotImplementedError:
            deviance = None

        # Build result
        result = ResultSchema()
        result.model = ModelInfo(
            command=self._stata_command,
            estimator_family=self._estimator_family,
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
            rank=k,
            ll=ll_model,
            pseudo_r2=pseudo_r2,
            f_stat=chi2,
            f_pvalue=chi2_pvalue,
            deviance=deviance,
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
        warnings = []
        if self._collinear_dropped:
            warnings.append(f"Collinear variables dropped: {', '.join(self._collinear_dropped)}")
        if not converged:
            warnings.append("IRLS did not converge")
        result.diagnostics = DiagnosticsInfo(
            cluster_count=cluster_count,
            warnings=warnings,
        )
        result.provenance = ProvenanceInfo(
            source="python",
            stata_version_target="17",
            stata_command=f"{self._stata_command} {self.y} {' '.join(self.x)}",
        )

        # Store fitted state for postestimation
        self._is_fitted = True
        self._beta = beta
        self._cov_beta = cov_beta
        self._mu = mu
        self._eta = eta
        self._result = result

        return result

    def predict(self, type: str = "xb", newdata: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Generate predictions after fitting."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        if type not in ("xb", "pr", "mu"):
            raise ValueError(f"type='{type}' not supported for {self.__class__.__name__}. Use 'xb', 'pr', or 'mu'.")

        if newdata is not None:
            df = newdata[self.x].copy()
            if self.add_constant:
                df["_cons"] = 1.0
            X = df.values.astype(np.float64)
            beta = np.zeros(X.shape[1])
            for i, name in enumerate((self.x + ["_cons"]) if self.add_constant else self.x):
                if name in self._coef_names:
                    beta[i] = self._beta[self._coef_names.index(name)]
            eta = X @ beta
        else:
            eta = self._eta

        if type == "xb":
            return eta
        return self._link_inv(eta)

    def margins(self, type: str = "dydx") -> SimpleNamespace:
        """Compute marginal effects."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted yet. Call fit() first.")
        from stataflow.postestimation import (
            margins_ame_logit, margins_mem_logit,
            margins_ame_probit, margins_mem_probit,
            margins_ame_poisson, margins_mem_poisson,
            _build_margins_result,
        )

        X = self._design_matrix
        if self.__class__.__name__ == "Logit":
            if type == "dydx":
                effects, J = margins_ame_logit(self._beta, X)
            else:
                effects, J = margins_mem_logit(self._beta, X)
        elif self.__class__.__name__ == "Probit":
            if type == "dydx":
                effects, J = margins_ame_probit(self._beta, X)
            else:
                effects, J = margins_mem_probit(self._beta, X)
        elif self.__class__.__name__ == "Poisson":
            if type == "dydx":
                effects, J = margins_ame_poisson(self._beta, X)
            else:
                effects, J = margins_mem_poisson(self._beta, X)
        else:
            raise ValueError(f"margins not supported for {self.__class__.__name__}")

        return _build_margins_result(
            effects, J, self._cov_beta, self._coef_names, self._result.sample.nobs
        )


class Logit(GLMBase):
    """Logistic regression aligned with Stata's logit."""

    _stata_command = "logit"
    _estimator_family = "logit"

    def _link_inv(self, eta: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-eta))

    def _link_deriv(self, eta: np.ndarray, mu: np.ndarray) -> np.ndarray:
        # g'(mu) = 1 / (mu * (1 - mu))
        # For logit, this equals 1 / (Lambda(eta) * (1 - Lambda(eta)))
        return 1.0 / (mu * (1.0 - mu))

    def _variance(self, mu: np.ndarray) -> np.ndarray:
        return mu * (1.0 - mu)

    def _loglik(self, y: np.ndarray, mu: np.ndarray) -> float:
        # ll = sum(y * log(mu) + (1-y) * log(1-mu))
        mu = np.clip(mu, 1e-15, 1 - 1e-15)
        return float(np.sum(y * np.log(mu) + (1.0 - y) * np.log(1.0 - mu)))

    def _deviance(self, y: np.ndarray, mu: np.ndarray) -> float:
        mu = np.clip(mu, 1e-15, 1 - 1e-15)
        term = np.zeros_like(y, dtype=np.float64)
        y1 = y == 1
        y0 = y == 0
        mask = ~y1 & ~y0
        term[y1] = -np.log(mu[y1])
        term[y0] = -np.log(1.0 - mu[y0])
        term[mask] = y[mask] * np.log(y[mask] / mu[mask]) + (1.0 - y[mask]) * np.log((1.0 - y[mask]) / (1.0 - mu[mask]))
        return float(2.0 * np.sum(term))

    def _null_loglik(self, y: np.ndarray) -> float:
        n = len(y)
        n1 = float(np.sum(y))
        n0 = n - n1
        if n1 == 0 or n0 == 0:
            return 0.0
        return n1 * np.log(n1 / n) + n0 * np.log(n0 / n)


class Probit(GLMBase):
    """Probit regression aligned with Stata's probit."""

    _stata_command = "probit"
    _estimator_family = "probit"

    def _link_inv(self, eta: np.ndarray) -> np.ndarray:
        from scipy.stats import norm
        return norm.cdf(eta)

    def _link_deriv(self, eta: np.ndarray, mu: np.ndarray) -> np.ndarray:
        from scipy.stats import norm
        phi = norm.pdf(eta)
        # g'(mu) = 1 / phi(eta)
        phi = np.clip(phi, 1e-15, np.inf)
        return 1.0 / phi

    def _variance(self, mu: np.ndarray) -> np.ndarray:
        return mu * (1.0 - mu)

    def _loglik(self, y: np.ndarray, mu: np.ndarray) -> float:
        from scipy.stats import norm
        mu = np.clip(mu, 1e-15, 1 - 1e-15)
        return float(np.sum(y * np.log(mu) + (1.0 - y) * np.log(1.0 - mu)))

    def _deviance(self, y: np.ndarray, mu: np.ndarray) -> float:
        raise NotImplementedError

    def _compute_vce(
        self,
        X: np.ndarray,
        y: np.ndarray,
        mu: np.ndarray,
        eta: np.ndarray,
        beta: np.ndarray,
        vce: str,
        cluster_arr: Optional[np.ndarray],
    ) -> tuple[np.ndarray, Optional[int]]:
        """Compute VCE using observed Hessian for probit to match Stata."""
        from scipy.stats import norm
        n, k = X.shape

        def _score(b):
            et = X @ b
            m = norm.cdf(et)
            ph = norm.pdf(et)
            m = np.clip(m, 1e-15, 1 - 1e-15)
            return X.T @ (ph * (y - m) / (m * (1 - m)))

        eps = 1e-7
        H = np.zeros((k, k))
        for j in range(k):
            bp = beta.copy()
            bp[j] += eps
            bm = beta.copy()
            bm[j] -= eps
            H[:, j] = (_score(bp) - _score(bm)) / (2 * eps)

        # Observed information = -H
        try:
            cov_bread = np.linalg.inv(-H)
        except np.linalg.LinAlgError:
            cov_bread = np.linalg.pinv(-H)

        cluster_count = None
        phi = norm.pdf(eta)
        mu_clip = np.clip(mu, 1e-15, 1 - 1e-15)

        if vce == "ols":
            cov_beta = cov_bread
        elif vce == "robust":
            score_i = phi * (y - mu) / (mu_clip * (1 - mu_clip))
            meat = (X * score_i[:, np.newaxis]).T @ (X * score_i[:, np.newaxis])
            n_adj = n / (n - 1) if n > 1 else 1.0
            cov_beta = n_adj * cov_bread @ meat @ cov_bread
        elif vce == "cluster":
            unique_clusters = np.unique(cluster_arr)
            cluster_count = len(unique_clusters)
            meat = np.zeros((k, k))
            for g in unique_clusters:
                mask_g = cluster_arr == g
                X_g = X[mask_g]
                phi_g = phi[mask_g]
                y_g = y[mask_g]
                mu_g = mu_clip[mask_g]
                score_g = X_g.T @ (phi_g * (y_g - mu_g) / (mu_g * (1 - mu_g)))
                meat += np.outer(score_g, score_g)
            n_adj = (n - 1) / (n - k) if n > k else 1.0
            g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
            cov_beta = n_adj * g_adj * cov_bread @ meat @ cov_bread
        else:
            raise ValueError(f"vce='{vce}' not supported")

        return cov_beta, cluster_count

    def _null_loglik(self, y: np.ndarray) -> float:
        n = len(y)
        n1 = float(np.sum(y))
        n0 = n - n1
        if n1 == 0 or n0 == 0:
            return 0.0
        return n1 * np.log(n1 / n) + n0 * np.log(n0 / n)


class Poisson(GLMBase):
    """Poisson regression aligned with Stata's poisson."""

    _stata_command = "poisson"
    _estimator_family = "poisson"

    def _link_inv(self, eta: np.ndarray) -> np.ndarray:
        return np.exp(eta)

    def _link_deriv(self, eta: np.ndarray, mu: np.ndarray) -> np.ndarray:
        # g(mu) = log(mu), g'(mu) = 1/mu
        mu = np.clip(mu, 1e-15, np.inf)
        return 1.0 / mu

    def _variance(self, mu: np.ndarray) -> np.ndarray:
        return mu

    def _loglik(self, y: np.ndarray, mu: np.ndarray) -> float:
        from scipy.special import gammaln
        mu = np.clip(mu, 1e-15, np.inf)
        # ll = sum(y * log(mu) - mu - log(y!))
        # Stata includes log(y!), so we match it exactly
        log_y_fact = gammaln(y + 1)
        return float(np.sum(y * np.log(mu) - mu - log_y_fact))

    def _deviance(self, y: np.ndarray, mu: np.ndarray) -> float:
        mu = np.clip(mu, 1e-15, np.inf)
        # D = 2 * sum(y * log(y/mu) - (y - mu))
        # When y == 0, y*log(y/mu) is treated as 0
        y_safe = np.where(y == 0, 1e-15, y)
        term = y_safe * np.log(y_safe / mu) - (y_safe - mu)
        # Correct the y=0 case: limit of y*log(y) as y->0 is 0, so term should be mu when y=0
        zero_mask = y == 0
        term = np.where(zero_mask, mu, term)
        return float(2.0 * np.sum(term))

    def _null_loglik(self, y: np.ndarray) -> float:
        from scipy.special import gammaln
        ybar = np.mean(y)
        if ybar <= 0:
            return 0.0
        # ll_null = sum(y * log(ybar) - ybar - log(y!))
        return float(np.sum(y * np.log(ybar) - ybar - gammaln(y + 1)))
