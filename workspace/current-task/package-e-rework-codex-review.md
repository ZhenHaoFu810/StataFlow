# 返工任务卡：Package E - Codex Review Rework

## 背景

`Package E` 首轮交付已经具备可运行的导出机制，也能在当前默认目标上完成导出与测试，但 Codex 复审发现了两处实现级阻断问题和一组文档/报告漂移，因此当前版本还不能视为通过：

1. export 脚本缺少危险目标路径保护。如果 `--target-root` 被错误地指向主仓自身或其父子危险路径，当前脚本会把源仓当作清理目标，存在误删风险。
2. `--dry-run` 仍会执行 `dst.parent.mkdir(...)`，在目标目录不存在的情况下会实际创建目录，不符合 dry-run 语义。
3. 开源范围审计文档和报告里仍残留旧的 `rdrobust` 数据依赖表述，并且报告中的导出文件数统计与实际导出结果不一致。

本轮返工只修这些阻断项，不扩新功能。

## 返工目标

使导出脚本达到“可重复且安全”的最低要求，并让审计文档与报告重新和当前事实对齐。

## 必修项

## E-R1. 修复 export 脚本的危险目标路径保护

当前实现位于：

- [scripts/release/export_open_source.py](</D:/OneDrive - SAIF/PhD3/StataFlow/scripts/release/export_open_source.py>)

现状问题：

- 脚本只解析 `target_root`，但没有保护 `target == source` 或其他危险重叠路径
- 当前 orphan 清理逻辑会删除目标仓中不属于 whitelist 的文件
- 如果目标路径配置错误，存在清理源仓文件的风险

你必须加入显式保护，至少阻止以下情况：

- 目标目录等于源仓根目录
- 目标目录是源仓的祖先目录
- 目标目录位于源仓内部
- 任何你判断会导致清理逻辑作用到主仓的危险路径

要求：

- 保护必须在任何复制、建目录、清理动作之前执行
- 报错必须是清晰的 `ValueError` 或显式非零退出，并说明为什么目标路径危险
- 补至少一个针对危险路径的测试或最小验证

## E-R2. 修复 `--dry-run` 的副作用

当前实现位于：

- [scripts/release/export_open_source.py](</D:/OneDrive - SAIF/PhD3/StataFlow/scripts/release/export_open_source.py>)

现状问题：

- 虽然 dry-run 不复制文件，但循环里无条件执行了 `dst.parent.mkdir(...)`
- 这意味着 dry-run 仍然会修改文件系统

你必须修成：

- `--dry-run` 下绝不创建目录
- `--dry-run` 下绝不删除文件
- dry-run 只输出“would ...” summary，不产生任何写入

建议验证：

- 对一个不存在的自定义目标目录执行 dry-run
- 验证目标目录不会被创建

## E-R3. 修正文档与报告漂移

必须同步修正：

- [docs/operations/open-source-scope-audit.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/operations/open-source-scope-audit.md>)
- [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

至少应修正：

1. scope audit 中仍把 `tests/test_rdrobust.py` 的依赖写成 `research/vendor/.../rdrobust_senate.dta`
2. scope audit 中仍保留“`stata/output/rdrobust_senate_with_z.dta` 之后会修”的旧叙述，但当前代码已不依赖它
3. `REPORT.md` 中导出后文件数/结构统计要与实际导出结果一致

如果发现还有其他明显的发布级表述漂移，可以顺手修，但要在报告中列出来。

## 测试 / 验证要求

至少补以下验证之一，且推荐都补：

- 危险目标路径被拒绝
- dry-run 不创建目录
- 修正后的 scope audit 与当前 `tests/test_rdrobust.py` 依赖一致
- 实际导出后 `StataFlow_open_source` 仍能通过非 golden 测试

## 不在返工范围内的事项

- 不扩新 estimator 功能
- 不改 manifest 的总体开源边界设计，除非为修正已确认的文档/事实不一致
- 不推进自动化 export CI
- 不重做 Package A-D 已通过的功能

## 交付要求

返工完成后，`REPORT.md` 必须新增一个“返工说明”小节，明确写：

1. Codex 复审指出了哪些问题
2. 你分别如何修复
3. 新增了哪些验证
4. 哪些文档或统计表述被纠正

## 完成标准

只有当以下条件全部满足时，返工才算完成：

- export 脚本不能对危险目标路径执行导出/清理
- `--dry-run` 没有文件系统副作用
- scope audit / report 与当前代码和测试依赖一致
- 相关验证通过，可再次交给 Codex 复审
