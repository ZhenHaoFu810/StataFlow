# Support Matrix: `ppmlhdfe`

## Completeness Status

**Partial / Phase B+ Subset** — PPML-HDFE with multiple FEs (1+ FEs dual-run verified; 3+ FE covered in synthetic tests), offset/exposure, robust/cluster VCE (including 2-way cluster), `maxiter`/`tolerance`, `predict(residuals)`, `deviance`, `pseudo_r2`, `separation(fe)`, `eform`, and `predict` with `pearson`/`deviance`/`working` residuals is implemented and verified. Wave 11 added full postestimation support: `predict(type="stdp")` is not applicable to PPML, but GLM residuals (`pearson`, `deviance`, `working`) and `estat_ic` are verified.

## Command Target

Poisson pseudo-maximum likelihood with high-dimensional fixed effects, aligned with Stata community command `ppmlhdfe`.

## Python Entry

```python
from stataflow.compat.stata import ppmlhdfe

result = ppmlhdfe(
    data, y="depvar", x=["x1", "x2"],
    absorb=["exporter", "importer"], vce="cluster", cluster="pair_id"
)
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable (count) |
| `x` | `list[str]` | Independent variables |
| `absorb` | `str \| list[str]` | Categorical variables to absorb (1+ supported) |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str \| list[str]` | Cluster variable(s); pass a list for 2-way cluster-robust VCE (required when `vce="cluster"`) |
| `offset` | `str` | Offset variable name (coefficient fixed at 1) |
| `exposure` | `str` | Exposure variable name (log-transformed to offset) |
| `noconstant` | `bool` | Omit the constant term *(Python extension; not in Stata `ppmlhdfe`)* |
| `maxiter` | `int` | Maximum IRLS iterations (default 100) |
| `tolerance` | `float` | IRLS convergence tolerance (default 1e-8) |
| `eform` | `bool` | Report incidence-rate ratios `exp(b)` with delta-method SE (default `False`) |
| `separation` | `str` | `"fe"` to drop FE groups where all `y == 0` (default `None`) |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, z-statistics, p-values, confidence intervals, log-likelihood, deviance, pseudo R-squared, absorbed degrees of freedom (`df_a`).

## Factor Variable Support

The wrapper layer automatically expands Stata-style factor terms in `x`:

- `c.x1`, `i.g`
- `ib2.g`, `b2.g` (explicit base level)
- `o2.g` (explicit omitted level)
- `c.x1#c.x2`, `c.x1##c.x2`
- `i.g1#i.g2`, `i.g1##i.g2`
- `i.g1#c.x1`, `i.g1##c.x1`
- `c.x1#i.g1`, `c.x1##i.g1` (mixed-order symmetry, equivalent to `i.g1#c.x1` / `i.g1##c.x1`)
- `x1#x2`, `x1##x2` (bare variables inside `#` / `##` are treated as continuous)
- `x1##i.g`, `i.g##x1` (mixed bare continuous and categorical)

`absorb` also accepts Stata-style space-separated strings (e.g., `absorb="firm year"`) in addition to Python lists.

Unsupported factor syntax (`ib.` without level, `o.` without level, `b.` without level, time-series operators, three-way+ interactions) is hard-rejected with `ValueError`.

## Postestimation (Core Estimator Layer Only)

The `compat.stata` wrapper returns a `ResultSchema` object. To use `predict()` or `margins()`, call the core estimator (`stataflow.estimators.PPMLHDFE`) directly.

- `predict(type="xb")`
- `predict(type="mu")`
- `predict(type="residuals")` — response residual `y - mu`
- `predict(type="pearson")` — Pearson residual `(y - mu) / sqrt(mu)`
- `predict(type="deviance")` — squared deviance contribution `2*(y*log(y/mu) - (y-mu))` (matches Stata `ppmlhdfe predict, deviance`)
- `predict(type="working")` — working residual `(y - mu) / mu`
- `margins(type="dydx")`
- `margins(type="atmeans")`

`estat_ic` is available via `stataflow.postestimation.estat_ic()`.

## Planned Parameters

- 3-way and higher multi-way clustering

## Explicitly Unsupported Parameters

`vceversion`, `individual`, `group`, `noreport`, `keepmata`, `anscombe`, and all other ppmlhdfe-specific options not listed above are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w3_ppmlhdfe_basic.py`, `tests/golden/test_w3_ppmlhdfe_cluster.py`
- Real-data cases: `tests/golden/test_w3_ppmlhdfe_real_gravity.py`
- Factor-syntax case: `tests/golden/test_a2_factor_ppmlhdfe_basic.py` — `ppmlhdfe y i.g##c.x1, absorb(firm year)`
- **Phase B fit-stats case**: `tests/golden/test_p3_ppmlhdfe_fit_stats.py` — deviance and pseudo-R2 dual-run verification
- **2-way cluster case**: `tests/golden/test_w7_ppmlhdfe_2way_cluster.py` — PPML + 2 FE + 2-way cluster; slope SEs < 1e-2, _cons SE known limitation
- **separation case**: `tests/golden/test_w7_ppmlhdfe_separation_fe.py` — `separation="fe"` synthetic dual-run verified
- **eform case**: `tests/golden/test_w7_ppmlhdfe_eform.py` — `eform=True` exp(b) and delta-method SE aligned
- Margins cases: covered in Wave 5 postestimation tests
- **Postestimation residuals case**: `tests/golden/test_w11_ppmlhdfe_residuals.py` — `predict(type="pearson"/"deviance"/"working")` aligned with Stata `ppmlhdfe predict`; ~0.35% max diff from IRLS convergence precision
- **Postestimation IC case**: `tests/golden/test_w11_estat_ic.py` — `estat_ic` AIC/BIC aligned with Stata `estat ic` after `ppmlhdfe`
- Local source mirror: `research/vendor/stata_community/ppmlhdfe/`
- Stata 17 dual-run verified for 1+ absorbed FEs with robust, single cluster, and 2-way cluster VCE

## Core Implementation

`src/stataflow/estimators/ppmlhdfe.py`
