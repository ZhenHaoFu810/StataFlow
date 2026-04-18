# 下一轮开发总计划：面向开源初版的命令映射与源码完整复现

## 1. 文档目的

本计划用于定义项目在当前 wave 全部完成之后的下一轮总目标、开发原则、范围边界、优先级顺序与验收门槛。

这一轮的目标不是继续零散扩充少量功能，也不是仅以“测试通过”为目标补数值，而是把项目从“研究型 Stata 对齐原型”推进为一个可以公开发布的、面向实证研究者的 Python 第三方库初版。

本轮开发有两个一级目标：

1. 对 `research/vendor/stata_community/` 下已镜像的 Stata 社区开源命令，进行尽可能完整、系统、数学口径正确的 Python 复现。
2. 将对外接口提升为命令级 API，使函数名、参数命名、结果语义尽量与 Stata 命令对齐，显著降低研究者迁移成本。

## 2. 当前项目状态判断

截至本计划编写时，项目已经具备以下基础：

- `OLS` / `FixedEffectsOLS` / `AbsorbingOLS`
- `IV2SLS` / `IVAbsorbingOLS`
- `Logit` / `Probit` / `Poisson`
- `PPMLHDFE`
- `DIDImputation` / `EventStudyInteract` / `CSDID`
- `predict` / `margins` 高频子集
- synthetic + real-data 双线测试框架
- 本地 Stata runner 与结果 schema
- 本地开源源码镜像与公开数据集镜像

但当前仍然存在两类关键缺口：

### 2.1 产品层缺口

- 对外暴露的仍主要是估计器类，而不是 Stata 命令层 API。
- `AbsorbingOLS` 同时承载 `areg` 与 `reghdfe`，`IVAbsorbingOLS` 同时承载 `ivreghdfe`，命令语义和实现内核没有分层。
- `compat.stata` 命令映射层在文档中已承诺，但代码中尚不存在。

### 2.2 完整度缺口

- 对 `reghdfe`、`ivreghdfe`、`ppmlhdfe`、`did_imputation`、`eventstudyinteract` 等命令，目前实现的是高频核心子集，而不是完整命令面。
- 对官方命令 `regress`、`xtreg, fe`、`logit`、`probit`、`poisson` 也主要实现了当前测试覆盖的高频路径，而不是完整 Stata 选项面。

因此，本轮开发的本质不是“再做几个命令”，而是：

- 把已有数值内核提升为可开源的用户产品接口。
- 把已有子集实现推进到“源码支持下的完整命令复现”。

## 3. 本轮开发总原则

本轮所有实现必须遵守以下原则。

### 3.1 Source-first, not test-first

对于有公开源码的命令：

- 优先研究本地镜像源码。
- 先理解算法、数据流、返回值语义、自由度修正、标准误逻辑、边界处理，再编码。
- 不允许仅通过调整数值运算或容差来“对齐测试”。

对于没有公开源码的官方命令：

- 以官方手册、返回结果、帮助文档和 Stata 双跑为依据。
- 仍然禁止“为了测试通过而反推数值”的行为。

### 3.2 Mathematical equivalence before test equivalence

通过测试只是最低门槛，不是最终目标。

每个命令的 Python 实现都必须满足：

- 数学对象正确：目标 estimand 与 Stata 命令一致。
- 估计流程正确：样本筛选、矩阵构造、变换、优化、推断过程与 Stata 逻辑一致。
- 推断语义正确：`t/z/chi2/F/Wald`、自由度、小样本修正、cluster 调整不能只在数值上“碰巧接近”。

如果测试通过但数学过程与源码或手册不一致，则视为不通过。

### 3.3 Command-semantic API over internal-class naming

对外 API 的首要目标是降低 Stata 用户的理解门槛，而不是维持内部类命名的整洁性。

因此本轮必须接受以下事实：

- `areg` 和 `reghdfe` 在内部可以共享内核，但对外必须是两个不同命令入口。
- `ivregress 2sls` 与 `ivreghdfe` 也应有独立入口。
- 对外暴露的函数名应优先使用 Stata 命令名。

### 3.4 No silent scope inflation

本轮虽然目标更大，但仍然不能无边界扩张。

必须区分三层状态：

- `implemented`: 代码已实现并可调用
- `verified`: 已经通过 synthetic + real-data +数学口径审查
- `documented-but-not-yet-complete`: 文档登记了但尚未完成

不得因为某个命令“已经有类”或“已有少量测试”就对外宣称完整支持。

## 4. 本轮一级交付目标

本轮交付分为两个主包。

### 4.1 交付包 A：Stata 命令映射层

目标是在 `src/statapy/compat/stata/` 下建立正式命令接口层。

最低要求：

- `regress(...)`
- `xtreg_fe(...)`
- `areg(...)`
- `reghdfe(...)`
- `ivregress_2sls(...)`
- `ivreghdfe(...)`
- `logit(...)`
- `probit(...)`
- `poisson(...)`
- `ppmlhdfe(...)`
- `did_imputation(...)`
- `eventstudyinteract(...)`
- `csdid(...)`

这些 wrapper 必须：

- 保持与现有内核估计器解耦
- 使用 Stata 风格命令名
- 参数名尽量贴近 Stata 语义
- 明确支持与不支持的参数
- 返回统一结果对象

### 4.2 交付包 B：开源命令完整复现

目标是对以下本地镜像命令做“完整度显著提升”：

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `rdrobust`

其中优先级最高的是前三个 HDFE 系列。

## 5. 分命令审查：已实现、未实现、下一轮要求

### 5.1 `regress`

当前已实现：

- OLS
- `vce(ols)`
- `vce(robust)`
- `vce(cluster clustvar)`
- `aweight`
- `noconstant`
- 缺失值剔除
- 共线性剔除
- `predict(xb residuals)`
- `margins` 高频子集

当前缺口：

- `fweight`
- `pweight`
- `iweight`
- 更完整的 Stata 命令级 wrapper
- 更完整 summary / 输出风格层

本轮要求：

- 补 `regress()` 命令 wrapper
- 对权重支持矩阵做文档化
- 明确哪些权重在初版开源版本中支持，哪些标记为 planned

### 5.2 `xtreg, fe`

当前已实现：

- `FixedEffectsOLS`
- `vce(ols)`
- `vce(cluster)`
- `predict(xb residuals)`
- `margins(dydx)`

当前缺口：

- 命令级 `xtreg_fe()` wrapper
- 更完整选项面
- 权重路径仍缺

本轮要求：

- 补 wrapper
- 将文档与结果字段明确标成“single-FE subset”

### 5.3 `areg`

当前已实现：

- `AbsorbingOLS(absorb=<single var>)`
- Stata 对齐测试通过
- 真实数据验证通过

当前缺口：

- 没有正式 `areg()` 命令 wrapper
- 与 `reghdfe` 共享实现但语义未分层
- 可支持参数尚未显式映射

本轮要求：

- 将 `areg` 从 `AbsorbingOLS` 中抽象成对外独立命令入口
- 明确 `areg` 只对应单吸收 FE 语义
- 对 `reghdfe` 共有但 `areg` 不支持的参数做硬边界

### 5.4 `reghdfe`

当前已实现：

- 基于 `AbsorbingOLS` 的最小子集
- `absorb()` 1-2 组
- 单 cluster
- singleton drop
- 部分 nested FE DoF 逻辑
- synthetic + real-data 对齐

当前缺口：

- 没有独立 `reghdfe()` wrapper
- `vce(robust)` 尚未作为正式命令面收口
- 未覆盖完整源码中的选项体系
- 未系统比对本地镜像中的测试集和行为路径
- 未形成“支持矩阵”

本轮要求：

- 建立独立 `reghdfe()` 命令入口
- 以本地镜像 [research/vendor/stata_community/reghdfe](</D:/OneDrive - SAIF/PhD3/Stata2Python/research/vendor/stata_community/reghdfe>) 为主参考
- 至少完成以下参数面：
  - `absorb()`
  - `vce(ols/robust/cluster)`
  - `cluster(varname)`
  - singleton 处理
  - 多组 FE 下的 `df_a`
  - `predict` 高频子集
- 同时输出一份 `reghdfe` 支持矩阵文档，列出未做项

### 5.5 `ivregress 2sls`

当前已实现：

- `IV2SLS`
- `vce(ols/robust/cluster)`
- synthetic + real-data 对齐

当前缺口：

- 没有正式 `ivregress_2sls()` wrapper
- 诊断工具链不完整

本轮要求：

- 补 wrapper
- 明确当前是否只支持 `2sls`
- 把 first-stage / weak-IV / overid 等缺口显式写进支持矩阵

### 5.6 `ivreghdfe`

当前已实现：

- `IVAbsorbingOLS`
- FE + 2SLS + cluster 的最小子集

当前缺口：

- 没有独立 `ivreghdfe()` wrapper
- 和本地镜像 [research/vendor/stata_community/ivreghdfe](</D:/OneDrive - SAIF/PhD3/Stata2Python/research/vendor/stata_community/ivreghdfe>) 相比，命令面明显不完整

本轮要求：

- 建立独立 wrapper
- 以镜像源码逐项建立参数支持矩阵
- 至少把最常见参数面做清楚，并对未支持项硬报错

### 5.7 `logit` / `probit` / `poisson`

当前已实现：

- MLE 主路径
- `vce(ols/robust/cluster)`
- `predict`
- `margins`
- z-based inference 已收口

当前缺口：

- 命令 wrapper 层不存在
- 更完整的 Stata 选项面与报告层不存在

本轮要求：

- 建立 `logit()` / `probit()` / `poisson()` 命令入口
- 明确每个命令的 `predict` 与 `margins` 支持范围
- 补结果字段与文档说明，而不是默认用户猜测

### 5.8 `ppmlhdfe`

当前已实现：

- HDFE + PPML 最小子集
- `vce(robust/cluster)`
- 真实数据 gravity 风格验证

当前缺口：

- 没有正式 `ppmlhdfe()` wrapper
- 与本地镜像 [research/vendor/stata_community/ppmlhdfe](</D:/OneDrive - SAIF/PhD3/Stata2Python/research/vendor/stata_community/ppmlhdfe>) 相比，仍缺重要命令面
- `offset` / `exposure` 等典型语法未见支持
- 分离问题处理尚未做完整覆盖矩阵

本轮要求：

- 独立 wrapper
- 以源码镜像为主，补全高频参数
- 把 `offset` / `exposure` / separation 行为列入明确开发范围

### 5.9 `did_imputation`

当前已实现：

- 核心 estimator
- `cluster`
- `allhorizons`
- `autosample`

当前缺口：

- 命令 wrapper 缺失
- 与原命令帮助文档和源码相比，参数面尚不完整

本轮要求：

- 建立 `did_imputation()` wrapper
- 根据本地源码镜像补参数支持矩阵

### 5.10 `eventstudyinteract`

当前已实现：

- 核心 estimator
- synthetic + real-data 对齐

当前缺口：

- 输入接口偏工程化，要求用户预生成 event dummies
- 不像 Stata 命令那样可直接调用

本轮要求：

- 建立 `eventstudyinteract()` wrapper
- 将“预生成虚拟变量”的内部要求转化为更贴近命令语义的参数接口

### 5.11 `csdid`

当前已实现：

- `method="reg"` 路径
- `estat_event()`
- 真实数据聚合标准误已对齐

当前缺口：

- 只支持 `reg`
- 并非完整 `csdid`

本轮要求：

- 建立 `csdid()` wrapper
- 将当前实现定位为 `csdid` 的最小子集，而不是完整命令
- 支持矩阵中清楚标注 `method` 限制

### 5.12 `rdrobust`

当前实现状态：

- 本地源码镜像已下载
- 尚无 Python 实现

本轮要求：

- 将 `rdrobust` 正式纳入待实现清单
- 先完成研究档案升级与支持矩阵设计
- 是否进入初版开源 release，取决于 HDFE 系列收口后资源情况

## 6. API 重构方案

本轮必须引入双层 API。

### 6.1 Core 层保留

现有类继续保留，作为内部和高级用户接口：

- `OLS`
- `FixedEffectsOLS`
- `AbsorbingOLS`
- `IV2SLS`
- `IVAbsorbingOLS`
- `Logit`
- `Probit`
- `Poisson`
- `PPMLHDFE`
- `DIDImputation`
- `EventStudyInteract`
- `CSDID`

### 6.2 Compat 层新增

新增目录：

- `src/statapy/compat/stata/`

最低文件规划：

- `src/statapy/compat/stata/__init__.py`
- `src/statapy/compat/stata/linear.py`
- `src/statapy/compat/stata/hdfe.py`
- `src/statapy/compat/stata/iv.py`
- `src/statapy/compat/stata/glm.py`
- `src/statapy/compat/stata/did.py`

对外导出：

- `regress`
- `xtreg_fe`
- `areg`
- `reghdfe`
- `ivregress_2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`

### 6.3 API 设计原则

- 命令名优先与 Stata 对齐
- 参数名尽量贴近 Stata
- Python 侧仍保留关键字安全与可读性
- 不支持的参数必须显式报错
- 不允许“悄悄忽略参数”

## 7. 数学复现与源码复现门禁

这一轮所有社区命令都必须增加“源码复现门禁”。

### 7.1 代码实现前必须完成

每个命令先形成一份 `source-to-python mapping` 文档，至少包含：

- 主入口 `.ado`
- 核心 `.mata` / 辅助程序入口
- 关键统计对象
- 关键选项对哪些内部流程有影响
- Python 端对应函数或模块位置

### 7.2 代码审查时必须回答

对每个高风险命令，审查时必须能回答：

- 这段 Python 代码对应 Stata 源码的哪一段逻辑
- 如果结果对齐，是否是因为逻辑一致，还是因为数值上碰巧接近
- 关键修正因子和自由度口径是按源码搬过来的，还是自行推断的

如果答不出，则视为复现依据不足。

### 7.3 测试不得成为唯一真值

禁止下列行为：

- 仅通过放宽容差让测试通过
- 针对单个样例反推修正系数
- 通过临时数值变换拟合单次 Stata 输出

允许的唯一例外是：

- 已知数值优化器差异导致的极小浮点误差
- 且数学路径与源码/手册一致

## 8. 本轮开发顺序

本轮不建议平均用力，应按“对开源初版价值最大”的顺序推进。

### 优先级 A：先做产品层收口

1. 建立 `compat.stata` 命令层
2. 为高频命令建立 wrapper
3. 为每个 wrapper 编写支持矩阵

这是开源初版能否让用户上手的首要条件。

### 优先级 B：补全 HDFE 系列

1. `reghdfe`
2. `ppmlhdfe`
3. `ivreghdfe`

理由：

- 这是项目最具差异化的能力
- 也是最能体现“Python 可以真正替代 Stata 高频实证建模”的部分

### 优先级 C：补全 DID 社区命令

1. `did_imputation`
2. `eventstudyinteract`
3. `csdid`

### 优先级 D：再考虑 `rdrobust`

`rdrobust` 应进入本轮规划，但不强制作为初版开源 release 的阻塞项。

## 9. 文档与治理更新要求

本轮除了代码实现，还必须同步更新以下文档：

- [docs/architecture/public-api.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/architecture/public-api.md>)
- [docs/architecture/overview.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/architecture/overview.md>)
- [docs/backlog.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/backlog.md>)
- [docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/testing/test-case-catalog.md>)
- 各命令研究档案

并新增以下文档类型：

- `docs/command-support-matrix/`
  - `reghdfe.md`
  - `ivreghdfe.md`
  - `ppmlhdfe.md`
  - `did_imputation.md`
  - `eventstudyinteract.md`
  - `csdid.md`

每份支持矩阵至少包括：

- 已支持参数
- 计划支持参数
- 明确不支持参数
- 当前对齐证据
- 当前已知差异

## 10. 初版开源 release 的建议定义

建议把下一轮的目标版本定义为：

- `v0.2.0` 或 `v0.3.0` 开源预发布版

这个版本的成功标准不是“Stata 常见命令全都做完”，而是：

1. 用户可以用 Stata 命令名调用高频命令
2. `reghdfe` / `ppmlhdfe` / `ivreghdfe` 的高频主路径具备源码支持下的数学复现依据
3. 研究文档、支持矩阵、测试证据完整
4. 未支持功能被清晰标识，而不是模糊处理

## 11. 本轮不建议立刻承诺的内容

为了避免范围失控，本轮不建议把以下内容作为初版 release 的硬阻塞：

- 完整 `rdrobust`
- multi-way cluster 的全命令统一实现
- 完整 `margins`
- 所有命令的完整 `predict` 子选项
- 所有官方命令的全部权重语法
- 所有 DID 命令的完整选项面

这些都可以进入后续版本，但不应抢占 HDFE 命令面与 API 收口的优先级。

## 12. 下一步执行建议

本计划落地后，后续执行应分为三类任务：

1. `API restructuring tasks`
   - 建立 `compat.stata`
   - 补 wrapper
   - 重写公开入口与 README 示例

2. `source-backed completion tasks`
   - 逐个命令对照本地镜像源码补全功能
   - 优先 `reghdfe` / `ppmlhdfe` / `ivreghdfe`

3. `support-matrix and release-hardening tasks`
   - 输出支持矩阵
   - 清理命令边界
   - 为开源初版做文档与命名收口

本计划是下一轮开发的总纲，不直接替代任务卡。后续所有 Claude Code 执行任务都应从本计划继续拆解，而不是重新定义方向。
