# Support Matrix: `csdid`

## Completeness Status

**Partial / Regression-Adjustment Subset** — the Callaway-Sant'Anna CSDID estimator with `method="reg"` and event-study aggregation (`estat_event`) is implemented and verified, but doubly-robust methods, IPW, other aggregation types, and wild bootstrap are missing. As of this round, `estat_event()` returns `ResultSchema` aligned with other DID commands.

## Command Target

Callaway-Sant'Anna DID estimator, aligned with Stata community command `csdid`.

## Python Entry

```python
from stataflow.compat.stata import csdid

result = csdid(
    data, y="y", id="county_id", time="year",
    first_treat="first_treat_year", method="reg", cluster="county_id"
)
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `id` | `str` | Unit identifier |
| `time` | `str` | Time identifier |
| `first_treat` | `str` | First treatment period variable |
| `method` | `str` | `"reg"` only (regression adjustment) |
| `vce` | `str` | `"cluster"` only |
| `cluster` | `str` | Cluster variable (defaults to `id`) |

## Supported Result Fields

ATT(g,t) estimates, event-study aggregation coefficients, standard errors, z-statistics, p-values, confidence intervals by relative time. Returned as `ResultSchema` via `estat_event()`.

## Planned Parameters

- `method="dr"` (doubly robust)
- `method="ipw"` (inverse probability weighting)
- `aggtype` (aggregation type: simple, dynamic, group, calendar)
- `gtcontrol` (control group strategy)
- `longdiff` (long-difference pre-trends)

## Explicitly Unsupported Parameters

`method="dr"`, `method="ipw"`, `aggtype`, `gtcontrol`, `longdiff`, `window`, `minn`, `save`, `replace`, `graph`, and all other csdid-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w4_csdid_basic.py`
- Real-data cases: `tests/golden/test_w4_csdid_real_ezunem.py`
- Stata 17 dual-run verified for `method="reg"` with event-study aggregation

## Core Implementation

`src/stataflow/estimators/csdid.py`
