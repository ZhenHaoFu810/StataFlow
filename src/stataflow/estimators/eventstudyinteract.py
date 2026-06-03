"""Event Study Interact estimator (Sun & Abraham)."""

import numpy as np
import pandas as pd
from scipy.stats import norm as norm_dist
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


class EventStudyInteract:
    """
    Sun & Abraham interaction-weighted event-study estimator.

    Parameters
    ----------
    data : pd.DataFrame
        Input data.
    y : str
        Dependent variable name.
    event_dummies : list[str]
        List of pre-generated relative time dummy variable names.
    cohort : str
        Cohort variable name (first treatment period).
    control_cohort : str
        Binary indicator variable name for control cohort.
    absorb : list[str]
        List of categorical variables to absorb as fixed effects.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y: str,
        event_dummies: list[str],
        cohort: str,
        control_cohort: str,
        absorb: list[str],
        covariates: Optional[list[str]] = None,
        weights: Optional[str] = None,
    ):
        self.data = data.copy()
        self.y_var = y
        self.event_dummies = list(event_dummies)
        self.cohort_var = cohort
        self.control_cohort_var = control_cohort
        self.absorb_vars = list(absorb)
        self.covariates = list(covariates) if covariates is not None else []
        self.weights_var = weights

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """
        Fit interaction-weighted event-study model.

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
        if vce not in ("ols", "cluster"):
            raise ValueError(f"vce='{vce}' not supported. Use 'ols' or 'cluster'.")
        if vce == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'.")

        df = self.data.copy()

        # Sample screening
        key_vars = (
            [self.y_var, self.cohort_var, self.control_cohort_var]
            + self.event_dummies
            + self.absorb_vars
            + self.covariates
        )
        if cluster and cluster not in key_vars:
            key_vars.append(cluster)
        if self.weights_var is not None and self.weights_var not in key_vars:
            key_vars.append(self.weights_var)
        mask = df[key_vars].notna().all(axis=1)
        df = df.loc[mask].copy()

        nobs_all = len(df)

        # Prior weights (aweight)
        w = np.ones(nobs_all)
        if self.weights_var is not None:
            w = df[self.weights_var].values.astype(np.float64)
            w = w * nobs_all / np.sum(w)

        # Create nD_h = D_h * (1 - control_cohort)
        non_control_mask = df[self.control_cohort_var] == 0
        nD_cols = []
        for d in self.event_dummies:
            col = f"_n{d}"
            df[col] = df[d] * non_control_mask.astype(float)
            nD_cols.append(col)

        # Cohort list (only non-control cohorts)
        cohort_list = sorted(
            df.loc[non_control_mask, self.cohort_var].dropna().unique()
        )
        n_cohort = len(cohort_list)
        n_rel = len(self.event_dummies)

        # Step 1: Cohort shares via weighted regression of cohort indicator on nD_h
        X_nd = df.loc[non_control_mask, nD_cols].values
        w_nc = w[non_control_mask.values]
        N_nc = len(X_nd)
        XtX_nd = X_nd.T @ (w_nc[:, None] * X_nd)
        XtX_nd_inv = np.linalg.pinv(XtX_nd)

        ff_w = np.zeros((n_cohort, n_rel))  # rows = cohorts, cols = event times
        residuals_list = []

        for i, g in enumerate(cohort_list):
            y_g = (df.loc[non_control_mask, self.cohort_var] == g).astype(float).values
            beta_g = XtX_nd_inv @ (X_nd.T @ (w_nc * y_g))
            ff_w[i, :] = beta_g
            resid_g = y_g - X_nd @ beta_g
            residuals_list.append(resid_g)

        # Step 2: Robust covariance of cohort shares (avar-style, weighted)
        # Stack residuals: shape (N_nc, n_cohort)
        resid_mat = np.column_stack(residuals_list)  # N_nc x n_cohort
        # Compute S = sum_i (s_i s_i') where s_i is the stacked score
        # For each obs, score is [X_i' * e_1i, ..., X_i' * e_Gi] as a vector
        S = np.zeros((n_cohort * n_rel, n_cohort * n_rel))
        sqrt_w_nc = np.sqrt(w_nc)
        for idx in range(N_nc):
            xi = X_nd[idx, :]  # shape (n_rel,)
            ei = resid_mat[idx, :]  # shape (n_cohort,)
            # Weighted score
            score_i = (xi[:, None] * ei[None, :]).ravel(order="F") * sqrt_w_nc[idx]
            S += np.outer(score_i, score_i)

        KSxxi = np.kron(np.eye(n_cohort), XtX_nd_inv)
        Sigma_ff = KSxxi @ S @ KSxxi

        # Step 3: Interaction regression via iterative TWFE residualization
        interaction_cols = []
        for d in self.event_dummies:
            for g in cohort_list:
                col = f"_int_{d}_{g}"
                df[col] = (df[self.cohort_var] == g).astype(float) * df[d]
                interaction_cols.append(col)

        # Residualize y and interaction columns by iterative weighted demeaning within absorb_vars
        def _twfe_residualize(values: np.ndarray, wgt: np.ndarray) -> np.ndarray:
            resid = values.copy()
            for _ in range(10000):
                max_diff = 0.0
                for fe_var in self.absorb_vars:
                    df_tmp = pd.DataFrame({'resid': resid, 'w': wgt, 'fe': df[fe_var].values})
                    group_means = df_tmp.groupby('fe').apply(
                        lambda g: np.average(g['resid'], weights=g['w']),
                        include_groups=False
                    )
                    means = df_tmp['fe'].map(group_means).values
                    resid -= means
                    max_diff = max(max_diff, np.nanmax(np.abs(means)))
                if max_diff < 1e-14:
                    break
            return resid

        y_resid = _twfe_residualize(df[self.y_var].values.astype(np.float64), w)
        X_int = np.column_stack([df[c].values.astype(np.float64) for c in interaction_cols])
        X_resid = np.column_stack([_twfe_residualize(X_int[:, i], w) for i in range(X_int.shape[1])])

        # Residualize covariates if provided
        n_cov = len(self.covariates)
        if n_cov > 0:
            X_cov = np.column_stack([df[c].values.astype(np.float64) for c in self.covariates])
            X_cov_resid = np.column_stack([_twfe_residualize(X_cov[:, i], w) for i in range(n_cov)])
            X_reg = np.column_stack([X_resid, X_cov_resid])
            # Track which columns are interaction vs covariate
            interaction_idx = list(range(len(interaction_cols)))
            covariate_idx = list(range(len(interaction_cols), len(interaction_cols) + n_cov))
        else:
            X_reg = X_resid
            interaction_idx = list(range(len(interaction_cols)))
            covariate_idx = []

        # Detect collinearity in residualized design matrix (same columns as reghdfe LSDV)
        R_qr = np.linalg.qr(X_reg, mode="r")
        tol = 1e-10
        independent = []
        dropped_indices = []
        for i in range(X_reg.shape[1]):
            if i < R_qr.shape[0] and abs(R_qr[i, i]) > tol:
                independent.append(i)
            else:
                dropped_indices.append(i)

        # Weighted OLS on kept columns only
        X_kept = X_reg[:, independent]
        XtX_kept = X_kept.T @ (w[:, None] * X_kept)
        beta_kept = np.linalg.solve(XtX_kept, X_kept.T @ (w * y_resid))
        resid_ols = y_resid - X_kept @ beta_kept

        # Reconstruct full beta vector with zeros for dropped columns
        beta_full_reg = np.zeros(X_reg.shape[1])
        beta_full_reg[independent] = beta_kept

        # Extract interaction coefficients for IW aggregation
        beta_full = beta_full_reg[:len(interaction_cols)]

        n = len(y_resid)
        k_total = len(interaction_cols)
        n_id_levels = df[self.absorb_vars[0]].nunique()
        n_year_levels = df[self.absorb_vars[1]].nunique()
        k_full = k_total + n_cov + n_id_levels - 1 + n_year_levels - 1
        k_kept = len(independent)

        if vce == "ols":
            sigma2 = float(np.sum(w * resid_ols ** 2)) / (n - k_full) if n > k_full else 0.0
            VV_kept = sigma2 * np.linalg.inv(XtX_kept)
            df_resid = float(n - k_full)
        else:
            # Cluster-robust VCE aligned with reghdfe (weighted)
            cluster_arr = df[cluster].values
            unique_clusters = np.unique(cluster_arr)
            G = len(unique_clusters)

            XtX_inv = np.linalg.inv(XtX_kept)
            meat = np.zeros((k_kept, k_kept))
            sqrt_w = np.sqrt(w)
            for g_val in unique_clusters:
                mask_g = cluster_arr == g_val
                X_g = X_kept[mask_g]
                e_g = resid_ols[mask_g]
                sw_g = sqrt_w[mask_g]
                Xe_g = X_g.T @ (sw_g * e_g)
                meat += np.outer(Xe_g, Xe_g)

            # Small-sample adjustment: id FEs are nested in cluster
            k_eff = k_kept + n_year_levels - 1
            n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
            g_adj = G / (G - 1) if G > 1 else 1.0
            VV_kept = n_adj * g_adj * XtX_inv @ meat @ XtX_inv
            df_resid = float(G - 1)

        # Embed VV_kept into full ((k_total + n_cov) x (k_total + n_cov)) matrix
        VV_all = np.zeros((k_total + n_cov, k_total + n_cov))
        if k_kept > 0:
            VV_all[np.ix_(independent, independent)] = VV_kept

        # Extract interaction-only covariance for IW aggregation
        VV = VV_all[:k_total, :k_total]

        # Extract coefficients into matrix: rows = cohorts, cols = event times
        evt_bb = beta_full.reshape((n_cohort, n_rel), order="F")

        # Step 4: IW coefficients
        b_iw = np.sum(ff_w * evt_bb, axis=0)  # shape (n_rel,)

        # Step 5: Variance of IW estimator
        # Build wlong: nr x (nr * nc)
        w = ff_w.T  # nr x nc
        wlong_blocks = []
        for i in range(n_rel):
            block = w * np.eye(n_rel)[i : i + 1, :].T  # nr x nc, keeps only row i
            wlong_blocks.append(block)
        wlong = np.hstack(wlong_blocks)  # nr x (nr * nc)

        V_iw = wlong @ VV @ wlong.T

        # Add variance from cohort share estimation
        for i in range(n_rel):
            for j in range(i + 1):
                share_idx = np.arange(0, n_cohort * n_rel, n_rel)
                Vshare_evt = Sigma_ff[
                    share_idx + i, :
                ][:, share_idx + j]
                contrib = float(evt_bb[:, i] @ Vshare_evt @ evt_bb[:, j])
                V_iw[i, j] += contrib
                if i != j:
                    V_iw[j, i] += contrib

        se_iw = np.sqrt(np.diag(V_iw).clip(min=0.0))

        # Build coefficient rows
        coefficients = []
        for idx, name in enumerate(self.event_dummies):
            beta = float(b_iw[idx])
            se = float(se_iw[idx])
            z_stat = beta / se if se > 0 else 0.0
            p_value = 2 * (1 - norm_dist.cdf(abs(z_stat))) if se > 0 else 1.0
            ci_low = beta - norm_dist.ppf(1 - alpha / 2) * se if se > 0 else beta
            ci_high = beta + norm_dist.ppf(1 - alpha / 2) * se if se > 0 else beta

            coefficients.append(
                CoefficientRow(
                    name=name,
                    beta=beta,
                    std_err=se,
                    t_stat=z_stat,
                    p_value=p_value,
                    ci_low=ci_low,
                    ci_high=ci_high,
                )
            )

        model_info = ModelInfo(
            command="eventstudyinteract",
            estimator_family="eventstudyinteract",
            vcetype=vce,
            cluster_var=cluster if cluster else None,
        )

        sample_info = SampleInfo(nobs=nobs_all, n_input_rows=nobs_all)

        fit_info = FitInfo(
            df_model=float(n_rel),
            df_resid=df_resid,
        )

        variance_info = VarianceInfo(
            row_names=[c.name for c in coefficients],
            values=V_iw.tolist(),
        )

        provenance = ProvenanceInfo(
            stata_command=(
                f"eventstudyinteract {self.y_var} {' '.join(self.event_dummies)}, "
                f"cohort({self.cohort_var}) control_cohort({self.control_cohort_var}) "
                f"absorb({' '.join(self.absorb_vars)}) vce({vce})"
            ),
        )

        return ResultSchema(
            model=model_info,
            sample=sample_info,
            fit=fit_info,
            coefficients=coefficients,
            variance=variance_info,
            diagnostics=DiagnosticsInfo(),
            provenance=provenance,
        )
