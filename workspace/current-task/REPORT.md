# StataFlow v1.0.0 全面复核 — 最终报告

**任务**: 对全部 6 个命令族进行源码审查 + 真实数据双跑验证 + 修缮路线图  
**日期**: 2026-06-03  
**状态**: ✅ 全部完成

---

## 一、执行概览

### Phase 1 — 源码审查
- **方法**: 6 个并行 Agent，每个负责一个命令族
- **产出**: 90 项问题（6 Blocker + 19 Critical + 38 Major + 27 Minor）
- **档案**: `docs/audit/revalidation-v1.1/REV-*.md`（6 份）

### Phase 2 — 真实数据双跑验证
- **方法**: 6 个并行 Agent + 手动验证（DID/Linear）
- **数据集**: ezunem, card, mroz, crime1, grunfeld, rdrobust_senate
- **产出**: 18 项新问题；本轮当前累计已修复 13 项审查问题
- **档案**: `docs/audit/revalidation-v1.1/phase2-evidence/VAL-*.md`（6 份）+ `NEW-*.md`（5 份）

### Phase 3 — 修缮路线图
- **产出**: `docs/audit/revalidation-v1.1/ROADMAP.md`
- **版本规划**: v1.0.1（热修复）→ v1.1.0（功能补齐）→ v1.2.0+（深度优化）

---

## 二、关键发现

### 2.1 已修复（13 项）

| # | 问题 | 命令族 | 修复内容 | 验证 |
|---|------|--------|----------|------|
| 1 | **PANEL-01**: MAP 路径崩溃 | Panel | `stats` → `t_dist`/`f_dist` + 补充局部变量 | ✅ MAP 路径恢复，数值与 Stata 完全一致 |
| 2 | **NEW-IV-01**: 2-way cluster 字符串拼接崩溃 | IV | `.astype(str) + "__"` → list comprehension | ✅ 不再崩溃 |
| 3 | **LINEAR-01**: 宽矩阵共线性检测错误丢弃独立列 | Linear | `detect_collinear_columns` 从 QR 对角线筛选改为按列 rank-increment 筛选 | ✅ 新增 regression test；focused tests 通过 |
| 4 | **GLM-01**: Logit/Poisson robust SE 缺失 `n/(n-1)` | GLM | `GLMBase` robust VCE 增加 Stata MLE 小样本修正 | ✅ 单元测试 + Stata golden 通过 |
| 5 | **GLM-02**: PPMLHDFE eform z/p 错误 | GLM | eform 只变换 beta/SE/CI/cov，z/p 保留 raw-scale 检验 | ✅ 单元测试 + Stata golden 通过 |
| 6 | **RD-01**: rdrobust 默认调用崩溃 | RD | core 和 wrapper 默认使用 `bwselect="mserd"` | ✅ 单元测试 + Stata golden 通过 |
| 7 | **DID-004**: did_imputation allhorizons 完全未生效 | DID | allhorizons 现在新增 Stata 风格 calendar omitted horizons（如 `tau1980`-`tau1988`） | ✅ 单元测试 + synthetic Stata golden 通过；real ezunem Python 行为与审查证据一致 |
| 8 | **DID-001 + DID-011**: csdid wrapper 阻断二次分析，pretrend 返回 dict/NaN | DID | 默认返回 fitted `CSDID`；显式 `aggtype` 返回 `ResultSchema`；pretrend 修复为 ResultSchema + 有效 Wald test | ✅ 单元测试通过；synthetic CSDID golden 通过 |
| 9 | **DID-002**: csdid kwargs 硬拒绝 Stata 合法参数 | DID | `notyet=True` 在 `method="reg"` 下真实支持；`window/minn/gtcontrol/longdiff` 改为明确 `NotImplementedError` | ✅ 单元测试 + focused DID/CSDID golden 通过 |
| 10 | **IV-02**: fix_psd_reghdfe 错误假设 `_cons` 存在 | IV | PSD helper 支持 `constant_index=None`；ivreghdfe reported VCE 无 `_cons` 时不再把最后一个 slope 当 constant | ✅ 单元测试 + ivreghdfe 2-way cluster golden 通过 |
| 11 | **DID-005**: CSDID 不平衡面板 NaN 静默传播 | DID | `_fit_reg` 跳过 treated/control 在 t/base 任一为空的 ATT(g,t)，不再输出 NaN 系数 | ✅ 单元测试 + focused DID/CSDID golden 通过 |
| 12 | **RD-02**: rdrobust cluster VCE 带宽偏差 | RD | 自动带宽选择阶段传入 cluster id，使用 cluster sandwich 小样本权重，并把 pilot range 改为 cutoff 到边界的 Stata 口径 | ✅ 严格 bandwidth Stata golden + RD regression suite 通过 |

### 2.2 最严重待修复（Top 10）

| 优先级 | 问题 | 命令族 | 影响 |
|--------|------|--------|------|
| 1 | DID-003 | DID | CSDID DR never-treated/control 逻辑仍需对齐 |

### 2.3 跨命令族共性问题

1. **kwargs 硬拒绝**: DID (csdid)、IV (ivregress)、GLM (logit/probit/poisson)、Linear (regress) 均存在
2. **VCE 小样本修正缺失**: GLM robust 已修复；RD cluster 带宽已修复；IV GMM2S cluster 仍需处理
3. **返回值类型不一致**: CSDID wrapper/pretrend 已修复；其余命令仍需逐项确认统一 ResultSchema 口径
4. **_cons 假设**: fix_psd_reghdfe 硬假设最后列为 _cons，但 ivreghdfe/reghdfe 可能无 _cons

---

## 三、产出文件清单

```
docs/audit/revalidation-v1.1/
├── summary.md              # 汇总报告（本文件的超集）
├── ROADMAP.md              # 修缮路线图
├── REV_TEMPLATE.md         # 问题记录模板
├── REV-DID.md              # DID 源码审查（18 项问题）
├── REV-IV.md               # IV 源码审查（21 项问题）
├── REV-GLM.md              # GLM 源码审查（13 项问题）
├── REV-PANEL.md            # Panel 源码审查（15 项问题）
├── REV-RD.md               # RD 源码审查（10 项问题）
├── REV-LINEAR.md           # Linear 源码审查（13 项问题）
└── phase2-evidence/
    ├── VAL-DID.md          # DID 双跑验证
    ├── VAL-IV.md           # IV 双跑验证
    ├── VAL-GLM.md          # GLM 双跑验证
    ├── VAL-PANEL.md        # Panel 双跑验证
    ├── VAL-RD.md           # RD 双跑验证
    ├── VAL-LINEAR.md       # Linear 双跑验证
    ├── NEW-GLM.md          # GLM 新发现
    ├── NEW-PANEL.md        # Panel 新发现 + 修复记录
    ├── NEW-RD.md           # RD 新发现
    └── [IV/DID/Linear NEW 档案由 Agent 补充]

stata/output/phase2/
├── *.do                    # Stata 执行脚本（40+ 个）
├── *.log                   # Stata 输出日志（40+ 个）
├── *_python_results.json   # Python 端结果（6 个命令族）
└── *_stata_*.txt           # Stata 端导出结果
```

---

## 四、代码变更

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/stataflow/estimators/absorbing_ols.py` | 修复 + 重构 | PANEL-01: stats→t_dist/f_dist；MAP 路径局部变量；新增 MAP/LSDV 双路径支持 |
| `src/stataflow/estimators/iv.py` | 修复 | NEW-IV-01: 字符串拼接崩溃；统一调用 detect_collinear_columns |
| `src/stataflow/estimators/_vce_utils.py` | 修复 | LINEAR-01: 共线性检测改为按列 rank-increment 筛选 |
| `src/stataflow/estimators/glm.py` | 修复 | GLM-01: Logit/Poisson robust VCE 增加 `n/(n-1)`；MLE cluster VCE 改为 `G/(G-1)` 口径 |
| `src/stataflow/estimators/ppmlhdfe.py` | 修复 | GLM-02: eform 保留 raw-scale z/p |
| `src/stataflow/estimators/rdrobust.py` | 修复 | RD-01: 默认 `bwselect` 设为 `mserd` |
| `src/stataflow/estimators/rdrobust.py` | 修复 | RD-02: 带宽选择传入 cluster id、使用 cluster sandwich 权重，并修正 pilot range cutoff 口径 |
| `src/stataflow/compat/stata/rdrobust.py` | 修复 | RD-01: 移除 wrapper 对缺省 bandwidth 的硬拒绝 |
| `src/stataflow/estimators/did_imputation.py` | 修复 | DID-004: allhorizons 使用 `_K_all=time-first_treat` 纳入 never-treated calendar horizons，并以 omitted 0 系数报告 |
| `src/stataflow/compat/stata/did.py` | 修复 | DID-001: `csdid()` 默认返回 fitted `CSDID`，显式 `aggtype` 返回对应 `ResultSchema` |
| `src/stataflow/estimators/csdid.py` | 修复 | DID-011: `estat_pretrend()` 识别 `numpy.integer` event keys，并返回统一 `ResultSchema` |
| `src/stataflow/compat/stata/did.py` | 修复 | DID-002: 显式声明 `notyet/window/minn/gtcontrol/longdiff`，区分真实支持和 known-unimplemented |
| `src/stataflow/estimators/csdid.py` | 修复 | DID-002: `method="reg"` 支持 `notyet=True` 强制 not-yet-treated 控制组 |
| `src/stataflow/estimators/_vce_utils.py` | 修复 | IV-02: `fix_psd_reghdfe()` 新增 `constant_index`，支持无 constant 的 reported VCE |
| `src/stataflow/estimators/iv.py` | 修复 | IV-02: ivreghdfe PSD fix 传入实际 `_cons` 位置；无 `_cons` 时传 `None` |
| `src/stataflow/estimators/csdid.py` | 修复 | DID-005: `_fit_reg` 跳过空 treated/control t/base cells，避免 NaN ATT(g,t) 进入聚合 |
| `tests/test_vce_utils.py` | 新增测试 | LINEAR-01: 宽矩阵中后置独立列不应被错误丢弃 |
| `tests/test_compat_stata_glm.py` | 新增测试 | GLM robust/cluster VCE 小样本修正口径 |
| `tests/test_compat_stata_hdfe.py` | 新增测试 | PPMLHDFE eform beta/SE 变换但 z/p 保持 raw-scale |
| `tests/golden/test_w7_ppmlhdfe_eform.py` | 增强测试 | Stata raw `_b/_se` 推导 eform z/p 并字段级比对 |
| `tests/test_rdrobust.py` | 修改测试 | RD-01: 默认调用等价于 `bwselect="mserd"`，覆盖 core 和 wrapper |
| `tests/golden/test_w8_rdrobust_cluster_real_senate.py` | 增强测试 | RD-02: cluster bandwidth 对 Stata 使用 field-level 严格容差 |
| `tests/test_compat_stata_did.py` | 修改测试 | DID-004: 覆盖 allhorizons 新增 calendar horizons、默认/窗口限制差异 |
| `tests/test_compat_stata_did.py` | 修改测试 | DID-001/DID-011: 覆盖默认返回 fitted model、链式 estat、pretrend ResultSchema |
| `tests/test_compat_stata_did.py` | 修改测试 | DID-002: 覆盖 `notyet=True` 真实支持与 known-unimplemented 参数错误类型 |
| `tests/test_vce_utils.py` | 修改测试 | IV-02: 覆盖无 constant reported VCE 不应保护最后一个 slope |
| `tests/test_compat_stata_did.py` | 修改测试 | DID-005: 覆盖不平衡面板空 group-time cell 不应产生 NaN 系数 |

## 四、后续修缮进展

### 2026-06-03 — LINEAR-01 hotfix

- **根因**: `detect_collinear_columns()` 使用无 pivot QR 的对角线位置判定列独立性；在 `n < p` 且后置列能提高 rank 时，该列会被错误丢弃。
- **修复**: 改为按原始列顺序逐列加入，只有候选列使矩阵 rank 增加时才保留，否则记录为 dropped。
- **验证**:
  - `pytest tests/test_vce_utils.py -q` → 1 passed
  - `pytest tests/test_factor_variables.py tests/test_compat_stata_iv.py tests/test_compat_stata_hdfe.py -q` → 56 passed

### 2026-06-03 — GLM-01 hotfix + GLM cluster VCE correction

- **根因（GLM-01）**: `GLMBase._compute_vce()` robust 分支只返回未修正 sandwich，少乘 Stata MLE robust VCE 的 `n/(n-1)`。
- **修复（GLM-01）**: Logit/Poisson 共用的 `GLMBase` robust 分支增加 `n/(n-1)`；Probit 保持其已有独立 observed-Hessian 实现。
- **附带发现与修复**: 既有 Logit/Poisson Stata golden 暴露 cluster VCE 多乘了线性模型修正 `(N-1)/(N-k)`。MLE cluster VCE 口径已改为只使用 `G/(G-1)`，Probit cluster 分支同步修正。
- **验证**:
  - `pytest tests/test_compat_stata_glm.py -q` → 17 passed
  - `pytest tests/golden/test_p1v_logit_robust_cluster.py tests/golden/test_p1v_poisson_robust_cluster.py -q` → 8 passed

### 2026-06-03 — GLM-02 hotfix

- **根因**: `PPMLHDFE.fit(eform=True)` 先做 delta-method 变换，再用 `exp(beta) / SE_exp` 重新计算 z/p；这检验的是错误的 transformed-scale null。
- **修复**: eform 分支仅变换 beta、cov、SE、CI；`t_stat` 和 `p_value` 保留 raw beta / raw SE 的检验结果。
- **验证**:
  - `pytest tests/test_compat_stata_hdfe.py -q` → 7 passed
  - `pytest tests/golden/test_w7_ppmlhdfe_eform.py -q` → 4 passed

### 2026-06-03 — RD-01 hotfix

- **根因**: `compat.stata.rdrobust()` 在 `h=None` 且 `bwselect=None` 时提前抛出 `NotImplementedError`，底层 `RDRobust.__init__()` 也要求二者至少提供一个；这与 Stata `rdrobust` 默认使用 `bwselect(mserd)` 不一致。
- **修复**: core `RDRobust` 默认 `bwselect="mserd"`；wrapper 不再对缺省 bandwidth 提前硬拒绝，显式 `h` 仍按既有逻辑覆盖 bandwidth selector。
- **验证**:
  - `pytest tests/test_rdrobust.py::test_rdrobust_default_bandwidth_selects_mserd tests/test_rdrobust.py::test_rdrobust_core_default_bandwidth_selects_mserd tests/test_rdrobust.py::test_rdrobust_bwselect_mserd_real_data_matches_stata tests/test_rdrobust.py::test_rdrobust_covs_bwselect_mserd_matches_stata tests/test_rdrobust.py::test_rdrobust_h_overrides_bwselect -q` → 5 passed
  - `pytest tests/golden/test_w8_rdrobust_bwselect_all_real_senate.py -q` → 8 passed
  - `pytest tests/test_rdrobust.py -q` → 50 passed

### 2026-06-03 — RD-02 hotfix

- **根因**: `RDRobust.fit()` 在自动带宽选择时将 `vce="cluster"` 映射为 HC0 残差基，但没有把 cluster id 传给 `_rdbwselect()` / `_rdrobust_bw()`，导致 pilot/MSE 带宽阶段使用非聚类 sandwich；同时 `_compute_pilot_bw()` 的 `range_l/r` 使用每侧内部 `max-min`，而 Stata/vendor rdrobust 使用 cutoff 到每侧边界的距离。
- **修复**: `_rdbwselect()`、三步带宽分支和 `_rdrobust_bw()` 传递并筛选窗口内 cluster id；`_rdrobust_vce_multi()` 在 cluster 路径按 rdrobust 口径聚合 cluster scores 并应用 `((n-1)/(n-k)) * (G/(G-1))`；pilot range 改为 `abs(c-min(X_l))` / `abs(c-max(X_r))`。
- **验证**:
  - RED: `pytest tests/golden/test_w8_rdrobust_cluster_real_senate.py::TestW8RDRobustClusterRealSenate::test_bandwidths -q` → failed，`h_l[cluster]` Python=17.6867196664, Stata=18.0842880000。
  - GREEN: 同一严格 bandwidth test → 1 passed。
  - `pytest tests/golden/test_w8_rdrobust_cluster_real_senate.py -q` → 6 passed。
  - `pytest tests/test_rdrobust.py tests/golden/test_w8_rdrobust_cluster_real_senate.py tests/golden/test_w8_rdrobust_bwselect_all_real_senate.py -q` → 64 passed。

### 2026-06-03 — DID-004 hotfix

- **根因**: `DIDImputation.fit()` 先把 never-treated 行的 `_K` 设为 `NaN`，之后无论 `allhorizons` 取值都只从 ever-treated 的非负 `_K` 取 horizon，因此 `allhorizons=True` 与默认结果完全相同。
- **修复**: 增加 `_K_all = time - first_treat` 保留 never-treated 的 calendar horizons；默认仍只报告 ever-treated 非负 event horizons，`allhorizons=True` 额外报告 Stata 风格 omitted calendar coefficients（例如 ezunem 的 `tau1980`-`tau1988`）。
- **验证**:
  - `pytest tests/test_compat_stata_did.py::test_did_imputation_allhorizons_true tests/test_compat_stata_did.py::test_did_imputation_allhorizons_more_horizons_than_default tests/test_compat_stata_did.py::test_did_imputation_window_with_allhorizons -q` → 3 passed
  - `pytest tests/test_compat_stata_did.py -q` → 50 passed
  - `pytest tests/golden/test_w4_did_imputation_basic.py -q` → 4 passed
  - `pytest tests/golden/test_w9_di_controls_basic.py tests/golden/test_w9_di_pretrends_basic.py tests/golden/test_w9_di_controls_pretrends_combo.py -q` → 14 passed
  - Python real ezunem check: default names `tau0`-`tau4`; `allhorizons=True` adds `tau1980`-`tau1988`, matching `docs/audit/revalidation-v1.1/phase2-evidence/VAL-DID.md`.
  - Limitation: `pytest tests/golden/test_w4_did_imputation_real_ezunem.py -q` cannot run because `stata/output/realdata_did_imputation_ezunem.log` is absent.

### 2026-06-03 — DID-001/DID-011 hotfix

- **根因（DID-001）**: `compat.stata.csdid()` 在 `fit()` 后直接返回 `model.estat(...)`，默认用户拿不到 fitted `CSDID`，无法复用同一拟合对象调用 event/simple/group/calendar/pretrend。
- **根因（DID-011）**: `estat_pretrend()` 返回 plain dict，且只用 `isinstance(e, int)` 识别负 event time；`numpy.int64` 键被漏掉后返回 NaN/df=0。
- **修复**: `csdid(..., aggtype=None)` 默认返回 fitted `CSDID`；显式 `aggtype` 仍返回对应 `ResultSchema`。`estat_pretrend()` 改为识别 `int`/`np.integer`，并用统一 `ResultSchema` 承载 Wald test 的 `fit.f_stat/f_pvalue/df_model`。
- **验证**:
  - `pytest tests/test_compat_stata_did.py::test_csdid_default_returns_fitted_model_for_chained_estat tests/test_compat_stata_did.py::test_csdid_agg_pretrend -q` → 2 passed
  - `pytest tests/test_compat_stata_did.py -q` → 51 passed
  - Python real ezunem check: `csdid(..., aggtype='pretrend')` returns `ResultSchema`, `fit.df_model=4.0`, finite `fit.f_stat` and `fit.f_pvalue`.
  - `pytest tests/golden/test_w9_csdid_dr_basic.py tests/golden/test_w4_csdid_real_ezunem.py -q` → `test_w9_csdid_dr_basic.py` passed; `test_w4_csdid_real_ezunem.py` cannot run because `stata/output/realdata_csdid.log` is absent.
  - Residual risk: real-data pretrend statistic still needs Stata field-level alignment once a fresh `realdata_csdid.log` or dual-run harness is available.

### 2026-06-03 — DID-002 hotfix

- **根因**: `compat.stata.csdid()` 对所有未声明 kwargs 一律 `ValueError`，导致 Stata 合法选项 `notyet/window/minn/gtcontrol/longdiff` 与真正未知参数没有区分。
- **修复**: wrapper 显式声明这些选项。`notyet=True` 在 `method="reg"` 下传入 core 并强制使用 not-yet-treated 控制组；`window/minn/gtcontrol/longdiff` 暂未实现时抛 `NotImplementedError`，符合项目对 known-but-unimplemented 参数的约定。
- **验证**:
  - `pytest tests/test_compat_stata_did.py::test_csdid_notyet_option_uses_not_yet_treated_controls tests/test_compat_stata_did.py::test_csdid_known_unimplemented_options_are_explicit -q` → 2 passed
  - `pytest tests/test_compat_stata_did.py -q` → 53 passed
  - `pytest tests/golden/test_w4_did_imputation_basic.py tests/golden/test_w9_di_controls_basic.py tests/golden/test_w9_di_pretrends_basic.py tests/golden/test_w9_di_controls_pretrends_combo.py tests/golden/test_w9_csdid_dr_basic.py -q` → 19 passed
  - Residual risk: `notyet=True` for DR methods remains intentionally `NotImplementedError` and should be handled with DID-003.

### 2026-06-03 — IV-02 hotfix

- **根因**: `fix_psd_reghdfe()` 默认假设 `_cons` 是 reported VCE 的最后一行/列，并在 PSD 修复后恢复除最后一列外的 slope submatrix。`ivreghdfe` reported coefficient table 不含 `_cons`，该逻辑会把最后一个 slope 当成 constant。
- **修复**: `fix_psd_reghdfe(mat, constant_index=...)` 支持显式 constant 位置；`constant_index=None` 表示 reported VCE 无 constant，改用普通 eigenvalue truncation。`IVAbsorbingOLS` 根据 `_coef_names` 传入实际位置或 `None`。
- **验证**:
  - `pytest tests/test_vce_utils.py::test_fix_psd_reghdfe_without_constant_does_not_treat_last_slope_as_constant -q` → 1 passed
  - `pytest tests/test_vce_utils.py tests/test_compat_stata_iv.py -q` → 11 passed
  - `pytest tests/golden/test_w7_ivreghdfe_2way_cluster.py -q` → 14 passed
  - Residual risk: Stata rank-deficiency fallback behavior for real-data 2-way cluster remains a separate algorithmic issue documented in `VAL-IV.md`.

### 2026-06-03 — DID-005 hotfix

- **根因**: CSDID `_fit_reg` 在计算 ATT(g,t) 时直接对 treated/control 的 t/base 子样本取均值；不平衡面板或 missing drop 后某个子样本为空会得到 `NaN`，并静默进入 event 聚合。
- **修复**: 在计算均值前检查 `treated_t/control_t/treated_base/control_base` 是否为空，并检查四个均值是否 finite；任一失败则跳过该 `(g,t)`。
- **验证**:
  - `pytest tests/test_compat_stata_did.py::test_csdid_unbalanced_panel_skips_empty_group_time_cells -q` → 1 passed
  - `pytest tests/test_compat_stata_did.py -q` → 54 passed
  - `pytest tests/golden/test_w4_did_imputation_basic.py tests/golden/test_w9_di_controls_basic.py tests/golden/test_w9_di_pretrends_basic.py tests/golden/test_w9_di_controls_pretrends_combo.py tests/golden/test_w9_csdid_dr_basic.py -q` → 19 passed
  - Residual risk: DR path and full Stata sample-screening parity remain separate DID follow-up work.

---

## 五、风险与建议

1. **最高风险**: DID 命令族仍有 kwargs 硬拒、CSDID NaN/样本筛选、did_imputation 样本筛选与 cluster SE 等核心对齐问题
2. **建议优先**: v1.0.1 集中修复 DID + GLM + RD 的 8 个 P0 问题，可快速恢复核心功能可用性
3. **测试覆盖**: 建议在修复后增加自动化 golden test，防止回归

---

### 2026-06-03 — v1.1.0 P1 修复（批次 2，3 项）

| # | 问题 | 命令族 | 修复内容 | 验证 |
|---|------|--------|----------|------|
| 16 | **IV-01**: GMM2S cluster VCE 主/fallback 路径不一致 | IV | `_fit_gmm2s` 主路径添加 `g_adj*n_adj` cluster 小样本修正；同步修复主路径 2-way cluster `__` 字符串拼接冲突 | 9 项 IV 测试通过 |
| 17 | **LINEAR-05**: `regress` wrapper 硬拒绝 `level()/beta/eform` | Linear | `regress`/`xtreg_fe`/`areg` 支持 `level` 参数（转 alpha）；`beta`/`eform` 抛出明确 `NotImplementedError` | 19 项 Linear 测试通过 |
| 18 | **PANEL-03**: savefe/slopes 错位 | Panel | `save_fixed_effects` 使用 `column_types` 过滤 slope columns，避免 intercept 错位；存在 slopes 时发出 `UserWarning` | 49 项 HDFE 测试通过 |

---

### 2026-06-03 — P2 修复（DID-006 + DID-007）

| # | 问题 | 命令族 | 修复内容 | 验证 |
|---|------|--------|----------|------|
| 19 | **DID-006**: CSDID `cluster_var` 始终为 `None` | DID | `_fit_reg`/`_fit_dr` 保存实际 cluster 列名到 `self._cluster_var`，`_finalize_fit` 传入 `ResultSchema` | 54 项 DID 测试通过 |
| 20 | **DID-007**: CSDID `df_resid` 使用 `n_units` 而非 cluster 实际层级数 | DID | `_n_clust` 从 `df[cluster_col].nunique()` 计算，而非固定 `n_units` | 54 项 DID 测试通过 |

---

*报告完成时间: 2026-06-03*
*总投入: 6 个并行 Agent + 人工验证 + 手动修复*
### 2026-06-03 — P2 修复（PANEL-05 partial）

| # | 问题 | 命令族 | 修复内容 | 验证 |
|---|------|--------|----------|------|
| 21 | **PANEL-05**: `areg()` 不支持 `noconstant` | Panel | `areg` wrapper 添加 `noconstant` 参数并传给 `AbsorbingOLS(add_constant=not noconstant)` | 20 项 Linear 测试通过 |

---

*报告完成时间: 2026-06-03*
*总投入: 6 个并行 Agent + 人工验证 + 手动修复*
*问题总数: 108（已修复 21，待修复 87）*
