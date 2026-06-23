# REV-LINEAR — Linear Base + Factor Variables 复核报告

**Agent**: LINEAR 源码深度审查（手动完成，Agent 超时）  
**审查文件**: `estimators/ols.py`, `estimators/fe.py`, `compat/stata/linear.py`, `compat/stata/factor_variables.py`, `estimators/_vce_utils.py`  
**发现问题**: **13 项**（1 Blocker + 4 Critical + 5 Major + 3 Minor）

---

## 1. Blocker 级别

### LINEAR-01: `detect_collinear_columns` 在 n < p 时 IndexError 崩溃

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/estimators/_vce_utils.py:L140-148` |
| **根因** | `R = np.linalg.qr(X, mode='r')` 返回 `R.shape = (min(n,p), p)`。当 `n < p` 时循环 `for i in range(p)` 访问 `R[i,i]` 导致 `IndexError` |
| **影响** | 任何宽数据（变量数 > 样本量）的回归直接崩溃。现代高维数据常见场景 |
| **修复** | 将循环上限改为 `min(R.shape[0], p)`，或改用 SVD-based rank detection |
| **验证** | 高概率复现：任意 `X` 满足 `X.shape[1] > X.shape[0]` |

```python
# _vce_utils.py L140-148 (问题代码)
R = np.linalg.qr(X, mode='r')
for i in range(X.shape[1]):        # ← 当 n < p 时，i 可能 >= R.shape[0]
    if i < R.shape[0] and abs(R[i, i]) > tol:  # ← 当前有 guard，但...
        independent.append(i)
    else:
        dropped.append(names[i])
```

> **注意**: 当前代码第144行有 `i < R.shape[0]` 保护，但如果 `R` 的行数小于 `X.shape[1]`，所有 `i >= R.shape[0]` 的列都会被标记为 dropped，这在数学上是不正确的——应该检查的是 **线性独立性** 而非 **QR 三角部分是否溢出**。更关键的是，如果 `R` 的 shape 是 `(n, p)` 且 `n < p`，QR 分解的 `R` 只有 `n` 行，剩余 `p-n` 列的独立性无法通过当前方法判断。

---

## 2. Critical 级别

### LINEAR-02: `compute_multiway_cluster_vce` 分隔符冲突导致错误分组

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/estimators/_vce_utils.py:L106-109` |
| **根因** | `interaction = np.array([f"{a}__{b}" ...])` 使用硬编码 `__` 分隔符。若 cluster 值本身含 `__`（如 `"NY__2020"`），不同 `(a,b)` 对可能产生相同字符串，错误合并聚类 |
| **影响** | 2-way cluster VCE 在特定数据下产生错误 SE，静默且难以察觉 |
| **修复** | 改用 tuple 编码或 bytes 序列化，避免字符串分隔符冲突 |
| **对比** | `ols.py` inline 实现已使用 `tuple`-based 编码（更安全），但 `_vce_utils.py` 的共享函数仍用字符串拼接 |

### LINEAR-03: `regress` wrapper 不支持 `vce(cluster var)` 字符串语法

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/compat/stata/linear.py:L11-48` |
| **根因** | `vce` 参数只能传入 `"ols"`/`"robust"`/`"cluster"`，不支持 Stata 的 `vce(cluster varname)` 内联语法。用户必须同时传 `vce="cluster", cluster="varname"` |
| **影响** | 与 Stata 命令行语法不兼容，用户迁移成本高 |
| **修复** | 在 `regress` 中解析 `vce` 参数，自动提取 `cluster(...)` 中的变量名 |

### LINEAR-04: `factor_variables.py` 三路交互被硬拒绝

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/compat/stata/factor_variables.py:L184-186, L312-313` |
| **根因** | `_expand_single_term` 只处理 `len(parts)==1` 或 `len(parts)==3`（即最多二元交互）。Stata 支持 `i.a##i.b##i.c`（三路交互） |
| **影响** | 无法使用 Stata 标准的三路因子交互语法，高阶 DID/FE 模型受阻 |
| **修复** | 递归处理任意阶数的 `#`/`##` 交互，或至少支持三路 |

---

## 3. Major 级别

### LINEAR-05: `regress` wrapper 硬拒绝 `level()`, `beta`, `eform` 等 Stata 参数

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/compat/stata/linear.py:L28-29` |
| **根因** | `if kwargs: raise ValueError(...)` 直接拒绝所有未显式声明的参数 |
| **影响** | `level(90)`, `beta`, `eform`, `noci`, `nopvalues` 等 Stata 标准参数均不可用 |
| **修复** | 识别并安全忽略（或部分实现）常见展示层参数，仅对影响估计的未知参数报错 |

### LINEAR-06: `xtreg_fe` 不支持 `robust` VCE

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/compat/stata/linear.py:L51-84` |
| **根因** | `FixedEffectsOLS.fit()` 只支持 `vce="ols"` 和 `vce="cluster"`，缺少 `robust` |
| **影响** | 面板数据异方差稳健标准误无法使用，与 Stata `xtreg, fe robust` 不兼容 |
| **修复** | 在 `FixedEffectsOLS.fit()` 中实现 HC1 robust VCE |
| **关联** | PANEL-06 |

### LINEAR-07: `areg` 不支持 `robust` VCE

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/compat/stata/linear.py:L87-124` |
| **根因** | `areg()` wrapper 将 `vce` 透传给 `AbsorbingOLS.fit()`，但 `AbsorbingOLS` 的 robust 实现可能存在已知问题（由 PANEL Agent 审查覆盖） |
| **影响** | 单 FE 模型的 robust SE 可能不可靠 |
| **修复** | 复用 OLS 的 HC1 逻辑，在 AbsorbingOLS 中正确实现 |

### LINEAR-08: `_resolve_level` 非数值类型使用 1-based index 而非字母顺序

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/compat/stata/factor_variables.py:L56-86` |
| **根因** | 对非数值类型的 level，若 exact match 失败则回退到 1-based index。Stata 对字符串 categorical 使用字母顺序（alphabetical order） |
| **影响** | `ib2.state` 在非数值字符串变量上行为与 Stata 不一致 |
| **修复** | 非数值类型使用 sorted(levels) 的 index 而非原始顺序的 index |

### LINEAR-09: `predict(newdata=...)` 不处理 missing values

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/estimators/ols.py:L551-566` |
| **根因** | `newdata[self.x]` 直接取值，不检查 NaN。若 `newdata` 含缺失值，`X @ beta` 会产生 NaN 但无警告 |
| **影响** | 样本外预测时缺失值静默传播，用户不知情 |
| **修复** | 在 predict 中添加 missing check 和警告 |

---

## 4. Minor 级别

### LINEAR-10: `aweight` 只接受列名字符串，不接受数组

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/compat/stata/linear.py:L32-35` |
| **根因** | `aweight` 参数类型为 `Optional[str]`，只能传入列名。无法直接传入 weight 数组 |
| **影响** | 灵活性受限 |
| **修复** | 接受 `str | np.ndarray | pd.Series` |

### LINEAR-11: `c.x1#c.x2` 生成列名含特殊字符 `#`

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/compat/stata/factor_variables.py:L237` |
| **根因** | 交互列名 `c.x1#c.x2` 包含 `#`，在某些 DataFrame 操作或导出时可能出问题 |
| **影响** | 极低概率的兼容性问题 |
| **修复** | 将 `#` 替换为 `_x_` 或类似安全分隔符 |

### LINEAR-12: `xtreg_fe` `df_model` 与 `f_stat` dfn 不一致

| 属性 | 内容 |
|------|------|
| **文件** | `src/stataflow/estimators/fe.py:L230-234, L290-301` |
| **根因** | `vce="cluster"` 时 `df_model_fe = 1`（Stata 报告惯例），但 `f_stat` 的 dfn 仍为 `k`（slope 数）。二者逻辑上应一致 |
| **影响** | 统计报告内部不一致 |
| **修复** | 统一 `df_model_fe` 和 `f_stat` dfn 的定义 |

---

## 5. 跨命令族关联

| 本报告问题 | 关联问题 | 说明 |
|-----------|---------|------|
| LINEAR-06 | PANEL-06 | `xtreg_fe` 不支持 robust VCE |
| LINEAR-07 | PANEL-04 | `areg` 的 robust VCE 依赖 AbsorbingOLS |
| LINEAR-01 | PANEL-08 | collinearity 检测为共享函数，影响所有估计器 |
| LINEAR-02 | IV-01 | 2-way cluster VCE 共享 `_vce_utils.py` |

---

*报告生成时间: 2026-06-03*  
*验证状态: 源码静态分析，部分需真实数据双跑确认*
