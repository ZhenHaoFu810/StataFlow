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
        controls: Optional[list[str]] = None,
        unitcontrols: Optional[list[str]] = None,
        timecontrols: Optional[list[str]] = None,
        pretrends: int = 0,
        wtr: Optional[list[str]] = None,
        hetby: Optional[str] = None,
        saveestimates: Optional[str] = None,
        saveweights: bool = False,
        sum: bool = False,
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

        if sum and autosample:
            raise ValueError("sum cannot be combined with autosample")

        df = self.data.copy()

        # Sample screening: drop rows with missing key variables
        key_vars = [self.y_var, self.id_var, self.time_var, self.first_treat_var]
        cov_vars = []
        if controls is not None:
            cov_vars.extend(controls)
        if unitcontrols is not None:
            cov_vars.extend(unitcontrols)
        if timecontrols is not None:
            cov_vars.extend(timecontrols)
        all_vars = key_vars + cov_vars
        mask = df[all_vars].notna().all(axis=1)
        df = df.loc[mask].copy()

        # Compute treatment indicator and relative time
        df["_D"] = (df[self.time_var] >= df[self.first_treat_var]).astype(int)
        df.loc[df[self.first_treat_var] <= 0, "_D"] = 0
        df["_K_all"] = df[self.time_var] - df[self.first_treat_var]
        df["_K"] = df[self.time_var] - df[self.first_treat_var]
        df.loc[df[self.first_treat_var] <= 0, "_K"] = np.nan

        # Construct pretreatment dummies for pretrends test
        pretrend_cols = []
        if pretrends > 0:
            for h in range(1, pretrends + 1):
                col = f"_pre_{h}"
                df[col] = (df["_K"] == -h).astype(int).fillna(0)
                pretrend_cols.append(col)

        # Control sample: not-yet-treated + never-treated
        control_mask = df["_D"] == 0

        # Fit TWFE on controls (with covariates if provided)
        # When pretrends > 0, we run two regressions:
        # 1. Main regression WITHOUT pretrends for Y0 computation
        # 2. Auxiliary regression WITH pretrends for pretrends coefficients only
        has_covariates = (
            controls is not None or unitcontrols is not None or timecontrols is not None or pretrends > 0
        )
        cov_matrix = None
        col_names = None
        df_resid_ctrl = None
        cov_result_pre = None
        if has_covariates:
            # Main regression: without pretrends for Y0 computation
            cov_result = self._fit_twfe_covariates(
                df, self.y_var, self.id_var, self.time_var, control_mask,
                controls=controls, unitcontrols=unitcontrols, timecontrols=timecontrols,
                pretrend_cols=None,
                cluster=cluster,
            )
            alpha_fe = cov_result.get("alpha_fe")
            gamma_fe = cov_result.get("gamma_fe")
            beta_controls = cov_result.get("beta_controls")
            uc_slopes = cov_result.get("uc_slopes")
            tc_slopes = cov_result.get("tc_slopes")

            # Auxiliary regression: with pretrends for their coefficients
            if pretrends > 0:
                cov_result_pre = self._fit_twfe_covariates(
                    df, self.y_var, self.id_var, self.time_var, control_mask,
                    controls=controls, unitcontrols=unitcontrols, timecontrols=timecontrols,
                    pretrend_cols=pretrend_cols,
                    cluster=cluster,
                )
                cov_matrix = cov_result_pre.get("cov")
                col_names = cov_result_pre.get("col_names")
                df_resid_ctrl = cov_result_pre.get("df_resid")
            else:
                cov_matrix = cov_result.get("cov")
                col_names = cov_result.get("col_names")
                df_resid_ctrl = cov_result.get("df_resid")
        else:
            alpha_fe, gamma_fe = self._fit_twfe(
                df, self.y_var, self.id_var, self.time_var, control_mask
            )
            beta_controls = None
            uc_slopes = None
            tc_slopes = None

        # Predict Y0 for all observations
        df["_Y0"] = 0.0

        # Regular FEs
        if alpha_fe is not None:
            df["_Y0"] += df[self.id_var].map(alpha_fe).fillna(0.0)
        if gamma_fe is not None:
            df["_Y0"] += df[self.time_var].map(gamma_fe).fillna(0.0)

        # Unitcontrols: unit-specific intercepts and slopes
        if uc_slopes is not None:
            uc_alphas = uc_slopes.get("_intercepts", {})
            for uid, alpha in uc_alphas.items():
                df.loc[df[self.id_var] == uid, "_Y0"] += alpha
            for z, slopes in uc_slopes.items():
                if z == "_intercepts":
                    continue
                for uid, slope in slopes.items():
                    mask_u = df[self.id_var] == uid
                    df.loc[mask_u, "_Y0"] += df.loc[mask_u, z] * slope

        # Timecontrols: time-specific intercepts and slopes
        if tc_slopes is not None:
            tc_gammas = tc_slopes.get("_intercepts", {})
            for tval, gamma in tc_gammas.items():
                df.loc[df[self.time_var] == tval, "_Y0"] += gamma
            for w, slopes in tc_slopes.items():
                if w == "_intercepts":
                    continue
                for tval, slope in slopes.items():
                    mask_t = df[self.time_var] == tval
                    df.loc[mask_t, "_Y0"] += df.loc[mask_t, w] * slope

        # Global controls
        if beta_controls is not None:
            for j, c in enumerate(controls):
                df["_Y0"] += df[c] * beta_controls[j]

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

        # Determine horizons to compute. By default only post-treatment event
        # horizons are reported. allhorizons also keeps non-negative horizons
        # observed among never-treated rows (time - 0), which Stata reports as
        # omitted calendar-time coefficients.
        if allhorizons:
            observed_horizons = df["_K_all"].dropna().unique()
            horizons = sorted(observed_horizons)
        else:
            observed_horizons = df.loc[ever_treated_mask, "_K"].dropna().unique()
            horizons = sorted([h for h in observed_horizons if h >= 0])

        # Apply window restriction
        if window is not None:
            if len(window) != 2:
                raise ValueError("window must be a two-element list or tuple [min, max]")
            horizons = [h for h in horizons if window[0] <= h <= window[1]]

        # Build wtr entries
        wtr_entries = []
        if wtr is None and hetby is None:
            wtr_entries = [("tau", "_wtr_default")]
            df["_wtr_default"] = 1.0
        else:
            base_wtrs = []
            if wtr is None:
                base_wtrs = [("tau", None)]
            else:
                wtr_list = [wtr] if isinstance(wtr, str) else list(wtr)
                for w in wtr_list:
                    base_wtrs.append((w, w))
            if hetby is not None:
                hetby_values = sorted(
                    df.loc[ever_treated_mask & df[hetby].notna(), hetby].unique()
                )
                for base_name, base_col in base_wtrs:
                    for g in hetby_values:
                        entry_name = f"{base_name}_{g}"
                        entry_col = f"_wtr_{base_name}_{g}"
                        if base_col is None:
                            df[entry_col] = (
                                (df[hetby] == g) & ever_treated_mask
                            ).astype(float)
                        else:
                            df[entry_col] = (
                                df[base_col] * (df[hetby] == g).astype(float)
                            )
                        df.loc[~ever_treated_mask, entry_col] = 0.0
                        wtr_entries.append((entry_name, entry_col))
            else:
                for base_name, base_col in base_wtrs:
                    if base_col is None:
                        entry_col = "_wtr_default"
                        df[entry_col] = 1.0
                    else:
                        entry_col = base_col
                    wtr_entries.append((base_name, entry_col))

        explicit_wtr_list = (
            [wtr] if isinstance(wtr, str) else (list(wtr) if wtr is not None else [])
        )
        if len(explicit_wtr_list) > 1 and len(horizons) > 1:
            raise ValueError(
                "Multiple wtr variables cannot be combined with multiple horizons"
            )

        # Normalize weights
        for name, col in wtr_entries:
            norm_col = f"{col}_norm"
            wtr_mask = ever_treated_mask & df[col].notna() & (df[col] != 0)
            if not sum:
                w_sum = df.loc[wtr_mask, col].sum()
                if w_sum > 0:
                    df[norm_col] = df[col] / w_sum
                else:
                    df[norm_col] = 0.0
            else:
                df[norm_col] = df[col].fillna(0.0)

        # Compute tau for each horizon
        tau_results = []
        for wtr_name, wtr_col in wtr_entries:
            norm_col = f"{wtr_col}_norm"
            for h in horizons:
                h_mask = ever_treated_mask & (df["_K"] == h)
                wtr_mask = h_mask & df[norm_col].notna() & (df[norm_col] != 0)
                if wtr_mask.sum() == 0:
                    if allhorizons:
                        if wtr_name == "tau" and hetby is None:
                            coeff_name = f"tau{int(h)}"
                        else:
                            coeff_name = f"{wtr_name}_h{int(h)}"
                        tau_results.append({
                            "name": coeff_name,
                            "beta": 0.0,
                            "std_err": 0.0,
                            "dropped": True,
                            "n_total": 0,
                            "n_imputable": 0,
                        })
                    continue

                # Check if any imputable treated obs exist
                imputable_mask = wtr_mask & (df["_can_impute"] == 1)
                n_total = wtr_mask.sum()
                n_imputable = imputable_mask.sum()

                # minn: skip horizon if too few imputable observations
                if minn is not None and n_imputable < minn:
                    continue

                # Determine coefficient name
                if wtr_name == "tau" and hetby is None:
                    coeff_name = f"tau{int(h)}"
                else:
                    coeff_name = f"{wtr_name}_h{int(h)}"

                if n_imputable == 0:
                    if not autosample:
                        raise RuntimeError(
                            f"Could not impute FE for horizon {coeff_name}. "
                            "Use autosample=True to drop automatically."
                        )
                    # Coefficient completely dropped
                    tau_results.append({
                        "name": coeff_name,
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
                    effective_mask = wtr_mask

                weights = df.loc[effective_mask, norm_col]
                if not sum and weights.sum() > 0:
                    beta = (
                        df.loc[effective_mask, "_effect"]
                        * weights / weights.sum()
                    ).sum()
                else:
                    beta = (
                        df.loc[effective_mask, "_effect"]
                        * weights
                    ).sum()

                tau_results.append({
                    "name": coeff_name,
                    "beta": float(beta),
                    "std_err": None,  # computed later
                    "dropped": False,
                    "n_total": n_total,
                    "n_imputable": n_imputable,
                    "effective_mask": effective_mask,
                    "norm_col": norm_col,
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

        # Build coefficient rows for tau horizons
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

        # Extract pretrends coefficients and compute joint F test
        pretrend_warnings = []
        if pretrends > 0 and cov_matrix is not None and col_names is not None:
            pre_names = [f"_pre_{h}" for h in range(1, pretrends + 1)]
            try:
                pre_indices = [col_names.index(n) for n in pre_names]
            except ValueError:
                pre_indices = []
            if pre_indices:
                beta_full = cov_result_pre.get("beta") if cov_result_pre is not None else cov_result.get("beta")
                pre_beta = beta_full[pre_indices]
                pre_se = np.sqrt(np.diag(cov_matrix)[pre_indices])
                for h in range(1, pretrends + 1):
                    idx = h - 1
                    b = pre_beta[idx]
                    se = pre_se[idx]
                    z = b / se if se > 0 else 0.0
                    p = 2 * (1 - norm_dist.cdf(abs(z))) if se > 0 else 1.0
                    ci_low = b - norm_dist.ppf(1 - alpha / 2) * se if se > 0 else b
                    ci_high = b + norm_dist.ppf(1 - alpha / 2) * se if se > 0 else b
                    coefficients.append(CoefficientRow(
                        name=f"pre{h}",
                        beta=float(b),
                        std_err=float(se),
                        t_stat=z,
                        p_value=p,
                        ci_low=ci_low,
                        ci_high=ci_high,
                    ))

                # Joint F test: H0: all pre coefficients = 0
                if pretrends == 1:
                    t_val = pre_beta[0] / pre_se[0] if pre_se[0] > 0 else 0.0
                    f_stat = float(t_val ** 2)
                    p_value_f = float(2 * (1 - norm_dist.cdf(abs(t_val))) if pre_se[0] > 0 else 1.0)
                else:
                    pre_cov = cov_matrix[np.ix_(pre_indices, pre_indices)]
                    try:
                        pre_cov_inv = np.linalg.inv(pre_cov)
                        f_stat = float(pre_beta @ pre_cov_inv @ pre_beta / pretrends)
                        df_r = df_resid_ctrl if df_resid_ctrl is not None else len(control_mask) - len(pre_indices)
                        from scipy.stats import f as f_dist
                        p_value_f = float(1 - f_dist.cdf(f_stat, pretrends, max(df_r, 1)))
                    except np.linalg.LinAlgError:
                        f_stat = np.nan
                        p_value_f = np.nan
                pretrend_warnings.append(
                    f"Pretrend joint F-test: F={f_stat:.6f}, p={p_value_f:.6f}, df=({pretrends}, {df_resid_ctrl or 'na'})"
                )

        # Save estimates and weights if requested
        if saveestimates is not None:
            self.saveestimates_ = pd.Series(np.nan, index=self.data.index)
            self.saveestimates_.loc[df.index] = df["_effect"].values

        if saveweights:
            self.saveweights_ = pd.DataFrame(index=self.data.index)
            for tr in tau_results:
                if not tr.get("dropped", False) and "imputation_weights" in tr:
                    self.saveweights_[tr["name"]] = pd.Series(
                        np.nan, index=self.data.index
                    )
                    self.saveweights_.loc[df.index, tr["name"]] = tr[
                        "imputation_weights"
                    ].values

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
            df_model=float(len([c for c in coefficients if c.name.startswith("tau") and c.std_err > 0])),
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

        diagnostics = DiagnosticsInfo(warnings=pretrend_warnings)

        options = [f"cluster({cluster})"]
        if allhorizons:
            options.append("allhorizons")
        if autosample:
            options.append("autosample")
        if window is not None:
            options.append(f"window({window[0]} {window[1]})")
        if minn is not None:
            options.append(f"minn({minn})")
        if pretrends > 0:
            options.append(f"pretrends({pretrends})")
        if wtr is not None:
            options.append(f"wtr({wtr})")
        if hetby is not None:
            options.append(f"hetby({hetby})")
        if saveestimates is not None:
            options.append(f"saveestimates({saveestimates})")
        if saveweights:
            options.append("saveweights")
        if sum:
            options.append("sum")
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

    def _fit_twfe_covariates(
        self,
        df: pd.DataFrame,
        y_var: str,
        id_var: str,
        time_var: str,
        control_mask: pd.Series,
        controls: Optional[list[str]] = None,
        unitcontrols: Optional[list[str]] = None,
        timecontrols: Optional[list[str]] = None,
        pretrend_cols: Optional[list[str]] = None,
        cluster: Optional[str] = None,
    ) -> dict:
        """
        Fit TWFE + covariates on control sample via dense LSDV.

        Returns a dict with:
        - alpha_fe: pd.Series of unit FE (None if unitcontrols present)
        - gamma_fe: pd.Series of time FE (None if timecontrols present)
        - beta_controls: np.ndarray of global control coefficients (None if no controls)
        - uc_slopes: dict of unitcontrol slopes by variable (None if no unitcontrols)
        - tc_slopes: dict of timecontrol slopes by variable (None if no timecontrols)
        - beta: full coefficient vector (np.ndarray)
        - cov: variance-covariance matrix (np.ndarray)
        - col_names: list of column names corresponding to beta/cov
        - df_resid: residual degrees of freedom
        """
        ctrl_df = df.loc[control_mask].copy()
        n_ctrl = len(ctrl_df)

        # Collinearity check: controls constant in D==0 subsample
        if controls is not None:
            for c in controls:
                if ctrl_df[c].nunique() <= 1:
                    raise ValueError(
                        f"Control variable '{c}' is collinear in the D==0 subsample. "
                        "Please drop it or adjust the sample."
                    )

        # Build design matrix columns
        cols = []
        col_names = []

        # Unit FEs (if no unitcontrols)
        if unitcontrols is None:
            unit_dummies = pd.get_dummies(ctrl_df[id_var], prefix="_u")
            cols.append(unit_dummies.values)
            col_names.extend(unit_dummies.columns.tolist())
        else:
            # Unit-specific intercepts for unitcontrols
            for uid in ctrl_df[id_var].unique():
                col = (ctrl_df[id_var] == uid).astype(float).values[:, None]
                cols.append(col)
                col_names.append(f"_u_{uid}_int")
            # Unit-specific slopes for each unitcontrol
            for z in unitcontrols:
                for uid in ctrl_df[id_var].unique():
                    col = ((ctrl_df[id_var] == uid).astype(float) * ctrl_df[z]).values[:, None]
                    cols.append(col)
                    col_names.append(f"_u_{uid}_s_{z}")

        # Time FEs (if no timecontrols)
        if timecontrols is None:
            time_dummies = pd.get_dummies(ctrl_df[time_var], prefix="_t")
            cols.append(time_dummies.values)
            col_names.extend(time_dummies.columns.tolist())
        else:
            # Time-specific intercepts for timecontrols
            for tval in ctrl_df[time_var].unique():
                col = (ctrl_df[time_var] == tval).astype(float).values[:, None]
                cols.append(col)
                col_names.append(f"_t_{tval}_int")
            # Time-specific slopes for each timecontrol
            for w in timecontrols:
                for tval in ctrl_df[time_var].unique():
                    col = ((ctrl_df[time_var] == tval).astype(float) * ctrl_df[w]).values[:, None]
                    cols.append(col)
                    col_names.append(f"_t_{tval}_s_{w}")

        # Global controls
        if controls is not None:
            cols.append(ctrl_df[controls].values)
            col_names.extend(controls)

        # Pretreatment dummies
        if pretrend_cols is not None:
            cols.append(ctrl_df[pretrend_cols].values)
            col_names.extend(pretrend_cols)

        X = np.hstack(cols) if cols else np.ones((n_ctrl, 1))
        y = ctrl_df[y_var].values

        # Solve via least squares (handles collinearity via minimum-norm)
        beta = np.linalg.lstsq(X, y, rcond=None)[0]

        # Compute VCE for inference
        resid = y - X @ beta
        rank = np.linalg.matrix_rank(X)
        df_resid = max(n_ctrl - rank, 1)
        xtx_inv = np.linalg.pinv(X.T @ X)
        if cluster is not None and cluster in ctrl_df.columns:
            from stataflow.estimators._vce_utils import compute_cluster_meat
            meat, cluster_count = compute_cluster_meat(X, resid, ctrl_df[cluster].values)
            g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
            n_adj = (n_ctrl - 1) / (n_ctrl - rank) if n_ctrl > rank else 1.0
            cov = n_adj * g_adj * xtx_inv @ meat @ xtx_inv
        else:
            sigma2 = np.dot(resid, resid) / df_resid
            cov = sigma2 * xtx_inv

        # Extract coefficients
        idx = 0
        result = {"beta": beta, "cov": cov, "col_names": col_names, "df_resid": df_resid}

        if unitcontrols is None:
            n_u = unit_dummies.shape[1]
            alpha_fe = pd.Series(beta[idx:idx + n_u], index=unit_dummies.columns)
            # Map dummy column names back to unit IDs
            alpha_fe.index = alpha_fe.index.str.replace("_u_", "").astype(
                ctrl_df[id_var].dtype)
            result["alpha_fe"] = alpha_fe
            idx += n_u
        else:
            uc_slopes = {"_intercepts": {}}
            for z in unitcontrols:
                uc_slopes[z] = {}
            for uid in ctrl_df[id_var].unique():
                uc_slopes["_intercepts"][uid] = beta[idx]
                idx += 1
                for z in unitcontrols:
                    uc_slopes[z][uid] = beta[idx]
                    idx += 1
            result["uc_slopes"] = uc_slopes

        if timecontrols is None:
            n_t = time_dummies.shape[1]
            gamma_fe = pd.Series(beta[idx:idx + n_t], index=time_dummies.columns)
            gamma_fe.index = gamma_fe.index.str.replace("_t_", "").astype(
                ctrl_df[time_var].dtype)
            result["gamma_fe"] = gamma_fe
            idx += n_t
        else:
            tc_slopes = {"_intercepts": {}}
            for w in timecontrols:
                tc_slopes[w] = {}
            for tval in ctrl_df[time_var].unique():
                tc_slopes["_intercepts"][tval] = beta[idx]
                idx += 1
                for w in timecontrols:
                    tc_slopes[w][tval] = beta[idx]
                    idx += 1
            result["tc_slopes"] = tc_slopes

        if controls is not None:
            result["beta_controls"] = beta[idx:idx + len(controls)]
            idx += len(controls)

        return result

    def _compute_imputation_weights(
        self,
        df: pd.DataFrame,
        effective_mask: pd.Series,
        control_mask: pd.Series,
        id_var: str,
        time_var: str,
        wtr_values: Optional[pd.Series] = None,
        max_iter: int = 100000,
        tol: float = 1e-14,
    ) -> pd.Series:
        """
        Compute imputation weights for standard errors.
        Returns a Series indexed like df.
        """
        # Initialize weights, normalized to sum to 1 over effective_mask
        w = pd.Series(0.0, index=df.index)
        if wtr_values is not None:
            w_vals = wtr_values.loc[effective_mask]
            w_sum = w_vals.sum()
            if w_sum > 0:
                w.loc[effective_mask] = w_vals / w_sum
            else:
                w.loc[effective_mask] = 0.0
        else:
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
            norm_col = tr.get("norm_col")
            wtr_values = df[norm_col] if norm_col is not None else None
            w = self._compute_imputation_weights(
                df, effective_mask, control_mask, self.id_var, self.time_var,
                wtr_values=wtr_values,
            )
            tr["imputation_weights"] = w

            # Compute residuals
            resid = pd.Series(np.nan, index=df.index)
            # Controls: resid = y - Y0
            resid.loc[control_mask] = (
                df.loc[control_mask, self.y_var] - df.loc[control_mask, "_Y0"]
            )
            # Treated: resid = effect - avgtau, where avgtau is the cell-level
            # average by (first_treat, time), matching Stata's default avgeffectsby
            treated_df = df.loc[treated_mask]
            cell_means = treated_df.groupby([self.first_treat_var, self.time_var])["_effect"].transform("mean")
            df.loc[treated_mask, "_avgtau"] = cell_means.values
            resid.loc[treated_mask] = df.loc[treated_mask, "_effect"] - df.loc[treated_mask, "_avgtau"]

            # Cluster-level aggregated influence
            df["_influence"] = w * resid
            # Replace NaN with 0 (for observations not in control or treated with effect)
            df["_influence"] = df["_influence"].fillna(0.0)

            cluster_sums = df.groupby(cluster_var)["_influence"].sum()
            V = float((cluster_sums ** 2).sum())

            tr["std_err"] = np.sqrt(V) if V >= 0 else 0.0

        return tau_results
