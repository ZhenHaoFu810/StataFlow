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

---

## Wave 7 研究收束：`first` / `ffirst` 一阶段诊断

### 1. 实现位置

`ivreghdfe.ado` 中 Mata 函数 `s_ffirst()`（~L6150-6493），底层调用 `ivreg2` 的一阶段输出框架。

### 2. 核心统计量

对每个内生变量，`s_ffirst()` 计算 21 元素结果向量：

| 行 | 统计量 | 说明 |
|----|--------|------|
| 1 | RMSE | 一阶段回归 RMSE |
| 2 | Shea partial R² | Shea (1997) 偏 R² |
| 3 | Partial R² | 简单偏 R² |
| 4 | F-statistic | 一阶段 F 统计量 |
| 5-6 | df / df_r | 分子/分母自由度 |
| 7 | p-value | F 检验 p 值 |
| 8-13 | Sanderson-Windmeijer F | 多内生变量时的 SW 稳健 F |
| 14 | SW partial R² | SW 偏 R² |
| 15-20 | Angrist-Pischke F | AP 多变量 F |
| 21 | AP partial R² | AP 偏 R² |

### 3. 关键公式

**Shea Partial R²**：
```
Shea_R2 = (Var(x_hat) / Var(x)) * (R2_full - R2_excluded) / (1 - R2_excluded)
```

**Sanderson-Windmeijer F**：
- 对每个内生变量，partial out 其他内生变量后，检验工具变量显著性
- 多变量时使用分块回归公式，避免单独跑回归
- 若 `robust` / `cluster`，使用稳健 Wald 检验

**Angrist-Pischke F**：
- 类似 SW，但 partial out 结构不同
- 更关注被排除工具变量对每个内生变量的解释力

### 4. Python 实现路径

在 `IVAbsorbingOLS` 中：
1. 第一阶段回归已完成（拟合 `X_endog` 对 `Z` 的回归）
2. 从第一阶段结果中提取：
   - 每个内生变量的 predicted value `x_hat`
   - 第一阶段 R²、RMSE、F 统计量
3. 计算 Shea R²：利用 `x_hat` 的方差与 `x` 的方差
4. 多内生变量时：
   - 用分块矩阵公式计算 SW F 和 AP F
   - 或直接对每个内生变量 partial out 其他变量后跑辅助回归
5. 将结果存入 `ResultSchema` 的扩展字段或新增 `FirstStageDiagnostics` 对象

### 5. 与 Stata 对齐要点

- `first` 输出每个内生变量的单独一阶段结果
- `ffirst` 输出紧凑版（仅 SW / AP 统计量）
- 若 `vce=cluster`，所有 F 统计量使用 cluster-robust 协方差矩阵
- 小样本自由度调整与第二阶段一致

### 6. Synthetic 样例设计

#### `w7_ivreghdfe_first_basic`
- **数据集**：手工面板，单内生变量 + 2 工具变量
- **Stata**：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) first`
- **Python**：`IVAbsorbingOLS(...).fit(vce="ols", first=True)`
- **风险焦点**：一阶段 F、Shea R²、Partial R² 字段级对齐

#### `w7_ivreghdfe_first_cluster`
- **数据集**：同上，加 cluster 结构
- **Stata**：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id time_id) vce(cluster entity_id) first`
- **Python**：`IVAbsorbingOLS(...).fit(vce="cluster", cluster="entity_id", first=True)`
- **风险焦点**：cluster-robust 一阶段 F 统计量对齐

#### `w7_ivreghdfe_ffirst_multi`
- **数据集**：2 个内生变量 + 3 工具变量
- **Stata**：`ivreghdfe y x1 (x2 x3 = z1 z2 z3), absorb(entity_id) ffirst`
- **Python**：`IVAbsorbingOLS(..., x_endog=["x2","x3"], instruments=["z1","z2","z3"]).fit(vce="ols", ffirst=True)`
- **风险焦点**：SW F、AP F、多变量偏 R² 对齐

---

## Wave 10 研究收束：GMM / LIML / weakiv 分支定位

### 1. 源码路径定位

`ivreghdfe.ado`（`research/vendor/stata_community/ivreghdfe/ivreghdfe-master/src/ivreghdfe.ado`）本质为 `ivreg2` 的薄封装。GMM/LIML/weakiv 选项直接透传至 `ivreg2` Mata 库，自身不做额外统计处理。

#### 1.1 选项解析分支（L280–324）

`ivparse` 子程序解析以下选项：
- `gmm2s` → 高效两步 GMM
- `gmm` →  legacy 选项，报错
- `cue` → 连续更新 GMM
- `liml` → 有限信息最大似然
- `fuller(#)` → Fuller LIML 修正
- `kclass(#)` → k-class 估计量
- `wmatrix(...)` → 用户自定义权重矩阵

解析结果通过 `s(kclassopt)`、`s(fulleropt)`、`s(liml)` 等 local 变量返回。

#### 1.2 估计器分发逻辑（L921–1190）

```
if (liml | kclass) → s_liml(...)          // L923
else if (gmm2s)    → s_gmm1s(...)         // L1010 第一步
                     → s_egmm(...)        // L1129 第二步（高效 GMM）
else if (cue)      → s_gmmcue(...)        // L1168
else               → s_gmm1s(...)         // L990  标准 IV/2SLS
```

`ivreghdfe` 对 GMM 的额外处理仅在于：
1. FE 吸收后调用 `ivreg2` Mata 函数
2. 自由度修正（`dofminus` 扣减已吸收 FE 数）
3. 无其他统计包装

#### 1.3 弱工具变量检验路径（L1730–1844）

`weakiv` 统计量计算在 `ivreg2` 层完成，`ivreghdfe` 透传：
- **Underidentification test**：`ranktest` 命令计算 Kleibergen-Paap rk LM statistic
- **Weak identification test**：
  - 同方差：Cragg-Donald Wald F statistic
  - 异方差/聚类：Kleibergen-Paap rk Wald F statistic
- **Stock-Yogo critical values**：调用 `s_cdsy()` Mata 函数查表（来源：Stock-Yogo 2005）

显示部分（L2619）：
```
(Kleibergen-Paap rk Wald F statistic):  [value]
Stock-Yogo weak ID test critical values: [10% maximal IV size, etc.]
```

### 2. Mata 核心函数清单

| 函数 | 行号 | 职责 |
|------|------|------|
| `s_liml` | L5724 | LIML / Fuller / k-class 估计量；特征值求 lambda；VCE 计算（含 robust/cluster） |
| `s_gmm1s` | L5349 | 一步 GMM（含 OLS、IV、用户提供权重矩阵三种子情况） |
| `s_egmm` | L5512 | 高效两步 GMM（使用第一步估计的 S 矩阵构造最优权重） |
| `s_iegmm` | L5618 | 非高效 GMM（使用用户提供权重矩阵，仅计算 V 和 J） |
| `s_gmmcue` | L5962 | CUE（连续更新 GMM）；调用 `optimize()` 数值最小化；使用 `m_cuecrit` 评价函数 |
| `m_cuecrit` | L6130 | CUE 目标函数：J(β) = N · ḡ' · S⁻¹ · ḡ，其中 ḡ = Z'e/N |
| `s_ffirst` | L6150 | 一阶段诊断：Shea R²、SW F、AP F、AR statistic |
| `m_omega` | L6497+ | 正交条件协方差矩阵（S/Ω）计算：homoskedastic / robust / cluster / HAC（位于 ivreg2 Mata 库或 ado 文件后部） |
| `s_cdsy` | 外部 | Stock-Yogo 临界值查表（ivreg2 Mata 库） |

### 3. 关键公式速查（来自 Mata 源码）

#### 3.1 LIML

**lambda 计算**（最小特征值）：
```
W = Y'Y - Y'Z (Z'Z)⁻¹ Z'Y          // Y' M_Z Y，残差二次型（未缩放；缩放因子在特征值问题中抵消）
W1 = Y'Y - Y'Z2 (Z2'Z2)⁻¹ Z2'Y     // Y' M_{Z2} Y（若无外生量则 W1 = Y'Y；未缩放）
M = W^(-1/2)
lambda = min(eigenvalues(M * W1 * M))
```

**k-class 参数**：
```
Fuller: k = lambda - fuller / (N - cols(Z))
k-class: k = kclass
LIML:    k = lambda
```

**估计量**：
```
Qh = (1-k)*QXX + k*QXZ*QZZ⁻¹*QXZ'
beta = Qh⁻¹ * [(1-k)*QXy + k*QXZ*QZZ⁻¹*QZy]
```

#### 3.2 GMM2S

**第一步**（`s_gmm1s`， inefficent）：
- 默认权重矩阵 W = (σ² · QZZ)⁻¹ = N · (σ² · Z'Z)⁻¹（即 IV/2SLS 权重）
- 若 `wmatrix()` 提供，则使用用户矩阵

**第二步**（`s_egmm`，efficient）：
```
omega = m_omega(vcvo)         // 基于第一步残差计算 S 矩阵
W = invsym(omega)             // 最优权重矩阵
beta = [QXZ · W · QXZ']⁻¹ · QXZ · W · QZy
V = 1/N · [QXZ · W · QXZ']⁻¹
```

**J statistic（过度识别检验）**：
```
gbar = Z'e / N
J = N · gbar' · omega⁻¹ · gbar
```

#### 3.3 CUE

**目标函数**：
```
J(β) = N · ḡ(β)' · S(β)⁻¹ · ḝ(β)
其中 ḝ(β) = Z'(y - Xβ) / N
S(β) = m_omega(基于残差 e = y - Xβ 计算)
```

使用 Stata `optimize()` 数值最小化，初始值来自 2SLS 或 GMM2S。

### 4. 与 2SLS 的差异要点

| 维度 | 2SLS | GMM2S | LIML | CUE |
|------|------|-------|------|-----|
| 权重矩阵 | (Z'Z)⁻¹ | 估计的 S⁻¹ | 不涉及 | 连续更新 S(β)⁻¹ |
| 估计量公式 | 线性闭式 | 线性闭式（两步） | 特征值问题 | 数值优化 |
| 小样本偏差 | 有 | 有 | 较小 | 较小 |
| 过度识别检验 | Sargan | Hansen J | 似然比型 | J 统计量 |
| VCE | 同方差/robust | 基于 S 矩阵 | LIML 专用公式 | 基于最终 S |

### 5. Python 实现路径（Round 2 规划）

#### 5.1 GMM2S

在 `IVAbsorbingOLS` 中新增 `estimator="gmm2s"`：
1. 第一阶段：使用 IV/2SLS 权重跑第一步 GMM，得到残差 e
2. 计算 `omega = m_omega(vcvo)`（复用现有 VCE 框架的 meat 矩阵计算）
3. 第二阶段：使用 W = omega⁻¹ 作为权重矩阵，重新估计 beta
4. V = 1/N · [QXZ · W · QXZ']⁻¹
5. 计算 J statistic 和 Hansen J p-value

#### 5.2 LIML

新增 `estimator="liml"`：
1. 构造矩阵 Y = [y, X_endo]、Z = [Z_excl, X_exog]、Z2 = X_exog
2. 计算 W 和 W1
3. 求最小特征值 lambda
4. 若 `fuller` 提供，k = lambda - fuller/(N-L)；否则 k = lambda
5. 用 k-class 公式计算 beta
6. VCE：
   - 同方差：`V = sigmasq/N · Qh⁻¹`
   - Robust/cluster：使用 LIML 专用公式（见 s_liml L5910-5943）

#### 5.3 CUE

新增 `estimator="cue"`：
1. 用 2SLS/GMM2S 估计值作为初始值
2. 定义目标函数 `cue_objective(beta)`：
   - 计算残差 e = y - Xβ
   - 计算 omega = m_omega(基于 e)
   - 返回 J = N · gbar' · omega⁻¹ · gbar
3. 使用 scipy.optimize.minimize 数值优化
4. 最终 omega 用于 VCE 计算

#### 5.4 weakiv

新增 `weakiv=True` 参数：
1. 调用 `ranktest` 等价的 Python 实现（或自行计算 Kleibergen-Paap F）
2. 计算 Kleibergen-Paap rk Wald F：
   - 基于约简型回归的 robust/cluster VCE
   - 公式：`F = chi2 / (N-1) * (N-L-sdofminus) / N_clust * (N_clust-1) / L1`
3. Stock-Yogo 临界值：运行时查表/插值（来源：Stock-Yogo 2005）
4. 输出字段：`widstat`、`idstat`、`cddstat`、`cddp`、`sy_critical_10` 等

### 6. Synthetic 样例设计

#### `w10_gmm2s_overid`
- **数据集**：手工 panel，1 内生变量 + 2 工具变量 + 1 外生变量
- **Stata**：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) gmm2s`
- **Python**：`ivreghdfe(..., estimator="gmm2s")`
- **风险焦点**：GMM2S 与 2SLS 在恰好识别时等价；过度识别时权重矩阵差异

#### `w10_liml_weak`
- **数据集**：手工 panel，弱工具变量设定（低第一阶段 F）
- **Stata**：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) liml`
- **Python**：`ivreghdfe(..., estimator="liml")`
- **风险焦点**：LIML 与 2SLS 系数差异、偏差方向

#### `w10_fuller_adjust`
- **数据集**：同上弱工具设定
- **Stata**：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) liml fuller(1)`
- **Python**：`ivreghdfe(..., estimator="liml", fuller=1)`
- **风险焦点**：Fuller 修正后 k-class 参数与系数稳定性

#### `w10_weakiv_test`
- **数据集**：同上弱工具设定
- **Stata**：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) weakiv`
- **Python**：`ivreghdfe(..., weakiv=True)`
- **风险焦点**：Kleibergen-Paap F 字段级对齐、Stock-Yogo 临界值一致

### 7. Real-data 样例设计

#### `w10_card_gmm2s`
- **数据集**：Card 教育回报数据（`research/data/public/iv/card.dta`）
- **Stata**：`ivreghdfe lwage exper expersq (educ = nearc4), absorb(south) gmm2s`
- **Python**：`ivreghdfe(..., estimator="gmm2s")`
- **风险焦点**：真实数据下 GMM2S 系数/SE 与 Stata 对齐

#### `w10_card_liml`
- **数据集**：同上
- **Stata**：`ivreghdfe lwage exper expersq (educ = nearc4), absorb(south) liml`
- **Python**：`ivreghdfe(..., estimator="liml")`
- **风险焦点**：真实数据下 LIML 估计量与 Stata 对齐

### 8. 研究残余风险

| 风险 | 说明 | Round 2 缓解 |
|------|------|-------------|
| `ivreg2` Mata 库中 `m_omega` 实现细节未完全阅读 | 仅阅读了顶层函数调用，未深入 `m_omega` 内部 | Round 2 中若 GMM VCE 偏差 >1e-4，需回头补读 |
| `s_cdsy` 外部定义 | Stock-Yogo 临界值表在 ivreg2 Mata 库中，本地镜像缺失 ivreg2 源码 | 使用公开文献插值公式或运行时从 Stata 抓取 |
| CUE 数值优化收敛性 | scipy.optimize 与 Stata optimize() 行为差异 | Round 2 中测试多种算法（Nelder-Mead, BFGS, L-BFGS-B） |
| GMM2S 小样本修正 | Stata 对小样本 GMM 有特定自由度调整 | Round 2 中对比 dofminus 参数影响 |
