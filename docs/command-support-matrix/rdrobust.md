# Support Matrix: `rdrobust`

## Command Target

Local polynomial Regression Discontinuity estimation with robust bias-corrected inference, aligned with the Stata community command `rdrobust` (Calonico, Cattaneo, and Titiunik 2014a; Calonico, Cattaneo, and Farrell 2018).

## Completeness Status

**Beta** — sharp RD is usable with all 9 automatic bandwidth selectors, covariate adjustment (`covs`), frequency weights (`weights`), masspoints handling (`masspoints`, `bwcheck`), fuzzy RD (`fuzzy`, `sharpbw`), and cluster-robust VCE (`cluster` with `vce="cluster"` or `vce="nncluster"`). The `rdplot` companion command is implemented for IMSE-optimal binning and local polynomial fit overlays, but lacks field-level Stata 17 comparison evidence (bin-selection algorithm differs from Stata by up to 2–3x on real data). Kink designs remain unsupported.

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

### Supported Core

| Parameter | Type | Description | Research Archive |
|-----------|------|-------------|-----------------|
| `bwrestrict` | `bool` | Restrict bandwidth to data range | `docs/research/rdrobust-bandwidth-selectors.md` |

### Deferred

- `deriv > 0` (kink designs)
- `stdvars` (standardized variables)
- `all` / `detail` (extended output)
- `rdbwselect` standalone command

The exported `rdplot` companion is a supported helper; it is not counted among
the 14 estimation commands. See `stataflow.compat.stata.rdplot`.

## Explicitly Unsupported Parameters

`deriv > 0`, `stdvars`, `all`, `detail`, and Stata-graph-specific options are hard-rejected via `ValueError` or `NotImplementedError`.

`bwrestrict` is hard-rejected in the current release and remains a researched
but unimplemented option (see `docs/research/rdrobust-bandwidth-selectors.md`).

## Alignment Evidence

### Frozen strict alignments

The July 2026 release aggregate includes `3/3` strict RD comparisons. Its
maximum coefficient relative deviation is `9.23e-8`; its maximum standard-error
relative deviation is `2.96e-8`.

- `rdrobust prestige run, c(0) h(5000)` on the public Prestige fixture.
- `rdrobust vote margin, c(0) h(15)` on the public Senate fixture.
- `rdrobust vote margin, c(0) h(15) vce(hc0) kernel(uniform)`.

These compare `tau_cl`, `tau_bc`, `se_tau_cl`, and `se_tau_rb`. Aggregate
values are traceable to
[`evidence-summary.json`](../../research/results/validation/evidence-summary.json).

### Additional completed comparisons

These broaden functional coverage but are not part of the strict `3/3`
release aggregate:

- Fixed-bandwidth covariate adjustment meets the strict field-level target.
- Automatic bandwidth comparisons agree at about `0.03%` for bandwidths and
  about `1e-4` for estimates; across all selectors, estimates can differ by
  up to `0.5%` and bandwidths by up to `1%`.
- Fuzzy RD estimates differ by up to `0.5%`; standard errors differ by up to
  `5%` on synthetic data and `0.5%` on the Senate data.
- Cluster and nearest-neighbor cluster estimates differ by up to `1%`, with
  standard-error differences up to `3%`.
- `rdplot` bin selection can differ by `2-3x` and has no strict alignment
  claim.

The mathematical basis is the CCT local-polynomial RD estimator with bias
correction and robust inference, compared with Stata 17 and the public
`rdrobust` release.

## Core Implementation

`src/stataflow/estimators/rdrobust.py` (`RDRobust`)
