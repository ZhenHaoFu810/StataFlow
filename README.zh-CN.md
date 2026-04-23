# StataFlow

StataFlow（`stataflow`）是一个 Python 计量经济学工具包，目标是在已公开声明的命令子集上，以高精度复现 **Stata 17** 的估计结果。它同时提供：

- 面向 Stata 用户的 **Stata 风格命令层**
- 面向高级用户的 **Python 原生 estimator 层**

## 当前可以做什么

- 在 Python 里直接使用 Stata 风格命令：`regress`、`reghdfe`、`ivregress 2sls`、`logit`、`ppmlhdfe`、`did_imputation`、`csdid`、`rdrobust` 等。
- 获得与 Stata 17 做过字段级比对的系数、标准误、t/z 统计量、p 值和置信区间。
- 使用 HDFE、IV/2SLS、二元/计数模型、DID / event-study 估计量。
- 在 wrapper 命令中直接使用 Stata 风格的 factor-variable 语法，例如 `i.group##c.post`、`c.x1#c.x2`、`x1##x2`。`#` / `##` 里的裸变量默认按连续变量处理。

## 当前尚不支持的内容

- **多维聚类标准误**：`regress` 支持 two-way clustering（Cameron-Gelbach-Miller 2011）；其他命令当前仍只支持单聚类稳健推断。
- **wrapper 层直接做 post-estimation**：`compat.stata` wrapper 返回 `ResultSchema`，不直接暴露 `.predict()` / `.margins()`；这些接口目前只在核心 estimator 层可用。
- **community commands 的完整命令面**：`reghdfe`、`ivreghdfe`、`ppmlhdfe`、`did_imputation`、`eventstudyinteract`、`csdid`、`rdrobust` 当前都是**已验证的高频子集**，不是完整 Stata 命令复刻。不支持的参数会显式报错，而不是静默忽略。

### 完整度图例

- **Stable**：synthetic + real-data dual-run 均已验证，核心 API 短期内不太可能发生破坏性变化。
- **Alpha**：高频路径已实现并验证，但命令面仍是社区命令的子集。
- **Alpha — Partial**：已有可验证实现，但仍缺失较大功能块。

各命令的细化边界见 [命令支持矩阵](./docs/command-support-matrix/README.md)。

---

## 安装

推荐普通用户直接安装发布版本：

```bash
pip install StataFlow
```

环境要求：Python 3.10+、NumPy、pandas、SciPy。

如果你是开发者，需要从源码 editable install：

```bash
git clone https://github.com/ZhenHaoFu810/StataFlow.git
cd StataFlow
pip install -e .
```

---

## 快速开始

### Stata 风格命令层（推荐）

所有 `compat.stata` wrapper 都返回 `ResultSchema` 对象，包含系数、标准误和拟合统计量；它们**不直接暴露** `.predict()` 或 `.margins()`，如需 post-estimation，请用下方的核心 estimator 层。

```python
import pandas as pd
from stataflow.compat.stata import regress, reghdfe, ivregress_2sls, logit

# OLS + robust SE
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")

# HDFE
result = reghdfe(
    df, y="wage", x=["edu", "exper"],
    absorb="firm_id year_id", vce="cluster", cluster="industry"
)

# HDFE + factor-variable
result = reghdfe(
    df, y="wage", x=["i.industry##c.post"], absorb="firm_id year_id"
)

# 2SLS
result = ivregress_2sls(
    df, y="lwage", x_exog=["edu"], x_endog=["exper"],
    instruments=["age", "kidslt6"], vce="robust"
)

# Logit
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
```

可直接运行的示例见：

- [examples/demo_regress.py](./examples/demo_regress.py)
- [examples/demo_reghdfe.py](./examples/demo_reghdfe.py)
- [examples/demo_ppmlhdfe.py](./examples/demo_ppmlhdfe.py)
- [examples/demo_ivregress_2sls.py](./examples/demo_ivregress_2sls.py)

### Python 原生 estimator 层（高级）

```python
from stataflow import OLS, FixedEffectsOLS, AbsorbingOLS, Logit, IV2SLS

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
```

---

## 当前支持的命令

| 命令 | Python 入口 | 当前核心能力 |
|------|-------------|--------------|
| `regress` | `stataflow.compat.stata.regress` | OLS、robust、cluster、aweight |
| `xtreg, fe` | `stataflow.compat.stata.xtreg_fe` | within FE、cluster |
| `areg` | `stataflow.compat.stata.areg` | 单吸收变量 FE |
| `reghdfe` | `stataflow.compat.stata.reghdfe` | 1+ 组 HDFE、cluster、singleton drop |
| `ivregress 2sls` | `stataflow.compat.stata.ivregress_2sls` | 2SLS、robust、cluster |
| `ivreghdfe` | `stataflow.compat.stata.ivreghdfe` | IV + 1+ 组 HDFE、cluster |
| `logit` | `stataflow.compat.stata.logit` | MLE、robust、cluster |
| `probit` | `stataflow.compat.stata.probit` | MLE、robust、cluster |
| `poisson` | `stataflow.compat.stata.poisson` | MLE、robust、cluster |
| `ppmlhdfe` | `stataflow.compat.stata.ppmlhdfe` | PPML + 1+ 组 HDFE |
| `did_imputation` | `stataflow.compat.stata.did_imputation` | BJS DID imputation |
| `eventstudyinteract` | `stataflow.compat.stata.eventstudyinteract` | Sun & Abraham IW estimator |
| `csdid` | `stataflow.compat.stata.csdid` | Callaway-Sant'Anna DID（仅 `method="reg"`） |
| `rdrobust` | `stataflow.compat.stata.rdrobust` | Sharp RD local polynomial（`bwselect="mserd"`、`covs`） |

完整说明见 [docs/command-support-matrix/README.md](./docs/command-support-matrix/README.md)。

---

## 验证原则

每个对外命令都要求两条证据线：

1. **Synthetic / controlled cases**：锁定公式、自由度、样本筛选和边界行为。
2. **真实公开数据**：与 Stata 17 做字段级对比。

只有两条证据线都通过，且 source-to-Python mapping 已记录，命令才算“完成”。项目不接受没有明确数学或源码依据的“统计意义上差不多”。

公开证据与结果见 `research/results/validation/`。

### 如何运行测试

```bash
# 单元与集成测试（快）
pytest tests/ -v --ignore=tests/golden/

# Golden dual-run tests（需要本地 Stata 17）
pytest tests/golden/ -v
```

---

## 项目结构

- **`src/stataflow/estimators/`**：核心 estimator（`OLS`、`AbsorbingOLS`、`Logit`、`PPMLHDFE`、`DIDImputation` 等）
- **`src/stataflow/compat/stata/`**：Stata 命令 wrapper（`regress()`、`reghdfe()`、`ivregress_2sls()` 等）
- **`docs/command-support-matrix/`**：逐命令支持矩阵
- **`examples/`**：可运行示例
- **`tests/`**：单元与集成测试

---

## 默认对齐版本

**Stata 17**

---

## 文档入口

- [用户手册](./docs/USER_GUIDE.md)
- [中文用户手册](./docs/USER_GUIDE.zh-CN.md)
- [Cookbook](./docs/cookbook.md)
- [中文 Cookbook](./docs/cookbook.zh-CN.md)
- [命令支持矩阵](./docs/command-support-matrix/README.md)

---

## 治理方式

- **Codex**：项目目标、架构、review gate、统计争议裁决
- **Claude Code**：实现、测试与证据回填
