# 任务卡：Package A 返工（Codex 审查意见）

## 背景

`Package A - Correctness and Release Hygiene` 的主体实现已经完成，但当前交付还不能通过复审。

Codex 的复审结论是：

- 代码主干基本成立
- 测试当前通过
- 但仍有两处关键问题使当前交付不满足“单一、可审计、公开信息一致”的标准

因此本轮需要做一次小范围返工，而不是进入下一包。

## 本轮返工必须完成的事项

## 1. 修复 `did_imputation` 的 provenance 漂移

### 问题

当前文件：

- [src/stataflow/estimators/did_imputation.py](</D:/OneDrive - SAIF/PhD3/StataFlow/src/stataflow/estimators/did_imputation.py>)

当前 `ProvenanceInfo.stata_command` 仍然无条件写入：

- `allhorizons`
- `autosample`

即使用户在实际调用中没有启用这两个选项，生成的 `stata_command` 也会错误地宣称这些选项被使用了。

### 为什么这会导致交付不合格

这和 `Package A` 的任务目标直接冲突：

- 本轮目标之一就是清理实现与公开信息之间的漂移
- provenance 是对外可见的结果元数据，不能继续保留错误语义

### 要求

你必须：

- 修复 `stata_command` 的生成逻辑
- 只在选项实际启用时才拼接相应 option
- 保持命令字符串语义清楚，不要再无条件追加

### 验证

至少验证两种情形：

1. 默认调用时，`stata_command` 不应包含未启用的 `allhorizons` / `autosample`
2. 显式启用这些选项时，`stata_command` 应正确包含它们

如需要，请补最小测试。

## 2. 清理 `REPORT.md`

### 问题

当前：

- [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

仍然包含上一轮 `open-source-export-and-ci-root-cause-fix` 的整份旧报告，`Package A` 报告只是追加在后面。

### 为什么这会导致交付不合格

这不满足当前任务入口的要求：

- `REPORT.md` 应该是本轮任务的单一交付物
- 现在它是“上一轮旧报告 + 本轮报告”的拼接体
- 这会直接降低后续复审和归档的可审计性

### 要求

你必须：

- 把 `REPORT.md` 清理为只保留本轮 `Package A` 交付
- 保留当前 `Package A` 的有效内容
- 删除上一轮旧任务报告内容
- 在报告中追加一个简短“返工说明”小节，说明：
  - 最初为何未通过
  - 本轮返工补了什么
  - 返工后如何验证

## 不在本轮返工范围内的事项

以下内容不要顺手扩张：

- 新功能开发
- `Package B / C / D`
- 开源导出机制继续重构
- 新的 command completeness 扩展
- 和本轮返工无关的大规模文档重写

## 推荐执行顺序

1. 先修 `did_imputation.py`
2. 补必要测试
3. 清理 `REPORT.md`
4. 重跑最小验证
5. 在 `REPORT.md` 中记录返工结果

## 最低交付物

完成后至少应交付：

- 修复后的 [did_imputation.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow/src/stataflow/estimators/did_imputation.py)
- 如有需要，新增或更新的测试
- 清理后的 [REPORT.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md)

## 必须在报告中回答的问题

1. `stata_command` 之前为什么是错的
2. 现在如何按实际选项构造
3. 本轮补了哪些验证
4. 为什么现在可以重新提交复审

## 成功标准

只有当以下条件全部满足时，本轮返工才算完成：

- provenance 不再错误声明未启用选项
- `REPORT.md` 只保留 `Package A` 本轮交付
- 报告中有返工说明
- 验证结果已更新
