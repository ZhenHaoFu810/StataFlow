---
name: command_stability
description: Tracks which Stata commands are stable, beta, or not yet started. Updated 2026-04-30 for Phase 3.
type: project
---

**Stable (synthetic + real-data dual-run verified; core API unlikely to change):**
- `regress` — OLS, robust, cluster (1- and 2-way), aweight, noconstant
- `xtreg, fe` — Within estimator, single FE, cluster
- `areg` — Single absorb var, OLS/cluster VCE
- `ivregress 2sls` — 2SLS, robust, cluster
- `logit` — MLE, robust, cluster
- `probit` — MLE, robust, cluster
- `poisson` — MLE, robust, cluster

**Beta (high-frequency paths implemented; v0.3.x wave hardening complete):**
- `reghdfe` — 1+ categorical FEs, singleton drop, robust/cluster (1- and 2-way), predict (xb/xbd/d/residuals/dresiduals/stdp), savefe, keepsingletons, noconstant, estat_summarize, **MAP iterative kernel (technique="map")**, **individual slope absorption (absorb(var##c.slope) / absorb(var#c.slope))**, **Driscoll-Kraay VCE (vce(dkraay))**
- `ivreghdfe` — IV + 1+ FEs, robust/cluster (1- and 2-way), predict (xb/xbd/residuals/d/dresiduals/stdp), first (1-stage diagnostics), gmm2s, liml (including Fuller/k-class), weakiv (Kleibergen-Paap rk LM / rk Wald F + Stock-Yogo critical values)
- `ppmlhdfe` — PPML + 1+ FEs, offset/exposure, robust/cluster (1- and 2-way), predict (xb/mu/residuals/pearson/deviance/working), deviance, pseudo-R2, eform/irr, separation(fe), estat_ic, estat_summarize
- `rdrobust` — Sharp RD, 11 bandwidth selectors, fuzzy RD (Wald ratio, sharpbw, perfect compliance), weights, masspoints (check/adjust), cluster/nncluster VCE, rdplot, bwcheck, scaleregul
- `did_imputation` — BJS imputation, allhorizons, autosample, cluster, controls/unitcontrols/timecontrols, pretrends, wtr/hetby/saveestimates/saveweights/sum
- `csdid` — Callaway-Sant'Anna, method="reg"/"drimp"/"dripw", xvars, estat_event, aggtype (simple/group/calendar/pretrend)
- `eventstudyinteract` — Sun-Abraham IW estimator, auto dummy generation, cluster

**Phase 3 Real-Data Coverage Gaps (existing tests only cover `vce="ols"` in most cases):**

| Command | Existing Real-Data Test | Gap |
|---------|------------------------|-----|
| `regress` / OLS | None (FF3 planned) | No comprehensive real-data test |
| `ivreghdfe` | `test_w2_ivregress_real_card.py` (ols only) | No GMM2S/LIML, no robust/cluster VCE, no weakiv/first on real data |
| `ppmlhdfe` | `test_w3_ppmlhdfe_real_gravity.py` (robust only) | No cluster VCE, no eform, no separation on real data |
| `did_imputation` | `test_w4_did_imputation_real_ezunem.py` (basic only) | No controls/pretrends on real data |
| `csdid` | `test_w4_csdid_real_ezunem.py` (reg only) | DRIMP SE rtol=0.2 known issue; no dripw real-data test |
| `rdrobust` | `test_w8_rdrobust_*_real_senate.py` (comprehensive) | Most complete real-data coverage; gaps in structured documentation |

**Wave 12 known limitations (v1.0.0 scope):**
- Slopes only work with LSDV path; MAP path explicitly raises NotImplementedError
- DK SE tolerance 1e-4 (documented in ADR; small-sample correction factor difference)
- No robust/cluster + slopes golden tests
- No slopes + DK combination golden tests
- Real data golden tests (wagepan) planned for Phase 3 Wave 2

**Deferred to v1.1.0+ (Roadmaster decision 2026-04-30):**
- `reghdfe`: group/individual FE, 3-way+ clustering, LSMR/LSQR, savefe MAP path, dofadjustments exact algorithms
- `ivreghdfe`: orthog/endogtest/redundant, partial()/fwl(), HAC for IV, ffirst, CUE, 3-way+ cluster
- `ppmlhdfe`: separation(ir/simplex/mu), d()/d2, guess(), keepsingletons, 3-way+ cluster
- `did_imputation`: window, minn, hbalance, project, saveresid, avgeffectsby/leaveout, repeated cross-section
- `eventstudyinteract`: covariates, window, minn, full matrix returns
- `csdid`: method="ipw", gtcontrol, longdiff
- `rdrobust`: deriv>0 (kink designs), stdvars, all/detail, rdbwselect standalone, bwrestrict, scalepar
- Postestimation: test/lincom/nlcom, margins full IV/GLM interaction

**Known limitations documented (all versions):**
- `reghdfe` 2-way cluster _cons SE: ~2-16% structural deviation (ADR-0003). Slope SEs < 1e-6.
- `ivreghdfe` / `ppmlhdfe` 2-way cluster _cons SE: same LSDV structural deviation.
- `ivreghdfe` cluster stdp: ~0.28% residual (Wave 11).
- `ppmlhdfe` predict pearson/deviance/working: ~0.35% max residual from IRLS/HDFE convergence.
- `did_imputation` controls: implemented via dense LSDV, may differ slightly from Stata iterative demeaning.
- `csdid` method="drimp": sklearn LogisticRegression for PS, trimming at [0.01, 0.99].
- `ivreghdfe` weakiv: k_endog > 1 returns nan (not yet implemented).
- `rdrobust` rdplot: bin-selection algorithm differs from Stata 2-3x. No golden dual-run.
- `reghdfe` MAP cluster slope SE (1-way): ~0.5% when cluster nests FE (MAP builds meat on partialled-out data).
