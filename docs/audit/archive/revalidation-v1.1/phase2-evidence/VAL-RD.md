# Phase 2 RD / Local Polynomial 双跑验证报告

**验证日期**: 2026-06-03
**数据集**: `rdrobust_senate_with_z.dta` (N=1390, 实际使用 N=1297)
**Stata 版本**: 17.0
**Python 版本**: StataFlow 1.0.0 (editable)

---

## 摘要

| 测试项 | Stata 结果 | Python 结果 | 状态 |
|--------|-----------|-------------|------|
| 1. rdrobust basic | tau=7.4141, h=17.754 | **崩溃** (NotImplementedError) | ❌ RD-01 |
| 2. rdrobust mserd | tau=7.4141, h=17.754 | tau=7.4139, h=17.759 | ✅ 通过 |
| 3. rdrobust covs | tau=6.9089, h=17.256 | **崩溃** (NotImplementedError) | ❌ RD-01 |
| 4. rdrobust cluster | tau=7.3948, h=18.084 | tau=7.4167, h=17.687 | ❌ RD-02 |
| 5. rdplot basic | J=15/35 | J=5/16 | ❌ 偏差大 |
| 6. rdplot covs | J=15/35 | J=5/16 | ❌ 偏差大 |

---

## 1. rdrobust - basic (默认)

### Stata
```stata
rdrobust vote margin, c(0)
```

- BW type: `mserd`
- h = 17.754, b = 28.028
- N = 1297, N_l = 595, N_r = 702
- N_h_l = 360, N_h_r = 323
- tau_cl = 7.4141, Robust CI = [4.0937, 10.9193]

### Python
```python
rdrobust(df, y='vote', x='margin', c=0)
```

**结果**: `NotImplementedError: Automatic bandwidth selection is required when h is not provided. Use bwselect='mserd' or provide h explicitly.`

**诊断**: Wrapper 默认未设置 `bwselect='mserd'`，与 Stata 的 rdrobust 默认行为不一致。Stata 的 `rdrobust` 在 `h` 未提供时默认使用 `mserd`。

**对应问题**: **RD-01**

---

## 2. rdrobust - 显式 bwselect="mserd"

### Stata
```stata
rdrobust vote margin, c(0) bwselect(mserd)
```

- h = 17.754, b = 28.028
- tau_cl = 7.4141, Robust z = 4.3110, CI = [4.0937, 10.9193]

### Python
```python
rdrobust(df, y='vote', x='margin', c=0, bwselect='mserd')
```

- h = 17.759, b = 28.035
- tau_cl = 7.4139, tau_bc = 7.5060, se_rb = 1.7411
- 推断 Robust CI = [4.0935, 10.9185]

**对比**:

| 指标 | Stata | Python | 相对偏差 |
|------|-------|--------|----------|
| h | 17.754 | 17.759 | 0.03% |
| b | 28.028 | 28.035 | 0.02% |
| tau_cl | 7.4141 | 7.4139 | 0.003% |
| tau_bc (推断) | 7.5065 | 7.5060 | 0.007% |
| se_rb (推断) | 1.7412 | 1.7411 | 0.006% |
| N_h_l | 360 | 360 | 0% |
| N_h_r | 323 | 323 | 0% |

**结论**: 显式 `bwselect='mserd'` 时，Python 与 Stata 结果高度一致，相对偏差 < 0.1%。

---

## 3. rdrobust - covariates

### Stata
```stata
rdrobust vote margin, c(0) covs(class termshouse)
```

- h = 17.256, b = 27.697
- N = 1108 (covariates 缺失值导致样本减少)
- N_h_l = 306, N_h_r = 277
- tau_cl = 6.9089, Robust CI = [3.6945, 10.4544]

### Python (默认调用)
```python
rdrobust(df, y='vote', x='margin', c=0, covs=['class', 'termshouse'])
```

**结果**: `NotImplementedError` (同测试 1)

### Python (显式 bwselect)
```python
rdrobust(df, y='vote', x='margin', c=0, bwselect='mserd', covs=['class', 'termshouse'])
```

- h = 17.241, b = 27.671
- tau_cl = 6.9088, tau_bc = 7.0741, se_rb = 1.7251
- 推断 Robust CI = [3.6939, 10.4543]

**对比**:

| 指标 | Stata | Python (显式) | 相对偏差 |
|------|-------|---------------|----------|
| h | 17.256 | 17.241 | 0.09% |
| b | 27.697 | 27.671 | 0.09% |
| tau_cl | 6.9089 | 6.9088 | 0.001% |
| N_h_l | 306 | 306 | 0% |
| N_h_r | 277 | 277 | 0% |

**结论**: 显式 `bwselect` 时结果高度一致。但默认调用崩溃，确认 **RD-01**。

---

## 4. rdrobust - cluster VCE

### Stata
```stata
rdrobust vote margin, c(0) vce(cluster state)
```

- h = 18.084, b = 27.651
- N = 1297, N_h_l = 366, N_h_r = 325
- tau_cl = 7.3948, Robust CI = [3.9889, 11.021]
- Number of clusters: 50 / 50

### Python (默认调用)
```python
rdrobust(df, y='vote', x='margin', c=0, vce='cluster', cluster='state')
```

**结果**: `NotImplementedError` (同测试 1)

### Python (显式 bwselect)
```python
rdrobust(df, y='vote', x='margin', c=0, bwselect='mserd', vce='cluster', cluster='state')
```

- h = 17.687, b = 28.097
- N = 1297, N_h_l = 359, N_h_r = 321
- tau_cl = 7.4167, tau_bc = 7.5054, se_rb = 1.7694
- 推断 Robust CI = [4.0373, 10.9735]

**对比**:

| 指标 | Stata | Python (显式) | 相对偏差 |
|------|-------|---------------|----------|
| h | 18.084 | 17.687 | **2.2%** |
| b | 27.651 | 28.097 | **1.6%** |
| tau_cl | 7.3948 | 7.4167 | 0.30% |
| N_h_l | 366 | 359 | 1.9% |
| N_h_r | 325 | 321 | 1.2% |
| se_rb (推断) | ~1.791 | 1.7694 | 1.2% |

**诊断**:
- Stata 在 `vce(cluster)` 下带宽选择为 **18.084**，而 Python 为 **17.687**，差异 **2.2%**。
- Python 代码中，带宽选择时将 `vce="cluster"` 映射为 `vce_bw="hc0"` 进行残差计算，仅通过 `cluster_l`/`cluster_r` 影响 CER scaling 部分，而未影响核心的 MSE 带宽选择过程。
- Stata 的 rdrobust 在 cluster VCE 下，带宽选择会考虑聚类结构（使用聚类稳健方差估计进行 pilot 和 MSE 计算），导致带宽变大。

**对应问题**: **RD-02** (Cluster VCE 带宽选择未考虑聚类结构)

---

## 5. rdplot - basic

### Stata
```stata
rdplot vote margin, c(0)
```

- Bins selected: J_l = 15, J_r = 35
- Average bin length: 6.667 (左), 2.857 (右)
- IMSE-optimal bins: 8 (左), 9 (右)
- Mimicking Var. bins: 15 (左), 35 (右)
- BW poly. fit (h): 100.000

### Python
```python
rdplot(df, y='vote', x='margin', c=0)
```

- J_star_l = 5, J_star_r = 16
- h_l = 100.0, h_r = 100.0
- mean_y_left = 36.77, mean_y_right = 70.86
- fit_beta_l (c 点) = 43.94, fit_beta_r (c 点) = 53.34

**对比**:
- Stata 选择 **15/35** bins，Python 选择 **5/16** bins。
- Python 的 `_compute_bins_esmv` 实现为简化版，与 Stata 的 rdplot 内部算法（基于 Calonico-Cattaneo-Titiunik 2015 JASA 的完整 IMSE-optimal bin 选择）存在显著差异。
- 拟合线截距（c 点）: Stata 未直接报告，但 Python 的 local polynomial fit 在 c=0 处的左值为 43.94，右值为 53.34。

---

## 6. rdplot - with covariates

### Stata
```stata
rdplot vote margin, c(0) covs(class)
```

- Bins selected: J_l = 15, J_r = 35 (与 basic 完全相同)
- Stata 给出警告: "covs() option is meant to be used when plotting RDROBUST estimates..."

### Python
```python
rdplot(df, y='vote', x='margin', c=0, covs=['class'])
```

- J_star_l = 5, J_star_r = 16 (与 basic 相同)
- fit_beta_l (c 点) = 44.35, fit_beta_r (c 点) = 53.74
- 协变量调整后拟合线有微小偏移 (43.94→44.35, 53.34→53.74)

**诊断**:
- Python 的协变量调整使用**全局 OLS** (`Z_centered = Z - Z.mean(); gamma_cov = np.linalg.lstsq(Z_centered, y_centered)`)。
- Stata 也使用全局多项式拟合进行 covariate adjustment（并明确警告可能不与局部 binned means 视觉兼容）。
- 但 Python 的 bin 数量与 Stata 差异巨大（5/16 vs 15/35），导致 binned means 的视觉呈现完全不同。

**对应问题**: **RD-03** (rdplot 协变量调整使用全局 OLS，且 bin 选择算法差异大)

---

## 已知问题验证结论

| 问题 ID | 描述 | 验证结果 | 严重程度 |
|---------|------|----------|----------|
| RD-01 | rdrobust wrapper 默认未启用 bwselect="mserd" | **确认存在**。默认调用必崩。 | 🔴 高 |
| RD-02 | Cluster VCE 带宽选择未考虑聚类结构 | **确认存在**。cluster VCE 下带宽偏差 2.2%。 | 🟡 中 |
| RD-03 | rdplot 协变量调整使用全局 OLS | **确认存在**。且 bin 选择算法差异更大 (5/16 vs 15/35)。 | 🟡 中 |

---

## 附件

- Stata `.do` 文件: `stata/output/phase2/val_rd.do`
- Stata 日志:
  - `stata/output/phase2/stata_rdrobust_basic.log`
  - `stata/output/phase2/stata_rdrobust_mserd.log`
  - `stata/output/phase2/stata_rdrobust_covs.log`
  - `stata/output/phase2/stata_rdrobust_cluster.log`
  - `stata/output/phase2/stata_rdplot_basic.log`
  - `stata/output/phase2/stata_rdplot_covs.log`
- Python 结果:
  - `stata/output/phase2/python_rd_results.json`
  - `stata/output/phase2/python_rd_results2.json`
