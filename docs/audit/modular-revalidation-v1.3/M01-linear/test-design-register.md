# M01 Linear 测试设计登记册 v1.3

## 说明

本登记册记录 M01 Linear 模块审查中每个新实验的独立设计。所有实验均为本轮新建，未复用旧 golden 测试的 DGP、随机种子、脚本或 expected values。

---

## Synthetic 实验

### S1_hand_computable

| 字段 | 内容 |
|---|---|
| test ID | S1_hand_computable |
| 审查问题 | OLS 正规方程、系数、RSS/TSS、R²、F 的解析正确性 |
| DGP | n=6，x = [-2,-1,0,1,2,3]，y = 2 + 3x + ε，ε ~ N(0, 0.5²) |
| 理论预期 | 系数可由 (X'X)⁻¹X'y 手工计算；R²、F 与 Stata 一致 |
| 新颖性说明 | 样本量极小，可手工复核；与旧 golden 的 n=200 随机 DGP 完全不同 |
| Stata 命令 | `regress y x` |
| Python API | `OLS(df, y="y", x=["x"]).fit(vce="ols")` |
| 比较字段 | nobs、df_model、df_resid、R²、adj R²、RMSE、F、p、RSS、TSS、系数、完整 VCE |
| 数据来源/seed | seed=20260612，手工构造 |
| 执行结果 | PASS |
| evidence 路径 | `evidence/synthetic/S1_hand_computable_report.json` |

### S2_heteroskedastic

| 字段 | 内容 |
|---|---|
| test ID | S2_heteroskedastic |
| 审查问题 | HC1 robust VCE 是否正确捕获已知异方差 |
| DGP | n=500，x ~ N(0,1)，σ_i = 1 + 2\|x_i\|，ε_i ~ N(0, σ_i²)，y = 1 + 2x + ε |
| 理论预期 | robust SE > 同方差 SE；Wald F 与 Stata `regress, robust` 一致 |
| 新颖性说明 | 异方差结构明确且随 x 单调变化，可验证 robust SE 是否系统性更大 |
| Stata 命令 | `regress y x, robust` |
| Python API | `OLS(df, y="y", x=["x"]).fit(vce="robust")` |
| 比较字段 | nobs、df、R²、RMSE、F、系数、SE、完整 VCE |
| 数据来源/seed | seed=2026061201 |
| 执行结果 | PASS |
| evidence 路径 | `evidence/synthetic/S2_heteroskedastic_report.json` |

### S3_imbalanced_cluster

| 字段 | 内容 |
|---|---|
| test ID | S3_imbalanced_cluster |
| 审查问题 | 单路 cluster-robust VCE 在极不均衡组大小下的行为 |
| DGP | n=400，19 个单例 cluster + 1 个 381 观测的大 cluster |
| 理论预期 | 系数不变；SE 使用 G=20 的小样本调整；df_resid = G-1 = 19 |
| 新颖性说明 | 旧 golden 使用均衡 cluster；本设计测试大组主导时的 cluster 推断 |
| Stata 命令 | `regress y x, cluster(g)` |
| Python API | `OLS(df, y="y", x=["x"]).fit(vce="cluster", cluster="g")` |
| 比较字段 | nobs、cluster_count、df_resid、系数、SE、完整 VCE |
| 数据来源/seed | seed=2026061202 |
| 执行结果 | PASS |
| evidence 路径 | `evidence/synthetic/S3_imbalanced_cluster_report.json` |

### S4_aweight_missing

| 字段 | 内容 |
|---|---|
| test ID | S4_aweight_missing |
| 审查问题 | aweight 含缺失值时的样本筛选与归一化 |
| DGP | n=300，20 个权重缺失 |
| 理论预期 | 缺失权重行被删除；有效 nobs=280；sum(w*) = 280 |
| 新颖性说明 | 专门测试权重缺失路径，与旧测试的完整权重设计不同 |
| Stata 命令 | `regress y x [aweight=w]` |
| Python API | `OLS(..., weights=..., weight_type="aweight").fit()` |
| 比较字段 | nobs、df、R²、RMSE、系数、SE、RSS、TSS、完整 VCE |
| 数据来源/seed | seed=2026061203 |
| 执行结果 | PASS |
| evidence 路径 | `evidence/synthetic/S4_aweight_missing_report.json` |

### S4b_aweight_zero

| 字段 | 内容 |
|---|---|
| test ID | S4b_aweight_zero |
| 审查问题 | aweight=0 时的样本处理 |
| DGP | n=100，10 个权重为 0 |
| 理论预期 | Stata 删除零权重行并完成回归；Python 当前抛出 ValueError |
| 新颖性说明 | 直接针对 v1.2 未覆盖的零权重边界 |
| Stata 命令 | `regress y x [aweight=w]` |
| Python API | `regress(df, y="y", x=["x"], aweight="w")` |
| 比较字段 | Python 是否崩溃、Stata nobs |
| 数据来源/seed | seed=2026061206 |
| 执行结果 | FAIL（Python 崩溃）→ 对应 finding M01-LIN-001 |
| evidence 路径 | `evidence/synthetic/S4b_aweight_zero_report.json` |

### S5_near_collinearity

| 字段 | 内容 |
|---|---|
| test ID | S5_near_collinearity |
| 审查问题 | 近共线回归变量的省略行为 |
| DGP | n=250，x2 = (x1 + tiny_noise) × 1e6 |
| 理论预期 | Stata 省略 x1 并估计稳定模型；Python 保留两列导致病态系数 |
| 新颖性说明 | 测试不同量纲下的共线性 tolerance，与旧测试的低相关设计不同 |
| Stata 命令 | `regress y x1 x2` |
| Python API | `OLS(df, y="y", x=["x1", "x2"]).fit()` |
| 比较字段 | 系数、SE、df、R²、RMSE、F、VCE、dropped vars |
| 数据来源/seed | seed=2026061204 |
| 执行结果 | FAIL → 对应 finding M01-LIN-002 |
| evidence 路径 | `evidence/synthetic/S5_near_collinearity_report.json` |

### S6_factor_missing_changes_base

| 字段 | 内容 |
|---|---|
| test ID | S6_factor_missing_changes_base |
| 审查问题 | factor base level 在缺失改变有效样本后是否正确重确定 |
| DGP | n=400，g ∈ {1,2,3,4}，所有 g=1 的 x 缺失，使用 `i.g##c.x` |
| 理论预期 | base level 从完整数据的 1 变为有效样本的 2；不删除常数 |
| 新颖性说明 | 直接验证 v1.2 FVAR-001 修复效果；与旧 factor 测试的完整数据不同 |
| Stata 命令 | `regress y i.g##c.x` |
| Python API | `regress(df, y="y", x=["i.g##c.x"])` |
| 比较字段 | 系数名称/顺序、系数值、nobs、df、VCE |
| 数据来源/seed | seed=2026061205 |
| 执行结果 | PASS |
| evidence 路径 | `evidence/synthetic/S6_factor_missing_changes_base_report.json` |

### S7_two_way_cluster_balanced

| 字段 | 内容 |
|---|---|
| test ID | S7_two_way_cluster_balanced |
| 审查问题 | 平衡两路 cluster VCE 与 F 统计量 |
| DGP | n=600，30 firms × 20 years，含 firm/year shock |
| 理论预期 | 系数/SE 与 Stata `vce(cluster firm year)` 一致 |
| 新颖性说明 | 与 R2 的小 G 真实数据互补，隔离 VCE 公式本身的问题 |
| Stata 命令 | `regress y x, vce(cluster firm year)` |
| Python API | `OLS(...).fit(vce="cluster", cluster=["firm", "year"])` |
| 比较字段 | nobs、df、R²、RMSE、系数、SE、F、完整 VCE |
| 数据来源/seed | seed=2026061207 |
| 执行结果 | 系数/SE/VCE PASS，F-stat FAIL → 对应 finding M01-LIN-003 |
| evidence 路径 | `evidence/synthetic/S7_two_way_cluster_balanced_report.json` |

---

## Real-Data 实验

### R1_engel_robust

| 字段 | 内容 |
|---|---|
| test ID | R1_engel_robust |
| 审查问题 | 公开数据上的典型 OLS + robust VCE |
| 数据集 | statsmodels.datasets.engel（Engel food expenditure） |
| 研究问题 | foodexp ~ income |
| Stata 命令 | `regress foodexp income, robust` |
| Python API | `regress(df, y="foodexp", x=["income"], vce="robust")` |
| 比较字段 | nobs、df、R²、RMSE、F、系数、SE、完整 VCE |
| 数据来源 | statsmodels 内置数据集 |
| 执行结果 | PASS |
| evidence 路径 | `evidence/real-data/R1_engel_robust_report.json` |

### R2_modechoice_two_way_cluster

| 字段 | 内容 |
|---|---|
| test ID | R2_modechoice_two_way_cluster |
| 审查问题 | 公开数据上的两路 cluster（困难条件：小 G） |
| 数据集 | statsmodels.datasets.modechoice（transport mode choice） |
| 研究问题 | linear probability model: choice ~ ttme invc invt gc hinc，cluster(individual mode) |
| Stata 命令 | `regress choice ttme invc invt gc hinc, vce(cluster individual mode)` |
| Python API | `regress(df, y="choice", x=[...], vce="cluster", cluster=["individual", "mode"])` |
| 比较字段 | nobs、df、R²、RMSE、系数、SE、F、VCE、cluster_count |
| 数据来源 | statsmodels 内置数据集；mode 仅 4 个 cluster |
| 执行结果 | FAIL（SE 1–3% 差异，F-stat 不一致）→ 与 M01-LIN-003 及小 G 调整有关 |
| evidence 路径 | `evidence/real-data/R2_modechoice_two_way_cluster_report.json` |

---

## Metamorphic / Property Tests

### P1_row_order_invariance

| 字段 | 内容 |
|---|---|
| test ID | P1_row_order_invariance |
| 审查问题 | 行顺序不影响估计 |
| 设计 | 同一数据集随机重排，比较原序与重排后的结果 |
| 理论预期 | 系数、SE、VCE、fit stats 不变 |
| Stata 命令 | `regress y x1 x2, robust`（对原序和重排后分别运行） |
| Python API | `regress(df, ...)` 和 `regress(df_perm, ...)` |
| 执行结果 | PASS |
| evidence 路径 | `evidence/synthetic/P1_row_order_invariance_report.json` |

### P2_irrelevant_column

| 字段 | 内容 |
|---|---|
| test ID | P2_irrelevant_column |
| 审查问题 | 增加不参与估计的无关列（含缺失）不应改变结果 |
| 设计 | 原数据 vs 加入全缺失列 z 的数据 |
| 理论预期 | nobs、系数、SE 完全相同 |
| Stata 命令 | `regress y x`（两数据集） |
| Python API | `regress(df, y="y", x=["x"])` 和 `regress(df_with_z, ...)` |
| 执行结果 | PASS |
| evidence 路径 | `evidence/synthetic/P2_irrelevant_column_report.json` |

### P3_scale_transformation

| 字段 | 内容 |
|---|---|
| test ID | P3_scale_transformation |
| 审查问题 | 合法尺度变换产生可推导的系数/VCE 变化 |
| 设计 | x10 = x × 10；验证 β_x10 = β_x / 10，SE_x10 = SE_x / 10 |
| 理论预期 | 常数项不变；x 的系数和标准误均缩小 10 倍 |
| Stata 命令 | `regress y x` 和 `regress y x10` |
| Python API | `regress(df, y="y", x=["x"])` 和 `regress(df_scaled, y="y", x=["x10"])` |
| 执行结果 | PASS |
| evidence 路径 | `evidence/synthetic/P3_scale_transformation_report.json` |

---

## 与旧测试的差异声明

- 未使用 `tests/golden/` 中的任何 `_make_ols_data`、`_make_cluster_data` 或固定随机种子。
- 未使用 `stata/cases/` 中的任何既有 `.do` 文件或 `.dta` 文件。
- 未复用 Grunfeld 数据集的 OLS 规格（旧 golden `test_v1_regress_real_grunfeld.py` 已存在）。
- 所有 Stata 输出均由本轮现场执行产生，未从旧日志复制。
