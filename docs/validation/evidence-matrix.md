# Evidence Matrix

本附录矩阵汇总每个已实现命令的对外证据。  
判定口径见 [Validation Policy](./validation-policy.md)。

## Summary Table

| Command | Status | Synthetic evidence | Real-data evidence | Public interpretation |
| --- | --- | --- | --- | --- |
| `regress` | stable | `p1_ols_basic` | `v1_regress_real_grunfeld` | 全功能基线命令，字段级对齐 |
| `xtreg, fe` | stable | `p2_fe_basic` | `v1_xtreg_fe_real_grunfeld` | within FE 路径验证完成 |
| `areg` | stable | `p3_areg_basic` | `p3_areg_real_panel` | 单吸收 FE 路径验证完成 |
| `reghdfe` | validated subset | `p3_reghdfe_basic` / `p3_reghdfe_cluster` | `p3_reghdfe_real_panel` | 已验证 1-2 FE + single cluster 高频子集 |
| `ivregress 2sls` | stable | `w2_ivregress_basic` | `w2_ivregress_real_card` | 2SLS 路径验证完成 |
| `ivreghdfe` | validated subset | `w2_ivreghdfe_basic` | `w2_ivreghdfe_real_panel` | 已验证 absorbed IV 高频子集 |
| `logit` | stable | `w3_logit_basic` | `w3_logit_real` | z 推断字段级对齐 |
| `probit` | stable | `w3_probit_basic` | `w3_probit_real` | z 推断字段级对齐 |
| `poisson` | stable | `w3_poisson_basic` | `w3_poisson_real` | MLE / count 路径验证完成 |
| `ppmlhdfe` | validated subset | `w3_ppmlhdfe_basic` | `w3_ppmlhdfe_real_gravity` | 已验证 1-2 FE + offset/exposure 高频子集 |
| `did_imputation` | validated subset | `w4_did_imputation_basic` | `w4_did_imputation_real_ezunem` | BJS 高频路径已验证 |
| `eventstudyinteract` | validated subset | `w4_eventstudyinteract_basic` | `w4_eventstudyinteract_real_ezunem` | IW estimator 高频路径已验证 |
| `csdid` | validated subset | `w4_csdid_basic` | `w4_csdid_real_ezunem` | `method="reg"` 高频路径已验证 |
| `rdrobust` | validated subset | `a1_rdrobust_basic` | `a1_rdrobust_senate` | sharp RD + `bwselect="mserd"` / `covs()` 子集已验证 |

## Command-by-Command Evidence

### `regress`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `p1_ols_basic` | synthetic | `regress y x1 x2` | `OLS.fit(vce="ols")` | `nobs`, `df_model`, `df_resid`, `r2`, `r2_adj`, `rmse`, `f_stat`, coefficients, SE | passed | `tests/golden/test_p1_ols_basic.py` |
| `v1_regress_real_grunfeld` | `grunfeld` | `regress inv value capital` | `stataflow.compat.stata.regress` | `nobs`, `df_model`, `df_resid`, `r2`, `r2_adj`, `rmse`, `f_stat`, coefficients, SE | passed | `tests/golden/test_v1_regress_real_grunfeld.py` |

### `xtreg, fe`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `p2_fe_basic` | synthetic | `xtreg y x1 x2, fe` | `FixedEffectsOLS.fit(vce="ols")` | `nobs`, `df_model`, `df_resid`, `r2_w`, `rmse`, `f_stat`, coefficients, SE | passed | `tests/golden/test_p2_fe_basic.py` |
| `v1_xtreg_fe_real_grunfeld` | `grunfeld` | `xtset firm year; xtreg inv value capital, fe` | `stataflow.compat.stata.xtreg_fe` | `nobs`, `df_model`, `df_resid`, `r2_w`, `rmse`, `f_stat`, slope coefficients, SE | passed | `tests/golden/test_v1_xtreg_fe_real_grunfeld.py` |

Known difference:
- wrapper 证据以公开 surface 为准，聚焦 slope coefficients 与 within fit statistics；Stata 输出中的 FE constant 不作为 wrapper 硬字段。

### `areg`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `p3_areg_basic` | synthetic | `areg y x1 x2, absorb(turn)` | `AbsorbingOLS(..., absorb="turn").fit()` | `df_a`, coefficients, SE | passed | `tests/golden/test_p3_areg_basic.py` |
| `p3_areg_real_panel` | `wagepan` | `areg lwage educ exper, absorb(nr)` | `AbsorbingOLS(..., absorb="nr").fit()` | `nobs`, `df_model`, `df_resid`, `df_a`, coefficients, SE | passed | `tests/golden/test_p3_areg_real_panel.py` |

### `reghdfe`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `p3_reghdfe_basic` | synthetic | `reghdfe y x1 x2, absorb(entity_id)` | `stataflow.compat.stata.reghdfe` | coefficients, SE, `df_a` | passed | `tests/golden/test_p3_reghdfe_basic.py` |
| `p3_reghdfe_cluster` | synthetic | `reghdfe y x1 x2, absorb(entity_id time_id) vce(cluster entity_id)` | `stataflow.compat.stata.reghdfe` | coefficients, SE, cluster semantics | passed | `tests/golden/test_p3_reghdfe_cluster.py` |
| `p3_reghdfe_real_panel` | `wagepan` | `reghdfe lwage educ exper union, absorb(nr year) vce(cluster nr)` | `stataflow.compat.stata.reghdfe` | `nobs`, `df_model`, `df_resid`, `df_a`, coefficients, SE | passed | `tests/golden/test_p3_reghdfe_real_panel.py` |

Current statement:
- 已验证子集是 1-2 个 categorical absorbs、single cluster、singleton handling、当前公开 `predict` 语义。
- 不宣称完整复现多路聚类、斜率吸收、全部社区命令表面。

### `ivregress 2sls`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w2_ivregress_basic` | synthetic | `ivregress 2sls y x1 (x2 = z)` | `IV2SLS.fit(vce="ols")` | coefficients, SE | passed | `tests/golden/test_w2_ivregress_basic.py` |
| `w2_ivregress_real_card` | `card` | `ivregress 2sls ...` | `stataflow.compat.stata.ivregress_2sls` | `nobs`, `df_model`, coefficients, SE | passed | `tests/golden/test_w2_ivregress_real_card.py` |

### `ivreghdfe`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w2_ivreghdfe_basic` | synthetic | `ivreghdfe y x1 (x2 = z), absorb(g1)` | `stataflow.compat.stata.ivreghdfe` | coefficients, SE, `df_a` | passed | `tests/golden/test_w2_ivreghdfe_basic.py` |
| `w2_ivreghdfe_real_panel` | `wagepan` | `ivreghdfe ... , absorb(nr year) vce(cluster nr)` | `stataflow.compat.stata.ivreghdfe` | `nobs`, `df_model`, `df_resid`, `df_a`, coefficients, SE | passed | `tests/golden/test_w2_ivreghdfe_real_panel.py` |

Current statement:
- 已验证子集为 absorbed IV + single cluster 高频路径。
- 不宣称 first-stage diagnostics / weak-IV 全功能复现。

### `logit`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w3_logit_basic` | synthetic | `logit y x1 x2` | `Logit.fit(vce="ols")` | `ll`, `chi2`, coefficients, SE, p-values, CI | passed | `tests/golden/test_w3_logit_basic.py` |
| `w3_logit_real` | `mroz` | `logit inlf nwifeinc educ ...` | `Logit.fit(vce="ols")` | `nobs`, `df_model`, `ll`, `chi2`, coefficients, SE, p-values, CI | passed | `tests/golden/test_w3_logit_real.py` |

### `probit`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w3_probit_basic` | synthetic | `probit y x1 x2` | `Probit.fit(vce="ols")` | `ll`, `chi2`, coefficients, SE, p-values, CI | passed | `tests/golden/test_w3_probit_basic.py` |
| `w3_probit_real` | `mroz` | `probit inlf nwifeinc educ ...` | `Probit.fit(vce="ols")` | `nobs`, `df_model`, `ll`, `chi2`, coefficients, SE, p-values, CI | passed | `tests/golden/test_w3_probit_real.py` |

### `poisson`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w3_poisson_basic` | synthetic | `poisson y x1 x2` | `Poisson.fit(vce="ols")` | `ll`, `deviance`, `chi2`, coefficients, SE, p-values, CI | passed | `tests/golden/test_w3_poisson_basic.py` |
| `w3_poisson_real` | `crime1` | `poisson narr86 pcnv avgsen ...` | `Poisson.fit(vce="ols")` | `nobs`, `df_model`, `ll`, `deviance`, `chi2`, coefficients, SE, p-values, CI | passed | `tests/golden/test_w3_poisson_real.py` |

### `ppmlhdfe`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w3_ppmlhdfe_basic` | synthetic | `ppmlhdfe y x1 x2, absorb(g1 g2)` | `stataflow.compat.stata.ppmlhdfe` | `ll`, coefficients, SE, p-values, CI | passed | `tests/golden/test_w3_ppmlhdfe_basic.py` |
| `p3_ppmlhdfe_fit_stats` | synthetic | `ppmlhdfe ...` | `PPMLHDFE.fit(vce="robust")` | `deviance`, `pseudo_r2` | passed | `tests/golden/test_p3_ppmlhdfe_fit_stats.py` |
| `w3_ppmlhdfe_real_gravity` | `countymurders_ca` | `ppmlhdfe murders density ... , absorb(countyid year)` | `stataflow.compat.stata.ppmlhdfe` | `nobs`, `df_model`, `df_a`, `ll`, coefficients, SE, p-values, CI | passed | `tests/golden/test_w3_ppmlhdfe_real_gravity.py` |

Current statement:
- 已验证子集为 1-2 FE、offset/exposure、当前 IRLS / inference 语义。
- 不宣称 separation 等全部社区命令边界已复现。

### `did_imputation`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w4_did_imputation_basic` | synthetic | `did_imputation ...` | `stataflow.compat.stata.did_imputation` | event-time estimates, SE | passed | `tests/golden/test_w4_did_imputation_basic.py` |
| `w4_did_imputation_real_ezunem` | `ezunem` | `did_imputation ... , allhorizons autosample cluster(city)` | `stataflow.compat.stata.did_imputation` | event-time estimates, SE | passed | `tests/golden/test_w4_did_imputation_real_ezunem.py` |

### `eventstudyinteract`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w4_eventstudyinteract_basic` | synthetic | `eventstudyinteract ...` | `stataflow.compat.stata.eventstudyinteract` | event-time estimates, SE | passed | `tests/golden/test_w4_eventstudyinteract_basic.py` |
| `w4_eventstudyinteract_real_ezunem` | `ezunem` | `eventstudyinteract ... , absorb(city year) vce(cluster city)` | `stataflow.compat.stata.eventstudyinteract` | event-time estimates, SE | passed | `tests/golden/test_w4_eventstudyinteract_real_ezunem.py` |

### `csdid`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `w4_csdid_basic` | synthetic | `csdid ... , method(reg)` | `stataflow.compat.stata.csdid` | ATT(g,t), aggregated event-study estimates, SE | passed | `tests/golden/test_w4_csdid_basic.py` |
| `w4_csdid_real_ezunem` | `ezunem` | `csdid ... , method(reg) cluster(city)` | `stataflow.compat.stata.csdid` | aggregated event-study estimates, SE | passed | `tests/golden/test_w4_csdid_real_ezunem.py` |

### `rdrobust`

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `a1_rdrobust_basic` | synthetic | `rdrobust y x, c(0) h(0.5)` | `stataflow.compat.stata.rdrobust` | `tau_cl`, bandwidth-window counts | passed | `tests/test_rdrobust.py` |
| `a1_rdrobust_senate` | `rdrobust_senate` | `rdrobust vote margin, c(0) h(15)` | `stataflow.compat.stata.rdrobust` | `tau_cl`, `tau_bc`, `se_tau_cl`, `se_tau_rb` | passed | `tests/test_rdrobust.py` |
| `a1_rdrobust_bwselect` | `rdrobust_senate` | `rdrobust vote margin, c(0) bwselect(mserd)` | `stataflow.compat.stata.rdrobust` | `tau_cl`, `tau_bc`, `se_tau_cl`, `se_tau_rb`, `h_l`, `b_l` | passed_with_documented_tolerance | `tests/test_rdrobust.py` |

Known difference:
- 自动带宽选择属于 plug-in selector 路径，容差比 deterministic path 宽，但在政策中显式登记。

## Out-of-Sample Validation Evidence

本轮（Validation Package 001）新增 OOS 公开真实数据验证，独立于开发期 `tests/golden/` 证据。

### OOS Summary

| Family | Cases | Passed | Blocked |
| --- | --- | --- | --- |
| linear | 5 | 5 | 0 |
| iv | 2 | 2 | 0 |
| glm | 5 | 5 | 0 |
| did | 3 | 2 | 1 |
| rd | 2 | 2 | 0 |
| **Total** | **17** | **16** | **1** |

### `regress` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_regress_airfare` | `airfare` | `regress lfare ldist concen y98 y99 y00` | `stataflow.compat.stata.regress` | `nobs`, `df_model`, `df_resid`, `r2`, `r2_adj`, `rmse`, `f_stat`, coefficients, SE | passed | `scripts/validation/oos/run_oos_linear.py` |

### `xtreg, fe` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_xtreg_fe_airfare` | `airfare` | `xtreg lfare concen y98 y99 y00, fe` | `stataflow.compat.stata.xtreg_fe` | `nobs`, `df_model`, `df_resid`, `r2_w`, `rmse`, `f_stat`, coefficients, SE | passed | `scripts/validation/oos/run_oos_linear.py` |

### `areg` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_areg_airfare` | `airfare` | `areg lfare concen, absorb(id)` | `stataflow.compat.stata.areg` | `nobs`, `df_model`, `df_resid`, `df_a`, `r2`, `r2_adj`, `rmse`, `f_stat`, coefficients, SE | passed | `scripts/validation/oos/run_oos_linear.py` |

### `reghdfe` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_reghdfe_airfare` | `airfare` | `reghdfe lfare concen, absorb(id year) vce(cluster id)` | `stataflow.compat.stata.reghdfe` | `nobs`, `df_model`, `df_resid`, `df_a`, `r2`, `r2_adj`, `rmse`, `f_stat`, coefficients, SE | passed | `scripts/validation/oos/run_oos_linear.py` |
| `oos_reghdfe_airfare_factor` | `airfare` | `reghdfe lfare i.year##c.ldist, absorb(id)` | `stataflow.compat.stata.reghdfe` | `nobs`, `df_model`, `df_resid`, `df_a`, `r2`, `r2_adj`, `rmse`, `f_stat`, coefficients, SE | passed | `scripts/validation/oos/run_oos_linear.py` |

### `ivregress 2sls` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_ivregress_card` | `card` | `ivregress 2sls lwage exper expersq smsa south (educ = nearc2 nearc4)` | `stataflow.compat.stata.ivregress_2sls` | `nobs`, `df_model`, `df_resid`, `f_stat`, coefficients, SE | passed | `scripts/validation/oos/run_oos_iv.py` |

### `ivreghdfe` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_ivreghdfe_wagepan` | `wagepan` | `ivreghdfe lwage hours fin (union = married), absorb(nr year) vce(cluster nr)` | `stataflow.compat.stata.ivreghdfe` | `nobs`, `df_model`, `df_resid`, `df_a`, `f_stat`, coefficients, SE | passed | `scripts/validation/oos/run_oos_iv.py` |

### `logit` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_logit_vote1` | `vote1` | `logit democA lexpendA lexpendB prtystrA` | `stataflow.compat.stata.logit` | `nobs`, `df_model`, `ll`, `chi2`, coefficients, SE | passed | `scripts/validation/oos/run_oos_glm.py` |
| `oos_logit_smoke_factor` | `smoke` | `logit smoker educ age i.white##c.income` | `stataflow.compat.stata.logit` | `nobs`, `df_model`, `ll`, `chi2`, coefficients, SE | passed | `scripts/validation/oos/run_oos_glm.py` |

### `probit` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_probit_vote1` | `vote1` | `probit democA lexpendA lexpendB prtystrA` | `stataflow.compat.stata.probit` | `nobs`, `df_model`, `ll`, `chi2`, coefficients, SE | passed | `scripts/validation/oos/run_oos_glm.py` |

### `poisson` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_poisson_fertil1` | `fertil1` | `poisson kids educ age agesq black` | `stataflow.compat.stata.poisson` | `nobs`, `df_model`, `ll`, `chi2`, coefficients, SE | passed | `scripts/validation/oos/run_oos_glm.py` |

### `ppmlhdfe` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_ppmlhdfe_fertil1` | `fertil1` | `ppmlhdfe kids educ age agesq black, absorb(year) vce(robust)` | `stataflow.compat.stata.ppmlhdfe` | `nobs`, `df_model`, `df_a`, `ll`, coefficients, SE | passed | `scripts/validation/oos/run_oos_glm.py` |

### `did_imputation` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_did_imputation_jtrain` | `jtrain` | `did_imputation lhrsemp fcode year first_treat, allhorizons autosample cluster(fcode)` | `stataflow.compat.stata.did_imputation` | event-time estimates, SE | blocked | `scripts/validation/oos/run_oos_did.py` |

Blocked reason:
- JTRAIN 只有 3 个时期（1987–1989），不足以让 Stata `did_imputation` 对所有 cohort 做 FE imputation。Stata 自动 drop 到 122 obs 并 suppress 大部分系数；Python 更宽松，继续输出 390 obs。这是短面板上的行为差异，非算法错误，已记录。

### `eventstudyinteract` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_eventstudyinteract_jtrain` | `jtrain` | `eventstudyinteract lhrsemp Dm2 D0 Dp1, cohort(first_treat) control_cohort(never_treated) absorb(fcode year) vce(cluster fcode)` | `stataflow.compat.stata.eventstudyinteract` | event-time estimates, SE | passed | `scripts/validation/oos/run_oos_did.py` |

### `csdid` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_csdid_jtrain` | `jtrain` | `csdid lhrsemp, ivar(fcode) time(year) gvar(first_treat) method(reg)` | `stataflow.compat.stata.csdid` | aggregated event-study estimates, SE | passed | `scripts/validation/oos/run_oos_did.py` |

### `rdrobust` — OOS

| case_id | Dataset | Stata command | Python API | Hard fields | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `oos_rdrobust_senate_covs` | `rdrobust_senate` | `rdrobust vote margin, c(0) h(15) covs(termshouse)` | `stataflow.compat.stata.rdrobust` | `tau_cl`, `tau_bc`, `se_tau_cl`, `se_tau_rb`, `nobs` | passed | `scripts/validation/oos/run_oos_rd.py` |
| `oos_rdrobust_senate_mserd` | `rdrobust_senate` | `rdrobust vote margin, c(0) bwselect(mserd)` | `stataflow.compat.stata.rdrobust` | `tau_cl`, `tau_bc`, `se_tau_cl`, `se_tau_rb`, `nobs` | passed_with_documented_tolerance | `scripts/validation/oos/run_oos_rd.py` |

Known difference:
- `oos_rdrobust_senate_mserd` 使用自动带宽选择（plug-in selector），Stata 与 Python 的迭代数值路径存在微小差异，容差已按 validation policy 放宽并记录。

## Artifact Entry Points

### Development-time evidence

- Generated summary artifact: `research/results/validation/evidence-summary.md`
- Structured JSON artifact: `research/results/validation/evidence-summary.json`

### Out-of-sample evidence (Validation Package 001)

- Master Markdown summary: `research/results/validation/oos/oos_master_summary.md`
- Master JSON summary: `research/results/validation/oos/oos_master_summary.json`
- Family summaries: `research/results/validation/oos/linear_summary.json`, `iv_summary.json`, `glm_summary.json`, `did_summary.json`, `rd_summary.json`
- Per-case reports: `research/results/validation/oos/case_*.json`
