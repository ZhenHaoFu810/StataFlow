# AGENTS.md — StataFlow

This file contains project-specific context for AI coding agents. Read this before modifying any code.

---

## 1. Project Overview

**StataFlow** (`stataflow`) is a Python econometrics toolkit that reproduces Stata 17 estimation results with high precision. It is not a generic stats library — every public capability must be field-level verified against Stata 17 through a dual-run (Stata + Python) validation framework.

The project provides two APIs:
- **Core estimator layer** (Python-native): `OLS`, `FixedEffectsOLS`, `AbsorbingOLS`, `IV2SLS`, `IVAbsorbingOLS`, `Logit`, `Probit`, `Poisson`, `PPMLHDFE`, `DIDImputation`, `EventStudyInteract`, `CSDID`, `RDRobust`.
- **Stata-compatible command layer** (`compat.stata`): `regress()`, `xtreg_fe()`, `areg()`, `reghdfe()`, `ivregress_2sls()`, `ivreghdfe()`, `logit()`, `probit()`, `poisson()`, `ppmlhdfe()`, `did_imputation()`, `eventstudyinteract()`, `csdid()`, `rdrobust()`.

**Default ground truth:** Stata 17.
**Current version:** 1.1.0.
**License:** MIT.

---

## 2. Technology Stack

- **Language:** Python 3.10+
- **Build system:** setuptools (via `pyproject.toml`)
- **Core dependencies:** NumPy >= 1.24, pandas >= 2.0, SciPy >= 1.10, PyYAML >= 6.0
- **Test framework:** pytest >= 7.0, pytest-cov >= 4.0
- **Stata integration:** Local Stata 17 executable (Windows batch execution via `StataMP-64.exe /e do`)
- **CI:** GitHub Actions (`.github/workflows/ci.yml`) running on Ubuntu with Python 3.10/3.11/3.12

There is no linting or formatting tool currently configured (no `ruff`, `black`, `flake8`, or `mypy` in `pyproject.toml`).

---

## 3. Build and Test Commands

### Installation (development)
```bash
pip install -e ".[dev]"
```

### Run unit and integration tests (fast, no Stata required)
```bash
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/audit_v1_3
```

`tests/audit_v1_3/` contains internal dual-run audits with documented known findings and is excluded from CI gate checks.

### Run golden dual-run tests (requires Stata 17)
```bash
pytest tests/golden/ -v
```

### Run a specific golden test
```bash
pytest tests/golden/test_p1_ols_basic.py -v
```

### Run example smoke tests (run in CI)
```bash
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

### Build wheel
```bash
python -m pip wheel . --no-deps -w dist_tmp
```

---

## 4. Project Structure

```
StataFlow/
├── pyproject.toml              # Package config (setuptools, pytest options)
├── src/stataflow/              # Main Python package
│   ├── __init__.py             # Exports core estimators + Stata compat commands
│   ├── estimators/             # Core estimation algorithms
│   │   ├── ols.py              # OLS (regress)
│   │   ├── fe.py               # FixedEffectsOLS (xtreg, fe)
│   │   ├── absorbing_ols.py    # AbsorbingOLS (areg, reghdfe)
│   │   ├── iv.py               # IV2SLS, IVAbsorbingOLS
│   │   ├── glm.py              # Logit, Probit, Poisson
│   │   ├── ppmlhdfe.py         # PPMLHDFE
│   │   ├── did_imputation.py   # DIDImputation (BJS)
│   │   ├── eventstudyinteract.py
│   │   ├── csdid.py            # Callaway-Sant'Anna DID
│   │   └── rdrobust.py         # Sharp RD local polynomial
│   ├── compat/stata/           # Stata command wrappers
│   │   ├── linear.py           # regress, xtreg_fe, areg
│   │   ├── hdfe.py             # reghdfe, ppmlhdfe
│   │   ├── iv.py               # ivregress_2sls, ivreghdfe
│   │   ├── glm.py              # logit, probit, poisson
│   │   ├── did.py              # did_imputation, eventstudyinteract, csdid
│   │   ├── rdrobust.py
│   │   └── factor_variables.py # Stata-style factor variable expansion
│   ├── results/                # Unified result schema
│   │   └── result.py           # ResultSchema, ModelInfo, FitInfo, etc.
│   ├── stata_runner/           # Stata 17 batch execution
│   │   └── runner.py           # StataRunner, find_stata_executable
│   └── postestimation.py       # predict, margins helpers
├── tests/                      # Test suite
│   ├── conftest.py             # pytest fixtures, project paths
│   ├── test_compat_stata_*.py  # Per-family wrapper tests (linear, hdfe, iv, glm, did)
│   ├── test_result_schema.py
│   ├── test_stata_runner.py
│   ├── test_smoke.py
│   └── golden/                 # Stata-Python dual-run tests
│       ├── test_utils.py       # parse_stata_log, tolerance_close helpers
│       ├── run_dual_test.py    # Legacy dual-run script
│       └── test_*.py           # Per-command golden tests
├── examples/                   # Runnable demo scripts
├── docs/                       # Governance and research docs
│   ├── architecture/           # overview.md, public-api.md, result-schema.md, stata-compatibility.md
│   ├── operations/             # executor-playbook.md, review-gates.md
│   ├── research/               # Per-command research archives (source maps, formulas)
│   ├── command-support-matrix/ # Per-command support matrices
│   ├── testing/                # testing-strategy.md, test-case-catalog.md
│   ├── project-charter.md      # Project goals and governance
│   ├── roadmap.md              # Long-term wave plan (Wave 0–12)
│   └── backlog.md              # Global task pool with status
├── stata/                      # Stata execution artifacts
│   ├── cases/                  # .do files and test data
│   └── output/                 # Stata logs and outputs
└── research/                   # Public datasets and validation evidence
    └── results/validation/     # Dual-run evidence archive
```

---

## 5. Architecture (4-Layer Kernel)

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| `stata_runner` | Calls local Stata 17, generates `.do` files, collects logs | `src/stataflow/stata_runner/runner.py` |
| `result_spec` | Unified result schema for Stata-Python comparison | `src/stataflow/results/result.py` |
| `estimators` | Core estimation algorithms (OLS, FE, IV, GLM, DID, RD) | `src/stataflow/estimators/` |
| `testing_harness` | Drives dual-run, field-level comparison, diff reports | `tests/golden/run_dual_test.py`, `tests/golden/test_utils.py` |

**Dependency direction:** `estimators` → `result_spec`; `testing_harness` → `stata_runner + result_spec + estimators`

**Layer boundaries (enforced by convention):**
- `stata_runner` must not contain estimation algorithms or comparison logic.
- `estimators` must not directly execute Stata or embed test gold standards.
- `testing_harness` must not modify estimator code.

---

## 6. Code Style Guidelines

- **Language:** All code comments, docstrings, and module-level strings are in **English**. Internal governance docs (`docs/`) are primarily in **Chinese**.
- **Docstrings:** Use Google-style docstrings with type annotations in signatures. Every public class and function must have a docstring.
- **Typing:** Use `from __future__ import annotations` and type hints (e.g., `Optional[str]`, `list[str]`).
- **Imports:** Standard library first, then third-party, then internal. Internal imports use absolute paths (`from stataflow.results.result import ...`).
- **Naming:**
  - Classes: `PascalCase` (e.g., `AbsorbingOLS`, `ResultSchema`)
  - Functions/variables: `snake_case` (e.g., `ivregress_2sls`, `df_resid`)
  - Private internals: `_leading_underscore`
- **Missing values / sample screening:** Drop any row with missing values in `y`, `x`, weights, cluster, FE, or IV variables before fitting. This is a hard alignment rule with Stata.
- **Unsupported arguments:** Stata-compatible wrappers use `**kwargs` to capture unknown arguments and must raise `ValueError` (or `NotImplementedError` for known-but-unimplemented options). **Never silently ignore unsupported parameters.**

---

## 7. Testing Instructions

### Dual-Run Validation (Mandatory for New Commands)
Every new public command requires **two lines of evidence**:
1. **Synthetic / controlled cases** — formula, degrees of freedom, sample screening, edge cases.
2. **Real public datasets** — field-level comparison against Stata 17 on openly available economic/financial data.

A command is only considered `done` when both lines pass and the source-to-Python mapping is documented.

### Tolerance
Field-level comparison must use relative tolerance `< 1e-6` for: coefficients, standard errors, t/z-statistics, R-squared, RMSE, F-statistic, and degrees of freedom.

### Standard comparison toolkit
Use `tests/golden/test_utils.py` (`parse_stata_log`, `tolerance_close`) as the standard comparison toolkit.

### Test file naming
- Unit/integration tests: `tests/test_<module>.py`
- Golden dual-run tests: `tests/golden/test_<wave>_<command>_<scenario>.py`

### Sample fixtures
Use `_make_ols_data()`, `_make_fe_data()` patterns (deterministic `np.random.default_rng(seed)`) for reusable synthetic fixtures.

---

## 8. Development Conventions

### Pre-task reading list (mandatory order)
1. `workspace/current-task/INSTRUCTIONS.md` (if it exists)
2. `docs/project-charter.md`
3. `docs/architecture/overview.md`
4. `docs/architecture/public-api.md`
5. `docs/architecture/stata-compatibility.md`
6. `docs/operations/executor-playbook.md`
7. `docs/operations/review-gates.md`
8. `docs/roadmap.md`
9. `docs/backlog.md`
10. Relevant `docs/tasks/*.md` task card

### Execution order
1. Tests first → 2. Minimal code → 3. Dual-run validation → 4. Backfill evidence and status

### Research-before-implementation
No new command may be implemented without a research archive in `docs/research/`. The archive must identify whether the rule source is "official Stata manual" or "public community source code".

### Branch conventions
- `main` — Stable line
- `codex/<topic>` — Codex maintains docs, governance, architecture
- `claude/<topic>` — Claude Code implements code and tests

### Reporting
When completing a task, update `workspace/current-task/REPORT.md` with: modified files, research archives added, synthetic/real-data test results, Stata dual-run results, risks, and any Codex escalation needed.

---

## 9. Key Alignment Rules with Stata 17

- **Sample screening:** Drop any row with missing values in `y`, `x`, weights, cluster, FE, or IV variables.
- **df_model convention:** Stata excludes the constant term. Python follows: `df_model = k - 1` if `add_constant` else `k`.
- **aweight normalization:** Normalize so `sum(w) = N` after missing drop.
- **Log parsing:** Stata displays numbers `< 1` as `.9318` (no leading zero). Parser must add the leading zero.
- **Factor variables:** Bare variables inside `#` / `##` are treated as continuous (matching common Stata usage).

---

## 10. Security Considerations

- The `stata_runner` executes Stata via `subprocess.run(..., shell=True)`. Only `.do` file content generated by the project itself (or tests) should be passed to `StataRunner.run_do_file()`.
- All Stata outputs (`.do`, `.log`, `.dta`) must be written to `stata/output/` or `stata/cases/` under the project directory. Never use temp directories or `C:\`.
- Do not commit Stata license information or proprietary datasets.

---

## 11. Governance and Escalation

- **Codex** — project goals, architecture, review gates, and statistical-dispute arbitration.
- **Claude Code** — implementation, testing, and evidence backfill.

**Escalate to Codex when:**
- Unexplainable deviation between Stata and Python results
- Public API needs new or changed parameters
- `ResultSchema` needs new fields
- Real-data and synthetic alignment conclusions conflict

**Agents must NOT:**
- Expand command coverage without documentation and research archives.
- Modify public API semantics without an ADR.
- Accept "statistical equivalence" without explicit Codex approval.
- Skip tests or replace field-level comparison with human observation.
- Modify `docs/project-charter.md`, architecture principles, or statistical equivalence criteria.

---

## 12. Stata Execution Details

- **Executable:** `D:\Software\Stata17\StataMP-64.exe`
- **Batch command:** `cmd /c "cd /d <output_dir> && StataMP-64.exe /e do <do_file>"`
- The runner uses `/e do` (non-interactive, no confirmation dialog) and writes `.log` files alongside the `.do` file.
- On Windows, `subprocess.STARTUPINFO` is used to hide the Stata window.

---

*Last updated: 2026-06-23*
