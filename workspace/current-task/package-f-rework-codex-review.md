# 返工任务卡：Package F - Codex Review Rework

## 背景

`Package F` 首轮交付已经把一批 release-candidate 级文档问题修到了正确方向，但 Codex 复审发现仍有两处阻断问题，因此当前版本还不能视为通过：

1. `docs/cookbook.md` 中仍残留至少一处编码损坏字符。报告声称修复了 cookbook 编码问题，但实际文件里 `Categorical × continuous interaction` 这一节仍然是损坏字符。
2. `REPORT.md` 中“导出后开源镜像文件数”仍与实际导出结果不一致。当前实测开源镜像为 167 个非 git 文件，但报告仍写 166。

本轮返工只修这两类问题，不扩新功能。

## 返工目标

让 `Package F` 的文档修复和报告表述重新与仓库真实状态对齐。

## 必修项

## F-R1. 修复 `docs/cookbook.md` 的剩余编码损坏

当前实现位于：

- [docs/cookbook.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/cookbook.md>)

现状问题：

- 报告声称 cookbook 的编码损坏字符已修复
- 但 `Categorical × continuous interaction` 这一节仍残留损坏字符

你必须：

- 把该节标题修成正常可读文本
- 顺手再检查同一文件中是否还有类似编码损坏字符
- 确保主仓和导出后的开源镜像都一致

## F-R2. 修正 `REPORT.md` 的导出文件计数

当前实现位于：

- [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

现状问题：

- 报告写“开源镜像文件数：166 个非 git 文件”
- 实际在 `StataFlow_open_source` 中复核是 167 个非 git 文件

你必须：

- 用实际导出结果重新核对文件总数
- 如果要保留分类统计，也必须与总数一致
- 不能再写未经验证的估算数字

## 建议验证

至少做以下验证：

- 重新执行一次导出
- 统计 `StataFlow_open_source` 的非 `.git` 文件数
- 检查 `docs/cookbook.md` 中相关标题已恢复正常

## 不在返工范围内的事项

- 不扩新功能
- 不重做 Package A-E 已通过的内容
- 不新开下一包

## 交付要求

返工完成后，`REPORT.md` 必须新增一个“返工说明”小节，明确写：

1. Codex 复审指出了哪两类问题
2. 你如何修复
3. 做了哪些复核
4. 哪些数字或文档表述被纠正

## 完成标准

只有当以下条件全部满足时，返工才算完成：

- `docs/cookbook.md` 不再残留该处编码损坏字符
- `REPORT.md` 中的导出文件计数与实际结果一致
- 相关验证完成，可再次交给 Codex 复审
