# RD Robust Fuzzy Design — Research Archive

**Version researched:** `rdrobust` v10.0.0 (2025-06-30)
**Stata source:** `rdrobust.ado` L106–123 (syntax), L313–323 (Mata setup), L614–619, L655–756 (estimation)
**Reference:** CCT (2014a, _Econometrica_), CCT (2016a, _Journal of Causal Inference_)
**Python target:** `stataflow.estimators.rdrobust.RDRobust.fit()` — fuzzy branch

---

## 1. Syntax and Parameter Parsing

**Source:** `rdrobust.ado` L106–123

```
fuzzy(varname [sharpbw])
```

- `varname`: treatment status variable (binary 0/1)
- `sharpbw` (optional): if specified, uses sharp RD bandwidth selection even though estimation is fuzzy

### 1.1 Perfect Compliance Detection

**Source:** L315–318

```mata
if (variance(T_l)==0 | variance(T_r)==0){
    T_l = T_r = 0
    st_local("perf_comp","perf_comp")
}
```

If treatment has zero variance on either side of the cutoff (all 0 or all 1), the implementation sets `T_l = T_r = 0`, which effectively forces sharp RD bandwidths. The `perf_comp` local flag triggers a warning: "bandwidths automatically computed for sharp RD estimation because perfect compliance was detected."

### 1.2 `sharpbw` Option

**Source:** L319–322

```mata
if ("`sharpbw'"!=""){
    T_l = T_r = 0
    st_local("sharpbw","sharpbw")
}
```

When `sharpbw` is specified, sets `T=0` during bandwidth selection (so sharp RD bandwidths are used), but restores `T` during estimation.

---

## 2. Data Structure in Fuzzy Mode

### 2.1 Design Matrix Extension

**Source:** L614–619

When `fuzzy` is specified:
```mata
T    = st_data(.,("`fuzzyvar'"), 0); dT = 1
T_l  = select(T, X:<c');  eT_l  = T_l[ind_l]
T_r  = select(T, X:>=c'); eT_r  = T_r[ind_r]
D_l  = D_l, eT_l; D_r = D_r, eT_r
```

The design matrix `D` is extended from `[y]` to `[y, T]` (and to `[y, T, Z]` with covariates). This means `beta_p_l` and `beta_p_r` now have **2 columns** (y and T) instead of 1.

### 2.2 Beta Matrix Structure

With fuzzy RD, `beta_p` (difference across cutoff) is a `(p+1) × 2` matrix:
- Column 1: `beta_p[:, 0]` = Y outcome coefficients
- Column 2: `beta_p[:, 1]` = T treatment coefficients

---

## 3. Wald Ratio Estimator (No Covariates)

**Source:** L655–678

### 3.1 First-Stage and Reduced-Form Estimates

```mata
// Reduced form (Y)
tau_Y_cl = scalepar * factorial(deriv) * beta_p[deriv+1, 1]
tau_Y_bc = scalepar * factorial(deriv) * beta_bc[deriv+1, 1]

// First stage (T)
tau_T_cl = factorial(deriv) * beta_p[deriv+1, 2]
tau_T_bc = factorial(deriv) * beta_bc[deriv+1, 2]
```

Note: no `scalepar` factor on T estimates.

### 3.2 Wald Estimator (L663–666)

```mata
s_Y = (1/tau_T_cl \ -(tau_Y_cl/tau_T_cl^2))
B_F = tau_Y_cl - tau_Y_bc \ tau_T_cl - tau_T_bc
tau_cl = tau_Y_cl / tau_T_cl
tau_bc = tau_cl - s_Y' * B_F
```

The fuzzy RD treatment effect is:
- **Conventional:** `tau_cl = tau_Y_cl / tau_T_cl` (ratio of reduced form to first stage)
- **Bias-corrected:** `tau_bc = tau_cl - s_Y' * B_F` where `B_F` is the bias vector `[bias_Y, bias_T]`

### 3.3 s-Vector (Delta Method Gradient)

The `s_Y` vector is the gradient of the Wald estimator `g(τ_Y, τ_T) = τ_Y / τ_T`:

```
∂g/∂τ_Y = 1/τ_T
∂g/∂τ_T = -τ_Y/τ_T²

s_Y = [1/τ_T_cl, -τ_Y_cl/τ_T_cl²]
```

This is used for:
1. **Bias correction:** `s_Y' * B_F` (delta method applied to bias)
2. **Variance:** The VCE computes variance of `s_Y' * [β_Y, β_T]'`

### 3.4 Side-Specific Bias

```mata
B_F_l = tau_Y_cl_l - tau_Y_bc_l \ tau_T_cl_l - tau_T_bc_l
B_F_r = tau_Y_cl_r - tau_Y_bc_r \ tau_T_cl_r - tau_T_bc_r
bias_l = s_Y' * B_F_l
bias_r = s_Y' * B_F_r
```

---

## 4. Fuzzy RD with Covariates

**Source:** L717–755

### 4.1 Extended s-Vectors

When `covs` are present, the FWL projection produces two gamma vectors:

```mata
s_Y = (1 \ -gamma_p[,1])     // for Y outcome
s_T = (1 \ -gamma_p[,2])     // for T treatment
```

These partial out covariates from Y and T respectively.

### 4.2 Covariate-Adjusted Estimates (L719–740)

```mata
// Reduced form
tau_Y_cl = scalepar * factorial(deriv) * s_Y' * beta_p[deriv+1, [1, colsZ]]
tau_Y_bc = scalepar * factorial(deriv) * s_Y' * beta_bc[deriv+1, [1, colsZ]]

// First stage
tau_T_cl = factorial(deriv) * s_T' * beta_p[deriv+1, [2, colsZ]]
tau_T_bc = factorial(deriv) * s_T' * beta_bc[deriv+1, [2, colsZ]]
```

### 4.3 Full s-Vector for VCE (L754)

```mata
s_Y = (1/tau_T_cl \                        // derivative w.r.t. τ_Y
      -(tau_Y_cl/tau_T_cl^2) \             // derivative w.r.t. τ_T
      -(1/tau_T_cl)*gamma_p[,1] +          // derivative w.r.t. γ_Y (covariates)
      (tau_Y_cl/tau_T_cl^2)*gamma_p[,2])   // derivative w.r.t. γ_T (covariates)
```

This is the combined gradient of the fuzzy RD Wald estimator with respect to all parameters: `[β_Y, β_T, β_Z]`. The length is `1 + dT + dZ`.

---

## 5. VCE for Fuzzy RD

**Source:** L803–819

### 5.1 Multi-Column Sandwich

```mata
V_Y_cl_l = invG_p_l * rdrobust_vce(dT+dZ, s_Y, R_p_l:*W_h_l, res_h_l, ...) * invG_p_l
```

`rdrobust_vce()` is called with dimension `dT+dZ` (1+dT+dZ columns total). When `dT=1` (fuzzy) and `dZ=0` (no covariates): `dim = 1`.

The `s_Y` vector selects the linear combination. The sandwich is:

```
V = invG_p * [Σ_i s_i * RX_i' * res_i * res_i' * RX_i * s_i'] * invG_p
```

### 5.2 First-Stage VCE (L811–816)

```mata
V_T_cl_l = invG_p_l * rdrobust_vce(dT+dZ, sV_T, R_p_l:*W_h_l, res_h_l, ...) * invG_p_l
V_T_cl = factorial(deriv)^2 * (V_T_cl_l + V_T_cl_r)[deriv+1, deriv+1]
```

Where `sV_T = (0 \ 1 \ -gamma_p[,2])` for covariate case, or `sV_T = (0, 1)` without covariates.

---

## 6. Output and Stored Results

**Source:** L869–878

When fuzzy:
```mata
st_numscalar("tau_T_cl", tau_T_cl)
st_numscalar("se_tau_T_cl", se_tau_T_cl)
st_numscalar("tau_T_bc", tau_T_bc)
st_numscalar("se_tau_T_rb", se_tau_T_rb)
st_matrix("beta_T_p_r", beta_T_p_r)
st_matrix("beta_T_p_l", beta_T_p_l)
```

The Stata output table shows first-stage estimates before treatment effect estimates.

---

## 7. Python Implementation Path

### 7.1 Required Changes

1. **RDRobust.fit() — parameter:**
   ```python
   def fit(self, fuzzy: str | None = None, sharpbw: bool = False, ...):
   ```

2. **Sample screening** — drop rows where `fuzzy` is missing (L127)

3. **D matrix extension** — when fuzzy:
   ```python
   D_l = np.column_stack([eY_l, eT_l])
   D_r = np.column_stack([eY_r, eT_r])
   if covs is not None:
       D_l = np.column_stack([D_l, eZ_l])
       D_r = np.column_stack([D_r, eZ_r])
   ```

4. **Perfect compliance detection:**
   ```python
   if np.var(eT_l) == 0 or np.var(eT_r) == 0:
       perf_comp = True  # triggers sharpbw behavior
   ```

5. **Wald estimator implementation:**
   ```python
   tau_Y_cl = scalepar * factorial(deriv) * beta_p[deriv, 0]
   tau_T_cl = factorial(deriv) * beta_p[deriv, 1]
   tau_cl = tau_Y_cl / tau_T_cl
   # Bias correction
   s_Y = np.array([1.0/tau_T_cl, -tau_Y_cl/tau_T_cl**2])
   B_F = np.array([tau_Y_cl - tau_Y_bc, tau_T_cl - tau_T_bc])
   tau_bc = tau_cl - s_Y @ B_F
   ```

6. **s-vector for VCE:**
   ```python
   # Without covariates: s = [1/tau_T, -tau_Y/tau_T²]
   # With covariates: s = [1/tau_T, -tau_Y/tau_T², -(1/tau_T)*gamma[:,0] + (tau_Y/tau_T²)*gamma[:,1]]
   ```

7. **VCE dimension:** `rdrobust_vce(dim=dT+dZ, s=s_Y, ...)` where `dT=1` for fuzzy.

8. **sharpbw bandwidth:** When `sharpbw=True` or `perf_comp=True`, set `T_l=T_r=0` during `_rdbwselect()` call only.

### 7.2 Implementation Complexity

- **Core Wald estimator:** LOW — simple ratio + delta method bias correction
- **FWL with covariates:** MEDIUM — extends existing covariate adjustment to two outcomes (Y, T)
- **s-vector construction:** MEDIUM — careful chain rule for delta method
- **VCE with multi-column s:** MEDIUM — existing `_rdrobust_vce_multi` already handles `s` vector
- **sharpbw + perf_comp:** LOW — conditional branching only

### 7.3 Key Edge Cases

1. **τ_T near zero:** When first stage is weak (τ_T ≈ 0), Wald estimator becomes unstable. Stata does not special-case this. Python should match Stata's numerical behavior.

2. **Perfect compliance on one side:** `variance(T_l)==0` or `variance(T_r)==0` triggers automatic sharpbw. This is common in real applications (e.g., all units below cutoff are untreated).

3. **Multi-dimensional s-vector with covariates:** The s-vector for the VCE must include partial derivatives with respect to covariate coefficients. The formula at L754 is the key reference.

---

## 8. Stata Source Line Reference

| Feature | Lines | Description |
|---------|-------|-------------|
| Syntax parsing | L106–123 | `fuzzy(varname [sharpbw])` |
| Data loading | L313–323 | T vector + perfect compliance detection |
| Perfect compliance | L315–318 | `variance(T_l)==0 \| variance(T_r)==0` |
| sharpbw | L319–322 | Sets T=0 for bandwidth selection |
| D matrix extension | L614–619 | `D_l = [eY_l, eT_l, eZ_l]` |
| Wald estimator (no covs) | L655–678 | `tau_cl = tau_Y_cl/tau_T_cl` |
| Wald estimator (with covs) | L717–755 | Extended s-vector with gamma_p |
| Bias correction | L663–666, L743–752 | Delta method bias correction |
| VCE for fuzzy | L803–819 | Multi-column sandwich with s_Y |
| Output | L869–878 | First-stage stored results |

---

## 9. Validation Strategy

### Synthetic Test Cases

| case_id | Description | Risk Focus |
|---------|-------------|------------|
| `w8_fuzzy_basic` | Sharp design (perfect compliance) as fuzzy | Wald = Sharp equivalence |
| `w8_fuzzy_partial` | Fuzzy with imperfect compliance both sides | τ_T < 1, correct Wald ratio |
| `w8_fuzzy_sharpbw` | Fuzzy with `sharpbw` option | Bandwidths match sharp RD |
| `w8_fuzzy_perfcomp` | One-sided perfect compliance | Automatic sharpbw trigger |
| `w8_fuzzy_covs` | Fuzzy + covariates | Extended s-vector VCE |
| `w8_fuzzy_real` | Real fuzzy RD dataset | Field-level alignment |

### Real-Data Validation

Standard fuzzy RD datasets (e.g., Medicaid expansion, Medicare Part D, or Head Start) — need to identify an accessible public dataset.
