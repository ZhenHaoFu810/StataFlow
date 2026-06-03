# Wave 12 Benchmark Datasets: LSDV Performance Bottleneck Evidence

**日期：** 2026-04-30
**任务：** `wave12-unblocker-benchmark-datasets`
**运行者：** Claude Code
**状态：** 完成

---

## 1. 目标

合成生成 3 组大规模基准数据集，在 Stata 17 `reghdfe` 与 Python 当前 LSDV 实现上运行相同模型，量化 LSDV 在高维 FE 场景下的性能瓶颈，为 Wave 12 MAP/LSMR 迭代内核的必要性提供实证依据。

## 2. 数据集规格

| 数据集 | N | FE 结构 | FE 级别数 | 聚类 | 缺失值 | 目的 |
|--------|---|---------|-----------|------|--------|------|
| A | 1,000,000 | 单 FE (`firm_id`) | 10,000 | `firm_id` | 无 | 测试单高维 FE 吸收 |
| B | 1,000,000 | 双向 FE (`firm_id` + `year_id`) | 5,000 + 200 | `firm_id` | 无 | 测试双向 FE（应用微观最常见场景） |
| C | 2,000,000 | 双向 FE (`worker_id` + `firm_id`) | 20,000 + 5,000 | `firm_id` | 随机缺失 5% | 测试不平衡面板 + 嵌套聚类 |

数据生成公式：`y = 0.5*x1 + 0.3*x2 + FE_effects + eps`，其中 `x1, x2, eps ~ N(0, 1)`。

## 3. 基准结果

### 3.1 Stata 17 `reghdfe`（迭代算法）

| 数据集 | 观测数 | FE 级别 | 运行时间 | 内存占用 | 结果 |
|--------|--------|---------|----------|----------|------|
| A | 1,000,000 | 10,000 | **2.57s** | ~2 GB | 成功 |
| B | 1,000,000 | 5,000 + 200 | **4.72s** | ~3 GB | 成功 |
| C | 1,900,123* | 20,000 + 5,000 | **10.16s** | ~5 GB | 成功 |

\* Dataset C 经缺失值剔除后剩余 1,900,123 条观测。

Stata `reghdfe` 在所有测试规模下均秒级完成，表现出迭代 HDFE 算法对高维固定效应的良好扩展性。

### 3.2 Python LSDV（当前实现）

| 数据集 | 观测数 | FE 级别 | 设计矩阵维度 | 所需内存 | 结果 |
|--------|--------|---------|--------------|----------|------|
| A | 1,000,000 | 10,000 | 1M × 10,002 | **74.5 GiB** | `MemoryError` |
| B | 1,000,000 | 5,000 + 200 | 1M × 5,201 | **38.8 GiB** | `MemoryError` |
| C | 1,900,123 | 20,000 + 5,000 | 1.9M × 25,001 | **283 GiB** | `MemoryError` |

Python LSDV 在**所有三组数据集上均因内存不足失败**。失败点发生在 `_prepare_data` 中构造完整设计矩阵 `X_full = np.column_stack([X, D])` 时，其中 `D` 为 FE 虚拟变量矩阵。

## 4. 关键发现

### 4.1 LSDV 的内存瓶颈是硬性的

LSDV（Least Squares Dummy Variables）需要将固定效应显式编码为设计矩阵中的虚拟变量列。对于 N 个观测和 G 个 FE 级别，设计矩阵大小为 `N × (k + G)`。

**理论内存需求（pre-drop，完整数据集）：**
- Dataset A (`G = 10,000`, `N = 1,000,000`): `1e6 × 1e4 × 8 bytes ≈ 80 GB`
- Dataset C (`G = 25,000`, `N = 2,000,000`): `2e6 × 2.5e4 × 8 bytes ≈ 400 GB`

**实际内存分配失败（empirical，post-drop）：**
- Dataset A: 尝试分配 **74.5 GiB** (`1,000,000 × 10,002 × 8 bytes`)
- Dataset B: 尝试分配 **38.8 GiB** (`1,000,000 × 5,201 × 8 bytes`)
- Dataset C: 尝试分配 **283 GiB** (`1,900,123 × 19,999 × 8 bytes`)

Dataset C 的实际失败规模小于理论值，因为缺失值剔除后观测数降至 1.9M，且 Python 在构造矩阵时只生成非参考级别的虚拟变量（`G - 1` 列）。即便如此，**283 GiB 仍远超标准工作站的内存容量**。

### 4.2 迭代算法的优势

Stata `reghdfe` 使用迭代 demeaning / MAP（Method of Alternating Projections）/ LSMR（Least Squares Minimal Residual）等算法，**不需要显式构造虚拟变量矩阵**。其内存占用主要取决于数据矩阵本身（`N × k`）和 FE 级别的索引结构（`O(G)`），因此可以在线性时间内、常数额外内存下完成估计。

### 4.3 性能差距量化

| 指标 | Stata reghdfe | Python LSDV | 差距 |
|------|---------------|-------------|------|
| Dataset A | 2.57s | ∞ (OOM) | **LSDV 不可行** |
| Dataset B | 4.72s | ∞ (OOM) | **LSDV 不可行** |
| Dataset C | 10.16s | ∞ (OOM) | **LSDV 不可行** |

## 5. 结论

当前 Python LSDV 实现在 `>1e6` 观测、`>1e4` FE 级别的场景下**完全不可行**。这是 Wave 12 引入 MAP/LSMR 迭代吸收内核的核心动机。

Wave 12 的目标应明确为：
1. 实现不依赖显式虚拟变量矩阵的迭代吸收内核
2. 确保迭代内核在标准测试集（Dataset A/B/C）上与 LSDV 小样本结果字段级一致
3. 在 Dataset A/B/C 规模下实现可接受的运行时间和内存占用

## 6. 文件清单

- `tests/benchmarks/generate_datasets.py` — 合成数据生成脚本
- `tests/benchmarks/data/benchmark_*.dta` — 3 组基准数据集
- `tests/benchmarks/run_benchmarks.py` — Stata/Python 双跑基准脚本
- `tests/benchmarks/results/*.json` — 基准结果（时间、系数、错误信息）
- `stata/cases/benchmark_reghdfe.do` — Stata 基准 do-file
