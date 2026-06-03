# Wave 10 Round 2: IV Completion — Min Implementation (GMM2S + LIML)

## 背景

Wave 10 Round 1（纯研究包）已完成 `ivreghdfe` GMM/LIML/weakiv 分支的源码阅读与研究档案建立，并通过 correctness-gatekeeper 复核（含 4 轮 rework）。研究档案已锁定：
- `docs/research/ivreghdfe-gmm.md` — GMM2S / CUE / LIML / k-class 算法详解、Python 伪代码
- `docs/research/ivreghdfe-weakiv.md` — weakiv 检验公式
- `docs/research/ivreghdfe.md` — Wave 10 研究收束章节
- `docs/testing/test-case-catalog.md` — 8 synthetic + 3 real-data 样例预登记

当前 `ivreghdfe` 实现为 2SLS + FE + robust/cluster VCE + first-stage diagnostics 子集。Round 2 目标为最小实现 GMM2S 和 LIML（含 Fuller / k-class），使 `ivreghdfe` 核心估计器生态完整。

## 目标

在 `IVAbsorbingOLS` 中新增 `estimator` 参数，实现：
1. **GMM2S**（`estimator="gmm2s"`）：两步高效 GMM，含 Hansen J 过度识别检验
2. **LIML**（`estimator="liml"`）：有限信息最大似然，含特征值计算
3. **Fuller**（`estimator="liml", fuller=1`）：Fuller 修正 LIML
4. **k-class**（`estimator="liml", kclass=0.5`）：用户指定 k-class 参数

所有新估计器必须：
- 复用现有 LSDV / FE 吸收框架（`_prepare_data`、collinearity、singleton drop、`df_a`）
- 复用现有 VCE 框架（homoskedastic / robust / cluster / 2-way cluster）
- 通过 synthetic + real-data Stata-Python 双跑验证（系数/SE/t < 1e-6）

## 为什么现在

- Wave 7-9 全部完成，917 测试全部通过，无阻塞返工包。
- Round 1 研究档案已通过 correctness-gatekeeper，公式与源码行号锁定。
- GMM2S 和 LIML 是 IV 生态最高频请求，且实现路径清晰（研究已消除不确定性）。
- weakiv / CUE 依赖 GMM2S/LIML 稳定后实现，故放在 Round 3。

## 允许修改范围

### 允许修改
- `src/stataflow/estimators/iv.py`：
  - 在 `IVAbsorbingOLS` 中新增 `estimator` 参数（`"2sls" | "gmm2s" | "liml"`）
  - 新增 `fuller`、`kclass` 参数（仅当 `estimator="liml"` 时生效）
  - 新增 `_fit_gmm2s()`、`_fit_liml()` 私有方法
  - 在 `fit()` 中根据 `estimator` 分发到对应方法
  - GMM2S 的 Hansen J 统计量存入 `ResultSchema.diagnostics` 或新增字段
  - LIML 的 `lambda`、`k` 参数存入 `ResultSchema.diagnostics`
- `src/stataflow/compat/stata/iv.py`：
  - 更新 `ivreghdfe()` wrapper，透传 `estimator`、`fuller`、`kclass` 参数
- `tests/golden/test_w10_*.py`（新建）：
  - `test_w10_gmm2s_overid.py`
  - `test_w10_gmm2s_cluster.py`
  - `test_w10_liml_weak.py`
  - `test_w10_fuller_adjust.py`
  - `test_w10_kclass_basic.py`
- `tests/test_compat_stata_iv.py`（修改）：
  - 新增 GMM2S / LIML 的 compat 层测试
- `docs/command-support-matrix/ivreghdfe.md`：
  - 更新支持参数列表，标记 `gmm2s`、`liml`、`fuller`、`kclass` 为 `supported`
- `workspace/current-task/REPORT.md`：记录 Round 2 实现结论与验证结果

### 禁止修改
- `ResultSchema` 的公共结构（若需新增字段，必须通过 ADR 并 escalate 至 Codex）
- `IV2SLS` 类（非吸收 IV，不在本轮范围）
- 其他命令族（reghdfe、ppmlhdfe、rdrobust、did_imputation、csdid）
- `docs/project-charter.md`、架构原则、统计等价性标准
- weakiv / CUE / orthog / endogtest / redundant / partial / fwl / HAC 标准误（这些属于 Round 3 或后续 wave）

## 执行顺序（强制）

```
Step 1: 在 IVAbsorbingOLS 中新增 estimator / fuller / kclass 参数，修改 fit() 分发逻辑
  └── Step 2: 实现 _fit_gmm2s()：两步结构、omega 计算、Hansen J
       └── Step 3: 实现 _fit_liml()：特征值、W/W1、k-class、VCE（同方差 + robust/cluster）
            └── Step 4: 更新 compat/stata/iv.py wrapper，透传新参数
                 └── Step 5: 编写 synthetic golden 测试（w10_gmm2s_overid, w10_liml_weak, w10_fuller_adjust, w10_kclass_basic）
                      └── Step 6: 运行 Stata 双跑，验证系数/SE/t < 1e-6
                           └── Step 7: 编写 real-data 测试（w10_card_gmm2s, w10_card_liml）
                                └── Step 8: 运行 Stata 双跑，验证 real-data 对齐
                                     └── Step 9: 更新 command-support-matrix/ivreghdfe.md
                                          └── Step 10: 更新 REPORT.md，记录实现结论与残余风险
```

## 关键实现细节

### GMM2S

根据 `docs/research/ivreghdfe-gmm.md` 第 4.1 节：

1. **第一步**：用现有 2SLS 逻辑跑 IV，得到残差 `e_1s`
2. **计算 omega**：复用现有 VCE 框架的 meat 矩阵计算
   - 同方差：`omega = sigmasq * QZZ`
   - Robust：`omega = 1/N * sum(Z_i' * e_i^2 * Z_i)`
   - Cluster：复用 `_compute_cluster_meat` 或 `compute_multiway_cluster_vce`
3. **第二步**：`W = omega^{-1}`，`beta = [QXZ * W * QXZ']^{-1} QXZ * W * QZy`
4. **VCE**：`V = 1/N * [QXZ * W * QXZ']^{-1}`（高效权重简化形式）
5. **Hansen J**：`J = N * gbar' * W * gbar`，其中 `gbar = Z'e / N`
   - 恰好识别时 J = 0
   - 过度识别时 J ~ chi2(L - K)

**注意**：GMM2S 在恰好识别时（L = K）应与 2SLS 数值等价（系数差异 < 1e-10）。此性质可作为天然验证点。

### LIML

根据 `docs/research/ivreghdfe-gmm.md` 第 2 节：

1. **构造矩阵**：
   - `Y = [y, X_endo]`（N x (1 + K_endo)）
   - `Z = [Z_excl, X_exog]`（N x L）
   - `Z2 = X_exog`（N x K_exog），若无外生量则 `Z2 = None`
2. **计算 W 和 W1**（残差矩阵，未缩放）：
   - `W = Y'Y - Y'Z (Z'Z)^{-1} Z'Y`
   - `W1 = Y'Y - Y'Z2 (Z2'Z2)^{-1} Z2'Y`（若 Z2 为空则 `W1 = Y'Y`）
3. **特征值**：`M = W^{-1/2}`（对称幂），`lambda = min(eigenvalues(M * W1 * M))`
   - Python：`scipy.linalg.eigvalsh(M @ W1 @ M)`
   - 恰好识别时 lambda = 1
4. **k-class 参数**：
   - `kclass` 用户提供：`k = kclass`
   - `fuller > 0`：`k = lambda - fuller / (N - cols(Z))`
   - 默认 LIML：`k = lambda`
5. **估计量**：
   - `Qh = (1-k) * QXX + k * QXZ * QZZ^{-1} * QXZ'`
   - `beta = Qh^{-1} * [(1-k) * QXy + k * QXZ * QZZ^{-1} * QZy]`
6. **VCE**：
   - 同方差：`V = 1/N * sigmasq * Qh^{-1}`
   - Robust/cluster：使用 `ivreghdfe-gmm.md` 第 2.2 节公式
     - `coviv` 为空（默认）：`aux5 = solve(Qh, QXZ)`，`aux9 = solve(QZZ, aux5')`，`V = 1/N * aux9' * omega * aux9`
     - `coviv` 非空：`aux3 = solve(QZZ, QXZ')`，`aux10 = QXZ * aux3`，`aux11 = solve(aux10, aux3')`，`V = 1/N * aux11 * omega * aux11'`
   - 当前 Python 实现暂不支持 `coviv` 选项，默认使用第一种形式

### 与现有框架的集成

- **FE 吸收**：GMM2S / LIML 均在 LSDV 残差化矩阵上运行，与现有 2SLS 完全一致。
- **VCE 计算**：GMM2S 的 omega 和 LIML 的 VCE 均使用现有 `_compute_cluster_meat` / `compute_multiway_cluster_vce` 计算 meat 矩阵。
- **T 矩阵变换**：LIML 的 beta 和 VCE 同样需要通过 T 矩阵映射到 reported 参数空间。
- **小样本修正**：cluster VCE 的 `n_adj`、`g_adj` 与现有 2SLS 一致（`k_eff = k_x_reported + df_a`）。

## 最小验证要求

### Synthetic 双跑

| 测试文件 | Stata 命令 | 验证字段 | 容忍度 |
|----------|-----------|----------|--------|
| `test_w10_gmm2s_overid.py` | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) gmm2s` | beta, se, t, J | < 1e-6 |
| `test_w10_gmm2s_cluster.py` | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) vce(cluster entity_id) gmm2s` | beta, se, t, J | < 1e-6 |
| `test_w10_liml_weak.py` | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) liml` | beta, se, t | < 1e-6 |
| `test_w10_fuller_adjust.py` | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) liml fuller(1)` | beta, se, t, k | < 1e-6 |
| `test_w10_kclass_basic.py` | `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) kclass(0.5)` | beta, se, t, k | < 1e-6 |

### Real-data 双跑

| 测试文件 | Stata 命令 | 验证字段 | 容忍度 |
|----------|-----------|----------|--------|
| `test_w10_card_gmm2s.py` | `ivreghdfe lwage exper expersq (educ = nearc4), absorb(south) gmm2s` | beta, se, t, J | < 1e-5 |
| `test_w10_card_liml.py` | `ivreghdfe lwage exper expersq (educ = nearc4), absorb(south) liml` | beta, se, t | < 1e-5 |

### 回归测试

- 全部现有 917 测试通过（251 non-golden + 666 golden）
- `test_compat_stata_iv.py` 中新增 GMM2S / LIML compat 测试通过

## 成功标准

- [ ] `IVAbsorbingOLS.fit(estimator="gmm2s")` 与 Stata `ivreghdfe ..., gmm2s` 在 synthetic 样例上系数/SE/t 差异 < 1e-6
- [ ] `IVAbsorbingOLS.fit(estimator="liml")` 与 Stata `ivreghdfe ..., liml` 在 synthetic 样例上系数/SE/t 差异 < 1e-6
- [ ] Fuller(1) 和 k-class(0.5) 的 k 参数与 Stata 一致（< 1e-6）
- [ ] GMM2S 在恰好识别时与 2SLS 数值等价（< 1e-10）
- [ ] Hansen J 统计量与 Stata 一致（< 1e-4）
- [ ] Card 真实数据上 GMM2S / LIML 系数/SE 与 Stata 差异 < 1e-5
- [ ] 全部现有 917 测试无回归
- [ ] `docs/command-support-matrix/ivreghdfe.md` 已更新
- [ ] `workspace/current-task/REPORT.md` 已更新

## 交付物

1. `src/stataflow/estimators/iv.py`（新增 GMM2S / LIML 估计器）
2. `src/stataflow/compat/stata/iv.py`（wrapper 参数透传）
3. `tests/golden/test_w10_gmm2s_overid.py`
4. `tests/golden/test_w10_gmm2s_cluster.py`
5. `tests/golden/test_w10_liml_weak.py`
6. `tests/golden/test_w10_fuller_adjust.py`
7. `tests/golden/test_w10_kclass_basic.py`
8. `tests/golden/test_w10_card_gmm2s.py`
9. `tests/golden/test_w10_card_liml.py`
10. `tests/test_compat_stata_iv.py`（新增 compat 测试）
11. `docs/command-support-matrix/ivreghdfe.md`（更新）
12. `workspace/current-task/REPORT.md`（Round 2 结论报告）

## 入口条件

- Wave 10 Round 1 研究档案通过 correctness-gatekeeper
- `ivreghdfe` 2SLS 子集稳定（已有 golden dual-run 证据）
- 全部 917 测试通过

## 出口条件

- 全部 synthetic + real-data 双跑通过
- 全部现有测试无回归
- 命令支持矩阵已更新
- `REPORT.md` 已更新

## 风险记录

| 风险 | 状态 | 说明 | 缓解 |
|------|------|------|------|
| `m_omega` 内部实现未完全阅读 | 已知 | GMM VCE 可能因 meat 矩阵计算细节偏差 | 若偏差 >1e-4，回头补读 `ivreg2` Mata 库；当前复用现有 VCE 框架 |
| LIML 特征值数值稳定性 | 已知 | scipy 与 Stata 特征值结果可能有微小差异 | 设定 rtol=1e-5 容忍度；强制对称化矩阵 |
| GMM2S 小样本修正 | 已知 | Stata 的 `dofminus` / `sdofminus` 调整细节待验证 | 在 cluster VCE 中复用现有 `k_eff = k_x_reported + df_a` 逻辑 |
| T 矩阵变换在 GMM/LIML 下的正确性 | 新 | GMM/LIML 的 VCE 在 full LSDV 空间计算后通过 T 变换到 reported 空间 | 验证 _cons SE 与 slope SE 同时正确 |
| Card 数据缺失 | 低 | `card.dta` 可能不在本地 | 使用 `research/data/public/iv/card.dta` 或从 Stata 示例数据复制 |

## Codex Escalation 触发条件

以下情况必须停止实现并 escalate 至 Codex：
1. GMM2S 或 LIML 的系数/SE 与 Stata 存在系统性偏差（>1e-4）且无法通过调整公式消除
2. 需要新增 `ResultSchema` 字段（如存储 Hansen J 的 p-value、LIML 的 lambda）
3. 公共 API 参数语义需要变更（如 `estimator` 的默认值从隐式 2SLS 变为显式）
4. Real-data 和 synthetic 数据的结论冲突（如 synthetic 通过但 real-data 偏差大）
