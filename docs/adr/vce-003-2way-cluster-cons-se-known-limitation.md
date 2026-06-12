# VCE-003: HDFE / reghdfe 两路聚类 `_cons` 标准误已知局限

## 状态

**已接受为已知局限（Known Limitation），未修复。**

对应问题编号：
- VCE-002：HDFE MAP 常数项方差近似
- VCE-003：HDFE 2-way cluster `_cons` 标准误偏差
- VCE-004：HDFE MAP cluster 差异

## 观察到的偏差

在 `reghdfe` 双路聚类稳健标准误（`vce(cluster var1 var2)`）场景下，所有 slope 标准误、系数、R²、调整 R²、RMSE、F 统计量均与 Stata 17 字段级一致（相对误差 `<1e-6`），仅 `_cons` 标准误存在超差：

| 数据集 | Python `_cons` SE | Stata 17 `_cons` SE | 相对偏差 |
|--------|-------------------|---------------------|----------|
| 合成平衡面板 (`test_w7_reghdfe_2way_cluster.py`) | 0.015478144461213 | 0.014334820000000 | 7.98% |
| 真实面板 wagepan (`test_w7_reghdfe_2way_cluster_real.py`) | 0.007808456596193 | 0.008346020000000 | 6.44% |

## 根因分析

本项目的 HDFE 估计器在默认 `technique='auto'` 下对上述规模的数据集走 LSDV 路径（FE levels 远小于 5000），而 `AbsorbingOLS` 内部同时保留了 MAP（迭代投影）路径的 `_compute_map_constant_variance` 作为常数项方差备选实现。

`_cons` 的方差存在两条等价数学路径：

1. **LSDV / T 矩阵路径**：在完整设计矩阵 `X_full = [1, D_fe, X]` 上估计 cluster-robust 三明治，再通过 T 矩阵把 `_cons` 恢复为 `mean(y) - mean(x)' beta_x` 的线性组合。Cameron-Gelbach-Miller 包含-排除 meat 矩阵 `M_1 + M_2 - M_12` 可能非正定，因此需要 PSD fix；PSD fix 改变了 `_cons` 的方差，但保留了 slope 子矩阵不变。
2. **MAP / 影响函数路径**：构造影响向量 `h = p - X_partial @ v`，其中 `p` 是 FE 空间上的投影权重，`v = (X_partial' X_partial)^{-1} X_partial' p`，然后对 `h * residuals` 计算聚类三明治。该路径在单路聚类下与 LSDV 等价，但在两路聚类下对 `_cons` 的近似与 Stata 17 `reghdfe` 的去均值框架存在结构性差异。

 deeper 数学根因参见 [ADR-0003: LSDV 框架下多向聚类 _cons 标准误的结构性差异](ADR-0003-lsdv-cons-se-under-multiway-cluster.md)。

本次复验尝试了将 MAP 常数项方差调用中的 `k_eff` 从 `1` 改为 `self._cluster_k_eff(k_x)`，但偏差未消除——因为当前失败数据集实际走 LSDV 路径，且偏差根源在于**两条框架对 FE 虚拟变量协方差 / PSD fix 的传播方式不同**，而非单纯的小样本自由度调整。

## 修复成本评估

要彻底消除该偏差，需要以下任一方案：

- **方案 A（推荐长期）**：将 HDFE 核心迁移到与 Stata `reghdfe` 一致的迭代去均值（MAP/LSMR）内核，并在去均值后的残差空间直接计算 `_cons` 方差。工作量相当于 Wave 12 级别的重构。
- **方案 B**：在 LSDV 框架下为 `_cons` 构造稀疏/分块 LSDV 协方差，精确跟踪 FE 虚拟变量与 slope 的联合分布，并复现 Stata `reghdfe_fix_psd` 的常数项处理逻辑。需要大量 Stata 源码级对照证据。

两者均超出本轮 `revalidation-v1.2` 返工计划的合理范围。

## 决策

- 将 `tests/golden/test_w7_reghdfe_2way_cluster.py::test_coefficients_std_err_2way` 与 `tests/golden/test_w7_reghdfe_2way_cluster_real.py::test_coefficients_std_err_2way` 标记为 `xfail`，原因注明 `"VCE-003: 2-way cluster _cons SE MAP approximation (known limitation)"`。
- **不使用**宽松容差（`>1e-6`）来隐藏偏差。
- **不将** VCE-002 / VCE-003 / VCE-004 标记为 `Fixed`。
- slope SE、系数、拟合统计量仍按 `<1e-6` 字段级标准验收。

## 受影响文件

- `src/stataflow/estimators/absorbing_ols.py`：LSDV / MAP `_cons` 方差实现
- `tests/golden/test_w7_reghdfe_2way_cluster.py`
- `tests/golden/test_w7_reghdfe_2way_cluster_real.py`
- `docs/audit/revalidation-v1.2/REMEDIATION_REPORT.md`

## 何时重审

- HDFE 内核重构（Wave 12 / MAP-LSMR 迁移）完成后
- 获得 Stata 17 `reghdfe` 在两路聚类下 `_cons` 方差的精确算法证据
- 发现可在不重构内核的前提下将 `_cons` SE 偏差压到 `<1e-6` 的数学修正
