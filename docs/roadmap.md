# 总体路线图

## Phase 0: Bootstrap

目标：

- 初始化项目骨架
- 建立 Stata runner 最小可用链路
- 打通第一条 OLS 双跑测试

完成标志：

- 能从 Python 触发 Stata 运行一个最小 `.do`
- 能读取 Stata 结构化输出
- 能执行一条 Python vs Stata 的字段级比较

前置条件：

- 本机可访问 Stata 17
- 基础 Python 项目结构已建立

风险：

- Stata 批处理调用方式不稳定
- 结构化导出设计过早绑定具体实现

不纳入项：

- 完整估计器实现
- 完整 CI 覆盖

## Phase 1: Linear Core

目标：

- OLS
- `vce(robust)`
- `vce(cluster)`
- 样本筛选、常数项、共线性处理

完成标志：

- 对上述能力有稳定公开 API
- 每项能力都有至少一组双跑黄金测试

前置条件：

- Phase 0 完成
- 结果 schema 稳定

风险：

- 自由度和修正因子规则不清晰
- 共线性处理与 Stata 细节偏差

不纳入项：

- 权重
- FE

## Phase 2: Weights And Single FE

目标：

- `aweight`
- 单向 FE
- FE 边界情况样例库

完成标志：

- `aweight` 与单向 FE 均有稳定实现与双跑样例
- FE 转换路径与显式哑变量回归结果可互证

前置条件：

- Phase 1 完成

风险：

- FE 自由度与 summary 语义难以完全复刻
- 面板非平衡样本的样本掩码规则复杂

不纳入项：

- 双向 FE
- `areg` 对外接口

## Phase 3: Absorption Foundation

目标：

- 稳定内部吸收/投影接口
- 为 `areg`、双向 FE、`reghdfe` 风格扩展清除架构障碍

完成标志：

- 内核层可以复用残差化组件
- 不破坏现有 API 与测试基线

前置条件：

- Phase 2 完成

风险：

- 性能优化冲动压倒正确性
- 为未来扩展过度设计

不纳入项：

- 全量高维 FE 公开支持

## 后续候选 Phase

- 离散选择模型：`logit`、`probit`、`poisson`
- IV / GMM
- DID 与事件研究封装
- 多维聚类与更复杂协方差估计
