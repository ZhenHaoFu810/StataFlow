# Codex Review: 审计主线任务包 004（`ivreghdfe` Phase B）返工复核

## 结论

本轮 **仍打回**。

`ivreghdfe` 的实现、测试，以及 `ivreghdfe-source-map.md` 现在都已经收口；当前唯一剩余阻塞点是 **`REPORT.md` 的 fresh-run 证据仍然是旧数字**，与当前真实 rerun 结果不一致。按主线门禁，这仍然不能作为 clean package-closure artifact。

## 我实际复核的内容

### Fresh verification

```powershell
python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v
python -m pytest tests -v
```

结果：

- `ivreghdfe` 相关专项 → `75 passed`
- 全量 → `676 passed`

### 文档 spot check

我复核了：

- `docs/research/ivreghdfe-source-map.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `workspace/current-task/REPORT.md`

当前状态：

- source map 中关于 `noconstant`、`predict`、`_cons` 的旧结论已经修正
- 支持矩阵与当前实现一致
- 但 `REPORT.md` 第 4 节 fresh run 结果仍保留旧数字

## 当前唯一阻塞问题

### `REPORT.md` fresh run 结果仍未与当前真实 rerun 一致

`workspace/current-task/REPORT.md` 里仍写：

- `5 passed`
- `76 passed`

但当前真实 fresh run 结果是：

- `75 passed`
- `676 passed`

这说明完成报告还没有与最终验证状态对齐。

## 返工要求

本次返工 **不要求新增任何 `ivreghdfe` 算法实现，也不要求再改 source map 或支持矩阵**。  
只要求更新：

- `workspace/current-task/REPORT.md`

## 返工通过标准

只有同时满足以下条件，才允许进入下一步主线任务：

1. `REPORT.md` 的 fresh run 数字与当前真实 rerun 结果一致。
2. 报告明确说明：这轮返工只修报告证据链，不涉及算法。
3. 重新跑：
   - `python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v`
   - `python -m pytest tests -v`
   全部通过。
