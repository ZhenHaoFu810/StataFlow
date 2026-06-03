# StataFlow `summary()` 方法开发计划

**日期:** 2026-04-30
**优先级:** 高（用户体验核心缺失）
**类型:** 纯显示功能 — 不涉及数学实现，不修改估计器代码

---

## 1. 背景

当前用户调用 Stata 命令后，返回 `ResultSchema` 对象，但该对象无 `__str__`、`__repr__` 或 `summary()` 方法。用户需要手动遍历 `result.coefficients` 并自行格式化打印（如 4 个 demo 文件所示）。这严重降低了交互式使用的体验。

所有必要数据已在 `ResultSchema` 中完整收集（`ModelInfo`, `FitInfo`, `SampleInfo`, `CoefficientRow`）。只需添加格式化输出层。

---

## 2. 目标输出效果

参照 Stata 17 回归输出格式，在终端中呈现结构化、对齐良好的结果表格：

```
reghdfe: lwage ~ exper
Absorbed FE: nr year         N = 4360
VCE: ols                     df_a = 552
──────────────────────────────────────────────────────
          |      Coef.   Std. Err.      t   P>|t|
──────────┼─────────────────────────────────────────
exper     |   0.063328    0.000848  74.68  0.000
_cons     |   1.649147    0.005372 306.97  0.000
──────────────────────────────────────────────────────
R² = 0.0003    R²-Adj = -0.0000    RMSE = 0.3567
F(1, 3807) = 1.23    Prob > F = 0.2678
```

---

## 3. 实现方案

### 3.1 添加 `ResultSchema.summary()` 方法

**文件:** `src/stataflow/results/result.py`

```python
def summary(self, file=None) -> Optional[str]:
    """Print a Stata-style regression table. Returns formatted string if file is not None."""
    lines = []
    # Header block → estimation command, sample info, VCE type
    # Separator
    # Coefficient table → names, betas, SEs, t/z-stats, p-values
    # Separator  
    # Footer block → R², F-stat, df_a (varies by estimator_family)
    # Notes → warnings, diagnostics
    
    output = "\n".join(lines)
    if file is None:
        print(output)
    else:
        file.write(output)
        return output
```

### 3.2 分 Estimator 族的输出格式

| Estimator Family | Header | Footer |
|-----------------|--------|--------|
| OLS / FE / absorbing_ols | y ~ x, N, VCE, df_a | R², R²-Adj, RMSE, F-stat |
| IV (2SLS / GMM / LIML) | y ~ x (x_endog = z), N, Estimator | R², F-stat, Hansen J (if GMM), weak-IV F (if first) |
| GLM (logit / probit) | y ~ x, N, VCE | Pseudo-R², Log-likelihood, LR chi2 |
| Poisson / ppmlhdfe | y ~ x, N, VCE, df_a (ppml) | Pseudo-R², Deviance, Log-likelihood |
| DID / CSDID / EventStudy | y, id, time, first_treat, N | ATT estimates, event-time coefs |
| RD (rdrobust) | y ~ x, cutoff, kernel, bwselect | tau, SE, bandwidths (h_l, h_r), effective N |

### 3.3 格式化细节

- **Coefficient names:** 最大宽度对齐；`_cons` 特殊处理
- **数值格式:** 系数保留 6 位小数（同 Stata）；SE 保留 6 位；t/z-stat 保留 2 位；p-value 保留 3 位
- **置信区间:** 可选项 `show_ci=True`（默认 `False`，保持简洁）
- **宽度:** 自动适配终端宽度（默认 80 列）

### 3.4 `__repr__` 快捷方式

```python
def __repr__(self):
    return self.summary(file=io.StringIO())
```

使得在 Jupyter/IPython 中直接输入 `result` 即可显示摘要。

---

## 4. 受影响的文件

| 文件 | 修改内容 |
|------|---------|
| `src/stataflow/results/result.py` | 添加 `ResultSchema.summary()` 方法 + `__repr__` |
| `examples/demo_regress.py` | 替换手动 print 为 `result.summary()` |
| `examples/demo_reghdfe.py` | 同上 |
| `examples/demo_ppmlhdfe.py` | 同上 |
| `examples/demo_ivregress_2sls.py` | 同上 |

**不修改** 任何估计器代码、测试代码、VCE 代码。

---

## 5. 分步执行

```
Step 1: 实现通用 summary() 方法骨架（result.py，~100 行）
  └── _build_header(): 命令名、因变量、自变量、N、VCE 类型
  └── _build_coef_table(): 系数表格
  └── _build_footer(): R²、F、RMSE 等拟合统计
  └── __repr__ 委托给 summary()

Step 2: 为 OLS / FE / AbsorbingOLS 定制 footer
  └── 从 FitInfo 提取 R²、R²-Adj、RMSE、F-stat、df_a

Step 3: 为 IV 命令定制
  └── 显示 estimator 类型（2SLS / GMM2S / LIML）
  └── 如果 first=True，显示一阶段 F
  └── 如果 GMM2S，显示 Hansen J

Step 4: 为 GLM 命令定制（logit / probit / poisson / ppmlhdfe）
  └── Pseudo-R²、Log-likelihood、Deviance
  └── ppmlhdfe 额外显示 df_a

Step 5: 为 DID / RD 命令定制
  └── CSDID: ATT 聚合、事件研究系数
  └── rdrobust: bandwidth、effective N

Step 6: 更新 4 个 demo 文件
  └── 将手动 print 循环替换为 result.summary()
```

---

## 6. 验证标准

- `regress(...).fit(vce="ols").summary()` 打印与 Stata 类似的输出
- `reghdfe(...).fit(vce="cluster").summary()` 显示 df_a、cluster VCE
- `ivreghdfe(...).fit(estimator="liml").summary()` 显示 LIML estimator
- `ppmlhdfe(...).fit(vce="robust").summary()` 显示 deviance、pseudo-R²
- `rdrobust(...).fit().summary()` 显示带宽
- 所有 demo 文件运行后输出完整表格
- 275 非 golden 测试 0 回归（summary 是纯打印，不影响计算）

---

## 7. 不在范围内

- 不修改任何估计器数学逻辑
- 不修改任何测试断言
- 不修改 CLI 接口
- 不添加表格渲染库依赖（纯 Python 字符串格式化）
- 不实现 `margins` / `test` / `lincom` 的 summary

---

*本计划是一个纯显示层功能，零风险，高用户体验价值。*
