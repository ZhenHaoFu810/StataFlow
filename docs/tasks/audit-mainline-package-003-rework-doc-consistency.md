# 审计主线任务包 003 返工：`ppmlhdfe` 报告证据链收口

## 任务类型

返工任务。  
**不要扩 `ppmlhdfe` 算法。不要新增参数面。不要改动主估计逻辑。**

本轮只做一件事：把 `workspace/current-task/REPORT.md` 的 fresh-run 证据收口到与当前真实实现一致。

## 背景

Codex 复核后确认：

- `ppmlhdfe` Phase B 的代码与测试主线是通过的；
- `ppmlhdfe` support matrix 已经收口；
- 当前唯一阻塞点是 `REPORT.md` 仍保留旧的 fresh-run 数字。

当前 fresh run 真实结果为：

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
# 28 passed

python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py tests/golden/test_w3_ppmlhdfe_cluster.py tests/golden/test_w3_ppmlhdfe_real_gravity.py tests/golden/test_p3_ppmlhdfe_fit_stats.py -v
# 37 passed

python -m pytest tests -v
# 672 passed
```

## 本轮必须完成的事项

### 更新 REPORT 中的 fresh run 结果

文件：

- `workspace/current-task/REPORT.md`

要求：

- 第 4 节 fresh run 结果必须与当前真实 rerun 一致
- 不能继续保留旧数字：
  - `8 passed`
  - `7 passed`
  - `72 passed`
- 报告结论必须明确：
  - 本轮返工只修文档一致性，不新增算法
  - 当前 `ppmlhdfe` Phase B 主线已由既有代码完成，本轮只是证据链收口

## 禁止事项

- 不要扩 `ppmlhdfe` 数值实现
- 不要再改 `docs/command-support-matrix/ppmlhdfe.md`，除非为了修正文案笔误
- 不要新增新的 wrapper 参数
- 不要新增新的 golden case
- 不要顺手启动 `ivreghdfe` 主线

## 回报要求

完成后在：

- `workspace/current-task/REPORT.md`

中明确写清：

1. fresh run 最终结果
2. 为什么这次返工只涉及报告证据链，不涉及算法

## 通过标准

Codex 只在以下条件同时满足时放行：

1. `workspace/current-task/REPORT.md` fresh run 数字与当前真实 rerun 一致。
2. 报告明确说明：这轮返工只修报告证据链，不涉及算法。
3. 重新跑以下命令全部通过：

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py tests/golden/test_w3_ppmlhdfe_cluster.py tests/golden/test_w3_ppmlhdfe_real_gravity.py tests/golden/test_p3_ppmlhdfe_fit_stats.py -v
python -m pytest tests -v
```
