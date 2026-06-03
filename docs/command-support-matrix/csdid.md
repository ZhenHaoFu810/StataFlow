# Support Matrix: `csdid`

## Completeness Status

**Beta — Core Estimator** — the Callaway-Sant'Anna CSDID estimator with `method="reg"`, `method="drimp"` / `method="dripw"` (doubly robust), and all standard aggregation types (`estat_event`, `estat_simple`, `estat_group`, `estat_calendar`, `estat_pretrend`) is implemented and verified. IPW and wild bootstrap are missing.

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
| `method` | `str` | `"reg"`, `"drimp"`, or `"dripw"` |
| `xvars` | `list[str]` | Covariates for doubly-robust estimation |
| `vce` | `str` | `"cluster"` only |
| `cluster` | `str` | Cluster variable (defaults to `id`) |
| `aggtype` | `str` | `"event"`, `"simple"`, `"group"`, `"calendar"`, or `"pretrend"` (defaults to `"event"`) |

## Supported Result Fields

ATT(g,t) estimates, event-study / simple / group / calendar aggregation coefficients, standard errors, z-statistics, p-values, confidence intervals. `estat_pretrend()` returns a joint Wald test dict. Returned as `ResultSchema` via `estat()`.

## Planned Parameters

- `method="ipw"` (inverse probability weighting)
- `aggtype="dynamic"` (already covered by `event`)
- `gtcontrol` (control group strategy)
- `longdiff` (long-difference pre-trends)

## Explicitly Unsupported Parameters

`method="ipw"`, `gtcontrol`, `longdiff`, `window`, `minn`, `save`, `replace`, `graph`, and all other csdid-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w4_csdid_basic.py` (reg), `tests/golden/test_w9_csdid_dr_basic.py` (drimp)
- Real-data cases: `tests/golden/test_w4_csdid_real_ezunem.py` (reg), `tests/golden/test_w9_csdid_dr_real_ezunem.py` (drimp)
- Stata 17 dual-run verified for `method="reg"` and `method="drimp"` with event-study aggregation

## Core Implementation

`src/stataflow/estimators/csdid.py`
