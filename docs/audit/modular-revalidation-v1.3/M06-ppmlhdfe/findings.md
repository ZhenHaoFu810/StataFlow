# M06 PPMLHDFE 模块独立审查 — 已确认发现

审查基线：`dev` @ `2c7db1ca095e03d29c471e8d523fdaa943306174`  
审查日期：2026-06-13  
Stata 17 MP (`D:\Software\Stata17\StataMP-64.exe`)，ppmlhdfe 2.3.3

---

## M06-PPMLHDFE-001：Stata `ppmlhdfe` 仅接受 `pweight`，`aweight`/`iweight` 被拒绝

- **Severity**: P2
- **Evidence status**: Confirmed-Stata
- **Affected API**: `stataflow.compat.stata.ppmlhdfe(..., aweight=...)`
- **最小复现**: `tests/audit_v1_3/m06_ppmlhdfe/repro_m06_ppmlhdfe_findings.py` (Finding A)
- **Stata 结果**: 运行 `ppmlhdfe y x1 x2 [aweight=w], absorb(entity_id) vce(robust)` 返回 `aweights not allowed` 与 `r(101)`；`[iweight=w]` 同样返回 `r(101)`。
- **Python 结果**: wrapper 接收 `aweight` 参数并将其传入 `PPMLHDFE(weights=aweight)`，Python 端可正常拟合。
- **根因**: Python 的权重语义映射为 `aweight`（归一化至 sum=N），而 Stata 的 `ppmlhdfe` 在社区命令层面仅实现了 `pweight`。
- **用户影响**: 使用 `aweight` 的用户无法直接把 Python wrapper 与 Stata 命令对齐；需要改用 `pweight` 并在 Python 端使用 `weights=`。
- **建议修复方向**: 在 wrapper 中明确文档化 `aweight` 的兼容性限制，或提供映射逻辑将 `aweight` 转换为 Stata 可接受的 `pweight`，但需先确认点估计与推断是否等价。
- **证据路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/minimal-reproductions/A_WeightSyntaxRejected.json`

---

## M06-PPMLHDFE-002：Python `separation=None` 不处理分离，结果与 Stata 默认分离样本不同

- **Severity**: P0
- **Evidence status**: Confirmed-Stata
- **Affected API**: `stataflow.PPMLHDFE(..., separation=None)`（默认）
- **最小复现**: `S5_SEPARATION_FE`，`repro_m06_ppmlhdfe_findings.py` (Finding B)
- **Stata 结果**: 默认 `separation(fe simplex relu)` 会删除 singleton 或被 FE 分离的观测（S5 中 60 → 44）。`separation(none)` 仍保留 60 个观测并收敛到合理估计。
- **Python 结果**: `separation=None` 不删除任何分离组，IRLS 在存在 y=0 实体时发散（`_cons` 达到 9.5e14，`ll` 达到 -4e12）。`separation="fe"` 可复现 Stata 默认样本。
- **根因**: Python 端只实现了最简单的 FE-level y=0 删除；缺少 Stata 默认的 simplex/relu 分离检测，也未在不收敛时发出警告或报错。
- **用户影响**: 在零膨胀或结构性零数据中，默认设置可能返回无意义估计且无明确报错，导致错误推断。
- **建议修复方向**: 默认启用与 Stata 一致的分离检测（或至少对 y=0 FE 组做删除），并在无法收敛/存在分离时给出清晰警告。
- **证据路径**:
  - `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S5_SEPARATION_FE_DEFAULT/`
  - `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S5_SEPARATION_FE_NONE/`
  - `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/minimal-reproductions/B_SeparationSampleDifference.json`

---

## M06-PPMLHDFE-003：`offset`/`exposure` 处理导致估计严重偏离 Stata

- **Severity**: P0
- **Evidence status**: Confirmed-Stata
- **Affected API**: `stataflow.PPMLHDFE(..., offset=..., exposure=...)`
- **最小复现**: `S7_WEIGHTS_OFFSET`、`R1_SHIPS_EXPOSURE`
- **Stata 结果**:
  - S7（pweight + offset）：`_cons=0.6789`，`x1=0.3395`，`ll=-340.91`。
  - R1（ships + exposure(service)）：`_cons=-6.7896`，`co_70_74=0.8184`，`ll=-68.28`。
- **Python 结果**:
  - S7：`_cons=-13.22`，`x1=0.2883`，`ll=-811.39`。
  - R1：`_cons=-19.15`，`co_70_74=0.0756`，`ll=-3.52e7`。
- **根因**: 当前实现把 offset 纳入 IRLS，但在常数项恢复（T 矩阵）中额外减去了 offset 的加权平均，造成常数项和协变量系数被错误吸收。在 exposure 场景下，log(service) 的量级进一步放大了偏差。
- **用户影响**: 任何使用 offset/exposure 的模型都会得到错误系数、标准误和似然值。
- **建议修复方向**: 重新审视 `_build_t_matrix` 中 offset 的处理；报告常数项时应与 Stata 的“offset 单独列出、_cons 不包含 offset 均值”语义一致。
- **证据路径**:
  - `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S7_WEIGHTS_OFFSET/`
  - `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/real-data/R1_SHIPS_EXPOSURE/`

---

## M06-PPMLHDFE-004：`predict(type="xb")` 包含吸收 FE，与 Stata `predict, xb` 语义不一致

- **Severity**: P1
- **Evidence status**: Confirmed-Stata
- **Affected API**: `stataflow.PPMLHDFE.predict(type="xb")` 及派生类型 `residuals`/`pearson`/`deviance`
- **最小复现**: `S8_EFORM_PREDICT`
- **Stata 结果**: `predict xb` 的均值为 0.514；`predict mu` 均值 1.77，与 Python `mu` 均值相同。
- **Python 结果**: `predict xb` 均值为 0.310；`predict mu` 均值 1.77，与 Stata相同。
- **根因**: Python `predict("xb")` 返回包含吸收 FE 的线性预测器 `_eta`；Stata `predict, xb` 在 `ppmlhdfe` 下返回不包含 FE 的部分（仅 xβ + _cons）。由于 `mu = exp(xb + FE)` 仍一致，说明 mu 包含 FE，xb 不包含。
- **用户影响**: 基于 `xb`/`residuals`/`pearson`/`deviance` 的后估计或诊断会与 Stata 不一致。
- **建议修复方向**: 提供与 Stata 对齐的 `xb`（不含 FE）以及含 FE 的替代类型，并统一 residuals/pearson/deviance 的计算基础。
- **证据路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S8_EFORM_PREDICT_PREDICT/`

---

## M06-PPMLHDFE-005：cluster-robust SE 存在 ~2e-6 残余差异；`df_resid` 语义不同

- **Severity**: P2（SE 残差）、P1（df 语义）
- **Evidence status**: Confirmed-Stata
- **Affected API**: `stataflow.PPMLHDFE(...).fit(vce="cluster", cluster=...)`
- **最小复现**: `S6_CLUSTER_SINGLETON`、`repro_m06_ppmlhdfe_findings.py` (Finding D)
- **Stata 结果**: cluster VCE 下 `e(df_r)` 缺失（`.`）；`e(N_clust)=21`。
- **Python 结果**: `df_resid = cluster_count - 1 = 20`；系数点估计一致，但 SE 相对差异约 2e-6（超出 1e-6 容差）。
- **根因**: Python 对 cluster VCE 使用 `G/(G-1)` 调整；Stata 的 ppmlhdfe 实现细节（如是否额外使用 `N/(N-K)` 小样本修正、常数项恢复精度）导致末尾位差异。`df_resid` 在 GLM 族中无统一 `e(df_r)` 定义。
- **用户影响**: 极严格容差场景下 SE 不一致；下游若使用 `df_resid` 做 t 分布推断会得到不同自由度。
- **建议修复方向**: 在文档中明确 cluster VCE 下 Python 使用 `G-1` 作为 `df_resid`；若需严格对齐 Stata，可研究 ppmlhdfe 的具体 meat 计算细节。
- **证据路径**:
  - `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S6_CLUSTER_SINGLETON/`
  - `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/minimal-reproductions/D_DfResidSemantic.json`

---

## M06-PPMLHDFE-006：Stata `e(V)` 在被省略变量后索引错位

- **Severity**: P2
- **Evidence status**: Confirmed-Stata
- **Affected API**: 审查辅助函数解析 `e(V)` 时需注意被 omitted 的变量仍占位
- **最小复现**: `S4_COLLINEAR_WITHIN_FE`
- **Stata 结果**: `x_const` 被 omitted 后，`e(V)` 中该变量位置为 0，`_cons` 实际位于第 3 列而非第 2 列。
- **Python 结果**: Python 直接剔除 `x_const`，`_cons` 位于第 2 列。
- **根因**: Stata 保留 omitted 变量的 0 系数和 0 方差行/列；Python 不保留。这是解析层面的差异，不是估计错误。
- **用户影响**: 直接按系数名索引 VCE 即可避免；对 VCE 全矩阵盲比较会失败。
- **建议修复方向**: 在比较工具中按系数名动态定位 `e(V)` 元素，或仅比较非 omitted 系数对应的子矩阵。
- **证据路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S4_COLLINEAR_WITHIN_FE/`

---

## M06-PPMLHDFE-007：当 FE 被 cluster 变量嵌套时，Stata 会把 FE 视为冗余

- **Severity**: P2
- **Evidence status**: Confirmed-Stata
- **Affected API**: `df_a` 解释
- **最小复现**: 早期 S3 设计（cluster=entity_id）
- **Stata 结果**: `entity_id` 的 FE 被 cluster `cl` 嵌套，`Absorbed degrees of freedom` 表显示 `Categories=20, Redundant=20, Num. Coefs=0`，因此 `e(df_a)=9` 而非 29。
- **Python 结果**: Python 的 `df_a` 仍按 FE 层数计算（29），未做嵌套修正。
- **根因**: Python `_compute_df_a` 未识别 FE 变量被 cluster 变量嵌套的情况。
- **用户影响**: cluster VCE 下报告的 `df_a` 与 Stata 不一致。
- **建议修复方向**: 在 `_compute_df_a` 中增加嵌套判定：若某 FE 变量与 cluster 变量一一映射，则不计入 `df_a`。
- **证据路径**: 该现象在调整 S3 DGP 前出现；相关日志保留在 `stata/output/audit_v1_3_m06/S3_MISSING_SAMPLE_SCREENING.log`（早期运行）。

---

## 未验证 / 需要进一步工作

- **多维 cluster (`vce(cluster cl1 cl2)`)**: 本次只测试了 1-way cluster；2-way cluster 的 inclusion-exclusion 与 PSD 修复未独立验证。
- **`margins` / `eform` 的完整 z/p**: 本次通过手工 delta-method 验证了 eform 系数/SE 与 raw 系数一致，但未与 Stata `ppmlhdfe ..., eform` 输出逐项比对。
- **不同 `technique` / 初始值**: 未测试 MAP vs LSDV 路径在 ppmlhdfe 中的等价性。
- **收敛失败行为**: 未系统测试 IRLS 达到 `max_iter` 时的返回与警告策略。
