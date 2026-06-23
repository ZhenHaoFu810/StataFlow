# M09 Postestimation — Test Design Register

All experiments are newly designed for this audit. They do not reuse DGPs, seeds, Stata scripts, or expected values from `tests/test_postestimation.py` or `tests/golden/`.

## Synthetic experiments

### S01 — OLS out-of-sample prediction with collinear regressor and new factor level

| Field | Value |
|---|---|
| **Test ID** | `S01` |
| **Question** | After a regressor is dropped due to collinearity, does out-of-sample `predict, xb` treat the dropped coefficient as zero and align with Stata? Does a new factor level in `newdata` produce the same prediction rule in both implementations? |
| **DGP** | `N=60`. `x1 ~ N(0,1)`, `x2 = 2*x1` (perfectly collinear), `x3 ∈ {0,1}` random. `y = 1 + 2*x1 + 3*x3 + ε`, `ε ~ N(0,0.5²)`. Estimation sample: rows 0–39. Prediction sample: rows 40–59 with some `x3` values equal to `2` (a level not seen during estimation). |
| **Theoretical expectation** | `x2` is dropped; its effective coefficient is zero. For rows with `x3=2`, Stata expands `i.x3` to all-zero dummies, so the prediction should equal `_cons + 2*x1`. Python must match this exactly. |
| **Novelty vs old tests** | Old tests check in-sample xb/residuals helpers only. This test combines collinearity, dropped-coefficient propagation, factor-variable expansion, and out-of-sample new levels. |
| **Stata command** | `regress y x1 x2 i.x3; predict xb_s, xb; predict resid_s, residuals; summarize xb_s resid_s; list xb_s resid_s in 1/5` |
| **Python API** | `regress(train, "y", ["x1","x2","i.x3"]).predict(type="xb", newdata=test)` and `type="residuals"` |
| **Comparison fields** | `xb` mean/sd, `residuals` mean/sd, first 5 predicted values, `nobs`, dropped-variable list, sample-mask sum |
| **Seed / hash** | Seed `202601`; SHA256 of generated CSV recorded in evidence JSON |
| **Execution result** | PASS |
| **Expected evidence path** | `docs/audit/modular-revalidation-v1.3/M09-postestimation/evidence/synthetic/S01/S01_evidence.json` |

### S02 — FE prediction with grand-mean correction and missing rows in newdata

| Field | Value |
|---|---|
| **Test ID** | `S02` |
| **Question** | Does `xtreg, fe` `predict, xb` add the entity fixed effect, and does `predict, e` exclude missing rows in `newdata` consistently with Stata? |
| **DGP** | `N=80`, 8 entities. Entity effects drawn `N(0,1)`. `x ~ N(0,1)`. `y = α_i + 1.5*x + ε`, `ε ~ N(0,0.3²)`. Estimation uses rows 0–59. Prediction rows 60–79 with 5 rows made missing in `x`. |
| **Theoretical expectation** | In-sample xb equals `x*β + α_i`. Python currently returns only `x*β`. |
| **Novelty vs old tests** | Old tests do not exercise FE prediction semantics or missing-row handling in `newdata`. |
| **Stata command** | `xtset id; xtreg y x, fe; predict xb_s, xb; predict e_s, e; summarize xb_s e_s; count if missing(xb_s)` |
| **Python API** | `xtreg_fe(data, "y", ["x"], fe="id").predict(type="xb", newdata=...)`, `type="residuals"` |
| **Comparison fields** | `xb` mean/sd, `residuals` mean/sd, number of non-missing predictions, `nobs` |
| **Seed / hash** | Seed `202602` |
| **Execution result** | XFAIL — M09-FE-001: Python omits entity fixed effects |
| **Expected evidence path** | `evidence/synthetic/S02/S02_evidence.json` |

### S03 — AbsorbingOLS all predict types (`xb`, `xbd`, `d`, `dresiduals`, `stdp`)

| Field | Value |
|---|---|
| **Test ID** | `S03` |
| **Question** | Do all declared `AbsorbingOLS` predict types match Stata `areg`? |
| **DGP** | `N=90`, 10 groups. Group effects `N(0,1.5)`. `x ~ N(0,1)`. `y = γ_g + 2*x + ε`, `ε ~ N(0,0.4²)`. |
| **Theoretical expectation** | `xbd` = full projection including FE; `xb` = reported `x*β + _cons`; `d` = `xbd - xb` (group effect at mean); `dresiduals` = `y - xb`; `stdp` = sqrt(X_reported V X_reported'). |
| **Novelty vs old tests** | First field-level comparison of `xbd`, `d`, and `stdp` for an absorbed model. |
| **Stata command** | `areg y x, absorb(g); predict xb_s, xb; predict xbd_s, xbd; predict d_s, d; predict dr_s, dresiduals; predict stdp_s, stdp; summarize xb_s xbd_s d_s dr_s stdp_s` |
| **Python API** | `areg(data, "y", ["x"], absorb="g").predict(type=...)` for each type |
| **Comparison fields** | Mean/sd of each predict type, `nobs`, `df_a` |
| **Seed / hash** | Seed `202603` |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/synthetic/S03/S03_evidence.json` |

### S04 — Logit margins `dydx(*)` for a continuous regressor and predicted probabilities

| Field | Value |
|---|---|
| **Test ID** | `S04` |
| **Question** | Does Python's logit AME match Stata `margins, dydx(x1)` for a continuous regressor, and do predicted probabilities / information criteria align? |
| **DGP** | `N=200`. `x1 ~ N(0,1)`, `x2 ∈ {0,1}` with `P=0.4`. Latent `y* = -1 + 0.8*x1 - 1.2*x2 + ν`, `ν` logistic. `y = 1(y*>0)`. |
| **Theoretical expectation** | AME for `x1` = `β1 * mean(Λ(η)(1-Λ(η)))`. `_cons` marginal effect is not reported by Stata. SEs computed via delta method must match. |
| **Novelty vs old tests** | Existing tests only unit-test the margin helper functions; this is an end-to-end logit AME vs Stata comparison. |
| **Stata command** | `logit y x1 x2; margins, dydx(x1); predict pr_s, pr; estat ic` |
| **Python API** | `logit(data, "y", ["x1","x2"])._model.margins("dydx")`; `result.predict("pr")`; `estat_ic(result)` |
| **Comparison fields** | AME and SE for `x1`; mean predicted probability; AIC/BIC; `nobs`, `ll`, `pseudo_r2` |
| **Seed / hash** | Seed `202604` |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/synthetic/S04/S04_evidence.json` |

### S05 — Poisson margins `atmeans` and response-scale predictions

| Field | Value |
|---|---|
| **Test ID** | `S05` |
| **Question** | Do Poisson MEMs (`margins, dydx(x1) atmeans`) and response predictions (`predict, n`) align with Stata? |
| **DGP** | `N=150`. `x1 ~ N(0,1)`, `x2 ∈ {0,1}`. `μ = exp(0.5 + 0.3*x1 + 0.6*x2)`. `y ~ Poisson(μ)`. |
| **Theoretical expectation** | MEM for continuous `x1` = `β1 * exp(x̄'β)`. Mean predicted count over sample equals mean `μ`. |
| **Novelty vs old tests** | Tests Poisson `atmeans`; existing helper tests do not run a Stata Poisson end-to-end. |
| **Stata command** | `poisson y x1 x2; margins, dydx(x1) atmeans; predict mu_s, n; summarize mu_s` |
| **Python API** | `poisson(data, "y", ["x1","x2"])._model.margins("atmeans")`; `result.predict("mu")` |
| **Comparison fields** | MEM and SE for `x1`; mean `mu`; `nobs`, `deviance` |
| **Seed / hash** | Seed `202605` |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/synthetic/S05/S05_evidence.json` |

### S06 — IVAbsorbingOLS prediction after `ivreghdfe`

| Field | Value |
|---|---|
| **Test ID** | `S06` |
| **Question** | Does `ivreghdfe` prediction (`xb`, `residuals`, `stdp`) reproduce Stata's post-estimation output? |
| **DGP** | `N=120`, 12 groups. Instrument `z ~ N(0,1)`. Endogenous `x = 0.5*z + γ_g/5 + v`, `v ~ N(0,0.5²)`. `y = 1 + 2*x + γ_g + ε`, `ε ~ N(0,0.4²)`. |
| **Theoretical expectation** | 2SLS estimates `β≈2`. Predictions follow the same `xb`/`xbd` decomposition as `AbsorbingOLS`. `stdp` uses the reported VCE. |
| **Novelty vs old tests** | First independent check of IV-with-absorption predict types. |
| **Stata command** | `ivreghdfe y (x = z), absorb(g) resid; predict xb_s, xb; predict resid_s, residuals; predict stdp_s, stdp; summarize xb_s resid_s stdp_s` |
| **Python API** | `ivreghdfe(data, "y", x_exog=[], x_endog=["x"], instruments=["z"], absorb=["g"])._model.predict(type=...)` |
| **Comparison fields** | Mean/sd of each predict type, `nobs` |
| **Seed / hash** | Seed `202606` |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/synthetic/S06/S06_evidence.json` |

## Real-data experiments

### R01 — Senate OLS predict and `estat summarize`

| Field | Value |
|---|---|
| **Test ID** | `R01` |
| **Question** | On the Senate RD dataset, do OLS `predict, xb` / `predict, residuals` and estimation-sample summary statistics match Stata? |
| **Dataset** | `research/data/public/rdrobust_senate_with_z.dta` |
| **Specification** | `vote ~ margin + termshouse` |
| **Novelty vs old tests** | New empirical design on a project public dataset; tests `predict` and `estat_summarize` together. |
| **Stata command** | `use rdrobust_senate_with_z; regress vote margin termshouse; predict xb_s, xb; predict resid_s, residuals; summarize xb_s resid_s; summarize vote margin if e(sample)` |
| **Python API** | `regress(df, "vote", ["margin","termshouse"]).predict(type="xb"/"residuals"); estat_summarize(result, df, variables=["vote","margin"])` |
| **Comparison fields** | `xb` mean/sd; `residuals` mean/sd; summary N/mean/sd for `vote`, `margin`; `nobs` |
| **Hash** | SHA256 of generated DTA recorded in evidence JSON |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/real-data/R01/R01_evidence.json` |

### R02 — JTrain areg prediction and `estat summarize`

| Field | Value |
|---|---|
| **Test ID** | `R02` |
| **Question** | On the JTrain panel, do `areg` predicted values and `estat summarize` over the estimation sample match Stata? |
| **Dataset** | `research/data/public/did/jtrain_prepared.dta` |
| **Specification** | `lscrap ~ grant + d89 + d88`, absorb `fcode` |
| **Novelty vs old tests** | New specification using `areg` postestimation and summary statistics on a real public dataset. |
| **Stata command** | `use jtrain_prepared; areg lscrap grant d89 d88, absorb(fcode); predict xb_s, xb; predict xbd_s, xbd; predict resid_s, residuals; summarize xb_s xbd_s resid_s; summarize lscrap if e(sample)` |
| **Python API** | `areg(df, "lscrap", ["grant","d89","d88"], absorb="fcode").predict(type=...); estat_summarize(result, df, variables=["lscrap"])` |
| **Comparison fields** | `xb`/`xbd`/`residuals` mean/sd; summary N/mean/sd for `lscrap`; `nobs`, `df_a` |
| **Hash** | SHA256 of generated DTA recorded in evidence JSON |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/real-data/R02/R02_evidence.json` |

## Metamorphic / property tests

### P01 — Row-order permutation invariance of OLS predictions

| Field | Value |
|---|---|
| **Test ID** | `P01` |
| **Question** | If rows are permuted, do in-sample OLS predictions remain unchanged up to the same permutation? |
| **DGP** | `N=80`. `x1, x2 ~ N(0,1)`, `y = 1 + 2*x1 - 0.5*x2 + ε`. Fit on original and on a random permutation. |
| **Theoretical expectation** | Prediction statistics (mean, sd) are identical; coefficients are identical. |
| **Novelty** | Tests that sample-mask/index alignment is robust to row reordering. |
| **Stata command** | `regress y x1 x2; predict xb_s, xb; summarize xb_s` (run on both orderings) |
| **Python API** | `regress(original,...).predict("xb")` vs `regress(permuted,...).predict("xb")` |
| **Comparison fields** | Mean/sd of `xb`, `nobs` |
| **Seed / hash** | Seed `202607` |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/property/P01/P01_evidence.json` |

### P02 — Irrelevant columns do not change OLS predictions

| Field | Value |
|---|---|
| **Test ID** | `P02` |
| **Question** | Does `predict, xb` ignore columns that were not part of the model? |
| **DGP** | `N=80`. `x1, x2 ~ N(0,1)`, `y = 1 + 2*x1 - 0.5*x2 + ε`. Add irrelevant `noise ~ N(0,1)`. |
| **Theoretical expectation** | Predictions with and without `noise` are exactly equal. |
| **Novelty** | Tests that the Python prediction path does not accidentally depend on extra columns. |
| **Stata command** | `regress y x1 x2; predict xb_s, xb` |
| **Python API** | `result.predict("xb")` with and without the extra column in the input frame |
| **Comparison fields** | `xb` vector equality, `nobs` |
| **Seed / hash** | Seed `202608` |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/property/P02/P02_evidence.json` |

### P03 — Linear scaling of the dependent variable scales predictions and residuals

| Field | Value |
|---|---|
| **Test ID** | `P03` |
| **Question** | If `y` is multiplied by `c`, do `predict, xb` and `predict, residuals` scale by `c`? |
| **DGP** | `N=80`. `x1, x2 ~ N(0,1)`, `y = 1 + 2*x1 - 0.5*x2 + ε`, `ε ~ N(0,0.5²)`. Define `y2 = 3*y`. |
| **Theoretical expectation** | `xb(y2) = 3*xb(y)`; `resid(y2) = 3*resid(y)`. Coefficients also scale by 3. |
| **Novelty** | Validates the linearity of the postestimation layer rather than a single numeric value. |
| **Stata command** | `regress y x1 x2; predict xb_s, xb; predict r_s, residuals; regress y2 x1 x2; predict xb2_s, xb; predict r2_s, residuals; summarize xb_s xb2_s r_s r2_s` |
| **Python API** | `regress(data, "y", ["x1","x2"]).predict(...)` vs `regress(data, "y2", ["x1","x2"]).predict(...)` |
| **Comparison fields** | Ratio of `xb` vectors (≈3), ratio of residual vectors (≈3) |
| **Seed / hash** | Seed `202609` |
| **Execution result** | PASS |
| **Expected evidence path** | `evidence/property/P03/P03_evidence.json` |
