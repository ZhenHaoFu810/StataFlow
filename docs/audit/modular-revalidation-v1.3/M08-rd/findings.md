# M08 RD 独立审查发现

## 执行基线

- 模块: M08 Regression Discontinuity
- 审查日期: 2026-06-13
- 基线 commit: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- Python: 3.11.7, NumPy 1.26.4, pandas 3.0.2, SciPy 1.17.1, statsmodels 0.14.6
- Stata 17 MP: `D:\Software\Stata17\StataMP-64.exe`
- 本轮未修改 `src/stataflow/` 产品代码

---

## M08-RD-001: `certwo` 带宽选择器在不对称密度设计下存在 ~0.3% 残余

- **Finding ID**: M08-RD-001
- **Severity**: P2
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `stataflow.RDRobust.fit()` / `stataflow.compat.stata.rdrobust(..., bwselect="certwo")`
- **最小复现**: `tests/audit_v1_3/m08_rd/test_m08_synthetic.py::TestM08S5UserBandwidth::test_s5b_cer_selector`
- **Stata 17 结果**:
  - `h_l` = 0.26235056, `h_r` = 0.46260535
  - `b_l` = 0.5802921, `b_r` = 0.96658664
  - `N_h_r` = 63
- **Python 结果**:
  - `h_l` = 0.262350558, `h_r` = 0.463800950
  - `b_l` = 0.580292093, `b_r` = 0.968044736
  - `N_h_r` = 64
- **根因分析**: S5 的 running variable 左侧密度为 65%、右侧为 35%，`certwo` 基于 `msetwo` 的左右独立 MSE 带宽再乘以 CER 缩放因子。Python 与 Stata 在右侧独立 MSE 带宽的迭代求解中出现了约 0.26% 的相对差异，并导致 cutoff 附近一个观测值的边界包含/排除不同（63 vs 64）。常规点估计与标准误仍高度一致（beta 相对误差 <1e-5，SE <0.1%），说明核心局部多项式估计公式一致，差异集中在三步 plug-in 带宽选择器对非对称分布的数值路径。
- **用户影响**: 使用 `bwselect="certwo"` / `"msetwo"` 等左右独立选择器且 running variable 密度明显不对称时，带宽和有效观测数可能与 Stata 有微小差异，但对点估计和推断结论影响极小。
- **受影响范围**: 非对称设计下的 `msetwo`、`certwo`、`msecomb2`、`cercomb2` 选择器。
- **共享基础设施问题**: 否，属于 `RDRobust` 内部 `_rdbwselect` / `_three_step_bw_two` 实现。
- **旧 issue**: 未发现已登记的同类问题。
- **建议修复方向**: 进一步比对新旧 rdrobust 包参考实现中 `_three_step_bw_two` 的边界处理、质点调整与 `bwcheck` 的交互；在差异可解释且 <1% 时也可文档化为已知残余。

---

## M08-RD-002: 小有效样本下 Python 返回有限 bias-corrected / robust 估计，Stata 返回缺失

- **Finding ID**: M08-RD-002
- **Severity**: P2
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `stataflow.RDRobust.fit()` / `stataflow.compat.stata.rdrobust()`
- **最小复现**: `tests/audit_v1_3/m08_rd/test_m08_synthetic.py::TestM08S1HandCheckable` (n=12, effective obs per side = 5–6)
- **Stata 17 结果**:
  - `e(b)[1,2]` (tau_bc) = .
  - `e(b)[1,3]` (tau_rb) = .
  - `e(V)[2,2]` / `e(V)[3,3]` = .
  - 输出警告: "Estimates might be unreliable due to low number of effective observations."
- **Python 结果**:
  - `tau_bc` = 2.9963, `tau_rb` = 2.9963（有限值）
  - `se_tau_rb` = 0.9471（有限值）
- **根因分析**: Stata `rdrobust` 在有效观测数过低时选择不报告 bias-corrected / robust 系数（矩阵元素缺失），而 Python 实现始终计算并返回这些值。这属于可靠性阈值语义差异：Python 没有复制 Stata 的“样本不足时抑制稳健推断”的 guardrails。
- **用户影响**: 在 cutoff 附近数据稀疏或带宽极小时，Python 会给出形式上完整的 conventional / bias-corrected / robust 结果，但用户可能意识不到这些值在 Stata 中会被视为不可靠。
- **受影响范围**: 所有小 effective sample 的 rdrobust 调用，尤其是用户指定极小带宽或自动选择器返回极窄带宽的场景。
- **共享基础设施问题**: 否。
- **旧 issue**: 未发现。
- **建议修复方向**: 在 `RDRobust.fit()` 中增加与 Stata 类似的低有效样本检查，当 `N_h_l` / `N_h_r` / `N_b_l` / `N_b_r` 低于可靠阈值时，将 `tau_bc`、`tau_rb` 及对应 SE 设为 `NaN` 或发出明确警告。

---

## 已验证通过的路径

以下路径字段级对齐（在调整后容差内）：

- 小样本手工可计算 local-linear (S1, conventional 部分)
- 标准 sharp RD 同质处理效应 (S2, `bwselect="mserd"`)
- 协变量调整 sharp RD (S3, `covs="z"`)
- Cluster-robust VCE (S4, `vce="cluster"`)
- 用户指定非对称带宽 (S5A, `h=(0.9, 1.3)`, `kernel="epanechnikov"`)
- 数值应力：极端尺度 + cutoff 附近稀疏 (S6)
- `rdplot` 自动 bin 选择 (S7, `esmv` / `qsmv`)
- 真实数据：Senate `cersum` + covs + `hc0` + epanechnikov (R1)
- 真实数据：Senate 交换轴 + `msetwo` (R2)
- Python 内部性质：行顺序不变性、无关列不变性、y 缩放可推导性 (P1–P3)
