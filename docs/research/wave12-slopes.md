# Wave 12 Research: Individual Slope Absorption `absorb(var##c.slope)`

**日期：** 2026-04-30
**主题：** 个体斜率吸收（heterogeneous slopes）的数学对象与实现路径
**来源：** reghdfe `explanation.tex` Section 6 + `reghdfe.sthlp` + ppmlhdfe `slopes1.do`

---

## 1. 语法定义

Stata `reghdfe` 支持两种斜率吸收语法：

| 语法 | 数学对象 | 示例 |
|------|----------|------|
| `absorb(firm_id##c.time_trend)` | 异质性截距 + 异质性斜率 | 每个 firm 有自己的截距和 time_trend 系数 |
| `absorb(firm_id#c.time_trend)` | 仅异质性斜率（无截距） | 每个 firm 有自己的 time_trend 系数，但共享全局截距 |

**警告：** `reghdfe` 文档明确指出，纯斜率吸收（`#` 而非 `##`）数值稳定性差、收敛慢。推荐始终使用 `##`（截距+斜率），即使截距是冗余的。

## 2. 数学原理

### 2.1 从截距到斜率

标准 FE 吸收：`Dα`，其中 `D` 是 `N × G` 虚拟变量矩阵，`D[i,g] = 1` 当且仅当观测 `i` 属于组 `g`。

斜率 FE 吸收：`D .* V` 的列乘以斜率系数，其中 `.*` 是 element-wise 乘积，`V` 是连续变量。

对于单组斜率，投影算子 `P_g` 不再是简单的组内均值，而是**组内加权均值**：

```
P_g(y) = v_i × q_g(i)
```

其中 `q_g = (Σ_{i∈g} v_i × y_i) / (Σ_{i∈g} v_i²)`

### 2.2 多组斜率的设计矩阵视角

如果 `D` 有 `G` 个组（`N × G` 矩阵），则 `P_D` 可以写成分块对角矩阵：

```
P_D = diag(P_1, P_2, ..., P_G)
```

其中每个 `P_j` 是组 `j` 内的投影矩阵。对于组 `j` 内的 `n_j` 个观测：

```
P_j = V_j V_j' / (V_j' V_j)
```

这里 `V_j` 是组 `j` 内连续变量的向量。

### 2.3 与截距吸收的等价性

当 `v_i = 1` 对所有 `i` 时：
- `q_g = (Σ_{i∈g} y_i) / (Σ_{i∈g} 1) = mean(y | g)`
- `P_g(y) = 1 × mean(y | g)`，即标准组内均值

因此，**截距吸收是斜率吸收的特例**（连续变量恒为1）。

## 3. 实现细节

### 3.1 核心操作：组内加权均值

对于每组 `g`，需要计算：
1. 分子：`sum(v * y for i in g)`
2. 分母：`sum(v^2 for i in g)`
3. 组内预测值：`v_i * (numerator / denominator)`

这与标准组内均值的区别仅在于：
- 标准：`sum(y) / count`
- 斜率：`sum(v*y) / sum(v^2)`

### 3.2 与 MAP 迭代的集成

reghdfe 的 `explanation.tex` Section 6 说明：

> "In terms of code, before we obtained a Q matrix where v_i=1, so we were basically computing group means... and now we are i) weighting them and ii) multiplying by v_i afterwards."

即：MAP 迭代框架**不需要改变**，只需要替换 `panelmean()` 的实现：
- 截距：`panelmean(y, 1)` → 组内简单均值
- 斜率：`panelmean(y, v)` → 组内加权均值（以 `v` 为权重）

### 3.3 多斜率同时吸收

`reghdfe` 支持 `absorb(firm_id##c.(x1 x2))`，即同一组变量下多个连续变量的异质性斜率。

实现上，这等价于扩展设计矩阵：
```
absorb(firm_id##c.x1)  →  [D, D.*X1]
absorb(firm_id##c.(x1 x2)) → [D, D.*X1, D.*X2]
```

每组 `g` 的投影算子变为分块对角矩阵，每块大小为 `n_j × (1 + num_slopes)`。

## 4. Python 伪代码

```python
def panelmean_weighted(y, weights, levels, num_levels):
    """
    Compute weighted group means: q[g] = sum(w * y) / sum(w^2)
    Then return v_i * q[level[i]] for each observation.
    """
    # Numerator: sum of w * y per group
    numerator = np.bincount(levels, weights=weights * y, minlength=num_levels)
    # Denominator: sum of w^2 per group
    denominator = np.bincount(levels, weights=weights ** 2, minlength=num_levels)
    # Avoid division by zero
    q = np.zeros(num_levels)
    mask = denominator > 0
    q[mask] = numerator[mask] / denominator[mask]
    return weights * q[levels]


def partial_out_with_slopes(y, factors):
    """
    factors: list of dicts, each with:
        - levels: group assignment array
        - num_levels: number of groups
        - slopes: list of continuous variables for slopes (empty = intercept only)
    """
    # Same MAP iteration as intercept-only, but use panelmean_weighted
    # when slopes are present
    ...
```

## 5. 与当前 `AbsorbingOLS` 的集成方案

### 5.1 设计矩阵扩展

当前 `AbsorbingOLS._prepare_data` 构造：
```python
X_full = np.column_stack([X, D1, D2, ...])
```

斜率吸收需要将 `D1` 替换为 `[D1, D1.*S1, D1.*S2, ...]`。

但在迭代 MAP 框架下，**不需要显式构造这些矩阵**。只需要：
1. 解析 `absorb` 字符串，识别 `var##c.slope` 模式
2. 为每个 FE 组存储其截距/斜率变量列表
3. 在 MAP 迭代中使用 `panelmean_weighted` 替代简单均值

### 5.2 API 兼容性

Wrapper 层 `reghdfe(..., absorb="firm_id##c.time_trend")` 需要：
1. 解析 `##c.` 语法，提取连续变量名
2. 传递给 `AbsorbingOLS` 的 `absorb` 参数（当前是字符串列表，需扩展为结构化对象）

**注意：** 这会轻微改变 `AbsorbingOLS` 的 `absorb` 参数类型（从 `List[str]` 到 `List[AbsorbSpec]`），需要评估是否属于公共 API 变更。

## 6. 测试策略

### 6.1 Synthetic 验证

生成数据：`y = 0.5*x + firm_fe + firm_slope*time + eps`

其中 `firm_fe ~ N(0,1)`，`firm_slope ~ N(0, 0.1)`。

比较：
1. Python MAP + 斜率 的 `β_x`
2. Stata `reghdfe y x, absorb(firm_id##c.time)` 的 `_b[x]`
3. 期望：相对误差 `< 1e-6`

### 6.2 边界情况

1. **某组内 slope 变量全为0**：分母为0，斜率未定义 → 该组斜率系数设为0
2. **某组内 slope 变量为常数**：与截距共线 → `reghdfe` 会自动检测并处理
3. **多 slope 变量**：`absorb(firm_id##c.(x1 x2 x3))`

## 7. 参考文献

1. Correia (2016), `explanation.tex` Section 6: "Extension: Interactions between FEs and continuous variables"
2. reghdfe help file: `absorb(varname##c.varname)` 语法说明
3. ppmlhdfe `slopes1.do`：斜率吸收基准测试
