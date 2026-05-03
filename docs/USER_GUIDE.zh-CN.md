# StataFlow 用户手册

## 1. 什么是 StataFlow？

StataFlow（`stataflow`）是一个 Python 计量经济学工具包，目标是高精度复现 **Stata 17** 的估计结果。它面向希望用 Python 做计量分析的科研人员、数据分析师和经济学者。

StataFlow 提供**两层使用方式**：

- **`stataflow.compat.stata`** — Stata 风格命令函数（`regress()`、`reghdfe()`、`logit()` 等）。推荐大多数用户使用，语法与 Stata 高度相似。
- **`stataflow`（核心 estimator）** — Python 原生 estimator 类（`OLS`、`Logit`、`PPMLHDFE` 等）。面向需要编程式控制、后估计分析及与 Python 数据管道集成的进阶用户。

每个对外命令都通过 **dual-run 测试** 验证：在相同的合成数据和真实数据集上分别运行 Stata 17 和 Python，对系数、标准误、t 统计量和拟合统计量进行字段级比对。

## 2. 安装

**环境要求：** Python 3.10+、NumPy、pandas、SciPy。

```bash
pip install StataFlow
```

从源码安装（开发者）：

```bash
git clone https://github.com/ZhenHaoFu810/StataFlow.git
cd StataFlow
pip install -e .
```

**验证安装：**

```python
import stataflow
print(stataflow.__version__)  # 例如 "1.0.0"
```

> 仅当需要本地运行 golden dual-run 测试时才需安装 Stata 17。包本身在正常使用中不依赖 Stata。

## 3. 核心概念：从 Stata 到 Python

### 3.1 DataFrame 替代 Stata 的内存数据

Stata 中数据 `use` 后就放在内存里，Python 中放在 `pd.DataFrame` 中：

```python
import pandas as pd

df = pd.read_stata("mydata.dta")  # 读取 Stata 数据
df = pd.read_csv("mydata.csv")    # 读取 CSV

df.head(10)      # 查看前 10 行（类似 browse）
df.describe()    # 描述统计（类似 summarize）
```

### 3.2 命令参数对比

| Stata 语法 | StataFlow (Python) | 说明 |
|---|---|---|
| `reg y x1 x2` | `regress(df, y="y", x=["x1", "x2"])` | `x` 必须是列表 |
| `reg y x1 x2, robust` | `regress(df, y="y", x=["x1", "x2"], vce="robust")` | |
| `reg y x1 x2, cluster(id)` | `regress(df, y="y", x=["x1", "x2"], vce="cluster", cluster="id")` | |
| `absorb(firm year)` | `absorb="firm year"` 或 `absorb=["firm", "year"]` | 两种形式均可 |
| `i.group##c.x` | `x=["i.group##c.x"]` | 因子语法支持 |
| `[aw=w]` | `aweight="w"` | 仅支持分析权重 |

### 3.3 读取结果

所有命令返回 `ResultSchema` 对象。最简单的查看方式：

```python
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")

# 一键输出 Stata 风格回归表
result.display()

# 含 95% 置信区间
result.display(show_ci=True)

# 获取字符串（用于日志、保存等）
text = result.summary()
```

程序化访问：

```python
for c in result.coefficients:
    print(f"{c.name}: b={c.beta:.6f}, se={c.std_err:.6f}, t={c.t_stat:.2f}, p={c.p_value:.3f}")

print(f"R2 = {result.fit.r2:.4f}")
print(f"F({int(result.fit.df_model)}, {int(result.fit.df_resid)}) = {result.fit.f_stat:.2f}")
print(f"N = {result.sample.nobs}")

# 在 Jupyter/IPython 中，直接输入变量名
result  # 调用 __repr__ → 显示回归表
```

## 4. 你的第一个模型（5 分钟）

```python
import pandas as pd
import numpy as np
from stataflow.compat.stata import regress

# 1. 构造数据
rng = np.random.default_rng(42)
df = pd.DataFrame({
    "wage": 5 + 1.5 * rng.normal(0, 1, 500) + rng.normal(0, 0.5, 500),
    "edu": rng.normal(12, 3, 500),
    "exper": rng.normal(10, 5, 500),
    "state": rng.choice(["CA", "TX", "NY", "FL"], 500),
})

# 2. 简单 OLS（缺失值自动处理）
result = regress(df, y="wage", x=["edu", "exper"])

# 3. 稳健标准误
result_r = regress(df, y="wage", x=["edu", "exper"], vce="robust")

# 4. 聚类标准误
result_c = regress(df, y="wage", x=["edu", "exper"],
                    vce="cluster", cluster="state")

# 5. 导出为 pandas DataFrame
coef_df = pd.DataFrame([
    {"var": c.name, "beta": c.beta, "se": c.std_err,
     "t": c.t_stat, "p": c.p_value}
    for c in result_r.coefficients
])
coef_df.to_csv("results.csv", index=False)
```

## 5. 命令选择指南

| 想做... | 使用命令 | 状态 |
|---|---|---|
| 简单 OLS 回归 | `regress()` | Stable |
| 控制一个固定效应 | `areg()` 或 `xtreg_fe()` | Stable |
| 控制多个固定效应 (HDFE) | `reghdfe()` | Beta |
| 工具变量 2SLS | `ivregress_2sls()` | Stable |
| IV + 多个固定效应 | `ivreghdfe()` | Beta |
| 二元结果 (0/1) | `logit()` 或 `probit()` | Stable |
| 计数数据 | `poisson()` | Stable |
| 计数 + 多个固定效应 | `ppmlhdfe()` | Beta |
| 交错处理 DID | `did_imputation()`、`csdid()`、`eventstudyinteract()` | Beta |
| 断点回归 (RD) | `rdrobust()` | Beta |

详细参数支持范围请参阅 [命令支持矩阵](./command-support-matrix/README.md)。

## 6. 两层使用方式

### 6.1 Stata 风格命令层（推荐）

```python
from stataflow.compat.stata import regress, reghdfe, logit, ivregress_2sls

result = regress(df, y="wage", x=["edu", "exper"], vce="robust")
result = reghdfe(df, y="wage", x=["edu", "exper"],
                 absorb="firm_id year", vce="cluster", cluster="state")
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
result = ivregress_2sls(df, y="lwage", x_exog=["edu"],
                         x_endog=["exper"], instruments=["age", "kidslt6"],
                         vce="robust")
```

返回 `ResultSchema`，包含 `.coefficients`、`.fit`、`.sample`、`.summary()`。

### 6.2 核心 estimator 层（进阶）

```python
from stataflow import OLS, AbsorbingOLS

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
predictions = model.predict(type="xb")        # 线性预测值

model = AbsorbingOLS(data=df, y="wage", x=["edu"], absorb="firm_id")
result = model.fit(vce="cluster", cluster="state")
```

用于需要 `predict()`、`margins()`、编程化迭代模型的场景。

## 7. 因子变量

所有 `x` 参数均支持 Stata 风格因子变量语法：

| 语法 | 含义 | 示例 |
|---|---|---|
| `i.var` | 从分类变量生成虚拟变量 | `i.state` |
| `ibN.var` | 将基组设为第 N 类 | `ib2.state` |
| `oN.var` | 省略第 N 类 | `o3.state` |
| `c.var` | 显式声明为连续变量 | `c.age` |
| `var1#var2` | 仅交互项 | `state#post` |
| `var1##var2` | 主效应 + 交互项 | `state##post` |

**注意**：`#` / `##` 中的裸变量默认按连续变量处理。`L.x` / `F.x` 时间序列算子、三向交互不支持。

## 8. 后估计 (Post-Estimation)

```python
from stataflow import OLS, Logit
from stataflow.postestimation import estat_summarize, estat_ic

# 预测
model = OLS(data=df, y="y", x=["x1", "x2"]); model.fit()
xb = model.predict(type="xb")
residuals = model.predict(type="residuals")

model = Logit(data=df, y="y_bin", x=["x1", "x2"]); model.fit()
pr = model.predict(type="pr")     # 预测概率

# estat summarize
summary = estat_summarize(result, data=df, variables=["y", "x1", "x2"], dep_var="y")

# estat ic（信息准则）
ic = estat_ic(result)
print(f"AIC = {ic['aic']:.2f}, BIC = {ic['bic']:.2f}")
```

## 9. 常见问题

**Q: `x` 为什么必须是列表？** 因为 stataflow 允许在 `x` 中使用 Stata 风格的因子变量语法（例如 `["i.state##c.post"]`），必须用列表来区分单个字符串与变量名列表。

**Q: 不支持我需要的某个 Stata 选项怎么办？** stataflow 对不支持的参数采用 "hard-reject" 策略（报错而非静默忽略）。查阅 [命令支持矩阵](./command-support-matrix/README.md) 确认具体命令的支持范围。

**Q: 如何区分 `xtreg_fe` 和 `reghdfe`？** `xtreg_fe` 用于单一 FE（面板变量），`reghdfe` 支持多个 FE 及高级功能（MAP、斜率吸收、DK VCE 等）。简单面板模型两者均可使用；2+ FE 场景必须用 `reghdfe`。

## 10. 下一步

- **[Cookbook（英文）](./cookbook.md)** — 逐命令可复制代码示例
- **[中文使用手册（详细版）](./cookbook.zh-CN.md)** — 含教程、图解和完整代码
- **[命令支持矩阵](./command-support-matrix/README.md)** — 逐命令完整参数支持表
- **[示例](../examples/)** — 可直接运行的 demo 脚本

---

*最后更新：2026-04-30*
