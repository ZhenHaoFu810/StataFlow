# Support Matrix: `ppmlhdfe`

## Completeness Status

**Partial / Phase B Subset** — PPML-HDFE with 1–2  FEs, offset/exposure, robust/cluster VCE, `maxiter`/`tolerance`, `predict(residuals)`, `deviance`, and `pseudo_r2` is implemented and verified. Still missing: separation detection, multi-way clustering, and additional predict types (`pearson`, `deviance`, `working`).

## Command Target

Poisson pseudo-maximum likelihood with high-dimensional fixed effects, aligned with Stata community command `ppmlhdfe`.

## Python Entry

```python
from stataflow.compat.stata import ppmlhdfe

result = ppmlhdfe(
    data, y="depvar", x=["x1", "x2"],
    absorb=["exporter", "importer", "year"], vce="cluster", cluster="pair_id"
)
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable (count) |
| `x` | `list[str]` | Independent variables |
| `absorb` | `str \| list[str]` | 1-2 categorical variables to absorb |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
| `offset` | `str` | Offset variable name (coefficient fixed at 1) |
| `exposure` | `str` | Exposure variable name (log-transformed to offset) |
| `noconstant` | `bool` | Omit the constant term *(Python extension; not in Stata `ppmlhdfe`)* |
| `maxiter` | `int` | Maximum IRLS iterations (default 100) |
| `tolerance` | `float` | IRLS convergence tolerance (default 1e-8) |
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
- `predict(type="residuals")` — response residual `y - 渭`
- `margins(type="dydx")`
- `margins(type="atmeans")`

## Planned Parameters

- Separation problem handling (`separation`)
- `d` (diagnostics)
- Additional predict types (`pearson`, `deviance`, `working`)

## Explicitly Unsupported Parameters

`separation`, `d`, `vceversion`, `individual`, `group`, `noreport`, `keepmata`, `pearson`, `anscombe`, and all other ppmlhdfe-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w3_ppmlhdfe_basic.py`, `tests/golden/test_w3_ppmlhdfe_cluster.py`
- Real-data cases: `tests/golden/test_w3_ppmlhdfe_real_gravity.py`
- Factor-syntax case: `tests/golden/test_a2_factor_ppmlhdfe_basic.py` — `ppmlhdfe y i.g##c.x1, absorb(firm year)`
- **Phase B fit-stats case**: `tests/golden/test_p3_ppmlhdfe_fit_stats.py` — deviance and pseudo-R虏 dual-run verification
- Margins cases: covered in Wave 5 postestimation tests
- Local source mirror: `research/vendor/stata_community/ppmlhdfe/`
- Stata 17 dual-run verified for 1-2 absorbed FEs with robust and cluster VCE

## Core Implementation

`src/stataflow/estimators/ppmlhdfe.py`
