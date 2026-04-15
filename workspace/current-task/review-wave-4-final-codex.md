# Wave 4 最终审查结论（Codex）

## 结论

本轮 **不通过**，暂不放行 `Wave 4`。

这次不通过的原因不是缺少真实数据样例，也不是测试文件没补齐；这些部分已经完成。当前阻塞点是：

- `csdid` 在真实数据 event-study 聚合标准误上，仍然与 Stata 存在约 `5%` 到 `10%` 的系统性偏差
- 当前黄金测试通过的原因，是对这些标准误使用了过宽的 `rtol=2e-1`
- 报告也明确把这部分差异记录为已知偏差并申请放行

在你要求“审查不仅是测试通过，更是计量算法在数学上的正确性”的口径下，这不能通过。

## 我独立复核的证据

我重新运行了以下命令：

```powershell
python -m pytest tests/golden/test_w4_did_imputation_real_ezunem.py tests/golden/test_w4_eventstudyinteract_real_ezunem.py tests/golden/test_w4_csdid_real_ezunem.py -v
python -m pytest tests -v
```

结果：

- Wave 4 real-data tests：`12 passed`
- 全量测试：此前本轮同样为全绿

这说明：

- 真实数据双跑样例已经补齐
- 旧 wave 没被破坏

但这些通过结果 **不能** 证明 `csdid` 的推断已经在数学上对齐，因为当前 `csdid` real-data test 对部分标准误使用了过宽容差。

## 阻塞点

### 1. `csdid` real-data SE 仍存在未解释的 5%–10% 偏差

报告已经明确写出：

- 单 pair event times 可以紧密匹配
- 多 pair event times 的标准误仍与 Stata 存在 `5%` 到 `10%` 偏差

这意味着当前 event-study 聚合方差实现还没有真正收口。

### 2. 黄金测试把关键推断差异用宽容差放过了

`tests/golden/test_w4_csdid_real_ezunem.py` 对多 pair event times 的标准误使用了 `rtol=2e-1`。这会让目前的推断偏差在测试中被掩盖。

在 Wave 4 这种整包放行节点上，我不能接受这种“测试绿了但关键统计量仍未严格对齐”的状态。

### 3. family 状态还没有真正进入完工态

虽然三个命令条目已推进为 `done`，但 `docs/backlog.md` 里的 `DID / Event Study Extensions` family 仍是 `ready`。这与当前“整包 wave 申请完成”的说法并不一致，也说明治理状态本身还没有完全收口。

## 下一轮必须完成的内容

1. 修正 `csdid` event-study 聚合标准误的实现，使其在真实数据样例上不再依赖 `rtol=2e-1`。
2. 收紧 `tests/golden/test_w4_csdid_real_ezunem.py` 中对多 pair event times 标准误的容差。
3. 重写 `workspace/current-task/REPORT.md` 中关于 `csdid` SE 偏差“可接受”的结论。
4. 只有在 `csdid` 推断真正收口后，才把 `docs/backlog.md` 中 `DID / Event Study Extensions` family 推进为 `done`。

## 备注

`did_imputation` 和 `eventstudyinteract` 当前没有发现新的阻塞性数学问题。当前阻塞点集中在 `csdid` 的 event-study 聚合推断。
