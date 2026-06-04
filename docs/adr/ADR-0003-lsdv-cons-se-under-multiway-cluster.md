# ADR-0003: LSDV 框架下多向聚类 _cons 标准误的结构性差异

## 背景

StataFlow 的 HDFE 估计器（`reghdfe`、`ivreghdfe`、`ppmlhdfe`）使用 LSDV（虚拟变量最小二乘）框架吸收固定效应，而 Stata 17 的 `reghdfe` 使用迭代去均值（iterative demeaning）框架。在单向 VCE 或非聚类场景下，两者等价。但在**多向聚类稳健标准误**（2-way cluster-robust VCE）下，两种框架在常数项（`_cons`）标准误上产生**结构性差异**。

此 ADR 记录该差异的数学根因、量化幅度、以及受控容忍度层级。

## 数学根因

### LSDV 框架

LSDV 将 FE 虚拟变量直接纳入设计矩阵 `X_full = [X, D_1, ..., D_G, 1]`，通过 OLS 正规方程求解全参数向量 `beta_full`。常数项通过 T 矩阵恢复：

```
_cons = gamma_const + sum_g (1/|G_g|) * sum_{i in g} alpha_g_i
```

其中 `gamma_const` 是显式常数项系数，`alpha_g_i` 是 FE 虚拟变量的系数。该线性组合的精确方差为：

```
Var(_cons) = T[cons, :] @ cov_full @ T[cons, :]'
```

其中 `cov_full = (X_full' X_full)^(-1) * Omega_meat * (X_full' X_full)^(-1)`，`Omega_meat` 为 Cameron-Gelbach-Miller 包含-排除 meat 矩阵（`M_1 + M_2 - M_12`）。

### reghdfe 迭代去均值框架

reghdfe 通过交替投影消除 FE，在去均值后的残差空间中进行估计。常数项通过以下公式恢复：

```
b0 = weighted_mean(y_resid) - sum_j weighted_mean(x_j_resid) * b_j
```

其方差涉及 `b_j`、`x_bar_j`、`y_bar` 的联合分布，reghdfe 通过迭代过程的内部传播矩阵计算。

### 差异来源

两个框架在 `_cons` SE 上出现差异，根因有三：

1. **T 矩阵变换后的 PSD fix**：包含-排除 meat 矩阵 `M_1 + M_2 - M_12` 可能非正定。PSD fix（特征值截断 + slope 子矩阵恢复）在 `cov_reported` 层级操作，改变了 `_cons` 的方差和协方差，但保留了 slope SE 不变。此操作在 reghdfe 的 Mata 代码 `reghdfe_fix_psd` 中同样存在，但操作对象不同（reghdfe 操作的是去均值后的残差空间 VCV）。

2. **小样本调整的传播路径差异**：LSDV 框架的小样本调整 `(N-1)/(N-k_eff) * G/(G-1)` 作用于全参数空间（含 FE 虚拟变量），然后通过 T 矩阵压缩到报告空间。reghdfe 的小样本调整直接作用于去均值后的残差空间。

3. **嵌套 FE 的 RMSE 自由度计算**：当 FE 变量嵌套于聚类变量时，两种框架对有效自由度的计算方式不同。

### 量化

| 场景 | Python LSDV `_cons` SE | Stata reghdfe `_cons` SE | 相对差异 |
|------|------------------------|--------------------------|---------|
| 合成数据（平衡 panel, x 均值≈0） | delta-method 近似 | 基准 | ~2.25% |
| 真实数据（wagepan, 非零 x 均值, 二元变量） | delta-method 近似 | 基准 | ~16% |

## 决策

### 容忍度层级体系

建立两级 `_cons` SE 容忍度：

| 层级 | 适用场景 | 最大 rtol | 理由 |
|------|---------|-----------|------|
| Tier 1 | 合成数据（平衡设计, 连续 x） | 0.03（3%） | delta-method 将残余控制在 ~2.25% 以内 |
| Tier 2 | 真实数据（非平衡设计, 含二元/分类 x） | 0.20（20%） | delta-method 在非零 x 均值下失效；T-matrix 直接结果受 PSD fix 影响 |

### 长期方向

此差异的**唯一根治方式**是实现迭代去均值（MAP/LSMR）吸收内核（当前计划在 Wave 12）。在此之前：

1. 所有受影响的测试**必须**在注释中引用 ADR-0003
2. 所有公开文档**必须**在已知限制中标注此差异
3. slope SEs 保持 `< 1e-6` 硬标准（不受此次 ADR 影响）
4. 如在非 2-way cluster 场景（OLS、robust、1-way cluster）下出现 _cons SE 偏差，**不可**引用此 ADR — 必须作为 bug 修复

### 例外审批流程

新增容忍度例外必须满足：
1. 数学根因已定位且可证明
2. 量化残余差异
3. 确认无更低成本修复方案
4. 通过 ADR 记录并获得 correctness-gatekeeper 批准

## 备选方案

### 方案 A：不接受差异，迁移到迭代去均值

- 优点：彻底消除差异
- 缺点：重大架构变更，需重写所有 HDFE 估计器内核，影响 Wave 0-7 全部内容；工作量为 3-6 个月

### 方案 B：仅报告 slope，不报告 _cons

- 优点：规避问题
- 缺点：Stata 报告 _cons，用户期望看到 _cons；破坏 API 兼容性

## 后果

- 多向聚类 VCE 的 `_cons` SE 永远不等于 Stata，直到迁移到迭代去均值
- 每个受影响命令的支持矩阵必须明确标注此限制
- 每个受影响的 golden 测试必须引用 ADR-0003

## 受影响文件

- `src/stataflow/estimators/absorbing_ols.py` L587-597（delta-method `_cons` SE）
- `src/stataflow/estimators/iv.py`（`_cons` 从不报告，不受影响）
- `src/stataflow/estimators/ppmlhdfe.py`（T 矩阵构造，`_cons` 恢复）
- `tests/golden/test_w7_reghdfe_2way_cluster.py` L200-210（rtol=0.03）
- `tests/golden/test_w7_reghdfe_2way_cluster_real.py` L170-183（rtol=0.20）
- `tests/golden/test_w7_ivreghdfe_2way_cluster.py` L197-207（rtol=0.03）
- `tests/golden/test_w7_ppmlhdfe_2way_cluster.py` L166-176（rtol=0.03）
- `docs/command-support-matrix/reghdfe.md`、`ivreghdfe.md`、`ppmlhdfe.md`

## 何时重审

- 实现迭代去均值内核后（Wave 12）
- LSDV T 矩阵构造方式发生重大变化
- 发现新的 _cons SE 计算公式可缩小差距至 < 1% 且证明正确

## 2026-06-04 裁定落地

在 `docs/audit/revalidation-v1.1` 这一轮全面复核中，`IV-14` 被正式按本 ADR 关闭为**已知局限**，不再作为本轮开放 bug 保留。  
关闭条件是：

- synthetic 2-way cluster `_cons` SE 残差仍处于 Tier 1 容忍度内
- real-data 2-way cluster `_cons` SE 残差仍处于 Tier 2 容忍度内
- slope SE、`df_resid`、weak-IV、first-stage、second-stage `fit.f_stat` 已全部独立收口

这意味着：在 Wave 12 / HDFE 内核重构之前，`_cons` SE 的 2-way cluster 残差继续按 ADR 约束管理，而不再进入本轮修缮的开放缺陷列表。
