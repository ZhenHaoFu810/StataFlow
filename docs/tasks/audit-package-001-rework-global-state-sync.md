# 审计后任务包 001 返工：`rdrobust` 全局状态与证据链同步

## 1. 返工目标

本次返工**不要求继续扩 `rdrobust` 算法主路径**。

主目标只有一个：

把 `rdrobust` 从“局部实现已完成”推进到“项目全局状态、测试目录、support matrix 入口、执行报告”全部同步一致。

## 2. 必须完成的内容

### A. 同步全局任务池

更新 [docs/backlog.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/backlog.md>)：

- 正式增加 `rdrobust` 条目
- 明确它当前的命令族归属
- 明确它当前的状态不是 `done/full`，而是与 support matrix 一致的子集状态

### B. 同步测试样例目录

更新 [docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/testing/test-case-catalog.md>)：

- 增加 `rdrobust` 的 synthetic case
- 增加 `rdrobust` 的 real-data / official-example case
- 状态应与当前真实测试情况一致

### C. 同步 support matrix 总入口

更新 [docs/command-support-matrix/README.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/command-support-matrix/README.md>)：

- 在 `Research Archives` 段落中加入 `rdrobust-source-map.md`
- 如有必要，调整 `Alpha — Partial` 的状态说明，使其与 `rdrobust.md` 保持一致

### D. 修正执行报告

更新 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/workspace/current-task/REPORT.md>)：

- 撤回“六命令完整度状态已统一收口”这类不准确表述
- 回填最新 fresh run 结果
- 明确说明本轮返工只做状态同步，不扩算法面

## 3. 不需要做的事

本轮不要额外做：

- `rdrobust` 新算法扩展
- `fuzzy` / `bwselect` / `cluster` 新功能
- 其他 vendor 命令功能扩展

除非你在同步文档时发现会直接影响现有结论的严重错误。

## 4. 验证要求

至少执行并回报：

```powershell
python -m pytest tests/test_rdrobust.py -v
python -m pytest tests -v
```

如果代码本身没有变化，可以在报告里说明“fresh run 主要用于确认返工未引入回归”。

## 5. 完成标准

本轮返工通过的条件是：

- `rdrobust` 已正式进入 backlog
- `rdrobust` 已进入 test-case-catalog
- `rdrobust-source-map.md` 已进入 command-support-matrix README 的总入口
- 报告不再夸大完成度

