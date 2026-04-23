# Open-Source Update Log: 0.1.5

**Date:** 2026-04-23
**Scope:** changes between the previous public open-source snapshot and the current `0.1.5` release-candidate export

---

## Summary

`0.1.5` is the synchronized public release for the recent Package A-F/G cycle. Relative to the previous public open-source snapshot, this release brings the mirror, public docs, release materials, and package metadata back into alignment with the current tested implementation.

---

## What Changed

### 1. Correctness and API hygiene

- Fixed the `did_imputation(..., allhorizons=...)` behavior so the option is no longer a no-op.
- Corrected provenance / `stata_command` emission so option strings reflect the actual invocation.
- Unified package metadata under `0.1.5`.
- Cleaned several release-facing documentation drifts and command-surface mismatches.

### 2. HDFE family expansion

- `reghdfe`, `ivreghdfe`, and `ppmlhdfe` now document and expose the current **1+ FE** support boundary instead of the older `1-2 FE` wording.
- Added synthetic coverage for 3+ FE paths.
- Kept the limitation explicit that the implementation remains an HDFE subset rather than a full `reghdfe` / `ivreghdfe` / `ppmlhdfe` reproduction.

### 3. DID family completion

- Extended the public DID subset with documented `window` / `minn` support where implemented.
- Fixed `did_imputation` documentation so `allhorizons` matches actual behavior.
- Kept unsupported parameters explicitly rejected instead of silently ignored.

### 4. Cross-cutting inference improvements

- `regress` now publicly exposes two-way clustering in both implementation and docs.
- Wrapper behavior for unsupported multi-cluster paths on FE/HDFE commands is now clearly rejected instead of failing with uncontrolled errors.

### 5. Open-source export and release readiness

- Added a manifest-driven open-source export workflow.
- Added export safety tests for dangerous target paths and dry-run behavior.
- Added release checklist, release status, and public scope-audit materials.
- Synced public validation, release, architecture, ADR, and operations docs into the open-source mirror.

### 6. Documentation cleanup

- Refreshed public English docs to match current implementation boundaries.
- Refreshed `README.zh-CN.md` to match the current public README structure and release posture.
- Updated Chinese installation guidance to distinguish PyPI install from editable source installs.
- Repaired several mojibake / damaged-text issues in public Markdown files.

---

## Public-Facing Additions in the Mirror

Compared with the previous public snapshot, the open-source mirror now includes or more reliably exposes:

- `docs/adr/`
- `docs/architecture/`
- `docs/operations/open-source-export.md`
- `docs/operations/open-source-scope-audit.md`
- `docs/release/`
- `docs/validation/`
- `scripts/release/export_open_source.py`
- `tests/test_export_safety.py`

---

## Current Verified Baseline

- Main repo non-golden tests: **194 passed**
- Open-source mirror non-golden tests: **194 passed**
- Current exported mirror size baseline: **168 non-git files**

---

## Known Remaining Limits

These are still true after the update:

- Community commands remain validated subsets, not full Stata command reproductions.
- Two-way clustering is currently only public on `regress`.
- Weights beyond `aweight` are not yet supported.
- Wrapper-layer `predict` / `margins` are still not broadly exposed.
- Golden dual-run tests still require local Stata 17 and are not part of the open-source CI baseline.

---

## Practical Impact for Users

For external users, this release means:

- the public docs now track the true implementation boundary more closely,
- the open-source mirror contains substantially more of the materials needed to understand and verify the project,
- the HDFE, DID, and release-support docs are less likely to mislead first-time users,
- and the published package/version metadata is now aligned with the current public snapshot.
