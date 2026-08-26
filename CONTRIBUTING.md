# Contributing to StataFlow

Thank you for your interest in contributing to StataFlow. This project has a
specific goal — reproducing Stata 17 estimation results in Python with
field-level validation — so contributions follow a stricter process than a
typical statistics library. Please read this guide before opening a pull
request.

## Scope

StataFlow is not a generic statistics library. Every public capability must
be validated through field-level Stata 17 comparison.
Contributions that add estimation features without validation evidence cannot
be merged.

## Research before implementation

No new public command or estimator option may be implemented without a
research archive. Before writing code:

1. Identify the rule source for every behavior you intend to reproduce —
   either the official Stata manual or public community source code (e.g.,
   published `reghdfe`/`csdid` source).
2. Document the source-to-Python mapping: formulas, degrees-of-freedom
   conventions, sample-screening rules, and defaults.
3. Open an issue describing the planned work and the research basis, so the
   design can be reviewed before implementation starts.

## Tests first

Write tests before (or alongside) implementation code:

- **Synthetic / controlled cases** — formula checks, degrees of freedom,
  sample screening, and edge cases with deterministic seeded fixtures
  (`np.random.default_rng(seed)`).
- **Real public datasets** — field-level comparison against Stata 17 on openly
  available data where the capability changes estimation behavior.

Field-level comparisons must use relative tolerance `< 1e-6` for coefficients,
standard errors, test statistics, R-squared, RMSE, F-statistics, and degrees
of freedom.

## Stata-required validation

Stata validation cases compare Python output against Stata 17 logs and require
a local Stata 17 installation. If you do not have Stata, you can still
contribute: write the unit/integration tests and the reproducible validation
case, then note in your PR that a maintainer with local Stata must execute the
comparison. A command is complete only when both the synthetic and real-data
evidence lines pass.

Never weaken tolerances or replace field-level comparison with visual
inspection to make a test pass.

## Public and private evidence boundaries

- Public evidence (validation summaries, exported test fixtures, public
  datasets) must be reproducible from the public repository and must not
  reference private machine paths or proprietary data.
- Do not commit internal audit artifacts, raw Stata logs containing local
  paths, proprietary datasets, credentials, tokens, or Stata license
  information.
- Before opening a pull request, inspect the tracked files and public diff for
  private paths, generated logs, local environment details, and files unrelated
  to the proposed change.

## Code conventions

- Python 3.10+, Google-style docstrings, type hints on public functions.
- English for all code comments and docstrings.
- Missing values: drop any row with missing values in `y`, `x`, weights,
  cluster, fixed-effect, or IV variables before fitting (hard alignment rule
  with Stata).
- Stata-compatible wrappers capture unknown arguments via `**kwargs` and must
  raise `ValueError` (or `NotImplementedError` for known-but-unimplemented
  options). Never silently ignore unsupported parameters.

## Pull request checks

Every PR is gated by CI, which runs:

- `ruff check src tests` and `mypy src`
- Import smoke test
- Unit and integration tests:
  `pytest tests/`
- Reproducible Stata validation case collection check (no Stata execution)
- All nine example smoke scripts in `examples/` (no network, no Stata)
- sdist/wheel build and clean-wheel install verification

Before opening a PR, please run locally:

```bash
pip install -e ".[dev]"
pytest tests/ -v
pytest tests/stata_validation/ -v -s  # requires local Stata 17
for d in examples/demo_*.py; do python "$d"; done
```

## Reporting issues

Use GitHub Issues for bugs and feature requests. Include a minimal reproducible
example, the StataFlow version, and — where relevant — the Stata output you
expected. For security vulnerabilities, do not open a public issue; see
[SECURITY.md](SECURITY.md).

## Code of conduct

Participation in this project is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md).
