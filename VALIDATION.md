# Stata Validation

[简体中文](docs/validation/README.zh-CN.md)

The July 2026 table is the "1.2.0 estimator-validation snapshot retained for 1.3.0".
The actual comparison environment was Stata 17. Each supported path is
exercised on the same data in Stata and Python, then compared field by field.
Evidence combines controlled synthetic cases with public real-data cases;
community commands are described only for their implemented subsets.

The retained snapshot covers the coefficient and standard-error comparisons reported below.
It does not cover result statistics first added in 1.3.0.

## July 2026 Snapshot

The release scope below is frozen as of July 2026. It is a release evidence
snapshot, not a claim that every option accepted by the corresponding Stata
command has been reproduced.

Relative deviation is:

```text
|Python - Stata| / max(|Stata|, 1e-15)
```

| Family | Passed comparisons | Max coefficient deviation | Max SE deviation |
|---|---:|---:|---:|
| Linear / FE | 18/18 | 2.48e-7 | 2.25e-7 |
| IV | 5/5 | 1.16e-8 | 3.74e-8 |
| Binary / count | 12/12 | 1.33e-7 | 8.42e-8 |
| DID | 2/2 + 1 functional check | 8.13e-8 | 5.13e-8 |
| RD | 3/3 | 9.23e-8 | 2.96e-8 |
| **Total** | **40/40** | **2.48e-7** | **2.25e-7** |

Full local Stata validation checks completed with `856 passed, 12 skipped`.
The skipped checks are eight intentionally unsupported weighted GLM/PPML
contracts and four IV fields that Stata does not store under the tested VCE;
none is a failed numerical comparison.
The public self-contained suite completed `10/10` reproducible validation
cases with Stata 17. The aggregate values and formula are stored in
[`research/results/validation/evidence-summary.json`](research/results/validation/evidence-summary.json).

## Comparison Method

Each numerical case records the Stata command, the Python entry point, the
data source, and the fields compared. Depending on the estimator, fields
include:

- coefficients and standard errors;
- t/z statistics, p-values, and confidence intervals;
- sample size and degrees of freedom;
- R-squared, RMSE, F statistics, log likelihood, and deviance;
- estimator-specific outputs such as absorbed degrees of freedom, ATT
  aggregations, or RD effective sample counts.

The standard acceptance target is relative deviation below `1e-6`.
Documented numerical or architectural exceptions are described in the
[ADRs](docs/adr/) and [known issues](docs/release/known-issues.md).

## Reproducible Validation Cases

Users with Stata 17 can run the 10 self-contained public cases:

```bash
pytest tests/stata_validation/ -v -s
```

The suite creates deterministic synthetic data and Stata input files at run
time. A missing or non-17 Stata executable fails the prerequisite check with
an explicit reason. If a required community command is unavailable, only its
case skips. Stata is needed only for these comparisons, not for normal
package use.

See [Reproducible Stata Validation](docs/validation/reproducible-validation.md) for
coverage and environment requirements.

## Command Coverage

| Family | Public commands | Evidence |
|---|---|---|
| Linear / FE | `regress`, `xtreg_fe`, `areg`, `reghdfe` | Synthetic and public real-data Stata 17 comparisons |
| IV | `ivregress_2sls`, `ivreghdfe` | Synthetic and public real-data Stata 17 comparisons |
| Binary / count | `logit`, `probit`, `poisson`, `ppmlhdfe` | Synthetic and public real-data Stata 17 comparisons |
| DID | `did_imputation`, `eventstudyinteract`, `csdid` | Numerical and functional Stata validation |
| RD | `rdrobust` | Synthetic and public real-data Stata 17 comparisons |

All 14 public commands have synthetic and real-data evidence for their
documented support surface. Exact option boundaries are listed in the
[command support matrix](docs/command-support-matrix/README.md).

## Evidence Index

- [Validation overview](docs/validation/overview.md)
- [Validation policy](docs/validation/validation-policy.md)
- [Evidence matrix](docs/validation/evidence-matrix.md)
- [Dataset registry](docs/validation/dataset-registry.md)
- [Machine-readable evidence summary](research/results/validation/evidence-summary.json)
- [Human-readable evidence summary](research/results/validation/evidence-summary.md)
