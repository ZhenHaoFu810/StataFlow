# `ivreghdfe` 研究档案

## 命令定位

- 命令族：`IV / GMM`
- 类型：社区贡献命令
- 规则来源：公开源码优先
- 作者：基于 `ivreg2`（Baum / Schaffer / Stillman）+ `reghdfe`（Correia）的封装
- 本地镜像：`research/vendor/stata_community/ivreghdfe/`

## 版本与许可证

- **版本**：`1.1.4  29nov2025`（本地镜像 master）
- **许可证**：开源社区模块（BSD 风格）
- **依赖**：
  - `reghdfe >= 6.12.5`
  - `ftools >= 2.49.1`
  - 底层调用 `ivreg2` 的 Mata 库

## 核心源码入口

| 文件 | 职责 |
|------|------|
| `src/ivreghdfe.ado` | 主命令入口；解析语法、验证版本、调用 `ivreg2` Mata 库 |
| `src/ivreghdfe.sthlp` | 帮助文档 |

`ivreghdfe.ado` 本身是一个**薄封装层**：
1. 解析 `absorb(...)` 和 `vce(...)`
2. 调用 `reghdfe` 对 **所有变量**（`y`, `X_endo`, `X_exog`, `Z`）进行 FE 吸收（partialling out）
3. 在吸收后的残差化数据上调用 `ivreg2` 执行 2SLS
4. 修正自由度（`df_a` 扣减、cluster 嵌套扣减等）

## 关键实现洞察

### 1. `ivreghdfe` = `reghdfe` 残差化 + `ivreg2` 2SLS

在内部，`ivreghdfe` 并不重新发明 2SLS 算法。它的核心工作是将 `reghdfe` 的**残差化器**（residualizer / partialling-out operator）应用到 IV 的每个变量上，然后跑标准的 2SLS。

数学上等价路径：
- 设 `D(y)` = `y` 经 FE 吸收后的残差
- 设 `D(X)` = `X` 经 FE 吸收后的残差
- 设 `D(Z)` = `Z` 经 FE 吸收后的残差
- 估计量：`β = [D(X)' P_{D(Z)} D(X)]^{-1} D(X)' P_{D(Z)} D(y)`

这与在完整 LSDV 矩阵上直接做 2SLS 在数学上严格等价。

### 2. Python 最小实现路径

**Phase A 推荐策略**：扩展 `AbsorbingOLS` 的 LSDV 框架为 `IVAbsorbingOLS`：

1. 对 `y`、`X_endo`、`X_exog`、`Z_excl` 分别调用与 `AbsorbingOLS` 相同的 `_prepare_data()` 逻辑，得到各自的 LSDV 残差化形式。
2. 实际上更简单：直接构造包含所有变量的**统一** LSDV 设计矩阵。
3. 在这个统一矩阵上：
   - 第一阶段：将 `X_endo` 对 `Z = [Z_excl, X_exog, 所有 FE dummies, constant]` 回归
   - 第二阶段：将 `y` 对 `[X̂_endo, X_exog, 所有 FE dummies, constant]` 回归
4. 报告的系数仅对应 `X_endo`、`X_exog` 和 `_cons`（FE dummy 系数不报告）。

**为什么这与 `ivreghdfe` 等价**：
- LSDV 的 OLS 投影 `P_W`（`W = [FE dummies, constant]`）等价于 `reghdfe` 的 partialling out。
- 在完整 LSDV 矩阵上做 2SLS，第一阶段的拟合值已经自动包含了 FE 效应的投影。

### 3. 结果字段

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(df_m)` | 模型自由度 | 高 |
| `e(df_r)` | 残差自由度 | 高 |
| `e(df_a)` | 吸收的 FE 参数数 | 高 |
| `e(r2)` / `e(r2_a)` | R2 / Adjusted R2 | 高 |
| `e(rmse)` | Root MSE | 高 |
| `e(F)` | F-statistic | 高 |
| `e(N_clust)` | 聚类组数 | 高（cluster 时） |
| `e(b)` / `e(V)` | 系数与协方差 | 高 |
| `e(absvars)` | 吸收变量 | 中 |

### 4. `df_a` 与 cluster 嵌套扣减

完全复用 `reghdfe` 的 Phase A 规则：
- 1 FE：`df_a = G`
- 2 FE（连通数据）：`df_a = G1 + G2 - 1`
- cluster 嵌套于某 FE：该 FE 对 `df_a` 贡献 0

### 5. 常数项恢复

与 `reghdfe` 一致：`_cons` = 常数项 + 所有 FE dummy 系数的未加权均值。

由于 2SLS 在 LSDV 矩阵上运行，我们可以复用现有的 `T` 矩阵变换，将 LSDV 参数映射到 reported 参数。

### 6. VCE 支持边界

Phase A 必须支持：
- `vce="ols"`
- `vce="cluster"`（单 cluster）

Phase A 建议支持：
- `vce="robust"`

**VCE 计算**：在 LSDV 矩阵上，先计算完整的 2SLS 协方差（对应于所有 LSDV 参数），再通过 `T` 矩阵变换到 reported 参数空间。

## 最小兼容子集（Wave 2 Phase A）

### 必须支持
- `IVAbsorbingOLS(data, y, x_exog, x_endog, instruments, absorb=[var1, var2], add_constant=True)`
- `fit(vce="ols")`
- `fit(vce="cluster", cluster="...")`
- 默认自动 drop singletons（复用 `AbsorbingOLS` 现有逻辑）
- 输出字段：`nobs`、`df_model`、`df_a`、`df_resid`、`r2`、`r2_adj`、`rmse`、`f_stat`、`系数`、`标准误`、`cluster_count`、`absorb_vars`

### 暂不支持
- `liml`
- `gmm`
- multi-way cluster
- `predict` 后估计
- 过度识别 / 弱工具检验

## Synthetic 样例设计

### `w2_ivreghdfe_basic`
- **数据集**：手工生成 panel 数据
- **Stata 命令**：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) keepsingletons`
- **Python API**：`IVAbsorbingOLS(..., absorb=["entity_id"]).fit(vce="ols")`
- **风险焦点**：单 FE 吸收 + 2SLS 系数对齐

### `w2_ivreghdfe_cluster`
- **数据集**：手工生成 panel 数据
- **Stata 命令**：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id time_id) vce(cluster entity_id)`
- **Python API**：`IVAbsorbingOLS(..., absorb=["entity_id","time_id"]).fit(vce="cluster", cluster="entity_id")`
- **风险焦点**：双 FE + cluster-robust SE + cluster 嵌套扣减 `df_a`

## Real-Data 样例设计

### `w2_ivreghdfe_real_panel`
- **数据集**：`wagepan`
- **本地路径**：`research/data/public/panel/wooldridge/wagepan.csv`
- **设计**：构造 `union_lag` 作为 `union` 的工具变量（个体层面的滞后一期）
- **Stata 命令**：`ivreghdfe lwage exper expersq (union = union_lag), absorb(nr year) vce(cluster nr)`
- **Python API**：`IVAbsorbingOLS(..., x_endog=["union"], instruments=["union_lag"], absorb=["nr","year"]).fit(vce="cluster", cluster="nr")`
- **风险焦点**：真实数据下双向 FE + IV + cluster 的完整对齐

**注意**：使用滞后工具变量仅用于**数值实现验证**，不对识别有效性（如外生性）作额外承诺。

## 与现有代码的复用关系

| 现有组件 | `ivreghdfe` 复用方式 |
|---------|---------------------|
| `AbsorbingOLS._prepare_data()` | 复用 LSDV 矩阵构造、singleton drop、共线性检测、`df_a` 计算 |
| `AbsorbingOLS._drop_singletons()` | 直接复用 |
| `AbsorbingOLS._detect_collinearity()` | 直接复用 |
| `AbsorbingOLS` 的 `T` 矩阵 | 复用 `_cons` 恢复逻辑 |
| `ResultSchema` | 复用；必要时在 `ModelInfo` 中新增 `iv_endog`、`iv_instruments` 字段 |

## 实现风险提示

1. **第一阶段共线性**：若某工具变量与 FE 完全共线（如 time-invariant 变量 + individual FE），QR 分解会自动剔除。需要确保第一阶段和第二阶段使用一致的 collinear dropped 集合。
2. **VCE 变换**：2SLS 的 VCE 需在 LSDV 全参数空间计算后通过 `T` 矩阵变换。cluster 时的小样本修正同样要排除 nested FE 参数。
3. **R² 口径**：`ivreghdfe` 的 R² 是第二阶段 OLS 的 R²（用 `X̂` 对 `y` 回归），但 RMSE 和 F 使用结构残差。
