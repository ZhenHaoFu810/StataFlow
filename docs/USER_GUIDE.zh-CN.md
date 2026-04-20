# 使用手册

## 1. 目的

这个目录是 StataFlow 的“面向开源发布的干净版本”。它用于：

- 外部用户使用
- 可复核 validation
- 对外分发与开源展示

开发期的大量任务卡、review 往返、AI 协作文档大多没有被带进来。

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

如果你希望更底层、更编程化地控制模型，可以直接使用 [src/stataflow/estimators](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/src/stataflow/estimators) 下的 estimator。

## 3. 安装与环境

建议用 editable mode：

```bash
pip install -e .
```

如果你要运行 Stata-Python 双跑验证，需要本地安装可用的 Stata 17。与 Stata 的交互逻辑在 [src/stataflow/stata_runner](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/src/stataflow/stata_runner)。

## 4. 示例

可直接参考：

- [examples/demo_regress.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples/demo_regress.py)
- [examples/demo_reghdfe.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples/demo_reghdfe.py)
- [examples/demo_ppmlhdfe.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples/demo_ppmlhdfe.py)
- [examples/demo_ivregress_2sls.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples/demo_ivregress_2sls.py)

## 5. 因子变量语义

命令层已经支持一部分 Stata 风格 factor-variable 语义。具体支持范围要按命令与文档来确认，尤其是：

- 连续变量交互，如 `x1#x2`、`x1##x2`
- 含 `i.` 的分类变量交互
- FE/HDFE 模型中主效应被 absorb 掉、交互项仍可识别的场景

## 6. 固定效应与 HDFE

在支持的 wrapper 中，可以使用 `absorb="firm year"` 这类 Stata 风格写法，或使用列表式吸收变量。具体命令支持范围见：

- [docs/command-support-matrix/reghdfe.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/reghdfe.md)
- [docs/command-support-matrix/ivreghdfe.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/ivreghdfe.md)
- [docs/command-support-matrix/ppmlhdfe.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/ppmlhdfe.md)

## 7. Validation 资产

当前目录同时保留了 validation 文档和可执行脚本。

文档：

- [docs/validation/README.zh-CN.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/README.zh-CN.md)
- [docs/validation/overview.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/overview.md)
- [docs/validation/evidence-matrix.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/evidence-matrix.md)

脚本：

- [scripts/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/scripts/validation)
- [scripts/validation/oos](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/scripts/validation/oos)

结果产物：

- [research/results/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/results/validation)

## 8. 公开数据

公开数据统一放在：

- [research/data/public](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/data/public)

数据来源、适用命令、是否进入 validation 等信息见：

- [docs/validation/dataset-registry.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/dataset-registry.md)

## 9. 建议阅读顺序

如果你第一次接触这个项目，建议按下面顺序阅读：

1. [README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/README.md)
2. [docs/command-support-matrix/README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/README.md)
3. [docs/validation/README.zh-CN.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/README.zh-CN.md)
4. [docs/validation/overview.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/overview.md)
5. 再看具体命令的 support matrix

## 10. 这个干净版本不包含什么

这个目录有意不包含以下大多数材料：

- AI 任务推进提示
- 多轮 review 报告
- 开发阶段 backlog 协调文档
- 临时日志和一次性进度文件

这些材料仍在原始工作仓库中，不在这个对外版本里。
