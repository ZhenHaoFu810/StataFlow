"""Callaway-Sant'Anna CSDID estimator (method='reg')."""

import numpy as np
import pandas as pd
from statapy.results.result import (
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

    def __init__(self, data, y, id, time, first_treat):
        self.data = data.copy()
        self.y_name = y
        self.id_name = id
        self.time_name = time
        self.first_treat_name = first_treat

        self._group_time_att = {}
        self._group_time_se = {}
        self._event_est = {}
        self._event_se = {}
        self._nobs = 0
        self._n_clust = 0

    def fit(self, method="reg", vce=None, cluster=None):
        """Fit the CSDID estimator.

        Parameters
        ----------
        method : str, optional
            Only ``"reg"`` (regression adjustment) is supported.
        vce : str, optional
            Variance estimator. Only ``"cluster"`` is supported.
        cluster : str, optional
            Cluster variable name. Defaults to ``self.id_name``.
        """
        if method != "reg":
            raise ValueError("Only method='reg' is supported.")

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

        # Determine control group strategy: Stata default is never-treated if available
        has_never_treated = (df[ft] == 0).any()

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

                mu_g_t = df.loc[treated_mask & (df[time] == t), y].mean()
                mu_c_t = df.loc[control_mask & (df[time] == t), y].mean()
                mu_g_base = df.loc[treated_mask & (df[time] == base), y].mean()
                mu_c_base = df.loc[control_mask & (df[time] == base), y].mean()

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
        self._n_clust = n_units

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
        n_units_total = len(units)
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

            atte, rif_event = _aggte(ag_rif, ag_wt)
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
            atte, rif_pre = _aggte(ag_rif, ag_wt)
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
            atte, rif_post = _aggte(ag_rif, ag_wt)
            if_post = rif_post - atte
            event_est["Post_avg"] = atte
            event_se["Post_avg"] = np.sqrt(np.sum(if_post ** 2)) / n_units_total

        self._event_est = event_est
        self._event_se = event_se

        return self

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
                cluster_var=None,
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
                stata_command="csdid y, ivar(id) time(time) gvar(first_treat) method(reg)",
            ),
        )

    @staticmethod
    def _normal_cdf(x):
        """Standard normal CDF."""
        from scipy.stats import norm
        return norm.cdf(x)
