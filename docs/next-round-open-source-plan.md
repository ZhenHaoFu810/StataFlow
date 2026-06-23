# 下一阶段开发总计划

## 1. 文档定位

本文档是 `StataFlow` 在当前审计之后的正式开发计划，目标是把项目从“高频子集可用、局部双跑验证完成”的状态，推进到“功能边界清晰、关键命令链条更完整、可稳定开源发布”的状态。

本文档关注四类目标：

- 修复已经确认的正确性问题和文档漂移问题
- 补全最关键的 Stata 命令功能缺口
- 提升代码质量、可维护性、用户可理解性
- 建立可持续的发布与验证门槛

## 2. 当前项目判断

### 2.1 已经成立的部分

- 核心包结构已经成型：`estimators`、`compat.stata`、`results`、`postestimation`、`validation`
- 常用主干路径可运行：`regress`、`xtreg, fe`、`areg`、`ivregress 2sls`、`logit`、`probit`、`poisson`
- HDFE / DID / RD 命令已经有可用雏形，并有 synthetic 与部分 real-data 验证
- support matrix、source map、examples、tests、validation artifacts 已形成完整骨架

### 2.2 当前最主要的问题

- 若干公开参数和文档承诺仍存在实现偏差或漂移
- 多个 vendor/community 命令仍是高频子集，而不是完整复现
- wrapper 层、support matrix、source map、tests 之间仍有继续漂移的风险
- 开源发布口径必须进一步收紧，避免用户把“可用子集”误解为“完整 Stata 命令复现”

## 3. 开发总目标

下一阶段不追求“命令数量继续快速增加”，而是优先追求以下四件事：

1. 先把现有命令做对、做稳、做清楚
2. 把 HDFE 家族和 DID 家族补到足以支撑真实研究迁移
3. 把 RD 与 IV 的关键诊断链条补齐
4. 把开源版本整理成一个边界清晰、文档可信、验证可审计的公开项目

## 4. 总体策略

### 4.1 优先级原则

- 正确性优先于新功能
- 命令完整度优先于命令数量
- 研究工作流关键缺口优先于边缘选项
- 公共能力优先于单命令私有补丁
- 文档、测试、验证必须与实现同步推进

### 4.2 工作流原则

每轮功能开发都必须同时完成：

- estimator 或 wrapper 实现
- support matrix 更新
- source map 或设计文档更新
- synthetic tests 更新
- 如有条件，追加 Stata dual-run 验证

不能再接受“代码先改，文档以后补”或“support matrix 先写，行为以后补”的推进方式。

## 5. 分阶段路线图

## Phase 0：正确性与发布清障

### 目标

先清掉已经确认的 bug、元数据漂移、文档冲突和编码问题，为后续补功能建立干净基线。

### 必做事项

- 修复 `did_imputation(..., allhorizons=...)` 当前无效的问题
- 统一版本号来源，消除 `pyproject.toml` 与 `src/stataflow/__init__.py` 的版本漂移
- 修复 support matrix 中与实现冲突的示例和表述
- 清理 estimator / wrapper / docs 中已经过时的“unsupported”说明
- 统一中文 Markdown 文件编码为 UTF-8，修复已损坏文档
- 清理内部状态命名不一致、明显拼写漂移和重复语义字段

### 交付物

- 一轮 correctness bugfix 提交
- 一组新增回归测试
- 清理后的 support matrix
- 编码修复后的中文文档

### 完成标志

- 快速测试全绿
- examples 全绿
- 不再存在已确认的公开参数无效问题
- 不再存在版本号或示例级别的明显对外误导

## Phase 1：HDFE 内核升级

### 目标

把 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 从“Phase A 高频子集”推进到更接近真实研究使用场景的 HDFE 平台。

### 1. `reghdfe`

优先补全：

- 超过 2 维的多重固定效应吸收
- 更清楚的 DoF 处理与结果元数据
- 多维聚类设计预留
- 更完整的 predict/postestimation 语义边界

后续再评估：

- mobility-group DoF
- slopes
- individual/group/team FE 语义
- `estat` 生态

### 2. `ivreghdfe`

优先补全：

- first-stage 结果对象与输出
- weak-IV diagnostics
- overidentification diagnostics
- 与 HDFE 结果对象的统一接口

后续再评估：

- LIML / GMM
- 更复杂的 k-class 系列
- 更完整的 IV postestimation

### 3. `ppmlhdfe`

优先补全：

- separation detection
- separation 失败时的明确行为和结果报告
- 更完整的 predict 类型
- HDFE 与 PPML 结果摘要统一

后续再评估：

- 更丰富 diagnostics
- 更细的 convergence/reporting 接口

### 本阶段交付物

- HDFE family roadmap 文档
- `reghdfe` / `ivreghdfe` / `ppmlhdfe` 对应的功能账本
- 至少一轮真实数据或 Stata 双跑验证扩充

### 完成标志

- `reghdfe` 不再被公开表述为仅限 1-2 FE 的早期子集
- `ivreghdfe` 不再只有系数和标准误，而具备基本诊断链
- `ppmlhdfe` 具备 separation handling 的最小可用能力

## Phase 2：DID 家族补全

### 目标

把 DID 命令从“能跑核心路径”推进到“能覆盖论文里常见的命令用法”。

### 1. `did_imputation`

优先补全：

- `window`
- `minn`
- `pretrends`
- 更明确的 horizon 选择逻辑
- controls / FE 结构的文档化与行为约束

### 2. `eventstudyinteract`

优先补全：

- `window`
- `minn`
- 自动生成 relative-time dummies 时的更完整边界控制
- 输出中对 cohort/control cohort 语义的更清晰标注

### 3. `csdid`

优先补全：

- 除 `method="reg"` 外的 method 规划与优先级
- aggregation / event summary 的边界设计
- 输出 schema 与其他 DID 命令统一

### 本阶段交付物

- DID command family support ledger
- 一轮 DID synthetic + real-data 验证扩展
- DID command comparison note，说明三者各自定位和边界

### 完成标志

- DID 三个命令的“支持什么、不支持什么、为什么”都已明确
- 至少 `did_imputation` 达到研究常用子集完整
- `eventstudyinteract` 与 `csdid` 的扩展路线对外可解释

## Phase 3：RD 与公共推断能力补全

### 目标

补齐 `rdrobust` 的关键研究工作流，并推进跨命令公共能力。

### `rdrobust`

优先补全：

- fuzzy RD
- kink (`deriv > 0`)
- 更多 bandwidth selectors
- cluster-robust VCE
- weights

### 跨命令公共能力

优先补全：

- multi-way clustering
- `aweight` 之外的权重体系评估
- wrapper 层 postestimation 策略
- 更统一的 summary/table 输出

### 本阶段交付物

- `rdrobust` Phase C 设计文档
- clustering / weights 跨命令设计说明
- 结果对象与表格输出统一方案

### 完成标志

- `rdrobust` 不再只是 sharp RD 的最小子集
- multi-way cluster 有明确设计和首个落地点
- 项目对“权重支持”不再停留在 README 级别说明

## Phase 4：开源发布整理与长期治理

### 目标

把项目整理成一个可持续开源维护的仓库，而不是开发母仓的手工镜像。

### 必做事项

- 建立并稳定运行 open-source export 机制
- 明确哪些文档公开、哪些文档内部保留
- 清理 docs 中历史遗留、乱码、审计痕迹过重、路径失效内容
- 建立 release gating checklist
- 建立 command-completeness ledger 和 known-issues 机制

### 发布门槛

- 公开文档编码统一、链接可用、命名一致
- support matrix 与实现一致
- 开源仓 CI 稳定
- 关键 examples 可运行
- 关键命令的边界说明完整

## 6. 重点命令补全优先级表

| 优先级 | 命令/模块 | 原因 |
| --- | --- | --- |
| P0 | `did_imputation` 正确性修复 | 已有公开参数无效，必须先修 |
| P0 | 版本号、文档漂移、编码修复 | 直接影响开源可信度 |
| P1 | `reghdfe` | HDFE 是项目的核心竞争力之一 |
| P1 | `ppmlhdfe` separation | 真实贸易/重力模型场景关键能力 |
| P1 | `ivreghdfe` diagnostics | 没有诊断链就不是成熟 IV 工具 |
| P1 | `did_imputation` / `eventstudyinteract` / `csdid` | DID 是当前最容易被外界关注的新增命令族 |
| P2 | `rdrobust` 扩展 | 现有基础不错，但仍偏子集 |
| P2 | multi-way clustering / weights | 跨命令收益高，但实现复杂度也高 |
| P3 | summary/table 输出统一 | 对用户体验重要，但晚于正确性与核心估计能力 |

## 7. 每轮开发必须遵守的 gating rules

任一功能完成前，必须同时满足：

- 实现代码完成
- 至少一个针对该功能的新增测试
- support matrix 已更新
- 若涉及 vendor/community 命令，source map 已同步
- 若改变公开行为，README 或用户文档已更新
- 若能做 dual-run，就补 Stata 验证；若不能做，必须说明原因

任一功能不得在以下状态下宣称完成：

- 只补了 wrapper，没补 estimator 行为
- 只补了 estimator，没更新 support matrix
- 文档仍沿用旧边界
- 测试只覆盖 happy path，不覆盖失败路径或边界条件

## 8. 建议的近期执行顺序

建议按以下顺序推进未来 4 个开发包：

### Package A：Correctness and Release Hygiene

- 修 bug
- 修版本号
- 修 support matrix 冲突
- 修中文文档编码
- 修开源仓文档漂移

### Package B：HDFE Completion Core

- `reghdfe` 多重 FE 扩展
- `ivreghdfe` 基础 diagnostics
- `ppmlhdfe` separation 设计与实现

### Package C：DID Completion Core

- `did_imputation` 关键选项补全
- `eventstudyinteract` 命令面扩展
- `csdid` 方法路线明确化

### Package D：Cross-Cutting Inference

- multi-way clustering
- weights
- summary/table 层
- wrapper postestimation 策略

## 9. 成功标准

下一阶段结束时，项目应达到以下状态：

- 不再存在公开参数无效或明显说明错误
- HDFE family 至少有一条更完整的可研究使用路径
- DID family 的支持边界清楚且主干能力显著增强
- RD 和 IV 不再停留在“能估计但诊断不足”的状态
- 开源版本的文档、代码、验证、CI 和支持矩阵形成一致闭环

## 10. 一句话路线判断

`StataFlow` 接下来的重点不是继续“加更多命令名”，而是把已经宣布迁移的命令做成真正可信、边界清晰、可研究使用、可开源审计的实现。
