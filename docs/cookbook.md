# Stata2Python (statapy) 中文使用手册

> **面向 Stata 用户的 Python 计量经济学工具包**
>
> 本文档假设你已经熟悉 Stata 的计量命令，但刚接触 Python / pandas。
> 所有示例均可直接复制运行。

---

## 目录

1. [安装与导入](#1-安装与导入)
2. [核心概念：从 Stata 到 Python](#2-核心概念从-stata-到-python)
3. [线性回归](#3-线性回归)
4. [工具变量与 2SLS](#4-工具变量与-2sls)
5. [非线性模型](#5-非线性模型)
6. [双重差分 (DID) 与事件研究](#6-双重差分-did-与事件研究)
7. [断点回归 (RD)](#7-断点回归-rd)
8. [因子变量与交互项](#8-因子变量与交互项)
9. [Stata 迁移常见问题](#9-stata-迁移常见问题)
10. [结果对象详解](#10-结果对象详解)

---

## 1. 安装与导入

```bash
pip install -e .
```

```python
import pandas as pd
import numpy as np

# 导入所有 Stata 兼容命令
from statapy.compat.stata import (
    regress, areg, xtreg_fe, reghdfe,
    ivregress_2sls, ivreghdfe,
    logit, probit, poisson, ppmlhdfe,
    did_imputation, eventstudyinteract, csdid,
    rdrobust,
)
```

**Stata 对应**：相当于 Stata 的 `use "data.dta", clear` + 各种 `regress` / `reghdfe` 命令。

---

## 2. 核心概念：从 Stata 到 Python

### 2.1 数据框 (`pd.DataFrame`) 就是 Stata 内存

在 Stata 里，数据始终在内存中。在 Python 里，数据存放在 `pd.DataFrame` 中：

```python
# 读取 Stata 数据
df = pd.read_stata("mydata.dta")

# 读取 CSV
df = pd.read_csv("mydata.csv")

# 查看数据（类似 Stata 的 browse / list）
print(df.head(10))        # 前 10 行
print(df.describe())      # 描述统计
```

### 2.2 命令参数对比

| Stata 语法 | statapy 语法 | 说明 |
|-----------|-------------|------|
| `reg y x1 x2` | `regress(df, y="y", x=["x1", "x2"])` | 列表用方括号 `[]` |
| `absorb(firm year)` | `absorb="firm year"` 或 `absorb=["firm", "year"]` | 字符串或列表均可 |
| `cluster(state)` | `cluster="state"` | 字符串 |
| `vce(robust)` | `vce="robust"` | 字符串 |
| `i.group` | `x=["i.group"]` | 在 x 列表中使用因子语法 |
| `c.x1##c.x2` | `x=["c.x1##c.x2"]` | 连续变量交互项 |

### 2.3 结果如何查看

Stata 的结果直接输出在屏幕上。statapy 返回一个 **结果对象**，你需要主动打印：

```python
result = regress(df, y="y", x=["x1", "x2"], vce="robust")

# 遍历所有系数
for c in result.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  t={c.t_stat:.4f}")

# 样本信息
print(f"观测值: {result.sample.nobs}")
print(f"R-squared: {result.fit.r2:.4f}")
```

---

## 3. 线性回归

### 3.1 普通最小二乘 (OLS) — `regress`

```python
# 基础 OLS
result = regress(df, y="y", x=["x1", "x2"])

# 稳健标准误
result = regress(df, y="y", x=["x1", "x2"], vce="robust")

# 聚类标准误
result = regress(df, y="y", x=["x1", "x2"], vce="cluster", cluster="state")

# 不加常数项
result = regress(df, y="y", x=["x1", "x2"], noconstant=True)

# 加权回归 (aweight)
result = regress(df, y="y", x=["x1", "x2"], aweight="w")
```

**Stata 对应**：
```stata
reg y x1 x2
reg y x1 x2, robust
reg y x1 x2, cluster(state)
reg y x1 x2, noconstant
reg y x1 x2 [aw=w]
```

### 3.2 固定效应 — `xtreg, fe` / `areg`

```python
# 单固定效应（组内估计量）— 类似 xtreg, fe
result = xtreg_fe(df, y="y", x=["x1", "x2"], fe="firm_id", vce="robust")

# 单吸收变量 — 类似 areg
result = areg(df, y="y", x=["x1", "x2"], absorb="firm_id", vce="cluster", cluster="state")
```

**Stata 对应**：
```stata
xtreg y x1 x2, fe robust
areg y x1 x2, absorb(firm_id) cluster(state)
```

### 3.3 高维固定效应 — `reghdfe`

```python
# 双向固定效应
result = reghdfe(
    df,
    y="y",
    x=["x1", "x2", "treat"],
    absorb="firm_id year",        # 字符串形式，空格分隔
    vce="cluster",
    cluster="state",
)

# 或者使用列表
result = reghdfe(
    df,
    y="y",
    x=["x1", "x2"],
    absorb=["firm_id", "year"],   # 列表形式
    vce="robust",
)

# 保留 singleton（不删除仅出现一次的观测）
result = reghdfe(
    df, y="y", x=["x1"],
    absorb="firm_id",
    keepsingletons=True,
)

# 不加常数项
result = reghdfe(
    df, y="y", x=["x1"],
    absorb="firm_id",
    noconstant=True,
)
```

**Stata 对应**：
```stata
reghdfe y x1 x2 treat, absorb(firm_id year) vce(cluster state)
reghdfe y x1 x2, absorb(firm_id year) robust
reghdfe y x1, absorb(firm_id) keepsingletons
reghdfe y x1, absorb(firm_id) noconstant
```

### 3.4 完整示例：合成数据上的 OLS

```python
import numpy as np
import pandas as pd
from statapy.compat.stata import regress

rng = np.random.default_rng(42)
n = 200

df = pd.DataFrame({
    "y": rng.normal(0, 1, n),
    "x1": rng.normal(0, 1, n),
    "x2": rng.normal(0, 1, n),
    "cluster_id": rng.integers(1, 21, size=n),
})

# OLS + 稳健标准误
result = regress(df, y="y", x=["x1", "x2"], vce="robust")
for c in result.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  t={c.t_stat:.4f}")
```

### 3.5 完整示例：双向固定效应

```python
import numpy as np
import pandas as pd
from statapy.compat.stata import reghdfe

rng = np.random.default_rng(42)
n_units, n_periods = 100, 5
n = n_units * n_periods

df = pd.DataFrame({
    "y": rng.normal(0, 1, n),
    "x1": rng.normal(0, 1, n),
    "treat": np.tile([0, 0, 1, 1, 1], n_units),
    "unit_id": np.repeat(np.arange(n_units), n_periods),
    "period": np.tile(np.arange(n_periods), n_units),
    "cluster_id": np.repeat(rng.integers(1, 21, size=n_units), n_periods),
})

result = reghdfe(
    df,
    y="y",
    x=["x1", "treat"],
    absorb="unit_id period",
    vce="cluster",
    cluster="cluster_id",
)

for c in result.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  t={c.t_stat:.4f}")
```

---

## 4. 工具变量与 2SLS

### 4.1 两阶段最小二乘 — `ivregress 2sls`

```python
from statapy.compat.stata import ivregress_2sls

result = ivregress_2sls(
    df,
    y="y",
    x_exog=["x1"],           # 外生变量
    x_endog=["x2"],          # 内生变量
    instruments=["z1", "z2"], # 工具变量
    vce="robust",
)
```

**Stata 对应**：
```stata
ivregress 2sls y x1 (x2 = z1 z2), robust
```

### 4.2 IV + 高维固定效应 — `ivreghdfe`

```python
from statapy.compat.stata import ivreghdfe

result = ivreghdfe(
    df,
    y="y",
    x_exog=["x1"],
    x_endog=["x2"],
    instruments=["z1"],
    absorb="firm_id year",
    vce="cluster",
    cluster="state",
)
```

**Stata 对应**：
```stata
ivreghdfe y x1 (x2 = z1), absorb(firm_id year) cluster(state)
```

### 4.3 完整示例

```python
import numpy as np
import pandas as pd
from statapy.compat.stata import ivregress_2sls

rng = np.random.default_rng(42)
n = 300

z = rng.normal(0, 1, n)
u = rng.normal(0, 1, n)
x_endog = 0.5 * z + u + rng.normal(0, 0.5, n)
x_exog = rng.normal(0, 1, n)
y = 1.0 + 0.8 * x_endog + 0.3 * x_exog + u

df = pd.DataFrame({
    "y": y, "x_exog": x_exog, "x_endog": x_endog,
    "z1": z, "z2": z + rng.normal(0, 0.3, n),
})

result = ivregress_2sls(
    df, y="y",
    x_exog=["x_exog"], x_endog=["x_endog"],
    instruments=["z1", "z2"], vce="robust",
)

for c in result.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  t={c.t_stat:.4f}")
```

---

## 5. 非线性模型

### 5.1 Logit / Probit

```python
from statapy.compat.stata import logit, probit

# Logit
result = logit(df, y="y_binary", x=["x1", "x2"], vce="robust")

# Probit
result = probit(df, y="y_binary", x=["x1", "x2"], vce="cluster", cluster="firm_id")

# 不加常数项
result = logit(df, y="y_binary", x=["x1"], noconstant=True)
```

**Stata 对应**：
```stata
logit y_binary x1 x2, robust
probit y_binary x1 x2, cluster(firm_id)
```

### 5.2 Poisson

```python
from statapy.compat.stata import poisson

result = poisson(df, y="count_y", x=["x1", "x2"], vce="robust")

# 不加常数项
result = poisson(df, y="count_y", x=["x1"], noconstant=True)
```

**注意**：`offset` 和 `exposure` 在当前版本中尚未支持。

### 5.3 PPML + 高维固定效应 — `ppmlhdfe`

```python
from statapy.compat.stata import ppmlhdfe

result = ppmlhdfe(
    df,
    y="count_y",
    x=["x1", "x2"],
    absorb="firm_id year",
    vce="cluster",
    cluster="state",
)

# 迭代控制
result = ppmlhdfe(
    df, y="count_y", x=["x1"], absorb="firm_id",
    maxiter=200, tolerance=1e-10,
)
```

**Stata 对应**：
```stata
ppmlhdfe count_y x1 x2, absorb(firm_id year) vce(cluster state)
```

### 5.4 完整示例：Logit

```python
import numpy as np
import pandas as pd
from statapy.compat.stata import logit

rng = np.random.default_rng(42)
n = 500

x1 = rng.normal(0, 1, n)
x2 = rng.normal(0, 1, n)
latent = 0.5 + 1.0 * x1 - 0.5 * x2 + rng.normal(0, 1, n)
y_binary = (latent > 0).astype(int)

df = pd.DataFrame({"y_binary": y_binary, "x1": x1, "x2": x2})

result = logit(df, y="y_binary", x=["x1", "x2"], vce="robust")
for c in result.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  z={c.t_stat:.4f}")
```

---

## 6. 双重差分 (DID) 与事件研究

### 6.1 Borusyak-Jaravel-Spiess 插补估计量 — `did_imputation`

```python
from statapy.compat.stata import did_imputation

result = did_imputation(
    df,
    y="y",
    id="unit_id",
    time="year",
    first_treat="first_treat_year",
    cluster="state",
    allhorizons=True,   # 估计所有时期效应
    autosample=True,    # 自动样本选择
)

for c in result.coefficients:
    print(f"{c.name:15s} beta={c.beta: .4f} se={c.std_err:.4f}")
```

**Stata 对应**：
```stata
did_imputation y unit_id year first_treat_year, cluster(state) allhorizons autosample
```

### 6.2 Sun-Abraham 交互加权估计量 — `eventstudyinteract`

有两种使用模式：

**模式 A：自动生成事件时间虚拟变量**

```python
result = eventstudyinteract(
    df,
    y="y",
    cohort="treat_group",
    control_cohort="control_group",
    time="year",
    first_treat="first_treat",
    horizons=[-3, -2, -1, 0, 1, 2, 3],
    omit=-1,                    # 以 -1 期为参照
    absorb=["unit_id", "year"],
    vce="cluster",
    cluster="state",
)
```

**模式 B：使用预生成的事件时间虚拟变量**

```python
# 假设你已经手动创建了 Dm3, Dm2, D0, Dp1, Dp2, Dp3
df["Dm3"] = (df["rel_time"] == -3).astype(float)
df["Dm2"] = (df["rel_time"] == -2).astype(float)
df["D0"]  = (df["rel_time"] == 0).astype(float)
df["Dp1"] = (df["rel_time"] == 1).astype(float)
# ... 以此类推

result = eventstudyinteract(
    df,
    y="y",
    cohort="treat_group",
    control_cohort="control_group",
    event_dummies=["Dm3", "Dm2", "D0", "Dp1", "Dp2", "Dp3"],
    absorb=["unit_id", "year"],
    vce="cluster",
    cluster="state",
)
```

**Stata 对应**：
```stata
eventstudyinteract y cohort control_cohort, cohort(first_treat) control_cohort(never_treat) absorb(unit_id year) cluster(state)
```

### 6.3 Callaway-Sant'Anna DID — `csdid`

```python
from statapy.compat.stata import csdid

result = csdid(
    df,
    y="y",
    id="unit_id",
    time="year",
    first_treat="first_treat_year",
    method="reg",           # 仅支持 regression-adjustment
    cluster="state",
)

# result 已经是 estat_event 的聚合结果
for c in result.coefficients:
    print(f"{c.name:15s} beta={c.beta: .4f} se={c.std_err:.4f}")
```

**Stata 对应**：
```stata
csdid y, ivar(unit_id) time(year) gvar(first_treat_year) method(drimp)
csdid_estat event
```

**注意**：当前仅支持 `method="reg"`。`drimp`、`dripw` 等方法尚未实现。

---

## 7. 断点回归 (RD)

### 7.1 清晰断点回归 — `rdrobust`

```python
from statapy.compat.stata import rdrobust

# 显式带宽
result = rdrobust(df, y="vote", x="margin", c=0.0, h=15.0)

# 自动带宽选择 (mserd)
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="mserd")

# 加入协变量
result = rdrobust(
    df, y="vote", x="margin", c=0.0,
    bwselect="mserd", covs="z",
)

# 不同核函数和 VCE
result = rdrobust(
    df, y="vote", x="margin", c=0.0, h=15.0,
    kernel="uniform", vce="hc0",
)
```

**Stata 对应**：
```stata
rdrobust vote margin, c(0) h(15)
rdrobust vote margin, c(0) bwselect(mserd)
rdrobust vote margin, c(0) covs(z)
rdrobust vote margin, c(0) h(15) kernel(uniform) vce(hc0)
```

### 7.2 读取 RD 结果

```python
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="mserd")

# 系数
print("Conventional:", result.coefficients[0].beta)
print("Bias-Corrected:", result.coefficients[1].beta)
print("Robust:", result.coefficients[2].beta)

# 带宽和样本信息（存储在 _rd_extras 中）
extra = result._rd_extras
print(f"带宽 h = {extra['h_l']:.3f}")
print(f"偏差带宽 b = {extra['b_l']:.3f}")
print(f"左侧有效样本 = {extra['N_h_l']}")
print(f"右侧有效样本 = {extra['N_h_r']}")
```

### 7.3 完整示例

```python
import pandas as pd
from statapy.compat.stata import rdrobust

# 使用 rdrobust 自带的数据
df = pd.read_stata(
    "research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta"
)

result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="mserd")
print(f"RD 效应 (Robust) = {result.coefficients[2].beta:.4f}")
print(f"标准误 = {result.coefficients[2].std_err:.4f}")
```

---

## 8. 因子变量与交互项

statapy 支持 Stata 风格的 **因子变量语法**，你可以在 `x` 参数列表中直接使用它们。

### 8.1 虚拟变量（分类变量）

```python
# i.group 生成 group 的虚拟变量，省略基组
result = regress(df, y="y", x=["x1", "i.group"])

# 指定基组为第 2 类
result = regress(df, y="y", x=["x1", "ib2.group"])

# 省略第 3 类
result = regress(df, y="y", x=["x1", "o3.group"])
```

**Stata 对应**：
```stata
reg y x1 i.group
reg y x1 ib2.group
reg y x1 o3.group
```

### 8.2 连续变量 × 连续变量

```python
# 仅交互项
result = regress(df, y="y", x=["x1", "x2", "c.x1#c.x2"])

# 主效应 + 交互项（等价于 x1 + x2 + x1*x2）
result = regress(df, y="y", x=["c.x1##c.x2"])
```

**Stata 对应**：
```stata
reg y x1 x2 c.x1#c.x2
reg y c.x1##c.x2
```

### 8.3 分类变量 × 分类变量

```python
# 仅交互项
result = regress(df, y="y", x=["i.group1#i.group2"])

# 主效应 + 交互项
result = regress(df, y="y", x=["i.group1##i.group2"])
```

**Stata 对应**：
```stata
reg y i.group1#i.group2
reg y i.group1##i.group2
```

### 8.4 分类变量 × 连续变量

```python
# 仅交互项（允许不同组的 x1 斜率不同）
result = regress(df, y="y", x=["i.group#c.x1"])

# 主效应 + 交互项
result = regress(df, y="y", x=["i.group##c.x1"])
```

**Stata 对应**：
```stata
reg y i.group#c.x1
reg y i.group##c.x1
```

### 8.5 裸变量在 # / ## 中视为连续

```python
# 以下两种写法等价
result = regress(df, y="y", x=["c.x1##c.x2"])
result = regress(df, y="y", x=["x1##x2"])   # 裸变量在 # 内被视为连续
```

### 8.6 不支持的功能（会报错）

以下语法会触发 `ValueError`：

- `ib.group`（未指定基组层级）
- `L.x` / `F.x`（时间序列算子）
- 三向或更高阶交互（如 `i.g1#i.g2#c.x3`）

---

## 9. Stata 迁移常见问题

### Q1: 为什么 `regress(df, y="y", x="x1")` 报错？

**A**: `x` 参数必须是 **列表**（list），即使只有一个变量：

```python
# ❌ 错误
result = regress(df, y="y", x="x1")

# ✅ 正确
result = regress(df, y="y", x=["x1"])
```

### Q2: 如何表示交互项？

**A**: 使用 Stata 因子语法，直接写在 `x` 列表中：

```python
# ✅ 推荐：使用因子语法
result = regress(df, y="y", x=["x1", "x2", "c.x1#c.x2"])

# ❌ 不要手动创建交互列（除非你需要自定义）
df["x1_x2"] = df["x1"] * df["x2"]
result = regress(df, y="y", x=["x1", "x2", "x1_x2"])  # 可以运行，但不推荐
```

### Q3: `absorb` 怎么写？

**A**: 支持 **字符串**（空格分隔）或 **列表**：

```python
# 两种写法等价
result = reghdfe(df, y="y", x=["x1"], absorb="firm year")
result = reghdfe(df, y="y", x=["x1"], absorb=["firm", "year"])
```

### Q4: 如何查看 R-squared、F 统计量？

**A**: 结果对象中存储了这些信息：

```python
result = regress(df, y="y", x=["x1", "x2"])

print(f"R-squared:     {result.fit.r2:.4f}")
print(f"调整 R-squared: {result.fit.r2_a:.4f}")
print(f"F 统计量:       {result.fit.f_statistic:.2f}")
print(f"F p-value:      {result.fit.f_pvalue:.4f}")
print(f"模型自由度:      {result.fit.df_model:.0f}")
print(f"残差自由度:      {result.fit.df_resid:.0f}")
```

### Q5: 结果里的 `t_stat` 到底是 t 还是 z？

**A**: `t_stat` 字段在 OLS 下是 t 统计量，在 Logit / Probit / Poisson / PPML 下是 z 统计量（大样本正态近似）。这是为了兼容不同估计族的惯例。对应的 `p_value` 和置信区间始终使用正确的分布。

### Q6: 为什么某些 Stata 选项不被支持？

**A**: statapy 对未实现的参数采取 **hard-reject** 策略（抛出 `ValueError` 或 `NotImplementedError`），而不是静默忽略。这能防止你得到错误的结果。如果你遇到了不支持的参数，请：

1. 查阅 `docs/command-support-matrix/` 中对应命令的支持矩阵。
2. 检查是否可以用其他方式实现（例如手动生成虚拟变量）。

### Q7: 聚类标准误只能有一层吗？

**A**: 是的，当前版本仅支持 **单层聚类**（`cluster="state"`）。多层聚类（如 `cluster(state year)`）尚未实现。

### Q8: 如何保存结果到文件？

**A**: Python 的结果对象可以用 pandas 导出：

```python
import pandas as pd

# 提取系数为 DataFrame
coef_df = pd.DataFrame([
    {"var": c.name, "beta": c.beta, "se": c.std_err,
     "t": c.t_stat, "p": c.p_value, "ci_low": c.ci_low, "ci_high": c.ci_high}
    for c in result.coefficients
])

# 保存为 CSV
coef_df.to_csv("regression_results.csv", index=False)

# 保存为 Stata 数据
coef_df.to_stata("regression_results.dta", write_index=False)
```

---

## 10. 结果对象详解

所有 `compat.stata` 命令都返回一个 **ResultSchema** 对象，包含以下主要字段：

### 10.1 模型信息 (`result.model`)

| 字段 | 说明 |
|------|------|
| `result.model.command` | 命令名称，如 `"regress"`、`"reghdfe"` |
| `result.model.estimator_family` | 估计族，如 `"ols"`、`"glm"`、`"rd"` |
| `result.model.vcetype` | 方差估计类型，如 `"robust"`、`"cluster"` |
| `result.model.has_constant` | 是否包含常数项 |

### 10.2 样本信息 (`result.sample`)

| 字段 | 说明 |
|------|------|
| `result.sample.nobs` | 最终使用的观测值数量 |
| `result.sample.n_input_rows` | 输入数据的原始行数 |

### 10.3 拟合信息 (`result.fit`)

| 字段 | 说明 |
|------|------|
| `result.fit.r2` | R-squared |
| `result.fit.r2_a` | 调整 R-squared |
| `result.fit.f_statistic` | F 统计量 |
| `result.fit.f_pvalue` | F 检验 p 值 |
| `result.fit.df_model` | 模型自由度 |
| `result.fit.df_resid` | 残差自由度 |
| `result.fit.df_a` | 吸收的自由度（仅 HDFE 命令） |

### 10.4 系数 (`result.coefficients`)

这是一个列表，每个元素包含：

| 字段 | 说明 |
|------|------|
| `c.name` | 变量名 |
| `c.beta` | 估计系数 |
| `c.std_err` | 标准误 |
| `c.t_stat` | t / z 统计量 |
| `c.p_value` | p 值 |
| `c.ci_low` | 置信区间下限 |
| `c.ci_high` | 置信区间上限 |

```python
# 示例：打印完整的回归表
print(f"{'Variable':<15} {'Coef.':>10} {'Std.Err.':>10} {'t':>8} {'P>|t|':>8} {'[95% CI]':>20}")
print("-" * 75)
for c in result.coefficients:
    print(f"{c.name:<15} {c.beta:>10.4f} {c.std_err:>10.4f} "
          f"{c.t_stat:>8.2f} {c.p_value:>8.4f} [{c.ci_low:>8.4f}, {c.ci_high:>8.4f}]")
```

### 10.5 特殊结果字段

某些命令有额外的结果字段：

- **DID / Event Study**: `result._event_horizons` 存储各期效应的时间点。
- **RD**: `result._rd_extras` 存储带宽、有效样本、tau_cl、tau_bc 等。

---

## 附录：命令速查表

| Stata 命令 | statapy 函数 | 状态 |
|-----------|-------------|------|
| `regress` | `regress()` | Stable |
| `xtreg, fe` | `xtreg_fe()` | Stable |
| `areg` | `areg()` | Stable |
| `reghdfe` | `reghdfe()` | Alpha |
| `ivregress 2sls` | `ivregress_2sls()` | Stable |
| `ivreghdfe` | `ivreghdfe()` | Alpha |
| `logit` | `logit()` | Stable |
| `probit` | `probit()` | Stable |
| `poisson` | `poisson()` | Stable |
| `ppmlhdfe` | `ppmlhdfe()` | Alpha |
| `did_imputation` | `did_imputation()` | Alpha |
| `eventstudyinteract` | `eventstudyinteract()` | Alpha |
| `csdid` | `csdid()` | Alpha |
| `rdrobust` | `rdrobust()` | Alpha — Partial |

---

*本文档最后更新于 2026-04-18。有关各命令的详细支持参数和已知限制，请参阅 `docs/command-support-matrix/`。*
