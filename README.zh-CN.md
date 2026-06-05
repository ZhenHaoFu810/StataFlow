# StataFlow

**一个高精度复现 Stata 17 结果的 Python 计量经济学工具包。**

[![PyPI version](https://img.shields.io/pypi/v/stataflow)](https://pypi.org/project/stataflow/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

```python
from stataflow.compat.stata import reghdfe

result = reghdfe(df, y="lwage", x=["exper", "edu"],
                 absorb="firm_id year_id", vce="cluster", cluster="firm_id")
result.display()
```

---

## 功能特性

- **14 个 Stata 命令**：`regress`、`reghdfe`、`ivregress 2sls`、`ivreghdfe`、`logit`、`probit`、`poisson`、`ppmlhdfe`、`did_imputation`、`eventstudyinteract`、`csdid`、`rdrobust`、`areg`、`xtreg_fe`
- **Stata 风格回归表**：`result.display()` 一键输出与 Stata 对齐的格式化表格
- **高维固定效应**：MAP 迭代吸收处理万级以上 FE 无内存溢出；个体斜率吸收（`absorb(firm_id##c.time)`）
- **Driscoll-Kraay 面板 HAC 标准误**：Bartlett 核时间序列自相关修正
- **工具变量**：2SLS、GMM2S、LIML 估计器，含一阶段诊断、弱工具变量检验（Kleibergen-Paap F + Stock-Yogo 临界值）及过度识别检验（Sargan / Hansen J）
- **二元/计数/PPML 模型**：Logit、Probit、Poisson、PPML（含高维固定效应）
- **因果推断**：DID（BJS imputation、Sun-Abraham、Callaway-Sant'Anna）；断点回归（9 个 MSE+CER 带宽选择器）
- **Stata 兼容语法**：因子变量（`i.group##c.post`）、分析权重、多组 FE
- **Stata 17 验证**：每个对外功能均有 Python-Stata 双跑验证证据

## 安装

```bash
pip install StataFlow
```

需要 Python 3.10+。依赖：NumPy、pandas、SciPy。

## 快速开始

### Stata 兼容 API

```python
import pandas as pd
from stataflow.compat.stata import regress, reghdfe, logit, ivregress_2sls, ppmlhdfe

# OLS + 异方差稳健标准误
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")
result.display()

# 高维固定效应
result = reghdfe(
    df, y="wage", x=["edu", "exper"],
    absorb="firm_id year_id", vce="cluster", cluster="industry"
)

# Logit
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
result.display()

# 2SLS + LIML
result = ivregress_2sls(
    df, y="lwage", x_exog=["edu"], x_endog=["exper"],
    instruments=["age", "kidslt6"], vce="robust"
)

# PPML + HDFE（引力模型）
result = ppmlhdfe(
    df, y="trade", x=["lndist", "contig", "fta"],
    absorb=["exporter", "importer", "year"], vce="cluster", cluster="exporter"
)
```

### Python 原生 API

```python
from stataflow import OLS, AbsorbingOLS, Logit

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
result.display()
```

### 使用结果

```python
# Stata 风格表格
result.display()
result.display(show_ci=True)  # 含置信区间

# 程序化访问
for c in result.coefficients:
    print(f"{c.name}: b={c.beta:.6f}, se={c.std_err:.6f}, t={c.t_stat:.2f}")

print(f"R² = {result.fit.r2:.4f}, N = {result.sample.nobs}")
```

## 支持的模型

| 族 | 可用命令 | 估计器与 VCE |
|----|---------|-------------|
| **线性** | `regress`, `areg`, `xtreg_fe`, `reghdfe` | OLS，支持 `ols` / `robust` (HC1) / `cluster` (单向、双向) / `dkraay` (面板 HAC) |
| **IV** | `ivregress_2sls`, `ivreghdfe` | 2SLS、GMM2S、LIML (含 Fuller)、一阶段诊断、弱工具检验 |
| **二元/计数** | `logit`, `probit`, `poisson` | MLE，支持 `ols` / `robust` / `cluster` |
| **PPML + HDFE** | `ppmlhdfe` | IRLS，支持 `ols` / `robust` / `cluster`，分离检测，eform |
| **DID** | `did_imputation`, `csdid`, `eventstudyinteract` | BJS imputation、Callaway-Sant'Anna (reg + DR)、Sun-Abraham IW |
| **RDD** | `rdrobust` | Sharp / Fuzzy RD、9 个 MSE+CER 带宽选择器、cluster/nncluster VCE |

## 文档

- [用户手册](docs/USER_GUIDE.md) — 完整教程与概念指南（英文: [User Guide](docs/USER_GUIDE.zh-CN.md)）
- [Cookbook](docs/cookbook.md) — 可复制的配方示例（英文: [Cookbook](docs/cookbook.zh-CN.md)）
- [示例](examples/) — 可运行的 demo 脚本
- [v1.1.0 更新日志](docs/release/open-source-update-log-1.1.0.md) — 最新热修复的更新内容

## 运行测试

```bash
# 单元与集成测试
pytest tests/ -v --ignore=tests/golden/

# Golden 双跑测试（需要本地 Stata 17）
pytest tests/golden/ -v
```

## 许可证

MIT License。详见 [LICENSE](LICENSE)。
