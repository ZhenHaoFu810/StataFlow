# `predict` 研究档案

## 命令定位

- 命令族：`Postestimation`
- 类型：Stata 官方 postestimation 命令
- 规则来源：官方手册 (`help predict`) + `e()` 返回值 + 双跑验证
- 版本目标：Stata 17

## 版本与许可证

- **Stata 官方命令**，随 Stata 17 分发
- 无外部依赖

## 支持的模型族与最小子集

### 线性类模型

| 模型 | `xb` | `residuals` | 说明 |
|------|------|-------------|------|
| `OLS` | 支持 | 支持 | `xb = Xβ`，含常数项（如适用） |
| `FixedEffectsOLS` | 支持 | 支持 | 基于 within 变换后的 Xβ；残差为 y - xb |
| `AbsorbingOLS` | 支持 | 支持 | 基于 LSDV 或去均值后的 Xβ；残差为 y - xb |

### 二元 / 计数类模型

| 模型 | `xb` | `pr` / `mu` | 说明 |
|------|------|-------------|------|
| `Logit` | 支持 | `pr` | `pr = Λ(xb)`，其中 `Λ(z) = 1 / (1 + exp(-z))` |
| `Probit` | 支持 | `pr` | `pr = Φ(xb)`，其中 `Φ` 为标准正态 CDF |
| `Poisson` | 支持 | `mu` | `mu = exp(xb)` |
| `PPMLHDFE` | 支持 | `mu` | `mu = exp(xb)`，注意 FE 吸收后的指数均值 |

## 输出对象与字段语义

### Python API 设计

```python
model = OLS(data, y="y", x=["x1", "x2"]).fit()
pred = model.predict(type="xb")           # 返回 np.ndarray / pd.Series
pred = model.predict(type="residuals")    # 仅线性模型

model = Logit(data, y="y", x=["x1", "x2"]).fit()
pred = model.predict(type="pr")           # 返回概率
```

### 语义规则

- **对齐样本**：`predict` 默认返回与 `fit()` 有效样本（经缺失值、共线性筛选后）长度一致的向量。
- **索引对齐**：优先返回 `pd.Series`，索引为原始 DataFrame 经筛选后的行索引；若无法对齐则返回 `np.ndarray`。
- **缺失处理**：若提供 `newdata`，对 `newdata` 中所需解释变量含缺失的行返回 `NaN`。
- **共线性处理**：`fit()` 阶段被剔除的共线性变量在 `predict` 时系数视为 0，不参与 `xb` 计算。

## 数学定义

### `xb`（线性预测 / index）

对于估计系数向量 `β`（`K × 1`，已剔除共线性变量）和解释变量矩阵 `X`（`N × K`）：

```
xb_i = x_i'β
```

- 若 `add_constant=True`，`X` 含常数列。
- 若使用 `AbsorbingOLS` 等含吸收的模型，`xb` 指**斜率部分**的线性预测，不含被吸收的 FE 水平值。

### `residuals`（残差）

仅对线性模型：

```
residuals_i = y_i - xb_i
```

注意：`FixedEffectsOLS` 的 `residuals` 基于 within 变换后的 y 与 xb；`AbsorbingOLS` 基于 LSDV 或去均值路径计算。

### `pr` / `mu`（预测概率 / 预测均值）

- **Logit**：`pr_i = 1 / (1 + exp(-xb_i))`
- **Probit**：`pr_i = Φ(xb_i)`，其中 `Φ` 由 `scipy.stats.norm.cdf` 计算
- **Poisson / PPMLHDFE**：`mu_i = exp(xb_i)`

## 推断口径

- `predict` 本身为点预测，不涉及推断。
- 标准误 (`stdp` / `stdf`) 等扩展**不在最小子集内**。

## 明确不支持的选项

以下 `predict` 子选项明确不纳入 Wave 5 最小子集：

- `stdp`（预测值标准误）
- `stdf`（预测值标准误，个体水平）
- `hat` / `cooksd` / `rstudent`（诊断统计量）
- `influence` / `score` / `dxbd()`（影响函数与得分）
- 针对 ` Heckman`、`ivregress` 等专用模型的 `predict` 特殊选项
- 图形接口或导出接口

## Synthetic 样例设计

### `w5_predict_ols_basic`

- **数据集**：手工生成横截面数据（已知系数，中等样本）
- **Stata 命令**：
  ```stata
  reg y x1 x2
  predict xb_ols, xb
  predict resid_ols, residuals
  ```
- **Python API**：
  ```python
  model = OLS(data, y="y", x=["x1", "x2"]).fit()
  xb = model.predict(type="xb")
  resid = model.predict(type="residuals")
  ```
- **风险焦点**：xb 系数还原、残差符号与数值、缺失值与常数项处理

### `w5_predict_logit_basic`

- **数据集**：手工生成二元响应数据（中等样本）
- **Stata 命令**：
  ```stata
  logit y x1 x2
  predict xb_logit, xb
  predict pr_logit, pr
  ```
- **Python API**：
  ```python
  model = Logit(data, y="y", x=["x1", "x2"]).fit()
  xb = model.predict(type="xb")
  pr = model.predict(type="pr")
  ```
- **风险焦点**：xb 与 pr 的数值转换、边界概率值（接近 0 或 1）

## Real-Data 样例设计

### `w5_predict_real_wagepan`

- **数据集**：`wagepan`（`research/data/public/panel/wooldridge/wagepan.csv`）
- **Stata 命令**：
  ```stata
  xtset nr year
  xtreg lwage educ exper expersq union, fe
  predict xb_fe, xb
  predict resid_fe, e
  ```
- **Python API**：
  ```python
  model = FixedEffectsOLS(data, y="lwage", x=["educ","exper","expersq","union"]).fit()
  xb = model.predict(type="xb")
  resid = model.predict(type="residuals")
  ```
- **风险焦点**：真实面板数据下 FE 模型的 xb 与残差对齐、time-invariant 变量 omitted 后的维度一致性

### `w5_predict_real_mroz`

- **数据集**：`Mroz`（`research/data/public/binary/mroz.csv`）
- **Stata 命令**：
  ```stata
  logit inlf nwifeinc educ exper expersq age kidslt6 kidsge6
  predict pr_mroz, pr
  predict xb_mroz, xb
  ```
- **Python API**：
  ```python
  model = Logit(data, y="inlf", x=["nwifeinc","educ","exper","expersq","age","kidslt6","kidsge6"]).fit()
  pr = model.predict(type="pr")
  xb = model.predict(type="xb")
  ```
- **风险焦点**：真实二元响应数据下概率预测、共线性变量剔除后的 xb 一致性

## 与现有代码的复用关系

| 现有组件 | 复用方式 |
|---------|---------|
| `ResultSchema.coefficients` | 提取估计系数名称与数值 |
| `OLS._prepare_data()` / `GLMBase._prepare_data()` | 复用缺失值剔除、常数项注入、共线性检测逻辑 |
| `ModelInfo.has_constant` | 判断 predict 时是否注入常数列 |
