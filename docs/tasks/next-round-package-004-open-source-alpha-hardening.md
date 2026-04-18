# 下一轮任务包 004：开源初版 Alpha 收口与发布准备

## 基本信息

- 任务名称：开源初版 Alpha 收口与发布准备
- 所属阶段：开源初版下一轮
- 对应 backlog 条目：
  - 开源命令映射产品化
  - 开源初版文档收口
  - 支持矩阵汇总
- 优先级：P1
- 执行人：Claude Code
- 审查人：Codex

## 目标

在命令层与高优先级开源命令补强后，对整个仓库做一次面向开源初版的产品化收口。

## 本轮必须交付

### A. README 与公开示例重写

README 必须体现：

- core estimator 层
- Stata command wrapper 层
- 当前已支持命令
- 当前未支持范围
- 真实数据与 Stata 对齐验证的说明

### B. 命令总览页

新增：

- `docs/command-support-matrix/README.md`

### C. 示例脚本或最小 demo

新增：

- `examples/`

至少包括：

- `regress`
- `reghdfe`
- `ppmlhdfe`
- `ivregress_2sls`

### D. 开源前一致性检查

检查：

- wrapper 名称是否统一
- README 示例是否都能运行
- 支持矩阵是否与 wrapper 报错一致
- 文档是否仍然夸大未完成功能

## 验收标准

- [ ] README 已面向外部用户重写
- [ ] 命令支持矩阵总览存在
- [ ] `examples/` 存在且高频命令可示范
- [ ] 文档、wrapper、测试、支持矩阵四者一致
- [ ] 开源初版边界清晰
