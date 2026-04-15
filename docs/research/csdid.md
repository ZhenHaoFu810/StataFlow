# `csdid` 研究档案

## 命令定位

- 命令族：`DID / Event Study Extensions`
- 类型：社区贡献命令
- 规则来源：作者论文 + SSC 分发版本 + Stata 17 双跑
- 作者：Brantly Callaway, Pedro H.C. Sant'Anna
- 论文依据：[Callaway & Sant'Anna (2021) "Difference-in-Differences with Multiple Time Periods"](https://www.sciencedirect.com/science/article/pii/S0304407620303948)

## 版本与许可证信息

- **SSC 安装命令**：`ssc install csdid`
- **依赖安装**：`ssc install drdid`（`csdid` 会调用 `drdid` 程序）
- **当前本地版本**：通过 `ssc install csdid, replace` 和 `ssc install drdid, replace` 安装（截至 2026-04-15）
- **许可证**：开源社区模块
- **Stata 最低版本要求**：未明确标注，建议 `>= 14`

## 依赖清单

| 依赖 | 用途 | 备注 |
|------|------|------|
| `drdid` | 内部调用以计算 doubly-robust 或回归调整估计量 | 已本地安装 |

## 目标 Estimand

`csdid` 的核心 estimand 是**组-时间平均处理效应（Group-Time ATT）**：

$$
\text{ATT}(g, t) = \mathbb{E}[Y_{i,t} - Y_{i,t}(0) \mid G_i = g]
$$

其中 $G_i = g$ 表示单元 $i$ 首次接受处理的 cohort（首次处理时间为 $g$），$t \geq g$ 为处理后的某一时点。

默认输出按 cohort（`g2004`, `g2006`, ...）和时期（`t_g_t`）组织的 `ATT(g,t)` 矩阵。

通过 post-estimation 命令 `csdid_estat event`，可进一步聚合为**事件研究动态效应**：

$$
\theta_e = \sum_{g,t: t-g=e} \omega_{g,t} \cdot \text{ATT}(g, t)
$$

其中 $e$ 为事件时间（相对处理发生时的 horizon）。

## 数据结构要求

- **面板数据**，每个单元有唯一标识 `id`（或 `ivar`）和时间标识 `time`。
- **处理变量**：`gvar(first_treat)` 指定每个单元的首次处理时间。
  - 从未处理单元取 `0`。
  - 若数据中不存在从未处理单元，命令会自动使用 **not-yet-treated** 作为对照组。
- **结果变量**：$y$（连续变量）。

## 识别假设

1. **无预期效应（No anticipation）**：处理前不存在预期行为。
2. **平行趋势（Parallel trends）**：从未处理单元（或 not-yet-treated 单元）可用于反事实推断。
3. **处理效应异质性允许**：不同 cohort 在不同时期的 ATT 可以任意不同。
4. ** positivity/overlap**：每个 cohort 在每个时期都有足够的对照组观测。

## 核心估计公式

`csdid` 默认使用 **回归调整（regression adjustment）** 方法估计 `ATT(g,t)`：

**步骤 1：估计反事实结果模型**

对每个 $(g,t)$ 组合，在**从未处理**或**尚未处理**的子样本上估计结果模型：

$$
\mathbb{E}[Y_{it}(0) \mid X_i] = \mu_g + \lambda_t + f(X_i)
$$

**步骤 2：计算组-时间 ATT**

对 cohort $g$ 在时期 $t$：

$$
\widehat{\text{ATT}}(g, t) = \frac{1}{N_g} \sum_{i: G_i=g} \left( Y_{it} - \hat{Y}_{it}(0) \right)
$$

**步骤 3：事件研究聚合（通过 `csdid_estat event`）**

按事件时间 $e = t - g$ 聚合：

$$
\hat{\theta}_e = \sum_{(g,t): t-g=e} \hat{w}_{g,t} \cdot \widehat{\text{ATT}}(g,t)
$$

权重 $\hat{w}_{g,t}$ 由样本中各 $(g,t)$ 组合的观测占比决定。

## 推断口径

- **标准误**：`csdid` 默认报告基于影响函数（influence function）的渐近标准误。
- **聚类标准误**：可通过 `vce(cluster varname)` 指定单聚类稳健推断（常见为单位层面 `cluster(id)`）。
- **分布假设**：系数报告 z 统计量与正态分布临界值下的置信区间。
- **事件研究聚合推断**：`csdid_estat event` 在聚合后重新计算标准误，考虑组-时间 ATT 之间的协方差。

## 关键 Stata 选项

### `ivar(idvar)`
- 指定单元标识变量。

### `time(timevar)`
- 指定时间标识变量。

### `gvar(first_treat_var)`
- 指定每个单元的首次处理时间变量。
- 从未处理单元应取 `0`。

### `method(string)`
- 估计方法。常见选项：
  - `drimp`（doubly robust imputation，默认或推荐）
  - `reg`（回归调整）
  - `stdipw`（stabilized IPW）
- **最小子集建议**：优先支持 `reg`（回归调整），因其在数学上最直观且与 `did_imputation` 有可比性。

### `notyet`
- 显式指定使用 **not-yet-treated** 作为对照组（而非 never-treated）。
- 若数据中无 never-treated，`csdid` 会自动回退到 not-yet-treated。

## Post-Estimation：`csdid_estat event`

运行 `csdid` 后，使用 `csdid_estat event` 提取事件研究动态效应。输出字段包括：
- `Pre_avg`：处理前平均效应
- `Post_avg`：处理后平均效应
- `Tme`：处理前 $e$ 期（如 `Tm4`, `Tm3`, `Tm2`, `Tm1`）
- `Tpe`：处理后 $e$ 期（如 `Tp0`, `Tp1`, `Tp2`）

## 输出字段与重点比对

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(b)` | 组-时间 ATT 系数向量 | 高 |
| `e(V)` | 协方差矩阵 | 高 |
| `e(N_clust)` | 聚类组数（cluster 时） | 高 |

`csdid_estat event` 的结果表需重点比对的字段：
- `Pre_avg`, `Post_avg`, `Tme`, `Tpe` 的系数
- 标准误
- z 值
- 95% 置信区间

## Synthetic 样例设计

### `w4_csdid_basic`
- **数据集**：手工生成 staggered adoption 面板（500 单元 × 11 年，3 个 cohort + never-treated）。
- **Stata 命令**：
  ```stata
  csdid y, ivar(id) time(year) gvar(first_treat)
  csdid_estat event
  ```
- **Python API**（拟定）：
  `CSDID(data, y="y", id="id", time="year", first_treat="first_treat").fit(method="reg")` 后接 `.estat_event()`
- **风险焦点**：
  - `ATT(g,t)` 系数与 Stata 的对齐
  - `csdid_estat event` 聚合后的动态效应
  - 无 never-treated 时自动回退 not-yet-treated 的行为
  - 标准误计算口径

## Real-Data 样例设计

### `w4_csdid_real_policy`
- **数据集**：州级或县级政策面板（待下载）。
- **Stata 命令**：
  ```stata
  csdid outcome, ivar(state_id) time(year) gvar(adopt_year)
  csdid_estat event
  ```
- **风险焦点**：
  - 真实数据下 `ATT(g,t)` 矩阵的维度与零值处理
  - 事件研究聚合时的有效样本量
  - 与 `did_imputation` / `eventstudyinteract` 的动态效应结果是否一致（方向与量级）

## 最小兼容子集建议

### 必须支持
- `ivar`, `time`, `gvar`（`first_treat`）三个核心变量
- `method("reg")` 回归调整方法
- `csdid_estat event` 事件研究聚合
- 单聚类稳健标准误（`vce="cluster"`, `cluster="id"`）
- 自动处理无 never-treated 的情况（回退 not-yet-treated）
- 结果对象：
  - 组-时间 ATT 矩阵
  - 事件研究动态效应（`Pre_avg`, `Post_avg`, `Tm*`, `Tp*`）

### 明确不做
- `repeated cross-section`
- `drdid` 的全部分支变体（如 `drimp`, `dripw`, `stdipw` 等一次性全开）
- bootstrap-based 推断
- 其他聚合方式（如 `csdid_estat simple`, `csdid_estat group`, `csdid_estat calendar`）
- 图形输出
