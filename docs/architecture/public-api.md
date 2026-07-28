# 公共 API 规范

## 1. 设计原则

- 对外 API 分为“核心层”和“Stata 兼容层”
- 核心层保持 Python 原生风格
- 兼容层使用 Stata 命令命名，但不承诺完整命令行解析
- 社区高频命令默认放扩展兼容层
- **不支持的参数必须硬报错，不允许静默忽略**

## 2. Core API

### 已有估计器

```python
from stataflow import (
    OLS,
    FixedEffectsOLS,
    AbsorbingOLS,
    IV2SLS,
    IVAbsorbingOLS,
    Logit,
    Probit,
    Poisson,
    PPMLHDFE,
    DIDImputation,
    EventStudyInteract,
    CSDID,
    RDRobust,
)
```

设计要求：

- `fit()` 语义尽量统一
- 结果对象字段尽量统一
- 不因某一条 Stata wrapper 的历史选项污染核心接口

## 3. Stata 兼容层

### 正式入口

```python
from stataflow.compat.stata import (
    regress,
    xtreg_fe,
    areg,
    reghdfe,
    ivregress_2sls,
    ivreghdfe,
    logit,
    probit,
    poisson,
    ppmlhdfe,
    did_imputation,
    eventstudyinteract,
    csdid,
    rdrobust,
)
```

### 命令映射表

| Stata 命令 | Python 函数 | 核心类 |
|-----------|-------------|--------|
| `regress` | `regress(...)` | `OLS` |
| `xtreg, fe` | `xtreg_fe(...)` | `FixedEffectsOLS` |
| `areg` | `areg(...)` | `AbsorbingOLS` |
| `reghdfe` | `reghdfe(...)` | `AbsorbingOLS` |
| `ivregress 2sls` | `ivregress_2sls(...)` | `IV2SLS` |
| `ivreghdfe` | `ivreghdfe(...)` | `IVAbsorbingOLS` |
| `logit` | `logit(...)` | `Logit` |
| `probit` | `probit(...)` | `Probit` |
| `poisson` | `poisson(...)` | `Poisson` |
| `ppmlhdfe` | `ppmlhdfe(...)` | `PPMLHDFE` |
| `did_imputation` | `did_imputation(...)` | `DIDImputation` |
| `eventstudyinteract` | `eventstudyinteract(...)` | `EventStudyInteract` |
| `csdid` | `csdid(...)` | `CSDID` |
| `rdrobust` | `rdrobust(...)` | `RDRobust` |

### 映射原则

- 优先贴近 Stata 常用命令与术语
- 仅对高频参数做显式支持
- 默认不追求完全字符串兼容
- 所有 wrapper 通过 `**kwargs` 捕获并硬拒绝未知参数
- 对已知但未实现的参数（如 `poisson` 的 `exposure`）显式抛出 `NotImplementedError`

## 4. 扩展兼容层定位

以下命令作为扩展兼容层实现，其完整历史选项面不自动成为稳定 API 承诺：

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

每份命令的当前支持边界见 `docs/command-support-matrix/`。

## 5. 结果对象要求

所有公开结果对象至少应包含：

- 系数与方差：
  - `params`
  - `bse`
  - `cov`
  - `tvalues` 或 `zvalues`
  - `pvalues`
- 模型统计量：
  - `nobs`
  - `df_model`
  - `df_resid`
  - `rss`
  - `tss`
  - `mss`
  - `rmse`
  - `r2`
  - `r2_adj`
  - `f_stat`
  - `f_pvalue`
- 元数据：
  - `vcetype`
  - `weight_type`
  - `cluster_var`
  - `fe_vars`
  - `sample_mask`
  - `estimator_family`

对于非线性模型，允许将 `f_stat` 替换为更贴合 Stata 的整体检验统计量，但必须在研究档案中明确记录其语义。

## 6. 输出层

结果对象必须支持：

- `summary()`
- `summary(style="stata")`
- `display(detail="full"|"compact", show_ci=True)`
- `to_html()` 与 Jupyter `_repr_html_()`

`summary()` 返回字符串且无输出副作用；`display()` 只负责打印同一份文本。
文本和 HTML 都由命令族适配器生成的 `DisplayDocument` 渲染，不单独推断统计量。

### 6.1 `csdid` 结果契约（ADR-0005）

`csdid()` 返回拟合好的 `CSDID` 模型对象（默认返回类型不变）。该对象满足：

- `model.result` — 默认（event）聚合的 `ResultSchema`，与 `model.estat("event")` 逐字段一致
- `model.summary()` / `model.display()` — 委托给 `model.result` 的同名方法
- `model.estat("simple"|"event"|"group"|"calendar"|"pretrend")` — 显式聚合入口

未拟合的模型访问上述入口时抛出
`ValueError("Model has not been fitted. Call fit() first.")`。

### 6.2 Summary 展示契约

- 回归族以 `Terms:` 展示系数项，不伪造未知的因变量名或公式。
- 仅线性、固定效应、吸收和 IV 族展示普通 `R2` / adjusted `R2`。
- GLM / PPML 展示适用的 pseudo-R2、log-likelihood 与 deviance。
- DID / RD 不展示不适用的普通 R2；RD 展示 kernel 信息。
- 默认 `full` 模式展示 95% 置信区间和当前命令适用的专属诊断；
  `compact` 模式只保留模型摘要、系数表和核心拟合统计量。
- 不支持的 `style` 或 `detail` 必须抛出 `ValueError`。

## 7. API 演化规则

以下变化必须先写 ADR：

- 重命名核心估计器类
- 改变核心参数默认值
- 删除或重命名已承诺结果字段
- 提升某个扩展兼容命令为核心稳定 API
