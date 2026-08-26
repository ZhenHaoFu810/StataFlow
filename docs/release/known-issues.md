# Known Issues

This page records the non-blocking limitations of the current StataFlow
release. The [command support matrix](../command-support-matrix/README.md) is the
authoritative option-by-option reference.

## Community Command Coverage

Community commands implement documented, high-frequency subsets rather than
every option provided by the corresponding Stata package.

| Command | Status | Largest remaining gap |
|---|---|---|
| `reghdfe` | Beta | 3-way+ clustering, mobility-group DoF, `group`/`individual` FE |
| `ivreghdfe` | Beta | CUE, `partial`/`fwl`, `orthog`/`endogtest`/`redundant` |
| `ppmlhdfe` | Beta | Full `separation` methods, 3-way+ clustering, `keepsingletons` |
| `did_imputation` | Beta | `window`, `minn`, `hbalance`, `leaveout`, `avgeffectsby` |
| `eventstudyinteract` | Beta | `covariates`, `window`, `minn`, complete matrix returns |
| `csdid` | Beta | `method="ipw"`, `gtcontrol`, `longdiff` |
| `rdrobust` | Beta | `deriv > 0`; exact `rdplot` bin-selection alignment |

## Documented Numerical Differences

These boundaries apply outside the strict July 2026 release snapshot or to
display/postestimation paths not represented by the aggregate 40-case table.

| Area | Observed difference | Public boundary |
|---|---:|---|
| `reghdfe` / `ivreghdfe` constant SE under 2-way clustering | about 2-16% | Governed by [ADR-0003](../adr/ADR-0003-lsdv-cons-se-under-multiway-cluster.md) |
| `ivreghdfe` clustered `stdp` when clusters nest all FEs | about 0.28% | `rtol=5e-3` |
| `ppmlhdfe` Pearson/deviance/working residuals | about 0.35% | `rtol=5e-3` |
| `reghdfe` MAP clustered slope SE when clusters nest an FE | about 0.5% | `rtol=5e-3` |
| `rdrobust` fuzzy RD SE | up to 5% synthetic; 0.5% Senate | Completed comparison, outside strict release aggregate |
| `rdrobust` cluster / nearest-neighbor cluster SE | up to 3% | Completed comparison, outside strict release aggregate |
| `rdrobust` automatic bandwidth paths | estimates up to 0.5%; bandwidths up to 1% | Completed comparison, outside strict release aggregate |

## Unsupported Surfaces

- Three-way and higher clustering is not supported.
- Weight support is command-specific. Only commands that document `aweight`
  accept analytic weights; other Stata weight types are not generally
  available.
- Most Stata-compatible estimation wrappers return `ResultSchema`; `csdid()`
  returns a fitted `CSDID` model. Use the core estimator layer for prediction
  and margins workflows that require a fitted model.
- `rdrobust` kink designs (`deriv > 0`) remain unsupported.
- The `rdplot` companion is available, but its bin-selection algorithm is not
  claimed to reproduce Stata exactly.

## Runtime Behavior

When a two-way clustered covariance meat matrix is not positive
semi-definite, affected HDFE estimators emit `RuntimeWarning` and apply the
documented PSD correction. See
[ADR-0004](../adr/ADR-0004-psd-fix-architecture.md).

Unsupported arguments raise `ValueError` or `NotImplementedError`; they are
never silently ignored.

## Validation Boundary

The July 2026 Stata 17 comparison snapshot contains `40/40` passing numerical
cases plus one DID functional check. Full local Stata validation checks
completed with `856 passed, 12 skipped`; the public suite completed `10/10`
reproducible validation cases. See [VALIDATION.md](../../VALIDATION.md) for
the formula, family maxima, and evidence links.
