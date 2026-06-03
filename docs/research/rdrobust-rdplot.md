# RD Plot (rdplot) Companion Command — Research Archive

**Version researched:** `rdrobust` v10.0.0 (2025-06-30)
**Stata source:** `rdplot.ado` (861 lines)
**Reference:** Calonico, Cattaneo, Titiunik (2015, _J. American Statistical Association_)
**Python target:** `stataflow.compat.stata.rdplot()` — NEW companion command

---

## 1. Syntax and Parameters

**Source:** `rdplot.ado` L9

```
rdplot y x [, c(#) p(#) nbins(# #) binselect(method) scale(# #)
            kernel(kernel) weights(var) h(# #) support(# #)
            masspoints(method) covs(varlist) covs_eval(method)
            covs_drop(method) hide ci(#) shade graph_options(...)
            genvars nochecks]
```

---

## 2. Core Algorithm

### 2.1 Data-Driven Optimal Binning

**Source:** Mata block L342–553

The `rdplot` command computes data-driven optimal bin counts using IMSE (Integrated Mean Squared Error) criteria, then constructs binned scatter points and overlays a local polynomial fit.

#### Step 1: Global Polynomial Fit (order k=4)

```mata
k = 4  // fixed global polynomial order for bin selection
rk_l = [1, x, x^2, x^3, x^4]  // polynomial basis
invG_k_l = cholinv(cross(rk_l, rk_l))  // OLS: (X'X)^(-1)
gamma_k1_l = invG_k_l * cross(rk_l, y_l)     // μ(x)
gamma_k2_l = invG_k_l * cross(rk_l, y_l:^2)  // μ(x²) for variance
```

If `k=4` fails (singular design), falls back to `k=3`, then `k=2` (L356–378).

#### Step 2: Bias and Variance Estimators

Two families of bin selectors:

**ES (Evenly Spaced, using spacings estimators):**
```mata
B_es_hat_dw = ((c-x_min)^2/(12*n)) * sum(mu1_hat_l^2)  // integrated squared bias
V_es_hat_dw = (0.5/(c-x_min)) * sum(dxi_l * dyi_l^2)    // integrated variance
J_es_hat_dw = ceil(((2*B/V) * n)^(1/3))                  // IMSE-optimal bins
```

**QS (Quantile Spaced):**
```mata
B_qs_hat_dw = (n_l^2/(24*n)) * sum(dxi_l^2 * mu1_i_hat_l^2)
V_qs_hat_dw = (1/(2*n_l)) * sum(dyi_l^2)
J_qs_hat_dw = ceil(((2*B/V) * n)^(1/3))
```

#### Step 3: Mimicking Variance (MV) Variants

Each ES and QS method has an MV variant that uses a different variance estimator:
```mata
J_es_hat_mv = ceil((var_y/V_es_hat_dw) * (n/log(n)^2))
J_qs_hat_mv = ceil((var_y/V_qs_hat_dw) * (n/log(n)^2))
```

#### Step 4: Polynomial Regression (PR) Variants

Each method has a PR variant that uses `sigma2_hat` (fitted variance from global polynomial) instead of spacings-based variance:
```mata
V_es_chk_dw = (1/(c-x_min)) * sum(dxi_l * sigma2_hat_l_bar)
V_qs_chk_dw = (1/n_l) * sum(sigma2_hat_l)
```

### 2.2 Complete Bin Selection Methods

**Source:** L475–513

| binselect | Spacing | Variance Estimator | Bin Type |
|-----------|---------|-------------------|----------|
| `es` | Spacings | Spacings | Evenly spaced |
| `esmv` (default) | Spacings | Mimicking variance | Evenly spaced |
| `espr` | Polynomial regression | Spacings | Evenly spaced |
| `esmvpr` | Polynomial regression | Mimicking variance | Evenly spaced |
| `qs` | Spacings | Spacings | Quantile spaced |
| `qsmv` | Spacings | Mimicking variance | Quantile spaced |
| `qspr` | Polynomial regression | Spacings | Quantile spaced |
| `qsmvpr` | Polynomial regression | Mimicking variance | Quantile spaced |

### 2.3 Bin Construction

**Evenly spaced bins (L571–575):**
```mata
binsL = rangen(x_min - 1e-8, c,     J_star_l + 1)
binsR = rangen(c,           x_max + 1e-8, J_star_r + 1)
```

**Quantile spaced bins (L562–563, L577–581):**
```stata
pctile binsL = `x' if `x'<`c',  nq(`J_star_l')
pctile binsR = `x' if `x'>=`c', nq(`J_star_r')
```

### 2.4 Bin Collapse

**Source:** L604–626

```mata
rdbin_collapse_l = rdrobust_collapse(d_l, bin_x_l)
// Returns: [count, mean_x, mean_y, variance_y] per bin
```

---

## 3. Local Polynomial Fit Overlay

**Source:** L255–339

### 3.1 WLS Fit

```mata
rp_l = [1, (x-c), (x-c)^2, ..., (x-c)^p]  // order p polynomial
wh_l = rdrobust_kweight(x_l, c, h_l+1e-8, kernel)
invG_p_l = cholinv(cross(rp_l, wh_l, rp_l))
gamma_p1_l = invG_p_l * cross(rp_l, wh_l, y_l)
```

### 3.2 Plot Points

```mata
nplot = 500  // fixed number of evaluation points
x_plot_l = rangen(c - h_l, c,     nplot)
x_plot_r = rangen(c,       c + h_r, nplot)
y_plot_l = rplot_l * gamma_p1_l
y_plot_r = rplot_r * gamma_p1_r
```

---

## 4. Covariate Adjustment in rdplot

**Source:** L284–316, L592–598

When `covs(varlist)` is provided, the polynomial fit uses FWL-partialled outcomes:
```mata
s_Y = (1 \ -gamma_p)  // partial out covariate effects
gamma_p1_l = (s_Y' * beta_p_l')'  // covariate-adjusted polynomial coefs
```

When `covs_eval="mean"`, the predicted values are shifted by `mean(Z) * gamma_p`.

---

## 5. Mass Points in rdplot

**Source:** L228–249

When mass points are detected and `masspoints="adjust"`, the `binselect` method is upgraded to its PR (polynomial regression) variant:
```stata
if ("`binselect'"=="es")    local binselect "espr"
if ("`binselect'"=="esmv")  local binselect "esmvpr"
if ("`binselect'"=="qs")    local binselect "qspr"
if ("`binselect'"=="qsmv")  local binselect "qsmvpr"
```

---

## 6. Python Implementation Path (Minimal Viable)

### 6.1 Scope for Minimal Version

For a minimal viable `rdplot`, implement:

1. **IMSE-optimal binning with `esmv` (default):**
   - Global quartic (k=4) polynomial fit
   - Spacings-based bias estimator
   - Mimicking variance estimator
   - Evenly spaced bins

2. **Binned means:**
   - Collapse observations into bins
   - Compute mean X, mean Y, and SE(Y) per bin

3. **Local polynomial fit line:**
   - WLS with kernel weights using user-specified or default bandwidth
   - 500 evaluation points for smooth curve

4. **Return data, NOT render graph:**
   - Return bin midpoints, bin means, bin SEs, and polynomial fit coordinates
   - Let the user choose their own plotting library (matplotlib, plotly, etc.)

### 6.2 API Design

```python
def rdplot(data, y, x, c=0.0, p=4, nbins=None, binselect="esmv",
           scale=1.0, kernel="uniform", weights=None, h=None,
           masspoints="adjust", covs=None, covs_eval="mean"):
    """
    Returns
    -------
    dict with keys:
        bins: DataFrame with columns [id, N, min_bin, max_bin, mean_bin, mean_x, mean_y, se_y, ci_l, ci_r]
        fit: DataFrame with columns [x_plot, y_plot] for left and right sides
        info: dict with [N_l, N_r, J_star_l, J_star_r, bin_avg_l, bin_avg_r, bin_med_l, bin_med_r]
    """
```

### 6.3 Implementation Steps

1. **Global polynomial fit (k=4→3→2 fallback):** Port the bias/variance estimation logic
2. **IMSE-optimal bin count:** `J_star = ceil(((2B/V) * n)^(1/3))`
3. **Evenly spaced bins:** `rangen(min, max, J+1)`
4. **Bin collapse:** Group observations by bin, compute means
5. **Local polynomial fit:** Reuse existing `_wls_poly()` from `rdrobust.py`
6. **No graph rendering:** Return data only; plotting is the user's responsibility

### 6.4 Key Simplifications vs Stata

- **No `hide` / `graph_options`:** No graph rendering in Python
- **No `genvars`:** No variable generation
- **No `shade` / `ci`:** CI bands returned as data, not rendered
- **`binselect="esmv"` only (Phase A):** Other methods deferred

---

## 7. Stata Source Line Reference

| Feature | Lines | Description |
|---------|-------|-------------|
| Syntax | L9 | Full parameter list |
| Missing drop | L81–95 | y, x, covs, weights |
| Global poly fit | L342–378 | Order k=4 with fallback |
| Bias/Variance ES | L458–462 | Spacings-based estimators |
| Bias/Variance QS | L464–468 | Quantile-based estimators |
| MV variants | L470–473 | Mimicking variance |
| Bin selection dispatch | L475–513 | 8 methods mapped to J_star |
| Bin construction (ES) | L571–575 | Evenly spaced bins |
| Bin construction (QS) | L577–581 | Quantile spaced bins |
| Bin collapse | L604–626 | Mean X, mean Y, SE per bin |
| Polynomial fit | L255–339 | WLS with kernel weights |
| Covariate FWL | L284–316 | Partial-out covariates |
| Mass points upgrade | L242–246 | binselect → PR variant |
| Output table | L766–793 | Summary statistics |
| Graph rendering | L799–824 | twoway scatter + line |

---

## 8. Validation Strategy

| case_id | Description | Risk Focus |
|---------|-------------|------------|
| `w8_rdplot_basic` | Default rdplot on senate data | Bin counts match Stata |
| `w8_rdplot_nbins` | Manual nbins(10, 15) | Manual override works |
| `w8_rdplot_esmv` | Explicit binselect(esmv) | Same as default |
| `w8_rdplot_qs` | binselect(qs) | Different bin counts |
| `w8_rdplot_poly` | Different p values | Polynomial fit changes |
| `w8_rdplot_covs` | With covariates | FWL-adjusted fit |
| `w8_rdplot_mp` | Mass points data | binselect upgrade to PR |

### Validation Approach

Since `rdplot` produces graphical output (not stored scalars/matrices), dual-run validation requires:
1. Run `rdplot` in Stata with `genvars` to extract bin-level data
2. Compare bin counts, bin midpoints, bin means, and polynomial fit values
3. Tolerance: bin counts must match exactly; bin means to < 1e-6
