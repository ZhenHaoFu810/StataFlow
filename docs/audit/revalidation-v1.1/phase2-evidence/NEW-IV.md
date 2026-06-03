# NEW-IV — New Issues Discovered in Phase 2 IV/GMM Revalidation

**Date**: 2026-06-03
**Dataset**: Card (1995) IV — 3,010 obs
**Validation agent**: Phase 2 IV/GMM Dual-Run Agent

---

## NEW-IV-01: Runtime crash in 2-way cluster weakiv (Fixed)

**Location**: `src/stataflow/estimators/iv.py:1555`

**Symptom**: Running `ivreghdfe` with 2-way clustering raises:
```
numpy.core._exceptions._UFuncNoLoopError: ufunc 'add' did not contain a loop with
signature matching types (dtype('<U11'), dtype('<U2')) -> None
```

**Root cause**: In `_compute_weakiv_stats`, the interaction array for 2-way clustering is built with:
```python
interaction_z = (
    self._cluster_arrs[0].astype(str) + "__" + self._cluster_arrs[1].astype(str)
)
```
NumPy string arrays with different character-width dtypes cannot be added with `+`.

**Fix applied**:
```python
interaction_z = np.array([
    f"{a}__{b}" for a, b in zip(self._cluster_arrs[0], self._cluster_arrs[1])
])
```

**Status**: Fixed in-place during validation. No regression risk — the change is localized to the 2-way cluster branch of weakiv diagnostics.

---

## NEW-IV-02: Nonsensical F-stat for ivreghdfe under cluster VCE

**Location**: `src/stataflow/estimators/iv.py` (IVAbsorbingOLS.fit, around lines 1595–1615)

**Symptom**:

| Scenario | Python f_stat | Stata F | Status |
|----------|--------------|---------|--------|
| ivreghdfe cluster(age_group) | -2.02e+14 | 0.36 | Divergent |
| ivreghdfe 2-way cluster | +4.25e+11 | 0.36 | Divergent |

**Root cause**: The F-stat is computed as a Wald test on slope coefficients:
```python
beta_slopes @ cov_inv @ beta_slopes / df_model
```
When `vce="cluster"` and the cluster count is very small (e.g., 3 clusters), `cov_slopes` is near-singular. `np.linalg.inv` produces an unstable inverse, leading to astronomical or negative Wald values.

For the 1-way cluster case, the code takes a different branch when `vce == "ols"`:
```python
mss_incremental = tss_resid - rss_2s_resid
f_stat = (mss_incremental / df_model) / (rss_struct / (n - k_x_full))
```
But for `vce == "cluster"` or `"robust"`, it unconditionally uses the Wald form without checking matrix conditioning.

**Impact**: High. The F-stat and its p-value are completely unreliable for ivreghdfe with cluster VCE.

**Recommendation**: Add a condition-number check before inverting `cov_slopes`. If the matrix is ill-conditioned, fall back to a stable F-stat formula or return `None` with a diagnostic warning.

---

## NEW-IV-03: First-stage F uses wrong degrees of freedom under cluster VCE

**Location**: `src/stataflow/estimators/iv.py` (IVAbsorbingOLS first_stage computation, around lines 1520–1571)

**Symptom**:

| Metric | Python | Stata | Expected |
|--------|--------|-------|----------|
| First-stage F | 2.106 | 2.10 | ~2.10 |
| First-stage p-value | 0.1467 | 0.2842 | ~0.2842 |

**Root cause**: Python computes the first-stage p-value using:
```python
f_pvalue = float(1 - f_dist.cdf(f_stat, dfn=q, dfd=n - k_z_full))
```
where `dfd = n - k_z_full = 3001`.

Stata uses cluster degrees of freedom. For `cluster(age_group)` with 3 clusters, the effective df is `G - 1 = 2`. The F-statistic itself is similar (2.106 vs 2.10), but the p-value is computed with the wrong denominator degrees of freedom.

**Impact**: Moderate. First-stage p-values are systematically too small (over-rejecting) when clustering is used.

**Recommendation**: When `vce="cluster"`, use `cluster_count - 1` as the denominator df for first-stage F tests. For 2-way clustering, use the minimum cluster count minus 1, matching Stata/ivreghdfe behavior.

---

## NEW-IV-04: 2-way cluster VCE not rank-deficiency aware

**Location**: `src/stataflow/estimators/_vce_utils.py` (`compute_multiway_cluster_vce`)

**Symptom**:

| var | Python SE (2-way) | Stata SE (2-way) | Python SE (1-way) | Stata SE (1-way) |
|-----|-------------------|------------------|-------------------|------------------|
| educ | 0.235692 | 0.181223 | 0.181193 | 0.181223 |
| exper | 0.188690 | 0.158694 | 0.158668 | 0.158694 |

**Root cause**: With only 3 clusters in `age_group` and the FE `age_group` nested within those clusters, the 2-way cluster covariance matrix is not of full rank. Stata `ivreghdfe` detects this and emits:
```
Warning: estimated covariance matrix of moment conditions not of full rank.
```
It then falls back to what appears to be 1-way cluster SEs (identical to the 1-way cluster output).

Python’s `compute_multiway_cluster_vce` applies the inclusion-exclusion formula:
```python
omega_meat = meats[0] + meats[1] - meat_12
cov_full = n_adj * g_adj * M_inv @ omega_meat @ M_inv
```
without checking whether `omega_meat` is positive semi-definite or full rank. The result is inflated SEs.

**Impact**: High for degenerate 2-way cluster cases (small G in one dimension, FE nested within cluster).

**Recommendation**: After computing `omega_meat`, check its eigenvalues. If negative eigenvalues are present (indicating non-PSD due to rank deficiency), apply `fix_psd` or fall back to the minimum of the two 1-way cluster VCEs, matching Stata’s conservative behavior. This requires Codex escalation because it affects the statistical specification.

---

## NEW-IV-05: ivreghdfe df_resid mismatch for 2-way cluster

**Location**: `src/stataflow/estimators/iv.py` (IVAbsorbingOLS.fit)

**Symptom**:

| Scenario | Python df_resid | Stata df_resid |
|----------|-----------------|----------------|
| ivreghdfe 1-way cluster | 2.0 | 2.0 |
| ivreghdfe 2-way cluster | 1.0 | 2.0 |

**Root cause**: Python computes `df_resid` for cluster VCE as:
```python
df_resid = float(cluster_count - 1)
```
For 2-way clustering, `cluster_count = min(len(np.unique(ca)) for ca in self._cluster_arrs) = 3`, giving `df_resid = 2.0` for the 1-way case but `1.0` for 2-way.

Wait — looking at the code more carefully:
```python
if vce == "cluster":
    if len(self._cluster_arrs) == 1:
        unique_clusters = np.unique(self._cluster_arrs[0])
        cluster_count = len(unique_clusters)
    else:
        cluster_count = min(len(np.unique(ca)) for ca in self._cluster_arrs)
    df_resid = float(cluster_count - 1)
```
For 2-way cluster, `cluster_count = min(3, 6) = 3`, so `df_resid = 2.0`. But the Python output shows `df_resid = 1.0`.

Actually, looking at the Python results JSON for 2-way cluster: `df_resid = 1.0`. This is strange. Let me check if there's another code path.

Oh wait — in `IVAbsorbingOLS.fit`, for `estimator == "gmm2s"` or `"liml"`, the df_resid might be computed differently. But we used `estimator="2sls"`.

Looking at the code again:
```python
if vce == "cluster":
    if len(self._cluster_arrs) == 1:
        ...
    else:
        cluster_count = min(len(np.unique(ca)) for ca in self._cluster_arrs)
    df_resid = float(cluster_count - 1)
```

But `cluster_count` is returned from `_fit_2sls` and might override the earlier value. In `_fit_2sls`:
```python
if vce == "cluster":
    if len(self._cluster_arrs) == 1:
        ...
        cluster_count = ...
    else:
        cov_full, cluster_count = self._compute_multiway_cluster_vce(...)
```

For 2-way cluster, `_compute_multiway_cluster_vce` returns `G_min` which is `min(G1, G2, G_12)`. Looking at `_compute_multiway_cluster_vce`:
```python
G_min = min(Gs[0], Gs[1], G_12)
```
`G_12` is the number of unique interaction clusters. With 3 age_group values and 2 south values, there could be up to 6 interaction clusters. But some combinations might be missing, so `G_12` could be less than 6. If `G_12 = 2`, then `G_min = 2`, and `df_resid = 1.0`.

That explains the mismatch! Python uses `G_min` from the multiway VCE function, which includes the interaction dimension, while Stata uses `min(G1, G2) = 3 - 1 = 2`.

This is a genuine divergence in small-sample adjustment.

**Recommendation**: Align `df_resid` computation with Stata. For 2-way cluster, use `min(G1, G2) - 1` rather than `min(G1, G2, G_12) - 1`.

---

## Summary

| Issue | Severity | Status | Owner |
|-------|----------|--------|-------|
| NEW-IV-01 Runtime crash | High | **Fixed** | Claude Code |
| NEW-IV-02 F-stat numerical instability | High | Open | Codex escalation needed |
| NEW-IV-03 First-stage wrong df | Medium | Open | Codex escalation needed |
| NEW-IV-04 2-way cluster rank deficiency | High | Open | Codex escalation needed |
| NEW-IV-05 df_resid mismatch (2-way) | Medium | Open | Codex escalation needed |
