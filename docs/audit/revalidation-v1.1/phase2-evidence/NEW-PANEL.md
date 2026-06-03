# NEW-PANEL — Phase 2 新发现问题与修复记录

**验证日期**: 2026-06-03  
**数据集**: grunfeld.csv (200 obs, 10 firms × 20 years)  
**关联报告**: `VAL-PANEL.md`

---

## 1. PANEL-01 修复详情

### 问题描述
`AbsorbingOLS` 的 MAP（Kaczmarz 迭代吸收）路径在 `technique='map'` 或自动选择 MAP 时完全崩溃。

### 原始崩溃信息
```python
NameError: name 'stats' is not defined
  File ".../absorbing_ols.py", line 1101, in _fit_map
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=df_resid))
```

### 根因分析
1. **NameError**: 模块头部仅导入 `from scipy.stats import t as t_dist, f as f_dist`，但 `_fit_map` 中错误地使用了未定义的 `stats` 名称。
2. **UnboundLocalError**: 修复 NameError 后，`_fit_map` 方法末尾 `fit()` 尝试访问局部变量 `beta_full`、`cov_full`、`T`，这些变量在 MAP 路径中未被定义（LSDV 路径中才定义）。

### 修复内容

**文件**: `src/stataflow/estimators/absorbing_ols.py`

#### 修复 1: stats → t_dist / f_dist (4 处)
```python
# 修改前
p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=df_resid))
t_crit = stats.t.ppf(1 - alpha / 2, df=df_resid)
f_pvalue = 1 - stats.f.cdf(f_stat, dfn=df_model, dfd=rmse_df)
f_pvalue = 1 - stats.f.cdf(f_stat, dfn=df_model, dfd=df_resid)

# 修改后
p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=df_resid))
t_crit = t_dist.ppf(1 - alpha / 2, df=df_resid)
f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=rmse_df)
f_pvalue = 1 - f_dist.cdf(f_stat, dfn=df_model, dfd=df_resid)
```

#### 修复 2: MAP 路径局部变量补充
在 `fit()` 方法的 MAP 分支末尾添加：
```python
# Ensure local variables exist for postestimation assignment at end of fit()
beta_full = self._beta_full
cov_full = self._cov_full
T = self._T
```

### 验证结果
修复后 MAP 路径成功执行，数值与 LSDV 路径和 Stata 17 完全一致：

| 路径 | value β | capital β | _cons β |
|------|---------|-----------|---------|
| LSDV | 0.11012380 | 0.31006534 | -58.743939 |
| MAP | 0.11012380 | 0.31006534 | -58.743939 |
| Stata | 0.11012380 | 0.31006534 | -58.743932 |

**状态**: ✅ FIXED

---

## 2. NEW-01: xtreg_fe 不支持 robust VCE

### 问题描述
Python `xtreg_fe` 仅接受 `vce='ols'` 或 `vce='cluster'`，不接受 `vce='robust'`。

### 复现
```python
xtreg_fe(df, y='inv', x=['value', 'capital'], fe='firm', vce='robust')
# ValueError: vce='robust' not supported for FE. Use 'ols' or 'cluster'.
```

### Stata 行为
```stata
xtreg inv value capital, fe robust
```
Stata 17 完全支持，且输出 df_m=1, df_r=9（与 cluster(firm) 相同的小样本校正逻辑）。

### 影响评估
- **中低**: `xtreg, fe robust` 在计量经济学中较常用，但用户可通过 `reghdfe` + `vce(robust)` 作为替代方案。
- **建议**: 在 `xtreg_fe` 中增加 `robust` 支持，或直接映射到 `reghdfe` 的等价实现。

**状态**: ⚠️ 已知缺口，建议 backlog

---

## 3. NEW-02: savefe 固定效应数值体系与 Stata 不一致

### 问题描述
Python `savefe=True` 返回的固定效应值与 Stata `reghdfe, absorb(..., savefe)` 的 `__hdfe1__` 数值不同。

### 数值对比

| Firm | Python (LSDV dummy) | Stata (__hdfe1__) | 差值 |
|------|---------------------|-------------------|------|
| 1 | 0.000000 | -11.552754 | — |
| 2 | 172.202531 | 160.649760 | -11.552771 |
| 3 | -165.275124 | -176.827890 | -11.552766 |
| ... | ... | ... | ~-11.55278 |

### 根因
- **Python (LSDV 路径)**: 返回的是 dummy 变量系数，其中第一个 level 为 reference level，系数固定为 0。其余系数是相对于 reference level 的差值。
- **Stata (reghdfe savefe)**: 返回的是经过内部归一化的固定效应值（通常均值为 0），参考系与 LSDV 不同。

### 影响评估
- **低**: 两种表示方式数学等价，均可用于预测。但用户在直接对比数值时可能产生困惑。
- **建议**: 在文档中明确说明 Python `savefe` 返回的是 LSDV dummy 系数体系，并建议用户如需 Stata 兼容的数值，可自行做均值平移。

**状态**: ⚠️ 文档化需求

---

## 4. NEW-03: xtreg_fe RMSE 定义与 Stata 不一致

### 问题描述
Python `xtreg_fe` 返回的 `rmse=52.768`，而 Stata `xtreg, fe` 报告 `e(sigma)=100.67035`。

### 根因
- **Python**: 返回的是 within-transformed 回归的 RMSE（即 sqrt(RSS / df_r)）。
- **Stata**: `e(sigma)` 是总体误差标准差估计（基于原始尺度，sqrt(Σ(u_it²) / (N - G - k)) 或类似公式，但使用了未去均值的残差）。

### 影响评估
- **中**: 用户在直接对比 RMSE 时会发现显著差异。
- **建议**: 在 `xtreg_fe` 结果中增加 `sigma` 字段以匹配 Stata 的 `e(sigma)`，或在文档中说明 RMSE 的定义差异。

**状态**: ⚠️ 文档化需求 / 建议增强 ResultSchema

---

## 5. 修复文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/stataflow/estimators/absorbing_ols.py` | 修复 | PANEL-01: `stats` → `t_dist`/`f_dist` (4 处) |
| `src/stataflow/estimators/absorbing_ols.py` | 修复 | PANEL-01: MAP 路径补充 `beta_full`/`cov_full`/`T` 局部变量 |

---

## 6. 风险与后续行动

| 风险 | 优先级 | 行动 |
|------|--------|------|
| MAP 路径在大样本下的数值稳定性 | 中 | 需在大样本（FE levels > 5000）数据集上重新验证 MAP vs LSDV |
| MAP 路径收敛检测（PANEL-02） | 中 | 当前小样本无法触发 MAP；需构造大样本测试用例验证 `max_iter` 未收敛时的警告行为 |
| xtreg_fe robust 支持 | 低 |  backlog 中增加 `xtreg_fe(vce='robust')` 功能请求 |
| savefe 数值体系文档 | 低 | 在 `docs/` 中补充说明 Python vs Stata 的 FE 系数参考系差异 |
