# Support Matrix: `eventstudyinteract`

## Completeness Status

**Beta** — the Sun-Abraham interaction-weighted event-study estimator with auto dummy generation is implemented and verified, but `window`, `minn`, and full output/reporting options are missing.

## Command Target

Sun & Abraham interaction-weighted event-study estimator, aligned with Stata community command `eventstudyinteract`.

## Python Entry

```python
from stataflow.compat.stata import eventstudyinteract

# Auto-generation mode (command-semantic interface)
result = eventstudyinteract(
    data, y="y", time="year", first_treat="first_treat",
    horizons=[-3, -2, -1, 0, 1, 2, 3], omit=-1,
    cohort="first_treat", control_cohort="never_treat",
    absorb=["unit_id", "year"], cluster="unit_id"
)

# Legacy mode with pre-generated dummies
result = eventstudyinteract(
    data, y="y", event_dummies=["dm3", "dm2", "d0", "dp1", "dp2"],
    cohort="first_treat", control_cohort="never_treat",
    absorb=["unit_id", "year"], cluster="unit_id"
)
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `event_dummies` | `list[str]` | Pre-generated relative-time dummy variables (legacy mode) |
| `time` | `str` | Time identifier (auto-generation mode) |
| `first_treat` | `str` | First treatment period variable (auto-generation mode) |
| `horizons` | `list[int]` | Relative-time horizons to include (auto-generation mode) |
| `omit` | `int` | Omitted reference horizon (auto-generation mode) |
| `cohort` | `str` | Cohort variable (first treatment period) |
| `control_cohort` | `str` | Binary indicator for control cohort |
| `absorb` | `list[str]` | Fixed-effect variables to absorb |
| `vce` | `str` | `"ols"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |

In auto-generation mode, observations outside the requested horizon range are
binned into the nearest endpoint. Never-treated observations remain zero in
every generated event dummy. This matches the explicit-dummy workflow commonly
used with the Stata command and prevents out-of-window treated observations from
silently entering the reference category.

## Supported Result Fields

Interaction-weighted event-study coefficients, standard errors, z-statistics, p-values, confidence intervals by relative time horizon.

## Planned Parameters

- `window` (event horizon window)
- `minn` (minimum cohort share)
- `cohort` share reporting

## Explicitly Unsupported Parameters

`window`, `minn`, `save`, `replace`, `graph`, and all other eventstudyinteract-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: Stata validation case `w4_eventstudyinteract_basic`
- Real-data cases: Stata validation case `w4_eventstudyinteract_real_ezunem`
- Endpoint-binning regression: `tests/test_compat_stata_did.py`
- Source basis: public `eventstudyinteract` release and published methodology
- Validated by Stata 17 comparison for interaction-weighted event-study coefficients

## Core Implementation

`src/stataflow/estimators/eventstudyinteract.py`
