# `ivregress 2sls` 研究档案

## 命令定位

- 命令族：`IV / GMM`
- 类型：Stata 官方命令
- 规则来源：官方手册 + `e()` 返回值 + 双跑验证
- 手册入口：`help ivregress`

## 版本与许可证

- **Stata 官方命令**，随 Stata 17 分发
- 无外部依赖

## 核心算法路径

### 2SLS 点估计

标准两阶段最小二乘法：

设：
- `y` = 被解释变量
- `X_endo` = 内生解释变量（`K1` 个）
- `X_exog` = 外生解释变量（`K2` 个，含常数项）
- `Z_excl` = 排他性工具变量（`L1` 个）
- `Z = [Z_excl, X_exog]` = 全部工具变量（`L = L1 + K2` 个）

**第一阶段**：对每个内生变量 `x_k` 做 OLS 回归：
```
x_k = Z * π_k + v_k
```
得到拟合值 `X̂_endo = Z * (Z'Z)^{-1} * Z' * X_endo`

**第二阶段**：用 `X̂_endo` 替换 `X_endo`，做 OLS：
```
y = [X̂_endo, X_exog] * β + ε
```

等价地，2SLS 估计量有闭式解：
```
β_2sls = (X' P_Z X)^{-1} X' P_Z y
```
其中 `P_Z = Z (Z'Z)^{-1} Z'` 为投影矩阵，`X = [X_endo, X_exog]`。

### 协方差矩阵

#### `vce(ols)`
同方差假设下：
```
V = σ² * (X' P_Z X)^{-1}
```
其中 `σ² = e'e / df_r`，`e = y - X β_2sls` 为结构残差（使用原始 `X`，非拟合值）。

#### `vce(robust)`（Wave 2 最小实现纳入）
HC1 型稳健协方差：
```
V = (X' P_Z X)^{-1} * (Σ_i e_i² * z_i z_i') * (X' P_Z X)^{-1}
```
或更标准的表达式：
```
V = (X' P_Z X)^{-1} * X' P_Z * Ω * P_Z X * (X' P_Z X)^{-1}
```
其中 `Ω = diag(e_i²)`。

#### `vce(cluster clustervar)`（Wave 2 最小实现纳入）
聚类稳健协方差：
```
V = (X' P_Z X)^{-1} * X' P_Z * (Σ_g e_g e_g') * P_Z X * (X' P_Z X)^{-1}
```
或等价地通过残差化形式构造 meat 矩阵：
```
S = Σ_g (X̃_g' e_g) (X̃_g' e_g)'
V = n/(n-k) * G/(G-1) * (X̃'X̃)^{-1} S (X̃'X̃)^{-1}
```
其中 `X̃ = P_Z X` 为第一阶段投影后的回归变量矩阵。

**小样本修正**：
- `n_adj = (n - 1) / (n - k)` 若 `n > k`
- `g_adj = G / (G - 1)` 若 `G > 1`
- `k` 为第二阶段回归变量数（`K1 + K2`）

## 结果字段与对齐优先级

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(df_m)` | 模型自由度（斜率参数数） | 高 |
| `e(df_r)` | 残差自由度 `N - K` | 高 |
| `e(r2)` | R-squared（第二阶段） | 高 |
| `e(rmse)` | Root MSE | 高 |
| `e(F)` | F-statistic（结构方程） | 高 |
| `e(b)` / `e(V)` | 系数与协方差 | 高 |
| `e(instd)` | 内生变量列表 | 中 |
| `e(insts)` | 工具变量列表 | 中 |
| `e(exogr)` | 外生变量列表 | 中 |

**注意**：`ivregress 2sls` 报告的 `e(r2)` 是**第二阶段**的 OLS R²，即用 `X̂` 对 `y` 回归的 R²。结构残差 `e = y - X β` 的 RSS 可能与第二阶段 RSS 略有差异，Stata 使用结构残差计算 `rmse` 和 `F`，但 `r2` 使用第二阶段回归的 RSS。

## 最小兼容子集（Wave 2 Phase A）

### 必须支持
- `IV2SLS(data, y, x_exog, x_endog, instruments, add_constant=True)`
- `fit(vce="ols")`
- `fit(vce="robust")`
- `fit(vce="cluster", cluster="...")`
- 输出字段：`nobs`、`df_model`、`df_resid`、`r2`、`rmse`、`f_stat`、`系数`、`标准误`

### 暂不支持
- `liml`（有限信息最大似然）
- `gmm`（广义矩估计）
- 过度识别检验（`estat overid`）
- 弱工具检验（`estat firststage` 的完整输出）
- `vce(hac)` 等时间序列稳健标准误

## Synthetic 样例设计

### `w2_ivregress_basic`
- **数据集**：手工生成（已知系数、内生性与工具变量强度）
- **Stata 命令**：`ivregress 2sls y x1 (x2 = z1 z2)`
- **Python API**：`IV2SLS(data, y="y", x_exog=["x1"], x_endog=["x2"], instruments=["z1", "z2"]).fit()`
- **风险焦点**：2SLS 系数是否与闭式解一致、是否与 Stata 对齐

### `w2_ivregress_cluster`
- **数据集**：手工 panel 数据（带 firm/cluster）
- **Stata 命令**：`ivregress 2sls y x1 (x2 = z1 z2), vce(cluster firm)`
- **风险焦点**：cluster-robust SE 小样本修正

## Real-Data 样例设计

### `w2_ivregress_real_card`
- **数据集**：Card (1995) returns-to-schooling 数据
- **本地路径**：`research/data/public/iv/card.csv`
- **Stata 命令**：`ivregress 2sls lwage exper expersq black south smsa reg661-reg668 smsa66 (educ = nearc4)`
- **Python API**：`IV2SLS(..., y="lwage", x_exog=["exper",...], x_endog=["educ"], instruments=["nearc4"]).fit()`
- **风险焦点**：真实数据下 2SLS 系数、SE、R² 的精确对齐

## 与 `ivreghdfe` 的关系

`ivreghdfe` = `ivreg2` 的 2SLS 算法 + `reghdfe` 的 FE 吸收。在 Phase A：
1. 先实现纯 2SLS（`IV2SLS`）
2. 再在 `AbsorbingOLS` / LSDV 框架上扩展 `IVAbsorbingOLS`：
   - 对所有变量（`y`, `X_endo`, `X_exog`, `Z`）做 FE 吸收（LSDV 投影）
   - 在吸收后的残差化空间运行 2SLS
   - 报告的系数与 VCE 对应于原始变量（非 LSDV 参数）

这一路径与 `ivreghdfe` 的核心算法（先 partialling out FE，再 ivreg2）在数学上等价。
