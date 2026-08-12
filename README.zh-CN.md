# StataFlow

**面向 Python 的 Stata 对齐计量经济学工具包，在已记录的支持范围内提供字段级验证。**

[English](README.md)

[![CI](https://github.com/ZhenHaoFu810/StataFlow/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ZhenHaoFu810/StataFlow/actions/workflows/ci.yml)
[![PyPI 版本](https://img.shields.io/pypi/v/stataflow.svg)](https://pypi.org/project/StataFlow/)
[![下载量](https://static.pepy.tech/badge/stataflow)](https://pepy.tech/projects/stataflow?timeRange=threeMonths&category=version&includeCIDownloads=true&granularity=weekly&viewType=line&versions=Total%2C1.*%2C0.*)
[![Python 版本](https://img.shields.io/pypi/pyversions/stataflow.svg)](https://pypi.org/project/StataFlow/)
[![许可证](https://img.shields.io/pypi/l/stataflow.svg)](LICENSE)
[![类型标记](https://img.shields.io/pypi/types/stataflow.svg)](https://pypi.org/project/StataFlow/)
[![Stata 验证](https://img.shields.io/badge/Stata_validation-documented_support_surface-1f6f5f.svg)](VALIDATION.md)

[安装](#安装) · [快速开始](#快速开始) · [验证](#验证状态) · [文档](#文档) · [参与贡献](CONTRIBUTING.md)

---

```python
from stataflow.compat.stata import reghdfe

result = reghdfe(
    df,
    y="lwage",
    x=["exper", "edu"],
    absorb="firm_id year_id",
    vce="cluster",
    cluster="firm_id",
)
result.display()
```

---

## 项目定位

StataFlow 面向希望在 Python 中复现 Stata 实证工作流的研究者。它不是泛化的统计库；公开能力在已记录的支持范围内经过 Stata 字段级验证，并以合成样例和公开真实数据样例为证据。

最新稳定版本是 **1.3.0**，覆盖 14 个 Stata 风格命令。

## 功能概览

- **14 个估计命令**：`regress`、`xtreg_fe`、`areg`、`reghdfe`、`ivregress_2sls`、`ivreghdfe`、`logit`、`probit`、`poisson`、`ppmlhdfe`、`did_imputation`、`eventstudyinteract`、`csdid`、`rdrobust`。另行导出的 `rdplot` 是辅助工具，不计入估计命令数。
- **双层 API**：Stata 兼容命令层（`stataflow.compat.stata`）和 Python 原生估计器层（`stataflow.estimators`）。
- **命令感知的 Stata 风格输出**：`result.display()` 自动展示当前命令适用的
  完整结果、拟合统计量和诊断信息；Notebook 使用同一份数据生成安全 HTML。
- **高维固定效应**：支持多固定效应吸收、singleton 处理、个体斜率、聚类 VCE 和大规模 FE 场景。
- **工具变量模型**：支持 2SLS、GMM2S、LIML、Fuller/k-class、一阶段诊断、弱工具变量检验和过度识别检验。
- **二元、计数和 PPML 模型**：支持 Logit、Probit、Poisson、PPML-HDFE 及常用稳健/聚类协方差估计。
- **因果推断**：支持 BJS DID imputation、Sun-Abraham event study、Callaway-Sant'Anna DID 和 sharp/fuzzy RD。
- **Stata 语法子集**：支持 factor variables、按命令列明的 analytic weights、多固定效应和常用 VCE；不支持的参数会显式报错，不会静默忽略。
- **验证优先**：每个公开能力都在已记录的支持范围内经过 Stata 字段级验证。

## 安装

```bash
pip install StataFlow
```

需要 Python 3.10、3.11 或 3.12。核心依赖包括 NumPy、pandas、SciPy、scikit-learn 和 PyYAML。

## 快速开始

### Stata 兼容 API

```python
from stataflow.compat.stata import regress, reghdfe, logit, ivregress_2sls, ppmlhdfe

# OLS + robust 标准误
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")
result.display()

# 高维固定效应
result = reghdfe(
    df,
    y="wage",
    x=["edu", "exper"],
    absorb="firm_id year_id",
    vce="cluster",
    cluster="industry",
)

# Logit
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
result.display()

# 2SLS + robust VCE
result = ivregress_2sls(
    df,
    y="lwage",
    x_exog=["educ"],
    x_endog=["exper"],
    instruments=["age", "kidslt6"],
    vce="robust",
)

# PPML + 高维固定效应
result = ppmlhdfe(
    df,
    y="trade",
    x=["lndist", "contig", "fta"],
    absorb=["exporter", "importer", "year"],
    vce="cluster",
    cluster="exporter",
)
```

### Python 原生 API

```python
from stataflow import OLS, AbsorbingOLS, Logit

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
result.display()
```

### 查看结果

```python
result.display()                         # 完整输出，默认含 95% 置信区间
result.display(detail="compact")        # 精简模式
result.display(show_ci=False)           # 隐藏置信区间
text = result.summary(width=100)        # 返回同一张纯文本结果表
html = result.to_html()                 # 用于报告或 Notebook 的安全 HTML
```

## 支持的模型

| 类型 | 命令 | 估计器与 VCE |
|------|------|--------------|
| 线性模型 | `regress`、`areg`、`xtreg_fe`、`reghdfe` | OLS，支持 `ols`、`robust` 和按命令列明的聚类 VCE；仅 `reghdfe` 支持 `dkraay` |
| 工具变量 | `ivregress_2sls`、`ivreghdfe` | 2SLS、GMM2S、LIML、Fuller/k-class、一阶段诊断、弱工具变量检验 |
| 二元/计数模型 | `logit`、`probit`、`poisson` | MLE，支持 `ols`、`robust` 和 `cluster` VCE |
| PPML + HDFE | `ppmlhdfe` | IRLS、固定效应、offset/exposure、separation 检测、`eform` 和常用预测类型 |
| DID | `did_imputation`、`csdid`、`eventstudyinteract` | BJS imputation、Callaway-Sant'Anna、Sun-Abraham IW |
| RD | `rdrobust` | Sharp/fuzzy RD、MSE/CER 带宽选择、协变量、权重、mass points、cluster/nncluster VCE |

完整支持边界见[命令支持矩阵](docs/command-support-matrix/README.md)和[已知问题](docs/release/known-issues.md)。

## 验证状态

下表是为 1.3.0 保留的 1.2.0 估计器验证快照，实际对照环境为 Stata 17。
StataFlow 1.3.0 仅更改了结果展示和元数据，未更改估计器或推断算法。相对偏差定义为
`|Python - Stata| / max(|Stata|, 1e-15)`。

| 命令族 | 覆盖命令 | Stata 17 对照 | 最大系数偏差 | 最大标准误偏差 |
|---|---|---:|---:|---:|
| 线性 / 固定效应 | `regress`、`areg`、`xtreg_fe`、`reghdfe` | 18/18 | 2.48e-7 | 2.25e-7 |
| 工具变量 | `ivregress_2sls`、`ivreghdfe` | 5/5 | 1.16e-8 | 3.74e-8 |
| 二元 / 计数 | `logit`、`probit`、`poisson`、`ppmlhdfe` | 12/12 | 1.33e-7 | 8.42e-8 |
| DID | `did_imputation`、`csdid`、`eventstudyinteract` | 2/2 + 1 项功能检查 | 8.13e-8 | 5.13e-8 |
| RD | `rdrobust` | 3/3 | 9.23e-8 | 2.96e-8 |
| **合计** | **14 个公开估计命令** | **40/40** | **2.48e-7** | **2.25e-7** |

完整本地 Stata 验证检查结果为 `856 passed, 12 skipped`；公开、自包含的
验证套件在 Stata 17 上通过 `10/10` 个可复现验证用例。以上数值存储在
[`evidence-summary.json`](research/results/validation/evidence-summary.json) 中。

## 文档

- [User Guide](docs/USER_GUIDE.md)（[中文](docs/USER_GUIDE.zh-CN.md)）
- [Cookbook](docs/cookbook.md)（[中文](docs/cookbook.zh-CN.md)）
- [Examples](examples/) — 九个确定性 demo 脚本，覆盖全部 14 个公开命令；无需网络或本地 Stata
- [验证证据（JSON）](research/results/validation/evidence-summary.json)
- [验证证据（可读版）](research/results/validation/evidence-summary.md)
- [Changelog](CHANGELOG.md)

## 运行测试

```bash
# 单元和集成测试
pytest tests/ -v

# 可复现 Stata 验证用例（需要本地 Stata 17）
pytest tests/stata_validation/ -v -s
```

## 社区

- [贡献指南](CONTRIBUTING.md) — 开发流程、测试要求与 PR 检查
- [安全政策](SECURITY.md) — 支持的版本与私密漏洞报告渠道
- [行为准则](CODE_OF_CONDUCT.md)

## 许可证

本项目采用 MIT License。详情见 [LICENSE](LICENSE)。
