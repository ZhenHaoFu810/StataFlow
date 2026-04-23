# 当前任务

`Package G` 首轮交付未通过 Codex 最终复审。`workspace/current-task` 的唯一执行任务现已切换为：

- [package-g-rework-codex-review.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/package-g-rework-codex-review.md>)

在本轮返工修完并再次通过 Codex 复审之前，不得继续宣称可以发布，也不要执行新的功能性工作。

## 你必须先读

1. [workspace/current-task/package-g-rework-codex-review.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/package-g-rework-codex-review.md>)
2. [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)
3. [workspace/current-task/REPORT_TEMPLATE.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT_TEMPLATE.md>)

## 执行边界

- 只修本轮 Codex 复审明确指出的文档一致性遗漏
- 不扩新功能
- 不改统计实现
- 不改 manifest 范围
- 若需验证，只做与本轮返工点直接相关的最小验证
- 修完后必须重新导出到 `StataFlow_open_source`

## 执行顺序

1. 修 `reghdfe.md`、`ivreghdfe.md`、`ppmlhdfe.md` 中仍残留的 `1-2 absorbed FEs` 旧口径
2. 运行最小必要验证
3. 重新执行导出
4. 更新 [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

## 交付要求

完成后必须在 `REPORT.md` 中新增“Package G Rework”说明，明确写出：

- Codex 复审指出的遗漏
- 修改了哪些文件
- 如何修正
- 做了哪些验证
- 导出后开源镜像是否同步

## 完成判定

只有当以下条件全部满足时，本轮返工才算完成：

- `docs/command-support-matrix/reghdfe.md` 不再保留 `1-2 absorbed FEs`
- `docs/command-support-matrix/ivreghdfe.md` 不再保留 `1-2 absorbed FEs`
- `docs/command-support-matrix/ppmlhdfe.md` 不再保留 `1-2 absorbed FEs`
- 主仓 `pytest tests/ -q --ignore=tests/golden/` 继续通过
- 重新导出后，`StataFlow_open_source` 与修正后的 HDFE 文档口径一致
