# Package I -- RD Completion Research (Wave 8 Round 1)

**日期：** 2026-04-28
**任务：** `package-i-rd-completion-research`
**编制：** StataFlow Roadmaster
**目标 Wave：** Wave 8 Round 1（Research）
**下一轮：** Round 2（Min Implementation）

---

## Background

Wave 6 实现了 `rdrobust` 的 sharp RD 子集（deriv=0、显式带宽、`mserd` 自动带宽、`covs`、`tri/epa/uni` kernel、`nn/hc0` VCE），并通过 `rdrobust_senate.dta` 双跑验证。

Wave 7（HDFE Hardening）已全部完成，2-way cluster 基础设施稳定，具备进入 Wave 8 的条件。

当前 `rdrobust` 的完整度约 40%，主要缺口为：
- 带宽选择器族仅实现 `mserd`（还缺 9 个）
- 不支持 fuzzy RD（模糊断点回归）
- 不支持 weights（频率权重）
- 不支持 vce(cluster) / vce(nncluster)
- masspoints 处理逻辑内嵌在 `_rdbwselect_mserd` 中，未作为独立参数暴露
- 无 rdplot 伴侣命令

## Objective

为 Wave 8 的六大功能缺口完成研究归档，锁定 Stata 源码证据与 synthetic 测试用例设计，使项目具备进入 Round 2（最小实现）的全部前置条件。

### 六大研究方向

| 编号 | 方向 | 当前状态 | 研究目标 |
|------|------|----------|----------|
| R1 | 完整带宽选择器族 | 仅 `mserd` | 研究 msetwo/msesum/msecomb1-2/cerrd/certwo/cersum/cercomb1-2 的公式与实现路径 |
| R2 | Fuzzy RD | 硬拒绝 | 研究两阶段局部多项式 Wald 估计量、sharpbw 子选项、完美依从处理 |
| R3 | vce(cluster) / vce(nncluster) | 硬拒绝 | 研究聚类稳健 VCE 的 sandwich 构造与小样本修正 |
| R4 | weights | 硬拒绝 | 研究频率权重在内核权重、带宽选择、VCE 中的传播路径 |
| R5 | masspoints | 内嵌但未暴露 | 研究 masspoints(check/adjust/off) 的完整参数化 |
| R6 | rdplot 伴侣命令 | 不存在 | 研究数据驱动分箱与局部多项式拟合线的绘制算法 |

## Why Now

1. RD 是因果推断三大工具（DID / IV / RD）之一，当前实现仅为 sharp RD 子集，真实研究几乎全用自动带宽选择器族和 fuzzy RD。
2. Wave 7 的 2-way cluster VCE 基础设施已稳定，可直接复用到 RD 的 cluster VCE。
3. RD 不依赖 HDFE 内核，独立性强，可与 DID Hardening（Wave 9）并行推进。
4. ROADMASTER_PLAN.md 明确指定 Wave 8 在 Wave 7 之后，入口标准已满足。

## Permitted Modification Scope

### 允许的操作
- 阅读 `research/vendor/stata_community/rdrobust/` 中的 Stata/Mata 源码（`.ado`, `.do`, `.mo`）
- 阅读 CCT (2014a, 2014b, 2016a, 2016b) 等 RD 方法论文献
- 在 `docs/research/` 下创建或更新研究档案：
  - `docs/research/rdrobust-bandwidth-selectors.md`（新增，R1）
  - `docs/research/rdrobust-fuzzy.md`（新增，R2）
  - `docs/research/rdrobust-cluster-vce.md`（新增，R3）
  - `docs/research/rdrobust-weights.md`（新增，R4）
  - `docs/research/rdrobust-masspoints.md`（新增，R5）
  - `docs/research/rdrobust-rdplot.md`（新增，R6）
  - `docs/research/rdrobust-source-map.md`（更新，统一所有研究的源码映射）
- 在 `docs/testing/test-case-catalog.md` 预登记 Wave 8 synthetic 和 real-data 样例
- 更新 `docs/command-support-matrix/rdrobust.md` 的 Planned Parameters 列表（将 Research 阶段确认可实现的选项加上 planned 标记）
- 运行 `pytest tests/ -q --ignore=tests/golden/` 确认无回归

### 禁止的操作
- **禁止修改 `src/stataflow/estimators/rdrobust.py`**（实现代码属于 Round 2）
- **禁止修改 `src/stataflow/compat/stata/rdrobust.py`**（wrapper 属于 Round 2）
- **禁止新增 golden 测试文件**（双跑验证属于 Round 3）
- **禁止修改 `ResultSchema`**（若研究表明确需新增字段，需记录为 escalation 项）
- **禁止运行 Stata 双跑**（Stata 双跑验证属于 Round 2/3）
- 禁止修改 `docs/project-charter.md` 或架构原则

## Execution Order

### 第一步：R1 完整带宽选择器族（优先）

**源码依据：** `rdbwselect.ado`（完整源码，已完整阅读）
**核心发现：** 当前 Python `_rdbwselect_mserd()` 已实现 MSE-RD 三步插件流程。其余 9 个选择器均基于同一 `rdrobust_bw()` 基础函数，仅组合方式不同。

需研究并归档的内容：
1. **TWO 分支**（`msetwo`, `certwo`）：两侧独立带宽。`d_bw_l` 和 `d_bw_r` 使用各自的分母 `C_d[2]^2`（非 sum/difference）。后续 `b_bw` 和 `h_bw` 也各自独立计算。适用范围：两侧数据分布不对称时。
2. **SUM 分支**（`msesum`, `cersum`）：共同带宽，使用分母 `(C_d_r[2] + C_d_l[2])^2`。与 RD 分支的关键差异是加法而非减法。
3. **RD 分支**（`mserd`, `cerrd`）：共同带宽，使用分母 `(C_d_r[2] - C_d_l[2])^2`。**已实现。**
4. **CER 缩放**（`cerrd`, `certwo`, `cersum`, `cercomb1`, `cercomb2`）：Coverage Error Rate optimal bandwidth。`cer_h = N^(-p/((3+p)*(3+2p)))`，cluster 时 `cer_h = (g_l+g_r)^(-p/((3+p)*(3+2p)))`。`cer_b = 1`。应用于对应 MSE 带宽上。
5. **comb 选择器**：
   - `msecomb1` = `min(mserd, msesum)`（取较保守/小的带宽）
   - `msecomb2` = `median(mserd, msesum, msetwo)`（取三个带宽的中位数）
   - CER 变体同理：`cercomb1` = `msecomb1 * cer_h`，`cercomb2` = `msecomb2 * cer_h`

**Python 实现路径预判：** 将 `_rdbwselect_mserd()` 重构为通用的 `_rdbwselect()` 函数，返回所有计算好的带宽值。按 `bwselect` 参数选择返回对应的 `(h_l, h_r, b_l, b_r)`。TWO 分支需要额外的 per-side `rdrobust_bw` 调用，SUM/RD 分支共享现有的 `C_d_l/C_d_r` 计算。

**复杂度评估：** 中。公式已明确，主要是机械性编码。

### 第二步：R2 Fuzzy RD

**源码依据：** `rdrobust.ado` 的 Mata section（L614-L755）
**核心公式：** Fuzzy RD 将 treatment variable T 作为额外 RHS 列。`D = [y, T]` 或 `D = [y, T, Z1, ..., Zk]`。Sharp RD 的 `s_Y = 1` 在 fuzzy 下变为 Wald 比率向量。

需研究并归档的内容：
1. **无协变量 fuzzy RD**：
   - `tau_Y_cl = factorial(deriv) * beta_p[deriv+1, 1]`（reduced form）
   - `tau_T_cl = factorial(deriv) * beta_p[deriv+1, 2]`（first stage）
   - `tau_cl = tau_Y_cl / tau_T_cl`（Wald estimator, LATE）
   - `s_Y = (1/tau_T_cl, -tau_Y_cl/tau_T_cl^2)`（delta method gradient）
   - Bias correction: `B_F = [tau_Y_cl - tau_Y_bc; tau_T_cl - tau_T_bc]`（2x1 vector）
   - `tau_bc = tau_cl - s_Y' @ B_F`
   - No-covs s_Y used in VCE: `s_Y = (1/tau_T_cl, -tau_Y_cl/tau_T_cl^2)`

2. **含协变量 fuzzy RD**：
   - Covariate-adjusted first stage and reduced form
   - `s_T = (1, -gamma_p[:, 2])`（协变量调整后的 treatment equation weights）
   - `s_Y = (1/tau_T_cl, -tau_Y_cl/tau_T_cl^2, -(1/tau_T_cl)*gamma[:,1] + (tau_Y_cl/tau_T_cl^2)*gamma[:,2])`
   - 此处 s_Y 维度 = 1 + dT + dZ

3. **sharpbw 子选项**：
   - 当 `sharpbw` 指定时：在带宽选择阶段将 `T_l = T_r = 0`（即不传递 treatment 给 `rdrobust_bw()`）
   - 结果是按 sharp RD 计算带宽，但估计阶段仍按 fuzzy RD 计算
   - 使用场景：当研究者想用 sharp RD 带宽做 fuzzy RD 估计时

4. **完美依从（perfect compliance）处理**：
   - 检测：`variance(T_l)==0` 或 `variance(T_r)==0`
   - 响应：将 `T_l = T_r = 0`，打印警告，带宽按 sharp RD 计算
   - `st_local("perf_comp","perf_comp")` 标志

5. **一阶段输出**：Stata 输出 first-stage 结果表，包括 `tau_T_cl`、`se_tau_T_cl`、`tau_T_bc`、`se_tau_T_rb`

**Python 实现路径预判：** 需要在 `RDRobust.fit()` 中新增 `fuzzy` 参数。当 fuzzy 变量名传入时，提取 T 列，将其追加到 D 矩阵（D = [y, T] 或 [y, T, Z]）。WLS 回归的 beta 矩阵维度从 (p+1, 1) 变为 (p+1, 1+dT+dZ)。Wald 比率计算复用现有的 `_wls_poly` 多列能力。

**复杂度评估：** 高。涉及多列 WLS（已部分支持）、Wald 比率 delta method、s 向量维度变化、B_F 2x1 向量。但 `_wls_poly` 已支持多列 y，`_rdrobust_vce_multi` 已支持多维 sandwich。核心风险在于 delta method 梯度 `s_Y` 在含协变量 fuzzy 下的正确性。

### 第三步：R3 Cluster / NNCluster VCE

**源码依据：** `rdrobust_functions.do` 的 `rdrobust_vce()` 函数
**核心机制：**

1. **Cluster VCE（vce(cluster clustvar)）**：
   - 内部 vce_select 在 cluster 时设为 "hc0"（即使用 hc0 residuals）
   - 但 VCE 计算进入 `rdrobust_vce()` 的 cluster 分支
   - 聚类 sandwich：按 cluster 分组，组内求和 score 后外积
   - 小样本修正：`w = ((n-1)/(n-k)) * (g/(g-1))` 其中 g = cluster 数，k = 多项式项数
   - CER 带宽中的 `cer_h` 使用 `(g_l+g_r)` 而非 `N`

2. **NNCluster VCE（vce(nncluster clustvar)）**：
   - 内部 vce_select 设为 "nn"（即使用 NN residuals）
   - VCE 计算仍进入 cluster 分支（同 cluster VCE）
   - 差异仅在于 residuals 的构建方式

3. **Mata rdrobust_vce() 函数分析**：
   - `d == 0`（no covariates, no fuzzy）：简单 `RX' @ diag(res^2) @ RX`
   - `d > 0`：多维 sandwich，`sum_{i,j} s[i]*s[j] * RX' @ diag(res_i * res_j) @ RX`
   - Cluster 分支（`n > 1`，即传入了 cluster 变量）：
     - `d == 0`：组内 `Xr = sum(Xi * ri)`，外积 `sum(Xr @ Xr')`
     - `d > 0`：对每个 (i,j)，组内 `sum(s[l]*ri_l * Xi)`，对 l 求和后外积

4. **当前 Python 的 _rdrobust_vce_multi() 对 cluster 的适配**：
   - 当前 `_rdrobust_vce_multi()` 仅实现了非 cluster 分支
   - 需要新增 cluster 参数和对应的分组逻辑

**Python 实现路径预判：** 需要修改 `_rdrobust_vce_multi()` 以接受可选的 `C` 和 `indC` 参数。当传入 cluster 变量时，使用 groupby 聚合。小样本修正因子应用到整个 M 矩阵。同时需要修改 `_rdrobust_bw()` 以传递 cluster 信息。

**复杂度评估：** 中。公式明确，Mata 源码清晰。但需要与现有的多维 VCE 正确交互，且需要处理 cluster 变量排序和分组。

### 第四步：R4 Weights

**源码依据：** `rdrobust.ado`（L138-L141, L333-L336, L560-L563）
**核心机制：**

1. **权重类型：** 频率权重（frequency weights / analytic weights）
2. **数据筛选：** `drop if mi(weights)` 和 `drop if weights<=0`
3. **权重应用：** 作为内核权重的乘法因子：`w_h_l = fw_l :* w_h_l`
4. **传播路径：** weights 在整个估计过程中与 kernel weights 相乘，因此影响：
   - WLS 的 Gram 矩阵 `R' diag(w) R`
   - 带宽选择（因为 `_rdrobust_bw()` 使用同样的加权）
   - VCE（通过加权 residuals）
   - 有效样本量（`N_h_l` 等变为加权计数）

5. **与 Stata `fweight` / `aweight` 的对应关系：**
   - `rdrobust` 源码未做 aweight 归一化（直接乘）
   - 但 Stata 的 `fweight` 语义是整数频率权重，`aweight` 是分析权重
   - 需要确认 `rdrobust` 实际使用的是哪种权重语义

**Python 实现路径预判：** 在 `RDRobust.fit()` 中新增 `weights` 参数。提取 weights 列，在 missing drop 时包含 weights。在 kernel weight 计算后乘以 weights 向量。需要注意 weights 在两侧带宽不同时的处理（weights 是原始数据上的，kernel weight 是带宽截断后的）。

**复杂度评估：** 低。主要是乘法因子的传播。

### 第五步：R5 Masspoints 处理

**源码依据：** `rdrobust.ado`（L380-L409）和 `rdbwselect.ado`（L318-L354）
**核心机制：**

1. **检测逻辑：** 对 running variable 去重排序，计算 `mass_l = 1 - M_l/N_l`
2. **阈值：** `mass_l >= 0.2` 或 `mass_r >= 0.2` 时判定 mass points 存在
3. **选项行为：**
   - `masspoints(check)`：仅检测并打印警告，不调整
   - `masspoints(adjust)`：检测 + 自动调整
     - 若 `bwcheck==0`：设置 `bwcheck = 10`
     - 用 `M^(-1/5)` 替代 `N^(-1/5)` 计算 pilot 带宽
     - 用 `bw_min = |X_uniq - c|[bwcheck] + 1e-8` 确保带宽覆盖至少 `bwcheck` 个唯一值
   - `masspoints(off)`：不做任何处理（默认值）
   - 注意：Stata 源码中 `masspoints` 默认为 `"adjust"`！

4. **当前 Python 状态：**
   - `_rdbwselect_mserd()` 已内嵌 masspoints 检测和调整逻辑（`bwcheck=10`）
   - 未作为独立参数暴露给用户
   - `RDRobust.__init__()` 未接受 `masspoints` 参数

**Python 实现路径预判：** 将 masspoints 逻辑从带宽选择函数中提取为独立方法。在 `RDRobust` 中新增 `masspoints` 参数（`"off"`, `"check"`, `"adjust"`）。当 `h` 显式提供时，masspoints 调整不适用（因为跳过了带宽选择）。

**复杂度评估：** 低。主要是参数化现有逻辑。

### 第六步：R6 rdplot 伴侣命令

**源码依据：** `rdplot.ado`（需阅读），`rdrobust_illustration.do`（使用示例）
**核心功能（最小可用）：**

1. **数据驱动分箱（data-driven bin selection）：** 
   - IMSE-optimal 分箱数选择（ mimicking variance 和 mimicking bias）
   - 每侧独立计算分箱数和分箱边界
2. **散点图：** 分箱均值 + 全局多项式拟合线（p=4 或 p=5）
3. **多项式阶数选择：** 默认 p=4，可配置
4. **图形元素：** cutoff 竖线、置信区间（可选）

**研究目标：** 确定最小可用的功能集（不要求完全复制 Stata 图形输出，仅需数据驱动分箱 + 局部多项式拟合线的数值计算）。图形渲染由 matplotlib 完成。

**Python 实现路径预判：** 独立于 `RDRobust` 的新函数 `rdplot()`。输入为 data/y/x/c/h 等。输出为分箱统计数据 + matplotlib figure。

**复杂度评估：** 中（应用层，不涉及统计内核变更）。

## Minimum Verification Requirements

研究阶段不要求 Stata 双跑，但需要完成以下验证：

1. **公式验证：** 每个研究方向至少引用 Stata `.ado` 或 `.do` 源码中的具体行号，确认公式转写无误
2. **边界行为预判：** 每个功能至少识别一个已知边界条件（如 fuzzy 下的完美依从、cluster 下单观测 cluster、weights 为 0）
3. **与现有代码的交互预判：** 识别新增参数与现有参数（`h`, `b`, `bwselect`, `covs`, `vce`）的交互/互斥关系
4. **synthetic 样例设计：** 为每个功能设计至少一个 synthetic 测试场景，预登记在 `docs/testing/test-case-catalog.md`
5. **非 golden 测试无回归：** `pytest tests/ -q --ignore=tests/golden/` 继续通过（194 passed）

## Deliverables

| 编号 | 交付物 | 文件路径 |
|------|--------|----------|
| D1 | 带宽选择器族研究档案 | `docs/research/rdrobust-bandwidth-selectors.md`（新增） |
| D2 | Fuzzy RD 研究档案 | `docs/research/rdrobust-fuzzy.md`（新增） |
| D3 | Cluster VCE 研究档案 | `docs/research/rdrobust-cluster-vce.md`（新增） |
| D4 | Weights 研究档案 | `docs/research/rdrobust-weights.md`（新增） |
| D5 | Masspoints 研究档案 | `docs/research/rdrobust-masspoints.md`（新增） |
| D6 | rdplot 研究档案 | `docs/research/rdrobust-rdplot.md`（新增） |
| D7 | 源码映射更新 | `docs/research/rdrobust-source-map.md`（更新） |
| D8 | 支持矩阵更新 | `docs/command-support-matrix/rdrobust.md`（更新 Planned Parameters） |
| D9 | 测试用例预登记 | `docs/testing/test-case-catalog.md`（新增 Wave 8 样例） |
| D10 | 进展报告 | `workspace/current-task/REPORT.md`（追加 Wave 8 Round 1 报告） |

## Success Criteria

- [ ] `docs/research/rdrobust-bandwidth-selectors.md` 记录了 msetwo/msesum/msecomb1-2/cerrd/certwo/cersum/cercomb1-2 的完整公式与实现路径
- [ ] `docs/research/rdrobust-fuzzy.md` 记录了 fuzzy RD 的 Wald 比率公式、sharpbw 机制、完美依从处理、s 向量更新公式、含/不含协变量的完整推导
- [ ] `docs/research/rdrobust-cluster-vce.md` 记录了 cluster 和 nncluster VCE 的 sandwich 构造、小样本修正、与 CER 带宽的交互
- [ ] `docs/research/rdrobust-weights.md` 记录了 weights 的传播路径、缺失值处理、与各子模块的交互
- [ ] `docs/research/rdrobust-masspoints.md` 记录了 masspoints check/adjust/off 的算法逻辑与参数化方案
- [ ] `docs/research/rdrobust-rdplot.md` 记录了 IMSE-optimal 分箱选择与最小可用 rdplot 的实现路径
- [ ] 所有研究档案包含 Stata 源码行号引用和公式转写
- [ ] `docs/testing/test-case-catalog.md` 已预登记 Wave 8 的 >= 12 个 synthetic/real-data 样例
- [ ] `docs/command-support-matrix/rdrobust.md` 的 Planned Parameters 已反映研究结果
- [ ] 主仓非 golden 测试：194 passed, 0 failed
- [ ] 无实现代码修改
- [ ] `INSTRUCTIONS.md` 已切换为 Wave 8 Round 2 入口

---

## 附录 A：六大研究方向的源码速查

| 方向 | 关键 ADO 行号 | 关键 Mata 函数 | 文献依据 |
|------|--------------|---------------|----------|
| R1 带宽选择器 | `rdbwselect.ado` L365-L552 | `rdrobust_bw()` | CCT (2014a) Sec. 3, CCT (2016b) |
| R2 Fuzzy RD | `rdrobust.ado` L106-L123, L313-L322, L614-L618, L642-L678, L717-L755 | `rdrobust_bw()`, `rdrobust_vce()` | CCT (2016a) |
| R3 Cluster VCE | `rdrobust.ado` L325-L331, L627-L631, `rdrobust_functions.do` L214-L267 | `rdrobust_vce()` cluster 分支 | CCT (2014a) Sec. 4.1 |
| R4 Weights | `rdrobust.ado` L138-L141, L333-L336, L560-L563 | 内核权重乘法 | Stata `fweight` 文档 |
| R5 Masspoints | `rdrobust.ado` L380-L409, `rdbwselect.ado` L318-L354 | — | CCT (2014a) Supplemental Appendix |
| R6 rdplot | `rdplot.ado`（待阅读） | — | CCT (2014b) |

## 附录 B：Synthetic 样例预登记清单（>= 12 个）

| case_id | 命令 | 验证线 | 风险焦点 | 状态 |
|---------|------|--------|----------|------|
| `w8_rdrobust_bw_msetwo` | `rdrobust` | synthetic | TWO-sided 带宽（非对称分布） | planned |
| `w8_rdrobust_bw_msesum` | `rdrobust` | synthetic | SUM 共同带宽 | planned |
| `w8_rdrobust_bw_msecomb1` | `rdrobust` | synthetic | comb1 = min(mserd, msesum) | planned |
| `w8_rdrobust_bw_msecomb2` | `rdrobust` | synthetic | comb2 = median(mserd, msesum, msetwo) | planned |
| `w8_rdrobust_bw_cerrd` | `rdrobust` | synthetic | CER 缩放 mserd | planned |
| `w8_rdrobust_bw_cersum` | `rdrobust` | synthetic | CER 缩放 msesum | planned |
| `w8_rdrobust_bw_certwo` | `rdrobust` | synthetic | CER 缩放 msetwo | planned |
| `w8_rdrobust_bw_cercomb1` | `rdrobust` | synthetic | CER 缩放 msecomb1 | planned |
| `w8_rdrobust_bw_cercomb2` | `rdrobust` | synthetic | CER 缩放 msecomb2 | planned |
| `w8_rdrobust_fuzzy_basic` | `rdrobust` | synthetic | 模糊 RD + 显式带宽 + Wald 估计量 | planned |
| `w8_rdrobust_fuzzy_sharpbw` | `rdrobust` | synthetic | 模糊 RD + sharpbw（sharp 带宽 + fuzzy 估计） | planned |
| `w8_rdrobust_fuzzy_covs` | `rdrobust` | synthetic | 模糊 RD + 协变量调整 | planned |
| `w8_rdrobust_cluster` | `rdrobust` | synthetic | cluster VCE | planned |
| `w8_rdrobust_nncluster` | `rdrobust` | synthetic | nncluster VCE（NN residuals + cluster sandwich） | planned |
| `w8_rdrobust_weights` | `rdrobust` | synthetic | 频率权重 | planned |
| `w8_rdrobust_masspoints_adjust` | `rdrobust` | synthetic | masspoints(adjust) 对带宽的影响 | planned |
| `w8_rdrobust_fuzzy_real` | `rdrobust` | real_data | 实际 fuzzy RD 数据集（如 elderly 投票率数据） | planned |
| `w8_rdrobust_bw_real` | `rdrobust` | real_data | 全部带宽选择器在 senate 数据上的对齐 | planned |
