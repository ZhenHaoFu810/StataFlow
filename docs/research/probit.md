# `probit` 研究档案

## 命令定位

- 命令族：`Binary / Count`
- 类型：Stata 官方命令
- 规则来源：官方手册 + `e()` 返回值 + 双跑验证
- 手册入口：`help probit`

## 版本与许可证

- **Stata 官方命令**，随 Stata 17 分发
- 无外部依赖

## 核心算法路径

### MLE 目标函数

对于二元响应 `y_i ∈ {0, 1}` 与线性预测 `η_i = x_i'β`：

```
ll(β) = Σ_i [ y_i * log(Φ(η_i)) + (1 - y_i) * log(1 - Φ(η_i)) ]
```

其中 `Φ(η)` 为标准正态 CDF，`φ(η)` 为标准正态 PDF。

### 估计路径

Stata `probit` 默认使用 **Newton-Raphson / IRLS**（Fisher scoring）路径：

1. 初始化 `β = 0`
2. 计算 `p = Φ(Xβ)`，`λ = φ(Xβ) / (p * (1 - p))`（inverse Mills ratio 相关项）
3. 计算 working response `z = Xβ + (y - p) / φ(Xβ)`
4. 计算权重 `w = φ(Xβ)^2 / (p * (1 - p))`
5. 加权最小二乘更新：`β_new = (X'WX)^{-1} X'Wz`
6. 重复直至收敛

等价地，可通过 Fisher scoring 更新：

```
β_new = β + (X'WX)^{-1} X'(y - p)
```

其中 `W = diag(φ_i^2 / (p_i * (1 - p_i)))`。

**收敛标准**：与 `logit` 一致，Stata 默认使用对数似然相对变化。Python 实现建议：
- 对数似然绝对变化 `< 1e-7`
- 或相对变化 `< 1e-8`
- 最大迭代次数默认 100

### 协方差矩阵

#### `vce(ols)`（同方差 / MLE 默认）

使用期望信息矩阵的逆：

```
V = (X'WX)^{-1}
```

其中 `W = diag(φ_i^2 / (p_i * (1 - p_i)))`。

#### `vce(robust)`（Wave 3 建议支持）

三明治估计量：

```
V = (X'WX)^{-1} * (Σ_i g_i g_i') * (X'WX)^{-1}
```

其中得分向量 `g_i = x_i * (y_i - p_i) * φ_i / (p_i * (1 - p_i))`（等价于 `X'W(z - Xβ)` 的个体贡献）。

更简洁的表达：使用观测得分 `g_i = x_i * ∂ll_i/∂β = x_i * (y_i - p_i) * φ_i / (p_i * (1 - p_i))`。

#### `vce(cluster clustervar)`（Wave 3 建议支持）

聚类稳健三明治：

```
V = (X'WX)^{-1} * (Σ_g u_g u_g') * (X'WX)^{-1}
```

其中 `u_g = Σ_{i∈g} x_i (y_i - p_i) * φ_i / (p_i * (1 - p_i))`。

小样本修正与 `logit` 一致：
- `n_adj = n / (n - 1)`
- `g_adj = G / (G - 1)`
- `k = K`

## 结果字段与对齐优先级

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(df_m)` | 模型自由度 | 高 |
| `e(ll)` | 对数似然 | 高 |
| `e(r2_p)` | McFadden Pseudo R² | 高 |
| `e(chi2)` | LR chi²（vs 空模型） | 高 |
| `e(b)` / `e(V)` | 系数与协方差 | 高 |
| `e(converged)` | 是否收敛 | 中 |

**Pseudo R²**：与 `logit` 相同，`1 - ll_model / ll_null`，`ll_null = n0*log(n0/n) + n1*log(n1/n)`。

**LR chi²**：`chi2 = 2 * (ll_model - ll_null)`，自由度 `df_m`。

## 最小兼容子集（Wave 3 Stage A）

### 必须支持
- `Probit(data, y, x, add_constant=True)`
- `fit(vce="ols")`
- 输出字段：`nobs`、`df_model`、`ll`、`pseudo_r2`、`chi2`、`系数`、`标准误`

### 建议支持
- `fit(vce="robust")`
- `fit(vce="cluster", cluster="...")`

### 暂不支持
- `offset()` / `exposure()`
- `constraints`
- `asis`（完全分离处理）
- 边际效应（`margins` 子集，属 Wave 5）

## Synthetic 样例设计

### `w3_probit_basic`
- **数据集**：手工生成二元响应数据（与 `w3_logit_basic` 共用设计矩阵，仅改变 DGP）
- **Stata 命令**：`probit y x1 x2`
- **Python API**：`Probit(data, y="y", x=["x1", "x2"]).fit()`
- **风险焦点**：MLE 收敛性、系数、标准误、ll、pseudo-R²、chi2 对齐

## Real-Data 样例设计

### `w3_probit_real`
- **数据集**：`Mroz` 劳动参与数据（Wooldridge）
- **本地路径**：`research/data/public/binary/mroz.csv`
- **Stata 命令**：`probit inlf nwifeinc educ exper expersq age kidslt6 kidsge6`
- **Python API**：`Probit(data, y="inlf", x=["nwifeinc", "educ", "exper", "expersq", "age", "kidslt6", "kidsge6"]).fit()`
- **风险焦点**：真实数据下 probit 系数、标准误、ll、pseudo-R²、chi2 精确对齐

## 与 `logit` 的代码复用

`probit` 与 `logit` 的算法结构几乎完全一致，唯一区别在于：
- 链接函数：`logit` 用 `Λ(η)`，`probit` 用 `Φ(η)`
- 权重：`logit` 用 `p*(1-p)`，`probit` 用 `φ^2/(p*(1-p))`
- 得分向量表达式相应调整

建议在实现时提取公共的 `GLMBinary` 基类，仅覆盖链接函数与导数方法。
