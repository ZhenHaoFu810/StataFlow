# 公共 API 规范

## 1. 设计原则

- 对外 API 以 Python 原生接口为主
- 术语、参数语义和结果字段尽量可映射回 Stata
- 不在 v1 支持完整 Stata 命令字符串解析
- 默认使用显式参数而非隐式全局状态

## 2. v1 公开对象

### `statapy.linear.OLS`

建议构造签名：

```python
OLS(
    data,
    y,
    x,
    add_constant=True,
    weights=None,
    weight_type=None,
    missing="drop",
)
```

参数约束：

- `data`：表格型输入，首选 pandas DataFrame
- `y`：单个因变量名
- `x`：自变量名列表
- `add_constant`：默认 `True`
- `weights`：默认 `None`
- `weight_type`：v1 仅为后续扩展预留，若启用需与支持列表一致
- `missing`：v1 仅允许 `"drop"`

### `statapy.linear.FixedEffectsOLS`

建议构造签名：

```python
FixedEffectsOLS(
    data,
    y,
    x,
    fe,
    add_constant=False,
    weights=None,
    weight_type=None,
    missing="drop",
)
```

参数约束：

- `fe`：v1 仅允许单个固定效应变量
- `add_constant`：默认 `False`，避免与 within 转换的语义冲突

## 3. 拟合接口

所有线性模型对象应暴露统一 `fit` 方法：

```python
fit(
    vce="ols",
    cluster=None,
    alpha=0.05,
)
```

约束如下：

- `vce`：仅允许 `"ols"`、`"robust"`、`"cluster"`
- 当 `vce="cluster"` 时，`cluster` 必填
- `alpha` 用于置信区间与 summary 展示

## 4. Stata 映射层

v1 可提供轻量 wrapper，例如：

```python
regress(
    data,
    depvar,
    indepvars,
    vce="ols",
    cluster=None,
    add_constant=True,
)
```

映射原则：

- 使用 Stata 术语但保留 Python 参数风格
- 不要求模拟完整命令行
- 仅作为迁移便利层，不应反向约束内核实现

## 5. 结果对象字段

所有公开结果对象至少应包含：

- `params`
- `bse`
- `tvalues`
- `pvalues`
- `cov`
- `conf_int()`
- `fittedvalues`
- `resid`
- `nobs`
- `df_model`
- `df_resid`
- `rank`
- `rss`
- `tss`
- `mss`
- `rmse`
- `r2`
- `r2_adj`
- `f_stat`
- `f_pvalue`
- `vcetype`
- `weight_type`
- `cluster_var`
- `fe_vars`
- `sample_mask`

## 6. summary 规范

结果对象必须支持：

- `summary()`：默认 Python 风格
- `summary(style="stata")`：Stata 风格展示

Stata 风格 summary 至少需要：

- 模型标题
- 样本数
- F 统计量
- `R-squared`
- Root MSE
- 系数表
- `Std. Err.`、`t`、`P>|t|`、置信区间

## 7. API 变更规则

以下变化视为公共 API 变更，必须先写 ADR：

- 修改默认参数
- 删除或重命名结果字段
- 改变 `summary(style="stata")` 的已承诺字段语义
- 让原先可用的参数组合失效
