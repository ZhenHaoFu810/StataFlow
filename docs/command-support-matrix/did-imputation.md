# Support Matrix: `did_imputation`

## Completeness Status

**Beta — Core Estimator** — the Borusyak-Jaravel-Spiess DID imputation estimator with TWFE-on-controls, imputation, cluster-robust standard errors, `minn`, `controls`, `unitcontrols`, and `timecontrols` is implemented and verified. Repeated cross-section is missing. `window` is available only on the Python-native estimator because the current target Stata `did_imputation` ado rejects `window()`.

## Command Target

Borusyak, Jaravel \& Spiess (2021) DID imputation estimator, aligned with Stata community command `did_imputation`.

## Python Entry

```python
from stataflow.compat.stata import did_imputation

result = did_imputation(
    data, y="y", id="unit_id", time="year",
    first_treat="first_treat",
    cluster="unit_id", allhorizons=True, autosample=False
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
| `cluster` | `str` | Cluster variable for cluster-robust SEs (defaults to `id`) |
| `allhorizons` | `bool` | Compute all event-time horizons, including pre-treatment (negative) horizons |
| `autosample` | `bool` | Automatically drop non-imputable observations |
| `window` | `list[int]` | Python-native extension only; rejected by the Stata-compatible wrapper for the current target ado |
| `minn` | `int` | Minimum imputable observations required per horizon |
| `controls` | `list[str]` | Control covariates (global slopes, applied to Y0) |
| `unitcontrols` | `list[str]` | Unit-specific control slopes (interacted with unit FE) |
| `timecontrols` | `list[str]` | Time-specific control slopes (interacted with time FE) |
| `pretrends` | `int` | Number of pretreatment periods to test for parallel trends |
| `wtr` | `str` or `list[str]` | Custom weight variable(s) for weighted average treatment effects |
| `hetby` | `str` | Group variable for heterogeneous effects (splits each `wtr` by group) |
| `saveestimates` | `str` | Save `effect = Y - Y0` as a pandas Series on the fitted model instance |
| `saveweights` | `bool` | Save imputation weights as a pandas DataFrame on the fitted model instance |
| `sum` | `bool` | Compute weighted sums instead of weighted averages (no normalization) |

## Supported Result Fields

Event-study horizon coefficients (`tau0`, `tau1`, ...), standard errors, z-statistics, p-values, confidence intervals. Returned as `ResultSchema`.

## Python-Native Extensions

- `DIDImputation.fit(window=[min, max])` restricts relative-time horizons inside Python.
- `compat.stata.did_imputation(..., window=...)` raises `NotImplementedError` because the local target Stata 17 validation ado, Borusyak `did_imputation` Nov 2023, reports `option window() not allowed`.

## Planned Parameters

- `horizons` (explicit horizon subsetting)
- `hbalance` (balanced panel constraint)
- `project` (projection to covariate space)
- `saveresid` (save regression residuals)
- Repeated cross-section support

## Explicitly Unsupported Parameters

`window` in the Stata-compatible wrapper, `horizons`, `hbalance`, `project`, `saveresid`, and all other did_imputation-specific options are hard-rejected via `NotImplementedError` or `ValueError`.

## Alignment Evidence


- Synthetic cases: Stata validation case `w4_did_imputation_basic` (basic), Stata validation case `w9_di_controls_basic` (controls), Stata validation case `w9_di_pretrends_basic` (pretrends), Stata validation case `w9_di_controls_pretrends_combo` (controls + pretrends)
- Real-data cases: Stata validation case `w4_did_imputation_real_ezunem`
- Source basis: public `did_imputation` release and BJS methodology
- Validated by Stata 17 comparison for TWFE-imputation event-study coefficients with cluster-robust SEs, controls, and pretrends.
- `M07-DID-006` documents that `window()` is not accepted by the current target ado; S2 validation therefore covers `allhorizons` without `window()`.

## Core Implementation

`src/stataflow/estimators/did_imputation.py`
