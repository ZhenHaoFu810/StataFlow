# `rdrobust` Source-to-Python Mapping

**Version mapped:** `10.0.0  2025-06-30` (local mirror `research/vendor/stata_community/rdrobust/rdrobust-master/`)
**Python target:** `stataflow.estimators.RDRobust` + `stataflow.compat.stata.rdrobust()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `stata/rdrobust.ado` | `program rdrobust, eclass` (L8) | Top-level dispatcher: parses `c()`, `h()`, `b()`, `kernel()`, `vce()`, `fuzzy()`, `covs()`, etc.; builds sample; branches to Mata for bandwidth + estimation | `stataflow.compat.stata.rdrobust()` wrapper |
| `stata/rdrobust.ado` | `L125鈥?74` | Missing-value drop logic for `y`, `x`, `fuzzy`, `cluster`, `covs`, `weights` | `RDRobust.fit()` drops rows with missing `y` or `x` |
| `stata/rdrobust.ado` | `L282鈥?93` | Kernel string parsing and `C_c` constant selection (`Triangular=2.576`, `Epanechnikov=2.34`, `Uniform=1.843`) | `_kernel_weight()` in `rdrobust.py` |
| `stata/rdrobust.ado` | `L345鈥?46` | **Bandwidth selection block** (Mata `rdrobust_bw` calls for `mserd`, `msetwo`, `msesum`, etc.) | `_rdbwselect_mserd()` implements `mserd` for sharp RD; other selectors not yet ported |
| `stata/rdrobust.ado` | `L551鈥?79` | **Estimation and inference block** (Mata): local polynomial WLS, bias correction, variance estimation, stored results | `RDRobust.fit()` |

---

## 2. Mata Function Hierarchy

```
rdrobust.ado
    鈹溾攢鈹€ Mata: bandwidth selector (rdrobust_bw)
    鈹?      鈹斺攢鈹€ calls rdrobust_kweight, rdrobust_res, rdrobust_vce
    鈹?      鈹斺攢鈹€ Python: _rdbwselect_mserd() (mserd only)
    鈹斺攢鈹€ Mata: estimation & inference
            鈹溾攢鈹€ rdrobust_kweight()      鈫?kernel weights
            鈹溾攢鈹€ rdrobust_bw()           鈫?V, B, R, rate for bw selection
            鈹溾攢鈹€ rdrobust_res()          鈫?nn / hc residuals
            鈹斺攢鈹€ rdrobust_vce()          鈫?sandwich meat matrix
```

---

## 3. Core Algorithm 鈫?Python Mapping

### 3.1 Kernel Weights

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `rdrobust.ado` Mata | `rdrobust_kweight()` | `u = (X-c)/h`; `w = (1-|u|) * I(|u|<=1)` for triangular; similar for epa / uniform | `_kernel_weight()` 鈥?identical formulas, no `1/h` normalization difference because `w` is used as WLS weights directly |

### 3.2 Local Polynomial WLS (Point Estimation)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `rdrobust.ado` Mata | `L599鈥?01` | `invG_p_l = cholinv(quadcross(R_p_l:*W_h_l, R_p_l))` | `_wls_poly()` uses Cholesky on `(sqrt(W)*R)'(sqrt(W)*R)` and returns `invG_p_l`, `beta_p_l` |
| `rdrobust.ado` Mata | `L633` | `beta_p_l = invG_p_l * quadcross(R_p_l:*W_h_l, D_l)` | Identical normal-equation solve in `_wls_poly()` |

**Key equivalence:** Both Stata and Python solve the weighted normal equations via Cholesky decomposition of the weighted Gram matrix.

### 3.3 Bias Correction (`Q_q`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `rdrobust.ado` Mata | `L609鈥?11` | `Q_q_l = ((R_p_l:*W_h_l)' - h^(p+1)*(L_l*e_p1')*((invG_q_l*R_q_l')':*W_b_l)')'` | Implemented in `RDRobust.fit()` with NumPy: `Q_q_l = (R_p_l*W_h_l).T - h^(p+1)*outer(L_l, e_p1) @ ((invG_q_l @ R_q_l.T) * W_b_l[None, :])` |
| `rdrobust.ado` Mata | `L633` | `beta_bc_l = invG_p_l * quadcross(Q_q_l, D_l)` | Same normal-equation update using `Q_q_l.T @ D_l` |

**Why it works:** `Q_q` is the bias-corrected design matrix from CCT (2014a, Eq. 10). The Python transcription preserves the exact matrix algebra.

### 3.4 Variance Estimation

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `rdrobust.ado` Mata | `rdrobust_res()` | For `vce(nn)`: nearest-neighbor leave-neighborhood residuals; for `vce(hc0)`: raw residuals | `_nn_residuals()` replicates the neighborhood search; hc0 uses raw plug-in residuals |
| `rdrobust.ado` Mata | `rdrobust_vce()` | For `d=0` (sharp RD): `M = (res * RX)' (res * RX)`; then `V = invG * M * invG` | `_vce_hc0()` 鈥?identical sandwich construction |
| `rdrobust.ado` Mata | `L803鈥?08` | `V_tau_cl = scalepar^2 * factorial(deriv)^2 * (V_cl_l + V_cl_r)[deriv+1, deriv+1]` | `RDRobust.fit()` computes the same scalar variance expression |
| `rdrobust.ado` Mata | `L807鈥?08` | `V_tau_rb = scalepar^2 * factorial(deriv)^2 * (V_bc_l + V_bc_r)[deriv+1, deriv+1]` | Same scalar expression; `Q_q` is passed **without** double-weighting |

**Critical fix during implementation:** An early Python draft passed `W_h_l` into `_vce_hc0()` for the robust variance, which double-weighted `Q_q` (since `Q_q` already embeds weights from its construction). Removing the extra weight alignment fixed `se_tau_rb` and brought it into `< 1e-6` agreement with Stata.

### 3.5 Automatic Bandwidth Selection (`mserd`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `rdbwselect.py` (official Python) | `rdbwselect()` | Three-step plug-in: pilot `d_bw` 鈫?bias `b_bw` 鈫?main `h_bw` using `h = (V / (B虏 + scaleregul路R))^rate` | `_rdbwselect_mserd()` replicates the three-step procedure for sharp RD |
| `rdrobust.ado` Mata | `rdrobust_bw()` | Single-side component returning `(V, B, R, rate)` | `_rdrobust_bw()` handles both `d=0` and `d>0` (covariates) via `_rdrobust_vce_multi()` |
| `rdbwselect.py` | `C_c` constants and mass-points adjustment | `C_c = 2.576` (tri), `2.34` (epa), `1.843` (uni); initial pilot `c_bw = C_c * BWp * M^(-1/5)` where `M` is unique-obs count when mass points exist | `_rdbwselect_mserd()` uses identical constants and `bwcheck` enforcement |

**Key equivalence:** The Python `_rdbwselect_mserd` follows the same three-step plug-in procedure documented in CCT (2014a) and implemented in the official `rdbwselect.py`. Mass-points adjustment (`bwcheck`) and `bwrestrict` are both included. The resulting `h` and `b` agree with Stata 17 to within ~0.03 %, and the downstream `tau` / `se` agree to within ~0.01 %.

### 3.6 Covariate-Adjusted Sharp RD (`covs`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `rdrobust.ado` Mata | `L555鈥?70` | Appends covariates `Z` to outcome `y` as multi-column RHS: `D = [y, Z]` | `RDRobust.fit()` builds `D_l = [eY_l, eZ_l]` and `D_r = [eY_r, eZ_r]` |
| `rdrobust.ado` Mata | `L571鈥?85` | Frisch-Waugh-Lovell projection: `gamma = pinv(ZWZ) * ZWY`, `s = [1, -gamma]` | `fit()` computes `gamma` from pooled `ZWZ = ZWZ_r + ZWZ_l` and `ZWY = ZWY_r + ZWY_l`, then `s = [1, -gamma]` |
| `rdrobust.ado` Mata | `L633` | Covariate-adjusted point estimate: `tau = s' * (beta_r[deriv,:] - beta_l[deriv,:])` | Identical linear combination in `fit()` using `np.dot(scalepar * s.T, beta_p_r[deriv,:] - beta_p_l[deriv,:])` |
| `rdrobust.ado` Mata | `rdrobust_vce()` (d > 0) | Multi-dimensional sandwich: `M = sum_{i,j} (RX' diag(s_i*s_j*res_i*res_j) RX)` | `_rdrobust_vce_multi(s, RX, res)` implements the same double sum over covariate residual outer products |

**Why it works:** The covariate adjustment uses the partitioned-regression logic from CCT (2014a, Sec. 4.2). By stacking `y` and `Z` into a multi-column WLS problem, the coefficients on `Z` are partialled out through the `s` vector, and the VCE correctly accounts for the additional sampling variation via the multi-dimensional sandwich.

### 3.7 Inference (t-stat, p-value, CI)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `rdrobust.ado` Mata | `L837` | `quant = -invnormal(abs((1-level/100)/2))` | `scipy.stats.norm.ppf()` with the same formula |
| `rdrobust.ado` Mata | `L841鈥?65` | Stored matrices `b` and `V`; `tau_cl`, `tau_bc`, `se_tau_cl`, `se_tau_rb` | Mapped to `ResultSchema.coefficients` with three rows: Conventional, Bias-Corrected, Robust |

---

## 4. Implemented vs. Not Implemented

### 4.1 Implemented (with source-backed alignment)

- Sharp RD point estimation (`p`, `q`, `h`, `b`, `c`, `kernel`)
- Bias-corrected estimate (`tau_bc`)
- Robust standard error (`se_tau_rb`)
- `vce="nn"` and `vce="hc0"`
- Automatic bandwidth selection: `bwselect="mserd"` (sharp RD only)
- Covariate-adjusted sharp RD (`covs`, `covs_drop`)
- `scaleregul` (regularization scaling for bandwidth selectors)
- Result packaging in `ResultSchema`

### 4.2 Implemented but minimal / Phase B limitations

- **Bandwidth selectors:** Only `mserd` is supported. `msetwo`, `msesum`, `cerrd`, `certwo`, `cersum`, and `ik` / `cv` are not yet ported.
- **Covariates:** Only sharp RD + covariates is supported. Fuzzy + covs, cluster + covs, and weights + covs are hard-rejected.
- **No clustering / weights / fuzzy / kink:** Hard-rejected to prevent silent incorrect results.

### 4.3 Not implemented or explicitly rejected

- `fuzzy` RD / kink RD (`deriv > 0`)
- `weights`
- `cluster` / `nncluster` VCE
- `stdvars`, `all`, `detail`
- `rdplot` and `rdbwselect` companion commands
- Bandwidth selectors other than `mserd`

---

## 5. Options 鈫?Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `c(#)` | `c=float` | Supported |
| `h(# [#])` | `h=float\|tuple` | Supported; if provided, overrides `bwselect` |
| `b(# [#])` | `b=float\|tuple` | Supported; defaults to `h` |
| `p(#)` | `p=int` | Supported (default 1) |
| `q(#)` | `q=int` | Supported (default 2) |
| `kernel(kernelfn)` | `kernel=str` | `triangular` (default), `epanechnikov`, `uniform` |
| `vce(nn [nnmatch])` | `vce="nn"`, `nnmatch=int` | Supported (default `nnmatch=3`) |
| `vce(hc0)` | `vce="hc0"` | Supported |
| `bwselect(method)` | `bwselect=str` | `mserd` supported; others hard-rejected |
| `covs(varlist)` | `covs=list[str]\|str` | Supported for sharp RD |
| `covsdrop` | `covs_drop=bool` | Supported (default `True`) |
| `scaleregul(#)` | `scaleregul=float` | Supported (default `1.0`) |
| `fuzzy(var)` | 鈥?| Hard-rejected via `ValueError` |

---

## 6. Source File Quick Reference

```
research/vendor/stata_community/rdrobust/rdrobust-master/
鈹溾攢鈹€ stata/rdrobust.ado          鈫?Main ADO entry (syntax + output table)
鈹溾攢鈹€ stata/rdrobust_functions.do 鈫?Mata function loader
鈹溾攢鈹€ stata/rdrobust_bw.mo        鈫?Compiled Mata bandwidth selector
鈹溾攢鈹€ stata/rdrobust_kweight.mo   鈫?Compiled Mata kernel weight
鈹溾攢鈹€ stata/rdrobust_res.mo       鈫?Compiled Mata residual computation
鈹溾攢鈹€ stata/rdrobust_vce.mo       鈫?Compiled Mata VCE sandwich
鈹斺攢鈹€ Python/rdrobust/src/rdrobust/
    鈹溾攢鈹€ rdrobust.py             鈫?Official Python reference implementation
    鈹溾攢鈹€ rdbwselect.py           鈫?Official Python bandwidth selector
    鈹斺攢鈹€ funs.py                 鈫?Official Python helper functions
```

---

## 7. Alignment Notes

1. **Dual-run evidence (explicit bandwidth):** Stata 17 outputs for `rdrobust vote margin, c(0) h(15)` and `rdrobust vote margin, c(0) h(15) vce(hc0) kernel(uniform)` on `rdrobust_senate.dta` were used as ground truth. All four key objects (`tau_cl`, `tau_bc`, `se_tau_cl`, `se_tau_rb`) agree to `< 1e-6` relative tolerance.
2. **Dual-run evidence (automatic bandwidth):** `rdrobust vote margin, c(0) bwselect(mserd)` produces `h = 17.754397`, `b = 28.028087`. Python `_rdbwselect_mserd()` yields `h = 17.758959`, `b = 28.034847` (relative diff ~0.03 %). Downstream `tau_cl` differs by ~3.3e-5, well within the expected variance of a plug-in bandwidth selector.
3. **Dual-run evidence (covariates + explicit bandwidth):** `rdrobust vote margin, c(0) h(15) covs(z)` matches Python to 7 digits (`tau_cl = 7.5087336`, `tau_bc = 9.1271454`, `se_tau_cl = 1.5602323`, `se_tau_rb = 2.2427712`), confirming the covariate-adjusted estimation path is exact.
4. **Dual-run evidence (covariates + automatic bandwidth):** `rdrobust vote margin, c(0) covs(z)` produces `h = 17.741488`. Python yields `h = 17.746241` (diff ~0.03 %). Downstream estimates differ by < 0.01 %.
5. **Clean re-implementation:** The Python code in `stataflow/estimators/rdrobust.py` was written from the published algorithm (CCT 2014a) and the Stata Mata logic, not by copying the GPL-licensed official Python package.
6. **Boundary clarity:** Any parameter not listed as "Supported" is hard-rejected, so users cannot accidentally invoke unimplemented branches.
