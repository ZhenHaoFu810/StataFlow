# `ppmlhdfe` 研究档案

## 命令定位

- 命令族：`Binary / Count`
- 类型：社区贡献命令
- 规则来源：公开源码优先
- 作者：Sergio Correia（基于 `reghdfe` 的泊松 PML 扩展）
- 本地镜像：`research/vendor/stata_community/ppmlhdfe/`

## 版本与许可证

- **版本**：`master`（本地镜像）
- **许可证**：开源社区模块（MIT/BSD 风格）
- **依赖**：
  - `reghdfe >= 6.12.5`
  - `ftools >= 2.49.1`
  - 底层复用 `reghdfe` 的 Mata 吸收内核

## 核心源码入口

| 文件 | 职责 |
|------|------|
| `ppmlhdfe.ado` | 主命令入口；解析语法、验证版本、调用 `reghdfe` 进行 HDFE 吸收 |
| `ppmlhdfe.mata` / 嵌入 Mata | IRLS 迭代器、收敛判定、分离检测、VCE 计算 |

`ppmlhdfe` 的核心算法可概括为：
1. 构造初始值 `β = 0`（`μ = 1`）
2. 进入 **IRLS（Iteratively Reweighted Least Squares）** 循环
3. 每一步计算 working response `z = Xβ + (y - μ) / μ`
4. 计算权重 `w = μ`
5. 对 `z` 关于 `X` 和 FE dummies 做 **加权 HDFE 回归**（即 partialling-out 后的加权 OLS）
6. 更新 `β` 和 FE 效应，重新计算 `μ = exp(Xβ + FE)`
7. 重复直至收敛

## 关键实现洞察

### 1. `ppmlhdfe` = Poisson PML + `reghdfe` 吸收内核

数学上等价路径：
- 设 `η = Xβ + Dα`，其中 `D` 为 FE dummy 矩阵，`α` 为 FE 系数
- 泊松对数似然：`ll = Σ_i [y_i η_i - exp(η_i)]`
- Score：`∂ll/∂β = X'(y - μ)`，`∂ll/∂α = D'(y - μ)`
- Hessian（Fisher）：`E[-∂²ll/∂β∂β'] = X'WX`，`W = diag(μ_i)`
- 因此 Newton-Raphson / Fisher scoring 更新等价于以 `w=μ` 为权重、以 `z = η + (y-μ)/μ` 为 working response 的加权最小二乘

### 2. Python 最小实现路径

**Phase A 推荐策略**：扩展 `AbsorbingOLS` 的 LSDV 框架为 `PPMLHDFE`：

1. 构造统一的 LSDV 设计矩阵 `W_full = [X, D, constant]`
2. 初始化 `β = 0`
3. 迭代：
   a. 计算 `η = W_full @ γ`（`γ` 包含 `β`、FE 系数和常数项）
   b. 计算 `μ = exp(η)`
   c. 计算 `z = η + (y - μ) / μ`
   d. 计算权重 `w = μ`
   e. 求解加权 OLS：`γ_new = (W_full' diag(w) W_full)^{-1} W_full' diag(w) z`
   f. 检查 `γ` 的收敛性
4. 收敛后，通过 `T` 矩阵变换将 LSDV 参数 `γ` 映射到 reported 参数空间（仅报告 `X` 的系数和 `_cons`）

**为什么这与 `ppmlhdfe` 等价**：
- 在完整 LSDV 矩阵上做 IRLS，每一步自动包含了 FE 效应的更新
- 这与 `ppmlhdfe` 调用 `reghdfe` 在残差化空间做加权回归在数学上严格等价

### 3. 零值处理

泊松 PML 天然支持 `y = 0`：
- 对数似然项为 `-exp(η)`，不发散
- 因此 `ppmlhdfe` 无需像对数线性模型那样删除零值观测
- 这也是 gravity trade 文献选择 PPML 的核心原因之一

### 4. 分离问题（Separation）

当存在某组 FE 或某条线性组合使得所有 `y=0` 时，理论上 `η → -∞`，导致部分系数无界。`ppmlhdfe` 的 Stata 实现通过以下方式处理：
- **迭代固定点检测**：若某些 FE 组合下的 `μ` 在迭代中趋于 0，则这些 FE 对应的参数趋向负无穷
- **简单 Phase A 策略**：先不实现完整的分离检测与剔除算法；若 synthetic 和真实数据样例均未触发分离，则将其标记为“尚未支持的边界情况”
- **若后续真实数据触发分离**：再引入 Correia, Guimarães, Zylkin (2020) 的迭代算法或 `ppmlhdfe` 源码中的 `check_separation` 逻辑

### 5. 结果字段

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(df_m)` | 模型自由度 | 高 |
| `e(df_a)` | 吸收的 FE 参数数 | 高 |
| `e(ll)` | 对数似然 | 高 |
| `e(deviance)` | 偏差 | 高 |
| `e(chi2)` | LR chi²（vs 空模型） | 高 |
| `e(r2_p)` | Pseudo R² | 中 |
| `e(b)` / `e(V)` | 系数与协方差 | 高 |
| `e(N_clust)` | 聚类组数 | 高（cluster 时） |
| `e(absvars)` | 吸收变量 | 中 |
| `e(converged)` | 是否收敛 | 中 |

### 6. `df_a` 与 cluster 嵌套扣减

完全复用 `reghdfe` 的规则：
- 1 FE：`df_a = G`
- 2 FE（连通数据）：`df_a = G1 + G2 - 1`
- cluster 嵌套于某 FE：该 FE 对 `df_a` 贡献 0

### 7. 常数项恢复

与 `reghdfe` 一致：`_cons` = 常数项 + 所有 FE dummy 系数的未加权均值。

由于 IRLS 在 LSDV 矩阵上运行，收敛后的 `γ` 可通过现有的 `T` 矩阵变换映射到 reported 参数空间。

### 8. VCE 支持边界

Phase A 必须支持：
- `vce="robust"`（默认，与 Stata `ppmlhdfe` 默认行为一致）
- `vce="ols"`（严格 conventional VCE）
- `vce="cluster"`（单 cluster）

**VCE 计算**：
- `vce="ols"`：收敛后计算 `V = (X'WX)^{-1}`（在 LSDV 全参数空间），再通过 `T` 矩阵变换到 reported 参数空间
- `vce="robust"`：在 LSDV 全参数空间计算 robust 三明治 `V = (X'WX)^{-1} X' diag((y-μ)^2) X (X'WX)^{-1}`，并应用 `N/(N-1)` 小样本修正
- `vce="cluster"`：在 LSDV 全参数空间计算聚类稳健三明治，再通过 `T` 矩阵变换；仅应用 `G/(G-1)` 修正（asymptotic mode）
- 小样本修正：`k_eff = k_x_reported + df_a`（与 `ivreghdfe` 的 cluster 修正一致）

## 最小兼容子集（Wave 3 Phase A）

### 必须支持
- `PPMLHDFE(data, y, x, absorb=[var1, var2], add_constant=True)`
- `fit(vce="robust")`（默认，与 Stata `ppmlhdfe` 默认行为一致）
- `fit(vce="ols")`（严格 conventional VCE）
- `fit(vce="cluster", cluster="...")`
- 默认自动 drop singletons（复用 `AbsorbingOLS` 现有逻辑）
- 输出字段：`nobs`、`df_model`、`df_a`、`df_resid`、`ll`、`deviance`、`chi2`、`系数`、`标准误`、`cluster_count`、`absorb_vars`

### 暂不支持
- 分离检测与自动剔除（若样例不触发，可延后）
- `offset()` / `exposure()`
- multi-way cluster
- `predict` 后估计
- 非泊松的 GLM 族

## Synthetic 样例设计

### `w3_ppmlhdfe_basic`
- **数据集**：手工生成 panel 计数数据（含零值）
- **Stata 命令**：`ppmlhdfe y x1 x2, absorb(entity_id) vce(ols)`
- **Python API**：`PPMLHDFE(..., absorb=["entity_id"]).fit(vce="robust")`（Stata 的 `vce(ols)` 在该命令中等价于 robust）
- **风险焦点**：单 FE 吸收 + IRLS 收敛 + 系数/ll/deviance 对齐

### `w3_ppmlhdfe_cluster`
- **数据集**：手工生成 panel 计数数据（含零值，带 cluster）
- **Stata 命令**：`ppmlhdfe y x1 x2, absorb(entity_id time_id) vce(cluster entity_id)`
- **Python API**：`PPMLHDFE(..., absorb=["entity_id","time_id"]).fit(vce="cluster", cluster="entity_id")`
- **风险焦点**：双 FE + cluster-robust SE + cluster 嵌套扣减 `df_a`

## Real-Data 样例设计

### `w3_ppmlhdfe_real_gravity`
- **数据集**：gravity trade panel（后续下载）
- **本地路径**：`research/data/public/gravity/gravity.csv`
- **Stata 命令**：`ppmlhdfe trade gdp_o gdp_d dist contig comlang, absorb(exporter importer) vce(cluster pair_id)` 或类似
- **Python API**：`PPMLHDFE(..., absorb=["exporter","importer"]).fit(vce="cluster", cluster="pair_id")`
- **风险焦点**：真实 gravity 数据含大量零值贸易流，验证 PPML + HDFE + cluster 的数值实现

**注意**：具体变量名和聚类变量以实际数据集为准，允许在回报中调整。

## 与现有代码的复用关系

| 现有组件 | `ppmlhdfe` 复用方式 |
|---------|---------------------|
| `AbsorbingOLS._prepare_data()` | 复用 LSDV 矩阵构造、singleton drop、共线性检测、`df_a` 计算 |
| `AbsorbingOLS._drop_singletons()` | 直接复用 |
| `AbsorbingOLS._detect_collinearity()` | 直接复用 |
| `AbsorbingOLS` 的 `T` 矩阵 | 复用 `_cons` 恢复与 VCE 变换逻辑 |
| `ResultSchema` | 复用；必要时新增 `deviance` 等字段的承载方式（可在回报中说明） |
| `Poisson`（若 Wave 3 内建） | 复用 IRLS 迭代器、收敛判定、链接函数逻辑 |

## 实现风险提示

1. **IRLS 收敛速度**：PPML + HDFE 的 IRLS 可能比纯 OLS 收敛慢，尤其是数据量较大时。建议设置默认最大迭代 100，并提供 `maxiter` 参数。
2. **分离问题**：若真实 gravity 数据中存在 exporter-importer 组合的所有贸易额均为 0，可能触发分离。建议在 Phase A 先跑通无分离数据；若触发，再升级处理策略。
3. **VCE 变换**：与 `ivreghdfe` 类似，cluster 时的小样本修正需要正确计算 `k_eff = k_x_reported + df_a`。
4. **零值与 log(y)**：与对数线性模型不同，PPML 不需要 `log(trade)`，因此零值观测保留。确保 Python 与 Stata 使用完全相同的样本（仅因缺失值剔除）。
