# VAL-LINEAR — Phase 2 双跑验证报告

**命令族:** Linear Base + Factor Variables  
**数据集:** Card (N=3,010) — `research/data/public/iv/card.csv`  
**Stata 版本:** 17.0 MP  
**Python 版本:** StataFlow 1.0.0  
**验证日期:** 2026-06-03  
**执行人:** Phase 2 双跑验证 Agent  

---

## 1. 验证概览

| 测试项 | Python 状态 | Stata 状态 | 结果 |
|--------|------------|-----------|------|
| 1. regress basic OLS | ✅ 通过 | ✅ 通过 | **PASS** |
| 2. regress robust VCE | ✅ 通过 | ✅ 通过 | **PASS** |
| 3. regress cluster VCE | ⚠️ 部分通过 | ✅ 通过 | **FAIL** (F-stat 数值爆炸) |
| 4. regress aweight | ✅ 通过 | ✅ 通过 | **PASS** |
| 5. regress noconstant | ⚠️ 部分通过 | ✅ 通过 | **FAIL** (F-stat 缺失) |
| 6. regress factor variables | ✅ 通过 | ✅ 通过 | **PASS** |
| 7. collinearity detection (LINEAR-01) | ❌ 失败 | N/A | **FAIL** (bug 确认) |
| 8. predict | ❌ 失败 | ✅ 通过 | **FAIL** (wrapper 未暴露 predict) |
| LINEAR-02 (2-way cluster __) | N/A | N/A | **FIXED in OLS, still in shared util** |
| LINEAR-03 (vce(cluster var) 语法) | N/A | N/A | **OPEN** |
| LINEAR-05 (level/beta/eform) | N/A | N/A | **CONFIRMED** |

---

## 2. 逐项验证详情

### 2.1 regress — basic OLS

**Python:**
```python
from stataflow.compat.stata.linear import regress
result = regress(df, y='lwage', x=['educ', 'exper', 'expersq', 'black', 'south'])
```

**Stata:**
```stata
regress lwage educ exper expersq black south
```

**比较结果:**

| 字段 | Python | Stata | 偏差 |
|------|--------|-------|------|
| N | 3,010 | 3,010 | 0 |
| R² | 0.265121 | 0.2651 | <1e-4 |
| Adj R² | 0.263898 | 0.2639 | <1e-4 |
| RMSE | 0.380762 | 0.38076 | <1e-5 |
| F(5,3004) | 216.7498 | 216.75 | <1e-2 |
| Prob > F | 0.0000 | 0.0000 | — |
| educ β | 0.0782330 | 0.078233 | <1e-6 |
| educ SE | 0.0035428 | 0.0035428 | <1e-6 |
| exper β | 0.0851268 | 0.0851268 | <1e-6 |
| expersq β | −0.0023404 | −0.0023404 | <1e-6 |
| black β | −0.1780477 | −0.1780477 | <1e-6 |
| south β | −0.1504920 | −0.150492 | <1e-6 |
| _cons β | 4.7963246 | 4.796325 | <1e-6 |

**结论:** 系数、SE、t、p、R²、F、df、N 全部在 1e-6 相对容差内对齐。**PASS**

---

### 2.2 regress — robust VCE

**Python:** `regress(..., vce='robust')`  
**Stata:** `regress ..., robust`

**比较结果:**

| 字段 | Python | Stata | 偏差 |
|------|--------|-------|------|
| educ SE | 0.0036886 | 0.0036886 | <1e-6 |
| exper SE | 0.0068201 | 0.0068201 | <1e-6 |
| expersq SE | 0.0003220 | 0.000322 | <1e-6 |
| black SE | 0.0177110 | 0.017711 | <1e-6 |
| south SE | 0.0153809 | 0.0153809 | <1e-6 |
| _cons SE | 0.0716322 | 0.0716322 | <1e-6 |
| F(5,3004) | 222.7004 | 222.70 | <1e-2 |

系数与 basic 完全一致（预期），稳健 SE 和 F-stat 完全对齐。**PASS**

---

### 2.3 regress — cluster VCE

**Python:** `regress(..., vce='cluster', cluster='south')`  
**Stata:** `regress ..., vce(cluster south)`

**比较结果:**

| 字段 | Python | Stata | 偏差 |
|------|--------|-------|------|
| educ SE | 0.0058100 | 0.00581 | <1e-5 |
| exper SE | 0.0108155 | 0.0108155 | <1e-5 |
| expersq SE | 0.0003774 | 0.0003774 | <1e-5 |
| black SE | 0.0657645 | 0.0657645 | <1e-5 |
| south SE | 0.0282078 | 0.0282078 | <1e-5 |
| _cons SE | 0.0133751 | 0.0133751 | <1e-5 |
| F-stat | **−5.75e+16** | **.** (missing) | ❌ 数值爆炸 |

**问题分析:**  
当 cluster 数极少时（`south` 只有 2 个取值），斜率协方差矩阵 `cov_slopes` 为奇异矩阵，`np.linalg.inv(cov_slopes)` 抛出 `LinAlgError`。当前代码在 `except` 块中返回 `f_stat = None`，但实际上异常**未被捕获**，因为 `np.linalg.inv` 在数值上返回了一个病态的逆矩阵（条件数极大），导致 Wald stat 为天文数字负值。

**结论:** SE 对齐，但 F-stat 在极端 cluster 数下数值不稳定。**FAIL**

---

### 2.4 regress — aweight

**Python:** `regress(..., aweight='weight')`  
**Stata:** `regress ..., aweight(weight)`

**比较结果:**

| 字段 | Python | Stata | 偏差 |
|------|--------|-------|------|
| educ β | 0.0784106 | 0.0784106 | <1e-6 |
| exper β | 0.0926752 | 0.0926752 | <1e-6 |
| expersq β | −0.0025379 | −0.0025379 | <1e-6 |
| black β | −0.2031372 | −0.2031372 | <1e-6 |
| south β | −0.1204090 | −0.120409 | <1e-6 |
| _cons β | 4.7421588 | 4.742159 | <1e-6 |
| R² | 0.2255808 | 0.2256 | <1e-4 |
| RMSE | 0.3817804 | 0.38178 | <1e-5 |
| F(5,3004) | 175.0072 | 175.01 | <1e-2 |

aweight 系数、SE、R²、F 全部对齐。**PASS**

---

### 2.5 regress — noconstant

**Python:** `regress(..., noconstant=True)`  
**Stata:** `regress ..., noconstant`

**比较结果:**

| 字段 | Python | Stata | 偏差 |
|------|--------|-------|------|
| educ β | 0.2996412 | 0.2996412 | <1e-6 |
| exper β | 0.3691561 | 0.3691561 | <1e-6 |
| expersq β | −0.0109710 | −0.010971 | <1e-6 |
| black β | 0.0416982 | 0.0416982 | <1e-6 |
| south β | 0.0195604 | 0.0195604 | <1e-6 |
| R² | 0.9903385 | 0.9903 | <1e-4 |
| RMSE | 0.6175519 | 0.61755 | <1e-5 |
| F-stat | **null** | **61604.34** | ❌ 未计算 |

**问题分析:**  
`OLS.fit()` 第 406 行逻辑为 `if self.add_constant and df_model > 0:`，当 `noconstant=True` 时直接跳过 F-stat 计算。但 Stata 在 `noconstant` 下仍然会报告 F-stat（检验所有系数联合显著性）。

**结论:** 系数、R² 对齐，但 F-stat 缺失。**FAIL**

---

### 2.6 regress — factor variables

**Python:** `regress(df, y='lwage', x=['i.black', 'c.educ##c.exper'])`  
**Stata:** `regress lwage i.black c.educ##c.exper`

**比较结果:**

| 字段 | Python | Stata | 偏差 |
|------|--------|-------|------|
| 1.black β | −0.2293063 | −0.2293063 | <1e-6 |
| educ β | 0.0478462 | 0.0478462 | <1e-6 |
| exper β | −0.0062525 | −0.0062525 | <1e-6 |
| c.educ#c.exper β | 0.0035841 | 0.0035841 | <1e-6 |
| _cons β | 5.3410913 | 5.341091 | <1e-6 |
| R² | 0.2385389 | 0.2385 | <1e-4 |
| F(4,3005) | 235.3402 | 235.34 | <1e-2 |

交互项 `c.educ##c.exper` 展开为 `educ`, `exper`, `c.educ#c.exper`，系数与 Stata 完全一致。**PASS**

---

### 2.7 collinearity detection — LINEAR-01 (关键)

**测试代码:**
```python
import numpy as np
from stataflow.estimators._vce_utils import detect_collinear_columns
X = np.zeros((5, 10))
X[:, 0] = [1, 0, 0, 0, 0]
X[:, 1] = [0, 1, 0, 0, 0]
X[:, 2] = [0, 0, 1, 0, 0]
X[:, 3] = [0, 0, 0, 1, 0]
X[:, 4] = X[:, 0] + X[:, 1]  # collinear with x0, x1
X[:, 5] = [0, 0, 0, 0, 1]     # independent
names = [f'x{i}' for i in range(10)]
X_res, dropped, kept = detect_collinear_columns(X, names)
```

**结果:**

| 指标 | 值 |
|------|-----|
| matrix_rank(X) | 5 |
| X_res.shape[1] | **4** |
| kept | [0, 1, 2, 3] |
| dropped | ['x4', 'x5', 'x6', 'x7', 'x8', 'x9'] |

**问题分析:**  
`detect_collinear_columns` 第 140 行使用 `R = np.linalg.qr(X, mode='r')`。当 `n < p`（5 行 10 列）时，QR 返回的 `R` 形状为 `(5, 10)`。第 144 行判断 `i < R.shape[0] and abs(R[i, i]) > tol`，由于 `R.shape[0] = 5`，循环到 `i = 5` 时条件不满足，直接判定 `x5` 为共线并丢弃。但 `x5` 是独立的单位向量 `[0,0,0,0,1]`，应被保留。正确做法应基于矩阵秩而非 QR 对角线长度来判定独立列。

**结论:** Bug 确认。rank=5 时仅保留 4 列，x5 被错误丢弃。**FAIL**

---

### 2.8 predict

**Python:**
```python
result = regress(df, y='lwage', x=['educ', 'exper', 'expersq', 'black', 'south'])
result.predict(type='xb')       # AttributeError
result.predict(type='residuals') # AttributeError
```

**问题分析:**  
`regress()` wrapper 返回 `model.fit()` 的结果，即 `ResultSchema` 对象。`predict()` 方法定义在 `OLS` 类上，不在 `ResultSchema` 上。用户无法通过 wrapper 直接调用 predict。

**底层模型直接调用:**
```python
model = OLS(data=df, y='lwage', x=[...])
result = model.fit()
xb = model.predict(type='xb')
resid = model.predict(type='residuals')
```

| 统计量 | Python (OLS.predict) | Stata predict | 偏差 |
|--------|----------------------|--------------|------|
| xb Mean | 6.261832 | 6.261832 | <1e-6 |
| xb Std | 0.228511* | 0.228511 | 0 (N-1 校正后) |
| xb Min | 5.395018 | 5.395018 | <1e-6 |
| xb Max | 6.821743 | 6.821743 | <1e-6 |
| resid Mean | ~0 | 1.83e-10 | ~0 |
| resid Std | 0.380446* | 0.380446 | 0 (N-1 校正后) |
| resid Min | −1.690925 | −1.690925 | <1e-6 |
| resid Max | 1.376881 | 1.376881 | <1e-6 |

*Python np.std 默认使用 N 分母；与 Stata 的 N-1 校正后完全一致。

**结论:** 底层 predict 逻辑正确，但 wrapper 未暴露 predict 接口。**FAIL (接口缺失)**

---

## 3. Phase 1 已知问题验证

### LINEAR-01: detect_collinear_columns n < p 时 IndexError / 错误丢弃列
- **状态:** ❌ **未修复** — 错误丢弃独立列，rank=5 时仅保留 4 列
- **根因:** `np.linalg.qr` 在 `n < p` 时返回的 `R` 行数为 `n`，循环条件 `i < R.shape[0]` 过早截断
- **影响:** 高维场景（如大量 FE 或交互项）下会错误丢弃有效变量

### LINEAR-02: 2-way cluster 分隔符 __ 冲突
- **状态:** ⚠️ **部分修复** — `OLS.fit()`（regress）已改用 tuple-based 编码避免冲突（ols.py:362-369）
- **状态:** ❌ **`compute_multiway_cluster_vce` 共享函数仍使用 `f"{a}__{b}"` 字符串拼接**（_vce_utils.py:107）
- **影响:** AbsorbingOLS、IVAbsorbingOLS、PPMLHDFE 仍受 __ 冲突影响

### LINEAR-03: regress wrapper 不支持 vce(cluster var) 语法
- **状态:** ❌ **未修复** — wrapper API 为 `vce='cluster', cluster='south'`，不支持 Stata 原生 `vce(cluster south)` 单字符串语法
- **影响:** API 与 Stata 语法不完全兼容

### LINEAR-05: wrapper 硬拒绝 level()/beta/eform
- **状态:** ✅ **按设计工作** — `**kwargs` 会抛出 `ValueError: Unsupported arguments: ['level']` 等
- **评估:** 这是符合 AGENTS.md 第 6 节 "Never silently ignore unsupported parameters" 的设计选择，但用户体验上 Stata 常用选项被硬拒绝

---

## 4. 新发现问题 (写入 NEW-LINEAR.md)

详见同目录 `NEW-LINEAR.md`。概要：

1. **NEW-LINEAR-01:** Cluster VCE 在极少 cluster 数下 F-stat 数值爆炸 (−5.75e+16)
2. **NEW-LINEAR-02:** Noconstant 模型未计算 F-stat（返回 null）
3. **NEW-LINEAR-03:** `regress()` wrapper 返回 `ResultSchema`，未暴露 `predict()` 接口

---

## 5. 证据文件清单

| 文件 | 说明 |
|------|------|
| `stata/output/phase2/stata_linear_basic.log` | Stata basic OLS 输出 |
| `stata/output/phase2/stata_linear_robust.log` | Stata robust VCE 输出 |
| `stata/output/phase2/stata_linear_cluster.log` | Stata cluster VCE 输出 |
| `stata/output/phase2/stata_linear_aweight.log` | Stata aweight 输出 |
| `stata/output/phase2/stata_linear_noconstant.log` | Stata noconstant 输出 |
| `stata/output/phase2/stata_linear_factor.log` | Stata factor variables 输出 |
| `stata/output/phase2/stata_linear_predict.log` | Stata predict 输出 |
| `stata/output/phase2/python_results.json` | Python 全量结果 JSON |
| `stata/output/phase2/python_predict_results.json` | Python predict 结果 JSON |
| `stata/output/phase2/val_linear_*.do` | 原始 .do 文件（未生成 log，改用 runner） |

---

## 6. 结论与建议

- **高优先级修复:** LINEAR-01（collinearity bug）影响所有 estimator，需在 `_vce_utils.py` 中修正 QR 逻辑
- **中优先级修复:** NEW-LINEAR-01（cluster F-stat 数值稳定性）、NEW-LINEAR-02（noconstant F-stat）
- **低优先级改进:** NEW-LINEAR-03（wrapper 暴露 predict 接口）、LINEAR-03（vce 语法兼容）
- **无需修复:** LINEAR-05 为按设计行为
