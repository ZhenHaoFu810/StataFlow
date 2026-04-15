# Wave 执行轮次规则

## 核心原则

从现在起，每个 wave 默认固定为 **3 轮任务**，不再随意膨胀。

统一节奏如下：

1. `Round 1: Research`
2. `Round 2: Minimum implementation`
3. `Round 3: Real-data validation and hardening`

这样做的目的：

- 保持审查节奏稳定
- 避免 Claude Code 一轮做太多
- 保证每个 wave 都能形成完整闭环

## Round 1：Research

目标：

- 补研究档案
- 锁定源码或官方手册来源
- 定义最小实现子集
- 设计 synthetic 与 real-data 样例

限制：

- 不写核心实现
- 不修改公共 API
- 不提前推进 backlog 为 `done`

通过标准：

- 对应研究档案完整
- 样例已在 `docs/testing/test-case-catalog.md` 登记
- 源码入口或手册入口已明确

## Round 2：Minimum implementation

目标：

- 实现最小可用功能
- 跑通 synthetic 黄金样例
- 锁定核心统计规则

限制：

- 不做真实数据收口
- 不顺势扩展额外功能
- 不把未研究清楚的选项面一并加入

通过标准：

- synthetic 黄金样例通过
- 全量测试通过
- 实现边界与任务卡一致

## Round 3：Real-data validation and hardening

目标：

- 用公开真实数据做双跑
- 修复边界问题
- 回填 backlog、样例目录和文档状态
- 决定该 wave 是否阶段完成

限制：

- 不引入新的大功能面
- 不把真实数据失败写成“可接受”直接放行

通过标准：

- 至少一个真实公开数据样例通过
- 全量测试通过
- 样例目录与 backlog 状态一致
- Codex 明确确认该 wave 收口

## 各 Wave 的默认拆法

### Wave 1：Panel / FE / HDFE

1. `areg / reghdfe` 研究轮
2. `areg` 最小实现轮
3. `areg` 真实数据验证与收口轮

说明：

- `reghdfe` 在 Wave 1 中先完成研究基础与最小范围设计
- 不把 `reghdfe` 实现强行挤进 `areg` 收口轮

### Priority Wave：`reghdfe`

1. `reghdfe` 研究收束轮
2. `reghdfe` 最小实现轮
3. `reghdfe` 真实数据验证与收口轮

说明：

- 这是 `Wave 1` 收尾后的独立优先 wave
- 默认只做 `reghdfe Phase A`，不顺势扩展到 `ivreghdfe`、`ppmlhdfe` 或多向 cluster
- 目标是把 `reghdfe` 从“研究完成”推进到“可独立验收的最小兼容实现”

### Wave 2：IV / GMM

1. `ivregress / ivreghdfe` 研究轮
2. `ivregress 2sls` 最小实现轮
3. 真实数据验证与 HDFE 联动收口轮

### Wave 3：Binary / Count

1. `logit / probit / poisson / ppmlhdfe` 研究轮
2. 官方内建离散与计数命令最小实现轮
3. 真实数据验证与 `ppmlhdfe` 最小子集收口轮

### Wave 4：DID / Event Study Extensions

1. DID / event study 研究轮
2. 最优先 DID 命令最小实现轮
3. 真实数据验证与扩展兼容层收口轮

### Wave 5：Postestimation

1. `predict / margins` 高频子集研究轮
2. 最小 postestimation 实现轮
3. 真实数据验证与输出层收口轮

## 审查方式

Codex 在每轮的审查重点固定如下：

- Round 1：
  - 研究是否扎实
  - 来源是否可信
  - 样例设计是否足够
- Round 2：
  - 统计实现是否与 Stata 对齐
  - synthetic 样例是否严格通过
- Round 3：
  - 真实数据是否稳定
  - 文档与状态是否收口
  - 是否允许把条目标记为 `done`
