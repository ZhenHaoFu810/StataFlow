# Release Candidate Checklist

This checklist governs the transition from development mainline to open-source release candidate. It must be completed before any public release tag is created.

**Current version:** 1.1.0 (Stable)
**Last updated:** 2026-06-23

---

## 1. Pre-Export Checks (Main Repository)

### 1.1 Version and Metadata

- [x] `pyproject.toml` version matches `src/stataflow/__init__.py::__version__`
- [x] `pyproject.toml` classifiers and dependencies are up to date
- [x] `README.md` and `README.zh-CN.md` installation instructions reference the correct package name (`StataFlow`)
- [x] No absolute Windows paths in any Markdown file
- [x] All `.md` files are UTF-8 encoded (no BOM, no replacement characters)

### 1.2 Documentation Consistency

- [x] `docs/command-support-matrix/README.md` status legend matches per-command matrices
- [x] Per-command matrices do not claim support for parameters that are hard-rejected in code
- [x] `README.md` "What is not yet supported" matches current implementation reality
- [x] `docs/release/known-issues.md` and `docs/release/open-source-status.md` are consistent with each other and with the code
- [x] `docs/cookbook.md` and `docs/cookbook.zh-CN.md` examples use data paths that exist in the open-source repo
- [x] Chinese and English user-facing docs convey equivalent scope and limitations

### 1.3 Tests and Examples

- [x] `pytest tests/ -v --ignore=tests/golden/ --ignore=tests/audit_v1_3` passes with 0 failures (392 passed)
- [x] All `examples/demo_*.py` scripts run without error
- [x] `scripts/validation/run_validation_all.py` produces expected artifacts (if run)

### 1.4 Export Script Safety

- [x] `python scripts/release/export_open_source.py --dry-run` executes without errors
- [x] Dry-run does not create directories or files
- [x] Dangerous target paths (same as source, inside source, parent of source) are rejected

---

## 2. Export Execution

```bash
python scripts/release/export_open_source.py --force
```

- [x] Command completes with no unexpected errors
- [x] Target directory is `../StataFlow_open_source` (or explicitly overridden)

---

## 3. Post-Export Checks (Open-Source Mirror)

### 3.1 Content Integrity

- [x] No closed files leaked (audit: `docs/audit/`, `docs/tasks/`, `workspace/`, `tests/golden/`, `tests/audit_v1_3/`, `.claude/`, `session_restore/`, secrets)
- [x] No `__pycache__/`, `.pytest_cache/`, or build artifacts present
- [x] `scripts/release/PRE_PUBLIC_SYNC_CHECKLIST.md` is present in the exported repo; export executables remain internal only
- [x] File count is within expected range (current baseline: 168 non-git files)

### 3.2 Verification in Clean Environment

- [x] `pip install -e .` succeeds in the exported repo
- [x] `pytest tests/ -v --ignore=tests/golden/ --ignore=tests/audit_v1_3` passes with 0 failures (392 passed)
- [x] `python examples/demo_regress.py` runs
- [x] `python examples/demo_reghdfe.py` runs
- [x] `python examples/demo_ppmlhdfe.py` runs
- [x] `python examples/demo_ivregress_2sls.py` runs

### 3.3 Git Hygiene (if tagging)

- [x] `.gitignore` covers standard Python artifacts, internal agent/session state, and internal audit/tests
- [x] `scripts/release/open_source_manifest.yml` exports only the public pre-sync checklist under `scripts/release/`
- [x] No large binary files accidentally committed
- [ ] Commit message references the checklist version

---

## 4. Documentation Risk Review

Before tagging, confirm the following public statements are still true:

| Claim | Verification Source |
|-------|---------------------|
| "Stata 17 is the default ground truth" | `docs/architecture/stata-compatibility.md` |
| "Unsupported parameters are hard-rejected" | Wrapper code + tests |
| "Base commands are Stable" | Support matrices + dual-run evidence |
| "Community commands are Beta" | Support matrices + test coverage |
| Two-way clustering on `regress`, `reghdfe`, `ivreghdfe`, `ppmlhdfe` | Support matrices + tests |
| `aweight` only | Wrapper parameter lists |

---

## 5. Known Risk Confirmation

The following risks are acknowledged and explicitly **not** treated as release blockers for Beta, but must be re-evaluated before v1.0.0:

- [x] Community command completeness gaps are documented in per-command support matrices
- [x] Post-estimation (`predict`, `margins`) is only on core estimator layer
- [x] Three-way and higher multi-way clustering is not supported
- [x] Weights beyond `aweight` are not supported
- [x] Golden dual-run tests require local Stata 17 and are excluded from open-source CI
- [x] `_cons` SE under 2-way cluster has known structural residual (~2-16%) documented in ADR-0003

---

## Sign-off

| Role | Name | Date | Signature / Commit |
|------|------|------|-------------------|
| Executor | Claude Code | 2026-04-30 | |
| Codex Review | | | |

---

*This checklist is versioned with the repository. Any change to release gating rules requires a PR and Codex approval.*
