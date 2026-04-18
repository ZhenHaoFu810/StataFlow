# 测试样例目录清单

## 字段定义

| 字段 | 含义 |
| --- | --- |
| `case_id` | 测试样例唯一标识 |
| `family` | 命令族 |
| `command` | 对应 Stata 命令 |
| `validation_line` | `synthetic` 或 `real_data` |
| `python_api` | 对应 Python API |
| `dataset` | 数据集或样例来源 |
| `risk_focus` | 主要风险点 |
| `status` | `planned` / `ready` / `done` |

## 已完成样例

| case_id | family | command | validation_line | python_api | dataset | risk_focus | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `p0_min_ols_auto` | Linear Base | `regress` | synthetic | `OLS.fit(vce="ols")` | 最小手工样例 | runner、结构化导出、字段对齐 | done |
| `p1_ols_basic` | Linear Base | `regress` | synthetic | `OLS.fit(vce="ols")` | 手工样例 | 系数、自由度、R2 | done |
| `p1_ols_missing_drop` | Linear Base | `regress` | synthetic | `OLS.fit(vce="ols")` | 手工样例 | 缺失值剔除 | done |
| `p1_ols_noconstant` | Linear Base | `regress, noconstant` | synthetic | `OLS(..., add_constant=False)` | 手工样例 | 无常数项语义 | done |
| `p1_collinearity_drop` | Linear Base | `regress` | synthetic | `OLS.fit(vce="ols")` | 手工样例 | 共线性剔除 | done |
| `p1_robust_hc1` | Linear Base | `regress, vce(robust)` | synthetic | `OLS.fit(vce="robust")` | 手工样例 | HC1 协方差 | done |
| `p1_cluster_firm` | Linear Base | `regress, vce(cluster firm_id)` | synthetic | `OLS.fit(vce="cluster", cluster="firm_id")` | 手工 panel 样例 | 单聚类修正 | done |
| `p2_aweight_basic` | Linear Base | `regress [aweight=...]` | synthetic | `OLS(..., weights=..., weight_type="aweight")` | 横截面样例 | 权重语义 | done |
| `p2_aweight_missing_weight` | Linear Base | `regress [aweight=...]` | synthetic | `OLS(..., weights=..., weight_type="aweight")` | 手工样例 | 缺失权重剔除 | done |
| `p2_fe_basic` | Panel / FE / HDFE | `xtreg ..., fe` | synthetic | `FixedEffectsOLS.fit(vce="ols")` | 面板样例 | within 转换、FE 自由度 | done |
| `p2_fe_cluster` | Panel / FE / HDFE | `xtreg ..., fe vce(cluster firm_id)` | synthetic | `FixedEffectsOLS.fit(vce="cluster", cluster="firm_id")` | 面板样例 | FE + cluster | done |

## 已登记但未实现的真实数据样例

| case_id | family | command | validation_line | python_api | dataset | risk_focus | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `real_ff3_time_series` | Linear Base | `regress` | real_data | `OLS.fit(vce="ols")` | 本地 `Fama-French 3 factors` 数据 | 真实金融数据回归基线 | ready |
| `real_panel_wooldridge_firm` | Panel / FE / HDFE | `xtreg ..., fe` | real_data | `FixedEffectsOLS.fit(vce="ols")` | 本地 `wagepan` / `Grunfeld` 数据 | 真实 panel FE 语义 | ready |
| `p3_areg_basic` | Panel / FE / HDFE | `areg` | synthetic | `AbsorbingOLS(..., absorb="turn").fit()` | 手工样例（auto 风格） | 单吸收变量、df_a、_cons | done |
| `p3_areg_real_panel` | Panel / FE / HDFE | `areg` | real_data | `AbsorbingOLS(..., absorb="nr").fit()` | 本地 `wagepan` / `Grunfeld` 数据 | 真实数据下的 FE 吸收 | done |
| `p3_reghdfe_basic` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., absorb=["entity_id"]).fit(vce="ols")` | 手工样例 | 多 FE 吸收（1 FE）、系数对齐、`df_a` 含常数 | done |
| `p3_reghdfe_two_fe` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., absorb=["entity_id","time_id"]).fit(vce="ols")` | 手工样例 | 双向 FE、df_a = G1+G2-1 | done |
| `p3_reghdfe_cluster` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., absorb=["entity_id","time_id"]).fit(vce="cluster")` | 手工 panel 样例 | FE + cluster、singleton drop、cluster 嵌套 FE 时 df_a 扣减 | done |
| `p3_reghdfe_keepsingletons` | Panel / FE / HDFE | `reghdfe` | synthetic | `reghdfe(..., absorb="g1", keepsingletons=True)` | 手工样例（含 singleton 组） | `keepsingletons` 样本保留、predict 子选项（xb/xbd/d/residuals/dresiduals）对齐 | done |
| `p3_reghdfe_real_panel` | Panel / FE / HDFE | `reghdfe` | real_data | `AbsorbingOLS(..., absorb=["nr","year"]).fit(vce="cluster", cluster="nr")` | 本地 `wagepan` 数据 | 真实数据双向 FE + cluster、time-invariant 变量自动 omitted | done |
| `w2_ivregress_basic` | IV / GMM | `ivregress 2sls` | synthetic | `IV2SLS(...).fit(vce="ols")` | 手工样例 | 2SLS 点估计、标准误 | done |
| `w2_ivregress_cluster` | IV / GMM | `ivregress 2sls` | synthetic | `IV2SLS(...).fit(vce="cluster")` | 手工 panel 样例 | cluster-robust SE | done |
| `w2_ivregress_real_card` | IV / GMM | `ivregress 2sls` | real_data | `IV2SLS(...).fit()` | Card returns-to-schooling 数据 | 真实数据 IV 对齐 | done |
| `w2_ivreghdfe_basic` | IV / GMM | `ivreghdfe` | synthetic | `IVAbsorbingOLS(..., absorb=[...]).fit(vce="ols")` | 手工样例 | FE + 2SLS 系数对齐 | done |
| `w2_ivreghdfe_cluster` | IV / GMM | `ivreghdfe` | synthetic | `IVAbsorbingOLS(..., absorb=[...]).fit(vce="cluster")` | 手工 panel 样例 | 双 FE + cluster-robust SE | done |
| `w2_ivreghdfe_real_panel` | IV / GMM | `ivreghdfe` | real_data | `IVAbsorbingOLS(..., absorb=[...]).fit(vce="cluster")` | 本地 `wagepan` 数据 | 真实数据双向 FE + IV + cluster | done |
| `w3_logit_basic` | Binary / Count | `logit` | synthetic | `Logit(...).fit(vce="ols")` | 手工样例 | MLE 收敛、系数、ll、pseudo-R²、chi2 | done |
| `w3_logit_real` | Binary / Count | `logit` | real_data | `Logit(...).fit()` | `Mroz` 劳动参与数据 | 真实二元响应数据对齐 | done |
| `w3_probit_basic` | Binary / Count | `probit` | synthetic | `Probit(...).fit(vce="ols")` | 手工样例 | MLE 收敛、系数、ll、pseudo-R²、chi2 | done |
| `w3_probit_real` | Binary / Count | `probit` | real_data | `Probit(...).fit()` | `Mroz` 劳动参与数据 | 真实二元响应数据对齐 | done |
| `w3_poisson_basic` | Binary / Count | `poisson` | synthetic | `Poisson(...).fit(vce="ols")` | 手工样例 | MLE 收敛、系数、ll、deviance、chi2 | done |
| `w3_poisson_real` | Binary / Count | `poisson` | real_data | `Poisson(...).fit()` | `crime1` 逮捕次数数据 | 真实计数数据对齐 | done |
| `w3_ppmlhdfe_basic` | Binary / Count | `ppmlhdfe` | synthetic | `PPMLHDFE(..., absorb=[...]).fit(vce="robust")` | 手工 panel 样例 | HDFE + IRLS 收敛、系数、ll | done |
| `w3_ppmlhdfe_cluster` | Binary / Count | `ppmlhdfe` | synthetic | `PPMLHDFE(..., absorb=[...]).fit(vce="cluster")` | 手工 panel 样例 | 双 FE + cluster-robust SE | done |
| `w3_ppmlhdfe_real_gravity` | Binary / Count | `ppmlhdfe` | real_data | `PPMLHDFE(..., absorb=[...]).fit(vce="robust")` | `countymurders` CA 县级面板 | 零值、HDFE、双向 FE | done |
| `p3_ppmlhdfe_fit_stats` | Binary / Count | `ppmlhdfe` | synthetic | `PPMLHDFE(..., absorb=[...]).fit(vce="robust")` | 手工 panel 样例 | deviance、pseudo-R² 与 Stata 17 对齐 | done |
| `w4_did_imputation_basic` | DID / Event Study Extensions | `did_imputation` | synthetic | `DIDImputation(...).fit(cluster="id", allhorizons=True, autosample=True)` | 手工 staggered adoption 样例 | imputation FE、事件时间系数、cluster SE | done |
| `w4_eventstudyinteract_basic` | DID / Event Study Extensions | `eventstudyinteract` | synthetic | `EventStudyInteract(...).fit(vce="cluster", cluster="id")` | 手工 staggered adoption 样例 | IW estimator、双向FE、cluster SE | done |
| `w4_csdid_basic` | DID / Event Study Extensions | `csdid` | synthetic | `CSDID(...).fit(method="reg")` | 手工 staggered adoption 样例 | group-time ATT、事件研究聚合 | done |
| `w4_did_imputation_real_ezunem` | DID / Event Study Extensions | `did_imputation` | real_data | `DIDImputation(...).fit(cluster="city", allhorizons=True, autosample=True)` | Wooldridge `ezunem` 面板 (22 cities × 9 years) | 真实数据动态效应、 autosample 缺失处理 | done |
| `w4_eventstudyinteract_real_ezunem` | DID / Event Study Extensions | `eventstudyinteract` | real_data | `EventStudyInteract(...).fit(vce="cluster", cluster="city")` | Wooldridge `ezunem` 面板 (22 cities × 9 years) | 真实数据IW估计、相对时间虚拟变量生成 | done |
| `w4_csdid_real_ezunem` | DID / Event Study Extensions | `csdid` | real_data | `CSDID(...).fit(method="reg", vce="cluster", cluster="city")` | Wooldridge `ezunem` 面板 (22 cities × 9 years) | 真实数据group-time ATT、 never-treated 默认控制组 | done |
| `a1_rdrobust_basic` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., h=...)` | 手工 Sharp RD 样例 | 局部多项式点估计、带宽内样本、nn VCE | done |
| `a1_rdrobust_kernel` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., kernel=...)` | 手工 Sharp RD 样例 | triangular / epanechnikov / uniform 核对齐 | done |
| `a1_rdrobust_bandwidth` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., h=...)` | 手工 Sharp RD 样例 | 带宽变化对有效样本量的影响 | done |
| `a1_rdrobust_senate` | RD / Local Polynomial | `rdrobust` | real_data | `rdrobust(..., h=15.0)` | `rdrobust_senate.dta` (Cattaneo et al. 2015) | 真实选举数据 Sharp RD dual-run (Stata 17) | done |

## Wave 5 预登记样例（Postestimation）

| case_id | family | command | validation_line | python_api | dataset | risk_focus | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `w5_predict_ols_basic` | Postestimation | `predict` | synthetic | `OLS(...).fit().predict(type="xb"/"residuals")` | 手工样例 | 线性模型 xb、残差对齐 | done |
| `w5_predict_logit_basic` | Postestimation | `predict` | synthetic | `Logit(...).fit().predict(type="xb"/"pr")` | 手工样例 | 二元模型 xb、概率转换 | done |
| `w5_predict_real_wagepan` | Postestimation | `predict` | real_data | `FixedEffectsOLS(...).fit().predict(type="xb"/"residuals")` | 本地 `wagepan` 数据 | 真实面板 FE 模型的 xb 与残差 | done |
| `w5_predict_real_mroz` | Postestimation | `predict` | real_data | `Logit(...).fit().predict(type="pr"/"xb")` | 本地 `Mroz` 数据 | 真实二元数据概率预测 | done |
| `w5_margins_logit_basic` | Postestimation | `margins` | synthetic | `Logit(...).fit().margins(type="dydx"/"atmeans")` | 手工样例 | Logit AME/MEM、delta-method SE | done |
| `w5_margins_probit_basic` | Postestimation | `margins` | synthetic | `Probit(...).fit().margins(type="dydx"/"atmeans")` | 手工样例 | Probit AME/MEM、正态 PDF 精度 | done |
| `w5_margins_ols_basic` | Postestimation | `margins` | synthetic | `OLS(...).fit().margins(type="dydx")` | 手工样例 | 线性模型 dydx 等于系数本身 | done |
| `w5_margins_real_mroz` | Postestimation | `margins` | real_data | `Logit(...).fit().margins(type="dydx"/"atmeans")` | 本地 `Mroz` 数据 | 真实二元数据 AME/MEM 对齐 | done |
| `w5_margins_real_crime1` | Postestimation | `margins` | real_data | `Poisson(...).fit().margins(type="dydx"/"atmeans")` | 本地 `crime1` 数据 | 真实计数数据 AME/MEM 对齐 | done |

## 维护规则

- 每个命令默认至少有一个 `synthetic` 和一个 `real_data` 样例
- 未登记条目不得进入实现
- `done` 只在门禁通过后使用
