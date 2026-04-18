# Codex Review: 下一轮任务包 002

## 结论

本轮 **打回**，暂不下放任务包 003。

原因不是 HDFE 代码主路径失败。相反，我重新跑了：

- `python -m pytest tests/test_hdfe_synthetic.py -v` -> `21 passed`
- `python -m pytest tests/golden/test_p3_reghdfe_basic.py tests/golden/test_p3_reghdfe_cluster.py tests/golden/test_p3_reghdfe_two_fe.py tests/golden/test_p3_reghdfe_real_panel.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py tests/golden/test_w3_ppmlhdfe_basic.py tests/golden/test_w3_ppmlhdfe_cluster.py tests/golden/test_w3_ppmlhdfe_real_gravity.py -v` -> `128 passed`
- `python -m pytest tests -v` -> `482 passed`

阻塞点在于：**本轮最关键的新增交付之一是三份 source-to-python mapping 文档，但这些文档仍保留了明显过期且错误的结论。**

## 阻塞项

### 1. `reghdfe-source-map.md` 仍声称 robust 还未实现

文档中仍写着：

- `reghdfe_vce_robust()` -> `Currently missing`
- `vce(robust)` -> `To be added in this task`

但当前代码与测试已经显示：

- `AbsorbingOLS.fit(vce="robust")` 已存在
- `reghdfe()` wrapper 已接受 `vce="robust"`
- synthetic 与 golden 路径均已通过

这意味着 `reghdfe-source-map.md` 已经不能作为可信研究依据。

### 2. `ivreghdfe-source-map.md` 仍声称 robust 未支持

文档中仍写着：

- `vce(robust)` -> `Not yet supported — to be added`

但当前实现中：

- `IVAbsorbingOLS.fit(vce="robust")` 已存在
- `ivreghdfe()` wrapper 已接受 `vce="robust"`
- synthetic tests 已通过

这会直接误导后续源码复现工作。

### 3. `ppmlhdfe-source-map.md` 仍声称 offset/exposure 未暴露、未实现

文档中仍写着：

- wrapper 没有暴露 `offset` / `exposure`
- `offset(var)` / `exposure(var)` -> `To be implemented or hard-rejected`
- `No offset/exposure`

但当前实现中：

- `PPMLHDFE.__init__()` 已接受 `offset` 与 `exposure`
- `ppmlhdfe()` wrapper 已暴露 `offset` 与 `exposure`
- 互斥校验与 `exposure > 0` 校验都已存在
- synthetic tests 已覆盖这些路径

因此这份 source map 当前同样不可信。

### 4. 报告中的测试结论也已过期

`REPORT.md` 仍写 `400/401 passed` 和“环境偶发超时”，但我 fresh run 的全量结果已经是 `482 passed`。  
这不是最核心的阻塞点，但说明报告没有随着返工收口同步更新。

## 返工要求

必须新增一个小返工轮，**只收口文档与证据链，不再扩实现范围**：

1. 更新三份 source map，使其与当前真实代码、wrapper 和测试完全一致。
2. 对每份 source map 单独增加一节：
   - `已实现并有源码依据`
   - `已实现但仅是 Phase A 近似/等价实现`
   - `未实现`
3. 更新 `REPORT.md` 的测试状态和结论，不得再保留 `400/401` 的旧结论。
4. 不允许只改措辞，必须逐项核对 source map 中的参数支持、VCE、postestimation、已知边界。

## 放行条件

只有当以下条件同时满足，任务包 002 才能放行：

- 三份 source map 不再包含与当前代码矛盾的旧结论
- `REPORT.md` 与最新 fresh run 结果一致
- 返工不引入新的实现回归
