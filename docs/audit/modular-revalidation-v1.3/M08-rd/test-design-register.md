# M08 RD 测试设计登记册 v1.3

## 执行基线

- 基线 commit: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- Stata 17 MP: `D:\Software\Stata17\StataMP-64.exe`
- `rdrobust` ado 版本: v10.0.0 (随 rdrobust 包安装)
- `rdplot` ado 版本: 与 rdrobust 包一致
- 全部 Stata 日志由本轮现场生成，未复用旧 golden expected values

## 新颖性说明

所有 synthetic DGP 使用新的随机种子、样本量、协变量结构、带宽规格和 VCE 类型。与现有 `tests/test_rdrobust.py` 和 `tests/golden/test_w8_*` / `test_v2_c1_8_*` 的主要区别：

- 旧测试主要使用 `n=500`、`seed=42`、uniform[-1,1] running variable、线性 DGP；本轮使用新 seed 系列 `20260620**`、非对称密度、二次/二次+协变量 DGP、聚类层级冲击、极端尺度。
- 旧 golden 在 Senate 数据上反复使用 `vote margin, c(0) bwselect(mserd)` 及 `h(15)` / `cluster(state)`；本轮真实数据实验使用 `cersum` + covs + `hc0` + epanechnikov，以及 swapped axes + `msetwo` 的全新规格。
- 旧 `test_rdplot_binselect_matches_stata_synthetic` 使用 `np.random.seed(42)` 的正态二次 DGP；本轮 rdplot 实验使用新的 seed 与显式 bin 数量对比。

## 1. Synthetic 双跑实验

### S1: 手工可计算小样本

- **Test ID**: `S1_HAND_CHECKABLE`
- **审查问题**: 局部线性设计矩阵、uniform kernel 全带宽时的手工可验证性
- **DGP**: n=12, x=±0.1,±0.2,...,±0.6, y=1+2x+3·1[x≥0]+N(0,0.001²)
- **理论预期**: 当 uniform kernel h=0.5 包含全部观测时，tau_cl ≈ 3.0；Stata 与 Python 在系数、SE、nobs 上字段级一致
- **新颖性**: 极小的 hand-checkable 样本；旧测试最小 n=100/200
- **Stata 命令**: `rdrobust y x, c(0) h(0.5) kernel(uniform)`
- **Python API**: `rdrobust(data, y="y", x="x", c=0.0, h=0.5, kernel="uniform")`
- **比较字段**: tau_cl, SE_cl, nobs, N_l, N_r, N_h_l, N_h_r, h_l, h_r
- **数据来源/seed**: seed=2026062001
- **执行结果**: 待执行
- **Evidence 路径**: `docs/audit/modular-revalidation-v1.3/M08-rd/evidence/synthetic/S1_HAND_CHECKABLE/`

### S2: 标准 sharp RD 同质处理效应

- **Test ID**: `S2_STANDARD_SHARP_RD`
- **审查问题**: 中等样本 sharp RD 的 conventional/robust 估计与带宽选择
- **DGP**: n=600, x~U(-1.5,1.5), y=0.5+1.2x-0.4x²+2.5·1[x≥0]+N(0,0.6²)
- **理论预期**: tau_cl 接近 2.5；bwselect(mserd) 自动带宽为正
- **新颖性**: 新 seed、二次 DGP、更广支撑、更大样本方差
- **Stata 命令**: `rdrobust y x, c(0) bwselect(mserd)`
- **Python API**: `rdrobust(data, y="y", x="x", c=0.0, bwselect="mserd")`
- **比较字段**: tau_cl/tau_bc/tau_rb, SE_cl/SE_rb, nobs, N_h_l/r, h_l/r, b_l/r
- **数据来源/seed**: seed=2026062002
- **Evidence 路径**: `evidence/synthetic/S2_STANDARD_SHARP_RD/`

### S3: 协变量调整

- **Test ID**: `S3_COVARIATES`
- **审查问题**: `covs` 选项的局部投影 / s-vector 构造
- **DGP**: n=600, z=0.3x+N(0,0.5²), y=0.5+1.2x-0.4x²+2.5·1[x≥0]+0.9z+N(0,0.6²)
- **理论预期**: 协变量调整后 tau 仍接近 2.5，SE 可能降低
- **新颖性**: 强相关协变量；旧 Senate covs 测试使用已有数据，本 synthetic 设计独立
- **Stata 命令**: `rdrobust y x, c(0) bwselect(mserd) covs(z)`
- **Python API**: `rdrobust(data, ..., covs="z")`
- **比较字段**: tau_cl/tau_rb, SE_cl/SE_rb, nobs, h_l/r
- **数据来源/seed**: seed=2026062003
- **Evidence 路径**: `evidence/synthetic/S3_COVARIATES/`

### S4: Cluster VCE

- **Test ID**: `S4_CLUSTER_VCE`
- **审查问题**: cluster-robust VCE 与聚类层级计数
- **DGP**: n=400, 40 clusters, cluster-level shock N(0,0.8²), x~U(-1.5,1.5), jump=2.5
- **理论预期**: cluster SE 与 nn SE 不同；Stata 与 Python 在 tau、SE、cluster count 上一致
- **新颖性**: 聚类冲击 DGP；旧 cluster 测试使用 Senate `state` 作为聚类
- **Stata 命令**: `rdrobust y x, c(0) bwselect(mserd) vce(cluster g)`
- **Python API**: `rdrobust(data, ..., vce="cluster", cluster="g")`
- **比较字段**: tau_cl/tau_rb, SE_cl/SE_rb, nobs, N_h_l/r, h_l/r
- **数据来源/seed**: seed=2026062004
- **Evidence 路径**: `evidence/synthetic/S4_CLUSTER_VCE/`

### S5: 用户指定带宽与 CER 选择器

- **Test ID**: `S5A_EXPLICIT_ASYMMETRIC_H`, `S5B_CER_SELECTOR`
- **审查问题**: 非对称 h、CER shrinkage 选择器
- **DGP**: n=600, 左侧密度 65%，右侧 35%，二次 DGP
- **理论预期**: S5A h_l=0.9, h_r=1.3 精确匹配；S5B certwo 带宽 ≤ msetwo 且按 CER factor 缩放
- **新颖性**: 非对称密度 + 非对称带宽 + CER；旧测试未组合
- **Stata 命令**: `rdrobust y x, c(0) h(0.9 1.3) kernel(epanechnikov)` / `rdrobust y x, c(0) bwselect(certwo)`
- **Python API**: `rdrobust(data, h=(0.9,1.3), kernel="epanechnikov")` / `bwselect="certwo"`
- **比较字段**: h_l/r, b_l/r, tau, SE, nobs, N_h_l/r
- **数据来源/seed**: seed=2026062005
- **Evidence 路径**: `evidence/synthetic/S5A_EXPLICIT_ASYMMETRIC_H/`, `evidence/synthetic/S5B_CER_SELECTOR/`

### S6: 数值应力（极端尺度 + 稀疏 cutoff 附近）

- **Test ID**: `S6_NUMERICAL_STRESS`
- **审查问题**: 极小带宽、稀疏 cutoff 数据、极端 y 尺度下的数值稳定性
- **DGP**: n≈500, 仅 5% 观测在 [-0.05,0.05], y 尺度 1e4
- **理论预期**: 不崩溃；tau_cl 接近 2.5×1e4；SE 同尺度
- **新颖性**: 极端数值条件；旧测试未主动构造
- **Stata 命令**: `rdrobust y x, c(0) h(0.35) kernel(triangular)`
- **Python API**: `rdrobust(data, h=0.35, kernel="triangular")`
- **比较字段**: tau_cl, SE, nobs, N_h_l/r, h_l/r
- **数据来源/seed**: seed=2026062006
- **Evidence 路径**: `evidence/synthetic/S6_NUMERICAL_STRESS/`

### S7: rdplot bin 选择

- **Test ID**: `S7_RDPLOT_ESMV`, `S7_RDPLOT_QSMV`
- **审查问题**: rdplot 自动 bin 数量 (J_star_l/r) 与 Stata 对齐
- **DGP**: n=500, x~N(0,1), y=2+1.5x+0.5x²+N(0,0.5²)
- **理论预期**: esmv/qsmv 各自 bin 数与 Stata 一致
- **新颖性**: 新 seed 的 rdplot 独立验证；旧 rdplot 测试使用 seed=42
- **Stata 命令**: `rdplot y x, c(0) binselect(esmv)` / `rdplot y x, c(0) binselect(qsmv)`
- **Python API**: `rdplot(data, ..., binselect="esmv")`
- **比较字段**: N_l, N_r, J_star_l, J_star_r
- **数据来源/seed**: seed=2026062007
- **Evidence 路径**: `evidence/synthetic/S7_RDPLOT_ESMV/`, `evidence/synthetic/S7_RDPLOT_QSMV/`

## 2. 真实数据双跑实验

### R1: Senate CER-SUM + 协变量 + HC0

- **Test ID**: `R1_SENATE_CERSUM_COVS_HC0`
- **审查问题**: 真实数据上 covariate-adjusted、非默认带宽选择器、非 nn VCE 的字段级对齐
- **数据**: `research/data/public/rdrobust_senate_with_z.dta`
- **理论预期**: tau/SE/bandwidths 与 Stata 一致
- **新颖性**: 不同于旧 golden 的 `mserd`/h(15)/cluster(state) 规格；使用 cersum + covs + hc0 + epanechnikov
- **Stata 命令**: `rdrobust vote margin, c(0) bwselect(cersum) covs(z) vce(hc0) kernel(epanechnikov)`
- **Python API**: `rdrobust(data, y="vote", x="margin", bwselect="cersum", covs="z", vce="hc0", kernel="epanechnikov")`
- **比较字段**: tau_cl/bc/rb, SE_cl/rb, nobs, h_l/r, b_l/r
- **数据来源/哈希**: 文件 `rdrobust_senate_with_z.dta`
- **Evidence 路径**: `evidence/real-data/R1_SENATE_CERSUM_COVS_HC0/`

### R2: Senate 交换轴 + MSE-TWO

- **Test ID**: `R2_SENATE_SWAPPED_MSETWO`
- **审查问题**: 不同识别设计（margin 作为 outcome，vote 作为 running var）+ 非对称选择器
- **数据**: `research/data/public/rdrobust_senate_with_z.dta`
- **理论预期**: msetwo 允许左右不同带宽；结果与 Stata 一致
- **新颖性**: 与旧 golden 使用 `vote` 作为 outcome、`margin` 作为 running var 相反；cutoff=50
- **Stata 命令**: `rdrobust margin vote, c(50) bwselect(msetwo) vce(nn) kernel(triangular)`
- **Python API**: `rdrobust(data, y="margin", x="vote", c=50.0, bwselect="msetwo")`
- **比较字段**: tau_cl/bc/rb, SE_cl/rb, nobs, h_l/r, b_l/r
- **数据来源/哈希**: 文件 `rdrobust_senate_with_z.dta`
- **Evidence 路径**: `evidence/real-data/R2_SENATE_SWAPPED_MSETWO/`

## 3. Metamorphic / Property Tests

### P1: 行顺序不变性

- **Test ID**: `P1_ROW_ORDER_INVARIANCE`
- **方法**: 对 S2 DGP 打乱行后重新运行 rdrobust
- **理论预期**: Python 内部 tau_cl/SE 不变；Stata 双跑与打乱后 Python 结果一致
- **Stata 命令**: `rdrobust y x, c(0) bwselect(mserd)`
- **Python API**: `rdrobust(shuffled, ..., bwselect="mserd")`
- **证据路径**: `evidence/property/P1_ROW_ORDER_INVARIANCE/`

### P2: 无关列不变性

- **Test ID**: `P2_IRRELEVANT_COLUMN`
- **方法**: 在数据中增加未使用的随机列
- **理论预期**: Python 内部 tau_cl/SE 不变；Stata 双跑与加列后 Python 结果一致
- **证据路径**: `evidence/property/P2_IRRELEVANT_COLUMN/`

### P3: 结果变量尺度变换可推导性

- **Test ID**: `P3_OUTCOME_SCALING`
- **方法**: 将 y 乘以常数 3.0，验证 tau 与 SE 同比例缩放
- **理论预期**: scaled tau_cl = 3 × base tau_cl, scaled SE_cl = 3 × base SE_cl
- **证据路径**: `evidence/property/P3_OUTCOME_SCALING/`

## 4. 字段级比较容差

- beta (tau_cl/bc/rb): rtol=1e-5, atol=1e-6
- std_err: rtol=3e-2, atol=1e-6（允许 plug-in / cluster 小样本修正残余）
- t_stat/z_stat: rtol=3e-2, atol=1e-6
- p_value: rtol=5e-2, atol=1e-6
- nobs / N_*: rtol=1e-5, atol=1e-6
- bandwidths (h_*, b_*): rtol=5e-4, atol=1e-6（自动带宽选择器的数值方差）
- rdplot bin counts: rtol=1e-5, atol=1e-6（整数精确匹配）
