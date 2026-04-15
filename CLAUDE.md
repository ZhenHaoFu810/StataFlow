# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Stata2Python** (`statapy`) is an econometrics toolkit that reproduces Stata 17 estimation results in Python with high precision. **Stata 17 is the default ground truth.** Every public capability must have Stata-Python dual-run evidence.

## Common Commands

### Installation
```bash
pip install -e .
```

### Running Tests
```bash
# Unit and integration tests (exclude golden dual-run tests)
pytest tests/ -v --ignore=tests/golden/

# Run a specific golden test
pytest tests/golden/test_p1_ols_basic.py -v

# Run all golden tests
pytest tests/golden/ -v

# Legacy dual-run script (requires Stata 17)
python tests/golden/run_dual_test.py
```

### Stata Execution
- **Executable:** `D:\Software\Stata17\StataMP-64.exe`
- **Batch command:** `cmd /c "cd /d <output_dir> && StataMP-64.exe /e do <do_file>"`
- All Stata outputs (`.do`, `.log`, `.dta`) must be written to `stata/output/` or `stata/cases/` under the project directory. Never use temp directories or `C:\`.

## Architecture (4-Layer Kernel)

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| `stata_runner` | Calls local Stata 17, generates `.do` files, collects logs | `src/statapy/stata_runner/runner.py` |
| `result_spec` | Unified result schema for Stata-Python comparison | `src/statapy/results/result.py` |
| `estimators.linear` | OLS, weighted OLS, robust, cluster, single FE | `src/statapy/estimators/ols.py`, `src/statapy/estimators/fe.py` |
| `testing_harness` | Drives dual-run, field-level comparison, diff reports | `tests/golden/run_dual_test.py`, `tests/golden/test_utils.py` |

**Dependency direction:** `estimators.linear → result_spec`; `testing_harness → stata_runner + result_spec + estimators.linear`

**Layer boundaries:**
- `stata_runner` must not contain estimation algorithms or comparison logic.
- `estimators` must not directly execute Stata or embed test gold standards.
- `testing_harness` must not modify estimator code.

## Code Structure

- `src/statapy/` — Main Python package
  - `estimators/` — Core estimators (`OLS`, `FixedEffectsOLS`)
  - `results/` — `ResultSchema` dataclasses
  - `stata_runner/` — Stata batch runner
- `tests/golden/` — Stata-Python dual-run tests and utilities
- `stata/cases/` — Stata `.do` files and test data
- `stata/output/` — Stata execution outputs
- `docs/` — Governance docs (architecture, roadmap, backlog, tasks)
- `workspace/current-task/` — Active task instructions and reports

## Development Workflow

### Pre-Task Reading List
Always read in this order before coding:
1. `workspace/current-task/INSTRUCTIONS.md` (if it exists)
2. `docs/project-charter.md`
3. `docs/architecture/overview.md`
4. `docs/architecture/public-api.md`
5. `docs/architecture/stata-compatibility.md`
6. `docs/roadmap.md`
7. `docs/backlog.md`
8. Relevant `docs/tasks/*.md` task card

### Execution Order
1. Tests first → 2. Minimal code → 3. Dual-run validation → 4. Backfill evidence and status

### Branch Conventions
- `main` — Stable line
- `codex/<topic>` — Codex maintains docs, governance, architecture
- `claude/<topic>` — Claude Code implements code and tests
- Create `claude/<topic>` from the latest stable baseline.

## Stata-Python Dual-Run Requirements

Every new command requires:
- **Synthetic/controlled cases** (formula, degrees of freedom, sample screening, edge cases)
- **Real public dataset cases** (at least one)
- **Field-level comparison** with relative tolerance `< 1e-6` for: coefficients, standard errors, t-statistics, R-squared, RMSE, F-statistic, degrees of freedom

Use `tests/golden/test_utils.py` (`parse_stata_log`, `tolerance_close`) as the standard comparison toolkit.

## Alignment Rules

- **Sample screening:** Drop any row with missing values in y, x, weights, cluster, FE, or IV variables.
- **df_model convention:** Stata excludes the constant term. Python follows: `df_model = k - 1` if `add_constant` else `k`.
- **aweight normalization:** Normalize so `sum(w) = N` after missing drop.
- **Log parsing:** Stata displays numbers `< 1` as `.9318` (no leading zero). Parser must add the leading zero.

## Escalation Rules (Stop and Report)

Escalate to Codex when any of the following occur:
- Unexplainable deviation between Stata and Python results
- Public API needs new or changed parameters
- `ResultSchema` needs new fields
- Real-data and synthetic alignment conclusions conflict

## What Claude Code Must Not Do

- Do not expand command coverage without documentation and research archives.
- Do not modify public API semantics without an ADR.
- Do not accept "statistical equivalence" without explicit Codex approval.
- Do not skip tests or replace field-level comparison with human observation.
- Do not modify `docs/project-charter.md`, architecture principles, or statistical equivalence criteria.
