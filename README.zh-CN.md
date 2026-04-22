# StataFlow

StataFlow 是一个面向计量经济学工作流的 Python 库，目标是在一组清晰限定的命令子集上，以 Stata 风格命令接口和源码支撑验证结果来复现 Stata 的使用体验。

本项目提供 Stata 风格的 Python 计量经济学命令接口，并对已实现子集提供基于 Stata 17 的字段级双跑验证。

## 当前包含的内容

- 核心代码：[src/stataflow](/src/stataflow)
- 示例：[examples](/examples)
- 命令支持矩阵：[docs/command-support-matrix](/docs/command-support-matrix)
- 验证结果产物：[research/results/validation](/research/results/validation)
- 英文使用手册：[docs/USER_GUIDE.md](/docs/USER_GUIDE.md)
- 中文使用手册：[docs/USER_GUIDE.zh-CN.md](/docs/USER_GUIDE.zh-CN.md)

## 安装

```bash
pip install -e .
```

Python 版本要求以 [pyproject.toml](/pyproject.toml) 为准。

## 快速开始

```python
import numpy as np
import pandas as pd
from stataflow.compat.stata import regress, reghdfe

rng = np.random.default_rng(42)
n = 200
df = pd.DataFrame({
    "y": rng.normal(0, 1, n),
    "x1": rng.normal(0, 1, n),
    "x2": rng.normal(0, 1, n),
    "cluster_id": rng.integers(1, 21, size=n),
})

ols_res = regress(df, y="y", x=["x1", "x2"], vce="robust")
hdfe_res = reghdfe(
    df, y="y", x=["x1", "x2"],
    absorb="cluster_id", vce="cluster", cluster="cluster_id"
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

- [docs/command-support-matrix/README.md](/docs/command-support-matrix/README.md)

## Validation 证据

对外最重要的验证入口：

- [Out-of-sample 结果汇总](/research/results/validation/oos/oos_master_summary.md)

当前 validation 的原则是：对已实现子集，优先做基于 Stata 17 的真实公开数据字段级双跑对比，而不是只给出开发期测试通过结论。

## 目录结构

- [src](/src)：包源码
- [examples](/examples)：可运行示例
- [docs](/docs)：面向外部用户的说明文档
- [scripts/validation](/scripts/validation)：验证脚本
- [research/results/validation](/research/results/validation)：验证结果产物

## 当前限制

- 若干 community commands 目前仍是“已验证子集”，不是完整迁移。
- 当前对外证据最强的是文档明确列出的功能范围与示例代码。
- 开发期内部任务卡、审查记录和 AI 协作文档没有被带入开源版本。
