# 总体路线图

## 路线图原则

项目后续不再以“单个命令补丁式推进”为主，而按命令族和研究层共同推进。每一波工作都要同时建设：

- 估计器或兼容命令
- 研究档案
- synthetic 黄金样例
- 真实公开数据样例

执行节奏固定为“每个 wave 三轮”，详见：

- `docs/roadmap-execution-rounds.md`

## Wave 0：已完成的原型验证

已验证能力：

- `regress`
- `vce(robust)`
- `vce(cluster)`
- `aweight`
- `xtreg, fe`
- FE + cluster

这一波的意义是证明 Python 端可在机器可验证框架下复现 Stata 结果。

## Wave 1：Panel / FE / HDFE

目标：

- `areg`
- 双向 FE 的核心吸收内核
- `reghdfe` 兼容层最小可用子集

默认三轮拆法：

1. 研究基础建设
2. `areg` 最小实现
3. `areg` 真实数据验证与收口

完成标志：

- `AbsorbingOLS` 或等价核心内核稳定
- `areg` 至少有一组 synthetic + real-data 双跑
- `reghdfe` 源码研究档案完成，并具备进入独立优先 wave 的前置条件

风险：

- singleton、nested FE、DoF 修正复杂
- `reghdfe` 吸收算法与输出行为需要分层实现

## Priority Wave：`reghdfe`

目标：

- `reghdfe` 最小兼容实现
- 多吸收 FE 的最小可用子集
- `reghdfe` 在 synthetic 与真实公开数据上的独立收口

默认三轮拆法：

1. `reghdfe` 研究收束与实现边界确认
2. `reghdfe` 最小实现轮
3. `reghdfe` 真实数据验证与 hardening 轮

完成标志：

- `reghdfe` 至少完成 `absorb(1-2 组 FE)` 的最小实现
- 支持 `vce(ols)` 与单 `cluster`
- 至少一组 synthetic 与一组 real-data 双跑通过
- 对 singleton、`df_a`、cluster 修正的当前口径有文档化说明

风险：

- 多 FE 吸收与 `df_a` 计算是最容易与 Stata 偏离的部分
- singleton 处理、nested FE 与 cluster 修正需要严格门禁
- 该 wave 不应顺势膨胀到 `ivreghdfe` 或 `ppmlhdfe`

## Wave 2：IV / GMM 与 HDFE 联动

目标：

- `ivregress 2sls`
- `ivreghdfe`

完成标志：

- 核心层具备稳定 IV 接口
- HDFE 与 IV 共享吸收、cluster 与结果对象框架
- 社区源码研究和双跑验证链路打通

默认三轮拆法：

1. `ivregress` / `ivreghdfe` 研究轮
2. `ivregress 2sls` 最小实现轮
3. 真实数据验证与 HDFE 联动收口轮

## Wave 3：Binary / Count

目标：

- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`

完成标志：

- 官方内建命令通过手册 + 双跑路径完成最小交付
- `ppmlhdfe` 源码研究与兼容层最小子集建立

默认三轮拆法：

1. `logit/probit/poisson/ppmlhdfe` 研究轮
2. 官方内建离散与计数命令最小实现轮
3. 真实数据验证 + `ppmlhdfe` 最小子集收口轮

## Wave 4：DID / Event Study Extensions

目标：

- `did_imputation`
- `eventstudyinteract`
- `csdid`

完成标志：

- 作为扩展兼容层独立成组
- 每个高频 DID 工具至少有研究档案与最小样例

默认三轮拆法：

1. DID / event study 命令研究轮
2. 最优先 DID 命令最小实现轮
3. 真实数据验证与扩展兼容层收口轮

## Wave 5：Postestimation

目标：

- `predict`
- 高频 `margins` 子集
- 更完整的 Stata 风格输出与 metadata

完成标志：

- 常用 postestimation 路径不再依赖手工拼接

默认三轮拆法：

1. `predict` / `margins` 高频子集研究轮
2. 最小 postestimation 实现轮
3. 真实数据验证与输出层收口轮

## Wave 6：RD / Local Polynomial

目标：

- `rdrobust` sharp RD 最小子集
- 自动带宽选择 `bwselect="mserd"`
- 协变量调整 `covs`

完成标志：

- Sharp RD 显式带宽与自动带宽选择均有双跑证据
- 协变量调整路径通过

默认三轮拆法：

1. `rdrobust` 研究轮
2. Sharp RD 最小实现轮
3. 真实数据验证与 RD 收口轮

---

## Wave 7：HDFE Hardening（HDFE 核心加固）

目标：

- 将 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 从 Alpha 推进到 Beta
- 补齐最影响使用的高频缺口：多向聚类、savefe、separation、一阶段诊断

包含内容：

1. `reghdfe`：多向聚类（2-way cluster）
2. `reghdfe`：`savefe` 与 `residuals()` 选项
3. `ppmlhdfe`：`eform` / `irr`，`d()` / `d2`
4. `ppmlhdfe`：separation 检测（`fe` 子方法，最小可用）
5. `ivreghdfe`：`first` / `ffirst` 一阶段诊断
6. 统一 `df_a` 精确算法（pairwise mobility groups）

完成标志：

- [x] 2-way cluster 在 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 上均有 synthetic + real-data 双跑证据
- [x] `savefe` 输出与 Stata `reghdfe, absorb(..., savefe)` 字段级一致
- [x] separation（`fe` 方法）至少有一组 synthetic 双跑证据
- [x] `ivreghdfe` `first` 一阶段诊断 synthetic 双跑通过
- [x] `ppmlhdfe` `eform` / `irr` synthetic 双跑通过
- [x] 所有新功能已更新命令支持矩阵
- **残余风险：** `reghdfe` 2-way cluster 真实数据 `_cons` SE 存在 ~16% 结构性偏差（LSDV vs 迭代去均值框架差异），已文档化为已知限制；slope SEs 仍保持 < 1e-6 硬标准

风险：

- 多向聚类 VCE 公式与 Stata 实现细节偏离
- separation 检测是 PPML 核心难点，算法复杂
- `df_a` 精确算法涉及图论，实现难度大

默认三轮拆法：

1. 研究轮：Cameron-Gelbach-Miller 公式、savefe 实现、separation `fe` 方法、一阶段诊断
2. 最小实现轮：2-way cluster、savefe、separation(fe)、first
3. 真实数据验证与 hardening 轮

---

## Wave 8：RD Completion（RD 补全）—— 已完成

目标：

- 将 `rdrobust` 从 Alpha — Partial 推进到 Beta
- 覆盖主要带宽选择器与模糊 RD

包含内容（全部已完成）：

1. 完整带宽选择器族：`msetwo`, `msesum`, `msecomb1/2`, `cerrd`, `certwo`, `cersum`, `cercomb1/2`
2. `fuzzy` RD（含 `sharpbw` 子选项）
3. `weights`
4. `vce(cluster)` / `vce(nncluster)`
5. `masspoints` 处理
6. `rdplot` 伴侣命令（最小可用）

完成标志：

- [x] 所有新增带宽选择器 synthetic 测试通过
- [x] Fuzzy RD synthetic 测试通过（basic、sharpbw、perfect compliance、with covs）
- [x] Cluster VCE synthetic 测试通过（cluster、nncluster、few clusters）
- [x] `rdplot` synthetic 测试通过
- [x] 命令支持矩阵已更新为 Beta
- [ ] **残余任务（与 Wave 9 并行补做）：** fuzzy RD real-data golden 双跑、cluster VCE real-data golden 双跑、`rdplot` golden 双跑

风险：

- 带宽选择器算法复杂，需实现 `rdbwselect` 核心
- Fuzzy RD 两阶段局部多项式数值稳定性

实际执行：

1. 研究轮（Round 1）：2026-04-28 完成，6 份研究档案，23 个预登记样例
2. 最小实现轮（Round 2）：2026-04-29 完成，gatekeeper 审查通过，P1/P2 全部修复
3. **真实数据验证轮（Round 3）降级为残余任务**：与 Wave 9 并行补做，不阻塞主线

---

## Wave 9：DID Hardening（DID 加固）—— 已完成

目标：

- 补全 `did_imputation` 与 `csdid` 的高频选项
- 支持更灵活的估计策略

包含内容：

1. `did_imputation`：`controls`, `unitcontrols`, `timecontrols`
2. `did_imputation`：`wtr`, `sum`, `hbalance`
3. `did_imputation`：`hetby`, `project`
4. `did_imputation`：`pretrends`
5. `did_imputation`：`saveestimates`, `saveweights`, `saveresid`
6. `csdid`：`method="dr"`（双重稳健）
7. `csdid`：`aggtype`（simple / dynamic / group / calendar）

完成标志：

- `did_imputation` 含 `controls` + `pretrends` 的 synthetic 双跑通过
- `csdid method="dr"` 至少有一组 synthetic + 一组 real-data 双跑证据
- 命令支持矩阵已更新

风险：

- `method="dr"` 需要倾向得分 + 结果模型双重拟合，复杂度高
- `controls` / `unitcontrols` / `timecontrols` 可能引入 imputation 不可能性判断的边界情况

默认三轮拆法：

1. 研究轮（Round 1）：`controls` 处理逻辑、DR 算法、聚合方式公式
2. 最小实现轮（Round 2）：`controls` + `pretrends` + `method="dr"`
3. 真实数据验证与 DID 收口轮（Round 3）

---

## Wave 10：IV Completion（IV 补全）—— 已完成

目标：

- 将 `ivreghdfe` 从 2SLS 子集推进到完整 IV 生态

包含内容：

1. `gmm2s` / `cue`（GMM 估计器）
2. `liml` / `kclass` / `fuller`
3. `weakiv`（弱工具变量检验）
4. `orthog`（过度识别检验）
5. `endogtest`（内生性检验）
6. `redundant`（冗余工具变量检验）
7. `partial()` / `fwl()`（偏出变量）
8. HAC 标准误：`bw()`, `kernel()`, `dkraay()`

完成标志：

- [x] `gmm2s` 与 `liml` 均有 synthetic + real-data 双跑证据
- [x] 弱工具变量检验统计量与 Stata 字段级一致
- [x] 命令支持矩阵已更新

风险：

- GMM/LIML 需独立估计器内核，与 2SLS 差异大
- 弱工具变量检验等诊断统计量需要精确公式对齐

实际执行：

1. 研究轮（Round 1）：2026-04-28 完成，GMM/LIML/weakiv 源码阅读与研究档案通过 correctness-gatekeeper（含 4 轮 rework）
2. 最小实现轮（Round 2）：2026-04-29 完成，GMM2S + LIML 估计器实现，5 synthetic + 2 real-data golden 测试通过
3. 真实数据验证轮（Round 3）：2026-04-30 完成，weakiv 统计量（Kleibergen-Paap rk LM / rk Wald F）与 Stock-Yogo 临界值实现，synthetic + real-data golden 双跑全部通过，correctness-gatekeeper 审核通过

残余任务（可推迟）：

- CUE 估计器
- `ffirst` compact first-stage
- 多内生变量 weakiv（k_endog > 1 的 ranktest 矩阵版本）
- `orthog` / `endogtest` / `redundant`

---

## Wave 11：Postestimation & `estat` Ecosystem（后估计生态）—— 已完成

目标：

- 建立完整的 postestimation 层，覆盖 `predict`, `margins`, `estat`

包含内容：

1. `predict` 缺失类型：`stdp`（`reghdfe` / `ivreghdfe`）、`pearson` / `deviance` / `working`（`ppmlhdfe`）
2. `estat` 子命令：`estat summarize`、`estat vce`、`estat ic`

完成标志：

- [x] 每个新增 predict 类型均有 synthetic 双跑证据
- [x] `estat summarize` 输出与 Stata 字段级一致
- [x] `estat ic` 有 synthetic 双跑证据
- [x] 命令支持矩阵已更新

实际执行：

1. 研究轮（Round 1）：2026-04-30 完成，`stdp` 公式、GLM 残差公式、`estat` 生态研究
2. 最小实现轮（Round 2）：2026-04-30 完成，`predict stdp`、`predict pearson/deviance/working`、`estat_summarize`、`estat_ic` 实现
3. 真实数据验证轮（Round 3）：2026-04-30 完成，21 golden 测试全部通过，correctness-gatekeeper 审核通过（5 个 findings 全部解决）

残余任务（可推迟）：

- `test` / `lincom` / `nlcom` 的 Python 等价层
- `margins` 在 IV/GLM 后的扩展

---

## Wave 12：Advanced HDFE & Performance（高级 HDFE 与性能）—— 已完成（v1.0.0）

目标：

- 解决极高维 FE 的性能瓶颈
- 补充高级吸收语法

包含内容：

1. 迭代 MAP 吸收内核（替代 LSDV）
2. `absorb(var##c.slope)`（个体斜率吸收）
3. `vce(dkraay)`（Driscoll-Kraay 标准误）
4. 性能基准测试与优化

完成标志：

- [x] MAP 内核在标准测试集上与 LSDV 结果字段级一致（Round 2：系数/SE rtol < 1e-10）
- [x] MAP 性能基准：Dataset A/B/C 内存 0.15–0.34 GB（LSDV OOM >74 GiB）
- [x] 个体斜率吸收有 synthetic 双跑证据（Round 2b/3：4 个 golden tests，系数/SE rtol < 1e-10）
- [x] 个体斜率吸收有 real-data 双跑证据（Round 4：wagepan `union hours ~ nr##c.year`）
- [x] Driscoll-Kraay VCE 有 synthetic 双跑证据（Round 2b/3：3 个 golden tests，系数 < 1e-10，SE < 1e-4）
- [x] Driscoll-Kraay VCE 有 real-data 双跑证据（Round 4：wagepan `union hours ~ nr year`）
- [x] 命令支持矩阵已更新（slopes + dkraay marked as supported）

风险：

- 迭代吸收内核是重大架构变更，需独立性能验证与稳定性测试
- MAP 收敛速度在某些 FE 结构下可能极慢（当前默认关闭 Aitken 加速）
- DK SE 与 Stata 对齐到 ~1e-4（小样本修正因子差异），已文档化为已知限制

执行历史：

1. 研究轮（Round 1）：MAP/LSMR 算法、个体斜率语法、Driscoll-Kraay 公式 — **已完成 2026-04-30**
2. 最小实现轮（Round 2）：MAP 迭代内核 — **已完成 2026-04-30**
3. 扩展实现轮（Round 2b/3）：个体斜率吸收 + Driscoll-Kraay 标准误 — **已完成 2026-04-30**
4. 真实数据验证与 v1.0.0 发布准备（Round 4）：wagepan golden tests + version bump + docs — **已完成 2026-04-30**

### 推迟至 v1.1.0+

以下四项原属 Wave 12 范围，Roadmaster 评估后决定推迟：

| 项目 | 复杂度 | 理由 |
|------|--------|------|
| `group(var) individual(var)` FE | 高 | 组级聚合 + 个体 FE，无用户阻塞 |
| 3-way+ clustering | 高 | 2-way cluster 已完整实现 |
| LSMR/LSQR 算法 | 中 | MAP 已解决性能瓶颈，LSMR 为锦上添花 |
| `savefe` MAP 路径 | 中 | LSDV 路径 savefe 已完整实现 |

---

## Wave 13 (v1.1.0)：Advanced HDFE Extensions — 已完成

目标：

- 补充 Wave 12 推迟项与残余高频功能

已完成内容：

1. IV first-stage diagnostics、weak-instrument tests、overidentification tests
2. GLM robust small-sample correction 与 `eform`/`irr`/`or_` 别名
3. DID `allhorizons`、`csdid notyet`、不平衡面板 NaN 修复
4. 2-way cluster rank-deficiency detection 与 documented PSD fallback
5. `reghdfe` 高级 tuple/list `absorb` API 与 `aweight` array/Series 支持

推迟至 v1.2.0+：

- `group(var) individual(var)` FE（团队/个体 FE）
- 3-way+ multi-way clustering VCE
- LSMR/LSQR 迭代算法评估与引入
- `savefe` MAP 路径支持
- `ivreghdfe`：`orthog` / `endogtest` / `redundant` / `partial()` / HAC standard errors
- `ppmlhdfe`：`separation(ir/simplex/mu)` / `d()` / `d2`
- `doffadjustments()` 精确算法（pairwise / firstpair / clusters / continuous）

## Wave 14 (v1.2.0+)：开源可持续维护与命令完整度深化（计划中）

目标：

- 完成 modular revalidation v1.3 修缮，修复已确认正确性问题
- 推进 HDFE / DID / RD 命令完整度
- 建立可持续的 CI、lint/type、release 与文档治理机制
- 实现公开仓库与内部开发母仓的自动化、白名单式同步

---

## 当前默认优先级

当前主线默认锁定为：

1. `Panel / FE / HDFE`
2. `Priority Wave: reghdfe`
3. `IV / GMM`
4. `Binary / Count`
5. `DID / Event Study Extensions`
6. `Postestimation`
7. `RD / Local Polynomial`
8. `HDFE Hardening`（已完成）
9. `RD Completion`（已完成）
10. `DID Hardening`（已完成）
11. `IV Completion`（已完成）
12. `Postestimation & estat Ecosystem`（已完成）
13. **`Advanced HDFE & Performance`**（已完成 / v1.1.0 Stable）
14. **`Advanced HDFE Extensions`**（已完成 / v1.1.0）
15. **`Open-Source Sustainability & Command Completeness`**（计划中 / v1.2.0+）

在没有新的用户优先级调整前，默认主线为开源可持续维护与命令完整度深化。

---

## 版本与发布节奏

| 版本 | 目标 | 对应 Wave |
|------|------|-----------|
| v0.1.x | Alpha 发布，最小可用子集 | Wave 0–6 |
| v0.2.x | Beta 发布，HDFE / RD / DID 核心加固 | Wave 7–9 |
| v0.3.x | Beta 发布，IV 完整生态 + Postestimation | Wave 10–11 |
| v1.0.0 | 稳定发布，高级 HDFE 与性能优化 | Wave 12 |
| v1.1.0 | 扩展发布，高级 HDFE 扩展 + 残余补全 | Wave 13（已完成） |
| v1.2.0+ | 开源可持续维护与命令完整度深化 | Wave 14（计划中） |

**发布门槛：**

- 每个 minor 版本升级前，必须通过 `docs/release/release-candidate-checklist.md` 的全部检查项。
- 每个 wave 完成后，必须 Codex 复审通过才能标记为 `done`。
- 任何公共 API 变化（`ResultSchema` 新增字段、参数语义变化）必须通过 ADR。
