# 项目严格审计报告

## 1. 审计范围

本次审计面向当前仓库的“开源第三方库初版”整体状态，重点检查：

- `research/vendor/stata_community/` 下开源 Stata 社区命令的复现完整度与正确性
- `src/stataflow/compat/stata/` 命令层接口是否与 Stata 语义一致
- core estimator、wrapper、文档、测试三者是否一致
- 当前代码是否达到“可公开发布的初版库”标准

本次审计不以“测试是否全绿”作为唯一判断标准，而以：

1. 源码/手册支撑下的数学与计量过程一致性  
2. 命令语义与参数面的完整性  
3. 文档、接口、结果对象与行为的一致性  

为主判断依据。

## 2. 审计环境与验证命令

### 环境

- OS: Windows
- Python: `3.11.7`
- 解释器: `C:\ProgramData\anaconda3\python.exe`
- 工作目录: `D:\OneDrive - SAIF\PhD3\Stata2Python`
- Stata 目标版本: 17

### 本轮实际执行的验证

#### 基线测试

```powershell
python -m pytest tests -v
```

结果：

- `681 passed in ~150s`

#### 示例脚本抽查

```powershell
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

结果：

- 四个示例均可运行

#### 结构与实现抽查

已核对：

- `src/stataflow/compat/stata/__init__.py`
- `src/stataflow/compat/stata/linear.py`
- `src/stataflow/compat/stata/hdfe.py`
- `src/stataflow/compat/stata/iv.py`
- `src/stataflow/compat/stata/glm.py`
- `src/stataflow/compat/stata/did.py`
- `docs/command-support-matrix/*`
- `docs/research/*-source-map.md`
- `research/vendor/stata_community/*`

## 3. 全库总体结论

### 结论摘要

当前仓库已经是一个**高质量、强验证、可运行的 Stata 对齐型计量库 Alpha 版本**，但**尚不能被认定为“全面完成的 Stata 开源命令完整复现库”**。

更准确的定位是：

- 数值与统计结果对齐框架已经成熟
- 高价值命令的高频路径已大面积实现并通过 synthetic + real-data 双线验证
- 命令层 API 已经显著改善，可直接使用 Stata 风格 wrapper
- 但 `vendor` 下社区命令整体仍主要停留在“高频子集 + 清晰边界 + 强测试”的阶段，而不是“完整命令级复现”

### 发布判断

按“研究型 Alpha / 技术预发布”的标准：**基本可发布**。  
按你当前要求的更严格标准，即：

- `vendor` 下开源命令必须完整、全面、正确复现
- 不能接受只实现核心路径而非完整命令

则当前版本**不满足最终标准**，原因见后文。

## 4. 分命令结论总表

### 4.1 Vendor 开源命令审计表

| 命令 | Python 入口 | wrapper 入口 | 测试状态 | 审计评级 | 结论 |
| --- | --- | --- | --- | --- | --- |
| `reghdfe` | `AbsorbingOLS` | `stataflow.compat.stata.reghdfe` | synthetic + real-data 通过 | `partial` | 核心路径成熟，但不是完整 `reghdfe` |
| `ivreghdfe` | `IVAbsorbingOLS` | `stataflow.compat.stata.ivreghdfe` | synthetic + real-data 通过 | `partial` | 2SLS + FE 主路径可用，但命令面明显不完整 |
| `ppmlhdfe` | `PPMLHDFE` | `stataflow.compat.stata.ppmlhdfe` | synthetic + real-data 通过 | `partial` | PPML-HDFE 主路径可用，但 separation 等关键功能未完成 |
| `did_imputation` | `DIDImputation` | `stataflow.compat.stata.did_imputation` | synthetic + real-data 通过 | `partial` | 基本 BJS 路径可用，但参数面远未完整 |
| `eventstudyinteract` | `EventStudyInteract` | `stataflow.compat.stata.eventstudyinteract` | synthetic + real-data 通过 | `partial` | IW 估计核心可用，但命令面仍是子集 |
| `rdrobust` | `RDRobust` | `stataflow.compat.stata.rdrobust` | synthetic + real-data 通过 | `partial` | Sharp RD 最小子集可用（需显式带宽），自动带宽选择、模糊 RD、协变量未实现 |

### 4.2 其他高频命令结论

| 命令 | 审计评级 | 结论 |
| --- | --- | --- |
| `regress` | `strong_subset` | 高频线性回归路径成熟，但权重类型和完整命令面未完成 |
| `xtreg, fe` | `strong_subset` | 单 FE within 路径成熟，仍非完整 `xtreg` |
| `areg` | `strong_subset` | 单吸收 FE 命令语义清楚，可稳定使用 |
| `ivregress 2sls` | `strong_subset` | 2SLS 高频路径成熟，但诊断工具链不完整 |
| `logit` / `probit` / `poisson` | `strong_subset` | MLE 高频路径成熟，wrapper 清楚，完整命令面未完成 |
| `csdid` | `partial` | `method="reg"` 路径成熟，但不是完整 `csdid` |
| `predict` / `margins` 高频子集 | `strong_subset` | 核心层可用，wrapper 层不直接暴露，边界已清楚 |

## 5. Vendor 命令逐项结论

### 5.1 `reghdfe`

#### 已确认成立

- 有本地源码镜像与 source map
- 已有正式 wrapper：`stataflow.compat.stata.reghdfe`
- 已通过 synthetic 与 real-data 双线验证
- 已实现并验证：
  - `absorb()` 1-2 个分类 FE
  - `vce(ols)` / `vce(robust)` / `vce(cluster)`
  - singleton 默认剔除
  - 基础 `df_a`
  - `predict(xb)` / `predict(residuals)` 在 core estimator 层

#### 不能认定为完整复现的原因

- 仅支持 1-2 个分类 FE，不足以覆盖用户通常理解的“高维固定效应完整任务”
- 未完成 mobility-group 等更复杂 DoF 逻辑
- 未支持 slopes、individual/group/team FE 等更完整命令面
- 不支持 multi-way clustering
- `keepsingletons` 等关键选项未暴露
- postestimation 不是命令层完整复现

#### 审计判断

`reghdfe` 当前是**高质量的 Phase A 子集实现**，不是完整、全面复现。

### 5.2 `ivreghdfe`

#### 已确认成立

- 有本地源码镜像与 source map
- 有正式 wrapper
- 已通过 synthetic 与 real-data 验证
- 已支持 2SLS + 1-2 FE + robust/cluster 高频路径

#### 不能认定为完整复现的原因

- 仅覆盖最小 2SLS 路径
- first-stage 报告、弱工具诊断、过识别检验等工具链未完成
- 更广的命令选项面未完成
- multi-way cluster 未完成

#### 审计判断

`ivreghdfe` 当前是**可用的最小子集实现**，不是完整 `ivreghdfe`。

### 5.3 `ppmlhdfe`

#### 已确认成立

- 有本地源码镜像与 source map
- 有正式 wrapper
- 已通过 synthetic 与 gravity 风格真实数据验证
- 已支持：
  - `absorb()`
  - `vce(ols)` / `vce(robust)` / `vce(cluster)`
  - `offset` / `exposure`
  - `predict(xb)` / `predict(mu)` 在 core estimator 层

#### 不能认定为完整复现的原因

- separation 检测尚未实现，而这恰恰是 `ppmlhdfe` 的关键复杂点之一
- `deviance` / `pseudo R2` / `LR chi2` 等输出层不完整
- `predict residuals` 未实现
- 命令参数面远不完整
- multi-way cluster 未完成

#### 审计判断

`ppmlhdfe` 当前是**强可用的高频主路径实现**，但不是完整社区命令复现。

### 5.4 `did_imputation`

#### 已确认成立

- 有本地源码镜像与 source map
- 有正式 wrapper
- synthetic 与真实数据均已通过
- `cluster`、`allhorizons`、`autosample` 可用

#### 不能认定为完整复现的原因

- `minn`、`window`、`pretrend` 等参数面未完成
- FE / truncation 等更完整命令行为未支持

#### 审计判断

是一个**核心路径已完成的子集实现**，不是完整命令。

### 5.5 `eventstudyinteract`

#### 已确认成立

- 有本地源码镜像与 source map
- wrapper 已支持自动生成 relative-time dummies
- synthetic 与真实数据验证通过

#### 不能认定为完整复现的原因

- `window`、`minn` 等参数未完成
- 结果输出与扩展命令面不完整
- 虽然 wrapper 已较接近命令语义，但仍是高频场景导向的子集

#### 审计判断

是一个**相当实用的 IW 子集实现**，但不是完整复现。

### 5.6 `rdrobust`

#### 已确认成立

- 已有本地源码镜像：`research/vendor/stata_community/rdrobust/`
- 已实现最小子集：`RDRobust` estimator + `rdrobust` wrapper
- 支持 sharp RD（`deriv=0`）的局部多项式 WLS + 偏差修正 + 稳健推断
- 支持显式带宽 `h`、核函数选择、`vce="nn"` / `vce="hc0"`
- 已通过 synthetic 和 `rdrobust_senate.dta` 真实数据 dual-run 验证

#### 不能认定为完整复现的原因

- 不支持自动带宽选择（`bwselect` 等），必须显式提供 `h`
- 不支持模糊 RD（`fuzzy`）
- 不支持协变量调整（`covs`）
- 不支持 `deriv > 0`（kink designs）
- 不支持权重和聚类稳健 VCE

#### 审计判断

`rdrobust` 当前是**最小可用子集实现**，不是完整社区命令复现。

## 6. 代码质量、稳定性与可用性判断

### 6.1 代码质量

总体判断：**中高水平，工程结构清楚，审查与测试文化明显优于一般研究型仓库。**

优点：

- estimator / wrapper / docs / golden tests 分层清楚
- 命令层 wrapper 已与 core estimator 解耦
- unsupported 参数普遍是显式报错，而不是静默忽略
- source map 与 support matrix 体系已经形成

主要保留意见：

- 个别 core estimator 仍同时承载多个命令语义，例如 `AbsorbingOLS`
- 一些“完整命令”在文档上已经写得很清楚是 `Alpha`，但从产品直觉上仍容易被误用为“已完整支持”

### 6.2 稳定性

总体判断：**强。**

证据：

- 全量 `489` 个测试通过
- wrapper、golden、real-data、postestimation 都已纳入回归集
- 示例脚本可运行

保留意见：

- 测试覆盖很强，但当前覆盖的是“已宣称支持的功能边界”
- 测试全绿并不等于命令完整复现

### 6.3 易用性

总体判断：**显著优于此前版本，但仍未达到“无 Stata 背景也能一眼明白完整支持范围”的程度。**

优点：

- `compat.stata` wrapper 层已经解决了大部分命令命名门槛
- README 与 support matrix 已经说明 wrapper 不直接暴露 `predict` / `margins`

问题：

- wrapper 名称与 Stata 对齐了，但“完整命令 vs 子集实现”的边界仍需要用户读文档才清楚
- 缺少一份面向外部开源用户的“已完整支持 / 仅子集支持 / 尚未实现”总览结论

## 7. 最终判断

### 按宽松标准

如果标准是：

- 作为一个可运行、强验证、Stata 对齐导向的 Python 计量库 Alpha 版本

则当前项目**已经达到较高质量水平**。

### 按你当前给出的严格标准

如果标准是：

- `research/vendor/stata_community` 下这些开源命令必须已经被**完整、全面、正确**复现
- 不能接受“只实现核心功能但不是完整命令”

则当前项目**未达到标准**。

根本原因不是代码差，也不是测试差，而是：

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

都仍是**高频主路径/核心子集复现**，不是完整命令复现。

因此，当前更合理的外部表述应是：

> 这是一个经过严格验证的 Stata 对齐型 econometrics library Alpha，已覆盖多类高频命令的高频路径，但尚未完成对所有社区命令的完整复现。

