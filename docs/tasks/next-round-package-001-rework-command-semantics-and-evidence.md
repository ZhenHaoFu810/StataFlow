# 下一轮任务包 001 返工：命令语义与证据矩阵收口

## 基本信息

- 任务名称：任务包 001 返工：命令语义与证据矩阵收口
- 对应原任务：`docs/tasks/next-round-package-001-command-surface-and-support-matrix.md`
- 优先级：P0
- 执行人：Claude Code
- 审查人：Codex

## 背景

任务包 001 已完成大部分结构性交付，但当前不能放行到任务包 002，原因不是测试没过，而是：

1. `reghdfe()` 的对外语义还没真正和命令名对齐
2. 支持矩阵中存在虚构或失真的证据路径
3. 报告夸大了“无语义冲突”的状态

## 本轮只做这些

### A. 修正 `reghdfe()` 的公共语义

必须确保：

- 用户调用 `reghdfe()` 时，结果对象中的命令标签是 `reghdfe`
- 相关元数据不再泄露成 `areg`
- 单 absorb 与多 absorb 只是内部实现差异，不应改变 wrapper 的外部命令身份

### B. 全面清洗支持矩阵证据路径

至少核查并修正所有 13 份支持矩阵中的：

- golden test 路径
- real-data case 路径
- 本地源码镜像路径
- case id 引用

要求：

- 只能引用仓库中真实存在的文件或目录
- case id 与 `docs/testing/test-case-catalog.md` 保持一致
- 不允许继续使用旧 wave 编号或虚构 case 名

### C. 修正完成报告

`workspace/current-task/REPORT.md` 必须重写：

- 删除“无 core / wrapper 语义冲突”的错误结论
- 单列“本轮修掉了哪些语义冲突”
- 单列“支持矩阵证据已重新核对”

## 测试要求

至少执行并回报：

1. wrapper 专项测试
2. 全量测试
3. 一个直接 spot check：
   - 调用 `reghdfe(..., absorb='g1')`
   - 明确展示 `result.model.command`

## 验收标准

- [ ] `reghdfe()` 结果对象语义已收口
- [ ] 支持矩阵不再引用不存在的路径
- [ ] `REPORT.md` 结论真实
- [ ] wrapper 专项测试通过
- [ ] 全量测试通过

## 明确不做

- 不提前进入任务包 002
- 不扩新参数
- 不扩新算法
