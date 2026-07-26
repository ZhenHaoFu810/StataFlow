# Reproducible Stata Validation Cases

`tests/stata_validation/` contains 10 self-contained cases that users can run
with a local Stata 17 installation. Each case generates deterministic
synthetic data, runs matching Stata and Python estimations, and compares
field-level results.

## Coverage

| Type | Case | Compared fields |
|---|---|---|
| Built-in | `regress, vce(robust)` | coefficients, robust SE, `df_resid` |
| Built-in | `xtreg, fe vce(robust)` | coefficients, robust SE, `df_resid` |
| Built-in | `areg, vce(cluster ...)` | coefficients, clustered SE |
| Built-in | `ivregress 2sls, vce(robust)` | coefficients, robust SE |
| Built-in | `logit, vce(robust)` | coefficients, robust SE |
| Built-in | `poisson, vce(robust)` | coefficients, robust SE |
| Community | `reghdfe, vce(cluster ...)` | coefficients, clustered SE |
| Community | `did_imputation` | event-study coefficients and SE |
| Community | `csdid, method(reg)` | event-study coefficients and SE |
| Community | `rdrobust, h(0.5)` | `tau_cl`, `se_tau_cl`, effective N |

Relative deviation uses
`|Python - Stata| / max(|Stata|, 1e-15)`. Coefficients and standard errors use
`rtol=1e-6` except for the `did_imputation` standard-error comparison, which
uses the documented `rtol=1e-2` numerical exception. The 10-case suite
therefore does not claim that every compared field meets `1e-6`. DID cases
also enforce compatible calendar-time units and a nonzero treatment-effect
guard.

## Run

```bash
pytest tests/stata_validation/ -v -s
```

The cases:

1. generate seeded synthetic data;
2. create Stata input and command files;
3. execute Stata 17 in batch mode;
4. parse high-precision output;
5. compare coefficients, standard errors, and applicable metadata.

Stata execution artifacts are temporary validation outputs and are not source
artifacts.

## Requirements

- A locally configured Stata 17 executable.
- `reghdfe` and `ftools` for the HDFE case.
- `did_imputation` for the BJS case.
- `csdid` and `drdid` for the Callaway-Sant'Anna case.
- `rdrobust` for the RD case.

Install community commands from their official distribution channels before
running the corresponding cases.

## Prerequisite and Skip Semantics

- If Stata 17 is unavailable, or another Stata release is selected, the suite
  fails its prerequisite check with an explicit reason.
- If a required community command is unavailable, only that case skips.
- The public CI environment collects the cases but does not claim proprietary
  Stata execution.

The July 2026 release run completed all `10/10` cases with Stata 17.

## Evidence Boundary

Public validation materials include deterministic generators, comparison
helpers, public datasets, field-level assertions, and the aggregate evidence
summary. They exclude Stata licenses, proprietary datasets, local paths,
third-party source mirrors, and pre-generated private logs.

Related documentation:

- [Validation Overview](./overview.md)
- [Validation Policy](./validation-policy.md)
- [Evidence Matrix](./evidence-matrix.md)
- [Validation Summary](../../research/results/validation/evidence-summary.md)
