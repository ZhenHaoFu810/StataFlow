# 审计驱动的下一轮开发推进计划

## 1. 总体目标

下一轮不再以“新增几个命令”作为目标，而以两个更严格目标驱动：

1. 把 `research/vendor/stata_community/` 下的高价值命令从“高频子集实现”推进到“完整命令复现”
2. 把当前项目从“高质量 Alpha”推进到“可被严格宣称为 Stata 开源命令映射库”的状态

## 2. 第一优先级：修复 release-blocking 问题

### 2.1 Vendor 命令完整度分级收口

#### 目标

对以下命令逐个形成正式“完整度清单”：

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `rdrobust`

#### 完成标准

每个命令都要有：

- `implemented`
- `verified`
- `missing`

三类条目清单，不能再用“整体已支持”模糊表述。

#### 验证标准

- support matrix 更新
- source map 更新
- README 总览更新

### 2.2 `rdrobust` 正式进入开发主线

#### 目标

停止把 `rdrobust` 作为“只有镜像、以后再说”的边缘项。

#### 完成标准

至少完成：

- `docs/research/rdrobust-source-map.md`
- `docs/command-support-matrix/rdrobust.md`
- `src/statapy/compat/stata/` 预留 `rdrobust` 入口规划
- 首轮 synthetic + real-data 测试设计

#### 验证标准

- 文档齐全
- backlog 与 test-case catalog 登记齐全

## 3. 第二优先级：HDFE 系列完整度推进

### 3.1 `reghdfe`

#### 目标

把 `reghdfe` 从 Phase A 子集推进到更接近完整命令。

#### 重点开发项

- 更完整 `absorb()` 语义
- singleton / keepsingletons 行为边界
- 更完整 DoF 与 nested/mobility 逻辑
- 更完整 `predict` 子选项
- 更清楚的 robust/cluster 行为矩阵

#### 完成标准

- 不是只有 1-2 FE 高频路径
- support matrix 中的 planned 项显著减少
- source map 能清楚说明每个新增功能的源码映射

### 3.2 `ppmlhdfe`

#### 目标

把 `ppmlhdfe` 从“主路径可用”推进到“复杂真实数据更可靠”。

#### 重点开发项

- separation 检测
- 更完整优化/收敛控制
- 更完整输出层
- 更丰富 predict 语义

#### 完成标准

- separation 不再是未实现的大缺口
- gravity / 稀疏计数场景更可用

### 3.3 `ivreghdfe`

#### 目标

把 `ivreghdfe` 从“2SLS + FE + VCE 子集”推进到“更接近真正 IV 命令”。

#### 重点开发项

- first-stage 输出
- 弱工具与诊断工具链
- 更完整 FE + IV 组合语义

#### 完成标准

- wrapper 层与结果 schema 能支持更完整 IV 使用场景

## 4. 第三优先级：DID 社区命令完整度推进

### 4.1 `did_imputation`

#### 目标

补齐常用命令选项，而不只停留在 `allhorizons` / `autosample`。

#### 重点开发项

- `minn`
- `window`
- `pretrend`

### 4.2 `eventstudyinteract`

#### 目标

让接口从“能跑 IW”进一步逼近真实 Stata 命令体验。

#### 重点开发项

- 更完整 auto-generation 语义
- 更完整命令参数面

### 4.3 `csdid`

#### 目标

明确是否继续只做 `method="reg"` 子集，还是进入更完整 method 扩展。

#### 建议

若资源有限，可继续把 `csdid` 定位为子集实现，但必须在文档和发布说明里明确。

## 5. 接口与易用性推进

### 5.1 README 顶层定位重写

#### 目标

首页必须一眼看出：

- 哪些命令是完整支持
- 哪些只是子集支持
- 哪些尚未实现

### 5.2 支持矩阵产品化

#### 目标

把 support matrix 从“工程内部文档”升级成“开源用户可直接理解的产品说明”。

#### 完成标准

每个命令固定列出：

- fully supported
- partially supported
- explicitly unsupported
- not yet implemented

### 5.3 wrapper 与 core estimator 的边界继续固化

#### 目标

保持命令级 API 与内部类的清晰分层。

#### 完成标准

- 用户默认只需记住 Stata 命令名
- core estimator 作为高级接口存在，但不再承载外部产品叙事

## 6. 建议的下一轮任务包顺序

### 包 1：Vendor 完整度基线重构

- 为 6 个 vendor 命令输出统一完整度清单
- 把 `rdrobust` 正式纳入主线
- 更新 support matrix / source map / README

### 包 2：`reghdfe` 完整度提升

- 专注 `reghdfe`
- 不混入其他命令

### 包 3：`ppmlhdfe` 与 `ivreghdfe`

- HDFE 家族继续推进

### 包 4：DID 社区命令扩展

- `did_imputation`
- `eventstudyinteract`
- `csdid`

## 7. 下一轮验收标准

下一轮完成后，至少要满足：

- `rdrobust` 不再处于完全缺失状态
- `reghdfe` / `ppmlhdfe` / `ivreghdfe` 的 support matrix 中，“planned” 项显著减少
- README 首页能明确反映完整度分层
- 任一 vendor 命令都不能再仅凭 wrapper 存在就被误解为“完整支持”

## 8. 最终判断

当前项目的下一步，不是继续横向扩命令，而是把已经最有价值的社区命令做“做深、做全、做准”。

在这个目标下，最重要的路线是：

1. 正式承认当前版本是 `Alpha + partial replication`
2. 用审计结果倒逼 vendor 命令完整度提升
3. 优先完成 HDFE 系列
4. 把 `rdrobust` 从研究镜像推进到真正实现主线

