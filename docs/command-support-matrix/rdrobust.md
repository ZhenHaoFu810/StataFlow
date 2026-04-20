# Support Matrix: `rdrobust`

## Command Target

Local polynomial Regression Discontinuity estimation with robust bias-corrected inference, aligned with the Stata community command `rdrobust` (Calonico, Cattaneo, and Titiunik 2014a; Calonico, Cattaneo, and Farrell 2018).

## Completeness Status

**Partial / Phase B Subset** — sharp RD is usable with automatic bandwidth selection (`bwselect="mserd"`) and covariate adjustment (`covs`). Fuzzy RD, kink designs, clustering, weights, and the full selector family remain unsupported.

## Python Entry

```python
from statapy.compat.stata import rdrobust

# Explicit bandwidth
result = rdrobust(
    data, y="vote", x="margin",
    c=0.0, h=15.0, kernel="triangular", vce="nn"
)

# Automatic bandwidth selection
result = rdrobust(
    data, y="vote", x="margin",
    c=0.0, bwselect="mserd"
)

# Covariate-adjusted sharp RD
result = rdrobust(
    data, y="vote", x="margin",
    c=0.0, h=15.0, covs="z"
)
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Outcome variable |
| `x` | `str` | Running (forcing) variable |
| `c` | `float` | Cutoff (default `0.0`) |
| `h` | `float \| tuple[float, float] \| None` | Main bandwidth(s). If scalar, used on both sides. Overrides `bwselect` when provided. |
| `b` | `float \| tuple[float, float] \| None` | Bias bandwidth(s). Defaults to `h` if not provided. |
| `p` | `int` | Polynomial order for point estimation (default `1`) |
| `q` | `int` | Polynomial order for bias correction (default `2`) |
| `kernel` | `str` | `"triangular"` (default), `"epanechnikov"`, `"uniform"` |
| `vce` | `str` | `"nn"` (nearest-neighbor), `"hc0"` (plug-in residuals) |
| `nnmatch` | `int` | Minimum neighbors for `vce="nn"` (default `3`) |
| `level` | `int` | Confidence level (default `95`) |
| `bwselect` | `str \| None` | Bandwidth selector. `"mserd"` supported. Ignored if `h` is provided. |
| `covs` | `list[str] \| str \| None` | Covariate variable name(s) for covariate-adjusted sharp RD. |
| `covs_drop` | `bool` | Drop collinear covariates (default `True`). |
| `scaleregul` | `float` | Regularization scaling for bandwidth selectors (default `1.0`). |

## Supported Result Fields

Conventional RD estimate (`tau_cl`), bias-corrected estimate (`tau_bc`), conventional standard error (`se_tau_cl`), robust standard error (`se_tau_rb`), z-statistics, p-values, and confidence intervals. Side-specific effective sample sizes (`N_h_l`, `N_h_r`) and bandwidths are attached as `_rd_extras`.

## Planned Parameters

- Additional bandwidth selectors: `msetwo`, `msesum`, `cerrd`, `certwo`, `cersum`, `ik`, `cv`
- `deriv > 0` (kink designs)
- `weights`
- `cluster` / cluster-robust VCE

## Explicitly Unsupported Parameters

`fuzzy`, `deriv > 0`, `weights`, `cluster`, `stdvars`, `all`, `detail`, and all other `rdrobust`-specific options are hard-rejected via `ValueError` or `NotImplementedError`. Bandwidth selectors other than `mserd` are also hard-rejected.

## Alignment Evidence

Validation evidence book entry: [`docs/validation/evidence-matrix.md#rdrobust`](../validation/evidence-matrix.md#rdrobust)

- **Synthetic cases:** `tests/test_rdrobust.py` (controlled jump, kernel/bandwidth variation, boundary behavior, automatic bandwidth selector behavior, covariate-adjusted estimation)
- **Real-data cases:** `tests/test_rdrobust.py` — official `rdrobust_senate.dta` (Cattaneo, Frandsen, and Titiunik 2015)
- **Dual-run verified against Stata 17** for:
  - `rdrobust vote margin, c(0) h(15)` — `tau_cl`, `tau_bc`, `se_tau_cl`, `se_tau_rb` all match to < 1e-6 relative tolerance.
  - `rdrobust vote margin, c(0) h(15) vce(hc0) kernel(uniform)` — full four-object match to < 1e-6 relative tolerance.
  - `rdrobust vote margin, c(0) bwselect(mserd)` — bandwidths agree to ~0.03 %, estimates to ~1e-4 relative tolerance.
  - `rdrobust vote margin, c(0) h(15) covs(z)` — full four-object match to < 1e-6 relative tolerance.
  - `rdrobust vote margin, c(0) covs(z)` — bandwidths agree to ~0.03 %, estimates to ~1e-4 relative tolerance.
- **Local source mirror:** `research/vendor/stata_community/rdrobust/`
- **Mathematical source:** CCT (2014a) local polynomial RD estimator with bias correction and robust inference; Stata `rdrobust.ado` v10.0.0 and Mata functions for verification.

## Core Implementation

`src/statapy/estimators/rdrobust.py` (`RDRobust`)
