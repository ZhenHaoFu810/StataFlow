# StataFlow

**一个以 Stata 17 字段级对齐为目标的 Python 计量经济学工具包。**

[![PyPI version](https://img.shields.io/pypi/v/stataflow)](https://pypi.org/project/stataflow/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

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

StataFlow 面向希望在 Python 中复现 Stata 实证工作流的研究者。它不是泛化的统计库；公开能力必须通过合成样例、公开真实数据样例，以及可运行的 Stata/Python 双跑证据来验证。

当前公开版本线是 **1.1.0 Stable**。截至 2026-07-09，项目已经完成一轮 **v1.2.0+ correctness hardening release-candidate sync**，重点是正确性加固、文档同步和开源可维护性。

## 功能概览

- **14 个 Stata 风格命令**：`regress`、`xtreg_fe`、`areg`、`reghdfe`、`ivregress_2sls`、`ivreghdfe`、`logit`、`probit`、`poisson`、`ppmlhdfe`、`did_imputation`、`eventstudyinteract`、`csdid`、`rdrobust`。
- **双层 API**：Stata 兼容命令层（`stataflow.compat.stata`）和 Python 原生估计器层（`stataflow.estimators`）。
- **Stata 风格输出**：`result.display()` 输出系数、标准误、检验统计量、p 值和拟合统计量。
- **高维固定效应**：支持多固定效应吸收、singleton 处理、个体斜率、聚类 VCE 和大规模 FE 场景。
- **工具变量模型**：支持 2SLS、GMM2S、LIML、Fuller/k-class、一阶段诊断、弱工具变量检验和过度识别检验。
- **二元、计数和 PPML 模型**：支持 Logit、Probit、Poisson、PPML-HDFE 及常用稳健/聚类协方差估计。
- **因果推断**：支持 BJS DID imputation、Sun-Abraham event study、Callaway-Sant'Anna DID 和 sharp/fuzzy RD。
- **Stata 语法子集**：支持 factor variables、analytic weights、多固定效应和常用 VCE；不支持的参数会显式报错，不会静默忽略。
- **验证优先**：每个公开能力都围绕 Stata 17 进行字段级验证。

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

### 结果访问

```python
result.display(show_ci=True)

for coef in result.coefficients:
    print(f"{coef.name}: b={coef.beta:.6f}, se={coef.std_err:.6f}, t={coef.t_stat:.2f}")

print(f"R2 = {result.fit.r2:.4f}, N = {result.sample.nobs}")
```

## 支持的模型

| 类型 | 命令 | 估计器与 VCE |
|------|------|--------------|
| 线性模型 | `regress`、`areg`、`xtreg_fe`、`reghdfe` | OLS，支持 `ols`、`robust`、`cluster` 和 `dkraay` |
| 工具变量 | `ivregress_2sls`、`ivreghdfe` | 2SLS、GMM2S、LIML、Fuller/k-class、一阶段诊断、弱工具变量检验 |
| 二元/计数模型 | `logit`、`probit`、`poisson` | MLE，支持 `ols`、`robust` 和 `cluster` VCE |
| PPML + HDFE | `ppmlhdfe` | IRLS、固定效应、offset/exposure、separation 检测、`eform` 和常用预测类型 |
| DID | `did_imputation`、`csdid`、`eventstudyinteract` | BJS imputation、Callaway-Sant'Anna、Sun-Abraham IW |
| RD | `rdrobust` | Sharp/fuzzy RD、MSE/CER 带宽选择、协变量、权重、mass points、cluster/nncluster VCE |

完整支持边界见 [Open-Source Status](docs/release/open-source-status.md) 和 [Known Issues](docs/release/known-issues.md)。

## 验证状态

最近一次本地 release-candidate 检查（2026-07-09）：

- 公开单元/集成测试：`405 passed`
- 内部 modular audit：`95 passed`
- golden 双跑收集检查：`839 tests collected`
- 四个公开 demo 脚本全部通过
- wheel 构建成功：`stataflow-1.1.0-py3-none-any.whl`
- 开源导出 dry-run：选择 150 个文件，0 个 orphan 删除

Golden Stata 双跑测试需要本地 Stata 17，不属于公开 CI gate。

## 文档

- [User Guide](docs/USER_GUIDE.md)（[中文](docs/USER_GUIDE.zh-CN.md)）
- [Cookbook](docs/cookbook.md)（[中文](docs/cookbook.zh-CN.md)）
- [Examples](examples/)
- [Validation Evidence](research/results/validation/README.md)
- [Changelog](CHANGELOG.md)

## 运行测试

```bash
# 单元和集成测试
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/audit_v1_3

# Golden 双跑测试（需要本地 Stata 17）
pytest tests/golden/ -v
```

## 许可证

本项目采用 MIT License。详情见 [LICENSE](LICENSE)。
