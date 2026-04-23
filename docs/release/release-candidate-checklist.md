# Release Candidate Checklist

This checklist governs the transition from development mainline to open-source release candidate. It must be completed before any public release tag is created.

**Current version:** 0.1.5 (Alpha)  
**Last updated:** 2026-04-23

---

## 1. Pre-Export Checks (Main Repository)

### 1.1 Version and Metadata

- [ ] `pyproject.toml` version matches `src/stataflow/__init__.py::__version__`
- [ ] `pyproject.toml` classifiers and dependencies are up to date
- [ ] `README.md` and `README.zh-CN.md` installation instructions reference the correct package name (`StataFlow`)
- [ ] No absolute Windows paths in any Markdown file
- [ ] All `.md` files are UTF-8 encoded (no BOM, no replacement characters)

### 1.2 Documentation Consistency

- [ ] `docs/command-support-matrix/README.md` status legend matches per-command matrices
- [ ] Per-command matrices do not claim support for parameters that are hard-rejected in code
- [ ] `README.md` "What is not yet supported" matches current implementation reality
- [ ] `docs/release/known-issues.md` and `docs/release/open-source-alpha-status.md` are consistent with each other and with the code
- [ ] `docs/cookbook.md` and `docs/cookbook.zh-CN.md` examples use data paths that exist in the open-source repo
- [ ] Chinese and English user-facing docs convey equivalent scope and limitations

### 1.3 Tests and Examples

- [ ] `pytest tests/ -v --ignore=tests/golden/` passes with 0 failures
- [ ] All `examples/demo_*.py` scripts run without error
- [ ] `scripts/validation/run_validation_all.py` produces expected artifacts (if run)

### 1.4 Export Script Safety

- [ ] `python scripts/release/export_open_source.py --dry-run` executes without errors
- [ ] Dry-run does not create directories or files
- [ ] Dangerous target paths (same as source, inside source, parent of source) are rejected

---

## 2. Export Execution

```bash
python scripts/release/export_open_source.py --force
```

- [ ] Command completes with no unexpected errors
- [ ] Target directory is `../StataFlow_open_source` (or explicitly overridden)

---

## 3. Post-Export Checks (Open-Source Mirror)

### 3.1 Content Integrity

- [ ] No closed files leaked (audit: `docs/audit/`, `docs/tasks/`, `workspace/`, `tests/golden/`, secrets)
- [ ] No `__pycache__/`, `.pytest_cache/`, or build artifacts present
- [ ] `scripts/release/export_open_source.py` is present in the exported repo
- [ ] File count is within expected range (current baseline: 168 non-git files)

### 3.2 Verification in Clean Environment

- [ ] `pip install -e .` succeeds in the exported repo
- [ ] `pytest tests/ -v --ignore=tests/golden/` passes with 0 failures
- [ ] `python examples/demo_regress.py` runs
- [ ] `python examples/demo_reghdfe.py` runs
- [ ] `python examples/demo_ppmlhdfe.py` runs
- [ ] `python examples/demo_ivregress_2sls.py` runs

### 3.3 Git Hygiene (if tagging)

- [ ] `.gitignore` covers standard Python artifacts
- [ ] No large binary files accidentally committed
- [ ] Commit message references the checklist version

---

## 4. Documentation Risk Review

Before tagging, confirm the following public statements are still true:

| Claim | Verification Source |
|-------|---------------------|
| "Stata 17 is the default ground truth" | `docs/architecture/stata-compatibility.md` |
| "Unsupported parameters are hard-rejected" | Wrapper code + tests |
| "Base commands are Stable" | Support matrices + dual-run evidence |
| "Community commands are Alpha/Alpha-Partial" | Support matrices + test coverage |
| Two-way clustering only on `regress` | `docs/command-support-matrix/regress.md` + `tests/test_compat_stata_linear.py` |
| `aweight` only | Wrapper parameter lists |

---

## 5. Known Risk Confirmation

The following risks are acknowledged and explicitly **not** treated as release blockers for Alpha, but must be re-evaluated before Beta:

- [ ] Community command completeness gaps are documented in per-command support matrices
- [ ] Post-estimation (`predict`, `margins`) is only on core estimator layer
- [ ] Multi-way clustering is only on `regress`
- [ ] Weights beyond `aweight` are not supported
- [ ] Golden dual-run tests require local Stata 17 and are excluded from open-source CI

---

## Sign-off

| Role | Name | Date | Signature / Commit |
|------|------|------|-------------------|
| Executor | | | |
| Codex Review | | | |

---

*This checklist is versioned with the repository. Any change to release gating rules requires a PR and Codex approval.*
