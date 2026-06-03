# ADR-0004: PSD Fix Architecture for Multi-Way Cluster VCE

## 背景

StataFlow 的 HDFE 估计器在多向聚类稳健标准误下使用 Cameron-Gelbach-Miller 包含-排除原理（`Omega = M_1 + M_2 - M_12`）。该 meat 矩阵在变换到报告空间后（`cov_reported = T @ cov_full @ T.T`）可能非正定。Stata 的 `reghdfe` 通过 `reghdfe_fix_psd` 函数处理此问题。此 ADR 记录 StataFlow 中的对应设计决策。

## 决策

### PSD Fix 操作层级：`cov_reported`（非 `omega_meat`）

- **最初实现**将 PSD fix 应用于 `omega_meat`（meat 矩阵层），这会在 T 矩阵变换前腐蚀 slope SEs
- **修正后**将 PSD fix 应用于 `cov_reported = T @ cov_full @ T.T`，匹配 Stata reghdfe 的 `reghdfe_fix_psd` 操作层级

### Slope 子矩阵恢复

`fix_psd_reghdfe(mat)` 的实现策略：
1. 备份 slope 子矩阵（除 `_cons` 外的所有行列）
2. 特征分解后截断负特征值至零
3. 从备份恢复 slope 子矩阵

此策略确保 slope SEs 不受 PSD fix 影响，仅 `_cons` SE 及 slope-cons 协方差可能被修改。这与 reghdfe 的 Mata 代码行为一致。

### 与 ADR-0003 的关系

PSD fix 主要处理 `_cons` 方向的非正定性。由于 ADR-0003 已确立 LSDV 框架下 `_cons` SE 的结构性差异，PSD fix 在此场景中起到保护性作用（防止负方差），但无法消除 ADR-0003 描述的残余差异。

### 代码位置

共享实现位于 `src/stataflow/estimators/_vce_utils.py`，由 `absorbing_ols.py`、`iv.py`、`ppmlhdfe.py` 统一导入。

## 备选方案

### 方案 A：在 omega_meat 层操作

- 优点：更早修复，全链路 PSD
- 缺点：在 CGM 包含-排除后、T 矩阵变换前截断特征值会改变 slope VCV；与 reghdfe 行为不一致

### 方案 B：在 cov_full 层操作

- 优点：在 T 矩阵变换前的全参数空间
- 缺点：`cov_full` 维度过高（含 FE 虚拟变量），特征分解计算量大；T 矩阵变换后仍需再次修复

## 后果

- 三个 HDFE 估计器的 PSD fix 行为一致
- 代码无重复（单一共享实现）
- 与 ADR-0003 的 _cons SE 容忍度体系互补

## 受影响文件

- `src/stataflow/estimators/_vce_utils.py`（新建，共享实现）
- `src/stataflow/estimators/absorbing_ols.py`（重构为导入共享模块）
- `src/stataflow/estimators/iv.py`（重构为导入共享模块）
- `src/stataflow/estimators/ppmlhdfe.py`（重构为导入共享模块）

## 何时重审

- 迁移到迭代去均值内核后（Wave 12），PSD fix 可能不再需要
- 发现 reghdfe Mata 源码中 `reghdfe_fix_psd` 的层级与本文档不一致
