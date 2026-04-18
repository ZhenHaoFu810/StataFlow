# 项目问题与不足清单

## Release-blocking

### 1. Vendor 开源命令未达到”完整复现”

#### 现象

- `reghdfe`、`ivreghdfe`、`ppmlhdfe`、`did_imputation`、`eventstudyinteract`、`csdid`、`rdrobust` 当前均为**高频子集实现**，不是完整 Stata 社区命令复现
- 每个命令都有 wrapper、source map、support matrix 和测试，但参数面和诊断工具链仍明显不完整

#### 为什么不可接受

如果项目目标是”把 `research/vendor/stata_community` 下的开源命令完整、全面、正确搬到 Python”，那当前状态与目标明显不符。

#### 影响范围

- 对外发布口径
- 用户预期管理
- 后续命令族优先级安排

#### 修复目标

- 对每个 vendor 命令保持明确的”完整度清单”（`implemented` / `planned` / `explicitly unsupported`）
- 按源码逐项补齐或明确拒绝
- 不得将 wrapper 存在等同于”完整支持”

### 2. `rdrobust` 仅为最小子集

#### 现象

- `RDRobust` estimator、`rdrobust` wrapper、`rdrobust.md` support matrix、`rdrobust-source-map.md` 研究文档、以及 synthetic + real-data 测试均已存在
- 但自动带宽选择、模糊 RD、协变量调整、`deriv > 0`、聚类稳健 VCE 等核心功能仍缺失
- 使用时必须显式提供带宽 `h`

#### 为什么不可接受

`rdrobust` 的社区命令价值很大程度上依赖自动带宽选择；当前实现仅为最小可用子集，不能覆盖典型 RD 研究流程。

#### 影响范围

- vendor 命令完整度
- 项目完整性叙事

#### 修复目标

- 补齐 `bwselect` / `rdbwselect` 自动带宽选择
- 补齐 `covs` 协变量调整
- 补齐 `cluster` 聚类稳健推断

### 3. `reghdfe`/`ppmlhdfe`/`ivreghdfe` 的”完整支持”表述不能成立

#### 现象

这些命令虽然都已有 wrapper、测试和 source map，但实际仍有大量未实现参数与行为。

#### 为什么不可接受

如果对外使用”已实现 `reghdfe`”而不加限定，很容易被理解为”完整 Stata 级复现”。

#### 影响范围

- 开源发布描述
- 用户误用风险

#### 修复目标

- 每个命令的支持矩阵已按 `implemented` / `planned` / `explicitly unsupported` 三分法细化
- README 和 release 文档已明确使用 `Stable` / `Alpha` / `Alpha — Partial` 分级
- 仍需持续维护，防止后续 drift

## High priority

### 4. `reghdfe` 仍受限于 1-2 个分类 FE 的 Phase A 边界

#### 现象

- 不支持更完整的高维 FE 语义
- mobility-group 等复杂 DoF 未完成
- multi-way cluster 未完成

#### 为什么不可接受

`reghdfe` 的核心价值就是复杂 HDFE 任务；当前只能覆盖最常见子集。

#### 影响范围

- HDFE 用户场景
- 金融/应用微观典型论文复现

#### 修复目标

- 明确 Phase B/C 功能面
- 逐项对照源码推进

### 5. `ppmlhdfe` 缺少 separation 检测

#### 现象

当前实现没有 `simplex` / `relu` / `fe` / `mu` 分离检测。

#### 为什么不可接受

这不是边缘选项，而是 `ppmlhdfe` 在很多应用中的关键稳定性特征。

#### 影响范围

- 真实贸易/重力模型数据
- 稀疏计数数据

#### 修复目标

- 将 separation 作为优先功能补齐
- 同时补支持矩阵、失败语义与测试

### 6. `ivreghdfe` 缺失诊断工具链

#### 现象

- first-stage 结果不完整
- 弱工具、过识别等常见诊断未形成稳定接口

#### 为什么不可接受

IV 命令只有系数和标准误远远不够，诊断是实证使用的核心部分。

#### 影响范围

- IV 研究用户
- 命令可信度

#### 修复目标

- 明确最小诊断集
- 分阶段纳入 wrapper 和结果 schema

### 7. DID 社区命令仍是高频路径实现，不是完整命令面

#### 现象

- `did_imputation` 缺少 `minn`/`window`/`pretrend`
- `eventstudyinteract` 缺少更完整命令面
- `csdid` 仅支持 `method="reg"`

#### 为什么不可接受

当前可用于演示与一部分研究，但不能声称是完整社区命令移植。

#### 影响范围

- DID 用户真实项目迁移

#### 修复目标

- 对三者分别建立完整度路线
- 特别是 `csdid` 要明确 method 扩展计划

## Medium priority

### 8. core estimator 与命令语义仍有部分耦合

#### 现象

- `AbsorbingOLS` 承载 `areg` 与 `reghdfe`
- `IVAbsorbingOLS` 承载 `ivreghdfe`

#### 为什么不可接受

对内部工程可接受，但对长期维护和审计解释不够理想。

#### 影响范围

- 维护者理解成本
- 审查时的命令语义拆分

#### 修复目标

- 强化 wrapper 层优先语义
- 进一步在文档和结果元数据中分离命令身份

### 9. 输出层与 Stata 风格 summary 仍不完整

#### 现象

- 当前有结果 schema，但缺少统一、成熟的 `summary(style="stata")`

#### 为什么不可接受

对真实迁移用户来说，可读输出层很重要。

#### 影响范围

- 易用性
- 教学与展示

#### 修复目标

- 把 summary / table 层纳入后续路线

### 10. 权重和 clustering 仍明显不完整

#### 现象

- 仅 `aweight`
- 仅单 cluster

#### 为什么不可接受

这限制了官方命令与社区命令的大量真实使用场景。

#### 影响范围

- 横截面与调查类研究
- 更复杂面板设定

#### 修复目标

- 明确 `fweight/pweight/iweight`
- 评估 multi-way cluster 进入时点

## Documentation / usability

### 11. “Alpha 可用”与”完整复现”两种口径需要彻底拆开

#### 现象

当前 README、`docs/command-support-matrix/`、`docs/release/open-source-alpha-status.md` 已引入 `Stable` / `Alpha` / `Alpha — Partial` 三级完整度声明，但用户仍可能把 wrapper 存在误解为”完整 Stata 命令支持”。

#### 为什么不可接受

如果不持续维护，文档会随代码演进再次产生 drift。

#### 影响范围

- 开源发布理解成本
- 外部 issue 质量

#### 修复目标

- README 首页已加入”完整支持 / 子集支持 / 未实现”总览（本轮完成）
- 每轮 Codex review 必须将文档同步列为 gating step

### 12. source map、support matrix、测试目录需要持续三向同步

#### 现象

这个问题在历史上反复出现过：代码先变了，文档和报告滞后（如 Package 004/005 的 `REPORT.md` stale fresh-run 数字问题）。

#### 为什么不可接受

审计时会直接削弱结论可信度。

#### 影响范围

- 研究档案可信度
- 后续代理执行质量

#### 修复目标

- 把 source map/support matrix/report 同步列为每轮必检项
- 已知的历史文档漂移问题已正式登记到 `docs/release/known-issues.md`，不再散落在旧 `REPORT.md` 中

