# 下一轮任务包 003：DID / Event Study 社区命令源码支撑下的完整度推进

## 基本信息

- 任务名称：DID / Event Study 社区命令源码支撑下的完整度推进
- 所属阶段：开源初版下一轮
- 对应 backlog 条目：
  - `did_imputation`
  - `eventstudyinteract`
  - `csdid`
  - `rdrobust` 研究预备
- 优先级：P1
- 执行人：Claude Code
- 审查人：Codex

## 目标

把当前已实现的 DID / Event Study 命令从“高频核心路径已经跑通”推进到“命令语义更像 Stata 社区命令、源码依据更明确、真实数据验证更有说服力”的状态。

## 必读文档

1. `docs/research/did_imputation.md`
2. `docs/research/eventstudyinteract.md`
3. `docs/research/csdid.md`
4. `research/vendor/stata_community/did_imputation/`
5. `research/vendor/stata_community/eventstudyinteract/`
6. `docs/operations/codex-review-protocol.md`

## 本轮必须交付

### A. 命令 wrapper 收口

正式建立：

- `did_imputation()`
- `eventstudyinteract()`
- `csdid()`

### B. source-backed 文档补全

新增：

- `docs/research/did_imputation-source-map.md`
- `docs/research/eventstudyinteract-source-map.md`

### C. `csdid` 边界清晰化

必须明确：

- 当前仅支持 `method="reg"`
- 支持矩阵、wrapper、README 说法一致

### D. 真实数据测试增强

本轮必须至少新增一类更灵活的变体检查，例如：

- 不同事件时间窗口
- 不同 cohort 过滤
- control group 边界验证

## 明确不做

- 完整 `rdrobust` 实现
- 所有 DID 命令的完整历史选项

## 验收标准

- [ ] 三个命令 wrapper 已建立
- [ ] source map 文档补齐
- [ ] `csdid` 边界清晰
- [ ] real-data 测试比当前更灵活
- [ ] 全量测试通过
- [ ] 无靠宽容差掩盖的系统性偏差
