# Validation Policy

## Purpose

本目录定义 `stataflow` 对外发布时使用的“迁移成功且准确”证据标准。  
目标不是证明“测试能过”，而是证明：**当前已实现的 Stata 17 命令路径，在数学口径、字段级结果和公开 API 语义上，与目标 Stata 命令对齐。**

## Scope

本政策覆盖以下公开命令：

- `regress`
- `xtreg, fe`
- `areg`
- `reghdfe`
- `ivregress 2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

## Evidence Standard

每个命令的对外证据至少包含两条线：

1. `synthetic`
   - 用于锁定估计公式、样本筛选、自由度、边界行为和选项语义。
2. `real_data`
   - 用于锁定真实经济学/金融学研究环境下的字段级对齐。

如果某命令当前只实现了子集，则证据册只宣称 **validated subset**，不包装成完整命令复现。

## Hard Fields

以下字段属于硬字段，只要命令公开暴露、Stata 可得，就必须比较：

- `nobs`
- `df_model`
- `df_resid`
- `df_a`（如适用）
- `ll`
- `chi2`
- `f_stat`
- `deviance`
- `pseudo_r2`
- coefficient names
- coefficients
- standard errors
- p-values
- confidence intervals

对 DID / event-study / RD 这类输出更接近“估计量表”的命令，硬字段至少包括：

- 结果名 / event-time 名称
- estimates
- standard errors
- 已公开的聚合统计量

## Tolerance Policy

### Deterministic paths

优先使用严格字段级容差：

- 推荐 `rtol=1e-6`
- 推荐 `atol=1e-8`

适用场景：

- OLS / FE / absorbed OLS
- 常规 2SLS
- 固定带宽 RD
- 已锁定 IRLS / MLE 路径且无自动选择器时

### Numerically adaptive paths

对自动带宽选择、数值优化或迭代 plug-in selector 路径，可以使用更宽容差，但必须同时满足：

- 放宽原因写入证据矩阵
- 放宽字段明确列出
- 差异规模足以被解释为算法迭代/数值路径差异，而不是公式错误

当前典型场景：

- `rdrobust` 的 `bwselect="mserd"`

## Explicitly Not Allowed

以下情况不能算“通过”：

- 只比较系数，不比较推断字段
- 只做 wrapper delegation，不做 Stata dual-run
- 容差被放宽但没有写明原因
- 通过手工修补某个样例数值来“对上”而不是实现真实统计逻辑
- 已知 support matrix / source map 只声明子集实现，却在证据册里宣称完整命令复现

## Status Labels

- `passed`
  - 当前命令/模型/数据组合在本政策下通过
- `passed_with_documented_tolerance`
  - 通过，但存在已说明的自适应数值容差
- `partial_subset`
  - 当前路径通过，但命令整体仍是子集实现
- `blocked`
  - 当前字段级门槛未通过或证据链不完整

## Artifact Rule

每一条对外证据都必须能追溯到：

- 数据集登记项
- Stata 命令
- Python API
- 测试/脚本文件
- 结果摘要文件或证据矩阵条目

见：

- [Overview](./overview.md)
- [Evidence Matrix](./evidence-matrix.md)
- [Dataset Registry](./dataset-registry.md)
