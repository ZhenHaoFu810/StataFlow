# Changelog

All notable public changes to StataFlow are documented here.

## 1.3.1 - 2026-08-25

### Changed

- Expanded the tested Python compatibility range to Python 3.10-3.14.
- Updated the NumPy version range for current Python releases.

### Packaging

- Added clean wheel checks for supported Python versions.
- Added an unpinned PyPI installation check for post-release validation.

## 1.3.0 - 2026-07-28

### Added

- Command-aware full and compact Stata-style displays for all 14 public
  estimation commands.
- Escaped HTML output through `to_html()` and automatic Jupyter rich display.
- Typed `IVInfo`, `DIDInfo`, and `RDInfo` result sections, plus model, panel,
  test, convergence, and iteration metadata.

### Changed

- `display()` and `summary()` now default to complete adaptive output with 95%
  confidence intervals. Existing positional `width` and `show_ci` calls remain
  valid.
- Text and HTML renderers consume one renderer-neutral `DisplayDocument`.
- IV diagnostics and command-specific result metadata now survive JSON
  serialization.

### Fixed

- Fixed-effects and IV family identifiers now select their command-aware
  displays.
- `rdrobust` reports the fitted kernel instead of falling back to
  `triangular`.

## 1.2.0 - 2026-07

### Added

- A consistent display and result surface for `csdid`, while preserving the
  existing default return type.
- Nine deterministic demo scripts covering all 14 public Stata-compatible
  commands.
- Ten self-contained reproducible validation cases spanning every command
  family. They generate synthetic data at run time and compare field-level
  results with Stata 17.
- Public contribution, security, conduct, validation, support-matrix, and ADR
  documentation.
- The `py.typed` marker for consumers of package type information.

### Changed

- Public documentation now uses one 1.2.0 support vocabulary across English
  and Chinese guides.
- Unsupported parameters continue to fail explicitly instead of being
  silently ignored.
- DID cohort and time labels accept integer-valued nullable inputs while
  retaining strict time-unit validation.
- `eventstudyinteract` bins event times outside the requested window at its
  endpoints.
- `ResultSchema` display metadata no longer fabricates formula or ordinary
  R-squared fields for estimators where they do not apply.
- Unfitted estimators now use a consistent error message.

### Fixed

- `xtreg_fe(..., vce="robust")` finite-sample scaling.
- `areg(..., vce="cluster")` absorbed-degree-of-freedom adjustment.
- `ivreghdfe(..., vce="cluster")` clustered 2SLS covariance scaling.
- DID estimators now reject incompatible cohort/time units and empty
  estimation samples.
- `rdrobust` nearest-neighbor residual construction for repeated mass points.

### Validation

- Stata 17 comparison snapshot: `40/40` numerical cases passed, plus one DID
  functional check.
- Maximum relative deviations by family are recorded in
  `research/results/validation/evidence-summary.json`.
- Full local Stata validation checks: `856 passed, 12 skipped`.
- Public reproducible suite: `10/10` cases passed with Stata 17.
- Nine example scripts passed and exercise all 14 public commands.

## 1.1.1 - 2026-07

### Fixed

- Corrected robust and clustered covariance paths for `xtreg_fe`, `areg`, and
  `ivreghdfe`.
- Added strict DID cohort/time compatibility and empty-sample guards.
- Corrected `rdrobust` nearest-neighbor handling at mass points.

This patch preserved the 1.1 public API and was incorporated into 1.2.0.

## 1.1.0 - 2026-06

### Added

- Advanced HDFE support, including MAP absorption, individual slopes, and
  Driscoll-Kraay covariance estimates.
- Expanded IV estimators and diagnostics, GLM covariance choices, DID
  options, prediction types, and `estat` helpers.
- Broader factor-variable and analytic-weight support.

### Changed

- Public support boundaries and known numerical differences were documented
  per command.

No breaking API changes were introduced relative to 1.0.0.
