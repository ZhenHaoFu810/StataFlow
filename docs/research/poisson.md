# `poisson` 研究档案

## 命令定位

- 命令族：`Binary / Count`
- 类型：Stata 官方命令
- 规则来源：官方手册 + `e()` 返回值 + 双跑验证
- 手册入口：`help poisson`

## 版本与许可证

- **Stata 官方命令**，随 Stata 17 分发
- 无外部依赖

## 核心算法路径

### MLE 目标函数

对于计数响应 `y_i ∈ {0, 1, 2, ...}` 与线性预测 `η_i = x_i'β`：

```
ll(β) = Σ_i [ y_i * η_i - exp(η_i) - log(y_i!) ]
```

均值 `μ_i = exp(η_i)`。

### 估计路径

Stata `poisson` 默认使用 **Newton-Raphson / IRLS**（Fisher scoring）路径：

1. 初始化 `β = 0`（`μ = 1`）
2. 计算 `μ = exp(Xβ)`
3. 计算 working response `z = Xβ + (y - μ) / μ`
4. 计算权重 `w = μ`
5. 加权最小二乘更新：`β_new = (X'WX)^{-1} X'Wz`
6. 重复直至收敛

等价地，Fisher scoring 更新：

```
β_new = β + (X'WX)^{-1} X'(y - μ)
```

其中 `W = diag(μ_i)`。

**收敛标准**：与 `logit` / `probit` 一致。Python 实现建议：
- 对数似然绝对变化 `< 1e-7`
- 或相对变化 `< 1e-8`
- 最大迭代次数默认 100

### 协方差矩阵

#### `vce(ols)`（同方差 / MLE 默认）

使用期望信息矩阵的逆：

```
V = (X'WX)^{-1}
```

其中 `W = diag(μ_i)`。在泊松模型中，这也等于 Poisson 方差假设下的协方差。

#### `vce(robust)`（Wave 3 建议支持）

三明治估计量（Huber-White / 准最大似然）：

```
V = (X'WX)^{-1} * (Σ_i g_i g_i') * (X'WX)^{-1}
```

其中得分向量 `g_i = x_i * (y_i - μ_i)`。

#### `vce(cluster clustervar)`（Wave 3 最小实现纳入）

聚类稳健三明治：

```
V = (X'WX)^{-1} * (Σ_g u_g u_g') * (X'WX)^{-1}
```

其中 `u_g = Σ_{i∈g} x_i (y_i - μ_i)`。

小样本修正：
- `n_adj = n / (n - 1)` 若 `n > 1`
- `g_adj = G / (G - 1)` 若 `G > 1`
- `k = K`（参数个数）

## 结果字段与对齐优先级

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(df_m)` | 模型自由度 | 高 |
| `e(ll)` | 对数似然 | 高 |
| `e(deviance)` | 偏差（deviance） | 高 |
| `e(chi2)` | LR chi²（vs 空模型） | 高 |
| `e(b)` / `e(V)` | 系数与协方差 | 高 |
| `e(dispers)` | 离散参数（Poisson 固定为 1） | 中 |
| `e(converged)` | 是否收敛 | 中 |

**Deviance**：

```
D = 2 * Σ_i [ y_i * log(y_i / μ_i) - (y_i - μ_i) ]
```

当 `y_i = 0` 时，项 `y_i * log(y_i / μ_i)` 取 0（极限意义）。

**LR chi²**：`chi2 = 2 * (ll_model - ll_null)`，其中 `ll_null = Σ_i [y_i * log(ȳ) - ȳ - log(y_i!)]`，`ȳ = mean(y)`。

**Pseudo R²**：Stata `poisson` 不默认报告 Pseudo R²，但部分版本支持 `e(r2_p)`。Wave 3 最小实现可不强制对齐 Pseudo R²，优先保证 `ll`、`deviance`、`chi2`。

## 最小兼容子集（Wave 3 Stage A）

### 必须支持
- `Poisson(data, y, x, add_constant=True)`
- `fit(vce="ols")`
- `fit(vce="cluster", cluster="...")`
- 输出字段：`nobs`、`df_model`、`ll`、`deviance`、`chi2`、`系数`、`标准误`

### 建议支持
- `fit(vce="robust")`

### 暂不支持
- `offset()` / `exposure()`
- `constraints`
- `irr`（incidence rate ratio 报告格式）
- `nbreg`（负二项，属于不同命令）

## Synthetic 样例设计

### `w3_poisson_basic`
- **数据集**：手工生成计数响应数据（已知系数，中等样本，含零值）
- **Stata 命令**：`poisson y x1 x2`
- **Python API**：`Poisson(data, y="y", x=["x1", "x2"]).fit()`
- **风险焦点**：MLE 收敛性、系数、标准误、ll、deviance、chi2 对齐

### `w3_poisson_cluster`
- **数据集**：手工 panel 数据（带 firm/cluster）
- **Stata 命令**：`poisson y x1 x2, vce(cluster firm)`
- **风险焦点**：cluster-robust SE 小样本修正、cluster_count

## Real-Data 样例设计

### `w3_poisson_real`
- **数据集**：`randhie`（RAND Health Insurance Experiment，Wooldridge / RDatasets）
- **本地路径**：`research/data/public/count/randhie.csv`
- **Stata 命令**：`poisson mdvis lncoins ndisease female age lfam children`
- **Python API**：`Poisson(data, y="mdvis", x=["lncoins", "ndisease", "female", "age", "lfam", "children"]).fit()`
- **风险焦点**：真实计数数据下的系数、标准误、ll、deviance、chi2 精确对齐

## 与 `ppmlhdfe` 的关系

`ppmlhdfe` = Poisson PML + HDFE 吸收。在 Phase A：
1. 先实现纯 `poisson`（`Poisson` 类）
2. 再在 `AbsorbingOLS` / LSDV 框架上扩展 `PPMLHDFE`：
   - 使用 IRLS 迭代，每一步将当前 working response 对 `X + FE dummies` 做加权 OLS
   - 或在残差化空间使用迭代加权最小二乘（IRWLS）
   - 等价于对泊松对数似然做 Newton-Raphson，其中 Hessian = `X'WX`

这一路径与 `ppmlhdfe` 的核心算法（IRLS + FE partialling out）在数学上等价。
