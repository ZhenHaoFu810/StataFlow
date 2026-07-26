# Support Matrix: `regress`

## Command Target

Ordinary least squares (OLS) linear regression, aligned with Stata 17 `regress`.

## Python Entry

```python
from stataflow.compat.stata import regress

result = regress(data, y="depvar", x=["x1", "x2"], vce="robust")
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `x` | `list[str]` | Independent variables |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str` or `list[str]` | Cluster variable(s). Single `str` for one-way; list of two `str` for two-way clustering (requires `vce="cluster"`) |
| `aweight` | `str` | Variable name for analytical weights |
| `noconstant` | `bool` | Drop constant term |
| `level` | `int` | Confidence level (default 95) |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, t-statistics, p-values, confidence intervals, R-squared, adjusted R-squared, RMSE, F-statistic, residual and model SS.

## Planned Parameters

- `fweight`, `pweight`, `iweight`
- `beta` (standardized coefficients)
- `hascons`, `tsscons`

## Explicitly Unsupported Parameters

Any other Stata options (e.g. `cformat`, `pformat`, `sformat`, `coeflegend`, `noheader`, `noretable`, `nodisplay`) are hard-rejected via `ValueError`.

## Factor Variable Support

The wrapper layer automatically expands Stata-style factor terms in `x`:

- `c.x1`, `i.g`
- `ib2.g`, `b2.g` (explicit base level)
- `o2.g` (explicit omitted level)
- `c.x1#c.x2`, `c.x1##c.x2`
- `i.g1#i.g2`, `i.g1##i.g2`
- `i.g1#c.x1`, `i.g1##c.x1`
- `x1#x2`, `x1##x2` (bare variables inside `#` / `##` are treated as continuous)
- `x1##i.g`, `i.g##x1` (mixed bare continuous and categorical)

Unsupported factor syntax (`ib.` without level, `o.` without level, `b.` without level, time-series operators) remain hard-rejected with `ValueError`.

## Alignment Evidence


- Synthetic cases: Stata validation case `p1_ols_basic`, Stata validation case `p1_cluster_firm`
- Factor-syntax cases: Stata validation case `a2_factor_regress_basic` — `regress y i.g##c.x1`; Stata validation case `a2_factor_regress_bare` — `regress y x1##x2` mapped to Stata `c.x1##c.x2`; Stata validation case `a2_factor_regress_base` — `regress y ib2.g##c.x1`
- Real-data cases: Stata validation case `v1_regress_real_grunfeld` (Grunfeld investment panel)
- Validated by Stata 17 comparison for OLS, HC1 robust, and cluster-robust VCE

## Core Implementation

`src/stataflow/estimators/ols.py`
