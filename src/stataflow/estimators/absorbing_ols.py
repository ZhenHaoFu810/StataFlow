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
from stataflow.estimators._absorb_spec import AbsorbSpec
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
        Note: a bare string selects Stata ``areg`` semantics; a list (even of
        length one) selects ``reghdfe`` semantics. The two modes use different
        cluster small-sample rank rules (see ``_cluster_k_eff``).
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
        absorb: str | list[str] | list[AbsorbSpec] | AbsorbSpec,
        add_constant: bool = True,
        missing: str = "drop",
        drop_singletons: bool = True,
        technique: str = "auto",
        weights: Optional[np.ndarray] = None,
        weight_type: Optional[str] = None,
    ):
        self.data = data
        self.y = y
        self.x = list(x)

        # Normalise absorb to a list of AbsorbSpec
        if isinstance(absorb, AbsorbSpec):
            absorb_specs = [absorb]
            self._reghdfe_mode = False  # single AbsorbSpec → areg semantics
        elif isinstance(absorb, str):
            # Parse slope syntax if present
            if "#c." in absorb or "##c." in absorb:
                from stataflow.compat.stata.factor_variables import parse_absorb
                absorb_specs = parse_absorb(absorb)
                self._reghdfe_mode = True  # slope syntax → reghdfe semantics
            else:
                absorb_specs = [AbsorbSpec(var=absorb, slopes=[], has_intercept=True)]
                self._reghdfe_mode = False
        elif len(absorb) > 0 and isinstance(absorb[0], AbsorbSpec):
            absorb_specs = list(absorb)
            self._reghdfe_mode = True  # list of AbsorbSpec → reghdfe semantics
        else:
            absorb_specs = [
                AbsorbSpec(var=v, slopes=[], has_intercept=True) for v in absorb
            ]
            # Any list input (even length 1) triggers reghdfe semantics for
            # backward compatibility with direct AbsorbingOLS(..., absorb=[...])
            self._reghdfe_mode = True

        self.absorb_specs = absorb_specs
        self.absorb_vars = [spec.var for spec in absorb_specs]
        self.add_constant = add_constant
        self.missing = missing
        self.drop_singletons = drop_singletons
        self.technique = technique
        self._weights_input = weights
        self._weight_type = weight_type
        self._weights: Optional[np.ndarray] = None

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
        self._cluster_arrs: list[np.ndarray] = []
        self._cluster_vars: list[str] = []

        # FE factor info for MAP
        self._fe_info: list[dict] = []

        # Fitted state
        self._is_fitted: bool = False
        self._beta_full: Optional[np.ndarray] = None
        self._cov_full: Optional[np.ndarray] = None
        self._T: Optional[np.ndarray] = None
        self._beta_reported: Optional[np.ndarray] = None
        self._cov_reported: Optional[np.ndarray] = None
        self._result: Optional[ResultSchema] = None

    def _use_map(self, fe_info: list[dict]) -> bool:
        """Decide whether to use MAP iterative absorption."""
        if self.technique == "map":
            return True
        if self.technique == "lsdv":
            return False
        # Weighted HDFE requires weighted partial-out; MAP currently ignores
        # weights, so fall back to LSDV when weights are present (VCE-005).
        if self._weights_input is not None:
            return False
        # auto: use MAP if total FE levels would exceed LSDV comfort threshold
        total_fe_levels = sum(info["num_levels"] for info in fe_info)
        return total_fe_levels > 5000

    def _drop_singletons(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        """
        Iteratively drop singleton observations across all absorb variables.

        Also drops observations in absorb groups that lack sufficient variation
        to estimate slopes (needs at least 2 distinct observations per slope
        combination).

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
            for spec in self.absorb_specs:
                var = spec.var
                counts = df[var].value_counts()
                # Basic singletons: groups with only 1 observation
                singletons = counts[counts == 1].index.tolist()
                # Slope singletons: groups with slopes but < 2 obs
                if spec.slopes:
                    for group_val, group_size in counts.items():
                        if group_size < 2 and group_val not in singletons:
                            singletons.append(group_val)
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

    @staticmethod
    def _aitken_accelerate(
        x_n: np.ndarray, x_n1: np.ndarray, x_n2: np.ndarray
    ) -> np.ndarray:
        """Vector Aitken Δ² acceleration (Macleod 1986 method 3).

        Extrapolates element-wise from three consecutive iterates.
        """
        u = x_n - 2.0 * x_n1 + x_n2
        delta = x_n - x_n1
        mask = np.abs(u) > 1e-15
        x_star = x_n.copy()
        x_star[mask] -= (delta[mask] ** 2) / u[mask]
        return x_star

    def _project_onto_fe(
        self,
        v: np.ndarray,
        info: dict,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Project vector v onto the column space of one FE group and return residual.

        For intercept-only, this subtracts group means.
        For slope absorption, this performs within-group OLS regression
        on [1, slopes] (or [slopes] if no intercept) and subtracts fitted values.

        Returns
        -------
        residual : np.ndarray
            v minus the projection.
        coeffs : np.ndarray
            Per-group coefficients (intercept first, then slopes).
        """
        levels = info["levels_int"]
        G = info["num_levels"]
        counts = info["counts"]
        slope_arrays = info.get("slope_arrays", [])
        has_intercept = info.get("has_intercept", True)
        p = len(slope_arrays)

        if p == 0:
            # Intercept-only: simple group means
            means = np.bincount(levels, weights=v, minlength=G)
            means /= counts
            residual = v - means[levels]
            # Return coeffs as 2D (G x 1) for consistency with slope case
            return residual, means.reshape(-1, 1)

        # Build sufficient statistics for within-group regression
        # Variables: [1, s1, s2, ...] or [s1, s2, ...]
        # For each group g, solve (Z_g' Z_g) beta_g = Z_g' v_g
        n_vars = p + (1 if has_intercept else 0)

        # Compute all pairwise sums using bincount
        # zz[g, i, j] = sum(z_i * z_j | g)
        # zv[g, i] = sum(z_i * v | g)

        # Flatten symmetric matrix index
        def _idx(i, j):
            if i > j:
                i, j = j, i
            return i * n_vars + j - i * (i + 1) // 2

        num_pairs = n_vars * (n_vars + 1) // 2
        zz_sums = np.zeros((G, num_pairs))
        zv_sums = np.zeros((G, n_vars))

        var_idx = 0
        if has_intercept:
            # z_0 = 1
            # zz[0,0] = counts
            zz_sums[:, _idx(0, 0)] = counts.astype(np.float64)
            # zv[0] = sum(v | g)
            zv_sums[:, 0] = np.bincount(levels, weights=v, minlength=G)
            var_idx = 1

        for s_idx, s in enumerate(slope_arrays):
            zi = var_idx + s_idx
            # diagonal: sum(s^2 | g)
            zz_sums[:, _idx(zi, zi)] = np.bincount(
                levels, weights=s ** 2, minlength=G
            )
            # cross with v: sum(s * v | g)
            zv_sums[:, zi] = np.bincount(levels, weights=s * v, minlength=G)
            if has_intercept:
                # cross with intercept: sum(s * 1 | g) = sum(s | g)
                zz_sums[:, _idx(0, zi)] = np.bincount(
                    levels, weights=s, minlength=G
                )
            # cross with other slopes
            for s_idx2 in range(s_idx + 1, p):
                zj = var_idx + s_idx2
                zz_sums[:, _idx(zi, zj)] = np.bincount(
                    levels, weights=s * slope_arrays[s_idx2], minlength=G
                )

        # Solve for each group
        coeffs = np.zeros((G, n_vars))
        for g in range(G):
            if counts[g] == 0:
                continue
            # Build ZZ matrix
            ZZ = np.zeros((n_vars, n_vars))
            for i in range(n_vars):
                for j in range(i, n_vars):
                    ZZ[i, j] = zz_sums[g, _idx(i, j)]
                    if i != j:
                        ZZ[j, i] = ZZ[i, j]
            Zv = zv_sums[g, :]
            try:
                beta_g = np.linalg.solve(ZZ, Zv)
            except np.linalg.LinAlgError:
                # Singular: e.g., slope constant within group
                beta_g = np.linalg.lstsq(ZZ, Zv, rcond=None)[0]
            coeffs[g, :] = beta_g

        # Compute fitted values and residual
        fitted = np.zeros_like(v)
        if has_intercept:
            fitted += coeffs[levels, 0]
        for s_idx, s in enumerate(slope_arrays):
            ci = (1 if has_intercept else 0) + s_idx
            fitted += coeffs[levels, ci] * s

        residual = v - fitted
        return residual, coeffs

    def _map_partial_out(
        self,
        y: np.ndarray,
        X: np.ndarray,
        fe_info: list[dict],
        max_iter: int = 10000,
        tol: float = 1e-12,
        accel_freq: int = 1_000_000,
    ) -> tuple[np.ndarray, np.ndarray, list[list[np.ndarray]]]:
        """Partial out fixed effects using MAP (Kaczmarz sequential projection).

        Memory cost is O(N * k + sum(G_g)) instead of O(N * sum(G_g)).

        Returns
        -------
        y_star, X_star : partialled-out data
        fe_cum : list of length (k+1), each element is a list of length num_fe
                 containing the cumulative group coefficients removed for that column
                 and FE group. Used for LSDV-compatible constant recovery.
        """
        import warnings

        n = len(y)
        k = X.shape[1]
        num_fe = len(fe_info)

        if num_fe == 0:
            return y.copy(), X.copy(), []

        # Aitken acceleration is not safe for multi-way FE (converges to wrong
        # fixed point for 2+ FE groups).  Guard against accidental enablement.
        if num_fe > 1 and accel_freq <= max_iter:
            raise NotImplementedError(
                "Aitken acceleration is not safe for multi-way FE; "
                "see docs/research/wave12-map-lsmr.md.  "
                "Use accel_freq > max_iter to disable it explicitly."
            )

        # Sort FE groups by size (largest first) for better convergence
        fe_order = sorted(
            range(num_fe), key=lambda i: fe_info[i]["num_levels"], reverse=True
        )

        # Stack y and X columns for vectorised processing
        variables = np.column_stack([y, X]) if k > 0 else y.reshape(-1, 1)
        m = variables.shape[1]

        # Determine max coeffs per FE group for storage
        max_coeffs = [
            info.get("has_intercept", True) + len(info.get("slope_arrays", []))
            for info in fe_info
        ]

        # fe_cum[j][g] = cumulative coefficients for column j, FE group g
        # Each is a (G_g x n_coeffs) array
        fe_cum: list[list[np.ndarray]] = [
            [np.zeros((info["num_levels"], max_coeffs[g]), dtype=np.float64)
             for g, info in enumerate(fe_info)]
            for _ in range(m)
        ]

        for j in range(m):
            v = variables[:, j].copy()

            # 1-way FE: exact in a single pass
            if num_fe == 1:
                residual, coeffs = self._project_onto_fe(v, fe_info[0])
                v = residual
                variables[:, j] = v
                fe_cum[j][0] += coeffs
                continue

            # Multi-way FE: Kaczmarz iteration
            v_prev2: Optional[np.ndarray] = None
            v_prev1: Optional[np.ndarray] = None

            for iteration in range(max_iter):
                v_old = v.copy()

                # Sequential projection onto each FE group's orthogonal complement
                for g in fe_order:
                    residual, coeffs = self._project_onto_fe(v, fe_info[g])
                    v = residual
                    fe_cum[j][g] += coeffs

                # Convergence check
                max_diff = np.max(np.abs(v - v_old))
                if max_diff < tol:
                    break

                # Aitken acceleration (Macleod 1986 method 3)
                if (
                    iteration >= 2
                    and v_prev1 is not None
                    and v_prev2 is not None
                    and (iteration + 1) % accel_freq == 0
                ):
                    v = self._aitken_accelerate(v, v_prev1, v_prev2)
                    # Reset history after acceleration
                    v_prev2 = None
                    v_prev1 = None
                else:
                    # Shift history
                    v_prev2 = v_prev1
                    v_prev1 = v_old
            else:
                # max_iter reached without convergence – warn but continue
                warnings.warn(
                    f"MAP partial-out did not converge within {max_iter} iterations "
                    f"(max_diff={max_diff:.2e} > tol={tol:.2e}). "
                    "Results may be numerically unstable.",
                    RuntimeWarning,
                    stacklevel=2,
                )

            variables[:, j] = v

        y_star = variables[:, 0]
        X_star = variables[:, 1:] if k > 0 else np.zeros((n, 0))
        return y_star, X_star, fe_cum

    def _compute_dkraay_vce(
        self,
        X: np.ndarray,
        residuals: np.ndarray,
        timevar: np.ndarray,
        bw: Optional[int] = None,
        df_a: float = 0.0,
    ) -> tuple[np.ndarray, float]:
        """Compute Driscoll-Kraay HAC VCE.

        Parameters
        ----------
        X : np.ndarray
            Design matrix after partial-out (N x K).
        residuals : np.ndarray
            Residuals (N,).
        timevar : np.ndarray
            Time variable array (N,).
        bw : int, optional
            Bandwidth (None = default).
        df_a : float
            Absorbed degrees of freedom.

        Returns
        -------
        cov : np.ndarray
            K x K covariance matrix.
        df_r : float
            Reference degrees of freedom (T - 1).
        """
        N, K = X.shape
        unique_times = np.unique(timevar)
        T = len(unique_times)

        if bw is None:
            bw = int(np.floor(4.0 * (T / 100.0) ** (2.0 / 9.0))) + 1
        lags = bw - 1
        lags = max(0, min(lags, T - 1))

        # Compute h_t for each time period: h_t = X_t' e_t
        h_list = []
        for t in unique_times:
            mask = timevar == t
            h_t = X[mask].T @ residuals[mask]
            h_list.append(h_t)
        h_matrix = np.array(h_list)  # T x K

        # S_0
        M = h_matrix.T @ h_matrix

        # S_j with Bartlett kernel
        for j in range(1, lags + 1):
            weight = 1.0 - j / (lags + 1)
            Omega_j = h_matrix[j:].T @ h_matrix[:-j]
            M += weight * (Omega_j + Omega_j.T)

        # Sandwich: V = D M D
        XtX = X.T @ X
        XtX_inv = np.linalg.inv(XtX)
        V = XtX_inv @ M @ XtX_inv

        # DOF adjustment: ivreg2 style
        k_full = K + df_a
        if N > k_full and T > 1:
            dof_adj = (N - 1) / (N - k_full) * T / (T - 1)
            V *= dof_adj

        # PSD fix
        from stataflow.estimators._vce_utils import fix_psd

        V = fix_psd(V)

        df_r = float(T - 1)
        return V, df_r

    # _compute_cluster_meat, _fix_psd, _fix_psd_reghdfe, _compute_multiway_cluster_vce
    # are imported from _vce_utils (ADR-0004).

    def _cluster_k_eff(self, k_x: int) -> int:
        """Effective rank for cluster small-sample adjustment.

        Command-owned formulas (must not be shared blindly):

        * **reghdfe**: ``k_eff = k_x + df_a + nested_adj``, where ``nested_adj``
          is 1 if any absorbed FE is nested in a cluster variable. Nested FE
          levels are already excluded from ``df_a`` in reghdfe mode.
        * **areg**: ``k_eff = k_x + 1_{const} + df_a``. Stata ``areg`` keeps
          absorbed rank in ``e(df_a)`` even when FE is nested in cluster and
          counts the reported intercept in the finite-sample factor.
        """
        if not self._reghdfe_mode:
            const_adj = 1 if self.add_constant else 0
            return k_x + const_adj + int(round(self._df_a))

        nested_adj = 0
        fe_info = getattr(self, '_dummy_info', []) or getattr(self, '_fe_info', [])
        for info in fe_info:
            if self._fe_is_nested_in_cluster(info):
                nested_adj = 1
                break
        return k_x + int(round(self._df_a)) + nested_adj

    def _fe_is_nested_in_cluster(self, info: dict) -> bool:
        """Return whether each FE level belongs to one cluster level."""
        if not self._cluster_vars:
            return False
        fe_var = info["var"]
        if fe_var in self._cluster_vars:
            return True
        for cluster_var in self._cluster_vars:
            nesting = self._df.groupby(fe_var, sort=False)[cluster_var].nunique(
                dropna=False
            )
            if bool((nesting <= 1).all()):
                return True
        return False

    def _reghdfe_coefficient_scales(self, y: np.ndarray) -> np.ndarray:
        """Return reghdfe's coefficient rescaling factors."""
        x_names = [name for name in self._coef_names if name != "_cons"]
        y_sd = max(float(np.std(y, ddof=1)), 1e-3)
        x_sd = np.maximum(
            np.std(self._df[x_names].to_numpy(), axis=0, ddof=1),
            1e-3,
        )
        scales = x_sd / y_sd
        if "_cons" in self._coef_names:
            scales = np.concatenate([scales, [1.0 / y_sd]])
        return scales

    def _compute_multiway_cluster_vce(
        self,
        X_full: np.ndarray,
        residuals: np.ndarray,
        XtX_inv: np.ndarray,
        k_full: int,
        n: int,
    ) -> tuple[np.ndarray, int]:
        """Compute 2-way cluster-robust VCE via inclusion-exclusion.

        Thin wrapper that computes k_eff with the Stata-aligned nested
        adjustment.
        """
        from stataflow.estimators._vce_utils import compute_multiway_cluster_vce

        k_x = X_full.shape[1] - (1 if self.add_constant else 0) - sum(
            info['num_levels'] - 1 for info in self._dummy_info
        )
        k_eff = self._cluster_k_eff(k_x)
        return compute_multiway_cluster_vce(
            X_full, residuals, XtX_inv, self._cluster_arrs, k_eff, n,
        )

    def _prepare_data(
        self, cluster_vars: Optional[list[str]] = None, build_dummies: bool = True
    ) -> tuple[np.ndarray, np.ndarray, list[bool], int, Optional[list[dict]]]:
        """
        Prepare design matrix and dependent variable.

        Uses LSDV ordering: [constant, dummies_1, dummies_2, ..., x variables]
        so that x variables are dropped if collinear with absorbed dummies.

        When build_dummies=False, skips dummy construction and returns FE factor
        info for MAP iterative absorption instead.
        """
        all_vars = [self.y] + self.absorb_vars + self.x
        # Include slope variables so they are not dropped for missingness
        slope_vars = []
        for spec in self.absorb_specs:
            for s in spec.slopes:
                if s not in all_vars:
                    all_vars.append(s)
                    slope_vars.append(s)
        cluster_var_list = cluster_vars or []
        for cv in cluster_var_list:
            if cv not in all_vars:
                all_vars.append(cv)

        df = self.data[all_vars].copy()
        self._n_input_rows = len(df)

        # Handle weights: add weight column to missing check if provided
        weight_arr = None
        if self._weights_input is not None:
            weight_arr = np.asarray(self._weights_input, dtype=np.float64)
            if len(weight_arr) != self._n_input_rows:
                raise ValueError(
                    f"weights length ({len(weight_arr)}) must match data length ({self._n_input_rows})"
                )
            df["_stataflow_weights"] = weight_arr

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
            self._num_singletons = num_singletons
        else:
            self._num_singletons = 0

        # Extract weights after missing/singleton drop
        if weight_arr is not None:
            weight_arr = df["_stataflow_weights"].values.astype(np.float64)
            if np.any(weight_arr <= 0):
                raise ValueError("aweight requires all weights > 0")
            # Normalize weights so that sum(w) = N (Stata aweight convention)
            n_after_drop = len(df)
            weight_arr = weight_arr * n_after_drop / np.sum(weight_arr)
            self._weights = weight_arr

        # Save filtered dataframe for postestimation
        self._df = df.copy()

        # Build sample mask using unique row ids (immune to duplicate index labels)
        kept_ids = set(df["_stataflow_row_id"].values)
        sample_mask = [i in kept_ids for i in range(self._n_input_rows)]

        # Drop helper columns from internal dataframe
        df = df.drop(columns=["_stataflow_row_id"])
        if "_stataflow_weights" in df.columns:
            df = df.drop(columns=["_stataflow_weights"])
        self._df = df.copy()

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

        # Build x variables
        X_cols = []
        x_names = []
        for var in self.x:
            X_cols.append(df[var].values.astype(np.float64))
            x_names.append(var)
        X = np.column_stack(X_cols) if X_cols else np.zeros((n, 0))

        # Build FE factor info (needed for both LSDV collinearity detection and MAP)
        self._absorb_var_levels = []
        fe_info = []
        dummy_info = []

        for fe_idx, spec in enumerate(self.absorb_specs):
            var = spec.var
            absorb_vals = df[var].values
            unique_levels = np.unique(absorb_vals)
            self._absorb_var_levels.append(unique_levels.tolist())
            G = len(unique_levels)

            # Build integer-coded levels (0-based) for fast MAP group-by
            level_map = {lvl: i for i, lvl in enumerate(unique_levels)}
            levels_int = np.array([level_map[v] for v in absorb_vals], dtype=np.int64)
            counts = np.bincount(levels_int, minlength=G)

            # Slope variable arrays (only needed for MAP / partial-out)
            slope_arrays = []
            for svar in spec.slopes:
                slope_arrays.append(df[svar].values.astype(np.float64))

            fe_info.append({
                'var': var,
                'levels': unique_levels.tolist(),
                'num_levels': G,
                'levels_int': levels_int,
                'counts': counts,
                'slopes': spec.slopes,
                'slope_arrays': slope_arrays,
                'has_intercept': spec.has_intercept,
            })

            if not build_dummies:
                continue

            if not self.add_constant and fe_idx == 0:
                # First FE gets all levels when no constant (no reference level)
                D = np.zeros((n, max(G, 0)))
                dummy_names = [f"__absorb_{var}_{lvl}" for lvl in unique_levels]
                column_types = [("intercept",) for _ in unique_levels]
                for i, level in enumerate(unique_levels):
                    D[:, i] = (absorb_vals == level).astype(np.float64)
            else:
                D = np.zeros((n, max(G - 1, 0)))
                dummy_names = [f"__absorb_{var}_{lvl}" for lvl in unique_levels[1:]]
                column_types = [("intercept",) for _ in unique_levels[1:]]
                for i, level in enumerate(unique_levels[1:], start=1):
                    D[:, i - 1] = (absorb_vals == level).astype(np.float64)

            # Add slope interaction dummies for LSDV
            for svar in spec.slopes:
                svals = df[svar].values.astype(np.float64)
                if not self.add_constant and fe_idx == 0:
                    for i, level in enumerate(unique_levels):
                        inter_name = f"__absorb_{var}_{level}#c.{svar}"
                        D = np.column_stack([D, D[:, i] * svals])
                        dummy_names.append(inter_name)
                        column_types.append(("slope", svar))
                else:
                    # Reference level slope interaction (needed for full slope absorption)
                    ref_inter = (absorb_vals == unique_levels[0]).astype(np.float64) * svals
                    inter_name = f"__absorb_{var}_{unique_levels[0]}#c.{svar}"
                    D = np.column_stack([D, ref_inter])
                    dummy_names.append(inter_name)
                    column_types.append(("slope", svar))

                    for i, level in enumerate(unique_levels[1:], start=1):
                        inter_name = f"__absorb_{var}_{level}#c.{svar}"
                        D = np.column_stack([D, D[:, i - 1] * svals])
                        dummy_names.append(inter_name)
                        column_types.append(("slope", svar))

            if D.shape[1] > 0:
                dummy_info.append({
                    'var': var,
                    'levels': unique_levels.tolist(),
                    'num_levels': G,
                    'counts': counts,
                    'D': D,
                    'dummy_names': dummy_names,
                    'column_types': column_types,
                    'slopes': spec.slopes,
                    'has_intercept': spec.has_intercept,
                })

        if not build_dummies:
            # For MAP: detect collinearity among x variables only
            X, dropped, kept_indices = self._detect_collinearity(X, x_names)
            self._collinear_dropped = dropped
            self._coef_names = [x_names[i] for i in kept_indices] + (["_cons"] if self.add_constant else [])
            self._df = df  # keep full df for postestimation
            self._design_matrix = X
            self._dep_var = y
            self._sample_mask = sample_mask
            self._fe_info = fe_info
            self._compute_df_a(fe_info)
            return X, y, sample_mask, self._n_input_rows, fe_info

        # Build LSDV design matrix
        matrix_pieces = []
        names = []

        if self.add_constant:
            matrix_pieces.append(np.ones((n, 1)))
            names.append("_cons")

        x_start = 1 if self.add_constant else 0
        for info in dummy_info:
            start = sum(p.shape[1] for p in matrix_pieces)
            matrix_pieces.append(info['D'])
            names.extend(info['dummy_names'])
            info['start'] = start
            info['end'] = start + info['D'].shape[1]

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
        self._orig_to_reduced = orig_to_reduced

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
        self._fe_dummy_indices = []
        self._fe_dummy_indices_reduced = []
        fe_levels_for_df_a = []

        for info in dummy_info:
            kept_orig = [i for i in range(info['start'], info['end']) if i in kept_indices]
            kept_reduced = [orig_to_reduced[i] for i in kept_orig]
            self._fe_dummy_indices.append(kept_orig)
            self._fe_dummy_indices_reduced.append(kept_reduced)
            fe_levels_for_df_a.append(info['num_levels'])

        self._compute_df_a(dummy_info)

        # Store dummy_info for T matrix construction
        self._dummy_info = dummy_info

        self._design_matrix = X_full
        self._dep_var = y
        self._sample_mask = sample_mask

        return X_full, y, sample_mask, self._n_input_rows, None

    def _compute_df_a(self, fe_info_or_dummy_info: list[dict]) -> None:
        """Compute absorbed degrees of freedom."""
        effective_levels = []
        for i, _var in enumerate(self.absorb_vars):
            if i < len(fe_info_or_dummy_info):
                info = fe_info_or_dummy_info[i]
                n_levels = info['num_levels']
                n_slopes = len(info.get('slopes', []))
                has_intercept = info.get('has_intercept', True)
                # reghdfe zeros nested FE intercept contribution; areg does not
                # (Stata areg keeps e(df_a)=G-1 even when absorb is nested in cluster).
                if self._reghdfe_mode:
                    intercept_df = (
                        1
                        if has_intercept and not self._fe_is_nested_in_cluster(info)
                        else 0
                    )
                else:
                    intercept_df = 1 if has_intercept else 0
                params_per_level = intercept_df + n_slopes
                effective_levels.append(n_levels * params_per_level)

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
        self._df_a = max(0.0, self._df_a)

    def _fit_map(self, vce_core, cluster_vars, bw, timevar, alpha, savefe):
        """MAP partial-out path: demean via Kaczmarz, then OLS on residuals."""
        X_raw, y, sample_mask, n_input_rows, _ = self._prepare_data(
            cluster_vars=cluster_vars, build_dummies=False
        )
        n = len(y)
        k_x = X_raw.shape[1]
        y_partial, X_partial, fe_cum = self._map_partial_out(y, X_raw, self._fe_info)
        XtX = X_partial.T @ X_partial
        Xty = X_partial.T @ y_partial
        beta_x = np.linalg.solve(XtX, Xty)
        residuals = y_partial - X_partial @ beta_x
        rss = float(np.sum(residuals ** 2))
        y_mean = np.mean(y)
        tss = float(np.sum((y - y_mean) ** 2))
        r2 = 1.0 - rss / tss if tss > 0 else 0.0
        df_model = float(k_x)
        df_a = self._df_a
        k_full = k_x + df_a if self._reghdfe_mode else k_x + 1 + df_a

        cluster_count = None
        if vce_core == "cluster":
            if len(self._cluster_arrs) == 1:
                cluster_count = len(np.unique(self._cluster_arrs[0]))
            else:
                cluster_count = min(len(np.unique(ca)) for ca in self._cluster_arrs)
            df_resid = float(cluster_count - 1)
        elif vce_core == "robust":
            df_resid = float(n - k_full)
        elif vce_core == "dkraay":
            df_resid = None
        else:
            df_resid = float(n - k_full)

        # RMSE denominator: align with Stata's used_df_r.
        if self._reghdfe_mode:
            # reghdfe subtracts levels of FEs nested in cluster variables
            # (Stata's e(df_a_nested) is excluded from df_a but still counts
            # against residual df for rmse/r2_a).
            fe_info = getattr(self, "_fe_info", [])
            nested_levels = sum(
                info["num_levels"] for info in fe_info
                if self._fe_is_nested_in_cluster(info)
            )
            rmse_df = float(n - df_model - df_a - nested_levels)
        else:
            # areg: constant is estimated separately; nested FEs are redundant.
            cons_penalty = 1.0 if self.add_constant else 0.0
            rmse_df = float(n - df_model - df_a - cons_penalty)
        rmse = np.sqrt(rss / rmse_df) if rmse_df > 0 else 0.0

        if self._reghdfe_mode:
            r2_adj = 1.0 - (rss / rmse_df) / (tss / (n - 1)) if rmse_df > 0 and tss > 0 else None
        else:
            r2_adj = 1.0 - (1.0 - r2) * (n - 1) / rmse_df if rmse_df > 0 else 0.0

        if vce_core == "ols":
            sigma2 = rss / df_resid if df_resid > 0 else 0.0
            cov_slopes = sigma2 * np.linalg.inv(XtX)
        elif vce_core == "robust":
            XtX_inv = np.linalg.inv(XtX)
            meat = X_partial.T @ (X_partial * (residuals ** 2)[:, np.newaxis])
            cov_slopes = XtX_inv @ meat @ XtX_inv
            if n > k_full:
                cov_slopes *= n / (n - k_full)
        elif vce_core == "dkraay":
            timevar_arr = self._df[timevar].values
            cov_slopes, df_resid = self._compute_dkraay_vce(
                X_partial, residuals, timevar_arr, bw=bw, df_a=df_a
            )
        else:
            XtX_inv = np.linalg.inv(XtX)
            k_eff = self._cluster_k_eff(k_x)
            if len(self._cluster_arrs) == 1:
                from stataflow.estimators._vce_utils import compute_cluster_meat
                meat, cluster_count = compute_cluster_meat(
                    X_partial, residuals, self._cluster_arrs[0]
                )
                n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
                g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
                cov_slopes = n_adj * g_adj * XtX_inv @ meat @ XtX_inv
            else:
                from stataflow.estimators._vce_utils import compute_multiway_cluster_vce
                cov_slopes, cluster_count = compute_multiway_cluster_vce(
                    X_partial, residuals, XtX_inv, self._cluster_arrs, k_eff, n,
                )

        report_dim = k_x + (1 if self.add_constant else 0)

        if self.add_constant:
            # Stata's areg/reghdfe report the regression-through-means intercept:
            # _cons = mean(y) - mean(x)' beta_x.
            retained_x_names = [
                name for name in self._coef_names if name != "_cons"
            ]
            xbar = np.array([
                self._df[name].mean() for name in retained_x_names
            ])
            _cons = float(np.mean(y) - xbar @ beta_x)
            beta_reported = np.concatenate([beta_x, [_cons]])

            # Influence matrix for [beta_x, _cons] in the partialling-out framework.
            # The i-th row gives the influence of observation i on each estimator.
            XtX_inv = np.linalg.inv(XtX)
            h = 1.0 / n - X_partial @ (XtX_inv @ xbar)
            X_infl = np.column_stack([X_partial @ XtX_inv, h.reshape(-1, 1)])

            if vce_core == "ols":
                sigma2_cons = rss / df_resid if df_resid > 0 else 0.0
                cov_reported = sigma2_cons * (X_infl.T @ X_infl)
            elif vce_core == "robust":
                meat = X_infl.T @ (X_infl * (residuals ** 2)[:, np.newaxis])
                if n > k_full:
                    meat *= n / (n - k_full)
                cov_reported = meat
            elif vce_core == "dkraay":
                # DK VCE already computed for slopes; recover _cons row via delta method.
                cov_reported = np.zeros((report_dim, report_dim))
                cov_reported[:k_x, :k_x] = cov_slopes
                cons_var = float(xbar @ cov_slopes @ xbar)
                cov_reported[k_x, k_x] = max(cons_var, 0.0)
            else:
                k_eff = self._cluster_k_eff(k_x)
                if len(self._cluster_arrs) == 1:
                    clusters = self._cluster_arrs[0]
                    unique_clusters = np.unique(clusters)
                    meat = np.zeros((report_dim, report_dim))
                    for g in unique_clusters:
                        mask_g = clusters == g
                        score_g = X_infl[mask_g].T @ residuals[mask_g]
                        meat += np.outer(score_g, score_g)
                    n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
                    g_adj = (
                        len(unique_clusters) / (len(unique_clusters) - 1)
                        if len(unique_clusters) > 1 else 1.0
                    )
                    cov_reported = n_adj * g_adj * meat
                else:
                    from stataflow.estimators._vce_utils import compute_multiway_cluster_vce
                    cov_reported, _ = compute_multiway_cluster_vce(
                        X_infl, residuals, np.eye(report_dim),
                        self._cluster_arrs, k_eff, n,
                    )

            if vce_core == "cluster" and len(self._cluster_arrs) > 1:
                from stataflow.estimators._vce_utils import fix_psd_reghdfe
                cov_reported = fix_psd_reghdfe(
                    cov_reported,
                    constant_index=k_x,
                    coefficient_scales=self._reghdfe_coefficient_scales(y),
                )
        else:
            beta_reported = beta_x
            cov_reported = cov_slopes

        if self.add_constant:
            X_ols = np.column_stack([np.ones(n), X_partial])
            beta_full = np.concatenate([[_cons], beta_x])
        else:
            X_ols = X_partial
            beta_full = beta_x
        self._design_matrix = X_ols
        self._dep_var = y_partial
        self._beta_full = beta_full
        self._map_residuals = residuals
        self._cov_full = cov_slopes
        self._T = np.eye(report_dim)
        self._x_indices_in_full = list(range(int(self.add_constant), int(self.add_constant) + k_x))
        self._dummy_info = []
        self._fe_dummy_indices_reduced = []
        self._constant_idx_reduced = 0 if self.add_constant else None
        self._orig_to_reduced = {i: i for i in range(report_dim)}

        diag_cov = np.maximum(np.diag(cov_reported), 0)
        se = np.sqrt(diag_cov)
        t_stats = beta_reported / se
        p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=df_resid))
        t_crit = t_dist.ppf(1 - alpha / 2, df=df_resid)
        ci_low = beta_reported - t_crit * se
        ci_high = beta_reported + t_crit * se

        rss_r = None
        f_stat = None
        f_pvalue = None
        if self.add_constant and df_model > 0 and rmse_df > 0 and rss > 0:
            if vce_core == "ols":
                rss_r = float(np.sum(y_partial ** 2))
                f_stat = ((rss_r - rss) / df_model) / (rss / rmse_df)
                f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=rmse_df)
            else:
                slope_idx = list(range(k_x))
                beta_s = beta_reported[slope_idx]
                cov_s = cov_reported[np.ix_(slope_idx, slope_idx)]
                try:
                    cov_inv = np.linalg.inv(cov_s)
                    wald_stat = float(beta_s @ cov_inv @ beta_s)
                    f_stat = wald_stat / df_model
                    f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
                except np.linalg.LinAlgError:
                    pass

        return dict(
            beta_reported=beta_reported, cov_reported=cov_reported, se=se,
            t_stats=t_stats, p_values=p_values, ci_low=ci_low, ci_high=ci_high,
            df_model=df_model, df_resid=df_resid, df_a=df_a, k_full=k_full,
            rss=rss, tss=tss, r2=r2, r2_adj=r2_adj, rmse=rmse,
            rss_r=rss_r, f_stat=f_stat, f_pvalue=f_pvalue,
            n=n, n_input_rows=n_input_rows, sample_mask=sample_mask,
            cluster_count=cluster_count, vce_core=vce_core,
        )

    def fit(
        self,
        vce: str = "ols",
        cluster: Optional[str | list[str]] = None,
        alpha: float = 0.05,
        savefe: bool = False,
        timevar: Optional[str] = None,
    ) -> ResultSchema:
        """
        Fit absorbing OLS model.

        Parameters
        ----------
        vce : str
            Variance-covariance estimator type. "ols", "robust", "cluster",
            or "dkraay" supported.
        cluster : str | list[str], optional
            Cluster variable name(s) (required when vce="cluster").
            Supports 1-way or 2-way clustering.
        alpha : float
            Significance level for confidence intervals.
        timevar : str, optional
            Time variable name (required when vce="dkraay").

        Returns
        -------
        ResultSchema
            Fitted result object.
        """
        is_dkraay = vce.startswith("dkraay")
        vce_core = "dkraay" if is_dkraay else vce
        bw = None
        if is_dkraay:
            parts = vce.split("_")
            if len(parts) > 1:
                try:
                    bw = int(parts[1])
                except ValueError:
                    raise ValueError(
                        f"dkraay bandwidth must be an integer, got '{parts[1]}'"
                    )

        if vce_core not in ("ols", "robust", "cluster", "dkraay"):
            raise ValueError(f"vce='{vce}' not supported.")
        if vce_core == "cluster" and cluster is None:
            raise ValueError("cluster variable required when vce='cluster'.")
        if vce_core == "dkraay" and timevar is None:
            raise ValueError("timevar required when vce='dkraay'.")
        if vce_core == "dkraay" and cluster is not None:
            raise ValueError("cluster is not compatible with vce='dkraay'.")
        if vce_core not in ("cluster", "dkraay") and cluster is not None:
            raise ValueError("cluster only used when vce='cluster'.")
        if vce_core == "cluster" and isinstance(cluster, list) and len(cluster) > 2:
            raise ValueError("Only 1-way and 2-way clustering are supported.")

        cluster_vars = [cluster] if isinstance(cluster, str) else cluster

        # Decide MAP vs LSDV before building dummy matrices
        _, _, _, _, fe_info = self._prepare_data(cluster_vars=cluster_vars, build_dummies=False)
        use_map = self._use_map(fe_info)
        # DK VCE is always computed on partialled-out data (MAP path)
        if vce_core == "dkraay":
            use_map = True

        if use_map:
            # MAP path does not yet support slope absorption (_cons recovery
            # and variance formulas need adaptation). Stata comparison cases
            # use small-N datasets that stay on the LSDV path.
            has_slopes = any(
                len(spec.slopes) > 0 for spec in self.absorb_specs
            )
            if has_slopes:
                raise NotImplementedError(
                    "MAP path does not currently support slope absorption "
                    "(absorb(...##c.var) / absorb(...#c.var)). "
                    "Use technique='lsdv' for slope absorption models."
                )
            if savefe:
                raise NotImplementedError(
                    "savefe not supported with technique='map'. "
                    "Use technique='lsdv' for savefe."
                )
            if self._weights is not None:
                raise NotImplementedError(
                    "aweight not supported with technique='map'. "
                    "Use technique='lsdv' for weighted models."
                )

            # -------- MAP path --------
            mr = self._fit_map(vce_core, cluster_vars, bw, timevar, alpha, savefe)
            beta_reported = mr["beta_reported"]
            cov_reported = mr["cov_reported"]
            se = mr["se"]
            t_stats = mr["t_stats"]
            p_values = mr["p_values"]
            ci_low = mr["ci_low"]
            ci_high = mr["ci_high"]
            df_model = mr["df_model"]
            df_resid = mr["df_resid"]
            df_a = mr["df_a"]
            k_full = mr["k_full"]
            rss = mr["rss"]
            tss = mr["tss"]
            r2 = mr["r2"]
            r2_adj = mr["r2_adj"]
            rmse = mr["rmse"]
            rss_r = mr["rss_r"]
            f_stat = mr["f_stat"]
            f_pvalue = mr["f_pvalue"]
            n = mr["n"]
            n_input_rows = mr["n_input_rows"]
            sample_mask = mr["sample_mask"]
            cluster_count = mr["cluster_count"]
            vce_core = mr["vce_core"]

            # Ensure local variables exist for postestimation assignment at end of fit()
            beta_full = self._beta_full
            cov_full = self._cov_full
            T = self._T

        else:
            # -------- LSDV path --------
            # Memory safety check: estimate dummy matrix size before allocating
            n_est = int(np.sum(fe_info[0]['counts'])) if fe_info else self._n_input_rows
            total_fe_levels = sum(info['num_levels'] for info in fe_info)
            # Each FE dummy matrix is n x (G-1) float64 bytes; also account for slopes
            estimated_dummies = total_fe_levels - len(self.absorb_specs)
            estimated_memory_gb = (n_est * estimated_dummies * 8) / (1024**3)
            if estimated_memory_gb > 2.0:
                import warnings
                warnings.warn(
                    f"LSDV dummy matrix estimated at {estimated_memory_gb:.1f} GB "
                    f"({n_est:,} obs x {estimated_dummies:,} dummies). "
                    f"Consider using technique='map' to reduce memory usage.",
                    ResourceWarning,
                    stacklevel=2,
                )

            X_full, y, sample_mask, n_input_rows, _ = self._prepare_data(cluster_vars=cluster_vars)
            n = len(y)
            k_full = X_full.shape[1]
            w = self._weights

            # LSDV estimation (weighted if aweight provided)
            if w is not None:
                XtX = (X_full * w[:, None]).T @ X_full
                Xty = X_full.T @ (w * y)
            else:
                XtX = X_full.T @ X_full
                Xty = X_full.T @ y
            beta_full = np.linalg.solve(XtX, Xty)

            # Residuals
            y_hat = X_full @ beta_full
            residuals = y - y_hat

            # Sum of squares
            if w is not None:
                rss = float(np.sum(w * residuals ** 2))
                y_mean = float(np.sum(w * y) / n)
                tss = float(np.sum(w * (y - y_mean) ** 2))
            else:
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
            if vce_core == "cluster":
                if len(self._cluster_arrs) == 1:
                    unique_clusters = np.unique(self._cluster_arrs[0])
                    cluster_count = len(unique_clusters)
                else:
                    cluster_count = min(len(np.unique(ca)) for ca in self._cluster_arrs)
                df_resid = float(cluster_count - 1)
            elif vce_core == "robust":
                df_resid = float(n - k_full)
            else:
                df_resid = float(n - k_full)

            # RMSE denominator: align with Stata's used_df_r.
            if self._reghdfe_mode:
                # reghdfe subtracts levels of FEs nested in cluster variables.
                dummy_info = getattr(self, "_dummy_info", [])
                nested_levels = sum(
                    info["num_levels"] for info in dummy_info
                    if self._fe_is_nested_in_cluster(info)
                )
                rmse_df = float(n - df_model - df_a - nested_levels)
            else:
                # areg: constant is estimated separately; nested FEs redundant.
                cons_penalty = 1.0 if self.add_constant else 0.0
                rmse_df = float(n - df_model - df_a - cons_penalty)
            rmse = np.sqrt(rss / rmse_df) if rmse_df > 0 else 0.0

            # Adjusted R-squared
            if self._reghdfe_mode:
                r2_adj = 1.0 - (rss / rmse_df) / (tss / (n - 1)) if rmse_df > 0 and tss > 0 else None
            else:
                r2_adj = 1.0 - (1.0 - r2) * (n - 1) / rmse_df if rmse_df > 0 else 0.0

            # Variance-covariance matrix on full LSDV coefficients
            if vce_core == "ols":
                sigma2 = rss / df_resid if df_resid > 0 else 0.0
                cov_full = sigma2 * np.linalg.inv(XtX)
            elif vce_core == "robust":
                # HC1 robust sandwich on full LSDV coefficients.
                # For aweighted regression the score contribution is w_i * x_i * e_i,
                # so the meat is X' W^2 diag(e^2) X (VCE-005).
                XtX_inv = np.linalg.inv(XtX)
                if w is not None:
                    meat = (X_full * ((w ** 2) * (residuals ** 2))[:, np.newaxis]).T @ X_full
                else:
                    meat = X_full.T @ (X_full * (residuals ** 2)[:, np.newaxis])
                cov_full = XtX_inv @ meat @ XtX_inv
                if n > k_full:
                    cov_full *= n / (n - k_full)
            else:
                # Cluster-robust VCE on full LSDV
                XtX_inv = np.linalg.inv(XtX)
                if len(self._cluster_arrs) == 1:
                    # Single-way clustering
                    if w is not None:
                        # Weighted cluster meat
                        k = X_full.shape[1]
                        unique_clusters = np.unique(self._cluster_arrs[0])
                        meat = np.zeros((k, k))
                        for g_val in unique_clusters:
                            mask = self._cluster_arrs[0] == g_val
                            score_g = X_full[mask].T @ (w[mask] * residuals[mask])
                            meat += np.outer(score_g, score_g)
                        cluster_count = len(unique_clusters)
                    else:
                        from stataflow.estimators._vce_utils import compute_cluster_meat
                        meat, cluster_count = compute_cluster_meat(
                            X_full, residuals, self._cluster_arrs[0]
                        )

                    # Small-sample adjustment: Stata uses k_eff = k_x + df_a + nested_adj
                    k_x_cluster = len(self._x_indices_in_full)
                    k_eff = self._cluster_k_eff(k_x_cluster)
                    n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
                    g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
                    cov_full = n_adj * g_adj * XtX_inv @ meat @ XtX_inv
                else:
                    # Multi-way clustering (2-way)
                    cov_full, cluster_count = self._compute_multiway_cluster_vce(
                        X_full, residuals, XtX_inv, k_full, n
                    )

            # Build transformation from full LSDV parameters to reported parameters
            # Reported order: [x1, x2, ..., _cons]
            # _cons = constant + sum over FE groups of mean(dummy coefficients for that FE)
            report_dim = k_x + (1 if "_cons" in self._coef_names else 0)
            T = np.zeros((report_dim, k_full))

            # Map x coefficients
            for i, full_idx in enumerate(self._x_indices_in_full):
                T[i, full_idx] = 1.0

            # Map _cons as linear combination.
            # Stata's areg/reghdfe report _cons as the regression-through-means
            # intercept: _cons = mean(y) - sum_j mean(x_j) * beta_j.  In the
            # LSDV parametrisation this equals b0 + sum_g sum_l (n_{g,l}/n) *
            # alpha_{g,l}, where alpha includes intercept and slope interactions.
            # We therefore weight each FE dummy by its share of observations.
            if "_cons" in self._coef_names:
                cons_row = report_dim - 1
                n = len(self._df)
                if self._constant_idx_reduced is not None:
                    T[cons_row, self._constant_idx_reduced] = 1.0
                for fe_idx, info in enumerate(self._dummy_info):
                    counts = info['counts']
                    levels = info['levels']
                    col_types = info.get('column_types', [])
                    len(info.get('slopes', []))
                    first_fe_no_const = (not self.add_constant) and (fe_idx == 0)
                    n_intercept_cols = len(levels) if first_fe_no_const else len(levels) - 1

                    for orig_idx, red_idx in zip(
                        self._fe_dummy_indices[fe_idx],
                        self._fe_dummy_indices_reduced[fe_idx]
                    ):
                        col_pos = orig_idx - info['start']
                        if 0 <= col_pos < len(col_types):
                            col_type = col_types[col_pos]
                        else:
                            col_type = ("intercept",)

                        if col_type[0] == "intercept":
                            if first_fe_no_const:
                                level_idx = col_pos
                            else:
                                level_idx = col_pos + 1
                            lvl = levels[level_idx]
                            weight = counts[level_idx] / n
                            T[cons_row, red_idx] += weight
                        elif col_type[0] == "slope":
                            slope_var = col_type[1]
                            # Slope interaction columns follow intercept dummies
                            # in blocks of (G or G-1) per slope variable.
                            slope_block_pos = col_pos - n_intercept_cols
                            n_cols_per_slope = len(levels) if first_fe_no_const else len(levels) - 1
                            if n_cols_per_slope > 0:
                                slope_col_in_block = slope_block_pos % n_cols_per_slope
                                if first_fe_no_const:
                                    level_idx = slope_col_in_block
                                else:
                                    level_idx = slope_col_in_block + 1
                            else:
                                level_idx = 0
                            lvl = levels[level_idx]
                            weight = counts[level_idx] / n
                            if self._df is not None and slope_var in self._df.columns:
                                group_mask = self._df[info['var']] == lvl
                                slope_mean_g = (
                                    self._df.loc[group_mask, slope_var].mean()
                                    if group_mask.any() else 0.0
                                )
                            else:
                                slope_mean_g = 0.0
                            T[cons_row, red_idx] += weight * slope_mean_g

            beta_reported = T @ beta_full
            cov_reported = T @ cov_full @ T.T

            # Reghdfe recovers the reported constant from the sample means after
            # estimating the slopes.  This also gives a stable normalization for
            # disconnected FE graphs, where dummy coefficients are not unique.
            has_slopes = any(len(info.get('slopes', [])) > 0 for info in self._dummy_info)
            if "_cons" in self._coef_names and self._df is not None:
                retained_x_names = [name for name in self._coef_names if name != "_cons"]
                k_slopes = len(retained_x_names)
                x_means = np.array([self._df[name].mean() for name in retained_x_names])
                beta_reported[k_slopes] = float(
                    np.mean(y) - x_means @ beta_reported[:k_slopes]
                )
                # Slope absorption also changes the constant's delta-method VCE.
                if has_slopes and vce_core == "ols":
                    cov_slopes = cov_full[np.ix_(self._x_indices_in_full, self._x_indices_in_full)]
                    sigma2 = rss / df_resid if df_resid > 0 else 0.0
                    cons_var = float(x_means @ cov_slopes @ x_means + sigma2 / n)
                    cov_reported[k_slopes, k_slopes] = max(cons_var, 0.0)
                    # Approximate covariance using delta method
                    cov_cons_x = -cov_slopes @ x_means
                    cov_reported[k_slopes, :k_slopes] = cov_cons_x
                    cov_reported[:k_slopes, k_slopes] = cov_cons_x

            # For multi-way clustering, cov_reported can be non-PSD due to
            # inclusion-exclusion. Apply reghdfe-style PSD fix (preserve slopes).
            if vce_core == "cluster" and len(self._cluster_arrs) > 1:
                from stataflow.estimators._vce_utils import fix_psd_reghdfe
                constant_index = (
                    self._coef_names.index("_cons") if "_cons" in self._coef_names else None
                )
                cov_reported = fix_psd_reghdfe(
                    cov_reported,
                    constant_index=constant_index,
                    coefficient_scales=self._reghdfe_coefficient_scales(y),
                )

            # Standard errors
            diag_cov = np.diag(cov_reported)
            diag_cov = np.maximum(diag_cov, 0)
            se = np.sqrt(diag_cov)

            # t-statistics and p-values
            t_stats = np.divide(
                beta_reported,
                se,
                out=np.full_like(beta_reported, np.nan, dtype=float),
                where=se > 0,
            )
            p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=df_resid))

            # Confidence intervals
            t_crit = t_dist.ppf(1 - alpha / 2, df=df_resid)
            ci_low = beta_reported - t_crit * se
            ci_high = beta_reported + t_crit * se

            # F-statistic
            rss_r = None
            if self.add_constant and df_model > 0 and rmse_df > 0 and rss > 0:
                if vce_core == "ols":
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
            dependent_variable=self.y,
            regressors=list(self.x),
            estimator_name="Absorbing least squares",
            vcetype=vce,
            absorb_var=absorb_var,
            absorb_vars=self.absorb_vars,
            cluster_var=cluster if vce_core == "cluster" else None,
            has_constant=self.add_constant,
        )

        result.sample = SampleInfo(
            nobs=n,
            n_input_rows=n_input_rows,
            sample_mask=sample_mask,
            group_count=(
                int(self._df[self.absorb_vars[0]].nunique())
                if len(self.absorb_vars) == 1
                else None
            ),
        )
        result.fit = FitInfo(
            df_model=df_model,
            df_resid=df_resid,
            df_a=df_a,
            rank=int(np.linalg.matrix_rank(cov_reported)),
            rss=rss,
            tss=tss,
            mss=rss_r - rss if rss_r is not None else None,
            rmse=rmse,
            r2=r2,
            r2_adj=r2_adj,
            f_stat=f_stat,
            f_pvalue=f_pvalue,
            model_test="F",
            model_stat=f_stat,
            model_df_num=df_model,
            model_df_den=df_resid,
            model_pvalue=f_pvalue,
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
        result._model = self

        if savefe:
            result.fixed_effects = self.save_fixed_effects()

        result.validate()
        return result

    def predict(self, type: str = "xb", newdata: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Generate predictions after fitting."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted. Call fit() first.")
        if type not in ("xb", "residuals", "d", "xbd", "dresiduals", "stdp"):
            raise ValueError(
                f"type='{type}' not supported for AbsorbingOLS. "
                "Use 'xb', 'residuals', 'd', 'xbd', 'dresiduals', or 'stdp'."
            )

        if newdata is not None:
            raise NotImplementedError("Out-of-sample prediction for AbsorbingOLS not yet implemented.")

        n = len(self._dep_var)
        xbd = self._design_matrix @ self._beta_full

        if type == "xbd":
            # MAP path: _design_matrix does not contain FE dummies,
            # so xbd must be reconstructed from y - residuals (PANEL-09).
            if hasattr(self, "_map_residuals") and self._map_residuals is not None:
                return self._dep_var - self._map_residuals
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
            return self._dep_var - xb_reported
        return xb_reported  # fallback

    def margins(self, type: str = "dydx") -> SimpleNamespace:
        """Compute marginal effects."""
        if not self._is_fitted:
            raise ValueError("Model has not been fitted. Call fit() first.")
        from stataflow.postestimation import margins_ame_linear, _build_margins_result

        k = len(self._beta_reported)
        effects = margins_ame_linear(self._beta_reported)
        J = np.eye(k)
        return _build_margins_result(
            effects, J, self._cov_reported, self._coef_names, self._result.sample.nobs
        )

    def save_fixed_effects(self) -> dict[str, pd.Series]:
        """
        Recover and return fixed-effect alpha estimates by absorb variable.

        Returns
        -------
        dict[str, pd.Series]
            Mapping from absorb variable name to a Series indexed by factor level
            with the estimated FE coefficient (alpha) for that level.
        """
        if not self._is_fitted:
            raise ValueError("Model has not been fitted. Call fit() first.")
        if self._beta_full is None:
            raise ValueError("No fitted coefficients available.")

        import warnings
        reduced_to_orig = {v: k for k, v in self._orig_to_reduced.items()}
        result: dict[str, pd.Series] = {}

        for fe_idx, info in enumerate(self._dummy_info):
            var = info["var"]
            levels = info["levels"]
            num_levels = info["num_levels"]
            start = info["start"]
            kept_reduced = self._fe_dummy_indices_reduced[fe_idx]
            column_types = info.get("column_types", [])

            alphas = np.zeros(num_levels)
            has_slopes = False
            # If add_constant or not the first FE, the first level is the reference
            # and dummy columns correspond to levels[1:].
            # Otherwise (no constant, first FE), all levels have dummies.
            if self.add_constant or fe_idx > 0:
                for r in kept_reduced:
                    o = reduced_to_orig[r]
                    j = o - start
                    ctype = column_types[j] if j < len(column_types) else ("intercept",)
                    if ctype[0] == "slope":
                        has_slopes = True
                        continue
                    level_idx = 1 + j
                    if 0 <= level_idx < num_levels:
                        alphas[level_idx] = self._beta_full[r]
            else:
                for r in kept_reduced:
                    o = reduced_to_orig[r]
                    j = o - start
                    ctype = column_types[j] if j < len(column_types) else ("intercept",)
                    if ctype[0] == "slope":
                        has_slopes = True
                        continue
                    if 0 <= j < num_levels:
                        alphas[j] = self._beta_full[r]

            if has_slopes:
                warnings.warn(
                    f"save_fixed_effects() for '{var}' currently saves only intercepts; "
                    "slope coefficients are not yet recovered.",
                    UserWarning,
                    stacklevel=2,
                )

            result[var] = pd.Series(alphas, index=levels)

        return result
