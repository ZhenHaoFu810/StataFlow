# Wave 5 Full Package: Postestimation Report (Rework)

**Date:** 2026-04-15  
**Executor:** Claude Code  
**Task:** `docs/tasks/wave-5-full-package-postestimation.md`

---

## 1. 执行摘要

Wave 5 首次提交后被 Codex 审查驳回，阻塞点为 `margins` 结果对象错误地包含 `_cons`。现已修复该数学语义问题，并收紧了 golden tests 的断言。全量测试通过，等待 Codex 复审。

---

## 2. Codex 审查结论与修复

### 2.1 阻塞点（来自 `review-wave-5-codex.md`）

- `margins` 结果对象中仍包含 `_cons`
- 但 Stata 的 `margins, dydx(*)` 与 `margins, dydx(*) atmeans` 并不会把常数项当作可报告的边际效应变量
- 这是一个**数学语义层面**的问题，不是展示差异

### 2.2 已完成的修复

#### 修复 1：`_build_margins_result` 中心化剔除 `_cons`

在 `src/statapy/postestimation.py` 中修改 `_build_margins_result`：

- 若 `coef_names` 中包含 `_cons`，则计算前将其从 `effects`、`J`（行和列）、`cov_beta`（行和列）以及 `coef_names` 中一并剔除。
- 这样所有调用 `_build_margins_result` 的模型（OLS、FE、AbsorbingOLS、Logit、Probit、Poisson、PPMLHDFE）都自动获得正确的语义，无需在每个 estimator 中重复处理。

```python
names = list(coef_names)
if "_cons" in names:
    cons_idx = names.index("_cons")
    names.pop(cons_idx)
    effects = np.delete(effects, cons_idx, axis=0)
    J = np.delete(np.delete(J, cons_idx, axis=0), cons_idx, axis=1)
    cov_beta = np.delete(np.delete(cov_beta, cons_idx, axis=0), cons_idx, axis=1)
```

#### 修复 2：收紧 golden tests

在所有 Wave 5 margins 测试中显式断言 `_cons` 不应出现在结果对象中：

- `tests/golden/test_w5_margins_logit_basic.py`
- `tests/golden/test_w5_margins_real_mroz.py`
- `tests/golden/test_w5_margins_real_crime1.py`

新增断言示例：
```python
assert "_cons" not in py_marg.params, "margins result should not contain _cons"
assert "_cons" not in py_dydx.params, "margins dydx result should not contain _cons"
assert "_cons" not in py_atmeans.params, "margins atmeans result should not contain _cons"
```

同时把原来 `for name in [..., "_cons"]` 的遍历循环改为仅遍历实际解释变量，避免对 `_cons` 做条件宽松的"如果 Stata 里没有就跳过"比较。

---

## 3. 实现覆盖范围（与首次提交一致）

### 3.1 `predict`

| 模型 | 支持类型 |
|------|----------|
| `OLS` | `xb`, `residuals` |
| `FixedEffectsOLS` | `xb`, `residuals`（对齐 Stata `xtreg, fe` 语义） |
| `AbsorbingOLS` | `xb`, `residuals`（LSDV 空间） |
| `Logit` | `xb`, `pr` |
| `Probit` | `xb`, `pr` |
| `Poisson` | `xb`, `mu` |
| `PPMLHDFE` | `xb`, `mu` |

### 3.2 `margins`

| 模型 | 支持类型 | 备注 |
|------|----------|------|
| `OLS` | `dydx` | 结果等于系数（不含 `_cons`） |
| `FixedEffectsOLS` | `dydx` | 结果等于系数（不含 `_cons`） |
| `AbsorbingOLS` | `dydx` | 结果等于系数（不含 `_cons`） |
| `Logit` | `dydx`, `atmeans` | 完整 Jacobian + delta-method SE（不含 `_cons`） |
| `Probit` | `dydx`, `atmeans` | 完整 Jacobian + delta-method SE（不含 `_cons`） |
| `Poisson` | `dydx`, `atmeans` | 完整 Jacobian + delta-method SE（不含 `_cons`） |
| `PPMLHDFE` | `dydx`, `atmeans` | 完整 Jacobian + delta-method SE（不含 `_cons`） |

---

## 4. 测试状态

### Wave 5 专项测试

```bash
pytest tests/golden/test_w5_predict_basic.py -v
pytest tests/golden/test_w5_predict_real_wagepan.py -v
pytest tests/golden/test_w5_predict_real_mroz.py -v
pytest tests/golden/test_w5_margins_logit_basic.py -v
pytest tests/golden/test_w5_margins_real_mroz.py -v
pytest tests/golden/test_w5_margins_real_crime1.py -v
```

结果：**10/10 passed**

### 全量回归测试

```bash
pytest tests/ -v
```

结果：**428/428 passed**

---

## 5. 文档更新

- `docs/testing/test-case-catalog.md` — Wave 5 全部 9 个样例状态为 `done`
- `docs/backlog.md` — `Postestimation`、`predict` 高频子集、`margins` 高频子集状态为 `done`

---

## 6. 结论

Wave 5 Postestimation 的 `_cons` 语义阻塞点已修复。`margins` 结果对象现在与 Stata 一致：不再对常数项报告边际效应。Golden tests 已显式覆盖该语义约束。全量 428 项测试通过，等待 Codex 复审放行。
