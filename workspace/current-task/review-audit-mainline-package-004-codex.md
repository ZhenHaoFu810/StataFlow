# Codex Review: 审计主线任务包 004（`ivreghdfe` Phase B）

## 结论

本轮 **打回**。

阻塞原因不是 `ivreghdfe` 的算法或测试失败，而是 **source-backed 核心证据文档 `docs/research/ivreghdfe-source-map.md` 仍保留多处 Phase A 旧结论，与当前代码、支持矩阵和测试状态不一致**。在主线审计模式下，这种 source map 不一致不能放行到下一条命令主线。

## 我实际复核的内容

### Fresh verification

```powershell
python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v
python -m pytest tests -v
```

结果：

- `ivreghdfe` 相关专项 → `75 passed`
- 全量 → `676 passed`

### Spot check

我额外检查了：

- `src/statapy/estimators/iv.py`
- `src/statapy/compat/stata/iv.py`
- `docs/research/ivreghdfe-source-map.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `workspace/current-task/REPORT.md`

当前真实实现已经支持并通过测试：

- wrapper: `noconstant`, `keepsingletons`
- estimator `predict(type="xb"|"xbd"|"residuals"|"d"|"dresiduals")`
- `vce="ols"|"robust"|"cluster"`

所以这轮阻塞点不是实现主线，而是 source map 仍未同步。

## 阻塞问题

### 1. syntax mapping 仍把 `noconstant` 说成内部始终加常数

`docs/research/ivreghdfe-source-map.md` 第 3.1 节还写着：

- Python 等价实现 `sets add_constant=True`

但当前 wrapper 已经公开支持：

- `noconstant`
- 并且传入 `IVAbsorbingOLS(add_constant=not noconstant)`

这会直接误导后续 source-backed 审计。

### 2. “Known Phase A Simplifications” 仍写着 `No predict beyond xb`

同一文件第 6 节还保留：

- `No predict beyond xb`

但当前代码、测试和支持矩阵都已经支持：

- `xb`
- `xbd`
- `residuals`
- `d`
- `dresiduals`

这属于明显过期结论。

### 3. `_cons` 映射段仍保留旧逻辑

第 3.8 节仍写：

- Python 会通过 `T` 矩阵恢复 `_cons`

但当前代码里：

- `IVAbsorbingOLS.fit()` 明确注释 `ivreghdfe never reports _cons`
- `_coef_names` 只包含 `x_endog + x_exog`

也就是说，这里保留的是旧实现痕迹，不再符合当前公共语义。

## 返工要求

本次返工 **不要求新增任何 `ivreghdfe` 算法实现**。只要求把以下文档收口到与当前真实实现一致：

- `docs/research/ivreghdfe-source-map.md`
- 如有必要，微调 `workspace/current-task/REPORT.md` 中对 source map 完整度的表述

## 返工通过标准

只有同时满足以下条件，才允许进入下一步主线任务：

1. `ivreghdfe-source-map.md` 不再保留 `add_constant=True` 的旧结论，而是明确说明 `noconstant` 的当前公共语义。
2. `ivreghdfe-source-map.md` 的 “Known Phase A Simplifications” 不再把 `predict` 说成仅支持 `xb`。
3. `ivreghdfe-source-map.md` 的 `_cons` 映射描述与当前代码和支持矩阵一致。
4. 重新跑：
   - `python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v`
   - `python -m pytest tests -v`
   全部通过。
