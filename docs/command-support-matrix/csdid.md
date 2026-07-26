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
| `notyet` | `bool` | Use not-yet-treated units as control group (supported for `method="reg"`) |

`aggtype` (`"event"`, `"simple"`, `"group"`, `"calendar"`, `"pretrend"`; defaults to `"event"`) is a parameter of `model.estat()`, **not** of the `csdid()` wrapper — passing it to `csdid()` raises `ValueError`.

`time` and `first_treat` may use integer dtype or floating dtype containing
integer-valued period labels (for example, `2004.0`). Equivalent integer and
floating labels produce the same estimates and normalized display names.

## Supported Result Fields

The wrapper returns a fitted `CSDID` model object. Result contract (ADR-0005):

- `model.result` — default (event) aggregation as a `ResultSchema`, field-by-field identical to `model.estat("event")`
- `model.summary()` / `model.display()` — delegate to `model.result`
- `model.estat(aggtype)` — explicit aggregations

ATT(g,t) estimates, event-study / simple / group / calendar aggregation coefficients, standard errors, z-statistics, p-values, confidence intervals. `estat_pretrend()` returns a joint Wald test dict. Returned as `ResultSchema` via `estat()`.

## Planned Parameters

- `method="ipw"` (inverse probability weighting)
- `aggtype="dynamic"` (already covered by `event`)
- `gtcontrol` (control group strategy)
- `longdiff` (long-difference pre-trends)
- `window`, `minn`

## Explicitly Unsupported Parameters

`method="ipw"`, `gtcontrol`, `longdiff`, `window`, `minn`, `save`, `replace`, `graph`, and all other csdid-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: Stata validation case `w4_csdid_basic` (reg), Stata validation case `w9_csdid_dr_basic` (drimp)
- Real-data cases: Stata validation case `w4_csdid_real_ezunem` (reg), Stata validation case `w9_csdid_dr_real_ezunem` (drimp)
- Validated by Stata 17 comparison for `method="reg"` and `method="drimp"` with event-study aggregation

## Core Implementation

`src/stataflow/estimators/csdid.py`
