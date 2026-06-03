# RD Robust Frequency Weights — Research Archive

**Version researched:** `rdrobust` v10.0.0 (2025-06-30)
**Stata source:** `rdrobust.ado` L138–141 (missing drop), L333–336 (Mata setup), L560–563 (weight application)
**Reference:** CCT (2014a)
**Python target:** `stataflow.estimators.rdrobust.RDRobust.fit()`

---

## 1. Syntax and Parameter

**Source:** `rdrobust.ado` L9

```
weights(varname)
```

A single variable name specifying frequency weights (analytical weights in Stata's RD context).

---

## 2. Missing Value Handling

**Source:** L138–141

```stata
if ("`weights'"~="") {
    qui drop if mi(`weights')
    qui drop if `weights'<=0
}
```

Observations with missing or non-positive weights are dropped from the estimation sample.

---

## 3. Weight Propagation in Mata

**Source:** L333–336

```mata
if ("`weights'"~="") {
    fw = st_data(.,("`weights'"), 0)
    fw_l = fw[ind_l]; fw_r = fw[ind_r]
}
```

Weights are loaded as a vector and split into left/right sides of the cutoff.

---

## 4. Multiplication with Kernel Weights

**Source:** L560–563

```mata
if ("`weights'"~="") {
    w_h_l = fw_l:*w_h_l;  w_h_r = fw_r:*w_h_r
    w_b_l = fw_l:*w_b_l;  w_b_r = fw_r:*w_b_r
}
```

Frequency weights are applied as **multiplicative factors** on top of kernel weights. The effective weight for observation `i` is:

```
w_effective_i = fw_i * K((X_i - c) / h)
```

This means:
- Zero-weight observations effectively drop out (their kernel weight is multiplied by 0)
- The weights affect both the main bandwidth (`h`) estimation weights AND the bias bandwidth (`b`) estimation weights
- The weights are NOT normalized (they are used as-is in WLS)

---

## 5. Propagation Through the Full Pipeline

### 5.1 Bandwidth Selection

The `rdrobust_bw()` function receives `fw_l, fw_r` as parameters (L413–414):

```mata
C_d_l = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, ...)
C_d_r = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, ...)
```

Weights are passed through all three steps (d_bw, b_bw, h_bw). The `rdrobust_bw()` function internally incorporates weights in the local polynomial WLS estimation used to compute `V`, `B`, `R`.

### 5.2 Point Estimation

The WLS normal equations become:

```
beta = inv(X'WX) * X'W y
```

where `W = diag(fw_i * K((X_i-c)/h))`.

### 5.3 VCE

Weights enter the sandwich estimator through the weighted residuals:
- For HC0: `res_i = y_i - X_i'beta` (where beta itself is weighted)
- For NN: leave-neighborhood-out residuals, but with weighted neighbor averaging

### 5.4 Effective Sample Size

With frequency weights:
```
N_eff_l = sum(fw_l)  // weighted count, not raw count
N_eff_r = sum(fw_r)
```

However, Stata `rdrobust` reports the raw observation count `N_l`, `N_r` in its output table, not the effective weighted count. The `N` used in bandwidth formulas (`mN`) is also the raw count.

---

## 6. Interaction with Other Features

### 6.1 Weights + Fuzzy RD

Weights multiply kernel weights for both Y and T equations. The Wald estimator uses weighted first-stage and reduced-form estimates.

### 6.2 Weights + Covariates

Weights are applied to the multi-column WLS problem `[y, Z]`. The FWL projection (gamma computation) uses weighted cross-products.

### 6.3 Weights + Cluster

Weights multiply kernel weights; cluster aggregation is done on the weighted scores:
```mata
score_g = Σ_{i in g} fw_i * K_i * RX_i' * res_i
```

### 6.4 Weights + Bandwidth Selection

Weights affect the `V`, `B`, `R` components returned by `rdrobust_bw()`, so bandwidth selection automatically accounts for weights.

---

## 7. Normalization

Stata `rdrobust` does NOT normalize frequency weights. This differs from Stata's `[fweight=...]` convention where weights are typically normalized. The weights are used as raw multiplicative factors.

For `aweight`-style normalization (where `sum(w) = N`), the user must pre-normalize the weight variable. This is consistent with the CCT (2014a) framework where weights are treated as known precision factors.

---

## 8. Python Implementation Path

### 8.1 Required Changes

1. **`RDRobust.fit()` parameter:**
   ```python
   def fit(self, weights: str | None = None, ...):
   ```

2. **Sample screening:**
   ```python
   if weights is not None:
       mask = mask & ~data[weights].isna() & (data[weights] > 0)
   ```

3. **Weight extraction:**
   ```python
   fw = data[weights].values if weights else None
   fw_l = fw[X < c] if fw is not None else None
   fw_r = fw[X >= c] if fw is not None else None
   # After bandwidth restriction:
   efw_l = fw_l[ind_l] if fw is not None else None
   efw_r = fw_r[ind_r] if fw is not None else None
   ```

4. **Kernel weight multiplication:**
   ```python
   if fw is not None:
       W_h_l = efw_l * w_h_l
       W_h_r = efw_r * w_h_r
       W_b_l = efw_l * w_b_l
       W_b_r = efw_r * w_b_r
   ```

5. **Bandwidth selection passthrough:** Pass `fw_l, fw_r` to `_rdrobust_bw()`.

### 8.2 Implementation Complexity

**LOW** — weights are purely multiplicative factors applied to kernel weights. The main work is threading the `weights` parameter through all internal functions.

---

## 9. Stata Source Line Reference

| Feature | Lines | Description |
|---------|-------|-------------|
| Missing weight drop | L138–141 | `drop if mi(weights) | weights<=0` |
| Mata weight load | L333–336 | `fw = st_data(.,("`weights'"), 0)` |
| Weight × kernel | L560–563 | `w_h_l = fw_l:*w_h_l` |
| BW function passthrough | L413–414 | `rdrobust_bw(..., fw_l, ...)` |

---

## 10. Validation Strategy

| case_id | Description | Risk Focus |
|---------|-------------|------------|
| `w8_weights_basic` | Sharp RD + uniform weights | Equivalence to unweighted |
| `w8_weights_double` | Integer weights = 2 | Coefficient invariance, SE shrinks by √2 |
| `w8_weights_zero` | Some zero-weight obs | Dropped from effective sample |
| `w8_weights_bwselect` | Weights + mserd | Bandwidth correctly incorporates weights |
| `w8_weights_covs` | Weights + covariates | FWL projection weighted |
