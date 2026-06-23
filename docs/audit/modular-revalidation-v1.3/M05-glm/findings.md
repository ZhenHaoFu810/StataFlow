# M05 GLM 审查发现

## 基线信息

- 基线 commit: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- 审查日期: 2026-06-12
- Python: 3.11.7, NumPy 1.26.4, pandas 3.0.2, SciPy 1.17.1
- Stata: 17 MP

---

## 发现清单

| ID | 严重等级 | 证据状态 | 问题概述 | 受影响 API |
|---|---|---|---|---|
| M05-GLM-001 | P1 | Confirmed-Stata | `logit`/`probit`/`poisson` 包装器支持 `aweight`，但 Stata 17 官方命令拒绝 `[aweight]` | `stataflow.compat.stata.logit`, `probit`, `poisson` |
| M05-GLM-002 | P2 | Confirmed-Stata | cluster VCE 下 Python 报告 `df_resid = G-1`，而 Stata GLM 命令不定义 `e(df_r)`，使用正态 z 推断 | `Logit`/`Probit`/`Poisson`.fit(vce="cluster") |
| M05-GLM-003 | P2 | Confirmed-Stata | robust/cluster VCE 下，Python 的 `f_stat` 仍是 LR chi2；Stata 的 `e(chi2)` 变为 Wald chi2 | `Logit`/`Probit`/`Poisson` ResultSchema |
| M05-GLM-004 | P2 | Confirmed-Stata | 完全/准完全分离时，Stata 检测并立即报错 r(2000)；Python 迭代至 max_iter 后报 `RuntimeError` 并产生除零警告 | `Logit`/`Probit`/`Poisson` |
| M05-GLM-005 | P3 | Confirmed-Stata | NLSW88 行业聚类 logit 的 VCE 存在约 2e-5 相对残余，在默认 1e-6 容差下未通过 | `logit(..., vce="cluster")` |

---

## M05-GLM-001: GLM 包装器 `aweight` 与 Stata 命令不兼容

### 严重性
P1

### 证据状态
Confirmed-Stata

### 受影响 API
- `stataflow.compat.stata.logit(..., aweight=...)`
- `stataflow.compat.stata.probit(..., aweight=...)`
- `stataflow.compat.stata.poisson(..., aweight=...)`

### 问题描述
`docs/command-support-matrix/{logit,probit,poisson}.md` 和支持矩阵均将 `aweight` 列为受支持参数，但 Stata 17 官方 `logit`/`probit`/`poisson` 命令并不接受 `[aweight]` 语法，执行后返回 `r(101)`（aweights not allowed）。Python 包装器接受 `aweight` 后会通过 `GLMBase` 进行内部归一化并返回结果，导致同一参数在 Python 和 Stata 端语义不一致。

### 最小复现
见 `tests/audit_v1_3/m05_glm/repro_m05_glm_findings.py` 函数 `repro_001_aweight_rejected_by_stata()`。

```python
import pandas as pd
from stataflow.compat.stata import logit
from stataflow.stata_runner import StataRunner

df = pd.DataFrame({
    "y": [0.0, 0.0, 1.0, 1.0, 1.0],
    "x": [1.0, 2.0, 3.0, 4.0, 5.0],
    "w": [1.0, 2.0, 1.0, 2.0, 1.0],
})
py_res = logit(df, y="y", x=["x"], aweight="w")  # Python 成功
# Stata: logit y x [aweight=w] -> r(101) aweights not allowed
```

### Stata 17 结果
Stata 命令 `logit y x [aweight=w]` 输出 `aweights not allowed r(101)`，不返回系数。

### Python 结果
Python 返回成功结果（系数、SE、VCE 均基于归一化后的权重）。

### 根因分析
包装层将 Python 的 `aweight` 直接映射为 Stata 的 `[aweight]`，但 Stata 的 GLM 命令仅支持 `[fweight]`、`[pweight]`、`[iweight]`（部分命令），不支持 `[aweight]`。核心估计器 `GLMBase` 内部实现了 aweight 归一化，但 wrapper 的命令生成与 Stata 实际语法不一致。

### 用户影响
用户在 Python 端使用 `aweight` 会得到结果，但同一语法在 Stata 中无法复现，文档和支持矩阵存在夸大。

### 建议修复方向
- 将 wrapper 的 `aweight` 改为生成 Stata 可接受的权重语法（例如映射到 `iweight` 并在内部保持归一化语义），或
- 将 `aweight` 重命名为 `iweight`/`pweight` 并更新支持矩阵；或
- 对 GLM 包装器明确拒绝 `aweight` 并提示使用 `pweight`/`iweight`。

### 是否共享基础设施问题
否，特定于 GLM wrapper 的参数映射。

### 旧 issue
未发现。

---

## M05-GLM-002: cluster VCE 下 `df_resid` 语义与 Stata 不一致

### 严重性
P2

### 证据状态
Confirmed-Stata

### 受影响 API
- `Logit.fit(vce="cluster")`
- `Probit.fit(vce="cluster")`
- `Poisson.fit(vce="cluster")`

### 问题描述
`glm.py:376-379` 在 cluster VCE 下将 `df_resid` 设为 `G-1`。然而 Stata 17 的 `logit`/`probit`/`poisson` 命令在 cluster VCE 下不返回 `e(df_r)`（输出 `.`），推断值应为 `N-k`。Stata 在 cluster GLM 中使用正态 z 统计量，不基于 `G-1` 的 t 分布。因此 Python 的 `ResultSchema.fit.df_resid` 与 Stata 的 `e(df_r)` 不同，尽管该字段在 Python 中可能用于 t 分布推断。

### 最小复现
`repro_m05_glm_findings.py::repro_002_cluster_df_resid_undefined_in_stata()`

### Stata 17 结果
`logit y x1, vce(cluster g)`：`E_DF_R=.`（我们解析时退化为 `N-k`），`E_N_CLUST=10`。

### Python 结果
`df_resid = 9.0`（G-1）。

### 根因分析
`glm.py` 在 `vce == "cluster"` 分支显式覆盖 `df_resid = cluster_count - 1`，而 Stata GLM 命令本身不定义该标量。

### 用户影响
若下游代码用 `df_resid` 计算 p-value 或置信区间，可能与 Stata 的 z 推断不一致；`ResultSchema` 字段与 Stata 字段不对应。

### 建议修复方向
- 对 GLM cluster VCE，将 `df_resid` 与 Stata 一致地设为 `N-k`（或缺失/None），并明确文档化推断使用正态分布；或
- 在 `FitInfo` 中新增 `df_r_cluster` 字段以区分 cluster 自由度和 residual 自由度。

### 是否共享基础设施问题
否，GLM 特定。

---

## M05-GLM-003: robust/cluster VCE 下 `f_stat` 字段语义不一致

### 严重性
P2

### 证据状态
Confirmed-Stata

### 受影响 API
- `ResultSchema.fit.f_stat` / `f_pvalue`

### 问题描述
`glm.py:411-412` 始终计算 LR chi2：`chi2 = 2*(ll_model - ll_null)`。但 Stata 17 在 `logit/probit/poisson, vce(robust)` 和 `vce(cluster)` 下将 `e(chi2)` 报告为 **Wald chi2**，而不是 LR chi2。因此 Python 的 `f_stat` 在 robust/cluster 下与 Stata 的 `e(chi2)` 不一致，而 ols VCE 下两者均为 LR chi2。

### 最小复现
`repro_m05_glm_findings.py::repro_003_robust_chi2_is_wald_in_stata()`

### Stata 17 结果
- OLS: `e(chi2)` = 5.4511（LR chi2）
- robust: `e(chi2)` = 5.6848（Wald chi2）

### Python 结果
robust VCE 下 `fit.f_stat` = 5.4511（LR chi2）。

### 根因分析
`fit()` 方法未根据 VCE 类型切换整体检验统计量，始终使用 LR chi2。

### 用户影响
字段级比较时 `f_stat`/`f_pvalue` 不匹配；向用户暴露的统计量与 Stata 输出不同。

### 建议修复方向
- 在 robust/cluster VCE 下计算并报告 Wald chi2（基于约束 `beta=0` 的 Wald 检验），与 Stata 一致；或
- 在 `FitInfo` 中区分 `lr_chi2` 和 `wald_chi2`，并更新 `ResultSchema` 字段语义。

### 是否共享基础设施问题
否，GLM 特定。

---

## M05-GLM-004: 完全分离检测与错误处理不一致

### 严重性
P2

### 证据状态
Confirmed-Stata

### 受影响 API
- `Logit.fit()` / `Probit.fit()` / `Poisson.fit()`

### 问题描述
当数据存在完全分离时，Stata 17 在第一次迭代后立即检测并返回 `r(2000)`（`outcome = ... predicts data perfectly`）。Python 实现没有分离检测逻辑，IRLS 会继续迭代至 `max_iter=160`，最终抛出 `RuntimeError("IRLS did not converge")`，过程中产生 `divide by zero` 和 `invalid value` 警告。两者错误类型、时机和信息均不同。

### 最小复现
`repro_m05_glm_findings.py::repro_004_separation_error_handling()`

```python
df = pd.DataFrame({
    "y": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
    "x": [-2.0, -1.0, -0.1, 0.1, 1.0, 2.0],
})
Logit(df, y="y", x=["x"]).fit()  # RuntimeError: IRLS did not converge
```

### Stata 17 结果
`outcome = x > -.1 predicts data perfectly r(2000)`，不返回结果。

### Python 结果
迭代至上限后 `RuntimeError: IRLS did not converge`，伴随数值警告。

### 根因分析
`GLMBase._irls_fit` 未在每次迭代后检查完美预测或准完美预测；`_link_deriv` 对接近 0/1 的 `mu` 计算 `1/(mu*(1-mu))` 时未做保护，导致数值异常。

### 用户影响
用户无法从错误信息判断分离问题；可能误以为算法 bug；长时间无意义迭代。

### 建议修复方向
- 在 IRLS 中加入准完全/完全分离检测（例如检查线性组合是否完美预测结果）；
- 对 `mu` 和 `gprime` 增加更严格的裁剪，避免除零；
- 提供 Stata 风格的诊断信息。

### 是否共享基础设施问题
否，GLM IRLS 特定。

---

## M05-GLM-005: NLSW88 行业聚类 logit 的 VCE 存在 2e-5 相对残余

### 严重性
P3

### 证据状态
Confirmed-Stata

### 受影响 API
- `logit(..., vce="cluster", cluster="...")`

### 问题描述
在真实数据 NLSW88 的行业聚类 logit 实验中，Python 与 Stata 17 的 cluster VCE 矩阵最大相对差异约为 `2.4e-5`，超出默认 `1e-6` 容差。系数和标准误均一致，差异仅出现在 VCE 的某些非对角元素上，量级约 `2e-5`。

### 最小复现
`tests/audit_v1_3/m05_glm/test_m05_realdata.py::test_r3_nlsw88_logit_cluster()`

### Stata 17 结果
VCE 矩阵与 Python 在 1e-4 容差下一致。

### Python 结果
VCE 在 1e-6 容差下个别元素未通过。

### 根因分析
可能是大样本聚类得分求和中的浮点累积误差，或 Stata 与 NumPy 在矩阵求逆/求和顺序上的差异。系数和主对角线 SE 均高度一致，说明估计方程和聚类 meat 结构正确。

### 用户影响
对实际推断影响极小；在严格字段级比较时需要放宽容差。

### 建议修复方向
- 使用更高精度累加（例如 `np.longdouble` 或 Kahan 求和）减少 cluster meat 的浮点误差；
- 在文档中说明真实大样本 cluster VCE 的残余容差。

### 是否共享基础设施问题
可能部分与 `_vce_utils` 的数值实现有关，但主要表现在 GLM cluster 路径。

---

## 共享基础设施风险登记

- **M01-M04 已识别的 `detect_collinear_columns` 容差过松问题** 同样影响 GLM：`glm.py` 调用 `detect_collinear_columns` 检测共线性。本次 S6/P3 实验中尚未触发因容差过松导致的额外变量保留，但理论上在强共线设计下存在与 Linear/FE/HDFE/IV 模块相同的风险。建议在全局审查中统一处理。

---

## 未发现问题的说明

- 常规 OLS/robust/cluster VCE 的系数和标准误在 synthetic 和 real-data 实验中均与 Stata 17 一致（容差内）。
- logit/probit/poisson 的 log-likelihood、伪 R²、deviance（logit/poisson）在有效样本下与 Stata 一致。
- 样本筛选（缺失值）、共线性变量删除、行顺序不变性、尺度变换、冗余变量处理均验证通过。
- `eform`/`or`/`irr` 的 delta-method SE 经内部一致性检查通过（未在 findings 中列为 bug）。

---

## 变更记录

- 2026-06-12: 初始 findings，包含 M05-GLM-001 至 M05-GLM-005。
