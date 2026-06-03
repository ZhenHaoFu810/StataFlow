# Wave 12 Round 2 任务卡：MAP 迭代吸收内核最小实现

**任务编号：** `wave12-round2-map-implementation`
**日期：** 2026-04-30
**状态：** ready → in_progress
**依赖：** `wave12-round1-research`（已完成）

---

## 背景

当前 `AbsorbingOLS` 使用 LSDV（Least Squares Dummy Variable）方法：将固定效应显式编码为设计矩阵的虚拟变量列。当 `N = 1e6`, `G = 1e4` 时，仅虚拟变量部分就需要 ~80 GB 内存。实际基准测试显示 Python LSDV 在 Dataset A (1M×10K) 上尝试分配 74.5 GiB 后 `MemoryError`。

Round 1 研究档案已确认 MAP（Method of Alternating Projections）迭代算法在数学上与 LSDV 完全等价，且内存占用为 `O(N*k + G)`。Round 2 负责将 MAP 内核落地到 `AbsorbingOLS`。

---

## 目标

1. 在 `AbsorbingOLS` 中添加 `technique` 参数（`"lsdv"` / `"map"`），默认小样本用 LSDV、大样本可切换 MAP。
2. 实现纯 NumPy 的 MAP 固定点迭代（Kaczmarz 顺序投影）+ Aitken Δ² 加速。
3. 小样本数值等价性验证：MAP 与 LSDV 系数/SE 相对误差 < 1e-10。
4. 基准数据集 A/B/C 运行验证：无 OOM，记录时间/内存/迭代次数。
5. VCE 框架兼容性：MAP partial-out 后，robust/cluster/2-way cluster 结果与 LSDV 一致。

---

## 为什么现在做

- Unblocker + 研究轮已完成，MAP 算法路径已确认。
- Wave 12 是 v1.0.0 前唯一剩余 wave，性能瓶颈是结构性阻塞。
- 个体斜率和 Driscoll-Kraay 均依赖 MAP 内核，MAP 必须先落地。

---

## 允许修改范围

- `src/stataflow/estimators/absorbing_ols.py`：添加 `technique` 参数、`_map_partial_out`、`_aitken_accelerate`、修改 `fit()` 分支（LSDV 代码不动）。
- `tests/golden/test_w12_map_*.py`：新增 golden 双跑测试。
- `tests/benchmarks/run_benchmarks.py`：补充 MAP 基准运行。
- `docs/testing/test-case-catalog.md`：登记新样例。
- `docs/research/wave12-map-lsmr.md`：补充实现细节。
- `workspace/current-task/REPORT.md`：记录结果。

---

## 禁止行为

- 禁止删除或修改现有 LSDV 代码。
- 禁止修改 `ResultSchema` 或公共 API 语义。
- 禁止修改 VCE 计算逻辑（MAP 只改变 partial-out 路径）。
- 禁止引入外部依赖（Numba/Cython/CuPy）。
- 禁止跳过小样本数值等价性验证。
- 禁止将个体斜率或 Driscoll-Kraay 混入本轮。
- 禁止修改 `docs/project-charter.md` 或架构原则。

---

## 执行顺序

1. 添加 `technique` 参数和 MAP 路径框架到 `AbsorbingOLS.__init__`。
2. 实现 `_map_partial_out(y, X, factors, max_iter=1000, tol=1e-12)`。
   - Kaczmarz 顺序投影（Guimaraes-Portugal 2010 通用形式）。
   - 支持 1-way / 2-way / G-way FE。
   - 每次迭代对 `g = 2..G` 更新 `Z_g`。
3. 实现 `_aitken_accelerate(Z_history)`（Macleod 1986 方法3）。
   - 每 `accel_freq` 次迭代执行一次。
   - 在残差空间操作，不构造设计矩阵。
4. 修改 `fit()`：根据 `technique` 选择 LSDV 或 MAP partial-out。
   - `technique="lsdv"`：现有代码路径。
   - `technique="map"`：MAP partial-out 得到 `y_star`, `X_star`，再用 OLS 估计 `β`。
   - VCE 计算复用现有代码（基于 `y_star`, `X_star` 的残差）。
5. 小样本 synthetic 测试（N=10K, G=100）。
6. MAP vs LSDV 字段级比对（系数/SE/R²/RMSE）。
7. 1-way / 2-way / 3-way FE 场景验证。
8. Robust / Cluster / 2-way Cluster VCE 兼容性验证。
9. 基准数据集 A/B/C 运行验证。
10. 编写 golden 双跑测试。
11. 更新文档和 REPORT.md。
12. correctness-gatekeeper 审核。

---

## 最小验证要求

| 验证项 | 方法 | 期望结果 |
|--------|------|----------|
| MAP 小样本数值等价性 | N=10K, G=100 合成数据，MAP vs LSDV | 系数/SE/rtol < 1e-10 |
| 1-way FE 等价性 | 单 FE 吸收，OLS + robust + cluster | 全部字段 < 1e-10 |
| 2-way FE 等价性 | 双向 FE 吸收，OLS + robust + cluster | 全部字段 < 1e-10 |
| 3-way FE 等价性 | 三组 FE 吸收（小样本） | 系数/SE < 1e-8 |
| Robust VCE 兼容 | MAP partial-out + robust 三明治 | 与 LSDV robust SE < 1e-6 |
| Cluster VCE 兼容 | MAP partial-out + cluster 三明治 | 与 LSDV cluster SE < 1e-6 |
| 2-way Cluster 兼容 | MAP partial-out + 2-way cluster | 与 LSDV < 1e-4（已知限制） |
| Dataset A 运行 | 1M obs, 10K FE, technique="map" | 成功，无 OOM，内存 < 10 GB |
| Dataset B 运行 | 1M obs, 5K+200 FE, technique="map" | 成功，无 OOM，内存 < 10 GB |
| Dataset C 运行 | 2M obs, 20K+5K FE, technique="map" | 成功，无 OOM，内存 < 16 GB |
| 全量回归测试 | `pytest tests/ --ignore=tests/golden/` | 271 passed, 0 failed |
| Golden 测试通过 | `pytest tests/golden/test_w12_map_*.py` | 全部通过 |

---

## 交付物

1. `src/stataflow/estimators/absorbing_ols.py` — 新增 MAP 内核路径。
2. `tests/golden/test_w12_map_small_sample.py` — 小样本 MAP vs LSDV 双跑 golden 测试。
3. `tests/golden/test_w12_map_benchmark.py` — 基准数据集 MAP 运行 golden 测试。
4. `tests/benchmarks/run_benchmarks.py` — 补充 MAP 运行时间与内存记录。
5. `docs/testing/test-case-catalog.md` — 新增 Wave 12 测试样例登记。
6. `workspace/current-task/REPORT.md` — Round 2 实现轮报告。

---

## 成功标准

- [ ] `AbsorbingOLS` 新增 `technique` 参数，支持 `"lsdv"`（默认小样本）和 `"map"`。
- [ ] 小样本（N=10K, G=100）MAP 与 LSDV 系数/SE 相对误差 < 1e-10。
- [ ] 1-way / 2-way / 3-way FE 场景均通过数值等价性验证。
- [ ] Robust / Cluster / 2-way Cluster VCE 在 MAP 路径下与 LSDV 一致。
- [ ] Dataset A/B/C 使用 `technique="map"` 成功运行，无 OOM。
- [ ] 全量回归测试 271 passed, 0 failed。
- [ ] 新增 golden 测试全部通过。
- [ ] `docs/testing/test-case-catalog.md` 已更新。
- [ ] 研究档案已补充实现细节和收敛日志。
- [ ] correctness-gatekeeper 审核通过。
- [ ] `docs/roadmap.md` Wave 12 状态更新为"Round 2 完成"。
