# 当前任务

你现在进入 **发布任务包 001**：首次开源 Alpha 修缮。

当前目标不是继续扩算法，也不是推进新的命令完整度。  
这一轮只做 **首次对外开源发布面修缮**：把当前仓库从“高质量 Alpha，但更像内部研究仓库”推进到“适合第一次正式对外开源展示与试用”的状态。

## 当前激活任务
- [docs/tasks/release-package-001-first-open-source-alpha-remediation.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/tasks/release-package-001-first-open-source-alpha-remediation.md>)

## 必须先阅读
1. [docs/tasks/release-package-001-first-open-source-alpha-remediation.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/tasks/release-package-001-first-open-source-alpha-remediation.md>)
2. [docs/qa/first-open-source-release-review.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/qa/first-open-source-release-review.md>)
3. [docs/qa/first-open-source-release-issues.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/qa/first-open-source-release-issues.md>)
4. [docs/qa/first-open-source-release-remediation-plan.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/qa/first-open-source-release-remediation-plan.md>)
5. [docs/operations/executor-playbook.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/operations/executor-playbook.md>)
6. [docs/operations/codex-review-protocol.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/operations/codex-review-protocol.md>)

## 本轮重点

- 不新增任何功能
- 只修首次开源的发布阻塞项与仓库表面问题
- 必须让 README、包元数据、release 文档、examples、仓库根目录形态相互一致
- 必须补上最基本的开源工程信号（如 LICENSE、CI workflow）

## 已知约束

- 不回头扩 `reghdfe` / `ppmlhdfe` / `ivreghdfe` / DID / `rdrobust` 算法
- 不为了“仓库看起来干净”而静默删除仍有价值的内部脚本；应优先迁移、归档或忽略

## 回报要求

完成后在 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/workspace/current-task/REPORT.md>) 中明确说明：

- 修掉了哪些 release-blocking 问题
- `pyproject.toml` / README / release 文档如何统一了
- 根目录哪些文件被迁移、清理或归档
- 新增了哪些 CI / release-facing 文件
- 跑了哪些验证命令
- 最新 fresh run 结果
- 当前仓库是否已经达到“适合第一次正式对外开源 Alpha 发布”的标准
