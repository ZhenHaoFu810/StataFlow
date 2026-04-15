# Stata / SSC 源码与规则清单

## 使用方式

本清单用于回答三个问题：

- 这个命令能否直接研究公开源码
- 若能，源码镜像在本地哪里
- 若不能，应该依赖什么官方资料和双跑路径

## A 类：公开源码优先

| 命令 | 类型 | 本地镜像目录 | 版本 | 许可证 | 关键源码入口 | 最小实现子集 | 研究优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `reghdfe` | GitHub / SSC | `research/vendor/stata_community/reghdfe/` | 6.13.1 (GitHub) / 6.12.3 (SSC) | 开源社区模块 | `src/reghdfe.ado` → `Estimate` → `reghdfe.mata` → `FE.mata` / `Regression.mata` / `DoF.mata` | `absorb()` 1-2 组、`vce(ols/robust/cluster)`、默认 drop singletons | 高 |
| `ivreghdfe` | GitHub / SSC | `research/vendor/stata_community/ivreghdfe/` | master | 开源社区模块 | `src/ivreghdfe.ado` | 依赖 `reghdfe` + `ivreg2` | 高 |
| `ppmlhdfe` | GitHub / SSC | `research/vendor/stata_community/ppmlhdfe/` | master | 开源社区模块 | `ppmlhdfe-master` 目录 | Poisson + HDFE + cluster | 高 |
| `did_imputation` | GitHub | `research/vendor/stata_community/did_imputation/` | main | 开源社区模块 | `did_imputation.ado` | DID imputation estimator | 中 |
| `eventstudyinteract` | GitHub | `research/vendor/stata_community/eventstudyinteract/` | main | 开源社区模块 | `eventstudyinteract.ado` | Event-study interaction | 中 |
| `rdrobust` | GitHub | `research/vendor/stata_community/rdrobust/` | — | 开源社区模块 | — | 断点回归 | 中 |

## B 类：官方手册优先

| 命令 | 主要来源 | 关键手册入口 | 关键 `e()` 返回 | 最小实现子集 | 研究优先级 |
| --- | --- | --- | --- | --- | --- |
| `regress` | 官方手册 + `e()` 返回值 + 双跑 | `help regress` | `N`, `df_m`, `df_r`, `r2`, `rmse`, `F`, `b`, `V` | OLS + constant + collinearity drop | 高 |
| `xtreg, fe` | 官方手册 + `e()` 返回值 + 双跑 | `help xtreg` | `N`, `N_g`, `df_m`, `df_r`, `r2_w`, `rmse`, `F`, `b`, `V` | within transformation、单向 FE、df 口径 | 高 |
| `areg` | 官方手册 + `e()` 返回值 + 双跑 | `help areg` | `N`, `df_m`, `df_r`, `df_a`, `r2`, `r2_a`, `rmse`, `F`, `b`, `V` | 单吸收变量、`_cons` 报告、与 `xtreg, fe` 等价性 | 高 |
| `ivregress` | 官方手册 + `e()` 返回值 + 双跑 | `help ivregress` | `N`, `df_m`, `df_r`, `b`, `V` | 2SLS、第一阶段、弱工具检验 | 中 |
| `logit` | 官方手册 + `e()` 返回值 + 双跑 | `help logit` | `N`, `b`, `V`, `ll` | MLE、odds ratio、LR test | 中 |
| `probit` | 官方手册 + `e()` 返回值 + 双跑 | `help probit` | `N`, `b`, `V`, `ll` | MLE、边际效应 | 中 |
| `poisson` | 官方手册 + `e()` 返回值 + 双跑 | `help poisson` | `N`, `b`, `V`, `ll`, `deviance` | MLE、exposure/offset | 中 |

## 研究要求

每个条目后续都应补：

- 版本信息
- 许可证信息
- 关键源码入口或手册入口
- 关键返回结果
- 最小实现子集
