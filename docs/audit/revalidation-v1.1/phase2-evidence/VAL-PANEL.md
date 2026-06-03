# VAL-PANEL — Phase 2 Panel/FE/reghdfe 双跑验证报告

**验证日期**: 2026-06-03  
**数据集**: `research/data/public/panel/grunfeld.csv` (200 obs, 10 firms × 20 years)  
**Stata 版本**: 17.0 MP  
**Python 版本**: StataFlow 1.0.0 (editable install)  
**验证 Agent**: StataFlow Phase 2 双跑验证 Agent

---

## 1. 执行摘要

本次验证覆盖 Panel / FE / reghdfe 命令族 9 个测试用例，与 Stata 17 进行逐字段对比。所有基础回归用例（系数、标准误、R²、样本量、自由度）均达到 <1e-6 相对精度。

**关键结论**:
- ✅ **PANEL-01 (MAP 路径崩溃)**: 已确认并修复。根因是 `_fit_map` 中引用了未导入的 `stats` 名称。
- ✅ **PANEL-06 (xtreg_fe robust 不支持)**: Python 端仅支持 `ols`/`cluster`，不支持 `robust`。Stata 17 支持 `xtreg, fe robust`，存在功能缺口。
- ⚠️ **savefe 固定效应数值**: Python LSDV 返回的是相对于 reference level 的 dummy 系数；Stata `reghdfe, absorb(..., savefe)` 返回的是内部归一化后的固定效应值，两者数值体系不同，但均正确。

---

## 2. 测试用例与双跑结果

### Case 1: reghdfe — basic OLS
**Python**:
```python
reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm')
```
**Stata**:
```stata
reghdfe inv value capital, absorb(firm)
```

| 指标 | Python | Stata | 偏差 |
|------|--------|-------|------|
| N | 200 | 200 | — |
| df_m | 2 | 2 | — |
| df_r | 188 | 188 | — |
| df_a | 10 | 10 | — |
| R² | 0.94407251 | 0.94407252 | <1e-7 |
| Adj R² | 0.94080016 | 0.94080016 | <1e-7 |
| RMSE | 52.767966 | 52.767964 | <1e-6 |
| value β | 0.11012380 | 0.11012380 | <1e-8 |
| value SE | 0.01185669 | 0.01185669 | <1e-8 |
| capital β | 0.31006534 | 0.31006534 | <1e-8 |
| capital SE | 0.01735450 | 0.01735450 | <1e-8 |
| _cons β | -58.743939 | -58.743932 | 7e-6 |
| _cons SE | 12.453692 | 12.453691 | 1e-6 |

**结论**: ✅ PASS

---

### Case 2: reghdfe — robust VCE
**Python**: `reghdfe(..., vce='robust')`  
**Stata**: `reghdfe ..., vce(robust)`

| 指标 | Python | Stata | 偏差 |
|------|--------|-------|------|
| value SE | 0.01937803 | 0.01937803 | <1e-8 |
| capital SE | 0.04279501 | 0.04279500 | <1e-8 |
| _cons SE | 23.374219 | 23.374217 | 2e-6 |
| F | 40.227560 | 40.227572 | 1.2e-7 |

**结论**: ✅ PASS

---

### Case 3: reghdfe — cluster VCE (firm)
**Python**: `reghdfe(..., vce='cluster', cluster='firm')`  
**Stata**: `reghdfe ..., vce(cluster firm)`

| 指标 | Python | Stata | 偏差 |
|------|--------|-------|------|
| df_r | 9 | 9 | — |
| df_a | 0.0 | 0 | — (firm 嵌套于 cluster) |
| value SE | 0.01519449 | 0.01519449 | <1e-8 |
| capital SE | 0.05275177 | 0.05275177 | <1e-8 |
| _cons SE | 27.602865 | 27.602861 | 4e-6 |
| F | 28.309582 | 28.309588 | 2e-7 |

**结论**: ✅ PASS

---

### Case 3b: reghdfe — cluster VCE (year)
**Python**: `reghdfe(..., vce='cluster', cluster='year')`  
**Stata**: `reghdfe ..., vce(cluster year)`

| 指标 | Python | Stata | 偏差 |
|------|--------|-------|------|
| df_r | 19 | 19 | — |
| df_a | 10.0 | 10 | — |
| value SE | 0.01732792 | 0.01732792 | <1e-8 |
| capital SE | 0.03227888 | 0.03227887 | <1e-8 |
| _cons SE | 20.073783 | 20.073782 | 1e-6 |
| F | 98.110459 | 98.110496 | 3.8e-7 |

**结论**: ✅ PASS

---

### Case 4: reghdfe — 2-way FE
**Python**: `reghdfe(..., absorb=['firm', 'year'])`  
**Stata**: `reghdfe ..., absorb(firm year)`

| 指标 | Python | Stata | 偏差 |
|------|--------|-------|------|
| df_r | 169 | 169 | — |
| df_a | 29.0 | 29 | — |
| R² | 0.95169340 | 0.95169340 | <1e-7 |
| value β | 0.11771586 | 0.11771585 | 1e-8 |
| capital β | 0.35791627 | 0.35791627 | <1e-8 |
| _cons β | -80.163795 | -80.163784 | 1.1e-5 |

**结论**: ✅ PASS

---

### Case 5: reghdfe — slopes (`firm##c.year`)
**Python**: `reghdfe(..., absorb='firm##c.year')`  
**Stata**: `reghdfe ..., absorb(firm##c.year)`

| 指标 | Python | Stata | 偏差 |
|------|--------|-------|------|
| df_a | 20.0 | 20 | — |
| R² | 0.96417438 | 0.96417438 | <1e-7 |
| value β | 0.10920696 | 0.10920695 | 1e-8 |
| capital β | 0.29948988 | 0.29948985 | 3e-8 |
| _cons β | -54.833198 | -54.833183 | 1.5e-5 |

**Python 行为**: 成功执行（走 LSDV 路径，因数据小）。  
**结论**: ✅ PASS（数值对齐）

---

### Case 6: areg — basic
**Python**: `areg(..., absorb='firm')`  
**Stata**: `areg inv value capital, absorb(firm)`

| 指标 | Python | Stata | 偏差 |
|------|--------|-------|------|
| df_a | 9.0 | 9 | — (areg 约定：不含 constant) |
| 系数 | 与 reghdfe basic 完全一致 | 一致 | — |

**结论**: ✅ PASS

---

### Case 7: xtreg_fe — basic
**Python**: `xtreg_fe(..., fe='firm')`  
**Stata**: `xtset firm year` + `xtreg inv value capital, fe`

| 指标 | Python | Stata | 偏差 |
|------|--------|-------|------|
| N | 200 | 200 | — |
| df_m | 11.0 | 11 | — (k + G - 1 = 2 + 9) |
| df_r | 188 | 188 | — |
| R² (within) | 0.766758 | 0.766758 | <1e-6 |
| Adj R² | 0.753110 | 0.753110 | <1e-6 |
| value β / SE | 0.110124 / 0.011857 | 0.110124 / 0.011857 | <1e-6 |
| capital β / SE | 0.310065 / 0.017355 | 0.310065 / 0.017355 | <1e-6 |
| _cons | **未报告** | **未报告** | — (默认无 _cons) |
| RMSE | 52.7680 | **100.67035** | ⚠️ 差异显著 |

**RMSE 差异说明**: Stata `xtreg, fe` 报告 `e(sigma)` = 100.67035，这是总体误差标准差 σ_ε（基于原始尺度），而 Python 返回的是 within-transformed 回归的 RMSE = 52.768。两者定义不同，并非计算错误。

**结论**: ✅ PASS（系数、R² 正确；RMSE 定义差异需文档化）

---

### Case 8: MAP 路径强制触发 (PANEL-01)
**Python**:
```python
AbsorbingOLS(data=df, y='inv', x=['value', 'capital'], absorb='firm', technique='map').fit(vce='ols')
```

**修复前行为**:
```
NameError: name 'stats' is not defined
  File ".../absorbing_ols.py", line 1101, in _fit_map
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=df_resid))
```

**根因**: `_fit_map` 使用了 `stats.t.cdf` / `stats.f.cdf`，但模块仅导入 `from scipy.stats import t as t_dist, f as f_dist`，未定义 `stats` 名称。

**修复**:
- `stats.t.cdf` → `t_dist.cdf`
- `stats.t.ppf` → `t_dist.ppf`
- `stats.f.cdf` → `f_dist.cdf`
- 补充 MAP 路径中 `beta_full` / `cov_full` / `T` 局部变量未定义导致的 `UnboundLocalError`

**修复后结果**: MAP 路径成功执行，数值与 LSDV / Stata 完全一致。

| 指标 | MAP 路径 | LSDV 路径 | Stata |
|------|----------|-----------|-------|
| value β | 0.11012380 | 0.11012380 | 0.11012380 |
| capital β | 0.31006534 | 0.31006534 | 0.31006534 |
| _cons β | -58.743939 | -58.743939 | -58.743932 |

**结论**: ✅ FIXED & VERIFIED

---

### Case 9: reghdfe — savefe
**Python**: `reghdfe(..., absorb='firm', savefe=True)`  
**Stata**: `reghdfe ..., absorb(firm, savefe)`

**Python 行为**: 成功执行，返回 `result.fixed_effects` 字典，包含 `firm` Series（10 个 levels）。

**Stata 行为**: 支持 `absorb(firm, savefe)`，生成 `__hdfe1__` 变量。

**固定效应数值对比**:

| Firm | Python (LSDV dummy coef) | Stata (__hdfe1__) | 差值 |
|------|--------------------------|-------------------|------|
| 1 | 0.000000 | -11.552754 | — (参考系不同) |
| 2 | 172.202531 | 160.649760 | -11.552771 |
| 3 | -165.275124 | -176.827890 | -11.552766 |
| 4 | 42.487423 | 30.934643 | -11.552780 |
| 5 | -44.320095 | -55.872880 | -11.552785 |
| 6 | 47.135422 | 35.582639 | -11.552783 |
| 7 | 3.743244 | -7.809542 | -11.552786 |
| 8 | 12.751060 | 1.198279 | -11.552781 |
| 9 | -16.925555 | -28.478338 | -11.552783 |
| 10 | 63.728874 | 52.176088 | -11.552786 |

**分析**: Python 返回 LSDV dummy 系数（firm 1 为 reference level，系数为 0）。Stata `reghdfe savefe` 返回的是去均值化后的固定效应值（整体均值为 0）。两者差值恒定为 -11.55278，即 Stata 的参考系平移量。两者数学等价，但数值体系不同。

**结论**: ✅ PASS（功能正常，数值体系差异需文档化）

---

## 3. Phase 1 已知问题验证状态

| 问题 ID | 描述 | 验证状态 | 备注 |
|---------|------|----------|------|
| PANEL-01 | MAP 路径完全崩溃（stats 未定义） | ✅ 已修复并验证 | 修复 `stats` → `t_dist`/`f_dist`；修复 `UnboundLocalError` |
| PANEL-02 | MAP 未收敛静默继续 | ⚠️ 未触发 | grunfeld 数据集太小（10 levels），无法触发 MAP 路径；需大样本验证 |
| PANEL-03 | savefe + slopes 错位 | ⚠️ 未验证 | slopes 用例未测试 savefe 组合；Python savefe 目前仅支持 LSDV 路径 |
| PANEL-06 | xtreg_fe 默认无 _cons 且不支持 robust | ✅ 确认 | Python 默认无 _cons（与 Stata 一致），但仅支持 `ols`/`cluster`，不支持 `robust` |
| PANEL-11 | df_a 简化算法 | ✅ 验证通过 | reghdfe 1-way: 10；areg: 9；2-way: 29；cluster(firm): 0；均与 Stata 一致 |

---

## 4. 文件清单

| 文件 | 说明 |
|------|------|
| `stata/output/phase2/panel_validation.do` | Stata 批量执行脚本 |
| `stata/output/phase2/stata_reghdfe_basic.txt` | Case 1 Stata 输出 |
| `stata/output/phase2/stata_reghdfe_robust.txt` | Case 2 Stata 输出 |
| `stata/output/phase2/stata_reghdfe_cluster_firm.txt` | Case 3 Stata 输出 |
| `stata/output/phase2/stata_reghdfe_cluster_year.txt` | Case 3b Stata 输出 |
| `stata/output/phase2/stata_reghdfe_2way.txt` | Case 4 Stata 输出 |
| `stata/output/phase2/stata_reghdfe_slopes.txt` | Case 5 Stata 输出 |
| `stata/output/phase2/stata_areg_basic.txt` | Case 6 Stata 输出 |
| `stata/output/phase2/stata_xtreg_fe_basic.txt` | Case 7 Stata 输出 |
| `stata/output/phase2/stata_xtreg_fe_robust.txt` | Case 7b Stata 输出 |
| `stata/output/phase2/stata_reghdfe_savefe.txt` | Case 9 Stata 输出 |
| `stata/output/phase2/stata_reghdfe_savefe_fe.txt` | Case 9 Stata FE 值 |
| `stata/output/phase2/python_results_final.json` | Python 全部结果 JSON |
| `docs/audit/revalidation-v1.1/phase2-evidence/VAL-PANEL.md` | 本报告 |
| `docs/audit/revalidation-v1.1/phase2-evidence/NEW-PANEL.md` | 新发现问题报告 |

---

## 5. 总体结论

- **9/9 用例 Python 端均成功执行**，无崩溃。
- **系数、标准误、R²、N、df 等核心指标与 Stata 17 一致**，满足 <1e-6 相对精度要求。
- **PANEL-01 已修复**: MAP 路径从完全崩溃修复为可正常运行，且数值与 LSDV/Stata 对齐。
- **功能缺口**: `xtreg_fe` 不支持 `robust` VCE（仅 `ols`/`cluster`）。
- **文档化需求**: `savefe` 固定效应数值体系、xtreg_fe RMSE 定义差异需要在用户文档中说明。
