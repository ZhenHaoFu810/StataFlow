# StataFlow

StataFlow 是一个面向计量经济学工作流的 Python 库，目标是在一组清晰限定的命令子集上，以 Stata 风格命令接口和源码支撑验证结果来复现 Stata 的使用体验。

这个目录是从原开发仓库中拆分出来的“干净开源版”。它保留：

- 核心代码
- 示例
- 命令支持矩阵
- validation 证据册
- 公开数据与验证结果
- 面向外部用户的中英文说明文档

同时尽量剔除了开发期 AI 协作、任务推进、审查往来等内部材料。

## 当前包含的内容

- 核心代码：[src/stataflow](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/src/stataflow)
- 示例：[examples](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples)
- 命令支持矩阵：[docs/command-support-matrix](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix)
- 验证证据册：[docs/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation)
- 公开数据与验证产物：[research/data/public](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/data/public)、[research/results/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/results/validation)
- 英文使用手册：[docs/USER_GUIDE.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/USER_GUIDE.md)
- 中文使用手册：[docs/USER_GUIDE.zh-CN.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/USER_GUIDE.zh-CN.md)

## 安装

```bash
pip install -e .
```

Python 版本要求以 [pyproject.toml](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/pyproject.toml) 为准。

## 快速开始

```python
import pandas as pd
from stataflow.compat.stata import regress, reghdfe

df = pd.read_csv("research/data/public/panel/oos/airfare.csv")

ols_res = regress(
    df=df,
    y="lfare",
    x=["ldist", "y98", "y99"],
    vce="robust",
)

hdfe_res = reghdfe(
    df=df,
    y="lfare",
    x=["ldist", "y98##y99"],
    absorb="id year",
    vce="cluster",
    cluster="id",
)
```

`compat.stata` 这一层返回稳定的命令风格结果对象；底层 estimator 仍然可直接调用，适合更编程化的工作流。

## 当前重点支持的命令族

当前版本重点覆盖以下命令的“已验证子集”：

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

命令名存在并不代表已经完整等同于 Stata 全命令。请以支持矩阵为准：

- [docs/command-support-matrix/README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/README.md)

## Validation 证据

对外最重要的验证入口如下：

- [Validation 导览](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/README.zh-CN.md)
- [总报告](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/overview.md)
- [证据矩阵](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/evidence-matrix.md)
- [Out-of-sample 结果汇总](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/results/validation/oos/oos_master_summary.md)

当前 validation 的原则是：对已实现子集，优先做基于 Stata 17 的真实公开数据字段级双跑对比，而不是只给出开发期测试通过结论。

## 目录结构

- [src](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/src)：包源码
- [examples](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples)：可运行示例
- [docs](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs)：面向外部用户的说明文档
- [scripts/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/scripts/validation)：验证脚本
- [research/data/public](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/data/public)：公开数据
- [research/results/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/results/validation)：验证结果产物

## 当前限制

- 若干 community commands 目前仍是“已验证子集”，不是完整迁移。
- 当前对外证据最强的是文档明确列出的功能范围与公开数据样例。
- 开发期内部任务卡、审查记录和 AI 协作文档没有被带入这个干净版本。

更多发布状态与已知问题见：

- [docs/release/open-source-alpha-status.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/release/open-source-alpha-status.md)
- [docs/release/known-issues.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/release/known-issues.md)
