# NEW-LINEAR — Phase 2 新发现问题

**验证日期:** 2026-06-03  
**数据集:** Card (N=3,010)  
**Stata 版本:** 17.0 MP  

---

## NEW-LINEAR-01: Cluster VCE 在极少 cluster 数下 F-stat 数值爆炸

**现象:**  
当 `cluster='south'`（仅 2 个取值）时，Python 返回 `f_stat = -5.750948797240051e+16`，`f_pvalue = 1.0`；Stata 显示 `F(0, 1) = .`（missing）。

**根因:**  
`OLS.fit()` 中 cluster VCE 的 Wald F 计算（ols.py:440-460）使用 `np.linalg.inv(cov_slopes)`。当 cluster 数极少时，斜率协方差矩阵接近奇异，`np.linalg.inv` 未抛出异常而是返回一个病态的逆矩阵，导致 Wald stat 为巨大的负数。

**建议修复:**  
在求逆前检查条件数，或使用 `np.linalg.lstsq` / `np.linalg.pinv` 处理奇异矩阵。若矩阵奇异，F-stat 应设为 `None`（与 Stata 的 missing 行为一致）。

```python
# 建议修复片段
try:
    cov_inv = np.linalg.inv(cov_slopes)
except np.linalg.LinAlgError:
    f_stat = None
    f_pvalue = None
else:
    # 额外检查数值稳定性
    if not np.all(np.isfinite(cov_inv)):
        f_stat = None
        f_pvalue = None
    else:
        wald_stat = float(beta_slopes @ cov_inv @ beta_slopes)
        ...
```

**优先级:** 高（影响统计推断可靠性）

---

## NEW-LINEAR-02: Noconstant 模型未计算 F-stat

**现象:**  
`regress(..., noconstant=True)` 时 `fit.f_stat` 返回 `null`；Stata 返回 `F(5, 3005) = 61604.34`。

**根因:**  
`OLS.fit()` 第 406 行：`if self.add_constant and df_model > 0:`。当 `noconstant=True` 时，`add_constant=False`，整个 F-stat 计算块被跳过。

**建议修复:**  
`noconstant` 下仍应计算 Wald F-stat（检验所有系数联合显著性），只是不使用 `const_idx` 排除常数项的逻辑。

```python
# 建议修复
if df_model > 0:
    # 不检查 add_constant，始终计算 F-stat
    if self.add_constant:
        const_idx = self._coef_names.index("_cons") if "_cons" in self._coef_names else -1
        slope_idx = [i for i in range(k) if i != const_idx] if const_idx >= 0 else list(range(k))
    else:
        slope_idx = list(range(k))
    # ... 后续 Wald F 计算不变
```

**优先级:** 中

---

## NEW-LINEAR-03: `regress()` wrapper 返回 ResultSchema，未暴露 predict 接口

**现象:**  
用户调用 `result = regress(...)` 后无法执行 `result.predict(type='xb')`，因为 `regress()` 返回的是 `ResultSchema` 对象，而 `predict()` 定义在 `OLS` 类上。

**根因:**  
`compat/stata/linear.py:48` 返回 `model.fit(vce=vce, cluster=cluster)`，即 `ResultSchema`。wrapper 未返回底层模型实例。

**建议修复:**  
两种方案：
1. 在 `ResultSchema` 中保存模型引用，并委托 `predict` 调用；
2. 返回一个增强的 result 对象（如 `SimpleNamespace` 或自定义类），同时暴露 result 字段和 predict 方法。

方案 1 示例：
```python
# result.py 中 ResultSchema 增加
class ResultSchema:
    ...
    _model: Optional[Any] = None

    def predict(self, type: str = "xb", newdata=None):
        if self._model is None:
            raise ValueError("predict not available for this result")
        return self._model.predict(type=type, newdata=newdata)
```

然后在 `OLS.fit()` 中设置 `result._model = self`。

**优先级:** 低（不影响统计结果，影响 API 易用性）

---

## NEW-LINEAR-04: `compute_multiway_cluster_vce` 仍使用字符串拼接 `__` 分隔符

**现象:**  
虽然 `OLS.fit()` 已修复 LINEAR-02（使用 tuple-based 编码），但共享函数 `compute_multiway_cluster_vce`（`_vce_utils.py:107`）仍使用 `f"{a}__{b}"` 字符串拼接生成交互 cluster ID。

**根因:**  
`_vce_utils.py:106-108`:
```python
interaction = np.array([
    f"{a}__{b}" for a, b in zip(cluster_arrs[0], cluster_arrs[1])
])
```

若 cluster 值本身包含 `__` 子串，会产生错误的交互分组。

**建议修复:**  
将 `compute_multiway_cluster_vce` 中的字符串拼接改为与 `OLS.fit()` 一致的 tuple-based 编码，或使用整数映射（如 `ols.py:364-368` 的做法）。

```python
# 建议修复
c1, c2 = cluster_arrs[0], cluster_arrs[1]
combo_to_id = {}
combo_ids = np.empty(len(c1), dtype=int)
for i, pair in enumerate(zip(c1, c2)):
    if pair not in combo_to_id:
        combo_to_id[pair] = len(combo_to_id)
    combo_ids[i] = combo_to_id[pair]
meat_12, G_12 = compute_cluster_meat(X, residuals, combo_ids)
```

**优先级:** 中（影响 reghdfe / ivreghdfe / ppmlhdfe 的 2-way cluster 正确性）
