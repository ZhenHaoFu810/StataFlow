# `did_imputation` 研究档案

## 命令定位

- 命令族：`DID / Event Study Extensions`
- 类型：社区贡献命令
- 规则来源：作者论文 + SSC 分发版本 + Stata 17 对照
- 作者：Kirill Borusyak, Xavier Jaravel, Jann Spiess
- 论文依据：[Borusyak, Jaravel & Spiess (2021) "Revisiting Event Study Designs"](https://www.nber.org/papers/w29170)

## 版本与许可证信息

- **SSC 安装命令**：`ssc install did_imputation`
- **当前本地版本**：Borusyak `did_imputation` Nov 2023（M07 audit revalidation target）
- **许可证**：开源社区模块
- **Stata 最低版本要求**：未明确标注，建议 `>= 14`

## 依赖清单

| 依赖 | 用途 | 备注 |
|------|------|------|
| `reghdfe` | 内部用于高维 FE 估计（如使用 `fe` 选项时） | 已本地安装 |
| `ftools` | `reghdfe` 的依赖 | 已本地安装 |

## 目标 Estimand

`did_imputation` 的核心 estimand 是**事件时间动态处理效应**（event-study dynamic effects），即在处理发生后第 `h` 期的平均处理效应（ATT）：

$$
\tau_h = \mathbb{E}[Y_{i, g_i+h} - Y_{i, g_i+h}(0) \mid \text{treated}]
$$

其中 $g_i$ 为单元 $i$ 的首次处理时期（cohort）。

命令默认输出各 horizon `tauh` 的估计系数，使用**插补法（imputation）**：
1. 利用**从未处理单元（never-treated）**和**尚未处理单元（not-yet-treated）**估计一个双向固定效应（TWFE）模型；
2. 对每个处理单元在每个时期插补其反事实结果 $Y_{i,t}(0)$；
3. 用实际结果与插补结果的差异估计处理效应。

## Treatment-time contract

`first_treat` must use the **same units as `time`**.

| Case | Rule |
|---|---|
| Calendar `time` (e.g. 2000–2008) + relative `first_treat` (e.g. 5) | **Rejected** pre-fit with `ValueError` mentioning “same units as time” |
| Calendar `first_treat=2004` with calendar `time` | **Allowed** |
| Cohort year not present as a row (skipped period) | **Allowed** if on the same scale |
| Future cohort after max observed time | **Not** a unit-scale error (may yield no post cells) |
| Never-treated | Missing `first_treat` (Stata coding) |

Validation: `stataflow.estimators._did_time_contract.validate_treatment_time_units`.
Tests: `tests/test_compat_stata_did.py` (`time` / calendar / relative), Stata validation case `w14_did_time_contract`.

## 数据结构要求

- **面板数据**（panel data），每个单元有唯一标识 `id` 和时间标识 `time`。
- **处理变量**：必须有一个变量记录每个单元的**首次处理时间**（`first_treat`）。在当前目标 ado 中，从未处理单元取缺失值；finite `0` 或负数会被解释为实际处理 cohort，而不是 never-treated。
- **结果变量**：$y$（连续变量）。
- **近平衡面板**：命令假设面板结构足够清晰以进行 FE 插补；若存在大量缺口，可能无法 impute。

## 识别假设

1. **无预期效应（No anticipation）**：处理前各期不存在预期行为导致的效应。
2. **平行趋势（Parallel trends）**：在以单位固定效应和时间固定效应为条件的反事实结果上，处理组和对照组（never-treated + not-yet-treated）满足平行趋势。
3. **处理效应同质性不需要**：由于使用 cohort-specific 的 TWFE 插补，该估计量对异质性处理效应稳健（相对于传统 TWFE 事件研究）。

## 核心估计公式

**步骤 1：估计 TWFE 模型**

在 never-treated 和 not-yet-treated 的子样本上运行：

$$
Y_{it} = \alpha_i + \gamma_t + \varepsilon_{it}
$$

**步骤 2：插补反事实结果**

对所有观测计算：

$$
\hat{Y}_{it}(0) = \hat{\alpha}_i + \hat{\gamma}_t
$$

**步骤 3：计算处理效应**

对处理组在处理后的各 horizon $h$：

$$
\hat{\tau}_h = \frac{1}{N_h} \sum_{i: \text{treated at } h} (Y_{i, g_i+h} - \hat{Y}_{i, g_i+h}(0))
$$

其中 $N_h$ 为该 horizon 的有效样本量。

## 推断口径

- **标准误**：默认使用 OLS 标准误（基于 TWFE 残差）。
- **聚类标准误**：通过 `cluster(varname)` 选项支持单聚类稳健推断。常见做法是将 `cluster(id)` 以在单位层面聚类。
- **分布假设**：系数报告 z 统计量与正态临界值下的置信区间。
- **小样本修正**：内部基于有效样本量做调整；对无法有效 impute 的 horizon 会自动 omit 或报错。

## 关键 Stata 选项

### `allhorizons`
- 输出所有可能的事件时间 horizon。
- 不设此选项时只输出部分默认 horizon（通常从 -1 或 0 开始）。

### `cluster(varname)`
- 指定聚类变量，计算单聚类稳健标准误。
- 典型用法：`cluster(id)`。

### `autosample`
- **关键选项**。自动剔除无法插补固定效应的观测（例如：某单元仅出现在一个时期，导致无法同时估计 $\alpha_i$ 和 $\gamma_t$）。
- 在 synthetic 数据中常见；不加此选项可能报错 "Could not impute FE"。

### `minn(#)`
- 设置每个 horizon 报告系数所需的最小有效样本量。
- 低于该值的 horizon 会被 omit（系数强制为 0）。

### `window()`
- M07 revalidation found that the current target ado (Borusyak `did_imputation` Nov 2023) rejects `window()` with `option window() not allowed`.
- Stata-compatible wrapper calls therefore reject `window` explicitly.
- The Python-native estimator retains `DIDImputation.fit(window=[min, max])` as an internal horizon-filtering extension, but this is not claimed as Stata-mapped behavior for the current target ado.

## 输出字段与重点比对的 `e()` 结果

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(b)` | 系数向量（`tau0`, `tau1`, ...） | 高 |
| `e(V)` | 协方差矩阵 | 高 |
| `e(df_r)` | 残差自由度 | 中 |
| `e(N_clust)` | 聚类组数（cluster 时） | 高 |

**注意**：`did_imputation` 的结果表与传统回归表格式不同，主要报告各 `tauh` 的系数、标准误、z 值、P>|z|、95% CI。

## Synthetic 样例设计

### `w4_did_imputation_basic`
- **数据集**：手工生成 staggered adoption 面板（500 单元 × 11 年，3 个处理 cohort + never-treated）。
- **Stata 命令**：
  ```stata
  did_imputation y id year first_treat, allhorizons cluster(id) autosample
  ```
- **Python API**（拟定）：`DIDImputation(data, y="y", id="id", time="year", first_treat="first_treat").fit(cluster="id", allhorizons=True, autosample=True)`
- **风险焦点**：
  - `tauh` 系数与 Stata 的对齐
  - `autosample` 后的有效样本量
  - 单位聚类标准误
  - 无法 impute 的 horizon 是否被正确 omit

## Real-Data 样例设计

### `w4_did_imputation_real_policy`
- **数据集**：州级或县级政策面板（待下载，如 Castle Doctrine / minimum wage）。
- **Stata 命令**：
  ```stata
  did_imputation outcome state_id year policy_adopt_year, allhorizons cluster(state_id) autosample
  ```
- **Python API**：同上，绑定真实数据变量名。
- **风险焦点**：
  - 真实数据中存在缺失值、不平衡面板时的 `autosample` 行为
  - 真实政策采纳时间分布下的 horizon 截断

## 最小兼容子集建议

### 必须支持
- `id`, `time`, `first_treat` 三个核心变量
- `allhorizons` 动态效应输出
- `cluster` 单聚类标准误（常见为 `cluster(id)`）
- `autosample` 自动样本调整
- 结果对象：事件时间系数 `tauh`、标准误、z 值、置信区间

### 明确不做
- `repeated cross-section`
- 多值处理（continuous / multi-value treatment）
- `minn` 以外的复杂 aggregation 变体
- 多层 bootstrap / 随机化推断
- 图形输出
