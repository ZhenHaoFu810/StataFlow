# 审计主线任务包 004 返工：`ivreghdfe` source map 一致性收口

## 任务类型

返工任务。  
**不要扩 `ivreghdfe` 算法。不要新增参数面。不要改动主估计逻辑。**

本轮只做一件事：把 `docs/research/ivreghdfe-source-map.md` 收口到与当前真实实现一致。

## 背景

Codex 复核后确认：

- `ivreghdfe` Phase B 的代码与测试主线是通过的；
- 当前阻塞点是 source-backed 核心文档仍保留 Phase A 旧结论。

当前 fresh run 真实结果为：

```powershell
python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v
# 75 passed

python -m pytest tests -v
# 676 passed
```

## 本轮必须完成的事项

### 1. 修正 3.1 节的 `noconstant` 映射描述

文件：

- `docs/research/ivreghdfe-source-map.md`

要求：

- 不得再写 Python 侧固定 `add_constant=True`
- 必须与当前 wrapper / estimator 语义一致：
  - wrapper 暴露 `noconstant`
  - estimator 使用 `add_constant=not noconstant`

### 2. 修正第 6 节的 predict 旧结论

文件：

- `docs/research/ivreghdfe-source-map.md`

要求：

- 删除或改写 `No predict beyond xb`
- 必须与当前 Phase B 实现一致，明确：
  - `xb`
  - `xbd`
  - `residuals`
  - `d`
  - `dresiduals`

### 3. 修正 `_cons` 映射描述

文件：

- `docs/research/ivreghdfe-source-map.md`

要求：

- 不得再保留旧的 `_cons` 恢复逻辑描述
- 必须与当前代码和支持矩阵一致：
  - 当前 `IVAbsorbingOLS` 不报告 `_cons`

### 4. 如有必要，更新 REPORT

文件：

- `workspace/current-task/REPORT.md`

要求：

- 仅在 source-map 收口后同步更新对应表述
- 不要再重写整份报告

## 禁止事项

- 不要扩 `ivreghdfe` 数值实现
- 不要新增 wrapper 参数
- 不要顺手启动 DID 主线
- 不要顺手扩 factor grammar

## 回报要求

完成后在 `workspace/current-task/REPORT.md` 中明确写清：

1. `ivreghdfe-source-map.md` 哪些旧结论被修正
2. 修正后与哪些代码位置保持一致
3. fresh run 最终结果
4. 为什么这轮返工不涉及算法，仅涉及 source-backed 证据链

## 通过标准

Codex 只在以下条件同时满足时放行：

1. `ivreghdfe-source-map.md` 不再保留 `add_constant=True` 的旧结论。
2. `ivreghdfe-source-map.md` 不再把 `predict` 写成仅支持 `xb`。
3. `ivreghdfe-source-map.md` 的 `_cons` 描述与当前代码一致。
4. 重新跑以下命令全部通过：

```powershell
python -m pytest tests/test_compat_stata_iv.py tests/test_hdfe_synthetic.py tests/golden/test_w2_ivreghdfe_basic.py tests/golden/test_w2_ivreghdfe_cluster.py tests/golden/test_w2_ivreghdfe_real_panel.py -v
python -m pytest tests -v
```
