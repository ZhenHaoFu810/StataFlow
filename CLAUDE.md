# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StataFlow (`stataflow`) is a Python econometrics toolkit that mirrors a focused subset of Stata 17 commands. It provides both a native Python estimator API (`stataflow.estimators`) and a Stata-compatible wrapper layer (`stataflow.compat.stata`). The project enforces strict field-level dual-run verification against Stata 17.

## Common Commands

### Installation (Development)
```bash
pip install -e ".[dev]"
```
This installs the package in editable mode with `pytest` and `pytest-cov`.

### Running Tests
```bash
# Run all unit tests (excludes golden/Stata dual-run tests)
python -m pytest tests/ -v --ignore=tests/golden/

# Run a specific test file
python -m pytest tests/test_compat_stata_linear.py -v

# Run with coverage
python -m pytest tests/ -v --cov=stataflow --ignore=tests/golden/
```

**Note:** Tests in `tests/golden/` and some `test_rdrobust.py` cases require a local Stata 17 installation and pre-generated `.dta` output files in `stata/output/`. These are excluded from CI.

### Build
```bash
python -m pip wheel . --no-deps -w dist
```

### Running Examples
```bash
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

## Architecture

The codebase follows a four-layer architecture (documented in `docs/architecture/overview.md`):

1. **`core` (`src/stataflow/estimators/`)** — Native Python estimators with a unified fitting interface and stable result schemas. Examples: `OLS`, `AbsorbingOLS`, `IV2SLS`, `PPMLHDFE`.
2. **`compat.stata` (`src/stataflow/compat/stata/`)** — Stata command wrappers that delegate to `core` but use Stata-like naming, defaults, and signatures. Examples: `regress()`, `reghdfe()`, `ivregress_2sls()`.
3. **`research` (`research/`)** — Rule archives, public validation datasets, and source documentation. Research artifacts must precede implementation.
4. **`validation` (`scripts/validation/`, `tests/golden/`)** — Synthetic and real-data dual-run verification against Stata 17.

### Dependency Direction
- `compat.stata` depends on `core`.
- `validation` depends on `core` and `compat.stata`.
- `research` does not depend on estimators but provides the rule basis for them.

**Critical invariant:** Do not let `compat.stata` constraints leak backward into `core` internal structure.

## Key Conventions

### Stata Compatibility & Validation
- Target alignment version is **Stata 17**.
- Unsupported parameters are **hard-rejected with `ValueError`** — silently ignoring them is not allowed.
- Every command requires **dual validation** before being considered complete:
  - **Synthetic/controlled cases** — lock formulas, degrees of freedom, edge cases, sample filtering, and cluster/FE corrections.
  - **Real public datasets** — lock field-level alignment in realistic research scenarios.
- Research archives must be created **before** implementing a new command. See `docs/architecture/stata-compatibility.md` for the full policy.

### Result Schema
All estimators and wrappers return a `ResultSchema` object (`src/stataflow/results/result.py`). This is the stable public interface. Fields like `params`, `bse`, `pvalues`, `conf_int`, `nobs`, `df_model`, `df_resid`, and `rsquared` are standard.

### Sample Handling
- Any row with missing values in variables participating in estimation (dependent variable, regressors, weights, cluster, FE absorb, or instruments) **must be dropped**.
- The sample mask must be recorded in the result object.

### Naming
- Import name: `stataflow` (lowercase).
- PyPI name: `StataFlow`.

## Important Paths

| Path | Purpose |
|------|---------|
| `src/stataflow/__init__.py` | Public API exports for both core estimators and Stata wrappers |
| `src/stataflow/estimators/__init__.py` | Core estimator exports |
| `src/stataflow/compat/stata/__init__.py` | Stata wrapper exports |
| `docs/command-support-matrix/README.md` | Per-command support quick reference |
| `docs/architecture/stata-compatibility.md` | Stata alignment rules and research requirements |
| `docs/validation/validation-policy.md` | Validation policy, hard fields, and tolerance rules |
| `research/data/public/` | Public datasets used for validation |
| `stata/cases/` | Stata `.do` case files for dual-run tests |
| `stata/output/` | Stata-generated output files required by some tests |

## CI Behavior

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on Python 3.10/3.11/3.12 on Ubuntu:
1. Installs with `pip install -e ".[dev]"`
2. Runs import smoke test
3. Runs `pytest tests/ -v --ignore=tests/golden/`
4. Runs the four example scripts
5. Builds the wheel

Golden tests and any test requiring Stata 17 are intentionally excluded from CI.
