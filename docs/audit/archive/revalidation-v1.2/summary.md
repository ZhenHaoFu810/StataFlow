# StataFlow 全功能再审查报告 v1.2

审查日期：2026-06-11  
审查对象：当前 `dev` 分支  
审查性质：只读问题识别，不含修复

## 总结结论

当前实现不能被判定为“所有既有功能均已可靠复现 Stata 17”。现有测试覆盖很广，但审查仍确认了多项会导致崩溃、错误样本、错误协方差、无效推断或与 Stata 语义直接冲突的问题。

本轮记录 **32 项**：

- P1：19 项
- P2：9 项
- P3：4 项

其中最需要优先修缮的不是新增命令，而是五个共享基础问题：

1. estimation sample 在 postestimation 和重复索引场景下不可靠；
2. FE 系数与 VCE schema 不一致，并缺少 within-collinearity 处理；
3. factor base level 在错误样本上确定；
4. 单 cluster 和 GLM 不收敛仍返回看似可用的推断结果；
5. CSDID 自定义聚类方差没有真正实现。

## 测试基线

| 基线 | 结果 | 解释 |
|---|---|---|
| 非 golden tests | 307 passed | 现有快速测试全部通过 |
| Python compileall | 通过 | 无语法级错误 |
| 完整 golden | 788 passed, 4 skipped, 16 errors | DID 真实数据日志缺失，当前 checkout 不能全量复验 |

测试通过不能覆盖本报告中的问题，因为多项测试复制了实现自身假设，或只验证特定数据集而没有覆盖秩退化、非法 outcome、单 cluster、重复索引和 schema 不变量。

## 阻断性结论

以下能力在修缮前不应被无条件标记为严格 Stata 复现：

- `xtreg, fe`：within-collinearity 可崩溃，常数项 VCE 缺失。
- 所有 factor wrappers：缺失值改变有效类别时，base 与常数参数化可能错误。
- `estat summarize`：当前不使用真实 estimation sample。
- HDFE/IV-HDFE：重复索引时 sample mask 错误。
- cluster VCE：单一 cluster 可产生伪精确推断。
- GLM：非法因变量和不收敛模型仍可返回结果对象。
- CSDID custom cluster：标准误没有按指定 cluster 聚合。
- DID 真实数据验证：仓库当前缺少所需日志，完整 golden 不是可重复全绿状态。
- `rdplot`：自动 bin selection 仍存在已记录的 2–3 倍 Stata 差异。

## 与 v1.1 的关系

v1.1 将既有 108 项归为已修复、已知限制或未来项。本轮没有否定其全部工作，但证明“无 open issue”不再成立：部分问题是 v1.1 后回归，部分是此前测试未覆盖的输入域和 schema 不变量，另一些则是已经公开承认但仍超过 `<1e-6` 的统计偏差。

## 文档索引

- `findings.md`：32 项问题、严重性、状态、复现和数学风险说明。
- `progress.md`：执行命令和基线结果。
- `task_plan.md`：本轮范围、阶段与审查约束。
- `source-map.md`：问题 ID 到当前代码位置的索引。

后续修缮应以 `findings.md` 的 ID 为唯一追踪键，并在关闭每项前补充最小回归测试和对应 Stata 17 双跑证据。
