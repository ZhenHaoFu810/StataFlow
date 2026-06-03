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

## Wave 7 预登记样例（HDFE Hardening）

| case_id | family | command | validation_line | python_api | dataset | risk_focus | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `w7_reghdfe_2way_cluster` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(...).fit(vce="cluster", cluster=["firm_id","year_id"])` | 手工 panel（firm × year 结构） | 2-way cluster VCE、Cameron-Gelbach-Miller 公式、PSD fix | done |
| `w7_reghdfe_savefe` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(...).fit(vce="ols", savefe=True)` | 手工 panel | `savefe` 后 FE 估计值与 LSDV dummy 系数一致 | done |
| `w7_reghdfe_2way_cluster_real` | Panel / FE / HDFE | `reghdfe` | real_data | `AbsorbingOLS(...).fit(vce="cluster", cluster=["nr","year"])` | 本地 `wagepan` 数据 | 真实数据 2-way cluster SE 与 Stata 字段级对齐（_cons SE 为已知限制） | done |
| `w7_ivreghdfe_2way_cluster` | IV / GMM | `ivreghdfe` | synthetic | `IVAbsorbingOLS(...).fit(vce="cluster", cluster=["firm_id","year_id"])` | 手工 panel | IV + 2-way cluster、一阶段 VCE 传播 | done |
| `w7_ivreghdfe_first_basic` | IV / GMM | `ivreghdfe` | synthetic | `IVAbsorbingOLS(...).fit(vce="ols", first=True)` | 手工 panel（单内生变量 + 2 工具） | 一阶段 F、Shea R²、Partial R² 对齐 | done |
| `w7_ivreghdfe_first_cluster` | IV / GMM | `ivreghdfe` | synthetic | `IVAbsorbingOLS(...).fit(vce="cluster", cluster="entity_id", first=True)` | 手工 panel | cluster-robust 一阶段 F 对齐 | planned |
| `w7_ivreghdfe_ffirst_multi` | IV / GMM | `ivreghdfe` | synthetic | `IVAbsorbingOLS(...).fit(vce="ols", ffirst=True)` | 手工 panel（2 内生 + 3 工具） | SW F、AP F、多变量偏 R² 对齐 | planned |
| `w7_ppmlhdfe_2way_cluster` | Binary / Count | `ppmlhdfe` | synthetic | `PPMLHDFE(...).fit(vce="cluster", cluster=["firm_id","year_id"])` | 手工 panel（含零值计数） | PPML + 2-way cluster、IRLS 收敛 | done |
| `w7_ppmlhdfe_separation_fe` | Binary / Count | `ppmlhdfe` | synthetic | `PPMLHDFE(..., separation="fe").fit(vce="robust")` | 手工 panel（构造 y=0 singleton） | separation(fe) 剔除观测数、剩余数据系数/SE/ll 对齐 | done |
| `w7_ppmlhdfe_eform` | Binary / Count | `ppmlhdfe` | synthetic | `PPMLHDFE(...).fit(vce="robust", eform=True)` | 手工 panel | `eform` 后 exp(b) 与 delta-method SE 对齐 | done |

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

## Wave 11 预登记样例（Postestimation & `estat` Ecosystem）

| case_id | family | command | validation_line | python_api | dataset | risk_focus | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `w11_reghdfe_stdp_ols` | Postestimation | `predict, stdp` | synthetic | `AbsorbingOLS(...).fit(vce="ols").predict(type="stdp")` | 手工 panel | reghdfe OLS stdp: sqrt(diag(X @ cov @ X.T)) | done |
| `w11_reghdfe_stdp_robust` | Postestimation | `predict, stdp` | synthetic | `AbsorbingOLS(...).fit(vce="robust").predict(type="stdp")` | 手工 panel | reghdfe robust stdp: HC1 small-sample n/(n-k_full) | done |
| `w11_reghdfe_stdp_cluster` | Postestimation | `predict, stdp` | synthetic | `AbsorbingOLS(...).fit(vce="cluster", cluster="entity_id").predict(type="stdp")` | 手工 panel | reghdfe cluster stdp | done |
| `w11_ivreghdfe_stdp_ols` | Postestimation | `predict, stdp` | synthetic | `IVAbsorbingOLS(...).fit(vce="ols").predict(type="stdp")` | 手工 panel | ivreghdfe OLS stdp | done |
| `w11_ivreghdfe_stdp_robust` | Postestimation | `predict, stdp` | synthetic | `IVAbsorbingOLS(...).fit(vce="robust").predict(type="stdp")` | 手工 panel | ivreghdfe robust stdp: n/(n-k_x_full) | done |
| `w11_ivreghdfe_stdp_cluster` | Postestimation | `predict, stdp` | synthetic | `IVAbsorbingOLS(...).fit(vce="cluster", cluster="entity_id").predict(type="stdp")` | 手工 panel | ivreghdfe cluster stdp; ~0.28% residual when cluster nests FE | done |
| `w11_ppmlhdfe_pearson` | Postestimation | `predict, pearson` | synthetic | `PPMLHDFE(...).fit().predict(type="pearson")` | 手工 panel | Pearson residual (y-mu)/sqrt(mu) | done |
| `w11_ppmlhdfe_deviance` | Postestimation | `predict, deviance` | synthetic | `PPMLHDFE(...).fit().predict(type="deviance")` | 手工 panel | Stata ppmlhdfe deviance = squared contribution, not signed residual | done |
| `w11_ppmlhdfe_working` | Postestimation | `predict, working` | synthetic | `PPMLHDFE(...).fit().predict(type="working")` | 手工 panel | Working residual (y-mu)/mu | done |
| `w11_estat_summarize` | Postestimation | `estat summarize` | synthetic | `estat_summarize(result, data)` | 手工 panel | N, mean, sd, min, max for model variables | done |
| `w11_estat_ic` | Postestimation | `estat ic` | synthetic | `estat_ic(result)` | 手工 panel | AIC/BIC after ppmlhdfe; k = df_model + 1 when constant present | done |

## Wave 8 预登记样例（RD Completion）

| case_id | family | command | validation_line | python_api | dataset | risk_focus | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `w8_bw_mserd` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="mserd")` | 手工 Sharp RD 样例 | mserd 基线回归（已有实现，w8 再验证） | done |
| `w8_bw_msesum` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="msesum")` | 手工 Sharp RD 样例 | SUM 准则带宽：`(V_l+V_r)/(B_r+B_l)²` | done |
| `w8_bw_msetwo` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="msetwo")` | 手工 Sharp RD 样例（非对称密度） | TWO 准则带宽：两侧不同 h_l ≠ h_r | done |
| `w8_bw_msecomb1` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="msecomb1")` | 手工 Sharp RD 样例 | comb1 = min(mserd, msesum) | done |
| `w8_bw_msecomb2` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="msecomb2")` | 手工 Sharp RD 样例 | comb2 = median(mserd, msesum, msetwo) | done |
| `w8_bw_cerrd` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="cerrd")` | 手工 Sharp RD 样例 | CER 缩放：`N^(-1/20)` | done |
| `w8_bw_cersum` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="cersum")` | 手工 Sharp RD 样例 | CER + SUM 交互 | done |
| `w8_bw_certwo` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="certwo")` | 手工 Sharp RD 样例 | CER + TWO 交互 | done |
| `w8_bw_cercomb1` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="cercomb1")` | 手工 Sharp RD 样例 | CER + comb1 | done |
| `w8_bw_cercomb2` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., bwselect="cercomb2")` | 手工 Sharp RD 样例 | CER + comb2 | done |
| `w8_bw_senate_all` | RD / Local Polynomial | `rdrobust` | real_data | `rdrobust(..., bwselect=<each>)` | `rdrobust_senate.dta` | 全部 9 个选择器在 senate 数据上的双跑对齐（带宽 < 0.1%，估计量 < 1e-4） | done |
| `w8_fuzzy_basic` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., fuzzy="treat")` | 手工 Fuzzy RD 样例（完美依从） | Wald = Sharp 等价性 | done |
| `w8_fuzzy_partial` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., fuzzy="treat")` | 手工 Fuzzy RD 样例（部分依从） | τ_T < 1 时 Wald 比率正确 | done |
| `w8_fuzzy_sharpbw` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., fuzzy="treat sharpbw")` | 手工 Fuzzy RD 样例 | sharpbw 带宽 = sharp RD 带宽 | done |
| `w8_fuzzy_covs` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., fuzzy="treat", covs="z")` | 手工 Fuzzy RD 样例 + 协变量 | 扩展 s-vector VCE（含 gamma 导数） | done |
| `w8_cluster_basic` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., vce="cluster", cluster="g")` | 手工 Sharp RD 样例（含组结构） | 聚类 sandwich、G 计数、CER 缩放 | done |
| `w8_cluster_nncluster` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., vce="nncluster", cluster="g")` | 手工 Sharp RD 样例 | NN 残差 + 聚类聚合 | done |
| `w8_cluster_few` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., vce="cluster", cluster="g")` | 手工 Sharp RD 样例（5 clusters/side） | 小样本聚类行为 | done |
| `w8_weights_basic` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., weights="w")` | 手工 Sharp RD 样例（所有权重=1） | 等价于无权重 | done |
| `w8_weights_double` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., weights="w")` | 手工 Sharp RD 样例（所有权重=2） | 系数不变，SE 缩小 | done |
| `w8_mp_adjust` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., masspoints="adjust")` | 手工 Sharp RD 样例（20%+ mass points） | M-based c_bw、自动 bwcheck=10 | done |
| `w8_mp_check` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., masspoints="check")` | 手工 Sharp RD 样例 | 检测但不调整 | done |
| `w8_rdplot_basic` | RD / Local Polynomial | `rdplot` | synthetic | `rdplot(..., binselect="esmv")` | `rdrobust_senate.dta` | 分箱数 J_star、分箱均值、多项式拟合线 | done |
| `w8_rdplot_nbins` | RD / Local Polynomial | `rdplot` | synthetic | `rdplot(..., nbins=(10, 15))` | `rdrobust_senate.dta` | 手动分箱覆盖 | done |
| `w8_bw_senate_all_golden` | RD / Local Polynomial | `rdrobust` | real_data | `rdrobust(..., bwselect=<each>)` | `rdrobust_senate.dta` | 全部 11 个带宽选择器 golden 双跑（系数 < 0.5%，带宽 < 1%） | done |
| `w8_fuzzy_synthetic_golden` | RD / Local Polynomial | `rdrobust` | synthetic | `rdrobust(..., fuzzy=t sharpbw)` | 手工 Fuzzy RD 样例 (n=500) | fuzzy + sharpbw 系数 + SE golden 双跑 | done |
| `w8_fuzzy_real_senate_golden` | RD / Local Polynomial | `rdrobust` | real_data | `rdrobust(..., fuzzy=fuzzy_treat sharpbw)` | `rdrobust_senate.dta` | 真实数据 fuzzy RD golden 双跑（系数/SE < 0.05%） | done |
| `w8_cluster_real_senate_golden` | RD / Local Polynomial | `rdrobust` | real_data | `rdrobust(..., vce(cluster state))` | `rdrobust_senate.dta` | cluster / nncluster VCE golden 双跑 | done |

## 维护规则

- 每个命令默认至少有一个 `synthetic` 和一个 `real_data` 样例
- 未登记条目不得进入实现
- `done` 只在门禁通过后使用

## Wave 9: DID Hardening（预登记样例）

| case_id | family | command | validation_line | Stata 命令 | 数据集 | 风险焦点 | 状态 |
|---------|--------|---------|-----------------|------------|--------|----------|------|
| `w9_di_controls_basic` | DID | `did_imputation` | synthetic | `did_imputation y id time first_treat, controls(x1) unitcontrols(x2) timecontrols(x3)` | 手工 staggered adoption 面板 | controls + unitcontrols + timecontrols 同时存在 | done |
| `w9_di_controls_collinear` | DID | `did_imputation` | synthetic | `did_imputation ..., controls(x_col)` | 手工 staggered adoption 面板 | 控制样本中完全共线，应报错 | done |
| `w9_di_pretrends_basic` | DID | `did_imputation` | synthetic | `did_imputation ..., pretrends(3)` | 手工 staggered adoption 面板（含轻微 pretrend） | pre1–pre3 系数 + joint F test | done |
| `w9_di_pretrends_no_violation` | DID | `did_imputation` | synthetic | `did_imputation ..., pretrends(3)` | 手工 staggered adoption 面板（纯正态噪声） | pre_F 不显著 | done |
| `w9_di_controls_pretrends_combo` | DID | `did_imputation` | synthetic | `did_imputation ..., controls(x1) pretrends(3)` | 手工 staggered adoption 面板 | controls + pretrends 联合 | done |
| `w9_di_wtr_basic` | DID | `did_imputation` | synthetic | `did_imputation ..., wtr(wvar)` | 手工 staggered adoption 面板 | 自定义加权平均处理效应 | done |
| `w9_di_hetby` | DID | `did_imputation` | synthetic | `did_imputation ..., hetby(group)` | 手工 staggered adoption 面板（含分组变量） | 子组异质性效应 | done |
| `w9_di_saveestimates` | DID | `did_imputation` | synthetic | `did_imputation ..., saveestimates(effect)` | 手工 staggered adoption 面板 | 保存 Y-Y0 为变量 | done |
| `w9_csdid_dr_basic` | DID | `csdid` | synthetic | `csdid y x1 x2, ivar(id) time(time) gvar(first_treat) method(drimp)` | 手工 staggered adoption 面板（含协变量） | DR ATT(g,t) 与 reg 方法对比 | done |
| `w9_csdid_dr_real_ezunem` | DID | `csdid` | real_data | `csdid uclms c1 c2 c3, method(drimp)` | `ezunem_prepared.dta` (22 cities × 9 years) | 真实数据下 DR 方法的行为 | done |
| `w9_csdid_dr_vs_reg` | DID | `csdid` | synthetic | `csdid y x1, method(drimp)` vs `method(reg)` | 手工 staggered adoption 面板 | OR 正确设定时 drimp ≈ reg | done |
| `w9_csdid_agg_simple` | DID | `csdid` | synthetic | `csdid ..., method(reg); csdid_estat simple` | 手工 staggered adoption 面板 | simple 总体平均效应 | done |
| `w9_csdid_agg_group` | DID | `csdid` | synthetic | `csdid ..., method(reg); csdid_estat group` | 手工 staggered adoption 面板 | 按 cohort 聚合 | done |
| `w9_csdid_agg_calendar` | DID | `csdid` | synthetic | `csdid ..., method(reg); csdid_estat calendar` | 手工 staggered adoption 面板 | 按 calendar time 聚合 | done |
| `w9_csdid_agg_pretrend` | DID | `csdid` | synthetic | `csdid ..., method(reg); csdid_estat pretrend` | 手工 staggered adoption 面板（含轻微 pretrend） | 事件前趋势联合检验 | done |
| `w9_di_real_ezunem_controls` | DID | `did_imputation` | real_data | `did_imputation ..., controls(pop) unitcontrols(inc)` | `ezunem.dta` 或类似公开面板 | 真实数据下 controls 的行为 | planned |
| `w9_csdid_dr_real_ezunem` | DID | `csdid` | real_data | `csdid y c1 c2 c3, method(drimp)` | `ezunem_prepared.dta` (22 cities × 9 years) | 真实数据下 DR 方法的行为 | done |

## Wave 10 预登记样例（IV Completion）

| case_id | family | command | validation_line | Stata 命令 | 数据集 | 风险焦点 | 状态 |
|---------|--------|---------|-----------------|------------|--------|----------|------|
| `w10_gmm2s_overid` | IV / GMM | `ivreghdfe` | synthetic | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) gmm2s` | 手工 panel（1 内生变量 + 2 工具变量 + 1 外生变量） | GMM2S 过度识别检验；与 2SLS 在恰好识别时等价 | done |
| `w10_gmm2s_cluster` | IV / GMM | `ivreghdfe` | synthetic | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) vce(cluster entity_id) gmm2s` | 手工 panel（含 cluster 结构） | cluster-robust GMM2S 权重矩阵与 VCE | done |
| `w10_liml_weak` | IV / GMM | `ivreghdfe` | synthetic | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) liml` | 手工 panel（弱工具变量设定） | LIML 与 2SLS 系数差异、偏差方向 | done |
| `w10_fuller_adjust` | IV / GMM | `ivreghdfe` | synthetic | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) liml fuller(1)` | 同上弱工具设定 | Fuller(1) 修正后 k-class 参数稳定性 | done |
| `w10_kclass_basic` | IV / GMM | `ivreghdfe` | synthetic | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) kclass(0.5)` | 手工 panel | k-class 估计量（k=0.5 为 2SLS/LIML 中间值） | done |
| `w10_cue_basic` | IV / GMM | `ivreghdfe` | synthetic | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) cue` | 手工 panel | CUE 数值优化收敛性与 GMM2S 等价条件 | planned |
| `w10_weakiv_test` | IV / GMM | `ivreghdfe` | synthetic | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) weakiv` | 手工 panel（弱工具设定） | Kleibergen-Paap F 与 Stock-Yogo 临界值对齐 | done |
| `w10_weakiv_cluster` | IV / GMM | `ivreghdfe` | synthetic | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) vce(cluster entity_id) weakiv` | 手工 panel（含 cluster 结构） | cluster-robust weakiv 统计量对齐 | done |
| `w10_card_gmm2s` | IV / GMM | `ivreghdfe` | real_data | `ivreghdfe lwage exper expersq black smsa reg661-reg668 smsa66 (educ = nearc4), absorb(south) gmm2s` | `card.csv`（Card 教育回报数据） | 真实数据下 GMM2S 系数/SE/Hansen J 与 Stata 对齐 | done |
| `w10_card_liml` | IV / GMM | `ivreghdfe` | real_data | `ivreghdfe lwage exper expersq black smsa reg661-reg668 smsa66 (educ = nearc4), absorb(south) liml` | `card.csv` | 真实数据下 LIML 系数/SE/k-class 与 Stata 对齐 | done |
| `w10_card_weakiv` | IV / GMM | `ivreghdfe` | real_data | `ivreghdfe lwage exper expersq (educ = nearc4), absorb(south) weakiv` | `card.dta` | 真实数据下 weakiv 统计量与 Stata 对齐 | done |

## Wave 12 预登记样例（Advanced HDFE & Performance — Round 2）

| case_id | family | command | validation_line | python_api | dataset | risk_focus | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `w12_map_small_1way` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., technique="map").fit(vce="ols")` | 手工 panel（N=10K, G=100 单 FE） | MAP 与 LSDV 系数/SE 数值等价（rtol < 1e-10） | done |
| `w12_map_small_1way_robust` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., technique="map").fit(vce="robust")` | 手工 panel（N=10K, G=100 单 FE） | MAP robust SE 与 LSDV 等价（rtol < 1e-10） | done |
| `w12_map_small_1way_cluster` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., technique="map").fit(vce="cluster", cluster="group")` | 手工 panel（N=10K, G=100 单 FE） | MAP cluster SE：slope SE ~0.5% 差异（LSDV meat 构建方式不同），_cons SE 精确匹配 | done |
| `w12_map_small_2way` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., technique="map").fit(vce="ols")` | 手工 panel（N=10K, G1=50, G2=20 双向 FE） | 双向 FE MAP 迭代收敛、OLS SE 等价（rtol < 1e-10） | done |
| `w12_map_small_2way_robust` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., technique="map").fit(vce="robust")` | 手工 panel（N=10K, G1=50, G2=20 双向 FE） | 双向 FE MAP robust SE 等价（rtol < 1e-10） | done |
| `w12_map_small_2way_cluster` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., technique="map").fit(vce="cluster", cluster="cluster")` | 手工 panel（N=10K, G1=50, G2=20 双向 FE） | 双向 FE MAP cluster SE 等价（rtol < 1e-10） | done |
| `w12_map_small_3way` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., technique="map").fit(vce="ols")` | 手工 panel（N=10K, 三组 FE） | 三组 FE MAP 收敛稳定性、OLS SE 等价（rtol < 1e-10） | done |
| `w12_map_benchmark_a` | Panel / FE / HDFE | `reghdfe` | benchmark | `AbsorbingOLS(..., technique="map").fit(vce="ols")` | `benchmark_a_single_fe.dta`（1M obs, 10K FE） | 大规模单 FE 无 OOM、运行时间 4.9s、内存 0.15GB | done |
| `w12_map_benchmark_b` | Panel / FE / HDFE | `reghdfe` | benchmark | `AbsorbingOLS(..., technique="map").fit(vce="ols")` | `benchmark_b_two_way_fe.dta`（1M obs, 5K+200 FE） | 大规模双向 FE 无 OOM、运行时间 5.9s、内存 0.17GB | done |
| `w12_map_benchmark_c` | Panel / FE / HDFE | `reghdfe` | benchmark | `AbsorbingOLS(..., technique="map").fit(vce="ols")` | `benchmark_c_unbalanced_cluster.dta`（2M obs, 20K+5K FE） | 大规模双向 FE 无 OOM、运行时间 29.7s、内存 0.33GB | done |
| `w12_map_benchmark_a_cluster` | Panel / FE / HDFE | `reghdfe` | benchmark | `AbsorbingOLS(..., technique="map").fit(vce="cluster", cluster="firm_id")` | `benchmark_a_single_fe.dta`（1M obs, 10K FE） | 大规模单 FE + cluster 无 OOM、运行时间 24.3s | done |
| `w12_map_benchmark_b_cluster` | Panel / FE / HDFE | `reghdfe` | benchmark | `AbsorbingOLS(..., technique="map").fit(vce="cluster", cluster="firm_id")` | `benchmark_b_two_way_fe.dta`（1M obs, 5K+200 FE） | 大规模双向 FE + cluster 无 OOM、运行时间 13.9s | done |
| `w12_map_benchmark_c_cluster` | Panel / FE / HDFE | `reghdfe` | benchmark | `AbsorbingOLS(..., technique="map").fit(vce="cluster", cluster="cluster_id")` | `benchmark_c_unbalanced_cluster.dta`（2M obs, 20K+5K FE） | 大规模双向 FE + cluster 无 OOM、运行时间 46.7s | done |
| `w12_map_real_wagepan` | Panel / FE / HDFE | `reghdfe` | real_data | `AbsorbingOLS(..., technique="map").fit(vce="cluster")` | 本地 `wagepan` 数据 | 真实数据下 MAP 与 LSDV 等价性 | planned |

## Wave 12 Round 2b/3 预登记样例（个体斜率 + Driscoll-Kraay）

| case_id | family | command | validation_line | python_api | dataset | risk_focus | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `w12_slopes_basic` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., absorb="firm_id##c.time").fit(vce="ols")` | 手工 panel（N=50 firms, T=10） | 截距+斜率吸收系数/SE 与 Stata 对齐 | done |
| `w12_slopes_multi` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., absorb="firm_id##c.(x1 x2)").fit(vce="ols")` | 手工 panel | 多斜率变量同时吸收 | done |
| `w12_slopes_only` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., absorb="firm_id#c.time").fit(vce="ols")` | 手工 panel | 纯斜率 `#c.`（无截距）数值稳定性 | done |
| `w12_slopes_zero` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(..., absorb="firm_id##c.time").fit(vce="ols")` | 手工 panel（某组 slope 全为 0） | 分母为 0 边界处理 | done |
| `w12_slopes_real_wagepan` | Panel / FE / HDFE | `reghdfe` | real_data | `reghdfe(..., absorb="nr##c.year")` | 本地 `wagepan` 数据 | 真实数据下斜率吸收行为 | done |
| `w12_dkraay_basic` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(...).fit(vce="dkraay")` | 手工 panel（N=50, T=10） | DK 系数/SE 与 Stata 对齐 | done |
| `w12_dkraay_truncate` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(...).fit(vce="dkraay")` | 手工 panel（N=50, T=3） | 带宽截断至 T-1 | done |
| `w12_dkraay_bw1` | Panel / FE / HDFE | `reghdfe` | synthetic | `AbsorbingOLS(...).fit(vce="dkraay_1")` | 手工 panel（N=50, T=10） | bw=1 退化为 cluster(time) | done |
| `w12_dkraay_real_wagepan` | Panel / FE / HDFE | `reghdfe` | real_data | `AbsorbingOLS(...).fit(vce="dkraay")` | 本地 `wagepan` 数据 | 真实数据下 DK 标准误行为 | done |

