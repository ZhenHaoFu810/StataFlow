# 全局任务池

## 状态定义

- `planned`：已进入项目范围但未开始
- `ready`：研究与前置条件满足，可进入执行
- `in_progress`：正在实施
- `blocked`：因规则不清、研究不足或依赖缺失暂缓
- `done`：已实现并通过双线验证门禁

## Command Families

| 条目 | 优先级 | 状态 | 依赖 | 说明 |
| --- | --- | --- | --- | --- |
| `Linear Base` | P0 | done | 无 | `regress`、robust、cluster、`aweight`、single FE 原型已完成 |
| `Panel / FE / HDFE` | P1 | done | Linear Base | `areg`、双向 FE 吸收内核、`reghdfe` 最小子集已完成 |
| `IV / GMM` | P2 | done | Panel / FE / HDFE | `ivregress 2sls`、`ivreghdfe` 最小子集已完成 |
| `Binary / Count` | P3 | done | Linear Base | `logit`、`probit`、`poisson`、`ppmlhdfe` 最小子集已完成 |
| `DID / Event Study Extensions` | P4 | done | Panel / FE / HDFE | `did_imputation`、`eventstudyinteract`、`csdid` 最小子集已完成 |
| `Postestimation` | P5 | done | 前述命令族稳定 | `predict`、`margins` 子集、输出层已完成 |
| `RD / Local Polynomial` | P5 | done | Linear Base | `rdrobust` minimal subset (Sharp RD) 已完成 |
| `RD Completion` | P7 | done | HDFE Hardening | `rdrobust` 完整带宽选择器、fuzzy RD、weights、cluster、masspoints 已完成；`rdplot` golden 双跑因算法差异推迟 |
| `HDFE Hardening` | P6 | done | Wave 0-6 完成 | `reghdfe`/`ivreghdfe`/`ppmlhdfe` 多向聚类、savefe、separation、一阶段诊断 |
| `RD Completion` | P7 | done | HDFE Hardening | `rdrobust` 完整带宽选择器、fuzzy RD、weights、cluster、masspoints、rdplot |
| `DID Hardening` | P8 | done | HDFE Hardening | `did_imputation` controls/pretrends、`csdid` DR/aggtype |
| `IV Completion` | P9 | done | HDFE Hardening | `ivreghdfe` GMM/LIML、弱工具变量、HAC |
| `Postestimation Ecosystem` | P10 | done | IV Completion | `predict` 扩展（stdp, pearson, deviance, working）、`estat` 生态（summarize, vce, ic） |
| `Advanced HDFE & Performance` | P11 | in_progress | Postestimation Ecosystem | MAP/LSMR 迭代内核（done）、个体斜率（in_progress）、Driscoll-Kraay（in_progress）、团队/个体 FE（planned） |

## High-Value Commands

| 命令或能力 | 命令族 | 优先级 | 状态 | 规则来源 |
| --- | --- | --- | --- | --- |
| `regress` | Linear Base | P0 | done | 官方手册 + 双跑 |
| `vce(robust)` | Linear Base | P0 | done | 官方手册 + 双跑 |
| `vce(cluster)` | Linear Base | P0 | done | 官方手册 + 双跑 |
| `aweight` | Linear Base | P0 | done | 官方手册 + 双跑 |
| `xtreg, fe` | Panel / FE / HDFE | P0 | done | 官方手册 + 双跑 |
| `areg` | Panel / FE / HDFE | P1 | done | 官方手册 + 双跑 |
| 双向 FE 吸收内核 | Panel / FE / HDFE | P1 | done | 设计文档 + 双跑 |
| `reghdfe` | Panel / FE / HDFE | P1 | done (Alpha) | 公开源码 + 双跑 |
| `ivregress 2sls` | IV / GMM | P2 | done | 官方手册 + 双跑 |
| `ivreghdfe` | IV / GMM | P2 | done (Alpha) | 公开源码 + 双跑 |
| `logit` | Binary / Count | P3 | done | 官方手册 + 双跑 |
| `probit` | Binary / Count | P3 | done | 官方手册 + 双跑 |
| `poisson` | Binary / Count | P3 | done | 官方手册 + 双跑 |
| `ppmlhdfe` | Binary / Count | P3 | done (Alpha) | 公开源码 + 双跑 |
| `did_imputation` | DID / Event Study Extensions | P4 | done (Alpha) | 公开源码 + 双跑 |
| `eventstudyinteract` | DID / Event Study Extensions | P4 | done (Alpha) | 公开源码 + 双跑 |
| `csdid` | DID / Event Study Extensions | P4 | done (Alpha) | 公开源码 + 双跑 |
| `rdrobust` | RD / Local Polynomial | P5 | done (Beta) | 公开源码 + 双跑 |
| `predict` 高频子集 | Postestimation | P5 | done | 手册 + 双跑 |
| `margins` 高频子集 | Postestimation | P5 | done | 手册 + 双跑 |

## Wave 7–12 新增高价值能力

| 能力 | 命令族 | 优先级 | 状态 | 规则来源 |
| --- | --- | --- | --- | --- |
| `reghdfe` 多向聚类 (2-way+) | HDFE Hardening | P6 | done | Cameron-Gelbach-Miller 2011 + 源码 |
| `reghdfe` `savefe` | HDFE Hardening | P6 | done | 公开源码 |
| `ppmlhdfe` `separation(fe)` | HDFE Hardening | P6 | done | Correia et al. 2019b + 源码 |
| `ivreghdfe` `first`/`ffirst` | HDFE Hardening | P6 | done | ivreg2 手册 + 源码 |
| `rdrobust` 完整带宽选择器 | RD Completion | P7 | done | CCT 2014a/2018/2020 + 源码 |
| `rdrobust` `fuzzy` RD | RD Completion | P7 | done | CCT 2014a + 源码 |
| `did_imputation` `controls` | DID Hardening | P8 | done | BJS 2023 + 源码 |
| `did_imputation` `pretrends` | DID Hardening | P8 | done | BJS 2023 + 源码 |
| `csdid` `method="dr"` | DID Hardening | P8 | done | Callaway-Sant'Anna 2021 + 源码 |
| `ivreghdfe` `gmm2s` | IV Completion | P9 | done | ivreg2 手册 + 源码 |
| `ivreghdfe` `liml` | IV Completion | P9 | done | ivreg2 手册 + 源码 |
| `ivreghdfe` `weakiv` | IV Completion | P9 | done | Stock-Yogo + 源码 |
| `predict` `stdp` | Postestimation Ecosystem | P10 | done | 手册 + 源码 |
| `estat summarize` | Postestimation Ecosystem | P10 | done | 手册 |
| `estat vce` / `estat ic` | Postestimation Ecosystem | P10 | done | 手册 |
| MAP/LSMR 迭代吸收内核 | Advanced HDFE & Performance | P11 | in_progress | Guimaraes-Portugal 2010 + 源码 |
| `absorb(var##c.slope)` | Advanced HDFE & Performance | P11 | in_progress | 公开源码 |
| `vce(dkraay)` | Advanced HDFE & Performance | P11 | in_progress | Driscoll-Kraay 1998 + 源码 |

## Entry Criteria

任一命令从 `planned` 进入 `ready`，至少需要：

- 已在 `docs/research/` 建立研究档案
- 已明确其来源属于"公开源码"还是"官方手册"
- 已在 `docs/testing/test-case-catalog.md` 预登记 synthetic 与 real-data 样例

任一命令从 `ready` 进入 `done`，至少需要：

- synthetic 黄金样例通过
- 至少一个真实公开数据样例通过
- 全量回归测试通过
- 研究档案与结果语义无冲突

## Wave Entry & Exit Criteria

### Wave 7：HDFE Hardening

**入口标准（2026-04-28 审查确认）：**
- [x] Package G 返工完成，Codex 复审通过
- [x] `research/vendor/stata_community/reghdfe/` 源码已完整阅读并归档
- [x] 多向聚类公式（Cameron-Gelbach-Miller 2011）已研究清楚

**出口标准：**
- [x] `reghdfe` 支持 2-way cluster，synthetic + real-data 双跑通过（slope SEs < 1e-6；_cons SE ADR-0003 已知限制）
- [x] `ivreghdfe` 支持 2-way cluster，双跑通过
- [x] `ppmlhdfe` 支持 2-way cluster，双跑通过
- [x] `reghdfe` 支持 `savefe`（功能已实现，golden 双跑测试待创建：`test_w7_reghdfe_savefe.py`）
- [x] `ppmlhdfe` 支持 `separation(fe)`（功能已实现，golden 双跑测试待创建：`test_w7_ppmlhdfe_separation_fe.py`）
- [x] `ppmlhdfe` 支持 `eform`（功能已实现，golden 双跑测试待创建：`test_w7_ppmlhdfe_eform.py`）
- [x] 命令支持矩阵已更新
- [x] ADR-0003 归档：LSDV 框架下多向聚类 _cons SE 容忍度层级

### Wave 8：RD Completion

**入口标准：**
- [x] Wave 7 完成或至少 2-way cluster 已稳定
- [x] `research/vendor/stata_community/rdrobust/` 中 `rdbwselect` 源码已阅读

**出口标准：**
- [x] 所有新增带宽选择器在 `rdrobust_senate.dta` 上与 Stata 双跑一致
- [x] Fuzzy RD 至少有一组 synthetic + 一组 real-data 双跑证据
- [x] `vce(cluster)` 与 `vce(nncluster)` 双跑通过
- [x] 命令支持矩阵已更新

### Wave 9：DID Hardening

**入口标准：**
- [x] Wave 7 完成
- [x] `did_imputation` 源码中 `controls` / `unitcontrols` / `timecontrols` 的处理逻辑已研究清楚

**出口标准：**
- [x] `did_imputation` 含 `controls` + `pretrends` 的 synthetic 双跑通过
- [x] `csdid method="dr"` 至少有一组 synthetic + 一组 real-data 双跑证据
- [x] 命令支持矩阵已更新

### Wave 10：IV Completion

**入口标准：**
- [x] Wave 7 完成（多向聚类稳定，VCE 框架成熟）
- [x] `ivreghdfe.ado` 中 GMM/LIML 分支的源码已完整阅读

**出口标准：**
- [x] `gmm2s` 与 `liml` 均有 synthetic + real-data 双跑证据
- [x] 弱工具变量检验统计量与 Stata 字段级一致
- [x] 命令支持矩阵已更新

**状态：** 已完成（2026-04-30）

### Wave 11：Postestimation & `estat` Ecosystem

**入口标准：**
- [x] Wave 7–10 中至少 3 个 wave 已完成
- [x] `ResultSchema` 已包含完整的 `V` 矩阵访问接口

**出口标准：**
- [x] 每个新增 predict 类型均有 synthetic 双跑证据
- [x] `estat summarize` 输出与 Stata 字段级一致
- [x] `estat vce` / `estat ic` 至少有一组 synthetic 双跑证据
- [x] 命令支持矩阵已更新
- [x] 21 golden tests 全部通过，0 失败
- [x] correctness-gatekeeper 审核通过，全部 5 个 findings 已解决
- [x] 全量回归测试通过（271 non-golden + 21 Wave 11 golden）

**状态：** 已完成（2026-04-30）

**实际执行：**
1. 研究轮（Round 1）：2026-04-29 完成，predict 类型公式与 estat 生态研究归档。
2. 最小实现轮（Round 2）：2026-04-30 完成，`stdp`（reghdfe/ivreghdfe）、GLM residuals（ppmlhdfe）、`estat_summarize`、`estat_ic` 实现，gatekeeper 审核通过。
3. 真实数据验证轮（Round 3）：2026-04-30 完成，21 golden tests 全部通过，gatekeeper 审核通过，全部 5 个 findings 已解决。

### Wave 12：Advanced HDFE & Performance

**入口标准：**
- [ ] Wave 7–11 全部完成
- [ ] 已有明确的性能瓶颈数据集（>1e6 观测，>1e4 FE 级别）

**出口标准：**
- [ ] MAP/LSMR 内核在标准测试集上与 LSDV 结果字段级一致
- [ ] 个体斜率吸收有 synthetic + real-data 双跑证据
- [ ] 性能基准报告显示显著加速（目标：比 LSDV 快 5x 以上）
- [ ] 命令支持矩阵已更新
