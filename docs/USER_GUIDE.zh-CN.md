# 使用手册

## 1. 目的

本文档面向使用 StataFlow 的外部用户，说明安装方式、主要使用路径、验证资产位置和推荐阅读顺序。

## 2. 两层主要使用方式

### `stataflow.compat.stata`

如果你希望按 Stata 风格使用命令接口，优先用这一层。

常见命令包括：

- `regress`
- `xtreg_fe`
- `areg`
- `reghdfe`
- `ivregress_2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

### Core estimator

如果你希望更底层、更编程化地控制模型，可以直接使用 [src/stataflow/estimators](/src/stataflow/estimators) 下的 estimator。

## 3. 安装与环境

普通用户建议直接安装发布版本：

```bash
pip install StataFlow
```

如果你在本地参与开发或需要直接跟踪源码，再使用 editable mode：

```bash
pip install -e .
```

如果你要运行 Stata-Python 双跑验证，需要本地安装可用的 Stata 17。与 Stata 的交互逻辑在 [src/stataflow/stata_runner](/src/stataflow/stata_runner)。

## 4. 示例

可直接参考：

- [examples/demo_regress.py](/examples/demo_regress.py)
- [examples/demo_reghdfe.py](/examples/demo_reghdfe.py)
- [examples/demo_ppmlhdfe.py](/examples/demo_ppmlhdfe.py)
- [examples/demo_ivregress_2sls.py](/examples/demo_ivregress_2sls.py)

## 5. 因子变量语义

命令层已经支持一部分 Stata 风格 factor-variable 语义。具体支持范围要按命令与文档来确认，尤其是：

- 连续变量交互，如 `x1#x2`、`x1##x2`
- 含 `i.` 的分类变量交互
- FE/HDFE 模型中主效应被 absorb 掉、交互项仍可识别的场景

## 6. 固定效应与 HDFE

在支持的 wrapper 中，可以使用 `absorb="firm year"` 这类 Stata 风格写法，或使用列表式吸收变量。具体命令支持范围见：

- [docs/command-support-matrix/reghdfe.md](/docs/command-support-matrix/reghdfe.md)
- [docs/command-support-matrix/ivreghdfe.md](/docs/command-support-matrix/ivreghdfe.md)
- [docs/command-support-matrix/ppmlhdfe.md](/docs/command-support-matrix/ppmlhdfe.md)

## 7. Validation 资产

当前仓库保留了可执行的 validation 脚本和结果产物。

脚本：

- [scripts/validation](/scripts/validation)
- [scripts/validation/oos](/scripts/validation/oos)

结果产物：

- [research/results/validation](/research/results/validation)

## 8. 建议阅读顺序

如果你第一次接触这个项目，建议按下面顺序阅读：

1. [README.md](/README.md)
2. [docs/command-support-matrix/README.md](/docs/command-support-matrix/README.md)
3. 再看具体命令的 support matrix
