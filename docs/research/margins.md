# `margins` 研究档案

## 命令定位

- 命令族：`Postestimation`
- 类型：Stata 官方 postestimation 命令
- 规则来源：官方手册 (`help margins`) + `e()` 返回值 + 双跑验证
- 版本目标：Stata 17

## 版本与许可证

- **Stata 官方命令**，随 Stata 17 分发
- 无外部依赖

## 支持的模型族与最小子集

### 首要覆盖模型（非线性）

| 模型 | `dydx(*)` | `atmeans` | 说明 |
|------|-----------|-----------|------|
| `Logit` | 支持 | 支持 | AME / MEM 基于 logistic CDF 导数 |
| `Probit` | 支持 | 支持 | AME / MEM 基于标准正态 PDF |
| `Poisson` | 支持 | 支持 | AME / MEM 基于指数均值 |

### 线性模型（高频子集）

| 模型 | `dydx(*)` | `atmeans` | 说明 |
|------|-----------|-----------|------|
| `OLS` | 支持 | 支持 | `dydx` 结果等于系数本身 |
| `FixedEffectsOLS` | 支持 | 支持 | `dydx` 结果等于系数本身 |
| `AbsorbingOLS` | 支持 | 支持 | `dydx` 结果等于系数本身 |

## 输出对象与字段语义

### Python API 设计

```python
model = Logit(data, y="y", x=["x1", "x2"]).fit()
marg = model.margins(type="dydx")         # 默认：Average Marginal Effect (AME)
marg = model.margins(type="atmeans")      # Marginal Effect at Means (MEM)
```

返回对象建议为 `SimpleNamespace` 或等效 dataclass，包含以下字段：

| 字段 | 类型 | 语义 |
|------|------|------|
| `params` | `dict[str, float]` | 每个解释变量的边际效应（dy/dx） |
| `bse` | `dict[str, float]` | 边际效应的标准误 |
| `tvalues` | `dict[str, float]` | z 统计量（dy/dx / SE） |
| `pvalues` | `dict[str, float]` | 双侧 p 值 |
| `conf_int` | `dict[str, tuple]` | 95% 置信区间 |
| `nobs` | `int` | 有效观测数 |

### 语义规则

- **AME（`dydx`）**：对每个观测计算边际效应，然后取样本平均。
- **MEM（`atmeans`）**：将所有解释变量取样本均值（或用户指定值），在该点计算边际效应。
- **标准误**：通过 delta-method 计算，基于估计系数的协方差矩阵 `V`。
- **常数项**：线性模型的常数项边际效应为 1（但 Stata 通常不报告 `_cons` 的 `dydx`）；非线性模型中常数项的 `dydx` 为 `g'(xb)` 的平均或均值点取值。最小子集可仅报告斜率变量的边际效应。

## 数学定义

### 平均边际效应（AME）

对解释变量 `x_k`，AME 定义为：

```
AME_k = (1/N) * Σ_i [ ∂E[y|x_i] / ∂x_{ik} ]
```

#### Logit

```
∂pr_i / ∂x_{ik} = β_k * Λ(xb_i) * (1 - Λ(xb_i))
AME_k = β_k * (1/N) * Σ_i [ p_i * (1 - p_i) ]
```

其中 `p_i = Λ(xb_i)`。

#### Probit

```
∂pr_i / ∂x_{ik} = β_k * φ(xb_i)
AME_k = β_k * (1/N) * Σ_i [ φ(xb_i) ]
```

其中 `φ(z)` 为标准正态 PDF。

#### Poisson / PPMLHDFE

```
∂μ_i / ∂x_{ik} = β_k * exp(xb_i)
AME_k = β_k * (1/N) * Σ_i [ exp(xb_i) ]
```

#### 线性模型（OLS / FE / Areg）

```
AME_k = β_k
```

因为 `∂E[y|x] / ∂x_k = β_k` 为常数，不随 `x` 变化。

### 均值点边际效应（MEM）

将所有解释变量取均值 `x̄`（含常数项 1），计算 `xb̄ = x̄'β`，则：

#### Logit

```
MEM_k = β_k * Λ(xb̄) * (1 - Λ(xb̄))
```

#### Probit

```
MEM_k = β_k * φ(xb̄)
```

#### Poisson / PPMLHDFE

```
MEM_k = β_k * exp(xb̄)
```

#### 线性模型

```
MEM_k = β_k
```

### Delta-Method 标准误

设 `g(β)` 为边际效应向量（`K × 1`），协方差矩阵为 `V = e(V)`，则边际效应的协方差矩阵为：

```
V_margins = J(β) * V * J(β)'
```

其中 `J(β) = ∂g(β) / ∂β'` 为 `K × K` Jacobian 矩阵。

对于 AME：
- `J` 的第 `(k, j)` 元素为 `∂AME_k / ∂β_j`。
- 对 Logit：`∂AME_k / ∂β_j = δ_{kj} * mean(p(1-p)) + β_k * mean(x_j * p(1-p)(1-2p))`（当 `j ≠ k` 时第二项非零）。
- 最小子集可先实现简化版：仅保留主导项 `δ_{kj} * mean(p(1-p))` 用于 diagonal SE，或完整计算 Jacobian。

**Wave 5 最小子集策略**：
- 优先实现 **MEM 的 delta-method SE**（Jacobian 结构简单，不依赖 `x` 的交叉平均）。
- AME 的 SE 可先用简化 diagonal 近似（`SE_k ≈ |mean(derivative)| * SE(β_k)`），但必须在真实数据验证中记录与 Stata 的差异来源；若差异过大，则升级到完整 Jacobian。

## 推断口径

- 汇报 z 统计量与双侧 p 值（`2 * (1 - Φ(|z|))`）。
- 默认 95% 置信区间：`dy/dx ± 1.96 * SE`。
- 不对 cluster-robust 的 margins 做小样本自由度调整（与 Stata `margins` 默认 delta-method 一致）。

## 明确不支持的选项

以下 `margins` 子选项明确不纳入 Wave 5 最小子集：

- `marginsplot`（图形输出）
- `contrast` 运算符（如 `r.` 参照对比）
- `pwcompare`（成对比较）
- 高维因子变量交互（`i.a##i.b`）的 margins 处理
- `over()` 子群 margins
- `at()` 多网格 predictive margins（仅支持单点 `atmeans`）
- `predict()` 子选项（如针对 `stdp` 的 margins）
- Bootstrap / Simulation inference（仅 delta-method）

## Synthetic 样例设计

### `w5_margins_logit_basic`

- **数据集**：手工生成二元响应数据（中等样本）
- **Stata 命令**：
  ```stata
  logit y x1 x2
  margins, dydx(*)
  margins, dydx(*) atmeans
  ```
- **Python API**：
  ```python
  model = Logit(data, y="y", x=["x1", "x2"]).fit()
  ame = model.margins(type="dydx")
  mem = model.margins(type="atmeans")
  ```
- **风险焦点**：AME 与 MEM 的数值、delta-method SE 与 Stata 对齐、常数项是否被 omit

### `w5_margins_probit_basic`

- **数据集**：同上
- **Stata 命令**：
  ```stata
  probit y x1 x2
  margins, dydx(*)
  margins, dydx(*) atmeans
  ```
- **风险焦点**：正态 PDF 在 xb 处的取值精度、AME / MEM 对齐

### `w5_margins_ols_basic`

- **数据集**：手工生成横截面数据
- **Stata 命令**：
  ```stata
  reg y x1 x2
  margins, dydx(*)
  ```
- **Python API**：
  ```python
  model = OLS(data, y="y", x=["x1", "x2"]).fit()
  ame = model.margins(type="dydx")
  ```
- **风险焦点**：线性模型 dydx 应严格等于系数、SE 应等于系数 SE

## Real-Data 样例设计

### `w5_margins_real_mroz`

- **数据集**：`Mroz`（`research/data/public/binary/mroz.csv`）
- **Stata 命令**：
  ```stata
  logit inlf nwifeinc educ exper expersq age kidslt6 kidsge6
  margins, dydx(*)
  margins, dydx(*) atmeans
  ```
- **Python API**：
  ```python
  model = Logit(data, y="inlf", x=["nwifeinc","educ","exper","expersq","age","kidslt6","kidsge6"]).fit()
  ame = model.margins(type="dydx")
  mem = model.margins(type="atmeans")
  ```
- **风险焦点**：真实二元数据下 AME / MEM 数值对齐、delta-method SE 精度、小样本中 Jacobian 完整项 vs 简化项的差异

### `w5_margins_real_crime1`

- **数据集**：`crime1`（`research/data/public/count/crime1.csv`）
- **Stata 命令**：
  ```stata
  poisson narr86 pcnv avgsen tottime ptime86 qemp86 inc86 black hispan born60
  margins, dydx(*)
  margins, dydx(*) atmeans
  ```
- **Python API**：
  ```python
  model = Poisson(data, y="narr86", x=["pcnv","avgsen","tottime","ptime86","qemp86","inc86","black","hispan","born60"]).fit()
  ame = model.margins(type="dydx")
  mem = model.margins(type="atmeans")
  ```
- **风险焦点**：计数数据下指数均值的 AME / MEM 对齐、overdispersion 不影响 margins 点估计但 delta-method SE 需与 Stata 一致

## 与现有代码的复用关系

| 现有组件 | 复用方式 |
|---------|---------|
| `ResultSchema.coefficients` | 提取系数名称 `beta` 与标准误 `std_err` |
| `ResultSchema.variance` | 提取协方差矩阵 `e(V)` 用于 delta-method |
| `predict(type="xb")` | 计算每个观测的 `xb`，作为 margins 的输入 |
| `predict(type="pr")` / `predict(type="mu")` | 计算每个观测的预测均值，用于 AME 的导数平均 |
