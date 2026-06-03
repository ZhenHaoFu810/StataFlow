# RD Robust Bandwidth Selectors — Complete Family

**Version researched:** `rdrobust` v10.0.0 (2025-06-30), `rdbwselect` v10.0.0
**Stata source:** `research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust.ado` (L345–527), `rdbwselect.ado`
**Reference:** Calonico, Cattaneo, Titiunik (2014a, _Econometrica_), CCT (2014b), CCT (2016b)
**Python target:** `stataflow.estimators.rdrobust._rdbwselect_*()` family

---

## 1. Architecture Overview

The bandwidth selection system has three orthogonal dimensions:

| Dimension | Variants |
|-----------|----------|
| **Criterion** | `mserd` (MSE, difference), `msetwo` (MSE, two-sided), `msesum` (MSE, sum) |
| **Objective** | MSE (point estimation) vs CER (coverage error rate for inference) |
| **Combination** | `comb1` = min(rd, sum), `comb2` = median(rd, sum, two) |

This yields 9 valid selectors: `mserd`, `msetwo`, `msesum`, `msecomb1`, `msecomb2`, `cerrd`, `certwo`, `cersum`, `cercomb1`, `cercomb2`.

The bandwidth selection follows a **three-step plug-in procedure** common to all selectors:

```
Step 1: Pilot bandwidth d_bw  →  Step 2: Bias bandwidth b_bw  →  Step 3: Main bandwidth h_bw
```

---

## 2. Core Mata Function: `rdrobust_bw()`

**Source:** `rdrobust.ado` Mata block, called at L413–484

### 2.1 Signature

```mata
rdrobust_bw(Y, X, T, Z, C, fw, c, o, nu, o_B, h_V, h_B, scaleregul, vce, nnmatch, kernel, dups, dupsid, covs_drop_coll)
```

### 2.2 Returns

A 4-element vector `[V, B, R, rate]`:

| Element | Meaning | Used in |
|---------|---------|---------|
| `V` | Variance component of the MSE expansion | Numerator of bandwidth formula |
| `B` | Bias component (signed, depends on `o_B` and `nu`) | Denominator of bandwidth formula |
| `R` | Regularization term | Added to `B²` with `scaleregul` scaling |
| `rate` | Optimal convergence rate | Exponent in bandwidth formula |

### 2.3 Key Parameters

| Parameter | Step 1 (d_bw) | Step 2 (b_bw) | Step 3 (h_bw) |
|-----------|---------------|---------------|---------------|
| `o` (estimation order) | `q+1` | `q` | `p` |
| `nu` (derivative order) | `q+1` | `p+1` | `deriv` |
| `o_B` (bias order) | `q+2` | `q+1` | `q` |
| `h_V` | `c_bw` (pilot) | `c_bw` (pilot) | `c_bw` (pilot) |
| `h_B` | `range+1e-8` (full range) | `d_bw` (Step 1 result) | `b_bw` (Step 2 result) |

### 2.4 Rate Formula

For sharp RD with `deriv=0, p=1, q=2`:
- Step 1 rate: `1/(2*q+3) = 1/7` (with `o=q+1=3, o_B=q+2=4`)
- Step 2 rate: `1/(2*q+1) = 1/5` (with `o=q=2, o_B=q+1=3`)
- Step 3 rate: `1/(2*q+1) = 1/5` (same structure)

General rate: `rate = 1 / (2*o_B + 1)` when `nu=0`, adjusted for derivative order.

---

## 3. Initial Pilot Bandwidth

**Source:** `rdrobust.ado` L356–398, `rdbwselect.ado` L339–353

### 3.1 Scale Estimator

```
BWp = min(x_sd, x_iq / 1.349)
```

Where `x_iq = p75 - p25` (interquartile range). This is a robust scale estimator.

### 3.2 Kernel Constants

| Kernel | `C_c` | Source Line |
|--------|-------|-------------|
| Triangular | 2.576 | L292 |
| Epanechnikov | 2.34 | L285 |
| Uniform | 1.843 | L289 |

### 3.3 Initial Bandwidth Formula

```
c_bw = C_c * BWp * N^(-1/5)
```

With mass points adjustment (source L398):
```
c_bw = C_c * BWp * M^(-1/5)    // M = total unique X values
```

### 3.4 Bandwidth Bounds

**bwrestrict (L399–402):**
```
c_bw = min(c_bw, max(range_l, range_r))
```

**bwcheck (L403–409):**
- Ensures at least `bwcheck` unique observations within the bandwidth window
- `bw_min_l = |X_uniq_l - c|[bwcheck_l] + 1e-8`
- `c_bw = max(c_bw, bw_min_l, bw_min_r)`

---

## 4. Three MSE-Optimal Branches

### 4.1 Branch: MSE-TWO (`msetwo`, `certwo`, `msecomb2`, `cercomb2`)

**Source:** `rdrobust.ado` L418–448

Different bandwidths for left and right sides.

**Step 1 — Pilot (L420–429):**
```
d_bw_l = (V_l / B_l^2 * (N/N_orig))^rate
d_bw_r = (V_r / B_r^2 * (N/N_orig))^rate
```

Apply bwrestrict and bwcheck per side.

**Step 2 — Bias bandwidth (L431–438):**
```
b_bw_l = (V_l / (B_l^2 + scaleregul*R_l) * (N/N_orig))^rate
b_bw_r = (V_r / (B_r^2 + scaleregul*R_r) * (N/N_orig))^rate
```

Note: `scaleregul` regularization term only enters in Steps 2 and 3.

**Step 3 — Main bandwidth (L440–448):**
```
h_bw_l = (V_l / (B_l^2 + scaleregul*R_l) * (N/N_orig))^rate
h_bw_r = (V_r / (B_r^2 + scaleregul*R_r) * (N/N_orig))^rate
```

### 4.2 Branch: MSE-SUM (`msesum`, `cersum`, `msecomb1`, `msecomb2`, `cercomb1`, `cercomb2`)

**Source:** `rdrobust.ado` L451–466

Same bandwidth for both sides, using sum criterion.

**Step 1 — Pilot (L453–455):**
```
d_bw_s = ((V_l + V_r) / (B_r + B_l)^2 * (N/N_orig))^rate
```

**Step 2 — Bias bandwidth (L457–460):**
```
b_bw_s = ((V_l + V_r) / ((B_r + B_l)^2 + scaleregul*(R_r + R_l)) * (N/N_orig))^rate
```

**Step 3 — Main bandwidth (L462–465):**
```
h_bw_s = ((V_l + V_r) / ((B_r + B_l)^2 + scaleregul*(R_r + R_l)) * (N/N_orig))^rate
```

Key difference from TWO: sums `V` components and `B` components before ratio, uses `(B_r + B_l)^2` in denominator (sum of bias, not difference).

### 4.3 Branch: MSE-RD (`mserd`, `cerrd`, `msecomb1`, `msecomb2`, `cercomb1`, `cercomb2`)

**Source:** `rdrobust.ado` L469–487

Same bandwidth for both sides, using difference criterion.

**Step 1 — Pilot (L471–474):**
```
d_bw_d = ((V_l + V_r) / (B_r - B_l)^2 * (N/N_orig))^rate
```

**Step 2 — Bias bandwidth (L476–479):**
```
b_bw_d = ((V_l + V_r) / ((B_r - B_l)^2 + scaleregul*(R_r + R_l)) * (N/N_orig))^rate
```

**Step 3 — Main bandwidth (L482–485):**
```
h_bw_d = ((V_l + V_r) / ((B_r - B_l)^2 + scaleregul*(R_r + R_l)) * (N/N_orig))^rate
```

Key difference from SUM: uses `(B_r - B_l)^2` in denominator — this is the "difference" criterion that directly targets the RD estimand.

---

## 5. CER Scaling

**Source:** `rdrobust.ado` L494–496, `rdbwselect.ado` L498–500

CER (Coverage Error Rate) optimal bandwidths shrink the MSE-optimal bandwidths by a factor to minimize coverage error rather than MSE:

```
cer_h = N^(-p / ((3+p) * (3+2p)))
```

With clustering (L495):
```
cer_h = (g_l + g_r)^(-p / ((3+p) * (3+2p)))
```

```
cer_b = 1  // bias bandwidth unchanged for CER
```

For the default case `p=1`: `cer_h = N^(-1/20)` ≈ 0.8 for N=1000.

**Application (L522–527):**
```
h_cer = h_mse * cer_h
b_cer = b_mse * cer_b = b_mse
```

---

## 6. Combination Selectors

**Source:** `rdrobust.ado` L512–521

### 6.1 `msecomb1` (L512–515)

Takes the **minimum** (more conservative) of mserd and msesum:

```
h_msecomb1 = min(h_mserd, h_msesum)
b_msecomb1 = min(b_mserd, b_msesum)
```

### 6.2 `msecomb2` (L516–521)

Takes the **median** of all three MSE selectors:

```
h_msecomb2_l = median(h_mserd, h_msesum, h_msetwo_l)  // sorted, take element [2]
h_msecomb2_r = median(h_mserd, h_msesum, h_msetwo_r)
```

This provides a robust compromise when the three selectors give divergent answers.

---

## 7. De-Standardization

**Source:** `rdrobust.ado` L535–543

When `stdvars="on"`, all variables are standardized before bandwidth computation. Results must be de-standardized:

```
c = c * x_sd
X_uniq = X_uniq * x_sd
X = X * x_sd
Y = Y * y_sd

h_mserd = x_sd * h_bw   // L499
b_mserd = x_sd * b_bw   // L500
```

---

## 8. Python Implementation Path

### 8.1 Current State

`_rdbwselect_mserd()` in `src/stataflow/estimators/rdrobust.py` implements only the MSE-RD branch with `mserd` only.

### 8.2 Required Refactoring

The current `_rdrobust_bw()` function (which wraps the three-step plug-in) must be extended to support three output modes:

```python
def _rdrobust_bw(Y, X, T, Z, C, fw, c, o, nu, o_B, h_V, h_B,
                 scaleregul, vce, nnmatch, kernel, dups, dupsid, covs_drop_coll):
    """Returns (V, B, R, rate). Currently hard-coded for d=0 (sharp RD).

    Extension needed for:
    - T != 0 (fuzzy RD): multi-column D matrix
    - Z != 0 (covariates): s-vector adjustment
    - C != 0 (cluster): cluster-robust VCE in V computation
    - fw != 0 (weights): weighted estimation
    """
```

### 8.3 New Top-Level Selector Function

```python
def _rdbwselect(data, bwselect, deriv=0, p=1, q=2, kernel="triangular",
                vce="nn", nnmatch=3, scaleregul=1.0, masspoints="adjust",
                bwcheck=0, bwrestrict=True, stdvars=False,
                fuzzy=None, covs=None, cluster=None, weights=None):
    """Unified bandwidth selector returning (h_l, h_r, b_l, b_r).

    Strategy:
    1. Compute pilot bandwidth c_bw (kernel constant, BWp, N scaling)
    2. Three branches compute d_bw, b_bw, h_bw for TWO/SUM/RD
    3. Select output based on bwselect value
    4. Apply CER scaling if cer* variant
    5. Apply comb logic if comb* variant
    6. De-standardize
    """
```

### 8.4 Implementation Order

| Priority | Selector | Branch Needed | Effort |
|----------|----------|---------------|--------|
| 1 | `msesum` | SUM (new branch) | Medium — add `(V_l+V_r)/(B_r+B_l)²` path |
| 2 | `msetwo` | TWO (already partially exists) | Low — the per-side formula is simpler |
| 3 | `msecomb1` | RD + SUM → min | Low — pure post-processing |
| 4 | `msecomb2` | RD + SUM + TWO → median | Low — pure post-processing |
| 5 | `cerrd` | RD × cer_h | Low — scaling factor only |
| 6 | `cersum` | SUM × cer_h | Low — scaling factor only |
| 7 | `certwo` | TWO × cer_h | Low — scaling factor only |
| 8 | `cercomb1` | comb1 × cer_h | Low — scaling factor only |
| 9 | `cercomb2` | comb2 × cer_h | Low — scaling factor only |

**Critical insight:** Once the three MSE branches (RD, SUM, TWO) are implemented, all 9 selectors follow mechanically from post-processing (CER scaling + comb logic). The CER scaling and comb logic are pure arithmetic on the already-computed `h_mse` and `b_mse` values.

### 8.5 Key Implementation Pitfalls

1. **`N/N_orig` ratio:** The `nN` variable in Stata is the original N before any restriction. When `stdvars="on"`, the sample size doesn't change, but in some configurations the effective sample may differ. Track `N_orig` vs `N_effective`.

2. **Signed B for RD criterion:** The `(B_r - B_l)^2` in the RD branch uses the signed difference of bias components. The sign of `B` is crucial — it comes from the `o_B` parameter in `rdrobust_bw()`.

3. **Regularization timing:** `scaleregul * R` is only added in Steps 2 and 3, never in Step 1.

4. **Mass points interaction:** When `masspoints="adjust"`, the initial pilot `c_bw` uses `M` (unique obs) instead of `N`, and `bwcheck` is set to 10.

5. **bwrestrict per side:** For TWO branch, bwrestrict is applied per-side. For SUM and RD branches, it's applied to the common bandwidth against `max(range_l, range_r)`.

6. **Cluster CER:** When clustered, `cer_h = (g_l+g_r)^(-p/((3+p)*(3+2p)))` instead of `N^(-p/((3+p)*(3+2p)))`. This is critical for correct `vce(cluster)` + CER selector interaction.

---

## 9. Stata Source Line Reference

| Selector | Main Logic | CER Scale | Comb Logic | Output Assignment |
|----------|-----------|-----------|------------|-------------------|
| `mserd` | L469–487 | — | — | L499–500 |
| `msetwo` | L418–448 | — | — | L507–510 |
| `msesum` | L451–466 | — | — | L503–504 |
| `msecomb1` | — | — | L512–515 | L513–514 |
| `msecomb2` | — | — | L516–521 | L517–520 |
| `cerrd` | L469–487 | L494, L522–527 | — | L523–527 |
| `certwo` | L418–448 | L494, L522–527 | — | L523–527 |
| `cersum` | L451–466 | L494, L522–527 | — | L523–527 |
| `cercomb1` | — | L494, L522–527 | L512–515 | L523–527 |
| `cercomb2` | — | L494, L522–527 | L516–521 | L523–527 |

---

## 10. Validation Strategy

### Synthetic Test Cases

| case_id | bwselect | Expected Behavior |
|---------|----------|-------------------|
| `w8_bw_mserd` | `mserd` | Already passing; regression baseline |
| `w8_bw_msesum` | `msesum` | `h_msesum ≈ h_mserd` for symmetric data; verify < 0.1% on senate |
| `w8_bw_msetwo` | `msetwo` | `h_l ≠ h_r` for asymmetric density; verify against Stata |
| `w8_bw_msecomb1` | `msecomb1` | `h_comb1 ≤ min(h_rd, h_sum)` by construction |
| `w8_bw_msecomb2` | `msecomb2` | `h_comb2 = median(h_rd, h_sum, h_two)` |
| `w8_bw_cerrd` | `cerrd` | `h_cerrd = h_mserd * N^(-1/20)`; verify formula |
| `w8_bw_cersum` | `cersum` | `h_cersum = h_msesum * N^(-1/20)` |
| `w8_bw_certwo` | `certwo` | `h_certwo = h_msetwo * N^(-1/20)` |
| `w8_bw_cercomb1` | `cercomb1` | CER-scaled comb1 |
| `w8_bw_cercomb2` | `cercomb2` | CER-scaled comb2 |
| `w8_bw_all` | `all` | `rdbwselect, all` returns all selectors simultaneously |

### Real-Data Validation

Use `rdrobust_senate.dta` — the standard benchmark dataset:
```
rdrobust vote margin, c(0) bwselect(<each>)
```

Target tolerance: bandwidth < 0.1%, estimates < 1e-4.

---

## 11. `rdbwselect` Companion Command

**Source:** `rdbwselect.ado`

The standalone `rdbwselect` command is essentially the bandwidth selection block extracted from `rdrobust.ado` without the estimation step. The Python equivalent would be:

```python
def rdbwselect(data, y, x, c=0.0, ...):
    """Standalone bandwidth selector. Returns h, b for chosen method."""
    # Same three-step plug-in as rdrobust bandwidth block
    # Returns dict with h, b, N_l, N_r, etc.
```

This can be implemented as a thin wrapper around `_rdbwselect()` once the full selector family is available.
