# 命令族规划

## 目标

本文件定义项目后续不再按零散命令推进，而按命令族推进。

## Command Families

### Linear Base

- `regress`
- `vce(robust)`
- `vce(cluster)`
- 权重

### Panel / FE / HDFE

- `xtreg, fe`
- `areg`
- 双向 FE
- `reghdfe`

### IV / GMM

- `ivregress`
- `ivreghdfe`

### Binary / Count

- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`

### DID / Event Study Extensions

- `did_imputation`
- `eventstudyinteract`
- `csdid`

### Postestimation

- `predict`
- 高频 `margins` 子集
- Stata 风格输出与 metadata

## 当前主线

当前默认主线：

- `Panel / FE / HDFE`

原因：

- 与金融和应用微观高频研究最贴近
- 已有 `OLS`、cluster、single FE 基础
- `reghdfe` 有公开源码
