# `logit` 研究档案

## 命令定位

- 命令族：`Binary / Count`
- 类型：Stata 官方命令
- 规则来源：官方手册 + `e()` 返回值 + 双跑验证
- 手册入口：`help logit`

## 版本与许可证

- **Stata 官方命令**，随 Stata 17 分发
- 无外部依赖

## 核心算法路径

### MLE 目标函数

对于二元响应 `y_i ∈ {0, 1}` 与线性预测 `η_i = x_i'β`：

```
L(β) = Σ_i [ y_i * Λ(η_i) + (1 - y_i) * (1 - Λ(η_i)) ]
```

其中 `Λ(η) = 1 / (1 + exp(-η))` 为 logistic CDF。

对数似然：

```
ll(β) = Σ_i [ y_i * log(Λ(η_i)) + (1 - y_i) * log(1 - Λ(η_i)) ]
      = Σ_i [ y_i * η_i - log(1 + exp(η_i)) ]
```

### 估计路径

Stata `logit` 默认使用 **Newton-Raphson / IRLS** 混合路径：

1. 初始化 `β = 0`（或从 `probit` 缩放转换得到初值）
2. 计算当前拟合概率 `p = Λ(Xβ)`
3. 计算 working response `z = Xβ + (y - p) / (p * (1 - p))`
4. 计算权重 `w = p * (1 - p)`
5. 加权最小二乘更新：`β_new = (X'WX)^{-1} X'Wz`
6. 重复直至收敛

**收敛标准**：Stata 默认使用对数似然相对变化 `|ll_new - ll_old| / (|ll_old| + 1) < tol`，默认 `tol = 1e-6`；同时检查参数变化。为与 Stata 对齐，Python 实现可采用双重收敛判据：
- 对数似然绝对变化 `< 1e-7`
- 或相对变化 `< 1e-8`
- 最大迭代次数默认 100

### 协方差矩阵

#### `vce(ols)`（同方差 / MLE 默认）

使用期望信息矩阵（Fisher information）的逆：

```
V = (X'WX)^{-1}
```

其中 `W = diag(p_i * (1 - p_i))`。Stata `logit` 默认报告此矩阵（即逆 Hessian）。

#### `vce(robust)`（Wave 3 建议支持）

三明治估计量（Huber-White）：

```
V = (X'WX)^{-1} * (Σ_i g_i g_i') * (X'WX)^{-1}
```

其中得分向量 `g_i = x_i * (y_i - p_i)`。

#### `vce(cluster clustervar)`（Wave 3 建议支持）

聚类稳健三明治：

```
V = (X'WX)^{-1} * (Σ_g u_g u_g') * (X'WX)^{-1}
```

其中 `u_g = Σ_{i∈g} x_i (y_i - p_i)`。

小样本修正：
- `n_adj = n / (n - 1)` 若 `n > 1`
- `g_adj = G / (G - 1)` 若 `G > 1`
- `k` 在 Stata `logit` 的 cluster 修正中通常等于参数个数 `K`

## 结果字段与对齐优先级

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(df_m)` | 模型自由度（斜率参数数） | 高 |
| `e(ll)` | 对数似然 | 高 |
| `e(r2_p)` | McFadden Pseudo R² | 高 |
| `e(chi2)` | LR chi²（vs 空模型） | 高 |
| `e(b)` / `e(V)` | 系数与协方差 | 高 |
| `e(converged)` | 是否收敛 | 中 |

**Pseudo R²**：Stata 使用 McFadden：`1 - ll_model / ll_null`，其中 `ll_null = n0*log(n0/n) + n1*log(n1/n)`。

**LR chi²**：`chi2 = 2 * (ll_model - ll_null)`，自由度 `df_m`。

**注意**：`logit` 不报告 `e(r2)` 或 `e(rmse)`；`f_stat` 被替换为 `chi2`（LR 检验）。

## 最小兼容子集（Wave 3 Stage A）

### 必须支持
- `Logit(data, y, x, add_constant=True)`
- `fit(vce="ols")`
- 输出字段：`nobs`、`df_model`、`ll`、`pseudo_r2`、`chi2`、`系数`、`标准误`

### 建议支持
- `fit(vce="robust")`
- `fit(vce="cluster", cluster="...")`

### 暂不支持
- `or`（odds ratio 报告格式，可通过 `exp(beta)` 后处理）
- `offset()` / `exposure()`
- `constraints`
- `asis`（完全分离处理）

## Synthetic 样例设计

### `w3_logit_basic`
- **数据集**：手工生成二元响应数据（已知系数，中等样本）
- **Stata 命令**：`logit y x1 x2`
- **Python API**：`Logit(data, y="y", x=["x1", "x2"]).fit()`
- **风险焦点**：MLE 收敛性、系数、标准误、ll、pseudo-R²、chi2 对齐

## Real-Data 样例设计

### `w3_logit_real`
- **数据集**：`Mroz` 劳动参与数据（Wooldridge）
- **本地路径**：`research/data/public/binary/mroz.csv`
- **Stata 命令**：`logit inlf nwifeinc educ exper expersq age kidslt6 kidsge6`
- **Python API**：`Logit(data, y="inlf", x=["nwifeinc", "educ", "exper", "expersq", "age", "kidslt6", "kidsge6"]).fit()`
- **风险焦点**：真实二元响应数据下的系数、标准误、ll、pseudo-R²、chi2 精确对齐

## 与现有代码的复用关系

| 现有组件 | 复用方式 |
|---------|---------|
| `ResultSchema` | 复用；在 `FitInfo` 中通过 `f_stat` 承载 `chi2`，需在研究档案中明确 |
| `OLS._prepare_data()` | 复用样本筛选、缺失值剔除、常数项注入、共线性检测 |
| `AbsorbingOLS._prepare_data()` | 未来 `ppmlhdfe` 阶段复用 FE 吸收逻辑 |
