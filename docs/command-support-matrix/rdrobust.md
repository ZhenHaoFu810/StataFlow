# Support Matrix: `rdrobust`

## Command Target

Local polynomial Regression Discontinuity estimation with robust bias-corrected inference, aligned with the Stata community command `rdrobust` (Calonico, Cattaneo, and Titiunik 2014a; Calonico, Cattaneo, and Farrell 2018).

## Completeness Status

**Beta** — sharp RD is usable with all 9 automatic bandwidth selectors, covariate adjustment (`covs`), frequency weights (`weights`), masspoints handling (`masspoints`, `bwcheck`), fuzzy RD (`fuzzy`, `sharpbw`), and cluster-robust VCE (`cluster` with `vce="cluster"` or `vce="nncluster"`). The `rdplot` companion command is implemented for IMSE-optimal binning and local polynomial fit overlays, but lacks Stata golden dual-run evidence (bin-selection algorithm differs from Stata by up to 2–3× on real data). Kink designs remain unsupported.

## Python Entry

```python
from stataflow.compat.stata import rdrobust

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
| `vce` | `str` | `"nn"` (nearest-neighbor, default), `"hc0"` (plug-in residuals), `"cluster"` (cluster-robust), `"nncluster"` (NN residuals + cluster aggregation) |
| `nnmatch` | `int` | Minimum neighbors for `vce="nn"` (default `3`) |
| `level` | `int` | Confidence level (default `95`) |
| `bwselect` | `str \| None` | Bandwidth selector. `"mserd"`, `"msesum"`, `"msetwo"`, `"msecomb1"`, `"msecomb2"`, `"cerrd"`, `"cersum"`, `"certwo"`, `"cercomb1"`, `"cercomb2"` supported. Ignored if `h` is provided. |
| `covs` | `list[str] \| str \| None` | Covariate variable name(s) for covariate-adjusted sharp RD. |
| `covs_drop` | `bool` | Drop collinear covariates (default `True`). |
| `scaleregul` | `float` | Regularization scaling for bandwidth selectors (default `1.0`). |
| `fuzzy` | `str \| None` | Fuzzy RD treatment variable name. |
| `sharpbw` | `bool` | Use sharp bandwidth selection for fuzzy RD (default `False`). |
| `weights` | `str \| None` | Frequency weight variable name. |
| `masspoints` | `str` | Mass points handling: `"adjust"` (default), `"check"`, `"off"`. |
| `bwcheck` | `int` | Minimum unique observations within bandwidth window (default `0`). |
| `cluster` | `str \| None` | Cluster variable name for `vce="cluster"` or `vce="nncluster"`. |

## Supported Result Fields

Conventional RD estimate (`tau_cl`), bias-corrected estimate (`tau_bc`), conventional standard error (`se_tau_cl`), robust standard error (`se_tau_rb`), z-statistics, p-values, and confidence intervals. Side-specific effective sample sizes (`N_h_l`, `N_h_r`) and bandwidths are attached as `_rd_extras`.

## Planned Parameters

### Wave 8 Round 2 Target (Min Implementation)

| Parameter | Type | Description | Research Archive |
|-----------|------|-------------|-----------------|
| `bwrestrict` | `bool` | Restrict bandwidth to data range | `docs/research/rdrobust-bandwidth-selectors.md` |

### Deferred (beyond Wave 8)

- `deriv > 0` (kink designs)
- `stdvars` (standardized variables)
- `all` / `detail` (extended output)
- `rdbwselect` standalone command

The `rdplot` companion command is implemented as a separate supported command; see `stataflow.compat.stata.rdplot`.

## Explicitly Unsupported Parameters

`deriv > 0`, `stdvars`, `all`, `detail`, and Stata-graph-specific options are hard-rejected via `ValueError` or `NotImplementedError`.

`bwrestrict` is hard-rejected in the current release but has completed Wave 8 Round 1 research and is targeted for Round 2 implementation (see `docs/research/rdrobust-bandwidth-selectors.md`).

## Alignment Evidence


- **Synthetic cases:** `tests/test_rdrobust.py` (controlled jump, kernel/bandwidth variation, boundary behavior, automatic bandwidth selector behavior, covariate-adjusted estimation), `tests/golden/test_w8_rdrobust_fuzzy_synthetic.py` (fuzzy RD)
- **Real-data cases:** `tests/test_rdrobust.py` — official `rdrobust_senate.dta` (Cattaneo, Frandsen, and Titiunik 2015), `tests/golden/test_w8_rdrobust_bwselect_all_real_senate.py` (all 9 bandwidth selectors), `tests/golden/test_w8_rdrobust_fuzzy_real_senate.py` (fuzzy RD), `tests/golden/test_w8_rdrobust_cluster_real_senate.py` (cluster / nncluster VCE)
- **Dual-run verified against Stata 17** for:
  - `rdrobust vote margin, c(0) h(15)` — `tau_cl`, `tau_bc`, `se_tau_cl`, `se_tau_rb` all match to < 1e-6 relative tolerance.
  - `rdrobust vote margin, c(0) h(15) vce(hc0) kernel(uniform)` — full four-object match to < 1e-6 relative tolerance.
  - `rdrobust vote margin, c(0) bwselect(mserd)` — bandwidths agree to ~0.03 %, estimates to ~1e-4 relative tolerance.
  - `rdrobust vote margin, c(0) h(15) covs(z)` — full four-object match to < 1e-6 relative tolerance.
  - `rdrobust vote margin, c(0) covs(z)` — bandwidths agree to ~0.03 %, estimates to ~1e-4 relative tolerance.
  - All 9 bandwidth selectors on `rdrobust_senate.dta` — estimates < 0.5 %, bandwidths < 1 % relative tolerance.
  - Fuzzy RD (synthetic + real senate data) — estimates < 0.5 %, SEs < 5 % (synthetic) / < 0.5 % (real) relative tolerance.
  - `vce(cluster)` and `vce(nncluster)` on `rdrobust_senate.dta` — estimates < 1 %, SEs < 3 % relative tolerance.
- **Local source mirror:** `research/vendor/stata_community/rdrobust/`
- **Mathematical source:** CCT (2014a) local polynomial RD estimator with bias correction and robust inference; Stata `rdrobust.ado` v10.0.0 and Mata functions for verification.

## Core Implementation

`src/stataflow/estimators/rdrobust.py` (`RDRobust`)
