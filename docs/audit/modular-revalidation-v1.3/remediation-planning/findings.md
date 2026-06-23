# Analysis Notes

This file records cross-module observations while reading M01-M10 audit outputs.

## Initial inventory

- All ten module directories contain structured audit deliverables and evidence assets.
- Risk is concentrated in PPMLHDFE, DID, Panel/FE, IV/GMM, and HDFE.
- M09 currently contains one confirmed FE prediction issue.
- M10 contains two confirmed shared-infrastructure issues.
- Finding IDs are not automatically equivalent to defects: M07-DID-002 is explicitly a successful algorithm alignment / test-design correction and must not become a remediation task.
- Existing module severity labels require normalization where one finding mixes multiple severities or where API/documentation incompatibility is distinct from estimator correctness.

## Finding inventory

- M01: 3 findings.
- M02: 7 findings.
- M03: 4 findings.
- M04: 4 findings.
- M05: 5 findings.
- M06: 7 findings.
- M07: 6 numbered entries, but M07-DID-002 is a positive alignment result and M07-DID-004 duplicates the root cause of M07-DID-001.
- M08: 2 findings.
- M09: 1 finding.
- M10: 2 findings.

Raw numbered entries total 41. The actionable defect count will be lower after deduplication and removal of positive/non-product entries.

## Early cross-module clusters

- Collinearity/rank handling: M01-LIN-002, M02-FE-002/006/007, and risk notes in M03-M05.
- FE degrees of freedom and nested FE semantics: M02-FE-001/004, M03-HDFE-001/002/003, M06-PPMLHDFE-007.
- Weight API incompatibility: M01-LIN-001 versus M05-GLM-001 and M06-PPMLHDFE-001 require command-specific treatment, not one global rule.
- Overall-test/schema semantics: M01-LIN-003, M02-FE-001/004, M05-GLM-002/003, M06-PPMLHDFE-005.
- Prediction semantics with absorbed effects: M06-PPMLHDFE-004 and M09-FE-001 are related conceptually but require opposite Stata command semantics to be verified per estimator.

## Normalization decisions

- M07-DID-002 is evidence that the core DIDImputation algorithm aligns after harmonizing treatment encoding; it is not an actionable defect.
- M07-DID-004 is merged into M07-DID-001 as one treatment-timing encoding task.
- M06-PPMLHDFE-006 is primarily a comparison/schema policy difference: Stata preserves omitted rows while Python removes them. It must first be resolved as a public ResultSchema contract decision, not patched inside PPML estimation blindly.
- M05-GLM-001 and M06-PPMLHDFE-001 are compatibility-contract issues. Mapping `aweight` to another Stata weight type is not automatically valid because point-estimation and VCE semantics may differ.
- M03-HDFE-004, M04-IV-004, M05-GLM-005, M06-PPMLHDFE-005 SE residual, M07-DID-005, and M08-RD-001 are numerical-residual investigations. They should not block higher-severity correctness fixes unless their discrepancy changes inference or exceeds the project tolerance after deterministic reproduction.
- M02-FE-005 changes wrapper default behavior and is therefore an API compatibility change requiring explicit regression and migration review.

## Highest-risk correctness defects

- M02-FE-002: deterministic crash after within-collinearity deletion because dimensions are not synchronized.
- M06-PPMLHDFE-002: default separation path can return meaningless divergent estimates without a hard failure.
- M06-PPMLHDFE-003: offset/exposure changes coefficients, VCE, likelihood, and deviance materially.
- M07-DID-003: `notyet=True` uses the wrong control population and changes ATT estimates materially.

## Econometric dependency observations

- Rank/collinearity handling determines the estimand's reported parameterization and must be resolved before downstream VCE/schema fixes.
- FE absorbed degrees of freedom feed `k_eff`, small-sample corrections, RMSE, adjusted R-squared, and overall tests; one df fix can change many fields and requires a single coherent formula audit.
- GLM/PPML overall tests must distinguish likelihood-ratio statistics from Wald statistics based on VCE semantics.
- DID treatment encoding and control-group definitions are identification rules, not input-cleaning details; they require explicit estimand-level tests before implementation.

## Current source map observations

- Audit baseline equals current `dev` HEAD: `2c7db1ca095e03d29c471e8d523fdaa943306174`.
- The worktree contains extensive untracked audit assets and an existing modification to `workspace/current-task/REPORT.md`; remediation work must preserve these user/agent changes.
- OLS zero-weight rejection is at `src/stataflow/estimators/ols.py:152`; multiway F calculation is around lines 458-486.
- Shared rank detection is `src/stataflow/estimators/_vce_utils.py:198-218` and uses `np.linalg.matrix_rank`.
- FE collinearity deletion is at `src/stataflow/estimators/fe.py:215-217`; downstream `k`, df, F, constant recovery, and prediction logic remain distributed across the file.
- FE prediction already stores `_entity_effects`, so M09-FE-001 may be repairable without a new result-schema field, but newdata handling for unseen entities must be specified explicitly.
- HDFE df logic is centralized in `_compute_df_a` and `_cluster_k_eff`, but duplicated MAP/LSDV downstream formulas mean fixes need both-path tests.
- IV weak statistics are computed and placed into `extra_stats`, but `DiagnosticsInfo` currently lacks obvious dedicated fields; schema/API design must precede implementation.
- PPML offset is explicitly subtracted again in `_build_t_matrix`, matching the audit's proposed root cause. Nonconvergence currently produces a warning while still returning a result.
- DIDImputation source comments encode the incompatible zero/negative convention; CSDID has the incorrect `notyet` branch in both regression and doubly robust paths.
- RD computes effective counts before constructing bias-corrected/robust results but does not use them as a reporting guardrail.
- StataRunner reports only the process return code and does not parse Stata `r(...)` errors from logs.

## Worktree safety

- Do not reset, clean, or overwrite the untracked `modular-revalidation-v1.3`, `tests/audit_v1_3`, or `stata/cases/audit_v1_3_*` assets.
- Every remediation Agent must inspect `git status` and stage explicit paths only.
- Product fixes should be split into isolated branches/worktrees after the audit assets are safely committed or otherwise preserved.
