# `eventstudyinteract` 研究档案

## 命令定位

- 命令族：`DID / Event Study Extensions`
- 类型：社区贡献命令
- 规则来源：作者论文 + SSC 分发版本 + Stata 17 双跑
- 作者：Liyang Sun, Sarah Abraham
- 论文依据：[Sun & Abraham (2021) "Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects"](https://www.sciencedirect.com/science/article/pii/S0304407620303948)

## 版本与许可证信息

- **SSC 安装命令**：`ssc install eventstudyinteract`
- **当前本地版本**：通过 `ssc install eventstudyinteract` 安装（截至 2026-04-15）
- **许可证**：开源社区模块
- **Stata 最低版本要求**：未明确标注，建议 `>= 14`

## 依赖清单

| 依赖 | 用途 | 备注 |
|------|------|------|
| `avar` | 内部计算聚类稳健方差-协方差矩阵 | 已本地安装 |
| `reghdfe` | 内部高维固定效应回归引擎 | 已本地安装 |
| `ftools` | `reghdfe` 的依赖 | 已本地安装 |

## 目标 Estimand

`eventstudyinteract` 估计的是**交互加权事件研究估计量（Interaction-Weighted Event-Study Estimator）**。其目标 estimand 是在存在**异质性处理效应**和**交错处理（staggered adoption）**时，各事件时间相对期 $h$ 上的平均处理效应：

$$
\beta_h = \sum_{g} \omega_{g,h} \cdot \text{ATT}(g, h)
$$

其中 $g$ 为处理 cohort（首次处理时间），$h$ 为相对时间（$year - g$），$\omega_{g,h}$ 为交互权重，确保估计量不受异质性处理效应下的 TWFE 偏差影响。

该估计量通过将相对时间虚拟变量与 cohort 虚拟变量交互，并以控制 cohort 的占比为权重，构造出一个对异质性稳健的加权平均。

## 数据结构要求

- **面板数据**，包含单元标识 `id` 和时间标识 `year`。
- **Cohort 变量**：记录每个单元的首次处理时间（如 `first_treat`），从未处理单元可取 `0` 或其他标识。
- **相对时间变量**：用户需要**预先生成**各事件时间期的虚拟变量（如 `Dm3`, `Dm2`, `Dm1`, `D0`, `Dp1`, `Dp2`, `Dp3`）。
- **控制 cohort 标识**：需要一个二元变量标识控制组（`never_treated` 或 `not_yet_treated`），通过 `control_cohort()` 传入。

## 识别假设

1. **无预期效应（No anticipation）**：处理前不存在预期效应。
2. **平行趋势**：控制 cohort（never-treated 或 not-yet-treated）与处理 cohort 在未处理时的结果趋势平行。
3. **处理效应异质性允许**：与传统 TWFE 不同，该估计量允许不同 cohort 在不同 horizon 上具有不同的 ATT。
4. **相对时间虚拟变量已生成**：用户必须显式提供并指定基准期（通过 omit 某一期的虚拟变量实现）。

## 核心估计公式

设 $D_{i,t}^{(g,h)}$ 为 cohort $g$ 在相对时间 $h$ 的交互虚拟变量，$C_i$ 为控制 cohort 指示变量。估计方程为：

$$
Y_{it} = \sum_{h \neq h_{base}} \sum_{g} \beta_{g,h} \cdot D_{i,t}^{(g,h)} + \alpha_i + \gamma_t + \varepsilon_{it}
$$

在 `eventstudyinteract` 的实现中，上述交互项被加权聚合为 cohort-平均的事件时间系数 $\beta_h$，并在内部通过 `reghdfe` 估计。权重由各 cohort 在处理后第 $h$ 期的样本占比决定。

## 推断口径

- **标准误**：通过 `vce(cluster varname)` 指定聚类稳健标准误。由于命令内部调用 `reghdfe` 和 `avar`，聚类推断的口径与 `reghdfe` 一致。
- **常见做法**：`vce(cluster id)` 在单位层面聚类。
- **分布假设**：报告 z 统计量和基于正态分布的置信区间。

## 关键 Stata 选项

### `cohort(varname)`
- 指定 cohort 变量（即每个单元的首次处理时间）。
- 示例：`cohort(first_treat)`。

### `control_cohort(varname)`
- 指定控制 cohort 的**二元指示变量**。
- **注意**：这里传入的是一个变量名，而不是一个数值（如 `0`）。
- 示例：若已运行 `gen never_treated = first_treat == 0`，则写 `control_cohort(never_treated)`。

### `absorb(varlist)`
- 指定需要吸收的固定效应。
- 典型用法：`absorb(id year)`（单位 FE + 时间 FE）。

### `vce(cluster varname)`
- 指定聚类变量。
- 示例：`vce(cluster id)`。

## 输出字段与重点比对

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(b)` | 各相对时间期的系数向量 | 高 |
| `e(V)` | 协方差矩阵 | 高 |
| `e(N)` | 观测数 | 高 |
| `e(N_clust)` | 聚类组数 | 高（cluster 时） |

结果表直接列出各相对时间虚拟变量（如 `Dm3`, `Dm2`, `D0`, `Dp1`, ...）的系数、标准误、z 值、P>|z|、95% CI。

## Synthetic 样例设计

### `w4_eventstudyinteract_basic`
- **数据集**：手工生成 staggered adoption 面板（500 单元 × 11 年，3 个 cohort + never-treated）。
- **预生成变量**：`Dm3`, `Dm2`, `Dm1`, `D0`, `Dp1`, `Dp2`, `Dp3`，以及 `never_treated = first_treat == 0`。
- **Stata 命令**：
  ```stata
  eventstudyinteract y Dm3 Dm2 D0 Dp1 Dp2 Dp3, cohort(first_treat) control_cohort(never_treated) absorb(id year) vce(cluster id)
  ```
- **Python API**（拟定）：
  `EventStudyInteract(data, y="y", event_dummies=["Dm3","Dm2","D0","Dp1","Dp2","Dp3"], cohort="first_treat", control_cohort="never_treated", absorb=["id","year"]).fit(vce="cluster", cluster="id")`
- **风险焦点**：
  - 各 event dummy 系数与 Stata 的对齐
  - 单位+时间双向 FE 的吸收效果
  - 聚类稳健标准误与 `reghdfe`/`avar` 的一致性
  - 基准期 `Dm1` 被 omit 的语义

## Real-Data 样例设计

### `w4_eventstudyinteract_real_policy`
- **数据集**：州级或县级政策面板（待下载）。
- **预生成变量**：根据政策生效年份生成相对时间虚拟变量；生成 `control_group` 指示变量。
- **Stata 命令**：
  ```stata
  eventstudyinteract outcome Dm3 Dm2 D0 Dp1 Dp2 Dp3, cohort(adopt_year) control_cohort(never_treated) absorb(state_id year) vce(cluster state_id)
  ```
- **风险焦点**：
  - 真实数据中相对时间虚拟变量的生成与截断
  - 控制组选择（never-treated vs not-yet-treated）对系数的影响
  - 多期 FE 与聚类的组合推断

## 最小兼容子集建议

### 必须支持
- 预先生成的相对时间虚拟变量列表（event dummies）
- `cohort` 变量
- `control_cohort` 二元指示变量
- `absorb` 支持 1-2 个分类吸收变量（典型为 `id` + `year`）
- `vce(cluster)` 单聚类稳健标准误
- 结果对象：event dummy 系数、标准误、z 值、CI

### 明确不做
- 多向 cluster（multi-way clustering）
- 高级 postestimation（如自定义权重聚合、图形输出）
- `not_yet_treated` 动态控制组的自动识别（用户需预先生成控制组指示变量）
- 图形输出
