# 当前任务

你现在进入 **审计主线任务包 007**：`rdrobust` 完整度推进（Phase B）。

当前主线不再横向扩别的命令，而是继续按审计计划把 vendor 命令做深做全。  
这一轮的重点是把 `rdrobust` 从 **最小 sharp RD 子集** 推进到 **常见 sharp RD 工作流可用** 的 Phase B 子集。

## 当前激活任务
- [docs/tasks/audit-mainline-package-007-rdrobust-completeness-phase-b.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/tasks/audit-mainline-package-007-rdrobust-completeness-phase-b.md>)

## 必须先阅读
1. [docs/tasks/audit-mainline-package-007-rdrobust-completeness-phase-b.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/tasks/audit-mainline-package-007-rdrobust-completeness-phase-b.md>)
2. [docs/research/rdrobust-source-map.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/research/rdrobust-source-map.md>)
3. [docs/command-support-matrix/rdrobust.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/command-support-matrix/rdrobust.md>)
4. [docs/audit/audit-findings.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/audit/audit-findings.md>)
5. [docs/audit/project-gaps.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/audit/project-gaps.md>)
6. [docs/audit/next-development-plan.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/audit/next-development-plan.md>)
7. [docs/operations/executor-playbook.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/operations/executor-playbook.md>)
8. [docs/operations/codex-review-protocol.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/operations/codex-review-protocol.md>)

## 本轮重点

- 先做 `rdrobust` 的自动带宽与 `covs()` 最小子集，再谈更大参数面
- 必须坚持 source-backed / formula-backed 实现，不能靠调容差或特例修补过测试
- `rdrobust` source map、support matrix、wrapper、测试证据要同步收口
- 不顺手改 `reghdfe` / `ppmlhdfe` / `ivreghdfe` / DID 内核

## 已知延后项

- 历史 `REPORT.md` 中关于 `ivreghdfe` Package 004 与 DID Package 005 的 fresh-run 旧数字问题，当前按项目决策不再阻塞主线。
- 本轮不要求回头修这些旧报告；如有必要，只在 release-facing known issues 中继续保持登记。

## 回报要求

完成后在 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/workspace/current-task/REPORT.md>) 中明确说明：

- 自动带宽选择实现了什么、没有实现什么
- `covs()` 实现了什么、没有实现什么
- 估计过程 / 偏差修正 / VCE 与 Stata / 源码如何对应
- 更新了哪些 source map / support matrix / release-facing 文档
- 跑了哪些 synthetic / dual-run / pytest
- 最新 fresh run 结果
