# Phase 2 RD 验证新发现

**验证日期**: 2026-06-03

---

## NEW-RD-01: rdplot bin 选择算法与 Stata 差异巨大

### 发现描述
在 Senate RD 数据集上，Stata 的 `rdplot vote margin, c(0)` 选择 **15 (左) / 35 (右)** 个 bins，而 Python (`RDPlot`) 选择 **5 (左) / 16 (右)** 个 bins。

- 左侧 bin 数偏差: 15 vs 5 (Python 少 **67%**)
- 右侧 bin 数偏差: 35 vs 16 (Python 少 **54%**)

### 影响
Bin 数量直接决定 RD 图中 binned means 的密度和局部多项式拟合的视觉呈现。偏差超过 50% 会导致图形与 Stata 输出完全不同，无法用于复现 Stata 的 RD 可视化结果。

### 根因分析
Python 的 `_compute_bins_esmv` 和 `_compute_bins_qsmv` 是简化实现：
- 使用全局多项式拟合（order 4 fallback 到 2）估计导数和方差
- Bias 估计使用均匀网格积分
- Variance 估计使用 spacing-based 近似

而 Stata 的 `rdplot` 使用 Calonico-Cattaneo-Titiunik (2015, JASA) 的完整算法，包括：
- 更精细的 pilot 估计
- 对 mimicking-variance 和 IMSE-optimal 两种准则的分别计算
- 更稳健的边界处理

### 建议
- 将 `RDPlot` 的 bin 选择算法与 Stata 的 `rdplot` 源码或 rdrobust 包的 Mata 源码对齐
- 或至少在文档中声明 bin 数量可能与 Stata 存在显著差异

---

## NEW-RD-02: rdplot 使用 covariates 时未给出兼容性警告

### 发现描述
Stata 的 `rdplot` 在使用 `covs()` 选项时明确给出警告：

> "covs() option is meant to be used when plotting RDROBUST estimates. If the option is used for global polynomial fitting, it may deliver results that are not visually compatible with the local binned means depicted due to the underlying assumptions used."

Python 的 `rdplot` wrapper 在使用 `covs` 时**静默执行**，未提供任何警告。

### 影响
用户可能误以为 covariate-adjusted rdplot 的拟合线与 binned means 是视觉兼容的，但实际上 Python 也使用全局 OLS 调整，与局部 bin 均值可能不一致。

### 建议
在 `rdplot` wrapper 中加入与 Stata 类似的警告信息。

---

## NEW-RD-03: rdrobust cluster VCE 下默认调用双重崩溃

### 发现描述
`rdrobust` wrapper 在 `vce='cluster'` 且未显式提供 `bwselect` 时，会因 **RD-01** 而崩溃。即使用户显式提供 `bwselect='mserd'`，带宽仍与 Stata 存在 **2.2%** 差异。

这意味着 Cluster VCE 场景在 Python 端存在两个层面的问题：
1. **可用性**: 默认调用不可用（崩溃）
2. **精度**: 显式调用后带宽仍偏差 2.2%

### 建议
- 修复 RD-01（默认 bwselect）
- 在 Cluster VCE 路径下，将聚类结构纳入 MSE 带宽选择的残差方差估计，而非仅用于 CER scaling
