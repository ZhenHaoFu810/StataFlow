# `areg` 研究档案

## 命令定位

- 命令族：`Panel / FE / HDFE`
- 类型：官方内建命令
- 规则来源：官方手册 + `e()` 返回值 + 双跑
- Stata 帮助入口：`help areg`

## 命令用途与典型场景

`areg` 用于线性回归中吸收（absorb）一个分类变量，将其作为固定效应从估计中剔除，但不在结果表中报告该变量的各水平系数。典型研究场景包括：

- 企业固定效应（firm fixed effects）
- 行业固定效应（industry fixed effects）
- 地区固定效应（state/province fixed effects）
- 任何只需要**单一**高维分类吸收变量的场景

与 `xtreg, fe` 的关键区别在于 `areg` 不要求数据是面板结构（不需要 `xtset`），也不要求每个组内有多个观测值。

## 与 `xtreg, fe` 的关系与差异

### 统计等价性
- 在数学上，单向固定效应的 within 估计量与 `areg` 的 LSDV（最小二乘虚拟变量）估计量是等价的。
- 系数 `b` 和方差 `V` 在无权重、无 cluster 时通常完全一致。

### 关键差异
| 维度 | `areg` | `xtreg, fe` |
|------|--------|-------------|
| 数据结构要求 | 无 panel 要求 | 需要 `xtset` |
| 常数项 | 报告 `_cons`（总体均值调整后的常数） | 默认不报告常数（within 变换后无显式常数） |
| R2 口径 | 基于 LSDV 的 overall R2 | 报告 within R2（`e(r2_w)`） |
| df_a | 报告 `e(df_a)`（吸收的 FE 数量） | 不报告 `e(df_a)` |
| FE 恢复 | 可用 `predict, d` 恢复被吸收的 FE | 可用 `predict, u` 恢复实体效应 |
| 多 FE | 只支持一个吸收变量 | 只支持单向 FE |

### 实现层面的衔接
- `areg` 可视为 `reghdfe` 的单吸收变量特例。
- 本项目的 `AbsorbingOLS` 内核也应能覆盖 `areg` 的语义。

## 关键 `e()` 返回值

| 返回值 | 含义 | 对齐优先级 |
|--------|------|------------|
| `e(N)` | 观测数 | 高 |
| `e(df_m)` | 模型自由度（斜率参数，不含常数） | 高 |
| `e(df_r)` | 残差自由度 | 高 |
| `e(df_a)` | 吸收的 FE 数量 | 高（areg 特有） |
| `e(r2)` | R-squared | 高 |
| `e(r2_a)` | Adjusted R-squared | 高 |
| `e(rmse)` | Root MSE | 高 |
| `e(F)` | F-statistic | 高 |
| `e(rss)` | Residual SS | 中 |
| `e(tss)` | Total SS | 中 |
| `e(mss)` | Model SS | 中 |
| `e(b)` | 系数向量 | 高 |
| `e(V)` | 协方差矩阵 | 高 |
| `e(wtype)` / `e(wexp)` | 权重类型与表达式 | 中 |

## 自由度与整体检验统计量

### 自由度规则
- `df_m = K`（斜率参数个数，不含常数；注意 Stata 的 `regress` 口径是 `K-1` if constant）
- `df_a = G - 1`（吸收的 FE 水平数减 1，因为有一个水平被基准组吃掉）
- `df_r = N - K - G`（残差自由度 = N - 斜率参数 - 吸收的 FE 参数）

**注意**：`reghdfe` 的 `df_a` 与 `areg` 相差 1（`reghdfe` 把常数也计入吸收，导致 `df_a` 比 `areg` 多 1）。这是已知的、有文献记录的区别。

### F-statistic
- `areg` 报告的 `e(F)` 是对所有**非吸收**斜率系数联合显著性的 Wald F 检验。
- 分母使用 `e(df_r)`。

## Synthetic 样例设计

### `p3_areg_basic`
- **数据集**：基于 `sysuse auto` 或手工生成数据
- **Stata 命令**：`areg price weight length, absorb(turn)`
- **Python API**：`AbsorbingOLS(data, y="price", x=["weight", "length"], absorb="turn").fit()`
- **风险焦点**：
  - 系数与 `regress` + turn dummies 是否一致
  - `df_a` 是否正确
  - `_cons` 的符号与数值
  - R2 是基于 overall 还是 within

### `p3_areg_cluster`
- **数据集**：同上
- **Stata 命令**：`areg price weight length, absorb(turn) cluster(foreign)`
- **Python API**：同上 + `vce="cluster", cluster="foreign"`
- **风险焦点**：
  - cluster-robust SE 与 `reghdfe` 的 `keepsingletons` 结果是否一致
  - 小样本修正因子

## Real-Data 样例设计

### `p3_areg_real_panel`
- **数据集**：`wagepan`（`research/data/public/panel/wooldridge/wagepan.csv`）
- **Stata 命令**：`areg lwage educ exper expersq union, absorb(nr)`
- **Python API**：`AbsorbingOLS(data, y="lwage", x=["educ","exper","expersq","union"], absorb="nr").fit()`
- **风险焦点**：真实面板数据下的 FE 吸收、缺失值处理、与 `xtreg, fe` 的系数一致性

### `p3_areg_real_grunfeld`
- **数据集**：`Grunfeld`（`research/data/public/panel/grunfeld.csv`）
- **Stata 命令**：`areg invest mvalue kstock, absorb(company)`
- **风险焦点**：非平衡 panel 下的吸收效果、与 `xtreg, fe` 的差异

## 最小实现子集建议

建议 `areg` 的最小公开兼容层至少支持：

1. **吸收变量**：单一分类变量（`absorb=`）
2. **协方差类型**：`vce="ols"`、`vce("robust")`、`vce(cluster varname)`
3. **权重**：`aweight`（如有余力再扩展 `fweight`/`pweight`）
4. **常数项**：默认报告 `_cons`（与 `areg` 一致）
5. **结果字段**：完整 `ResultSchema`，含 `df_a`（放入 `diagnostics` 或 `fit` 的扩展字段）

**暂不纳入最小子集**：
- 多吸收变量（交给 `reghdfe`）
- `predict, d`（FE 恢复，属于 Postestimation）
- 复杂因子交互
