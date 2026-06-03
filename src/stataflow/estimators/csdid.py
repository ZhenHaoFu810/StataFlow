"""Callaway-Sant'Anna CSDID estimator (method='reg')."""

import numpy as np
import pandas as pd
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


class CSDID:
    """Callaway-Sant'Anna CSDID estimator.

    Parameters
    ----------
    data : pd.DataFrame
    y : str
    id : str
    time : str
    first_treat : str
    """

    def __init__(self, data, y, id, time, first_treat, xvars=None):
        self.data = data.copy()
        self.y_name = y
        self.id_name = id
        self.time_name = time
        self.first_treat_name = first_treat
        self.xvars = xvars

        self._group_time_att = {}
        self._group_time_se = {}
        self._event_est = {}
        self._event_se = {}
        self._nobs = 0
        self._n_clust = 0

    def fit(self, method="reg", vce=None, cluster=None, xvars=None, notyet=False):
        """Fit the CSDID estimator.

        Parameters
        ----------
        method : str, optional
            ``"reg"`` (regression adjustment) or ``"drimp"`` / ``"dripw"``
            (doubly robust).
        vce : str, optional
            Variance estimator. Only ``"cluster"`` is supported.
        cluster : str, optional
            Cluster variable name. Defaults to ``self.id_name``.
        xvars : list[str], optional
            Covariate names for doubly-robust estimation.
        notyet : bool, optional
            If True, use not-yet-treated units as controls even when
            never-treated units are available.
        """
        if xvars is not None:
            self.xvars = xvars

        if method not in ("reg", "drimp", "dripw"):
            raise ValueError(
                f"Only method='reg', 'drimp', or 'dripw' is supported. Got {method!r}"
            )

        self._method = method
        self._notyet = bool(notyet)
        if method == "reg":
            return self._fit_reg(vce=vce, cluster=cluster, notyet=notyet)
        return self._fit_dr(method=method, vce=vce, cluster=cluster, notyet=notyet)

    def _fit_reg(self, vce=None, cluster=None, notyet=False):
        """Regression-adjustment (method='reg') implementation."""
        df = self.data.copy()
        y = self.y_name
        uid = self.id_name
        time = self.time_name
        ft = self.first_treat_name

        # Drop missings in key variables
        df = df.dropna(subset=[y, uid, time, ft])

        cohorts = sorted([g for g in df[ft].unique() if g > 0])
        years = sorted(df[time].unique())
        min_year = min(years)

        units = df[uid].unique()
        n_units = len(units)

        # Wide format for influence function convenience
        df_wide = df.pivot(index=uid, columns=time, values=y)
        cohort_map = df.groupby(uid)[ft].first()

        # Compute ATT(g,t) and unit-level IFs
        att_gt = {}
        if_gt = {}  # dict of dicts: {(g,t): {unit_id: if_value}}

        # Determine control group strategy: Stata default is never-treated if
        # available, unless notyet=True forces not-yet-treated controls.
        has_never_treated = (df[ft] == 0).any() and not notyet

        for g in cohorts:
            for t in years:
                # Control group: never-treated by default; fall back to not-yet-treated
                if has_never_treated:
                    control_mask = df[ft] == 0
                else:
                    control_mask = df[ft] > max(g, t)
                treated_mask = df[ft] == g

                if control_mask.sum() == 0:
                    continue

                if t < g:
                    base = t - 1
                else:
                    base = g - 1

                if base < min_year:
                    continue

                # Use the same control group (defined at t) for both periods
                ctrl_ids = df.loc[control_mask, uid].unique()
                treat_ids = df.loc[treated_mask, uid].unique()
                N_g = len(treat_ids)
                N_c = len(ctrl_ids)

                treated_t = treated_mask & (df[time] == t)
                control_t = control_mask & (df[time] == t)
                treated_base = treated_mask & (df[time] == base)
                control_base = control_mask & (df[time] == base)
                if (
                    treated_t.sum() == 0
                    or control_t.sum() == 0
                    or treated_base.sum() == 0
                    or control_base.sum() == 0
                ):
                    continue

                mu_g_t = df.loc[treated_t, y].mean()
                mu_c_t = df.loc[control_t, y].mean()
                mu_g_base = df.loc[treated_base, y].mean()
                mu_c_base = df.loc[control_base, y].mean()
                if not np.all(np.isfinite([mu_g_t, mu_c_t, mu_g_base, mu_c_base])):
                    continue

                att = (mu_g_t - mu_c_t) - (mu_g_base - mu_c_base)
                # Store as tuple (att, N_g) for weighted aggregation
        # Note: att_gt is populated inside the loop above now

                # Unit-level influence function
                ifs = {}
                for u in units:
                    c = cohort_map.loc[u]
                    is_treat = 1 if c == g else 0
                    if has_never_treated:
                        is_ctrl = 1 if c == 0 else 0
                    else:
                        is_ctrl = 1 if c > max(g, t) else 0

                    y_t = df_wide.loc[u, t] if t in df_wide.columns else np.nan
                    y_base = df_wide.loc[u, base] if base in df_wide.columns else np.nan

                    if pd.isna(y_t) or pd.isna(y_base):
                        ifs[u] = 0.0
                        continue

                    term = 0.0
                    if is_treat:
                        term += (1.0 / N_g) * ((y_t - mu_g_t) - (y_base - mu_g_base))
                    if is_ctrl:
                        term -= (1.0 / N_c) * ((y_t - mu_c_t) - (y_base - mu_c_base))
                    ifs[u] = term

                if_gt[(g, t)] = ifs
                # Store N_g for weighting
                att_gt[(g, t)] = (att, N_g)

        # Effective observations: all unit-year rows that appear in any (g,t) estimation
        used_rows = set()
        for (g, t), (att, N_g) in att_gt.items():
            if has_never_treated:
                ctrl_ids = df.loc[df[ft] == 0, uid].unique()
            else:
                ctrl_ids = df.loc[df[ft] > max(g, t), uid].unique()
            treat_ids = df.loc[df[ft] == g, uid].unique()
            for u in treat_ids:
                used_rows.add((u, t))
                base = t - 1 if t < g else g - 1
                if base >= min_year:
                    used_rows.add((u, base))
            for u in ctrl_ids:
                used_rows.add((u, t))
                base = t - 1 if t < g else g - 1
                if base >= min_year:
                    used_rows.add((u, base))

        self._nobs = len(used_rows)
        cluster_col = cluster if cluster is not None else uid
        self._n_clust = int(df[cluster_col].nunique()) if cluster_col in df.columns else n_units
        self._cluster_var = cluster_col
        return self._finalize_fit(att_gt, if_gt, df, units, cohort_map, has_never_treated)

    def _finalize_fit(self, att_gt, if_gt, df, units, cohort_map, has_never_treated):
        """Compute SEs and event-study aggregation from ATT(g,t) and IFs."""
        uid = self.id_name
        n_units_total = len(units)

        # Group-time SEs
        se_gt = {}
        for k, ifs in if_gt.items():
            vals = np.array(list(ifs.values()))
            se_gt[k] = np.sqrt(np.sum(vals ** 2))

        self._group_time_att = att_gt
        self._group_time_se = se_gt

        # Event study aggregation using Stata's aggte delta-method
        event_map = {}
        for (g, t) in att_gt:
            e = t - g
            event_map.setdefault(e, []).append((g, t))

        # Build RIF matrices for ATT(g,t) and weights, matching Stata's scaling
        total_treated_all_pairs = sum(N_g for (att, N_g) in att_gt.values())
        scale = total_treated_all_pairs / n_units_total if total_treated_all_pairs > 0 else 1.0

        rifgt = {}
        rifwt = {}
        for (g, t) in att_gt:
            att, N_g = att_gt[(g, t)]
            # Scale IFs to match Stata's RIF scale: Stata's SE formula divides by n^2,
            # so its RIF deviations are n times larger than our scaled IFs.
            rifgt[(g, t)] = {u: n_units_total * if_gt[(g, t)][u] + att for u in units}
            rifwt[(g, t)] = {u: (1.0 / scale if cohort_map.loc[u] == g else 0.0) for u in units}

        event_est = {}
        event_rif = {}
        event_se = {}

        for e, pairs in event_map.items():
            k = len(pairs)
            ag_rif = np.zeros((n_units_total, k))
            ag_wt = np.zeros((n_units_total, k))
            for j, p in enumerate(pairs):
                for i, u in enumerate(units):
                    ag_rif[i, j] = rifgt[p][u]
                    ag_wt[i, j] = rifwt[p][u]

            atte, rif_event = self._aggte(ag_rif, ag_wt)
            if_event = rif_event - atte

            event_est[e] = atte
            event_rif[e] = {u: float(rif_event[idx]) for idx, u in enumerate(units)}
            # Stata's SE formula divides by n^2 for unit-level RIF data
            event_se[e] = np.sqrt(np.sum(if_event ** 2)) / n_units_total

        # Pre_avg and Post_avg using aggte on event-time RIFs with equal weights
        # Stata uses J(rows(aux), n, 1) as weight matrix for Pre_avg/Post_avg
        pre_es = sorted([e for e in event_est if e < 0])
        post_es = sorted([e for e in event_est if e >= 0])

        if pre_es:
            k = len(pre_es)
            ag_rif = np.zeros((n_units_total, k))
            ag_wt = np.ones((n_units_total, k))
            for j, e in enumerate(pre_es):
                for i, u in enumerate(units):
                    ag_rif[i, j] = event_rif[e][u]
            atte, rif_pre = self._aggte(ag_rif, ag_wt)
            if_pre = rif_pre - atte
            event_est["Pre_avg"] = atte
            event_se["Pre_avg"] = np.sqrt(np.sum(if_pre ** 2)) / n_units_total

        if post_es:
            k = len(post_es)
            ag_rif = np.zeros((n_units_total, k))
            ag_wt = np.ones((n_units_total, k))
            for j, e in enumerate(post_es):
                for i, u in enumerate(units):
                    ag_rif[i, j] = event_rif[e][u]
            atte, rif_post = self._aggte(ag_rif, ag_wt)
            if_post = rif_post - atte
            event_est["Post_avg"] = atte
            event_se["Post_avg"] = np.sqrt(np.sum(if_post ** 2)) / n_units_total

        self._event_est = event_est
        self._event_se = event_se
        self._event_rif = event_rif
        self._rifgt = rifgt
        self._rifwt = rifwt
        self._units = units

        return self

    def _fit_dr(self, method="drimp", vce=None, cluster=None, notyet=False):
        """Doubly-robust implementation (drimp / dripw)."""
        from sklearn.linear_model import LogisticRegression, LinearRegression

        df = self.data.copy()
        y = self.y_name
        uid = self.id_name
        time = self.time_name
        ft = self.first_treat_name
        xvars = self.xvars

        if xvars is None:
            raise ValueError(
                "method='drimp' requires xvars. Pass xvars to CSDID() or fit()."
            )

        # Drop missings in key variables
        df = df.dropna(subset=[y, uid, time, ft] + xvars)

        cohorts = sorted([g for g in df[ft].unique() if g > 0])
        years = sorted(df[time].unique())
        min_year = min(years)

        units = df[uid].unique()
        n_units = len(units)

        # Wide format for influence function convenience
        df_wide = df.pivot(index=uid, columns=time, values=y)
        cohort_map = df.groupby(uid)[ft].first()

        # Covariates in wide format (unit-level, first observation)
        X_wide = df.groupby(uid)[xvars].first()

        # Control group strategy: never-treated by default; fall back to not-yet-treated
        has_never_treated = (df[ft] == 0).any() and not notyet

        att_gt = {}
        if_gt = {}

        for g in cohorts:
            for t in years:
                if has_never_treated:
                    control_mask = df[ft] == 0
                else:
                    control_mask = df[ft] > max(g, t)
                treated_mask = df[ft] == g

                if control_mask.sum() == 0:
                    continue

                if t < g:
                    base = t - 1
                else:
                    base = g - 1

                if base < min_year:
                    continue

                # Fit PS: G=g vs control at unit level
                ps_units = df.loc[treated_mask | control_mask, uid].unique()
                ps_y = (cohort_map.loc[ps_units] == g).astype(int).values
                ps_X = X_wide.loc[ps_units]

                # Skip if insufficient variation
                if np.unique(ps_y).size <= 1 or len(ps_y) < 10:
                    continue

                try:
                    ps_model = LogisticRegression(
                        penalty=None, solver="lbfgs", max_iter=1000
                    )
                    ps_model.fit(ps_X, ps_y)
                    p_hat = ps_model.predict_proba(X_wide)[:, 1]
                except Exception:
                    # Fall back to uniform weights if PS fails
                    p_hat = np.full(len(X_wide), 0.5)

                # Trimming
                p_hat = np.clip(p_hat, 0.01, 0.99)

                # Fit OR: on controls (never-treated), delta_Y = Y_t - Y_{g-1}
                or_mask = control_mask
                or_df = df.loc[or_mask].copy()
                or_units = or_df[uid].unique()

                delta_y = []
                valid_units = []
                for u in or_units:
                    y_t = (
                        df_wide.loc[u, t]
                        if t in df_wide.columns else np.nan
                    )
                    y_base = (
                        df_wide.loc[u, base]
                        if base in df_wide.columns else np.nan
                    )
                    if pd.isna(y_t) or pd.isna(y_base):
                        continue
                    delta_y.append(y_t - y_base)
                    valid_units.append(u)

                if len(valid_units) == 0:
                    continue

                or_X = X_wide.loc[valid_units]
                or_y = np.array(delta_y)

                try:
                    or_model = LinearRegression()
                    or_model.fit(or_X, or_y)
                    m_hat = or_model.predict(X_wide)
                except Exception:
                    m_hat = np.zeros(len(X_wide))

                # Compute DR score (Sant'Anna & Zhao 2020)
                G_g = (cohort_map == g).astype(float).values

                delta_Y_all = np.array([
                    df_wide.loc[u, t] - df_wide.loc[u, base]
                    if t in df_wide.columns and base in df_wide.columns
                    else np.nan
                    for u in units
                ])

                psi = G_g * delta_Y_all - (
                    (1 - G_g) * delta_Y_all * p_hat + (G_g - p_hat) * m_hat
                ) / (1 - p_hat)

                psi = np.nan_to_num(psi, nan=0.0)

                # Restrict to treated and control units only
                eligible_units = df.loc[treated_mask | control_mask, uid].unique()
                eligible_set = set(eligible_units)
                eligible_arr = np.array([u in eligible_set for u in units])
                psi[~eligible_arr] = 0.0

                N_g = int(G_g.sum())
                att = float(np.sum(psi) / N_g) if N_g > 0 else 0.0

                # Influence function for inference
                # Scale IF to match reg method: (psi - G_g * att) / N_g
                if N_g > 0:
                    ifs_array = (psi - G_g * att) / N_g
                else:
                    ifs_array = np.zeros_like(psi)

                ifs = {u: float(ifs_array[i]) for i, u in enumerate(units)}

                if_gt[(g, t)] = ifs
                att_gt[(g, t)] = (att, N_g)

        # Effective observations
        used_rows = set()
        for (g, t), (att, N_g) in att_gt.items():
            if has_never_treated:
                ctrl_ids = df.loc[df[ft] == 0, uid].unique()
            else:
                ctrl_ids = df.loc[df[ft] > max(g, t), uid].unique()
            treat_ids = df.loc[df[ft] == g, uid].unique()
            for u in treat_ids:
                used_rows.add((u, t))
                base = t - 1 if t < g else g - 1
                if base >= min_year:
                    used_rows.add((u, base))
            for u in ctrl_ids:
                used_rows.add((u, t))
                base = t - 1 if t < g else g - 1
                if base >= min_year:
                    used_rows.add((u, base))

        self._nobs = len(used_rows)
        cluster_col = cluster if cluster is not None else uid
        self._n_clust = int(df[cluster_col].nunique()) if cluster_col in df.columns else n_units
        self._cluster_var = cluster_col
        return self._finalize_fit(
            att_gt, if_gt, df, units, cohort_map, has_never_treated
        )

    @property
    def params(self):
        """Event study parameters as a dict."""
        return dict(self._event_est)

    @property
    def bse(self):
        """Event study standard errors as a dict."""
        return dict(self._event_se)

    @property
    def nobs(self):
        return self._nobs

    @property
    def n_clust(self):
        return self._n_clust

    def estat_event(self):
        """Return a ResultSchema with event study estimates."""
        params = self.params
        bse = self.bse

        # Build ordered list of display keys: Pre_avg, Post_avg, Tm*, Tp*
        numeric_events = [k for k in params if not isinstance(k, str)]

        display_keys = []
        if "Pre_avg" in params:
            display_keys.append("Pre_avg")
        if "Post_avg" in params:
            display_keys.append("Post_avg")
        for e in sorted(numeric_events):
            if e < 0:
                display_keys.append(f"Tm{abs(e)}")
            else:
                display_keys.append(f"Tp{e}")

        # Map display key back to params key
        def _to_param_key(k):
            if k in ("Pre_avg", "Post_avg"):
                return k
            if k.startswith("Tm"):
                return -int(k[2:])
            if k.startswith("Tp"):
                return int(k[2:])
            raise ValueError(f"Unknown key: {k}")

        param_keys = [_to_param_key(k) for k in display_keys]

        coefs = np.array([params[k] for k in param_keys])
        ses = np.array([bse[k] for k in param_keys])
        tvalues = coefs / ses
        pvalues = 2 * (1 - self._normal_cdf(np.abs(tvalues)))

        conf_int = np.column_stack([coefs - 1.96 * ses, coefs + 1.96 * ses])

        coefficients = []
        for i, k in enumerate(display_keys):
            coefficients.append(CoefficientRow(
                name=k,
                beta=float(coefs[i]),
                std_err=float(ses[i]),
                t_stat=float(tvalues[i]),
                p_value=float(pvalues[i]),
                ci_low=float(conf_int[i, 0]),
                ci_high=float(conf_int[i, 1]),
            ))

        active_names = [c.name for c in coefficients if c.std_err > 0]
        cov = np.zeros((len(active_names), len(active_names)))
        for i, c in enumerate([c for c in coefficients if c.std_err > 0]):
            cov[i, i] = c.std_err ** 2

        n_active = len(active_names)
        df_model = float(n_active) if n_active > 0 else 0.0
        df_resid = float(self._n_clust - 1) if self._n_clust > 1 else float(self._nobs - n_active)

        return ResultSchema(
            model=ModelInfo(
                command="csdid",
                estimator_family="csdid",
                vcetype="cluster",
                cluster_var=getattr(self, "_cluster_var", None),
            ),
            sample=SampleInfo(
                nobs=self._nobs,
                n_input_rows=self._nobs,
            ),
            fit=FitInfo(
                df_model=df_model,
                df_resid=df_resid,
            ),
            coefficients=coefficients,
            variance=VarianceInfo(
                row_names=active_names,
                values=cov.tolist(),
            ),
            diagnostics=DiagnosticsInfo(
                cluster_count=self._n_clust,
            ),
            provenance=ProvenanceInfo(
                stata_command=f"csdid y, ivar(id) time(time) gvar(first_treat) method({getattr(self, '_method', 'reg')})",
            ),
        )

    @staticmethod
    def _aggte(ag_rif, ag_wt):
        """Replicate Mata aggte(rifgt, rifwt)."""
        mn_attg = ag_rif.mean(axis=0)
        mn_wgt = ag_wt.mean(axis=0)
        atte = np.sum(mn_attg * mn_wgt) / np.sum(mn_wgt)
        wgtw = mn_wgt / np.sum(mn_wgt)
        attw = mn_attg / np.sum(mn_wgt)
        r1 = wgtw * (ag_rif - mn_attg)
        r2 = attw * (ag_wt - mn_wgt)
        r3 = (ag_wt - mn_wgt) * (atte / np.sum(mn_wgt))
        rif_event = np.sum(r1 + r2 - r3, axis=1) + atte
        return atte, rif_event

    def estat(self, aggtype="event"):
        """Post-estimation aggregation.

        Parameters
        ----------
        aggtype : str
            - ``"event"``: average by event time (default)
            - ``"simple"``: simple average of all ATT(g,t)
            - ``"group"``: average by cohort
            - ``"calendar"``: average by calendar time
            - ``"pretrend"``: joint test of pre-trends
        """
        if aggtype == "event":
            return self.estat_event()
        elif aggtype == "simple":
            return self.estat_simple()
        elif aggtype == "group":
            return self.estat_group()
        elif aggtype == "calendar":
            return self.estat_calendar()
        elif aggtype == "pretrend":
            return self.estat_pretrend()
        else:
            raise ValueError(f"Unknown aggtype: {aggtype!r}")

    def estat_simple(self):
        """Simple average of all ATT(g,t)."""
        if not hasattr(self, "_rifgt") or not self._rifgt:
            raise ValueError("Model has not been fitted.")

        pairs = list(self._group_time_att.keys())
        n_units_total = len(self._units)
        k = len(pairs)

        ag_rif = np.zeros((n_units_total, k))
        ag_wt = np.zeros((n_units_total, k))
        for j, p in enumerate(pairs):
            for i, u in enumerate(self._units):
                ag_rif[i, j] = self._rifgt[p][u]
                ag_wt[i, j] = self._rifwt[p][u]

        atte, rif_simple = self._aggte(ag_rif, ag_wt)
        if_simple = rif_simple - atte
        se = np.sqrt(np.sum(if_simple ** 2)) / n_units_total

        return self._make_result_schema(
            names=["simple"],
            coefs=[atte],
            ses=[se],
            command="csdid_estat simple",
        )

    def estat_group(self):
        """ATT averaged by cohort."""
        if not hasattr(self, "_rifgt") or not self._rifgt:
            raise ValueError("Model has not been fitted.")

        n_units_total = len(self._units)
        cohorts = sorted(set(g for g, t in self._group_time_att.keys()))

        names = []
        coefs = []
        ses = []

        for g in cohorts:
            pairs = [(g_c, t) for g_c, t in self._group_time_att.keys() if g_c == g and t >= g]
            if not pairs:
                continue

            k = len(pairs)
            ag_rif = np.zeros((n_units_total, k))
            ag_wt = np.zeros((n_units_total, k))
            for j, p in enumerate(pairs):
                for i, u in enumerate(self._units):
                    ag_rif[i, j] = self._rifgt[p][u]
                    ag_wt[i, j] = self._rifwt[p][u]

            atte, rif_g = self._aggte(ag_rif, ag_wt)
            if_g = rif_g - atte
            se = np.sqrt(np.sum(if_g ** 2)) / n_units_total

            names.append(f"g{int(g)}")
            coefs.append(atte)
            ses.append(se)

        return self._make_result_schema(
            names=names,
            coefs=coefs,
            ses=ses,
            command="csdid_estat group",
        )

    def estat_calendar(self):
        """ATT averaged by calendar time."""
        if not hasattr(self, "_rifgt") or not self._rifgt:
            raise ValueError("Model has not been fitted.")

        n_units_total = len(self._units)
        times = sorted(set(t for g, t in self._group_time_att.keys()))

        names = []
        coefs = []
        ses = []

        for t in times:
            pairs = [(g, t_c) for g, t_c in self._group_time_att.keys() if t_c == t and g <= t and g > 0]
            if not pairs:
                continue

            k = len(pairs)
            ag_rif = np.zeros((n_units_total, k))
            ag_wt = np.zeros((n_units_total, k))
            for j, p in enumerate(pairs):
                for i, u in enumerate(self._units):
                    ag_rif[i, j] = self._rifgt[p][u]
                    ag_wt[i, j] = self._rifwt[p][u]

            atte, rif_t = self._aggte(ag_rif, ag_wt)
            if_t = rif_t - atte
            se = np.sqrt(np.sum(if_t ** 2)) / n_units_total

            names.append(f"t{int(t)}")
            coefs.append(atte)
            ses.append(se)

        return self._make_result_schema(
            names=names,
            coefs=coefs,
            ses=ses,
            command="csdid_estat calendar",
        )

    def estat_pretrend(self):
        """Joint Wald test of pre-trends."""
        pre_events = sorted([
            e for e in self._event_est
            if isinstance(e, (int, np.integer)) and e < 0
        ])
        if not pre_events:
            return self._make_pretrend_result(
                stat=float("nan"),
                p_value=float("nan"),
                df=0,
            )

        n = self._n_clust
        pre_est = np.array([self._event_est[e] for e in pre_events])

        # Build IF matrix: (n_pre_events, n_units)
        pre_if = np.zeros((len(pre_events), n))
        for i, e in enumerate(pre_events):
            for j, u in enumerate(self._units):
                pre_if[i, j] = self._event_rif[e][u] - self._event_est[e]

        # Covariance matrix
        cov = (pre_if @ pre_if.T) / (n ** 2)

        try:
            inv_cov = np.linalg.inv(cov)
            wald = float(pre_est @ inv_cov @ pre_est)
        except np.linalg.LinAlgError:
            inv_cov = np.linalg.pinv(cov)
            wald = float(pre_est @ inv_cov @ pre_est)

        df = len(pre_events)

        from scipy.stats import chi2
        p_value = float(chi2.sf(wald, df)) if df > 0 and not np.isnan(wald) else float("nan")

        return self._make_pretrend_result(
            stat=wald,
            p_value=p_value,
            df=df,
        )

    def _make_pretrend_result(self, stat, p_value, df):
        """Build a ResultSchema for the pretrend joint Wald test."""
        return ResultSchema(
            model=ModelInfo(
                command="csdid",
                estimator_family="csdid",
                vcetype="cluster",
                cluster_var=getattr(self, "_cluster_var", None),
            ),
            sample=SampleInfo(
                nobs=self._nobs,
                n_input_rows=self._nobs,
            ),
            fit=FitInfo(
                df_model=float(df),
                df_resid=float(self._n_clust - df) if self._n_clust > df else 0.0,
                f_stat=float(stat),
                f_pvalue=float(p_value),
            ),
            coefficients=[],
            variance=VarianceInfo(row_names=[], values=[]),
            diagnostics=DiagnosticsInfo(
                cluster_count=self._n_clust,
                warnings=[f"Pretrend joint Wald test with df={df}"],
            ),
            provenance=ProvenanceInfo(
                stata_command="csdid_estat pretrend",
            ),
        )

    def _make_result_schema(self, names, coefs, ses, command):
        """Build a ResultSchema from coefficient names, values, and SEs."""
        coefficients = []
        for name, beta, se in zip(names, coefs, ses):
            t_stat = beta / se if se > 0 else 0.0
            p_value = 2 * (1 - self._normal_cdf(abs(t_stat)))
            ci_low = beta - 1.96 * se
            ci_high = beta + 1.96 * se
            coefficients.append(CoefficientRow(
                name=name,
                beta=float(beta),
                std_err=float(se),
                t_stat=float(t_stat),
                p_value=float(p_value),
                ci_low=float(ci_low),
                ci_high=float(ci_high),
            ))

        active_names = [c.name for c in coefficients if c.std_err > 0]
        cov = np.zeros((len(active_names), len(active_names)))
        for i, c in enumerate([c for c in coefficients if c.std_err > 0]):
            cov[i, i] = c.std_err ** 2

        n_active = len(active_names)
        df_model = float(n_active) if n_active > 0 else 0.0
        df_resid = float(self._n_clust - 1) if self._n_clust > 1 else float(self._nobs - n_active)

        return ResultSchema(
            model=ModelInfo(
                command="csdid",
                estimator_family="csdid",
                vcetype="cluster",
                cluster_var=getattr(self, "_cluster_var", None),
            ),
            sample=SampleInfo(
                nobs=self._nobs,
                n_input_rows=self._nobs,
            ),
            fit=FitInfo(
                df_model=df_model,
                df_resid=df_resid,
            ),
            coefficients=coefficients,
            variance=VarianceInfo(
                row_names=active_names,
                values=cov.tolist(),
            ),
            diagnostics=DiagnosticsInfo(
                cluster_count=self._n_clust,
            ),
            provenance=ProvenanceInfo(
                stata_command=command,
            ),
        )

    @staticmethod
    def _normal_cdf(x):
        """Standard normal CDF."""
        from scipy.stats import norm
        return norm.cdf(x)
