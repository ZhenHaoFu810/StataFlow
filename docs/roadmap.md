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

## 当前默认优先级

当前主线默认锁定为：

1. `Panel / FE / HDFE`
2. `Priority Wave: reghdfe`
3. `IV / GMM`
4. `Binary / Count`

在没有新的用户优先级调整前，不自动切换主线。
