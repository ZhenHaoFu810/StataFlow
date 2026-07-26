# Support Matrix: `xtreg, fe`

## Command Target

Fixed-effects (within) panel regression, aligned with Stata 17 `xtreg, fe`.

## Python Entry

```python
from stataflow.compat.stata import xtreg_fe

result = xtreg_fe(data, y="depvar", x=["x1", "x2"], fe="id")
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `x` | `list[str]` | Independent variables |
| `fe` | `str` | Entity identifier |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` (`robust` is panel-robust: the same sandwich as `cluster(fe)` in Stata 17) |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
| `level` | `int` | Confidence level (default 95) |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, t-statistics, p-values, confidence intervals, within R-squared, adjusted R-squared, RMSE, F-statistic.

## Planned Parameters

- Weights (`aweight`, `fweight`, `pweight`)
- `nonest` (nonestimable handling)
- `dfadj`

## Explicitly Unsupported Parameters

All other Stata options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: Stata validation case `p2_fe_basic`, Stata validation case `p2_fe_cluster`
- Real-data cases: Stata validation case `v1_xtreg_fe_real_grunfeld` (within-estimator alignment on Grunfeld)
- Validated by Stata 17 comparison for conventional and cluster-robust VCE

## Core Implementation

`src/stataflow/estimators/fe.py`
