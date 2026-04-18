# 审计主线任务包 002 返工：`reghdfe` 文档与证据链一致性收口

## 1. 返工背景

`reghdfe` Phase B 的代码实现和测试主线已经通过，但主线任务包 002 仍未放行，因为核心证据文档没有完全收口。

当前主要矛盾是：

- `docs/research/reghdfe-source-map.md` 里同时存在旧的 Phase A 结论和新的 Phase B 结论
- `docs/command-support-matrix/reghdfe.md` 顶部完整度状态仍写成 `Phase A Subset`

这会直接破坏“源码支撑、数学口径优先”的审计链。

## 2. 本轮只做什么

只做文档一致性返工，不扩实现，不改算法。

必须收口以下文件：

- [docs/research/reghdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/research/reghdfe-source-map.md>)
- [docs/command-support-matrix/reghdfe.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/command-support-matrix/reghdfe.md>)
- 如有必要，微调 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/workspace/current-task/REPORT.md>) 里的措辞，但不要重写已正确的测试结果

## 3. 必须完成的修正

### A. 修正 source map 的 `predict` 映射

`docs/research/reghdfe-source-map.md` 第 4 节当前仍保留旧说法，必须改成与当前实现一致：

- `xb` = 仅 reported 系数的线性预测，不含 FE 贡献
- `xbd` = 含 FE 的完整预测
- `d` = `xbd - xb`
- `residuals` = `y - xbd`
- `dresiduals` = `y - xb`
- `stdp` 仍未实现

不能继续保留 “`d` / `xbd` 未实现” 或 “`xb` 含 FE” 这种旧结论。

### B. 修正 source map 的 wrapper parameter matrix

必须把以下条目改到与当前代码一致：

- `keepsingletons`
- `noconstant`

不能再写成 wrapper 未暴露或总是加常数。

### C. 更新 `reghdfe` support matrix 的完整度状态

`docs/command-support-matrix/reghdfe.md` 顶部完整度状态必须从旧的 `Phase A Subset` 更新成与当前任务阶段一致的表述。

推荐写法方向：

- 仍然 `Partial`
- 但已进入 `Phase B`
- 明确写出本轮新纳入的行为：
  - `keepsingletons`
  - `noconstant`
  - expanded `predict`

### D. 保证四方一致

修完后必须保证以下四方不再互相冲突：

1. `src/statapy/compat/stata/hdfe.py`
2. `src/statapy/estimators/absorbing_ols.py`
3. `docs/research/reghdfe-source-map.md`
4. `docs/command-support-matrix/reghdfe.md`

## 4. 验证要求

本轮不用重跑全量 golden matrix，但至少要回报：

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests -v
```

并在报告中明确写：

- 修了哪些文档冲突
- 修后 source map / support matrix / code 如何一一对应

## 5. 完成标准

本轮通过的最低标准：

- `reghdfe-source-map.md` 不再保留与当前实现冲突的旧结论
- `reghdfe.md` 的完整度状态不再停留在 `Phase A`
- 报告、support matrix、source map、代码四者一致

做到这一点后，Codex 再决定是否下放下一步主线任务：`ppmlhdfe` 完整度推进。
