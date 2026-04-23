"""DID imputation estimator (Borusyak, Jaravel, Spiess)."""

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


class DIDImputation:
    """
    DID imputation estimator (Borusyak, Jaravel, Spiess 2021).

    Parameters
    ----------
    data : pd.DataFrame
        Input data.
    y : str
        Dependent variable name.
    id : str
        Unit identifier variable name.
    time : str
        Time identifier variable name.
    first_treat : str
        Variable recording the first treatment period for each unit.
        Never-treated units should have value 0 or missing.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y: str,
        id: str,
        time: str,
        first_treat: str,
    ):
        self.data = data.copy()
        self.y_var = y
        self.id_var = id
        self.time_var = time
        self.first_treat_var = first_treat

    def fit(
        self,
        cluster: Optional[str] = None,
        allhorizons: bool = False,
        autosample: bool = False,
        window: Optional[list[int]] = None,
        minn: Optional[int] = None,
        alpha: float = 0.05,
    ) -> ResultSchema:
        """
        Fit DID imputation model.

        Parameters
        ----------
        cluster : str, optional
            Cluster variable name for cluster-robust standard errors.
            Default is the unit identifier.
        allhorizons : bool
            If True, compute all possible event time horizons.
        autosample : bool
            If True, automatically drop observations where FE cannot be imputed.
        window : list[int], optional
            Two-element list [min, max] restricting the relative-time horizons
            to compute. Applied after ``allhorizons`` filtering.
        minn : int, optional
            Minimum number of imputable observations required per horizon.
            Horizons with fewer imputable observations are skipped.
        alpha : float
            Significance level for confidence intervals.

        Returns
        -------
        ResultSchema
            Fitted result object.
        """
        if cluster is None:
            cluster = self.id_var

        df = self.data.copy()

        # Sample screening: drop rows with missing key variables
        key_vars = [self.y_var, self.id_var, self.time_var, self.first_treat_var]
        mask = df[key_vars].notna().all(axis=1)
        df = df.loc[mask].copy()

        # Compute treatment indicator and relative time
        df["_D"] = (df[self.time_var] >= df[self.first_treat_var]).astype(int)
        df.loc[df[self.first_treat_var] <= 0, "_D"] = 0
        df["_K"] = df[self.time_var] - df[self.first_treat_var]
        df.loc[df[self.first_treat_var] <= 0, "_K"] = np.nan

        # Control sample: not-yet-treated + never-treated
        control_mask = df["_D"] == 0

        # Fit TWFE on controls using iterative demeaning
        alpha_fe, gamma_fe = self._fit_twfe(
            df, self.y_var, self.id_var, self.time_var, control_mask
        )

        # Predict Y0 for all observations
        df["_Y0"] = df[self.id_var].map(alpha_fe) + df[self.time_var].map(gamma_fe)

        # Determine which observations can be imputed
        # A unit must have at least one control obs for alpha to be valid
        # A time must have at least one control obs for gamma to be valid
        unit_has_control = df.loc[control_mask, self.id_var].unique()
        time_has_control = df.loc[control_mask, self.time_var].unique()
        df["_can_impute"] = (
            df[self.id_var].isin(unit_has_control)
            & df[self.time_var].isin(time_has_control)
        ).astype(int)

        # Compute effect for all ever-treated observations (including pretrends)
        df["_effect"] = np.nan
        ever_treated_mask = df[self.first_treat_var] > 0
        df.loc[ever_treated_mask, "_effect"] = (
            df.loc[ever_treated_mask, self.y_var] - df.loc[ever_treated_mask, "_Y0"]
        )

        # Determine horizons to compute
        if allhorizons:
            horizons = sorted(df.loc[ever_treated_mask, "_K"].dropna().unique())
        else:
            horizons = sorted(
                [h for h in df.loc[ever_treated_mask, "_K"].dropna().unique() if h >= 0]
            )

        # Apply window restriction
        if window is not None:
            if len(window) != 2:
                raise ValueError("window must be a two-element list or tuple [min, max]")
            horizons = [h for h in horizons if window[0] <= h <= window[1]]

        # Compute tau for each horizon
        tau_results = []
        for h in horizons:
            h_mask = ever_treated_mask & (df["_K"] == h)
            if h_mask.sum() == 0:
                continue

            # Check if any imputable treated obs exist
            imputable_mask = h_mask & (df["_can_impute"] == 1)
            n_total = h_mask.sum()
            n_imputable = imputable_mask.sum()

            # minn: skip horizon if too few imputable observations
            if minn is not None and n_imputable < minn:
                continue

            if n_imputable == 0:
                if not autosample:
                    raise RuntimeError(
                        f"Could not impute FE for horizon tau{int(h)}. "
                        "Use autosample=True to drop automatically."
                    )
                # Coefficient completely dropped
                tau_results.append({
                    "name": f"tau{int(h)}",
                    "beta": 0.0,
                    "std_err": 0.0,
                    "dropped": True,
                    "n_total": n_total,
                    "n_imputable": 0,
                })
                continue

            # Autosample: drop non-imputable observations and re-normalize
            if n_imputable < n_total and autosample:
                effective_mask = imputable_mask
            else:
                effective_mask = h_mask

            beta = df.loc[effective_mask, "_effect"].mean()

            tau_results.append({
                "name": f"tau{int(h)}",
                "beta": float(beta),
                "std_err": None,  # computed later
                "dropped": False,
                "n_total": n_total,
                "n_imputable": n_imputable,
                "effective_mask": effective_mask,
            })

        # Compute effective sample size (after autosample)
        effective_sample_mask = control_mask.copy()
        for tr in tau_results:
            if not tr.get("dropped", False):
                effective_sample_mask = effective_sample_mask | tr["effective_mask"]
        nobs_all = int(effective_sample_mask.sum())

        # Compute standard errors
        if cluster:
            tau_results = self._compute_se(
                df, tau_results, cluster, control_mask, ever_treated_mask
            )

        # Build coefficient rows
        coefficients = []
        for tr in tau_results:
            beta = tr["beta"]
            se = tr.get("std_err", 0.0) or 0.0
            z_stat = beta / se if se > 0 else 0.0
            p_value = 2 * (1 - norm_dist.cdf(abs(z_stat))) if se > 0 else 1.0
            ci_low = beta - norm_dist.ppf(1 - alpha / 2) * se if se > 0 else beta
            ci_high = beta + norm_dist.ppf(1 - alpha / 2) * se if se > 0 else beta

            coefficients.append(CoefficientRow(
                name=tr["name"],
                beta=beta,
                std_err=se,
                t_stat=z_stat,
                p_value=p_value,
                ci_low=ci_low,
                ci_high=ci_high,
            ))

        nobs = int((df["_D"] == 0).sum())  # Control observations (Nc in Stata)

        # Build minimal result schema
        model_info = ModelInfo(
            command="did_imputation",
            estimator_family="did_imputation",
            vcetype="cluster" if cluster else "ols",
            cluster_var=cluster if cluster else None,
        )

        sample_info = SampleInfo(
            nobs=nobs_all,
            n_input_rows=nobs_all,
        )

        fit_info = FitInfo(
            df_model=float(len([c for c in coefficients if c.std_err > 0])),
            df_resid=float(nobs - 1) if cluster else float(nobs),
        )

        # Covariance matrix (only for non-dropped coefficients)
        active_coeffs = [c for c in coefficients if c.std_err > 0]
        cov = np.zeros((len(active_coeffs), len(active_coeffs)))
        for i, c in enumerate(active_coeffs):
            cov[i, i] = c.std_err ** 2

        variance_info = VarianceInfo(
            row_names=[c.name for c in active_coeffs],
            values=cov.tolist(),
        )

        diagnostics = DiagnosticsInfo()

        options = [f"cluster({cluster})"]
        if allhorizons:
            options.append("allhorizons")
        if autosample:
            options.append("autosample")
        if window is not None:
            options.append(f"window({window[0]} {window[1]})")
        if minn is not None:
            options.append(f"minn({minn})")
        provenance = ProvenanceInfo(
            stata_command=(
                f"did_imputation {self.y_var} {self.id_var} {self.time_var} "
                f"{self.first_treat_var}, {' '.join(options)}"
            ),
        )

        return ResultSchema(
            model=model_info,
            sample=sample_info,
            fit=fit_info,
            coefficients=coefficients,
            variance=variance_info,
            diagnostics=diagnostics,
            provenance=provenance,
        )

    def _fit_twfe(
        self,
        df: pd.DataFrame,
        y_var: str,
        id_var: str,
        time_var: str,
        control_mask: pd.Series,
        max_iter: int = 100000,
        tol: float = 1e-14,
    ) -> tuple[pd.Series, pd.Series]:
        """Fit TWFE model on control sample using iterative demeaning."""
        controls = df.loc[control_mask].copy()

        # Initialize FE
        alpha_fe = pd.Series(0.0, index=controls[id_var].unique())
        gamma_fe = pd.Series(0.0, index=controls[time_var].unique())

        for _ in range(max_iter):
            # Update alpha_i = mean(y_it - gamma_t) for controls in unit i
            controls["_resid"] = controls[y_var] - controls[time_var].map(gamma_fe)
            alpha_new = controls.groupby(id_var)["_resid"].mean()
            # Reindex to include all possible units
            alpha_new = alpha_new.reindex(alpha_fe.index, fill_value=0.0)

            # Update gamma_t = mean(y_it - alpha_i) for controls in time t
            controls["_resid"] = controls[y_var] - controls[id_var].map(alpha_new)
            gamma_new = controls.groupby(time_var)["_resid"].mean()
            gamma_new = gamma_new.reindex(gamma_fe.index, fill_value=0.0)

            max_diff = max(
                np.max(np.abs(alpha_new - alpha_fe)),
                np.max(np.abs(gamma_new - gamma_fe)),
            )
            alpha_fe = alpha_new
            gamma_fe = gamma_new

            if max_diff < tol:
                break

        return alpha_fe, gamma_fe

    def _compute_imputation_weights(
        self,
        df: pd.DataFrame,
        effective_mask: pd.Series,
        control_mask: pd.Series,
        id_var: str,
        time_var: str,
        max_iter: int = 100000,
        tol: float = 1e-14,
    ) -> pd.Series:
        """
        Compute imputation weights for standard errors.
        Returns a Series indexed like df.
        """
        # Initialize weights: 1/N_h on effective treated, 0 on controls
        w = pd.Series(0.0, index=df.index)
        n_eff = effective_mask.sum()
        if n_eff > 0:
            w.loc[effective_mask] = 1.0 / n_eff

        controls = df.loc[control_mask].copy()

        for _ in range(max_iter):
            # Demean within units (control obs only)
            # sumw = sum(wei * w) over ALL observations in the unit
            # denom = sum(wei) over CONTROL observations in the unit
            # update: w_control -= sumw / denom
            unit_sumw = df.groupby(id_var).apply(lambda g: w.loc[g.index].sum())
            unit_denom = controls.groupby(id_var).size()
            unit_adjustment = unit_sumw / unit_denom
            w.loc[control_mask] -= controls[id_var].map(unit_adjustment).values

            # Demean within times (control obs only)
            time_sumw = df.groupby(time_var).apply(lambda g: w.loc[g.index].sum())
            time_denom = controls.groupby(time_var).size()
            time_adjustment = time_sumw / time_denom
            w.loc[control_mask] -= controls[time_var].map(time_adjustment).values

            max_diff = max(
                unit_adjustment.abs().max() if len(unit_adjustment) > 0 else 0.0,
                time_adjustment.abs().max() if len(time_adjustment) > 0 else 0.0,
            )
            if max_diff < tol:
                break

        return w

    def _compute_se(
        self,
        df: pd.DataFrame,
        tau_results: list[dict],
        cluster_var: str,
        control_mask: pd.Series,
        treated_mask: pd.Series,
    ) -> list[dict]:
        """Compute cluster-robust standard errors."""
        for tr in tau_results:
            if tr.get("dropped", False):
                tr["std_err"] = 0.0
                continue

            effective_mask = tr["effective_mask"]
            tau_h = tr["beta"]

            # Compute imputation weights
            w = self._compute_imputation_weights(
                df, effective_mask, control_mask, self.id_var, self.time_var
            )

            # Compute residuals
            resid = pd.Series(np.nan, index=df.index)
            # Controls: resid = y - Y0
            resid.loc[control_mask] = (
                df.loc[control_mask, self.y_var] - df.loc[control_mask, "_Y0"]
            )
            # Treated: resid = effect - tau_h
            resid.loc[treated_mask] = df.loc[treated_mask, "_effect"] - tau_h

            # Cluster-level aggregated influence
            df["_influence"] = w * resid
            # Replace NaN with 0 (for observations not in control or treated with effect)
            df["_influence"] = df["_influence"].fillna(0.0)

            cluster_sums = df.groupby(cluster_var)["_influence"].sum()
            V = float((cluster_sums ** 2).sum())

            tr["std_err"] = np.sqrt(V) if V >= 0 else 0.0

        return tau_results
