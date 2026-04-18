# Support Matrix: `xtreg, fe`

## Command Target

Fixed-effects (within) panel regression, aligned with Stata 17 `xtreg, fe`.

## Python Entry

```python
from statapy.compat.stata import xtreg_fe

result = xtreg_fe(data, y="depvar", x=["x1", "x2"], fe="id")
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `x` | `list[str]` | Independent variables |
| `fe` | `str` | Entity identifier |
| `vce` | `str` | `"ols"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
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

- Synthetic cases: `tests/golden/test_p2_fe_basic.py`, `tests/golden/test_p2_fe_cluster.py`
- Real-data cases: `tests/golden/test_w5_predict_real_wagepan.py` (predict alignment on wagepan)
- Stata 17 dual-run verified for conventional and cluster-robust VCE

## Core Implementation

`src/statapy/estimators/fe.py`
