# M06 PPMLHDFE 测试设计登记册

## 1. Synthetic 双跑实验

### S1: 小样本面板 Poisson 真值（手工/半解析）

- **Test ID**: `S1_SMALL_PANEL_OLS_ROBUST`
- **审查问题**: IRLS 收敛、系数、标准误、对数似然、deviance 在最小面板下是否与 Stata 一致
- **DGP**: n=60，12 个实体各 5 期，实体 FE + 时间趋势，x1、x2 为连续变量，y ~ Poisson(exp(η))
- **理论预期**: 系数为生成时使用的真实参数（但受随机性影响）；Stata 与 Python 应字段级一致
- **新颖性**: 新随机种子、新样本结构；旧 golden 使用 40 实体×5 期且未检查 deviance/ll
- **Stata 命令**: `ppmlhdfe y x1 x2, absorb(entity_id) vce(robust)`
- **Python API**: `PPMLHDFE(..., absorb=["entity_id"]).fit(vce="robust")`
- **比较字段**: coefficients, SE, VCE, nobs, df_model, df_a, df_resid, ll, deviance, pseudo_r2
- **数据来源/seed**: seed=20260612
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S1/`

### S2: 双向 FE + robust VCE

- **Test ID**: `S2_TWO_WAY_FE_ROBUST`
- **审查问题**: 双向 FE 吸收、df_a、VCE、拟合优度
- **DGP**: n=200，20 实体×10 期，实体+时间 FE，x1、x2，零膨胀 Poisson
- **理论预期**: Stata/Python 字段级一致
- **新颖性**: 双向 FE；旧测试多为单 FE 或已用特定 eform 数据
- **Stata 命令**: `ppmlhdfe y x1 x2, absorb(entity_id time_id) vce(robust) separation(none)`
- **Python API**: `PPMLHDFE(..., absorb=["entity_id","time_id"]).fit(vce="robust")`
- **比较字段**: coefficients, SE, VCE, nobs, df_model, df_a, df_resid, ll, deviance, pseudo_r2
- **数据来源/seed**: seed=20260613
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S2/`

### S3: 缺失值与 estimation sample

- **Test ID**: `S3_MISSING_SAMPLE_SCREENING`
- **审查问题**: y/x/FE/cluster 缺失时的样本剔除、sample_mask 长度与 nobs
- **DGP**: S2 数据基础上随机缺失 y（5%）、x1（5%）、entity_id（3%）、cluster（3%）
- **理论预期**: Stata 与 Python 的 nobs 相同；`sum(sample_mask) == nobs`；`len(sample_mask) == n_input_rows`
- **新颖性**: 主动在 FE/cluster 变量制造缺失；旧测试未系统检查
- **Stata 命令**: `ppmlhdfe y x1 x2, absorb(entity_id time_id) vce(cluster cl)`
- **Python API**: `PPMLHDFE(...).fit(vce="cluster", cluster="cl")`
- **比较字段**: nobs, sample_mask, df_resid, cluster_count, coefficients, SE
- **数据来源/seed**: seed=20260614
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S3/`

### S4: 共线性 / FE 内无变异变量

- **Test ID**: `S4_COLLINEAR_WITHIN_FE`
- **审查问题**: 某 x 在 FE 组内为常数时应被省略；名称/矩阵不错位
- **DGP**: 20 实体，x1 随机；x_const 等于实体编号（被 entity FE 完全解释）
- **理论预期**: x_const 被丢弃；其余系数与 Stata 一致
- **新颖性**: 检验 FE 吸收后的共线性检测
- **Stata 命令**: `ppmlhdfe y x1 x_const, absorb(entity_id) vce(robust)`
- **Python API**: `PPMLHDFE(..., x=["x1","x_const"]).fit(vce="robust")`
- **比较字段**: coefficient names, dropped variables, coefficients, SE, VCE
- **数据来源/seed**: seed=20260615
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S4/`

### S5: FE 触发分离（separation="fe"）

- **Test ID**: `S5_SEPARATION_FE`
- **审查问题**: Stata 默认 separation 与 Python `separation=None` 的样本差异
- **DGP**: 15 实体×4 期，故意让 3 个实体所有 y=0
- **理论预期**: Python `separation="fe"` 与 Stata 默认剔除 y=0 实体后 nobs、系数一致；Python `separation=None` 收敛异常或系数不同
- **新颖性**: 主动构造结构性零；旧 golden 未覆盖分离
- **Stata 命令**: `ppmlhdfe y x1 x2, absorb(entity_id) vce(robust)`（默认） 与 `..., separation(none)`
- **Python API**: `PPMLHDFE(..., separation="fe").fit(...)` 与 `separation=None`
- **比较字段**: nobs, separation_dropped, coefficients, SE, ll, deviance, warnings
- **数据来源/seed**: seed=20260616
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S5/`

### S6: Cluster-robust + singleton drop

- **Test ID**: `S6_CLUSTER_SINGLETON`
- **审查问题**: cluster VCE、singleton 删除、cluster_count、nobs
- **DGP**: n=120，10 实体×12 期，cluster id 与实体不完全相同，部分 cluster 仅含 1 观测
- **理论预期**: Stata/Python 剔除 singleton 后 nobs 一致；SE 字段级一致（默认 1e-6）
- **新颖性**: cluster 与 FE 层级不一致 + singleton
- **Stata 命令**: `ppmlhdfe y x1 x2, absorb(entity_id) vce(cluster cl)`
- **Python API**: `PPMLHDFE(...).fit(vce="cluster", cluster="cl")`
- **比较字段**: nobs, cluster_count, singleton_count, coefficients, SE, df_a
- **数据来源/seed**: seed=20260617
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S6/`

### S7: aweight 与 offset/exposure

- **Test ID**: `S7_WEIGHTS_OFFSET`
- **审查问题**: aweight 语义、offset/exposure 对常数项和似然的影响
- **DGP**: n=150，实体 FE，y ~ Poisson(exp(η + offset))，提供 offset 变量和 aweight
- **理论预期**: Stata `ppmlhdfe` 仅接受 `pweight`；Python `weights` 内部按 aweight 归一化。两者差异应被记录为 finding。
- **新颖性**: 同时施加权重与 offset；旧测试未组合
- **Stata 命令**: `ppmlhdfe y x1 x2 [pweight=w], absorb(entity_id) offset(off) vce(robust)`
- **Python API**: `PPMLHDFE(..., weights="w").fit(vce="robust")` with `offset="off"`
- **比较字段**: coefficients, SE, ll, deviance, nobs, _cons value
- **数据来源/seed**: seed=20260618
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S7/`

### S8: eform 与 predict 类型

- **Test ID**: `S8_EFORM_PREDICT`
- **审查问题**: eform beta/SE/z/p 语义；predict xb/mu/residuals/pearson/deviance
- **DGP**: n=100，实体 FE，x1、x2
- **理论预期**: eform beta=exp(raw)，SE=delta-method，z/p=raw-scale；predict mu=exp(xb)
- **新颖性**: 检查 predict pearson/deviance 与 Stata
- **Stata 命令**: `ppmlhdfe y x1 x2, absorb(entity_id) vce(robust)`；`predict ...`；`ppmlhdfe ..., eform`
- **Python API**: `PPMLHDFE(...).fit(eform=True/False).predict(type=...)`
- **比较字段**: eform coefficients/SE/z/p; predict summaries for xb, mu, residuals, pearson, deviance
- **数据来源/seed**: seed=20260619
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/synthetic/S8/`

## 2. 真实数据双跑实验

### R1: Ships 事故数据（offset/exposure + ship FE）

- **Test ID**: `R1_SHIPS_EXPOSURE`
- **审查问题**: 经典 Poisson 面板、offset、缺失值、ship FE
- **DGP/数据**: Stata `webuse ships, clear`；y=`accident`，offset=`service`，FE=`ship`
- **理论预期**: Stata/Python 字段级一致；nobs 因 service/accident 缺失为 34
- **新颖性**: 真实公开数据 + offset；旧 golden 未使用 ships
- **Stata 命令**: `ppmlhdfe accident co_65_69 co_70_74 co_75_79 op_75_79, absorb(ship) exposure(service) vce(robust)`
- **Python API**: `PPMLHDFE(..., exposure="service").fit(vce="robust")`
- **比较字段**: coefficients, SE, nobs, df_a, df_model, df_resid, ll, deviance, pseudo_r2
- **数据来源**: Stata `webuse ships`
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/real-data/R1/`

### R2: MedPAR 住院日数据（高维 provider FE + cluster）

- **Test ID**: `R2_MEDPAR_PROVIDER_CLUSTER`
- **审查问题**: 高维 FE、cluster 与 FE 同层级、大样本稳健性
- **DGP/数据**: Stata `webuse medpar, clear`；y=`los`，covariates `age white hmo died`，FE/cluster=`provnum`
- **理论预期**: Stata/Python 字段级一致（容差默认 1e-6，必要时记录并解释）
- **新颖性**: 1495 观测、高维 provider FE；旧 golden 未使用 medpar
- **Stata 命令**: `ppmlhdfe los age white hmo died, absorb(provnum) vce(cluster provnum)`
- **Python API**: `PPMLHDFE(..., absorb=["provnum"]).fit(vce="cluster", cluster="provnum")`
- **比较字段**: coefficients, SE, nobs, df_a, cluster_count, ll, deviance, pseudo_r2
- **数据来源**: Stata `webuse medpar`
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/real-data/R2/`

## 3. Metamorphic / Property Tests

### P1: 行顺序不变性

- **Test ID**: `P1_ROW_ORDER_INVARIANCE`
- **审查问题**: 行重排不应改变估计与样本掩码
- **方法**: 对 S2 DGP 随机打乱行，分别运行 Python/Stata，比较系数、nobs、sample_mask（按原行对齐）
- **理论预期**: 估计统计量完全相同
- **证据路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/property/P1/`

### P2: 无关列不变性

- **Test ID**: `P2_IRRELEVANT_COLUMN_INVARIANCE`
- **审查问题**: 增加未参与估计的列不应改变结果
- **方法**: 在 DGP 中加入随机变量 `noise`，不在 x 中使用；运行前后比较
- **理论预期**: 系数、nobs、VCE 不变
- **证据路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/property/P2/`

### P3: x 尺度变换可推导性

- **Test ID**: `P3_SCALE_TRANSFORMATION`
- **审查问题**: 对 x1 做线性尺度变换后系数/SE 应相应缩放
- **方法**: 将 x1 乘以 10，比较 beta_x1/SE_x1 变为 1/10；常数项不变
- **理论预期**: Python 与 Stata 均满足；字段级比较
- **证据路径**: `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/property/P3/`

## 4. 字段级比较容差

- 默认相对容差 `< 1e-6`，绝对容差 `< 1e-8`
- cluster VCE 下 `df_resid` 因 Stata GLM 不返回 `e(df_r)`，将单独处理：比较 Python 与从 `e(N)`/`e(k)`/`e(N_clust)` 推导的值
- 若某字段存在残余差异，需在 `findings.md` 中记录原始值、相对误差、理论解释

## 5. 本轮执行结果（2026-06-13）

| ID | Stata 命令关键选项 | 结果 | 主要差异 / finding |
|---|---|---|---|
| S1 | `vce(robust)` | PASS | 全部字段级一致 |
| S2 | `vce(robust) separation(none)` | PASS | 禁用分离后一致 |
| S3 | `vce(cluster cl) separation(none)` | PASS | 调整 cluster 为非嵌套后一致 |
| S4 | `vce(robust)` | PASS（VCE 未全矩阵比） | Stata e(V) 对 omitted 变量保留 0 行/列 |
| S5 | 默认 vs `separation(none)` | FAIL | Python `separation=None` 发散 |
| S6 | `vce(cluster cl)` | FAIL | cluster SE 残余 ~2e-6 差异 |
| S7 | `[pweight=w] offset(off)` | FAIL | offset + weights 处理严重偏离 Stata |
| S8 | `d`（predict） | FAIL | predict `xb` 语义不一致；raw/eform 系数一致 |
| R1 | `exposure(service)` | FAIL | exposure 处理严重偏离 Stata |
| R2 | `vce(cluster provid)` | PASS | 高维 FE + cluster 一致 |
| P1 | 行重排 | PASS | Python/Stata 均不变 |
| P2 | 加入无关列 | PASS | Python/Stata 均不变 |
| P3 | x1 缩放 10 倍 | PASS | Python/Stata 均满足理论缩放 |

详细差异见 `findings.md` 与 `evidence/` 各子目录。
