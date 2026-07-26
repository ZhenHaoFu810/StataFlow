# Validation Evidence

This directory contains the reviewed, public record of StataFlow's Stata 17
validation.

- `evidence-summary.md` provides the human-readable command, dataset, and
  evidence overview.
- `evidence-summary.json` provides the same evidence in machine-readable form,
  including the frozen Stata 1.2.0 release-validation aggregate.

The public repository also ships ten self-contained comparison cases under
`tests/stata_validation/`. They generate deterministic synthetic data, run
Stata 17 and Python locally, and compare coefficients and standard errors.
They require a licensed local Stata 17 installation; Stata itself is not
distributed with this project.

The larger development-time validation archive is intentionally not published.
Only reviewed aggregate results and reproducible public cases are included.
