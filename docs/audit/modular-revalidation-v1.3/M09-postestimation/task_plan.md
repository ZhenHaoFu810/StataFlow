# M09 Postestimation — Task Plan

## Baseline

- **Repository:** `D:/OneDrive - SAIF/PhD3/StataFlow`
- **Baseline commit SHA:** `2c7db1ca095e03d29c471e8d523fdaa943306174`
- **Branch:** current working tree (no local modifications to `src/stataflow/`)
- **Python:** 3.11.7 (Anaconda)
- **Stata:** Stata 17 MP-64 (`D:\Software\Stata17\StataMP-64.exe`)
- **Key dependencies:**
  - numpy 1.26.4
  - pandas 3.0.2
  - scipy 1.17.1
  - PyYAML 6.0.1
  - pytest 7.4.0
  - stataflow 1.1.0
- **Reference test status:** `tests/test_postestimation.py` passes (16 passed)

## Scope

This module audit independently re-validates StataFlow's postestimation layer against Stata 17:

- `predict()` on fitted result/model objects:
  - `OLS` / `regress()` — `xb`, `residuals`, out-of-sample.
  - `FixedEffectsOLS` / `xtreg_fe()` — `xb`, `residuals`, grand-mean semantics.
  - `AbsorbingOLS` / `areg()` / `reghdfe()` — `xb`, `xbd`, `d`, `dresiduals`, `stdp`.
  - `IVAbsorbingOLS` / `ivreghdfe()` — same family of predict types.
  - `Logit`/`Probit`/`Poisson` / `logit()`/`probit()`/`poisson()` — `xb`, `pr`/`mu`, margins.
  - `PPMLHDFE` / `ppmlhdfe()` — `xb`, `mu`, GLM-style residuals.
- `margins` helpers in `src/stataflow/postestimation.py`:
  - `dydx` (AME) and `atmeans` (MEM) for GLM families.
  - Discrete/continuous variable handling.
- `estat_summarize`, `estat_vce`, `estat_ic`.
- Result propagation:
  - sample mask length/sum/nobs consistency;
  - out-of-sample prediction with missing rows;
  - new factor levels in `newdata`;
  - row reordering and duplicate indexes;
  - dropped coefficients / collinearity.

## Key files read

- `docs/audit/modular-revalidation-v1.3/MASTER_AUDIT_BRIEF.md`
- `src/stataflow/postestimation.py`
- `src/stataflow/results/result.py`
- `src/stataflow/estimators/ols.py` (predict/margins)
- `src/stataflow/estimators/fe.py` (predict/margins)
- `src/stataflow/estimators/absorbing_ols.py` (predict/margins)
- `src/stataflow/estimators/iv.py` (predict)
- `src/stataflow/estimators/glm.py` (predict/margins)
- `src/stataflow/estimators/ppmlhdfe.py` (predict/margins)
- `tests/test_postestimation.py`
- `tests/audit_v1_3/m08_rd/m08_audit_utils.py` (pattern reference)

## Audit questions (aligned with MASTER_AUDIT_BRIEF §M09)

1. Does each model family expose a `predict()` whose supported `type` values match Stata's documented predict options?
2. Does in-sample `predict, xb` reproduce the fitted linear predictor to field-level tolerance?
3. Does out-of-sample prediction use only the estimation-sample coefficients and correctly handle missing rows in `newdata`?
4. After row reordering or duplicate row indexes, are predictions aligned with the original observations?
5. When a regressor is dropped due to collinearity, does `predict` treat its coefficient as zero and retain alignment?
6. Does `margins, dydx(*)` for GLM families match Stata's AMEs and delta-method SEs for both continuous and indicator variables?
7. Does `margins, dydx(*) atmeans` match Stata's MEMs?
8. Does `estat summarize` return the same N/mean/sd/min/max over the estimation sample as Stata?
9. Does `estat vce` return exactly the reported variance-covariance matrix?
10. Does `estat ic` use the same k-counting convention as Stata (df_model + constant when present)?
11. Are sample-mask invariants (`len(mask) == n_input_rows`, `sum(mask) == nobs`) always satisfied after prediction?
12. Do postestimation calls raise clear errors for unsupported options instead of silently ignoring them?

## Deliverable checklist

- [x] `task_plan.md` (this file)
- [x] `test-design-register.md` — ≥6 synthetic, ≥2 real-data, ≥3 property tests
- [x] `findings.md` — any confirmed findings with severity/evidence
- [x] `progress.md` — task list and execution status
- [ ] `summary.md` — pass/fail/undecided summary and risks
- [x] `evidence/synthetic/` JSON evidence (S01–S03)
- [ ] `evidence/real-data/` JSON evidence
- [ ] `evidence/property/` JSON evidence
- [x] `evidence/minimal-reproductions/` (via S02 evidence + findings.md)
- [x] `tests/audit_v1_3/m09_postestimation/m09_audit_utils.py`
- [x] `tests/audit_v1_3/m09_postestimation/test_m09_synthetic.py` — first 3 synthetic tests (S01–S03)
- [ ] `tests/audit_v1_3/m09_postestimation/test_m09_realdata.py` — ≥2 real-data tests
- [ ] `tests/audit_v1_3/m09_postestimation/test_m09_property.py` — ≥3 property tests
- [ ] `tests/audit_v1_3/m09_postestimation/repro_m09_postestimation_findings.py`
- [x] Stata `.do`/`.log`/`.dta` saved under `stata/cases/audit_v1_3_m09/` and `stata/output/audit_v1_3_m09/`
- [x] `pytest tests/audit_v1_3/m09_postestimation -v` executed
- [x] Regression check `pytest tests/ --ignore=tests/golden/ --ignore=tests/benchmarks/ -q` executed
- [x] M09 section appended to `workspace/current-task/REPORT.md`
