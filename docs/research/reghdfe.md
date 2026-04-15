# `reghdfe` 研究档案

## 命令定位

- 命令族：`Panel / FE / HDFE`
- 类型：社区贡献命令
- 规则来源：公开源码优先
- 作者：Sergio Correia, Noah Constantine
- 论文依据：[Correia (2017) "Linear Models with High-Dimensional Fixed Effects"](http://scorreia.com/research/hdfe.pdf)

## 版本与许可证信息

- **本地镜像目录**：`research/vendor/stata_community/reghdfe/reghdfe-master/`
- **当前 GitHub 版本**：`6.13.1 10Jan2026`
- **当前 SSC 稳定版本**：`6.12.3 20aug2023`
- **许可证**：开源社区模块（随 GitHub 仓库分发）
- **Stata 最低版本要求**：`>= 11.2`（GitHub 版标注 `>= 12.1`）

## 依赖清单

| 依赖 | 用途 | 本地镜像 |
|------|------|----------|
| `ftools` (>= 2.50.0) | Mata 层面的快速因子变量处理（`Factor` 类） | `research/vendor/stata_community/`（尚未单独镜像） |
| `require` (>= 1.3.1) | 依赖版本管理 | 通过 SSC/GitHub 安装 |
| `ivreg2` | IV/GMM 场景（由 `ivreghdfe` 调用） | `research/vendor/stata_community/ivreghdfe/` |

## 核心源码入口

### ADO 层入口
| 文件（相对本地镜像根） | 职责 |
|--------|------|
| `src/reghdfe.ado` | 主命令入口；解析语法、验证选项、调用 `Estimate` |
| `src/reghdfe5.ado` | v5 历史版本入口 |
| `src/reghdfe3.ado` | v3 历史版本入口 |
| `src/reghdfe_estat.ado` | `estat` 后估计支持 |
| `src/reghdfe_header.ado` | 结果表头输出 |
| `src/reghdfe_footnote.ado` | 结果脚注输出 |
| `src/reghdfe_p.ado` | `predict` 后估计支持 |

### Mata 层入口
| 文件 | 职责 |
|------|------|
| `src/reghdfe.mata` | Mata 代码总入口；包含 `ftools` 引入和所有子模块 include |
| `current-code/Factor_FE.mata` | 扩展 `ftools` 的 `Factor` 类以支持 FE 场景 |
| `current-code/FE.mata` | `FixedEffects` Mata 类的核心定义 |
| `current-code/Regression.mata` | 回归求解（ partialling out + OLS ） |
| `current-code/DoF.mata` | 自由度估计（mobility group、nested、continuous 等） |
| `current-code/MAP.mata` | 均值吸收映射（Mean Absorption Procedure）迭代求解 |
| `current-code/LSMR.mata` / `LSQR.mata` | 可选的稀疏迭代求解器 |
| `current-code/Bipartite.mata` | 二分图处理（用于 team/individual FE） |

**核心算法流程**：
1. `reghdfe.ado` 解析 `absorb(...)` 和 `vce(...)`
2. 调用 Mata 中的 `FixedEffects` 对象
3. 用 `ftools` 将吸收变量编码为 `Factor`
4. 通过 MAP/LSMR/LSQR 对 RHS 变量做 **partialling out**（残差化）
5. 在残差化后的数据上运行 OLS
6. 计算 VCE（OLS / Robust / Cluster / MWC / Driscoll-Kraay）
7. 估计并报告 DoF

## 关键选项

### `absorb(varlist)`
- 核心选项；支持**多组**高维固定效应
- 示例：`absorb(firm_id year state#year)`
- 每一组都是一个分类变量或交互项
- 默认不把常数项单独报告（被吸收进 FE）

### `vce(robust)` / `vce(cluster clustervar)`
- Robust：HC1 异方差稳健标准误
- Cluster：单聚类或多聚类（multi-way clustering）
- 小样本修正：默认含 `(N-1)/(N-K) * G/(G-1)` 类修正

### `keepsingletons`
- 默认行为：**自动迭代剔除 singleton 组**
- singleton = 在某一个吸收变量中只有 1 个观测的组
- 原因：singleton 与 cluster 嵌套时会严重低估标准误、夸大显著性（参见 `docs/nested_within_cluster.md`）
- 如果不 drop，finite-sample correction `q` 会趋于 1，导致 cluster-robust SE 过小

### `dofadjustments(string)`
- 控制自由度修正策略
- 可选值：`none`、`firstpair`、`pairwise`、`clusters`、`continuous`
- 默认通常是 `firstpair` + `clusters`（视版本而定）
- 复杂度来源：多个 FE 时，mobility group 算法用于计算真正独立的 FE 参数数量

## 输出字段与重点比对的 `e()` 结果

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(df_m)` | 模型自由度（斜率参数） | 高 |
| `e(df_r)` | 残差自由度 | 高 |
| `e(df_a)` | 吸收的 FE 参数数量 | 高 |
| `e(r2)` / `e(r2_a)` | R2 / Adjusted R2 | 高 |
| `e(rmse)` | Root MSE | 高 |
| `e(F)` | F-statistic | 高 |
| `e(N_clust)` | 聚类组数 | 高（cluster 时） |
| `e(b)` / `e(V)` | 系数与协方差 | 高 |
| `e(absvars)` | 吸收变量列表 | 中 |
| `e(wtype)` / `e(wexp)` | 权重 | 中 |

**注意**：
- `reghdfe` 的 `e(df_a)` 通常比 `areg` 多 1（因为常数项也被视为被吸收）。
- `reghdfe` 不报告 `_cons` 的系数，除非显式使用 `noconstant`（v5+ 后反而默认加 `_cons` 以兼容 `margins`）。

## Synthetic 样例设计

### `p3_reghdfe_basic`
- **数据集**：`sysuse auto` 风格手工数据（20-30 组，2-3 个时期）
- **Stata 命令**：`reghdfe price weight length, absorb(turn) keepsingletons verbose(-1)`
- **Python API**：`AbsorbingOLS(data, y="price", x=["weight","length"], absorb=["turn"]).fit()`
- **风险焦点**：
  - 系数是否与 `areg` 对齐（容差 `1e-12` 级别）
  - `df_a` 是否与 `areg` 差 1
  - R2 / RMSE / F 的对齐口径

### `p3_reghdfe_two_fe`
- **数据集**：平衡面板（firm × year）
- **Stata 命令**：`reghdfe y x1 x2, absorb(firm year) keepsingletons`
- **Python API**：`AbsorbingOLS(..., absorb=["firm", "year"]).fit()`
- **风险焦点**：
  - 双向 FE 的系数是否与手动 LSDV 或 `reghdfe` 一致
  - 两个 FE 的 within/partialling out 精度

### `p3_reghdfe_cluster`
- **数据集**：同上
- **Stata 命令**：`reghdfe y x1 x2, absorb(firm year) cluster(firm)`
- **风险焦点**：
  - cluster-robust SE
  - singleton 自动 drop 后的样本量变化
  - cluster 嵌套于 FE 时的小样本修正

## Real-Data 样例设计

### `p3_reghdfe_real_panel`
- **数据集**：`wagepan`（`research/data/public/panel/wooldridge/wagepan.csv`）
- **Stata 命令**：`reghdfe lwage educ exper expersq union, absorb(nr year) vce(cluster nr)`
- **Python API**：`AbsorbingOLS(..., absorb=["nr","year"], ...).fit(vce="cluster", cluster="nr")`
- **风险焦点**：
  - 真实面板数据下双向 FE 的稳健性
  - 与 `xtreg, fe` + year dummies 或 `areg` 的系数一致性

### `p3_reghdfe_real_grunfeld`
- **数据集**：`Grunfeld`
- **Stata 命令**：`reghdfe invest mvalue kstock, absorb(company year)`
- **风险焦点**：
  - 非平衡面板下的吸收效果
  - `df_a` 的计算

## 最小兼容子集建议

建议 `reghdfe` 的 Python 兼容层最小子集分阶段实现：

### Phase A（最小可用）
1. `absorb(varlist)`：支持 1-2 个分类吸收变量
2. `vce`：`ols`、`robust`、单 `cluster`
3. 默认 **drop singletons**（可先支持单轮 drop，暂不要求迭代）
4. 权重：`aweight`（次优先）
5. 结果对象：完整 `ResultSchema`，含 `absorb_vars`、`df_a`、`cluster_count`

### Phase B（扩展）
1. 多聚类（multi-way clustering）
2. 复杂 DoF 修正（mobility group、pairwise）
3.  slopes / individual FEs / team FEs
4. `predict` 后估计

### 暂不纳入
- IV/GMM（交给 `ivreghdfe`）
- Driscoll-Kraay 标准误
- 并行计算
- LSMR/LSQR 以外的求解器（MAP 足够覆盖大部分场景）

## Phase A 实现规格（研究收束版）

本节基于本地源码镜像与 Stata 17 双跑实验，将 `reghdfe` Phase A 的最小实现边界收束为可直接进入编码的规格。

### 1. 推荐 Python 实现路径

**Phase A 推荐策略**：**直接扩展现有 `AbsorbingOLS`，以 LSDV（显式虚拟变量）方式支持 `absorb=[var1, var2]`。**

理由：
- 对 1-2 个分类吸收变量，LSDV 与 `reghdfe` 的 MAP/残差化算法在数学上完全等价，系数差异在机器精度内（已用 `wagepan` 双向 FE 验证，差异 `< 1e-12`）。
- 项目已有成熟的 `AbsorbingOLS` 单 FE 实现（含 QR 共线性剔除、常数项恢复、增量 F 统计量），扩展多 FE 的边际成本最低。
- 对经济学常见面板规模（如 `wagepan`：545 + 8 = 553 个 FE 水平），稠密 LSDV 矩阵完全在 NumPy 可处理范围内。
- `reghdfe` 的 MAP/LSMR 迭代求解器可作为 Phase B 的性能优化路径，不在 Phase A 阻塞最小实现。

### 2. 吸收变量处理顺序

LSDV 矩阵构造顺序（与 `AbsorbingOLS` 当前惯例一致）：

```
[constant, dummy_1, dummy_2, ..., x_variables]
```

- 每组 FE dummy **均丢弃第一水平**（参照 `areg` 惯例）。
- 在 QR 共线性检测阶段，按上述顺序确保：若 `x` 变量与 FE dummy 完美共线，则被丢弃的是 `x` 变量而非 dummy。
- 多组 FE 之间的共线性（如第一组 FE 的常数与第二组 FE 的所有 dummy 之和）通过完整 QR 分解统一处理。

### 3. `df_a` 精确公式（Phase A 范围）

Phase A 仅支持 1-2 个**纯分类**吸收变量（无 slopes、无 individual FEs）。在此范围内，`reghdfe` 的默认 `dofadjustments(all)` 行为可收束为以下显式公式：

#### 3.1 无 cluster 时
- **1 个 FE**：`df_a = G`（G 为类别数）
  - 注意：比 `areg` 多 1，因为 `reghdfe` 将常数项也视为被吸收。
- **2 个 FE（连通数据）**：`df_a = G1 + G2 - 1`
  - 对典型面板数据（如 firm + year），观测网络通常连通，mobility groups = 1，因此第二组 FE 的冗余系数为 1。

#### 3.2 有 cluster 且 cluster 嵌套于某一 FE 时
若 `cluster = var` 且其中一个吸收变量与该 cluster 变量相同或被其嵌套：
- 该 FE 的全部类别数视为冗余，`doflist_M = G`，对 `df_a` 贡献为 **0**。
- 剩余 FE 按 3.1 规则计算。

**实证验证**（`wagepan`，`absorb(nr year) vce(cluster nr)`）：
- `nr`（545 类）因与 cluster `nr` 完全嵌套，贡献 0；
- `year`（8 类）贡献 7；
- `df_a = 7`。

### 4. `df_r` 与 F 统计量

- **OLS / Robust**：`df_r = N - df_a - df_m`
- **Cluster**：`df_r = N_clust - 1`（用于 F 统计量和 t 分布的分母自由度）
  - 注意：这与 `OLS.fit(vce="cluster")` 的现有实现一致，但需确保当 cluster 变量嵌套于 FE 时，`df_a` 已正确扣减。

### 5. 默认 singleton drop 口径

`reghdfe` 默认 `drop_singletons = 1`（即不指定 `keepsingletons` 时自动剔除）。

**迭代算法**（源自 `FE.mata:init()`）：
1. 对每组 FE 依次检测 singleton（该 FE 组内只有 1 个观测的类别）。
2. 剔除该观测后，**重新从头扫描**所有 FE，因为剔除一个观测可能使其他 FE 组变为 singleton。
3. 重复直到完整一轮扫描中无任何 FE 出现新的 singleton。

**Phase A 建议**：
- 先实现**单轮迭代**（循环扫描直到无新 singleton），已覆盖绝大多数真实数据场景。
- 暂不要求与 `reghdfe` 的 `ftools` 优化路径逐行对齐，只要求结果样本量一致。

### 6. 与 FE 共线的变量自动剔除

`reghdfe` 在 partialling out 后，会检查 `x` 变量的范数是否接近 0（`check_collinear_with_fe()`）。LSDV 的等价做法是：
- 在完整 LSDV 矩阵上做 QR 分解时，若某 `x` 变量列可被 `[constant, all dummies]` 线性表出，则该 `x` 变量被标记为 collinear 并剔除。
- 典型案例：`educ`（time-invariant）在 `absorb(nr)` 时被剔除；`exper` 在 `absorb(nr year)` 时也被剔除（因 `exper` 可由 `nr` + `year` 线性组合得到）。

### 7. 常数项 `_cons` 恢复

`reghdfe` v5+ 默认在输出表中报告 `_cons`（以兼容 `margins`）。其值等于**所有 FE 组截距的未加权均值**。

在 LSDV 框架下：
- 设 full beta 向量为 `[constant, dummy_1, ..., dummy_G1-1, dummy_2, ..., dummy_G2-1, x_betas]`。
- 报告的 `_cons` = `constant + mean(all dummy_1 coefficients) + mean(all dummy_2 coefficients)`。
- 每系数的均值按**原始总类别数**（含被丢弃的第一水平，其系数视为 0）做未加权平均。

这与 `areg` 的 `_cons` 语义一致，可直接复用 `AbsorbingOLS` 的现有 `T` 矩阵变换逻辑，扩展为支持多组 FE 的线性组合。

### 8. R² 口径选择

`reghdfe` 同时报告四种 R²。Phase A 的对齐口径建议：
- **主 R²**（与 `areg` 对齐）：`R² = 1 - RSS / TSS`，其中 TSS 基于原始 `y` 的总平方和。
- **Adjusted R²**：使用 `df_r_used = N - df_a - df_m - df_a_nested`。Phase A 无 nested 修正时，`df_a_nested = 0`。
- **Within R²**：可作为额外字段报告，但不作为门禁主字段。

### 9. 源码入口速查（供实现轮参考）

| 功能 | 本地源码文件 | 关键函数/行号 |
|------|-------------|--------------|
| 主命令入口 | `src/reghdfe.ado` | `program Estimate, eclass`（L113） |
| Mata 总入口 | `current-code/reghdfe.mata` | include 顺序（L48-74） |
| FE 对象与 singleton drop | `current-code/FE.mata` | `FixedEffects::init()`（L186-385） |
| DoF 计算 | `current-code/DoF.mata` | `estimate_dof()`（L7-106） |
| 回归求解与 VCE | `current-code/Regression.mata` | `reghdfe_solve_ols()`（L8-199） |
| 共线性检测 | `current-code/Solution.mata` | `check_collinear_with_fe()`（L106-150） |
| MAP 求解器 | `current-code/MAP.mata` | `map_solver()`（L7-39） |

### 10. Phase A 功能边界最终清单

**必须支持**：
- `absorb=[var1]` 和 `absorb=[var1, var2]`（仅分类变量）
- `vce="ols"`、`vce="robust"`、单 `vce="cluster"`
- 默认自动 drop singletons（单轮迭代）
- 输出字段：`nobs`、`df_m`、`df_a`、`df_r`、`r2`、`r2_adj`、`rmse`、`F`、`b`、`se`、`cluster_count`（cluster 时）

**暂不支持（Phase B）**：
- 多聚类（multi-way clustering）
- mobility group 的复杂 pairwise DoF 修正（Phase A 使用简化公式 `df_a = G1 + G2 - 1`）
- slopes、individual FEs、team FEs
- `predict` 后估计

## 实现风险提示

1. **DoF 修正**：`reghdfe` 的 DoF 逻辑是社区命令中最复杂的部分之一。最小子集建议先用 `firstpair` 或 `none` 近似，明确记录与 Stata 的差异。**Phase A 已收束为显式公式 `df_a = G1 + G2 - 1`（无 cluster）或嵌套扣减（有 cluster），对典型面板数据足够。**
2. **Singleton Drop**：真实数据中 singleton 的迭代剔除可能影响样本量和 cluster 数量。建议先在 synthetic 样例中锁定行为，再在 real-data 中验证。
3. **常数项**：`reghdfe` v5+ 默认在输出表中加 `_cons`，但系数向量中的常数实际上由 FE 的平均值恢复而来。Python 实现需要明确是否走同样的恢复路径。**已确认：复用 `AbsorbingOLS` 的 `T` 矩阵变换，扩展为多组 FE 未加权均值。**
4. **R2 口径**：`reghdfe` 提供四种 R2（overall/within × standard/adjusted），与 `areg` 和 `xtreg` 的口径不完全一致，需在研究档案中明确记录选取的口径。**Phase A 以 overall R2 / Adjusted R2 为主对齐字段。**
