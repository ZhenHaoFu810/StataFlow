# REV-IV — IV / GMM 命令族源码审查报告

## 元信息
- **命令族**: `ivregress 2sls`, `ivreghdfe`
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03
- **审查人**: Agent 子审查

---

## 汇总表格

| 严重度 | 问题类型 | 数量 |
|--------|---------|------|
| Blocker | 数学偏差 / 路径不一致 | 2 |
| Critical | API设计缺陷 / 数学偏差 / 参数缺失 | 5 |
| Major | 参数缺失 / 输出不完整 / 边界case | 8 |
| Minor | API不便利 / 文档不一致 | 6 |
| **合计** | | **21** |

---

## 问题详情（按严重度排序）

---

# REV-IV-01

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Blocker
- **问题类型**: 数学偏差 / 路径不一致

## 现象描述
`ivreghdfe` GMM2S 在 `vce="cluster"` 下存在两条计算路径：
1. **主路径** (`_fit_gmm2s`): 当 `omega` 非奇异时，VCE 公式为 `V = inv(Q) / N`，**完全不施加** 聚类小样本修正（无 `G/(G-1)`、无 `(N-1)/(N-L)`）。
2. **Fallback 路径** (`_fit_gmm2s_residualized`): 当 `omega` 奇异（如 cluster 嵌套 FE）时，VCE 额外乘以 `g_adj * n_adj`（`G/(G-1) * (N-1)/(N-L)`）。

**后果**: 同一模型、同一数据，仅因 cluster 是否与 FE 嵌套，就会产生不同的标准误。当前测试 `test_w10_gmm2s_cluster.py` 恰好使用 `absorb(entity_id) vce(cluster entity_id)`，触发了 fallback 路径并通过；但 **非嵌套场景的主路径从未被验证**，且数学上与 Stata 行为不一致。

## 最小复现代码
```python
import numpy as np
import pandas as pd
from stataflow.estimators.iv import IVAbsorbingOLS

np.random.seed(42)
n = 200
df = pd.DataFrame({
    'entity_id': np.repeat(np.arange(40), 5),
    'time_id': np.tile(np.arange(5), 40),
    'z1': np.random.normal(size=n),
    'z2': np.random.normal(size=n),
    'x1': np.random.normal(size=n),
    'v': np.random.normal(size=n),
})
df['x2'] = 0.5*df.z1 + 0.3*df.z2 + 0.2*df.x1 + df.v
df['u'] = np.random.normal(size=n) + 0.3*df.v
df['y'] = 1 + 2*df.x1 + 1.5*df.x2 + df.u

# 非嵌套 cluster：cluster=time_id, absorb=entity_id
model = IVAbsorbingOLS(
    data=df, y='y', x_exog=['x1'], x_endog=['x2'],
    instruments=['z1', 'z2'], absorb='entity_id'
)
res = model.fit(vce='cluster', cluster='time_id', estimator='gmm2s')
# 对比 Stata：ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) vce(cluster time_id) gmm2s
# Python SE 会与 Stata 存在系统性偏差（缺少 g_adj * n_adj）
```

## 根因分析
- `_fit_gmm2s` (主路径) 在 Step 4 直接返回 `V = inv(Q) / N`，仅对 `vce=="ols"` 做了 `N/df_resid` 修正，对 cluster/robust 完全无小样本修正。
- `_fit_gmm2s_residualized` (fallback) 在 Step 4 之后显式追加了 `g_adj * n_adj`（line 1150–1161）。
- 两条路径逻辑未统一，导致估计结果依赖于数值稳定性条件（omega 是否奇异）。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 973–1060, 1062–1177)

## 影响评估
- **影响范围**: `ivreghdfe` GMM2S + cluster VCE
- **用户workaround**: 无
- **是否阻塞实际使用**: 是（非嵌套 cluster 场景 SE 不可靠）

## 修复建议
1. 在主路径 `_fit_gmm2s` 的 Step 4 之后，统一追加与 fallback 一致的 cluster/robust 小样本修正：
   - `cluster`: `g_adj * n_adj`
   - `robust`: `n / (n - k_x_full)` (HC1)
2. 添加非嵌套 cluster 的 golden test（如 `absorb(entity_id) vce(cluster time_id)`）。

## 关联项
- `docs/research/ivreghdfe-gmm.md` §4.1
- `tests/golden/test_w10_gmm2s_cluster.py`（仅覆盖嵌套场景）

---

# REV-IV-02

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Blocker
- **问题类型**: 数学偏差

## 现象描述
`ivreghdfe` 2-way cluster 场景下，`fit()` 调用 `fix_psd_reghdfe(cov_reported)`（line 1463–1465）。该函数在 `src/stataflow/estimators/_vce_utils.py` 中**硬假设 `_cons` 是 VCE 矩阵的最后一行/列**（line 35–57），其逻辑为：
- 备份 `k-1` 行（即除 `_cons` 外的所有 slope 系数）
- PSD fix 后恢复备份

但 `ivreghdfe` **从不报告 `_cons`**（line 639: `self._coef_names = kept_x_endog_names + kept_x_exog_names`，不含 `_cons`）。因此 `cov_reported` 的维度 `k x k` 中**全部为 slope 系数**。`fix_psd_reghdfe` 会错误地将最后一个 slope（如最后一个 `x_exog`）当作 `_cons` 处理，导致：
- 该系数被 PSD fix 修改（不应被修改）
- 其余 `k-1` 个系数被强制保留原值（本应全部接受 PSD fix 或全部保留）

## 最小复现代码
```python
import numpy as np, pandas as pd
from stataflow.estimators.iv import IVAbsorbingOLS

np.random.seed(1)
n = 100
df = pd.DataFrame({
    'fe': np.repeat(np.arange(10), 10),
    'z1': np.random.normal(size=n),
    'z2': np.random.normal(size=n),
    'x1': np.random.normal(size=n),
    'v': np.random.normal(size=n),
})
df['x2'] = df.z1 + df.v
df['y'] = df.x1 + df.x2 + np.random.normal(size=n)

model = IVAbsorbingOLS(
    data=df, y='y', x_exog=['x1'], x_endog=['x2'],
    instruments=['z1', 'z2'], absorb='fe'
)
res = model.fit(vce='cluster', cluster=['fe', 'z2'], estimator='2sls')
# cov_reported 经 fix_psd_reghdfe 后，最后一个系数的 SE 可能被错误修改
```

## 根因分析
- `_vce_utils.fix_psd_reghdfe` 的设计文档（ADR-0004）明确说明"Assumes _cons is the last row/col"，这一假设对 `reghdfe`（报告 `_cons`）成立，但对 `ivreghdfe`（不报告 `_cons`）不成立。
- `IVAbsorbingOLS.fit()` 在调用 `fix_psd_reghdfe` 前未检查 `_cons` 是否存在。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 1463–1465)
- `src/stataflow/estimators/_vce_utils.py` (lines 35–57)

## 影响评估
- **影响范围**: `ivreghdfe` + multi-way cluster + 任意 estimator
- **用户workaround**: 无
- **是否阻塞实际使用**: 是（2-way cluster 下 VCE 结构被破坏）

## 修复建议
1. 在 `IVAbsorbingOLS.fit()` 中，调用 `fix_psd_reghdfe` 前判断 `"_cons" in self._coef_names`：
   - 若存在，调用 `fix_psd_reghdfe`
   - 若不存在，调用 `fix_psd`（全部系数统一处理）
2. 或修改 `fix_psd_reghdfe` 增加 `has_cons: bool = True` 参数。

## 关联项
- ADR-0004
- `tests/golden/test_w7_ivreghdfe_2way_cluster.py`

---

# REV-IV-03

## 元信息
- **命令**: `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 数学偏差

## 现象描述
`IV2SLS.fit()` 对所有 `vce` 类型均使用 **z-统计量**（正态分布）计算 p-value 和置信区间（lines 237–239, 286–293）。但 Stata 17 `ivregress 2sls` 的文档明确说明：
- `vce(ols)` → 使用 **t-统计量**，自由度 `df = N - K`
- `vce(robust)` / `vce(cluster)` → 使用 **z-统计量**（渐近正态）

当前实现使 conventional VCE 下的 p-value / CI 与 Stata 存在系统性差异，尤其在样本量较小时不可忽略。

## 根因分析
- `IV2SLS.fit()` 中 `df_resid = None`（line 238），`df_stat = float('inf')`（line 239）。
- 后续统一使用 `scipy.stats.norm`（lines 286–288），未根据 `vce` 切换为 `t_dist`。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 237–239, 286–293)

## 影响评估
- **影响范围**: `ivregress 2sls` 全场景
- **用户workaround**: 无
- **是否阻塞实际使用**: 否（系数和 SE 正确，但推断统计量在小样本偏差）

## 修复建议
1. 当 `vce == "ols"` 时，设置 `df_resid = n - k_x`，使用 `t_dist` 计算 p-value / CI。
2. 当 `vce != "ols"` 时，保持 `df_stat = inf`，使用 `norm`。
3. 同步更新 `ivregress_2sls` wrapper 使其返回 `df_resid`。

## 关联项
- `tests/golden/test_w2_ivregress_basic.py`（未检测 t/z 差异）

---

# REV-IV-04

## 元信息
- **命令**: `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 边界case崩溃 / 数学偏差

## 现象描述
`IV2SLS._prepare_data()` 对回归矩阵 `X` 和工具矩阵 `Z` **分别独立进行共线性检测**（lines 150–153）。`X` 和 `Z` 的列顺序不同：
- `X` = [x_endog, x_exog, constant]
- `Z` = [instruments, x_exog, constant]

若 `x_exog` 内部存在共线性，QR 分解在两矩阵中可能**丢弃不同的列**（取决于列顺序和数值稳定性），导致：
- `X` 保留的 `x_exog` 集合 ≠ `Z` 保留的 `x_exog` 集合
- 后续 2SLS 中，第一阶段投影矩阵与第二阶段回归量不匹配
- 可能产生无意义的标准误或估计量偏差

## 根因分析
- 共线性检测应先在完整的 `[X, Z_instruments]` 或至少在 `Z` 上进行，然后令 `X` 的 `x_exog` 子集与 `Z` 的 `x_exog` 子集严格一致。
- `IVAbsorbingOLS` 采用全矩阵共线性检测（line 610），避免了此问题；`IV2SLS` 未复用该模式。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 80–163, esp. 150–153)

## 影响评估
- **影响范围**: `ivregress 2sls`
- **用户workaround**: 无（用户无法控制 QR 列选择）
- **是否阻塞实际使用**: 是（共线性数据下结果不可靠）

## 修复建议
1. 重构 `IV2SLS._prepare_data()`: 先构建 `Z`，检测共线性；然后令 `X` 的 `x_exog` / `constant` 列与 `Z` 保持一致（或反之）。
2. 或直接构建联合矩阵 `M = [X, Z_excl]` 进行统一共线性检测。

---

# REV-IV-05

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 参数缺失 / 数学未实现

## 现象描述
多内生变量（`k_endog > 1`）时，`_compute_weakiv_stats()` 对 `idstat` 和 `widstat` 均返回 `np.nan`（lines 809–811, 814–899 仅在 `k_endog == 1` 分支有实现）。

这意味着：
- **不可识别检验 (Kleibergen-Paap rk LM)**: 完全缺失
- **弱识别检验 (Kleibergen-Paap rk Wald F)**: 完全缺失
- **Stock-Yogo 临界值**: 虽返回，但无法与任何统计量对比

Stata `ivreghdfe` 对多内生变量完整输出上述统计量（基于 `ranktest` 的 SVD 分解）。当前实现仅支持单内生变量，属于重大功能缺口。

## 根因分析
- 单内生变量的 LM 和 Wald F 可用 OLS / 投影公式显式计算。
- 多内生变量需要计算 canonical correlations 或 `ranktest` 的 SVD-based rk 统计量，实现复杂度更高，当前版本未覆盖。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 691–922, esp. 753–811, 814–899)

## 影响评估
- **影响范围**: `ivreghdfe` + 多内生变量
- **用户workaround**: 无
- **是否阻塞实际使用**: 是（多内生变量模型无法获得弱工具诊断）

## 修复建议
1. 实现多内生变量的 Kleibergen-Paap rk LM 和 rk Wald F，最小可行路径：
   - 使用 `scipy.linalg.svd` 或广义特征值分解近似 `ranktest` 行为
   - 参考 `docs/research/ivreghdfe-weakiv.md` §8.1 的伪代码框架
2. 添加合成数据 golden test（`k_endog = 2, k_excl = 3`）。

---

# REV-IV-06

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 数学偏差

## 现象描述
`stock_yogo_critical_values()` 对 LIML 模型 **忽略 `fuller` 参数**（`_stock_yogo.py` line 167: "fuller parameter (only affects LIML; not yet implemented)"）。但 Stata `ivreg2` 的 `s_cdsy()` 函数明确根据 `fuller` 值调整 LIML 临界值（见 `docs/research/ivreghdfe-weakiv.md` §4.3）。

后果：用户使用 `estimator="liml", fuller=1` 时，得到的 Stock-Yogo 临界值与标准 LIML 相同，而非 Fuller-adjusted LIML 的临界值，可能导致错误的弱工具判断。

## 根因分析
- `_stock_yogo.py` 的 LIML 表为静态硬编码，未区分 `fuller=0, 1, 4` 等情形。

## 涉及文件
- `src/stataflow/estimators/_stock_yogo.py` (lines 149–193)
- `src/stataflow/estimators/iv.py` (lines 902–908)

## 影响评估
- **影响范围**: `ivreghdfe` LIML + Fuller 修正
- **用户workaround**: 无
- **是否阻塞实际使用**: 否（偏差在临界值查表，估计量本身不受影响）

## 修复建议
1. 查阅 ivreg2 Mata 库 `s_cdsy()` 中 Fuller 参数对 LIML 临界值的调整公式。
2. 在 `stock_yogo_critical_values()` 中增加 `fuller` 分支逻辑，或补充 Fuller-specific 查表。

---

# REV-IV-07

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 参数硬拒绝

## 现象描述
`ivreghdfe()` wrapper 对 `**kwargs` 一律 `raise ValueError`（line 90–91）。以下 Stata 合法高频参数被硬拒绝：
- `orthog(varlist)` — 正交性检验（C 统计量）
- `endogtest(varlist)` — 内生性检验
- `redundant(varlist)` — 冗余工具变量检验
- `partial(varlist)` —  partialling out
- `fwl` — Frisch-Waugh-Lovell 变换

这些参数在 Stata 社区命令 `ivreghdfe` 中属于常见选项。硬拒绝虽符合"不静默忽略"原则，但用户无法通过任何方式启用这些功能，且错误信息未区分"已知未实现"与"未知参数"。

## 根因分析
- Wrapper 层未维护允许参数白名单，未对高频但未实现参数给出友好提示（如 `NotImplementedError`）。

## 涉及文件
- `src/stataflow/compat/stata/iv.py` (lines 90–91)

## 影响评估
- **影响范围**: `ivreghdfe` wrapper
- **用户workaround**: 无
- **是否阻塞实际使用**: 否（功能缺失，但不 crash）

## 修复建议
1. 在 wrapper 中显式捕获高频参数并抛出 `NotImplementedError`，附带说明预计实现版本。
2. 或在 `docs/command-support-matrix/ivreghdfe.md` 中增加"高频硬拒绝参数列表"，减少用户困惑。

---

# REV-IV-08

## 元信息
- **命令**: `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失 / API设计缺陷

## 现象描述
`ivregress_2sls()` wrapper **完全不支持一阶段诊断** (`first`, `ffirst`)。底层 `IV2SLS` 类也没有 `first` 参数或相关实现。Stata 17 `ivregress 2sls, first` 输出每个内生变量的第一阶段 R²、偏 R²、F 统计量等，是 IV 实证工作的标准需求。

## 涉及文件
- `src/stataflow/compat/stata/iv.py` (lines 11–43)
- `src/stataflow/estimators/iv.py` (`IV2SLS.fit()` 无 `first` 参数)

## 影响评估
- **影响范围**: `ivregress 2sls`
- **用户workaround**: 手动跑 OLS 第一阶段
- **是否阻塞实际使用**: 否

## 修复建议
1. 在 `IV2SLS.fit()` 增加 `first: bool = False` 参数。
2. 对每个内生变量运行第一阶段 OLS（`x_endog ~ instruments + x_exog + constant`），输出 `r2`, `partial_r2`, `f_stat`, `f_pvalue`。
3. wrapper 层透传 `first=True`。

---

# REV-IV-09

## 元信息
- **命令**: `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失

## 现象描述
`ivregress_2sls()` wrapper 没有 `noconstant` 参数，也未透传 `add_constant` 给 `IV2SLS`。用户无法运行无常数项的 2SLS，而 Stata 的 `ivregress 2sls, noconstant` 是合法命令。

## 涉及文件
- `src/stataflow/compat/stata/iv.py` (lines 11–43)

## 影响评估
- **影响范围**: `ivregress 2sls`
- **用户workaround**: 直接调用 `IV2SLS(data, ..., add_constant=False)`
- **是否阻塞实际使用**: 否

## 修复建议
1. wrapper 增加 `noconstant: bool = False`，透传为 `add_constant=not noconstant`。

---

# REV-IV-10

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 数学偏差

## 现象描述
`ivreghdfe` LIML 估计量在 `vce="robust"` 或 `vce="cluster"` 下，VCE 计算（`_fit_liml` lines 1269–1298）**缺少小样本修正**：
- `robust`: 未施加 HC1 修正 `n/(n-k)`
- `cluster`: 未施加 `G/(G-1)` 和 `(N-1)/(N-k)` 修正

虽然 LIML 的渐近理论不要求这些修正，但 Stata `ivreg2` 的默认行为包含它们，导致与 Stata 的字段级对齐存在残余偏差。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 1269–1298)

## 影响评估
- **影响范围**: `ivreghdfe` LIML + robust/cluster
- **用户workaround**: 无
- **是否阻塞实际使用**: 否（当前 golden test 容忍度未暴露）

## 修复建议
1. 在 LIML 的 robust VCE 分支追加 `n/(n-k_eff)`。
2. 在 cluster 分支追加 `g_adj * n_adj`，与 2SLS/GMM2S 保持一致。

---

# REV-IV-11

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 输出不完整

## 现象描述
`ivreghdfe, first` 输出的第一阶段诊断字典缺少 Stata 标准输出中的多个统计量：
- **AP F (Angrist-Pischke F)** — 单内生变量下最重要的弱工具参考统计量之一
- **SW F (Sanderson-Windmeijer F)** — 多内生变量下的首选统计量
- **SW partial R²**
- ** first-stage R² / adj R² 的完整表格**

当前仅输出：`r2`, `partial_r2`, `shea_r2`, `f_stat`, `f_pvalue`, `df`, `df_r`。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 1479–1581)

## 影响评估
- **影响范围**: `ivreghdfe` first-stage diagnostics
- **用户workaround**: 手动计算
- **是否阻塞实际使用**: 否

## 修复建议
1. 在 `first_stage` 字典中补充 `ap_f`, `sw_f`, `sw_r2` 字段。
2. 参考 `ivreghdfe.ado` 中 `first` 输出的 e(first) 矩阵结构。

---

# REV-IV-12

## 元信息
- **命令**: `ivreghdfe`, `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 边界case处理不足

## 现象描述
当弱工具变量 F 统计量低于 Stock-Yogo 10% 临界值时，代码**不发出任何警告**。弱工具变量是 IV 估计中最常见的实证陷阱之一，Stata `ivreg2` / `ivreghdfe` 会在输出中标注弱工具风险。当前 Python 实现仅将统计量静默附加到 result 对象，无用户可见提示。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 1414–1418)

## 影响评估
- **影响范围**: 全 IV 命令族
- **用户workaround**: 无
- **是否阻塞实际使用**: 否（但极易导致实证误用）

## 修复建议
1. 在 `fit()` 返回前检查 `widstat < sy_10pct`：
   ```python
   if not np.isnan(widstat) and widstat < weakiv_stats.get('sy_10pct', 0):
       warnings.append(f"Weak instruments: KP F={widstat:.2f} < SY 10% critical value")
   ```
2. 同步在 `IV2SLS.fit()` 中增加同样的弱工具检测。

---

# REV-IV-13

## 元信息
- **命令**: `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失 / 数学未实现

## 现象描述
`ivregress 2sls` **不实现过度识别检验**（Sargan / Hansen J）。Stata 用户可通过 `estat overid` 在 `ivregress 2sls` 后执行 Sargan 检验（同方差）或 Hansen J（异方差/聚类）。当前 `IV2SLS.fit()` 完全缺失此功能，且 wrapper 也未暴露相关参数。

## 涉及文件
- `src/stataflow/estimators/iv.py` (`IV2SLS.fit()`)
- `src/stataflow/compat/stata/iv.py` (`ivregress_2sls()`)

## 影响评估
- **影响范围**: `ivregress 2sls`
- **用户workaround**: 手动计算或使用 `ivreghdfe` GMM2S
- **是否阻塞实际使用**: 否

## 修复建议
1. 在 `IV2SLS.fit()` 中增加 Sargan 统计量（`vce="ols"`）和 Hansen J（`vce="robust"/"cluster"`）计算。
2. 返回字段名：`sargan` / `hansen_j`, `overid_df`。

---

# REV-IV-14

## 元信息
- **命令**: `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 输出缺失

## 现象描述
Stata `ivregress 2sls` 对所有 VCE 类型均报告 **Wald chi² 统计量**（而非 F 统计量）。当前 `IV2SLS.fit()` 将 `f_stat` 和 `f_pvalue` 设为 `None`（lines 296–297），且 `ResultSchema` 中无 `chi2_stat` / `chi2_pvalue` 字段，导致 chi² 统计量完全丢失。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 296–297)
- `src/stataflow/results/result.py` (无 chi² 字段)

## 影响评估
- **影响范围**: `ivregress 2sls`
- **用户workaround**: 无
- **是否阻塞实际使用**: 否

## 修复建议
1. 计算 Wald chi² = `beta' @ VCE^{-1} @ beta`（排除 constant 后）。
2. 将 chi² 存入 `ResultSchema.fit.f_stat`（字段复用）或新增 `chi2_stat` 字段。

---

# REV-IV-15

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 数学偏差

## 现象描述
`ivreghdfe` 2-way cluster 下 `_cons` 的标准误与 Stata 存在结构性偏差，当前 golden test 允许 `rtol=0.03`（`test_w7_ivreghdfe_2way_cluster.py` line 205）。文档将此归因于 "LSDV and reghdfe's demeaning framework produce structurally different constant SEs"，但 **未明确说明该偏差的数学根因** 和 **是否可修复**。

若该偏差是 LSDV 与 MAP 路径的固有差异，应在 ADR-0003 中给出定量上界；若可通过 T-matrix 修正，则应排期修复。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 1435–1459, T-matrix)
- `tests/golden/test_w7_ivreghdfe_2way_cluster.py`
- `docs/adr/ADR-0003.md`

## 影响评估
- **影响范围**: `ivreghdfe` + 2-way cluster + `_cons`
- **用户workaround**: 忽略 `_cons` SE（ivreghdfe 通常不报告 _cons）
- **是否阻塞实际使用**: 否

## 修复建议
1. 评审 ADR-0003，明确 `_cons` SE 偏差的来源（T-matrix 线性近似 vs 精确 demeaning）。
2. 若不可修复，将 `_cons` 从 2-way cluster 的 reported coefficients 中移除（与 Stata ivreghdfe 行为一致，其不报告 _cons）。

---

# REV-IV-16

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失

## 现象描述
GMM2S 实现**不支持用户自定义权重矩阵** (`wmatrix`)。Stata `ivregress gmm` 和 `ivreg2` 均支持 `wmatrix()` 选项，允许用户指定非高效的 GMM 权重矩阵，此时 VCE 必须切换为 sandwich 形式（`s_iegmm` 逻辑，见 `docs/research/ivreghdfe-gmm.md` §1.4）。当前代码一律假设高效权重，使用简化公式 `V = 1/N * inv(Q)`，若未来支持 `wmatrix` 将产生严重数学错误。

## 涉及文件
- `src/stataflow/estimators/iv.py` (`_fit_gmm2s`, `_fit_gmm2s_residualized`)
- `docs/research/ivreghdfe-gmm.md` (§1.4)

## 影响评估
- **影响范围**: GMM2S 扩展性
- **用户workaround**: 无
- **是否阻塞实际使用**: 否（当前未暴露该参数）

## 修复建议
1. 在支持 `wmatrix` 参数前，于代码中预留明确的 `if wmatrix is not None: raise NotImplementedError` 守卫。
2. 文档中标注：当前 GMM VCE 公式仅适用于高效权重。

---

# REV-IV-17

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: API设计缺陷

## 现象描述
`ivreghdfe()` 的 `first` 参数返回 Python `dict`，而非 Stata 的格式化表格或结构化对象。用户无法直接以 Stata 的字段名（如 `e(first)`）访问。`ffirst` 紧凑型诊断更是完全缺失（标记为 Planned）。

## 涉及文件
- `src/stataflow/compat/stata/iv.py`
- `src/stataflow/estimators/iv.py` (lines 1479–1581)

## 影响评估
- **影响范围**: `ivreghdfe` first-stage 输出
- **用户workaround**: 手动解析 `result.first_stage` dict
- **是否阻塞实际使用**: 否

---

# REV-IV-18

## 元信息
- **命令**: `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 参数缺失

## 现象描述
`ivregress_2sls()` 的 `vce` 参数仅接受 `"ols"`, `"robust"`, `"cluster"`，不支持 `vce(hc1)`, `vce(hc2)`, `vce(hc3)` 等子类型。Stata 17 `ivregress` 支持 `vce(robust, hc2)` 等语法。

## 涉及文件
- `src/stataflow/estimators/iv.py` (line 194)
- `src/stataflow/compat/stata/iv.py`

## 影响评估
- **影响范围**: `ivregress 2sls`
- **用户workaround**: 无
- **是否阻塞实际使用**: 否

---

# REV-IV-19

## 元信息
- **命令**: `ivreghdfe`, `ivregress 2sls`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 参数缺失

## 现象描述
两命令均未实现 `level(#)` 参数（置信区间显著性水平）。`alpha=0.05` 在 `IV2SLS.fit()` 和 `IVAbsorbingOLS.fit()` 中硬编码，wrapper 未暴露。

## 涉及文件
- `src/stataflow/estimators/iv.py` (lines 176, 1306)
- `src/stataflow/compat/stata/iv.py`

## 影响评估
- **影响范围**: 全 IV 命令族
- **用户workaround**: 手动计算 CI
- **是否阻塞实际使用**: 否

---

# REV-IV-20

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: API不便利

## 现象描述
`ivreghdfe()` 的 `cluster` 参数不支持 Stata 风格的空格分隔字符串（如 `cluster="firm year"`）。当前必须传入 Python list：`cluster=["firm", "year"]`。对于从 Stata 迁移的用户不够友好。

## 涉及文件
- `src/stataflow/compat/stata/iv.py` (line 55, 98–116)

## 影响评估
- **影响范围**: `ivreghdfe` wrapper
- **用户workaround**: 手动 split 为 list
- **是否阻塞实际使用**: 否

---

# REV-IV-21

## 元信息
- **命令**: `ivreghdfe`
- **命令族**: IV / GMM
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 边界case处理不足

## 现象描述
Stock-Yogo 临界值查表仅覆盖 `nendog ∈ [1,10]`, `k2 ∈ [1,10]`。对于高维 IV 模型（如 Angrist-Krueger QOB 数据，`k2` 可达 30+），查表返回 `np.nan`，弱工具诊断失去参照标准。

## 涉及文件
- `src/stataflow/estimators/_stock_yogo.py` (lines 22–132)

## 影响评估
- **影响范围**: 高维 IV 模型
- **用户workaround**: 无
- **是否阻塞实际使用**: 否

## 修复建议
1. 在表格外推区间使用线性插值或返回明确的 `NotImplementedError`，提示超出查表范围。
2. 考虑引入 Stock-Yogo  asymptotic 公式或扩展表格至 20×20。

---

## 附录：按类型与严重度分布

| 严重度 | 参数缺失 | API设计缺陷 | 边界case崩溃 | 数学偏差 | 文档不一致 |
|--------|----------|-------------|--------------|----------|------------|
| Blocker | — | — | — | 2 | — |
| Critical | 1 | 1 | 1 | 2 | — |
| Major | 4 | 1 | 1 | 2 | — |
| Minor | 2 | 2 | 1 | — | 1 |

**关键行动项（按优先级）**：
1. **立即修复**: REV-IV-01（GMM2S 路径不一致）、REV-IV-02（fix_psd_reghdfe 错误假设）
2. **高优先级**: REV-IV-03（IV2SLS t/z 统计量）、REV-IV-04（X/Z 共线性检测分离）、REV-IV-05（多内生变量 weakiv）
3. **中优先级**: REV-IV-06（LIML Fuller 临界值）、REV-IV-08/09（ivregress_2sls first/noconstant）、REV-IV-12（弱工具警告）
4. **排期实现**: REV-IV-11（AP/SW F）、REV-IV-13（过度识别检验）、REV-IV-16（wmatrix）
