# M09 Postestimation — Summary

## Audit objective

Independently re-validate StataFlow postestimation capabilities (`predict`, `margins`, `estat summarize/vce/ic`, and result propagation) against Stata 17 without modifying `src/stataflow/` product code.

## Assets created

- `docs/audit/modular-revalidation-v1.3/M09-postestimation/task_plan.md`
- `docs/audit/modular-revalidation-v1.3/M09-postestimation/test-design-register.md`
- `docs/audit/modular-revalidation-v1.3/M09-postestimation/findings.md`
- `docs/audit/modular-revalidation-v1.3/M09-postestimation/progress.md`
- `docs/audit/modular-revalidation-v1.3/M09-postestimation/summary.md` (this file)
- `docs/audit/modular-revalidation-v1.3/M09-postestimation/evidence/{synthetic,real-data,property}/`
- `tests/audit_v1_3/m09_postestimation/m09_audit_utils.py`
- `tests/audit_v1_3/m09_postestimation/test_m09_synthetic.py`
- `tests/audit_v1_3/m09_postestimation/test_m09_realdata.py`
- `tests/audit_v1_3/m09_postestimation/test_m09_property.py`
- `tests/audit_v1_3/m09_postestimation/repro_m09_postestimation_findings.py`
- `stata/cases/audit_v1_3_m09/*.dta`
- `stata/output/audit_v1_3_m09/*.log`

## Experiment counts

| Category | Count | Result |
|---|---|---|
| Synthetic dual-run | 6 | 5 PASS, 1 XFAIL |
| Real-data dual-run | 2 | 2 PASS |
| Property / metamorphic | 3 | 3 PASS |

## Confirmed findings

| ID | Severity | Status | Description |
|---|---|---|---|
| M09-FE-001 | P1 | Confirmed-Stata | `FixedEffectsOLS.predict(type="xb")` returns only `X @ beta` and omits the entity-specific fixed effect; Stata `predict, xb` after `xtreg, fe` returns `X @ beta + u_i`. |

## Verified paths

The following postestimation paths align with Stata 17 at the recorded tolerances:

- OLS out-of-sample prediction with collinearity and new factor levels (S01)
- AbsorbingOLS all predict types: `xb`, `xbd`, `d`, `dresiduals`, `stdp` (S03)
- Logit predicted probabilities and continuous-regressor AME/SE (S04)
- Poisson predicted counts and continuous-regressor MEM/SE at means (S05)
- IVAbsorbingOLS `xb`, `residuals`, `stdp` after `ivreghdfe` (S06)
- Senate OLS predict + `estat summarize` (R01)
- JTrain `areg` predict + `estat summarize` (R02)
- Row-order invariance, irrelevant-column invariance, and outcome-scale linearity (P01–P03)

## Limitations and residual risks

- M09-FE-001 affects any workflow that expects Stata-compatible FE predictions. A fix requires storing and adding back entity effects.
- Discrete/binary regressor margins were not claimed as fully Stata-aligned in this audit; Stata's default `margins, dydx()` treats numeric 0/1 variables as continuous unless they are declared as factors. Python's `stataflow_discrete_columns` attribute can produce a different (discrete-change) effect, so users must ensure equivalent model specifications.
- `estat_vce` and `estat_ic` are exercised only indirectly; deeper field-level checks across all model families remain future work.

## Test baselines

```bash
pytest tests/audit_v1_3/m09_postestimation -v
# 10 passed, 1 xfailed, 11 total

pytest tests/ --ignore=tests/golden/ --ignore=tests/benchmarks/ -q
# No new failures introduced by M09 assets
```

## Recommendation

- Prioritize fixing M09-FE-001 before declaring `xtreg_fe()` postestimation Stata-compatible.
- Document the discrete-margins semantic caveat in the support matrix.
