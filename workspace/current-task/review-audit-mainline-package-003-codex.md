# Codex Review: 审计主线任务包 003（`ppmlhdfe` Phase B）返工复核

## 结论

本轮 **仍打回**。

`ppmlhdfe` 的实现、测试，以及 support matrix 本身已经收口；当前唯一剩余阻塞点是 **`REPORT.md` 的 fresh-run 证据仍然是旧数字**，与当前真实 rerun 不一致。按主线门禁，这仍然不能作为 clean package-closure artifact。

## 我实际复核的内容

### Fresh verification

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py tests/golden/test_w3_ppmlhdfe_cluster.py tests/golden/test_w3_ppmlhdfe_real_gravity.py tests/golden/test_p3_ppmlhdfe_fit_stats.py -v
python -m pytest tests -v
```

结果：

- `tests/test_hdfe_synthetic.py` → `28 passed`
- `ppmlhdfe` golden / fit-stats 组合 → `37 passed`
- 全量 → `672 passed`

### 文档 spot check

我复核了：

- `docs/command-support-matrix/ppmlhdfe.md`
- `workspace/current-task/REPORT.md`

当前状态：

- support matrix 顶部完整度状态已经改成 `Partial / Phase B Subset`
- 重复的 `Alignment Evidence` 已经清理
- 但 `REPORT.md` 第 4 节 fresh run 结果仍保留旧数字

## 当前唯一阻塞问题

### `REPORT.md` fresh run 结果仍未与当前真实 rerun 一致

`workspace/current-task/REPORT.md` 里仍写：

- `8 passed`
- `7 passed`
- `72 passed`

但当前真实 fresh run 结果是：

- `28 passed`
- `37 passed`
- `672 passed`

这说明完成报告还没有与最终验证状态对齐。

## 返工要求

本次返工 **不要求新增任何 `ppmlhdfe` 算法实现，也不要求再改 support matrix**。  
只要求更新：

- `workspace/current-task/REPORT.md`

## 返工通过标准

只有同时满足以下条件，才允许进入下一步主线任务：

1. `REPORT.md` 的 fresh run 数字与当前真实 rerun 结果一致。
2. 报告明确说明：这轮返工只修报告证据链，不涉及算法。
3. 重新跑：
   - `python -m pytest tests/test_hdfe_synthetic.py -v`
   - `python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py tests/golden/test_w3_ppmlhdfe_cluster.py tests/golden/test_w3_ppmlhdfe_real_gravity.py tests/golden/test_p3_ppmlhdfe_fit_stats.py -v`
   - `python -m pytest tests -v`
   全部通过。
