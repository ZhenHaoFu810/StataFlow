# 下一轮任务包 002：HDFE 系列源码支撑下的完整度推进

## 基本信息

- 任务名称：HDFE 系列源码支撑下的完整度推进
- 所属阶段：开源初版下一轮
- 对应 backlog 条目：
  - `reghdfe`
  - `ppmlhdfe`
  - `ivreghdfe`
- 优先级：P0
- 执行人：Claude Code
- 审查人：Codex

## 目标

本任务包的目标是把当前已经存在的 HDFE 系列最小实现，从“高频子集可跑”推进到“有明确源码依据、支持矩阵清晰、主路径数学过程与 Stata 社区源码对应”的可开源初版水位。

## 必读文档

1. `docs/next-round-open-source-plan.md`
2. `docs/research/reghdfe.md`
3. `docs/research/ivreghdfe.md`
4. `docs/research/ppmlhdfe.md`
5. `research/vendor/stata_community/reghdfe/`
6. `research/vendor/stata_community/ivreghdfe/`
7. `research/vendor/stata_community/ppmlhdfe/`
8. `docs/operations/codex-review-protocol.md`

## 前置条件

- [ ] 任务包 001 已完成
- [ ] 命令层 wrapper 已存在
- [ ] 支持矩阵框架已存在

## 本轮必须交付

### A. source-to-python mapping 文档

必须新增：

- `docs/research/reghdfe-source-map.md`
- `docs/research/ivreghdfe-source-map.md`
- `docs/research/ppmlhdfe-source-map.md`

### B. `reghdfe` 提升

至少推进：

- `vce("robust")`
- `reghdfe()` wrapper 的正式命令语义
- `predict` 高频子选项文档化与必要补全
- 更明确的 absorb / cluster / singleton / nested FE 行为

### C. `ppmlhdfe` 提升

至少推进：

- `ppmlhdfe()` wrapper 的正式命令语义
- `offset` 与 `exposure` 的明确实现或显式拒绝
- separation 行为的文档化与测试扩展

### D. `ivreghdfe` 提升

至少推进：

- `ivreghdfe()` wrapper 的正式命令语义
- FE + IV 主路径的 source-backed 对照说明
- 常见 cluster 路径的对齐补强

## 明确不做

- multi-way cluster 全覆盖
- 所有历史或冷门选项
- 完整 `estat` 生态
- 完整 `predict` 全子选项

## 关键原则

### 1. 源码优先于样例调参

如果某段 Python 行为不能指出对应源码依据，即使测试通过也不能视为完成。

### 2. 不允许“为了过样例而局部修补”

必须避免：

- 针对个别数据集硬编码修正
- 通过放宽 real-data 容差掩盖系统性偏差
- 在缺少源码依据时随意调整 df / small-sample correction

### 3. 测试必须更灵活

除原有 golden tests 外，本轮建议新增：

- 基于源码自带测试思路改编的 synthetic cases
- 不同 FE 结构、不同 cluster 结构下的交叉样例
- 参数拒绝测试

## 验收标准

- [ ] 三份 source map 文档完整
- [ ] `reghdfe/ppmlhdfe/ivreghdfe` wrapper 均已收口
- [ ] 完成本任务包中列出的高频路径补强
- [ ] 新增测试具有“多样灵活性”
- [ ] 不支持参数已显式拒绝
- [ ] 全量测试通过
- [ ] 无无法解释的数学偏差
