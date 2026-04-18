# 审计主线任务包 004 返工：`ivreghdfe` 报告证据链收口

## 任务类型

返工任务。  
**不要扩 `ivreghdfe` 算法。不要新增参数面。不要改动 source map 和支持矩阵。**

本轮只做一件事：把 `workspace/current-task/REPORT.md` 的 fresh-run 证据收口到与当前真实实现一致。

## 背景

Codex 复核后确认：

- `ivreghdfe` Phase B 的代码与测试主线是通过的；
- `docs/research/ivreghdfe-source-map.md` 已经收口；
- `docs/command-support-matrix/ivreghdfe.md` 已经收口；
- 当前唯一阻塞点是 `REPORT.md` 仍保留旧的 fresh-run 数字。

当前 fresh run 真实结果为：

```powershell
python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v
# 75 passed

python -m pytest tests -v
# 676 passed
```

## 本轮必须完成的事项

### 更新 REPORT 中的 fresh run 结果

文件：

- `workspace/current-task/REPORT.md`

要求：

- 第 4 节 fresh run 结果必须与当前真实 rerun 一致
- 不能继续保留旧数字：
  - `5 passed`
  - `76 passed`
- 报告结论必须明确：
  - 本轮返工只修报告证据链，不新增算法
  - 当前 `ivreghdfe` Phase B 主线已由既有代码完成，本轮只是证据链收口

## 禁止事项

- 不要扩 `ivreghdfe` 数值实现
- 不要再改 `docs/research/ivreghdfe-source-map.md`
- 不要再改 `docs/command-support-matrix/ivreghdfe.md`
- 不要新增新的 golden case
- 不要顺手启动 DID 主线

## 回报要求

完成后在 `workspace/current-task/REPORT.md` 中明确写清：

1. fresh run 最终结果
2. 为什么这次返工只涉及报告证据链，不涉及算法

## 通过标准

Codex 只在以下条件同时满足时放行：

1. `workspace/current-task/REPORT.md` fresh run 数字与当前真实 rerun 一致。
2. 报告明确说明：这轮返工只修报告证据链，不涉及算法。
3. 重新跑以下命令全部通过：

```powershell
python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v
python -m pytest tests -v
```
