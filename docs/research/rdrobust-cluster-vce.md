# RD Robust Cluster VCE — Research Archive

**Version researched:** `rdrobust` v10.0.0 (2025-06-30)
**Stata source:** `rdrobust.ado` L22–54 (VCE parsing), L325–331 (cluster data setup), L627–631 (effective cluster), L803–808 (VCE computation)
**Reference:** CCT (2014a), Cameron & Miller (2015, _J. Human Resources_)
**Python target:** `stataflow.estimators.rdrobust._vce_cluster()`, `_vce_nncluster()`

---

## 1. VCE Parsing

**Source:** `rdrobust.ado` L22–54

### 1.1 Syntax

```
vce(nn [nnmatch])           → vce_type="NN", vce_select="nn"
vce(hc0)                    → vce_type="HC0", vce_select="hc0"
vce(hc1|hc2|hc3)            → vce_type="HC1"|"HC2"|"HC3"
vce(cluster varname)        → vce_type="Cluster", vce_select="hc0" (residual basis)
vce(nncluster varname)      → vce_type="NNcluster", vce_select="nn" (residual basis)
vce(cluster varname nnmatch) → vce_type="Cluster", nnmatch overridden
```

### 1.2 Residual Basis Mapping (L52–54)

```stata
if ("`vce_select'"=="cluster")   local vce_select = "hc0"
if ("`vce_select'"=="nncluster") local vce_select = "nn"
```

Critical: `cluster` uses **HC0 residuals** as the basis, `nncluster` uses **NN residuals** as the basis. The clustering only affects the **aggregation** (meat matrix construction), not the residual computation.

---

## 2. Cluster Variable Setup

**Source:** L325–331

```mata
if ("`cluster'"!="") {
    C  = st_data(.,("`clustvar'"), 0)
    C_l  = C[ind_l]; C_r  = C[ind_r]
    indC_l = order(C_l,1);  indC_r = order(C_r,1)
    g_l = rows(panelsetup(C_l[indC_l],1))
    g_r = rows(panelsetup(C_r[indC_r],1))
    st_numscalar("g_l", g_l)
    st_numscalar("g_r", g_r)
}
```

- `order(C_l, 1)`: Returns indices that sort the cluster variable
- `panelsetup(C_l[indC_l], 1)`: Mata function that returns panel boundaries (start/end rows for each unique cluster)
- `g_l`, `g_r`: Number of unique clusters on each side of the cutoff

### 2.1 Effective Cluster After Bandwidth

**Source:** L627–631

```mata
if ("`cluster'"!="") {
    eC_l  = C_l[ind_l];    eC_r  = C_r[ind_r]
    indC_l = order(eC_l,1); indC_r = order(eC_r,1)
    g_l = rows(panelsetup(eC_l[indC_l],1))
    g_r = rows(panelsetup(eC_r[indC_r],1))
}
```

The effective cluster counts `g_l`, `g_r` are computed **after** bandwidth restriction (only observations within the bandwidth window are included).

---

## 3. Cluster-Robust Sandwich Estimator

### 3.1 VCE Function Signature

**Source:** Mata function `rdrobust_vce()` (compiled `.mo` file, logic inferred from usage)

```mata
V = rdrobust_vce(dim, s, RX, res, C, indC)
```

Parameters:
- `dim`: number of outcome columns (0 = sharp, 1 = fuzzy, >1 = fuzzy + covs)
- `s`: linear combination vector (e.g., `s_Y` = `[1]` for sharp, `[1/tau_T, -tau_Y/tau_T²]` for fuzzy)
- `RX`: weighted design matrix `R_p * W_h` (element-wise) or `Q_q` (bias-corrected)
- `res`: residual vector (NN or HC0)
- `C`: cluster ID vector (0 if no clustering)
- `indC`: cluster sort index (0 if no clustering)

### 3.2 Without Clustering (`C=0`)

```mata
// Sandwich: M = Σ_i (s' * RX_i') * res_i^2 * (RX_i * s)
// V = invG * M * invG
```

The meat matrix is a sum over individual observations.

### 3.3 With Clustering (`C ≠ 0`)

```mata
// For each cluster g:
//   score_g = Σ_{i in g} s' * RX_i' * res_i
//   M_g = score_g * score_g'
// M = Σ_g M_g
// V = invG * M * invG
```

The key difference: scores are **summed within each cluster** before taking the outer product. This accounts for arbitrary within-cluster correlation.

### 3.4 Invocation Pattern

**Source:** L803–808

```mata
V_Y_cl_l = invG_p_l * rdrobust_vce(dT+dZ, s_Y, R_p_l:*W_h_l, res_h_l, eC_l, indC_l) * invG_p_l
V_Y_cl_r = invG_p_r * rdrobust_vce(dT+dZ, s_Y, R_p_r:*W_h_r, res_h_r, eC_r, indC_r) * invG_p_r
V_Y_bc_l = invG_p_l * rdrobust_vce(dT+dZ, s_Y, Q_q_l,     res_b_l, eC_l, indC_l) * invG_p_l
V_Y_bc_r = invG_p_r * rdrobust_vce(dT+dZ, s_Y, Q_q_r,     res_b_r, eC_r, indC_r) * invG_p_r
```

Four variance matrices are computed:
- `V_Y_cl_l/r`: Conventional variance (uses `R_p * W_h` design + `res_h` residuals)
- `V_Y_bc_l/r`: Robust (bias-corrected) variance (uses `Q_q` design + `res_b` residuals)

### 3.5 Scalar Variance Extraction

```mata
V_tau_cl = scalepar^2 * factorial(deriv)^2 * (V_Y_cl_l + V_Y_cl_r)[deriv+1, deriv+1]
V_tau_rb = scalepar^2 * factorial(deriv)^2 * (V_Y_bc_l + V_Y_bc_r)[deriv+1, deriv+1]
```

---

## 4. Small-Sample Correction

### 4.1 Cluster Count Adjustment

In standard Stata clustered SEs, a small-sample correction `G/(G-1) * (N-1)/(N-k)` is applied. However, `rdrobust` uses a **different approach**:

- The sandwich estimator uses `g_l` and `g_r` (number of clusters per side) directly
- The CER bandwidth adjustment changes when clustering: `cer_h = (g_l+g_r)^(-p/((3+p)*(3+2p)))` instead of `N^(-p/((3+p)*(3+2p)))` (L495)

The `rdrobust` package does NOT apply the standard `G/(G-1)` correction factor. This is specific to the RD context where the effective degrees of freedom are not simply `G-1`.

### 4.2 nncluster Variant

When `vce(nncluster varname)`:
- Residuals computed via NN (nearest-neighbor) method
- But aggregated by cluster for the meat matrix
- The NN residuals are leave-neighborhood-out, which provides an additional layer of robustness

---

## 5. Residual Computation Interaction

**Source:** L790–801

```mata
res_h_l = rdrobust_res(eX_l, eY_l, eT_l, eZ_l, predicts_p_l, hii_p_l,
                       "`vce_select'", `nnmatch', edups_l, edupsid_l, `p'+1)
res_h_r = rdrobust_res(eX_r, eY_r, eT_r, eZ_r, predicts_p_r, hii_p_r,
                       "`vce_select'", `nnmatch', edups_r, edupsid_r, `p'+1)

if ("`vce_select'"=="nn") {
    res_b_l = res_h_l; res_b_r = res_h_r  // NN: same residuals for both
} else {
    res_b_l = rdrobust_res(eX_l, eY_l, eT_l, eZ_l, predicts_q_l, hii_q_l,
                           "`vce_select'", `nnmatch', edups_l, edupsid_l, `q'+1)
    res_b_r = rdrobust_res(eX_r, eY_r, eT_r, eZ_r, predicts_q_r, hii_q_r,
                           "`vce_select'", `nnmatch', edups_r, edupsid_r, `q'+1)
}
```

Key detail: For `nn` residuals, `res_b` uses the same NN residuals as `res_h` (no separate computation for bias bandwidth). For HC0/HC1/HC2/HC3, separate residuals are computed using the bias-correction polynomial order `q`.

---

## 6. Python Implementation Path

### 6.1 Cluster-Robust Meat Matrix

```python
def _vce_cluster(RX, res, cluster_ids, s=None):
    """
    Cluster-robust meat matrix for local polynomial RD.

    Parameters
    ----------
    RX : np.ndarray, shape (n, k)
        Weighted design matrix (R_p * W_h or Q_q)
    res : np.ndarray, shape (n,) or (n, d)
        Residuals
    cluster_ids : np.ndarray, shape (n,)
        Cluster identifier for each observation
    s : np.ndarray, shape (k,) or None
        Linear combination vector (for fuzzy/covariate-adjusted)

    Returns
    -------
    meat : np.ndarray, shape (k, k)
    """
    if s is not None:
        score_i = RX * res[:, None] * s[None, :]  # (n, k)
    else:
        score_i = RX * res[:, None]  # (n, k)

    unique_clusters = np.unique(cluster_ids)
    meat = np.zeros((RX.shape[1], RX.shape[1]))
    for g in unique_clusters:
        mask = cluster_ids == g
        score_g = score_i[mask].sum(axis=0)
        meat += np.outer(score_g, score_g)
    return meat
```

### 6.2 Required Changes to `RDRobust.fit()`

1. **Parameter:** `cluster: str | None = None` for `vce(cluster)` or `vce(nncluster)`

2. **Sample screening:** Drop rows where cluster variable is missing (L128)

3. **Cluster data setup:**
   ```python
   if cluster is not None:
       C = data[cluster].values
       C_l = C[X < c]; C_r = C[X >= c]
       # After bandwidth restriction:
       eC_l = C_l[ind_l]; eC_r = C_r[ind_r]
       g_l = len(np.unique(eC_l))
       g_r = len(np.unique(eC_r))
   ```

4. **VCE call modification:** Pass `eC_l, eC_r` to the VCE function instead of `0, 0`

5. **CER bandwidth adjustment:** When cluster is present, use `(g_l+g_r)` instead of `N`:
   ```python
   cer_h = (g_l + g_r) ** (-p / ((3+p) * (3+2*p)))
   ```

### 6.3 Implementation Order

1. **`_vce_cluster()` helper** — cluster-robust meat matrix (low complexity)
2. **Cluster data flow in `fit()`** — pass cluster variable through the pipeline (medium)
3. **nncluster variant** — NN residuals + cluster aggregation (low, reuses existing NN residual code)
4. **CER × cluster interaction** — bandwidth adjustment (low, formula change only)

### 6.4 Key Edge Cases

1. **Single-observation clusters:** A cluster with only 1 observation contributes `score_i * score_i'` — no special handling needed.

2. **Cluster variable nested in running variable:** When every value of `X` is its own cluster (e.g., cluster on individual ID), cluster-robust SEs should approach HC0 SEs with `G/(G-1)` scaling.

3. **Cross-cutoff clusters:** Clusters that span both sides of the cutoff are handled naturally — they appear in both `C_l` and `C_r` separately.

4. **Cluster count < 10:** Stata `rdrobust` does not warn. Python should match this behavior.

---

## 7. Stata Source Line Reference

| Feature | Lines | Description |
|---------|-------|-------------|
| VCE syntax parsing | L22–54 | cluster, nncluster, nnmatch |
| Residual basis mapping | L52–54 | cluster → hc0, nncluster → nn |
| Missing cluster drop | L128 | `drop if mi(clustvar)` |
| Cluster data setup | L325–331 | C, indC, g_l, g_r |
| Effective cluster | L627–631 | Post-bandwidth cluster counts |
| Residual computation | L790–801 | NN vs HC0 basis for res_h, res_b |
| VCE with cluster | L803–808 | `rdrobust_vce(..., eC_l, indC_l)` |
| CER with cluster | L495 | `(g_l+g_r)` in CER formula |
| Output | L924 | Number of clusters in output table |

---

## 8. Validation Strategy

### Synthetic Test Cases

| case_id | Description | Risk Focus |
|---------|-------------|------------|
| `w8_cluster_basic` | Sharp RD + `vce(cluster)` | Cluster SE vs HC0 ratio |
| `w8_cluster_nncluster` | Sharp RD + `vce(nncluster)` | NN + cluster interaction |
| `w8_cluster_few` | Only 5 clusters per side | Small-cluster behavior |
| `w8_cluster_covs` | Sharp RD + covariates + cluster | 3-way interaction |
| `w8_cluster_fuzzy` | Fuzzy RD + cluster | Full complexity |
| `w8_cluster_cer` | CER bandwidth + cluster | Correct CER scaling with G |

### Real-Data Validation

Use `rdrobust_senate.dta` with a synthetic cluster variable (e.g., state groups), or identify a public RD dataset with natural clustering (e.g., school-level programs with student-level data).
