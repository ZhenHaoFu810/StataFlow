---
name: project_phase
description: Tracks the current active phase, recently completed packages, and wave progression for StataFlow.
type: project
---

**Current active phase:** Audit Phase 3 Wave 1 — Real-Data Dual-Run Validation (2026-04-30)
**Task card:** `workspace/current-task/package-audit-phase3-real-data-wave1.md`
**Status:** Task card written, awaiting execution

**Why this now:**
- Phase 1 (Math Audit) confirmed 24 items correct, 5 P1 issues verified, 0 P0 blockers
- Phase 2 (Code Refactoring) delivered 6/8 sub-items, 0 regressions
- Real-data coverage is the weakest evidence link (~30% of golden tests use real data, most only cover `vce="ols"`)
- Phase 3 adds 10 structured financial economics experiments across 3 waves

**Phase 3 Wave 1 scope (5 experiments, all data already in project, no external download):**
1. C1.1 CAPM/FF3 (P0) — OLS vce(ols/robust/cluster) on Fama-French 3-factor daily returns
2. C1.4 Card IV (P0) — IV 2SLS/GMM2S/LIML all VCE on Card 1995 returns-to-schooling
3. C1.6 Gravity PPML (P0) — PPMLHDFE vce(robust/cluster) on trade gravity data
4. C1.7 DID Policy (P1) — DID methods on ezunem staggered adoption
5. C1.8 RD Senate (P2) — RD all bandwidth selectors on senate election data

**Phase 3 Waves 2-3 (subsequent packages):**
- Wave 2: C1.9 DK HAC, C1.10 Slopes, C1.3 CEO/wagepan, C1.5 Mroz (data already in project)
- Wave 3: C1.2 Compustat (needs external data acquisition)

**Recently completed:**
- Waves 0-12: All estimation commands implemented, v1.0.0 Stable
- Audit Phase 1 (Math Audit): 3 audit reports, 24 items correct, 5 P1 verified
- Audit Phase 2 (Code Refactoring): 6/8 sub-items delivered, 275+765 tests pass, 0 regressions
- Phase 2 remaining (low priority): T-matrix assessment (2.1d), Aitken removal (2.3b), error handling review (2.3c)

**Current test baseline (2026-04-30):**
- 275 non-golden + 765 golden (approximately), all passing
- Current version: 1.0.0 (Stable)

**How to apply:**
- Current task is `workspace/current-task/INSTRUCTIONS.md` (Phase 3 Wave 1)
- Task card at `workspace/current-task/package-audit-phase3-real-data-wave1.md`
- Each experiment requires: data_prep.py, analysis.do, analysis.py, README.md, results.md, golden test
- Execute experiments in order: C1.1 → C1.4 → C1.6 → C1.7 → C1.8
- After Wave 1, proceed to Wave 2 (wagepan/mroz experiments) then Wave 3 (external data)
