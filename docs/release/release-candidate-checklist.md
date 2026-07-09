# Release Candidate Checklist

This checklist governs the transition from the development repository to the public open-source release candidate. It must be completed before a public release tag is treated as final.

**Current package version:** 1.1.0 (Stable)
**Release-candidate sync:** v1.2.0+ correctness hardening
**Last updated:** 2026-07-09

---

## 1. Pre-Export Checks (Main Repository)

### 1.1 Version and Metadata

- [x] `pyproject.toml` version matches `src/stataflow/__init__.py::__version__` (`1.1.0`).
- [x] `pyproject.toml` classifiers and dependencies are up to date for Python 3.10-3.12.
- [x] README installation instructions reference the public package name (`StataFlow`).
- [x] Public README files are UTF-8 readable.
- [x] Public docs distinguish the `1.1.0` package version from the v1.2.0+ correctness-hardening sync.

### 1.2 Documentation Consistency

- [x] `README.md` and `README.zh-CN.md` describe the current command surface and validation stance.
- [x] `docs/release/open-source-status.md` records the July 2026 hardening sync and current verification gates.
- [x] `docs/release/known-issues.md` records remaining support boundaries and known structural residuals.
- [x] `docs/cookbook.md` and `docs/cookbook.zh-CN.md` remain in the export manifest.
- [x] Unsupported options remain documented as hard-rejected rather than silently ignored.

### 1.3 Tests and Examples

- [x] `pytest tests/ -q --ignore=tests/golden/ --ignore=tests/audit_v1_3` passed: `405 passed, 76 warnings`.
- [x] `pytest tests/audit_v1_3 -q` passed: `95 passed, 19 warnings`.
- [x] `pytest tests/golden --collect-only -q` passed: `839 tests collected`.
- [x] `python -m compileall -q src/stataflow tests/golden tests/audit_v1_3` passed.
- [x] `python examples/demo_regress.py` passed.
- [x] `python examples/demo_reghdfe.py` passed.
- [x] `python examples/demo_ppmlhdfe.py` passed.
- [x] `python examples/demo_ivregress_2sls.py` passed.

### 1.4 Export Script Safety

- [x] `python scripts/release/export_open_source.py --dry-run --target-root '..\StataFlow_open_source_dryrun'` passed.
- [x] Dry-run selected 150 public files and reported 0 orphan removals.
- [x] Dangerous target paths remain rejected by `validate_target_path()`.

---

## 2. Export Execution

Target repository:

```bash
python scripts/release/export_open_source.py --force --target-root '..\StataFlow_open_source'
```

- [x] Command completed with no unexpected errors.
- [x] Target directory is the public mirror repository (`..\StataFlow_open_source`).
- [x] Public mirror diff contains only manifest-selected public files.
- [x] Public mirror branch is pushed to GitHub as `codex/public-hardening-sync`.

---

## 3. Post-Export Checks (Open-Source Mirror)

### 3.1 Content Integrity

- [x] No internal-only files leaked: `workspace/`, `.claude/`, `session_restore/`, `docs/audit/`, `tests/golden/`, `tests/audit_v1_3/`, Stata output artifacts, secrets.
- [x] No `__pycache__/`, `.pytest_cache/`, or build artifacts present.
- [x] `scripts/release/PRE_PUBLIC_SYNC_CHECKLIST.md` is present; internal export executables remain internal-only unless deliberately exposed.
- [x] File count remains close to the manifest baseline.

### 3.2 Verification in Public Mirror

- [x] Existing environment confirmed usable with public mirror import check (`stataflow.__version__ == "1.1.0"`).
- [x] `pytest tests/ -q --ignore=tests/golden/ --ignore=tests/audit_v1_3` passed in the public mirror: `397 passed, 76 warnings`.
- [x] Public example smoke tests passed:
  - [x] `python examples/demo_regress.py`
  - [x] `python examples/demo_reghdfe.py`
  - [x] `python examples/demo_ppmlhdfe.py`
  - [x] `python examples/demo_ivregress_2sls.py`
- [x] `python -m pip wheel . --no-deps -w dist_tmp` passed; generated `dist_tmp` was removed after verification.

### 3.3 GitHub Release Hygiene

- [x] Public sync branch is pushed.
- [x] Draft PR is opened against `main`: [#4](https://github.com/ZhenHaoFu810/StataFlow/pull/4).
- [x] Release-candidate tag is created only after the public mirror commit is verified: `v1.1.0-public-hardening-20260709`.
- [ ] Final release tag is created only after PR review/merge decision.

---

## 4. Documentation Risk Review

Before final tagging, confirm the following public statements are still true:

| Claim | Verification source |
|-------|---------------------|
| Stata 17 is the default ground truth | Architecture docs and validation harness |
| Unsupported parameters are hard-rejected | Wrapper code and tests |
| Base commands are Stable | Support matrices and dual-run evidence |
| Community commands are Beta subsets | Support matrices and known issues |
| Two-way clustering support is bounded | Support matrices and VCE tests |
| `aweight` is the only public weight type | Wrapper parameter lists and golden skips |

---

## 5. Known Risk Confirmation

The following risks are acknowledged and are not treated as blockers for this release-candidate sync:

- [x] Community commands remain verified high-frequency subsets, not full Stata command clones.
- [x] Post-estimation is primarily exposed through the core estimator layer.
- [x] Three-way and higher multi-way clustering is not supported.
- [x] Weights beyond `aweight` are not supported.
- [x] Golden dual-run tests require local Stata 17 and are excluded from public CI.
- [x] HDFE/PPML/IV-HDFE structural residuals are documented in `known-issues.md`.
- [x] One Stata batch timeout was observed during local audit and did not reproduce.

---

## Sign-off

| Role | Name | Date | Signature / Commit |
|------|------|------|--------------------|
| Executor | Codex | 2026-07-09 | pending public sync commit |
| Codex Review | Codex | 2026-07-09 | pending PR |

---

Any change to release gating rules should be reviewed before final release tagging.
