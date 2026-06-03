# DoF 计算审查报告

**Phase:** Audit Phase 1.2
**审查日期:** 2026-04-30
**审查范围:** 7 个核心 estimator 的 df_a, df_model, df_resid 计算

---

## 1. 审查方法

逐 estimator 追踪 `df_a`, `df_model`, `df_resid` 的计算路径，对照 Stata 的 `e(df_m)`, `e(df_r)`, `e(df_a)` 输出。对 HDFE estimator 还需验证 nested FE 扣减、singleton drops、keepsingletons 等特殊路径。

---

## 2. df_model 与 df_resid

| Estimator | df_model | df_resid (ols) | df_resid (cluster) | Stata convention |
|-----------|----------|---------------|-------------------|------------------|
| **OLS** | k - 1 (if constant) | n - k | G - 1 | `e(df_m)` 不含常数 |
| **FixedEffectsOLS** | k (slopes only) / k+G-1 (with FEs) | n - G - k | G - 1 | Stata reports k for xtreg, fe |
| **AbsorbingOLS** | k_x (slopes only) | n - k_x - df_a - 1 | G - 1 or custom | k_x = number of x variables |
| **IV2SLS** | k_endog + k_exog | n - k (asymptotic: n) | asymptotic | df_m = k, uses large-sample |
| **IVAbsorbingOLS** | k_x (non-absorbed params) | n - k_x_full | G - 1 cluster-count based | Same as AbsorbingOLS |
| **GLM** | k (all betas) | n - k (not used) | n - k (not used) | GLM uses deviance-based df |
| **PPMLHDFE** | k_x | n - k_x - df_a - 1 | G - 1 | Same as GLM + HDFE absorbed |

### 2.1 关键发现

**2.1.1 FixedEffectsOLS df_model 的双重身份**

`FixedEffectsOLS` 在 ols VCE 下报告 `df_model = k + (G - 1)`（含 FE 参数），但在 cluster VCE 下报告 `df_model = k`（仅斜率）。这是因为 Stata 的 `xtreg, fe` cluster 结果表只显示斜率参数而有不同的 `e(df_m)` 约定。代码 (L227-233) 正确处理了这种双重性。

**状态:** ✅ 正确。

**2.1.2 OLS df_model = k - 1**

Stata convention: `e(df_m)` does NOT count the constant term. So for `regress y x1 x2`, `e(df_m) = 2` even though k = 3 (with _cons). OLS correctly uses `k - 1` for df_model when `add_constant=True`.

**状态:** ✅ 正确，与 Stata 约定一致。

**2.1.3 IV2SLS 渐近约定**

IV2SLS 不显式计算 `df_resid` 用于 VCE（因为使用渐近 VCE）。`df_resid` 仅在 `ResultSchema` 中报告，此时使用 `n - k_x`。

**状态:** ✅ 正确（渐近推断不需要显式 df_resid）。

---

## 3. df_a 计算

df_a（absorbed degrees of freedom）是 reghdfe/ivreghdfe/ppmlhdfe 的核心差异化特征。

### 3.1 AbsorbingOLS._compute_df_a (L544-570)

**核心逻辑：**
```python
df_a = 0
for info in self._dummy_info:
    n_levels = info['n_levels']
    n_slopes = len(info.get('slopes', []))
    has_intercept = info.get('has_intercept', True)
    params_per_level = (1 if has_intercept else 0) + n_slopes
    effective_levels = n_levels * params_per_level
    df_a += effective_levels
```

**正确性验证：**
- 每个 FE 变量的参数数 = 截距参数（如有）+ 斜率参数
- `has_intercept=False` 时（`#c.` 纯斜率），仅计数斜率参数
- `effective_levels` 直接等于 `n_levels * params_per_level`

**斜率吸收的 df_a:** 对于 `absorb(firm_id##c.time)`，每个 firm 贡献 1 截距 + 1 斜率 = 2 参数。df_a = G * 2。正确。

### 3.2 Nested FE 扣减

当 cluster 变量嵌入在 absorb 变量中时（如 `cluster="firm_id"` 而 absorb 包含 `firm_id`），嵌套参数应从有效参数计数中扣除。

**代码路径 1 (MAP):** L1151-1154
```python
nested_params = df_a_reduced  # 嵌套 FE 参数
k_eff = k_x - nested_params  # 有效参数数
```
在计算 multi-way cluster VCE 时使用 `k_eff` 而非 `k_full`，以避免过惩罚。

**代码路径 2 (LSDV):** L1385-1388
```python
nested = self._get_nested_cluster_params(cluster_vars)
if nested > 0:
    k_eff = k_x_full - nested
```
同样的逻辑。

**正确性:** 嵌套 FE 扣减的数学逻辑正确。当 cluster 变量 = FE 变量本身时，该 FE 的每个 level 的观测已经是独立聚类的，不需要用 `G/(G-1)` 重复惩罚。

### 3.3 Singleton Drops

`_prepare_data` 在构建 FE dummies 前自动标记 singleton 观测。Singleton 的 FE level 仅有一个观测，在 LSDV 下会产生完美拟合（zero residual），因此被剔除。

Singleton 剔除后的 df_a 减少了被剔除的 singleton groups 的参数数。

**状态:** ✅ 正确处理。有专门的 golden test (`test_p3_reghdfe_keepsingletons.py`) 验证。

### 3.4 keepsingletons

当 `keepsingletons=True` 时，singleton 观测被保留，df_a 计入所有 FE levels（包括 singleton）。这与 Stata `reghdfe, keepsingletons` 一致。

**状态:** ✅ 正确处理。

---

## 4. 特殊 DoF 路径

### 4.1 DK VCE 的 df_r

```python
df_r = float(T - 1)  # L687
```

Driscoll-Kraay VCE 使用时间维度自由度 `T-1`，而非标准 OLS 的 `n-k_full`。这与 Stata 的 `e(df_r)` for DK 一致。

**状态:** ✅ 正确。

### 4.2 Cluster VCE 的 df_resid

```python
# L437 in ols.py
df_resid = float(cluster_count - 1)
```

Cluster VCE 的 df_resid 基于 cluster 数量（`G-1`），而非观测数量。这是 Stata 的约定：当使用 cluster VCE 时，t 统计量的自由度是 `G-1`（cluster 数 - 1）。

所有 estimator（OLS, FE, AbsorbingOLS, IVAbsorbingOLS, PPMLHDFE）在 cluster VCE 下都使用 `G-1` 作为 df_resid。

**状态:** ✅ 正确。

### 4.3 IV2SLS + GMM/LIML

IVAbsorbingOLS 的 GMM2S 和 LIML 路径使用 `df_resid = n - k_x_full`（L1252）。这与 2SLS 一致 — LIML/GMM 的 VCE 使用相同的自由度计算。

**状态:** ✅ 正确（LIML/GMM 的渐近分布与 2SLS 相同）。

---

## 5. 审查发现汇总

### ✅ 确认正确

| ID | 内容 |
|----|------|
| DOF-OK-1 | OLS: df_model = k-1, df_resid = n-k (ols) / G-1 (cluster) |
| DOF-OK-2 | FixedEffectsOLS: df_model 双模式处理正确 |
| DOF-OK-3 | AbsorbingOLS: df_a = sum(levels * params_per_level) |
| DOF-OK-4 | 斜率吸收 df_a = G * (1 + n_slopes) |
| DOF-OK-5 | Nested FE 扣减: MAP 和 LSDV 路径均正确处理 |
| DOF-OK-6 | Singleton drops 和 keepsingletons 正确处理 |
| DOF-OK-7 | DK VCE: df_r = T-1 与 Stata 一致 |
| DOF-OK-8 | Cluster VCE: df_resid = G-1 与 Stata 一致 |

### P2 发现

| ID | 发现 | 建议 |
|----|------|------|
| DOF-P2-1 | dofadjustments() 精确算法全部缺失（pairwise, firstpair, clusters, continuous）| v1.1.0 中至少实现 firstpair（两两嵌套精确算法） |

### 推迟至 v1.1.0+ 的 DoF 项目

- `dofadjustments(pairwise)` — 图论算法，计算 mobility group 的精确 df_a
- `dofadjustments(clusters)` — cluster 维度的 DoF 计数
- `dofadjustments(continuous)` — 连续变量的 DoF 等效参数
- `dofadjustments(firstpair)` — 两两 FE 对的精确嵌套计数

这些项目在 `ROADMASTER_PLAN.md` Section 2.1 中标记为 "部分实现" 且推迟至 v1.1.0+。

---

## 6. 结论

**所有 7 个 estimator 的基本 DoF 计算（df_model, df_resid, df_a）均正确。**

唯一的重要缺失是 `dofadjustments()` 精确算法（pairwise, firstpair, clusters, continuous），但这些已明确推迟至 v1.1.0+ 且不影响当前 v1.0.0 的 Daily use。

No P0/P1 DoF issues found。

---

*下一审查: 特殊路径审查 (`docs/audit/special-paths-audit.md`)*
