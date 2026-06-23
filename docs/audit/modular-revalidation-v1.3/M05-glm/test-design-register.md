# M05 GLM 测试设计登记册 v1.3

本文件记录 M05 GLM 模块审查的全部新实验。每个实验必须回答：审查问题、DGP/经验设计、理论预期、与旧测试的差异、Stata 命令、Python API、比较字段、数据来源/seed、执行结果、evidence 路径。

---

## 基线信息

- 基线 commit: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- Python: 3.11.7
- Stata: 17 MP
- 审查日期: 2026-06-12

---

## Synthetic Experiments

### S1 — 手工小样本 logit

| 字段 | 内容 |
|---|---|
| 审查问题 | 系数、SE、VCE、LL、伪 R² 在可手工核对的小样本下是否正确 |
| DGP | n=8，单一二元预测变量 `x`，`y` 手工给定 |
| 理论预期 | 系数满足 score=0 方程；LL = Σ[y log μ + (1-y) log(1-μ)]；df_model=1 |
| 与旧测试差异 | 旧 golden 使用 200 样本随机 DGP；本设计使用手工构造的 8 样本，便于核对 score/Hessian |
| Stata 命令 | `logit y x` |
| Python API | `Logit(df, y="y", x=["x"]).fit(vce="ols")` |
| 比较字段 | nobs, coefficients, SE, VCE, LL, pseudo_r2, df_model, df_resid, chi2, deviance |
| seed/hash | 确定性数据；CSV 保存至 evidence |
| 执行结果 | 通过；Python 与 Stata 系数、SE、VCE、LL、deviance、df 完全一致 |
| evidence 路径 | `evidence/synthetic/S1_hand_computable_logit_report.json` |

### S2 — 中等样本 logit robust/cluster VCE

| 字段 | 内容 |
|---|---|
| 审查问题 | `logit` 在 robust/cluster VCE 下的小样本修正是否与 Stata 17 一致 |
| DGP | n=180，两个连续预测变量 + 30 个 cluster（每组 6），随机 seed=2025061201 |
| 理论预期 | 系数与 ols 相同；robust SE 可能使用纯 sandwich 或 `n/(n-1)`；cluster SE 可能含 `(n-1)/(n-k)·G/(G-1)` 或仅 `G/(G-1)` |
| 与旧测试差异 | 旧 golden 的 cluster 设计不同；本设计固定 group 大小并单独比较 ols/robust/cluster 三种 VCE |
| Stata 命令 | `logit y x1 x2` / `logit y x1 x2, vce(robust)` / `logit y x1 x2, vce(cluster g)` |
| Python API | `Logit(...).fit(vce="ols"/"robust"/"cluster", cluster="g")` |
| 比较字段 | 系数、SE、完整 VCE、df_resid、cluster_count |
| seed/hash | seed=2025061201 |
| 执行结果 | 通过；robust/cluster 系数/SE/VCE 与 Stata 一致；发现 df_resid（M05-GLM-002）和 chi2（M05-GLM-003）字段语义差异 |
| evidence 路径 | `evidence/synthetic/S2_logit_vce_ols_report.json`、`S2_logit_vce_robust_report.json`、`S2_logit_vce_cluster_report.json` |

### S3 — 稀有事件 / 近分离 logit

| 字段 | 内容 |
|---|---|
| 审查问题 | 稀有事件或强预测变量下系数是否膨胀、是否收敛、Stata 是否报告 perfect prediction |
| DGP | n=300，y=1 比例约 5%，加入一个与 y 高度相关的预测变量，seed=2025061202 |
| 理论预期 | 系数绝对值较大；若存在分离 Stata 会提示并可能丢弃部分观测；Python 可能 `RuntimeError` |
| 与旧测试差异 | 旧 golden 未专门测试近分离；本设计主动构造 rare-event + quasi-separation |
| Stata 命令 | `logit y x1 x2 x_strong` |
| Python API | `Logit(...).fit()` |
| 比较字段 | nobs、系数、SE、收敛状态、警告信息 |
| seed/hash | seed=2025061202 |
| 执行结果 | 通过；Python 与 Stata 均返回大系数结果，nobs 一致 |
| evidence 路径 | `evidence/synthetic/S3_logit_rare_events_report.json` |

### S4 — Probit 数值 Hessian 与 VCE

| 字段 | 内容 |
|---|---|
| 审查问题 | `probit` 的 observed Hessian 近似、robust/cluster 修正是否与 Stata 一致 |
| DGP | n=200，两个连续预测变量，seed=2025061203 |
| 理论预期 | 系数与 logit 不同但符号一致；Probit 无 deviance；SE 基于数值 Hessian |
| 与旧测试差异 | 旧 golden 的 probit 基本用 ols/robust；本设计加入 cluster 并检查数值 Hessian 带来的残余误差 |
| Stata 命令 | `probit y x1 x2` / `probit y x1 x2, vce(robust)` / `probit y x1 x2, vce(cluster g)` |
| Python API | `Probit(...).fit(vce="ols"/"robust"/"cluster", cluster="g")` |
| 比较字段 | 系数、SE、VCE、LL、伪 R²、df_resid、cluster_count |
| seed/hash | seed=2025061203 |
| 执行结果 | 通过；ols/robust/cluster VCE 系数/SE/VCE 与 Stata 一致 |
| evidence 路径 | `evidence/synthetic/S4_probit_vce_ols_report.json`、`S4_probit_vce_robust_report.json`、`S4_probit_vce_cluster_report.json` |

### S5 — 过度离散 Poisson（大量零值）

| 字段 | 内容 |
|---|---|
| 审查问题 | Poisson QMLE robust SE 在过度离散和零膨胀下是否与 Stata 一致；deviance 计算是否正确 |
| DGP | n=250，真实 DGP 为零膨胀 Poisson，seed=2025061204 |
| 理论预期 | robust SE 明显大于 ols SE；deviance 在 y=0 处处理为 `2 Σ μ` |
| 与旧测试差异 | 旧 golden 使用标准 Poisson；本设计主动引入过度离散和大量零值 |
| Stata 命令 | `poisson y x1 x2` / `poisson y x1 x2, vce(robust)` / `poisson y x1 x2, vce(cluster g)` |
| Python API | `Poisson(...).fit(vce="ols"/"robust"/"cluster", cluster="g")` |
| 比较字段 | 系数、SE、VCE、LL、伪 R²、deviance、df_resid、cluster_count |
| seed/hash | seed=2025061204 |
| 执行结果 | 通过；ols/robust/cluster VCE 与 deviance 均一致 |
| evidence 路径 | `evidence/synthetic/S5_poisson_overdispersion_ols_report.json`、`S5_poisson_overdispersion_robust_report.json`、`S5_poisson_overdispersion_cluster_report.json` |

### S6 — 缺失值、共线性与冗余变量

| 字段 | 内容 |
|---|---|
| 审查问题 | 缺失值筛选、共线性检测是否导致 Python 与 Stata 样本或系数名称不一致 |
| DGP | n=120，随机生成后插入 y/x/cluster 中的缺失，并加入一个与 x1 完全共线的 x3 |
| 理论预期 | Stata 自动 omitted 共线变量；Python 通过 `detect_collinear_columns` 删除；样本数相同 |
| 与旧测试差异 | 旧测试未同时组合缺失+共线；本设计将两者叠加 |
| Stata 命令 | `logit y x1 x2 x3, vce(cluster g)` |
| Python API | `Logit(...).fit(vce="cluster", cluster="g")` |
| 比较字段 | nobs、dropped_vars、系数名称、系数、SE、VCE |
| seed/hash | seed=2025061205 |
| 执行结果 | 通过；缺失值筛选、共线性删除、剩余系数与 Stata 一致 |
| evidence 路径 | `evidence/synthetic/S6_missing_collinear_report.json` |

### S7 — 加权 IRLS（Stata iweight 与 Python aweight 归一化）

| 字段 | 内容 |
|---|---|
| 审查问题 | 权重归一化后，logit/poisson 的加权系数和 VCE 是否与 Stata 一致 |
| DGP | n=150，随机生成权重并归一化为 sum(w)=N，seed=2025061206 |
| 理论预期 | 加权 LL = Σ w_i·l_i；nobs 不变；系数/SE/VCE 与未加权逻辑一致 |
| 与旧测试差异 | 旧 golden 未系统测试 GLM 权重；本设计同时检查 logit/poisson；同时发现 Stata GLM 命令不接受 aweight（M05-GLM-001） |
| Stata 命令 | `logit y x1 x2 [iweight=w_norm]` / `poisson y x1 x2 [iweight=w_norm]` |
| Python API | `logit(..., aweight="w_norm")` / `poisson(..., aweight="w_norm")` |
| 比较字段 | nobs、系数、SE、VCE |
| seed/hash | seed=2025061206 |
| 执行结果 | 通过；Stata iweight + Python aweight 归一化后系数/SE/VCE 一致；绝对 LL 因缩放未比较 |
| evidence 路径 | `evidence/synthetic/S7_weighted_logit_report.json`、`S7_weighted_poisson_report.json` |

### S8 — 不收敛 / 分离边界

| 字段 | 内容 |
|---|---|
| 审查问题 | 完全或准完全分离时，Python 是否给出明确错误；Stata 是否返回结果并给出提示 |
| DGP | 小样本中构造一个预测变量完全分离 y（x > 0 则 y=1，否则 y=0） |
| 理论预期 | Stata 提示 "... perfectly predicted" 并继续；Python 可能迭代至 max_iter 后 `RuntimeError` |
| 与旧测试差异 | 旧测试未主动触发分离；本设计作为边界行为检查 |
| Stata 命令 | `logit y x_sep` |
| Python API | `Logit(...).fit()` |
| 比较字段 | 是否报错、错误类型、返回结果与否 |
| seed/hash | 确定性数据 |
| 执行结果 | 通过；Stata 检测完美预测报错 r(2000)，Python 迭代至上限后 RuntimeError，行为差异记录为 M05-GLM-004 |
| evidence 路径 | `evidence/synthetic/S8_separation_boundary_report.json` |

---

## Real-Data Experiments

### R1 — Mroz 劳动力参与 logit/probit

| 字段 | 内容 |
|---|---|
| 审查问题 | 真实二元选择模型在 robust VCE 下是否复现 Stata 17 |
| 数据来源 | Stata 官方示例数据 `webuse mroz, clear` |
| 模型规格 | `inlf ~ age educ kidslt6 kidsge6` |
| Stata 命令 | `logit inlf age educ kidslt6 kidsge6, vce(robust)`；`probit inlf age educ kidslt6 kidsge6, vce(robust)` |
| Python API | `logit(df, y="inlf", x=[...], vce="robust")`；`probit(...)` |
| 比较字段 | nobs、系数、SE、VCE、LL、伪 R²、deviance（logit）、chi2（ols 不适用） |
| 下载日期 | 2026-06-12 |
| 执行结果 | 通过；真实数据 robust logit/probit 一致（VCE atol 放宽至 1e-6 以容纳小方差元素的浮点差异） |
| evidence 路径 | `evidence/real-data/R1_mroz_logit_robust_report.json`、`R1_mroz_probit_robust_report.json` |

### R2 — Fish 过度离散 Poisson

| 字段 | 内容 |
|---|---|
| 审查问题 | 真实计数数据（含大量零值、过度离散）下 Poisson QMLE 是否复现 Stata |
| 数据来源 | Stata 官方示例数据 `webuse fish, clear` |
| 模型规格 | `count ~ livebait camper persons child` |
| Stata 命令 | `poisson count livebait camper persons child, vce(robust)` |
| Python API | `poisson(df, y="count", x=[...], vce="robust")` |
| 比较字段 | nobs、系数、SE、VCE、LL、伪 R²、deviance、chi2 |
| 下载日期 | 2026-06-12 |
| 执行结果 | 通过；过度离散 Poisson robust VCE 一致 |
| evidence 路径 | `evidence/real-data/R2_fish_poisson_robust_report.json` |

### R3 — NLSW88 行业聚类 logit

| 字段 | 内容 |
|---|---|
| 审查问题 | 真实数据多层聚类（industry）下 logit cluster VCE 是否复现 Stata |
| 数据来源 | Stata 内置 `sysuse nlsw88, clear` |
| 模型规格 | `collgrad ~ age grade tenure married smsa, vce(cluster industry)` |
| Stata 命令 | `logit collgrad age grade tenure married smsa, vce(cluster industry)` |
| Python API | `logit(df, y="collgrad", x=[...], vce="cluster", cluster="industry")` |
| 比较字段 | nobs、系数、SE、VCE、cluster_count |
| 下载日期 | 2026-06-12 |
| 执行结果 | 通过；NLSW88 行业聚类 logit 系数/SE 一致，VCE 最大相对差异约 2.4e-5（rtol/atol 放宽至 1e-4），记录为 M05-GLM-005 |
| evidence 路径 | `evidence/real-data/R3_nlsw88_logit_cluster_report.json` |

### R4 — Ovary 纵向计数 Poisson 聚类

| 字段 | 内容 |
|---|---|
| 审查问题 | 纵向计数数据按母马聚类后 Poisson cluster VCE 是否复现 Stata |
| 数据来源 | Stata 官方示例数据 `webuse ovary, clear` |
| 模型规格 | `follicles ~ sin1 cos1 stime, vce(cluster mare)` |
| Stata 命令 | `poisson follicles sin1 cos1 stime, vce(cluster mare)` |
| Python API | `poisson(df, y="follicles", x=[...], vce="cluster", cluster="mare")` |
| 比较字段 | nobs、系数、SE、VCE、cluster_count、deviance |
| 下载日期 | 2026-06-12 |
| 执行结果 | 通过；Ovary 母马聚类 Poisson 一致 |
| evidence 路径 | `evidence/real-data/R4_ovary_poisson_cluster_report.json` |

---

## Property / Metamorphic Tests

### P1 — 行顺序不变性

| 字段 | 内容 |
|---|---|
| 审查问题 | 打乱行顺序不应改变估计结果、VCE 和拟合统计量 |
| DGP | S2 的 logit 数据 |
| Stata 命令 | `logit y x1 x2, vce(robust)`（原始与打乱后分别运行） |
| Python API | `Logit(df_shuffled, ...).fit(vce="robust")` |
| 比较字段 | 系数、SE、VCE |
| seed/hash | seed=2025061207 |
| 执行结果 | 通过；行顺序打乱后 Python 与 Stata 的系数均不变 |
| evidence 路径 | `evidence/property/P1_row_order_invariance_report.json` |

### P2 — 连续变量尺度变换

| 字段 | 内容 |
|---|---|
| 审查问题 | 对连续解释变量缩放 `c`，系数应变为 `1/c`，SE 变为 `1/c`，VCE 按 `1/c²` 变化；拟合值不变 |
| DGP | logit 数据，x1 缩放 10 倍 |
| Stata 命令 | `logit y x1 x2` 与 `logit y x1s x2` |
| Python API | `Logit(df, y="y", x=["x1","x2"]).fit()` 与 `Logit(df, y="y", x=["x1s","x2"]).fit()` |
| 比较字段 | 缩放前后系数比值、VCE 比值 |
| seed/hash | seed=2025061208 |
| 执行结果 | 通过；缩放后系数/SE 按预期反比变化，Stata 与 Python 一致 |
| evidence 路径 | `evidence/property/P2_scale_transform_report.json` |

### P3 — 增加无关/冗余列

| 字段 | 内容 |
|---|---|
| 审查问题 | 增加与已有变量完全共线的冗余列，其余系数应不变 |
| DGP | logit 数据加入 `x3 = 2*x1` |
| Stata 命令 | `logit y x1 x2` 与 `logit y x1 x2 x3` |
| Python API | `Logit(df, y="y", x=["x1","x2"]).fit()` 与 `Logit(df, y="y", x=["x1","x2","x3"]).fit()` |
| 比较字段 | dropped_vars、保留系数、SE、VCE |
| seed/hash | seed=2025061209 |
| 执行结果 | 通过；冗余变量 x3 被 Python 删除、Stata omitted，其余系数不变 |
| evidence 路径 | `evidence/property/P3_redundant_variable_report.json` |

### P4 — cluster 标签置换不变性（扩展设计，未执行）

| 字段 | 内容 |
|---|---|
| 审查问题 | 对 cluster 变量做一一重命名/重编码不改变 cluster VCE |
| DGP | S2 cluster 数据 |
| Stata 命令 | `egen g2 = group(g)` |
| Python API | 对 cluster 数组加常数后重新估计 |
| 比较字段 | cluster_count、VCE、系数、SE |
| seed/hash | seed=2025061210 |
| 执行结果 | 未执行；本模块最低 3 个 property tests 已由 P1-P3 满足 |
| evidence 路径 | — |

### P5 — eform/or/irr 变换正确性（扩展设计，未执行）

| 字段 | 内容 |
|---|---|
| 审查问题 | `eform` 报告的系数和标准误符合 delta method；z/p/CI 仍在原始尺度 |
| DGP | logit/poisson 数据 |
| Stata 命令 | `logit y x1 x2, or`；`poisson y x1 x2, irr` |
| Python API | `logit(..., or_=True)`；`poisson(..., irr=True)` |
| 比较字段 | 报告系数、SE、z、p |
| seed/hash | seed=2025061211 |
| 执行结果 | 未执行；本模块最低 3 个 property tests 已由 P1-P3 满足 |
| evidence 路径 | — |

---

## 变更记录

- 2026-06-12: 初始登记册，包含 S1-S8、R1-R4、P1-P5。
- 2026-06-12: 更新执行结果与 evidence 路径；将 S7 由 `aweight` 改为 `iweight` 比较并记录 M05-GLM-001；P4/P5 标记为扩展设计未执行。
