# Codex Review：审计主线任务包 002（`reghdfe` 完整度推进 Phase B）

## 审查结论

**结论：打回。**

本轮 `reghdfe` 的实现主线和测试主线基本成立，但还不能下放下一步主线任务，原因不是算法失败，而是 **核心证据链文档没有完全收口**。

我实际复跑了：

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests/golden/test_p3_reghdfe_basic.py tests/golden/test_p3_reghdfe_cluster.py tests/golden/test_p3_reghdfe_two_fe.py tests/golden/test_p3_reghdfe_real_panel.py tests/golden/test_p3_reghdfe_keepsingletons.py -v
python -m pytest tests -v
```

结果分别为：

- `25 passed`
- `74 passed`
- `663 passed`

这说明：

- `keepsingletons`
- `noconstant`
- `predict(xb/xbd/d/residuals/dresiduals)`

这批新增能力在实现层和测试层都已经站住。

阻塞点在于：任务包 002 明确要求同步更新 `reghdfe-source-map.md` 与 `reghdfe.md`，但这两份文档仍保留了与当前实现相冲突的旧结论。

## 阻塞问题

### 1. `reghdfe-source-map.md` 内部仍保留旧的 Phase A `predict` 结论

文件位置：

- [docs/research/reghdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/research/reghdfe-source-map.md>)

问题：

- 第 4 节仍写：
  - `xb` = 含 FE 的完整预测
  - `d` / `xbd` = 未实现
- 这和当前真实代码、support matrix、synthetic tests、报告都矛盾。

这不是措辞问题，而是 source-backed 审计文档内部自相矛盾，会直接误导后续的源码级完整复现工作。

### 2. `reghdfe-source-map.md` 的 wrapper parameter matrix 仍保留旧的未支持结论

同一文件中，第 5 节仍写：

- `keepsingletons`：wrapper 不暴露
- `noconstant`：wrapper 总是加常数

但当前实际代码：

- `statapy.compat.stata.reghdfe(..., keepsingletons=True)`
- `statapy.compat.stata.reghdfe(..., noconstant=True)`

都已支持。

### 3. `reghdfe.md` 顶部完整度状态仍停留在 “Phase A Subset”

文件位置：

- [docs/command-support-matrix/reghdfe.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/command-support-matrix/reghdfe.md>)

问题：

- 顶部仍写 `Partial / Phase A Subset`
- 但本轮任务本身就是要推进到 Phase B，并且确实补齐了 Phase B 行为

如果完整度状态不改，后续主线任务和审计结论都会失真。

## 非阻塞说明

- [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/workspace/current-task/REPORT.md>) 的 fresh run 数字现在已经更新为 `663 passed`，这一点不再阻塞。
- 当前我没有发现本轮新增 `reghdfe` 语义存在必须阻塞的数学错误。

## 返工要求

本次返工只做文档与状态收口，不再扩实现：

1. 统一修正 `docs/research/reghdfe-source-map.md`
2. 更新 `docs/command-support-matrix/reghdfe.md` 的完整度状态与文字描述
3. 确保 source map / support matrix / report / 当前代码四者一致

通过后，我再决定是否下放下一步主线任务（`ppmlhdfe` 完整度推进）。
