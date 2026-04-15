# Wave 4 Final Rework: CSDID Event-Study SE 对齐

## 基本信息

- 任务名称：Wave 4 最终返工
- 执行人：Claude Code
- 审查人：Codex

## 目标

完成 `csdid` 在真实数据 event-study 聚合标准误上的最后收口，使 `Wave 4` 可以按严格口径放行。

## 本轮只做什么

- 只聚焦 `CSDID.estat_event()` 和相关影响函数 / 聚合标准误逻辑
- 只修 `csdid` 的 real-data SE 偏差
- 只更新相关 golden test、报告和状态文件

## 本轮明确不做什么

- 不改 `did_imputation`
- 不改 `eventstudyinteract`
- 不推进到 `Wave 5`
- 不扩展到 `drdid`、`did2s`、`honestdid`

## 任务要求

1. 找出 `csdid` 多 pair event times 标准误仍比 Stata 偏差 `5%` 到 `10%` 的具体原因。
2. 在数学上修正 event-study 聚合标准误实现。
3. 收紧 `tests/golden/test_w4_csdid_real_ezunem.py` 的标准误容差，不允许继续使用 `rtol=2e-1` 掩盖差异。
4. 更新 `workspace/current-task/REPORT.md`，撤回“该偏差可接受”的结论。
5. 若 Wave 4 最终通过，再同步更新 `docs/backlog.md` 中 `DID / Event Study Extensions` family 状态为 `done`。

## 强制验证命令

```powershell
python -m pytest tests/golden/test_w4_csdid_basic.py -v
python -m pytest tests/golden/test_w4_csdid_real_ezunem.py -v
python -m pytest tests -v
```

## 通过标准

只有同时满足以下条件，Codex 才会放行整个 Wave 4：

1. `tests/golden/test_w4_csdid_real_ezunem.py` 在收紧容差后通过。
2. `REPORT.md` 不再把 `csdid` 的 SE 偏差写成可接受。
3. 不存在未解释的关键统计口径偏差。
4. 全量测试通过。
