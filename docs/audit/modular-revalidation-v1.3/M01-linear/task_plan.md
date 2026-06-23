# M01 Linear 模块独立审查计划 v1.3

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对 StataFlow 的 M01 Linear 模块（`OLS` / `regress()` / `xtreg_fe()` / `areg()` 中的 OLS 相关路径、robust/cluster VCE、aweight、factor variables、sample mask、postestimation）进行完全独立的重新审查，发现数学错误、统计语义偏差、代码缺陷、边界条件错误、结果字段错误和 Stata 17 复现失败。本轮只记录问题，不修改 `src/stataflow/` 产品代码。

**Architecture:** 每个实验都独立设计新的 DGP / 研究规格，独立编写新的 Stata 17 `.do` 文件和新的 Python 审查脚本，现场执行字段级双跑。审查资产保存在 `docs/audit/modular-revalidation-v1.3/M01-linear/evidence/` 下，按 synthetic / real-data / minimal-reproductions 分类。复用项目通用基础设施（`StataRunner`、日志解析、数值比较辅助函数），但不复用旧 golden 测试的经济设计、数据、脚本或 expected values。

**Tech Stack:** Python 3.10+, NumPy, pandas, SciPy, pytest, Stata 17 (local `D:\Software\Stata17\StataMP-64.exe`), project `stataflow` package.

---

## 审查基线

| 项目 | 值 |
|---|---|
| 审查日期 | 2026-06-12 |
| 基线分支 | `dev` |
| 基线 commit SHA | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | (执行时记录) |
| 关键依赖 | (执行时记录) |
| Stata 版本 | 17 |

---

## 模块范围与边界

### 纳入审查的 API

- 核心估计器：`stataflow.OLS`
- Stata 兼容层：`stataflow.compat.stata.regress`
- 共享基础设施在 M01 场景下的使用：
  - `factor_variables.expand_factor_terms` / `get_underlying_vars`
  - `_vce_utils.compute_cluster_meat` / `detect_collinear_columns`
  - `ResultSchema` 字段与不变量
  - `StataRunner`
- Postestimation（M01 范围内）：`OLS.predict`、`OLS.margins`

### 明确不纳入本次 M01 审查的 API

- `FixedEffectsOLS` / `xtreg_fe()` 的 within-FE 专属行为（归 M02）
- `AbsorbingOLS` / `areg()` / `reghdfe()` 的多向吸收行为（归 M03）
- `IV2SLS` / `IVAbsorbingOLS`（归 M04）
- GLM / PPMLHDFE / DID / RD（归 M05-M08）

> 注意：`areg()` 和 `xtreg_fe()` 在 M01 中仅检查它们委托给 `OLS` 的路径（例如 `noconstant`、aweight、cluster 参数传递），不重复检查 FE 估计器本身。

---

## 文件结构

```text
docs/audit/modular-revalidation-v1.3/M01-linear/
  task_plan.md                 # 本文件
  test-design-register.md      # 每个实验的登记信息
  findings.md                  # 发现的问题台账
  progress.md                  # 执行命令、基线结果、时间戳
  summary.md                   # 模块审查总结
  evidence/
    synthetic/                 # 6+ 新 synthetic 双跑证据
    real-data/                 # 2+ 新真实数据双跑证据
    minimal-reproductions/     # 每个 confirmed finding 的最小复现
```

可执行的新测试/脚本资产放在项目既有目录中，并采用 `v1_3_m01` 标识：

- Python 审查脚本：`tests/audit_v1_3/m01_linear/`
- Stata `.do` 文件：`stata/cases/audit_v1_3_m01/`
- Stata 日志：`stata/output/audit_v1_3_m01/`

---

## 审查层次与任务分解

### Task 1: 记录基线环境与依赖

**Files:**
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/progress.md`

- [ ] **Step 1.1: 记录 commit、Python、依赖和 Stata 版本**

Run:
```bash
python --version
python -c "import numpy, pandas, scipy, stataflow; print(numpy.__version__, pandas.__version__, scipy.__version__, stataflow.__version__ if hasattr(stataflow, '__version__') else 'no version')"
git rev-parse HEAD
git status --short
```

Expected: 输出写入 `progress.md` 的 "Environment" 小节。

- [ ] **Step 1.2: 确认 Stata 17 可执行**

Run:
```bash
ls -la "D:/Software/Stata17/StataMP-64.exe"
```

Expected: 文件存在。

---

### Task 2: 支持边界核对

**Files:**
- Read: `docs/command-support-matrix/regress.md`
- Read: `docs/command-support-matrix/areg.md`
- Read: `docs/command-support-matrix/xtreg-fe.md`
- Read: `docs/architecture/public-api.md`
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/progress.md`

- [ ] **Step 2.1: 列出 public API 声明与当前实现参数**

```python
import inspect
from stataflow import OLS
from stataflow.compat.stata import regress, xtreg_fe, areg

print(inspect.signature(OLS.__init__))
print(inspect.signature(OLS.fit))
print(inspect.signature(regress))
```

Expected: 形成支持矩阵表格，记录默认值、已实现/未实现/硬拒绝行为。

- [ ] **Step 2.2: 检查未知参数硬拒绝**

```python
import pandas as pd, numpy as np
df = pd.DataFrame({"y": [1.,2.,3.], "x": [1.,2.,3.]})
try:
    regress(df, y="y", x=["x"], unknown_opt=True)
except ValueError as e:
    print("OK:", e)
```

Expected: 抛出 `ValueError` 或 `NotImplementedError`，不静默忽略。

- [ ] **Step 2.3: 检查已知未实现参数行为**

```python
for opt in ["beta", "eform"]:
    try:
        regress(df, y="y", x=["x"], **{opt: True})
    except NotImplementedError as e:
        print("OK:", e)
```

Expected: 抛出 `NotImplementedError`。

---

### Task 3: 数学与代码走查

**Files:**
- Read: `src/stataflow/estimators/ols.py`（全文件）
- Read: `src/stataflow/compat/stata/linear.py`
- Read: `src/stataflow/compat/stata/factor_variables.py`（M01 相关部分）
- Read: `src/stataflow/estimators/_vce_utils.py`
- Read: `src/stataflow/results/result.py`
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/progress.md`

- [ ] **Step 3.1: 公式清单核对**

对以下公式逐项写出 Stata 17 对应定义，并核对 `ols.py` 实现：

1. OLS 正规方程 / 加权正规方程
2. `df_model`（不含常数）与 `df_resid`
3. RSS / TSS / MSS / R² / adjusted R² / RMSE
4. 同方差 VCE：`σ² (X'X)⁻¹`，`σ² = RSS / df_resid`
5. HC1 robust VCE：`(n/(n-k)) (X'X)⁻¹ X' diag(e²) X (X'X)⁻¹`
6. 加权 robust VCE 的 score 权重阶数
7. One-way cluster VCE：`(N-1)/(N-k) * G/(G-1) * (X'X)⁻¹ Ω_cluster (X'X)⁻¹`
8. Two-way cluster VCE（Cameron-Gelbach-Miller inclusion-exclusion）
9. Wald F 统计量（robust/cluster）
10. `aweight` 归一化：`sum(w*) = N`

Expected: 形成 `progress.md` 中的 "Formula Checklist" 小节，标注任何疑点。

- [ ] **Step 3.2: 关键代码路径审查**

重点检查：
- `_prepare_data` 的 missing screening 是否包含 y、x、cluster、aweight
- 共线性检测 `detect_collinear_columns` 的列顺序与 Stata 是否一致
- 加权 robust VCE 是否使用 `w² * e²` 还是 `w * e²`
- cluster VCE 的 `df_resid` 改为 `G-1` 是否与 Stata 一致
- `predict` 在 newdata 中处理 collinearity drops 的方式
- `margins` 对线性模型是否正确
- 空设计矩阵 / 全缺失 / 单 cluster / 完美拟合的边界

Expected: 记录疑点，用于后续实验设计。

---

### Task 4: 设计 6 个新 synthetic 双跑实验

**Files:**
- Create: `tests/audit_v1_3/m01_linear/test_m01_synthetic.py`
- Create: `stata/cases/audit_v1_3_m01/synthetic_*.do`
- Create: `docs/audit/modular-revalidation-v1.3/M01-linear/test-design-register.md`

每个实验必须：
- 使用新的随机种子（不使用 42/99/123/54321 等旧种子）
- 使用新的数据维度或结构
- 检验与旧测试不同的统计机制
- 现场执行 Stata 17 并保存日志
- 字段级比较：nobs、系数、完整 VCE、SE、t、p、ci、df、R²、RMSE、F、cluster count

#### Experiment S1: 手工可计算小样本

- DGP: n=6, y = 2 + 3*x + ε，x 手工指定，ε 已知
- 目的：验证 OLS 系数、RSS/TSS、R²、F 的解析真值
- Stata: `regress y x`
- Python: `OLS(df, y="y", x=["x"]).fit(vce="ols")`
- 比较字段：系数、SE、RSS、TSS、MSS、R²、adj R²、RMSE、F

#### Experiment S2: 异方差结构已知的中等样本

- DGP: n=500, x ~ N(0,1), ε_i ~ N(0, σ_i²), σ_i = 1 + 2*|x_i|
- 目的：验证 robust VCE 是否捕获异方差，与同方差 SE 比较
- Stata: `regress y x, robust`
- Python: `OLS(...).fit(vce="robust")`
- 比较字段：同方差 SE vs robust SE、VCE 矩阵、Wald F

#### Experiment S3: 组大小高度不均衡的 cluster

- DGP: n=400, 20 个 cluster，其中 19 个组各 1 个观测，1 个大组 381 个观测
- 目的：验证 cluster-robust SE 在小 G、极不均衡组大小下的行为
- Stata: `regress y x, cluster(g)`
- Python: `OLS(...).fit(vce="cluster", cluster="g")`
- 比较字段：cluster count、系数、SE、df_resid

#### Experiment S4: 带零/缺失权重的 aweight

- DGP: n=300, aweight 部分为 0 或缺失
- 目的：验证权重筛选、归一化和加权统计量
- Stata: `regress y x [aweight=w]`
- Python: `OLS(..., weights=..., weight_type="aweight").fit()`
- 比较字段：有效 nobs、sum(w)、系数、SE、R²、RMSE

#### Experiment S5: 近共线缩放实验

- DGP: n=250, x1 ~ N(0,1), x2 = x1 + tiny_noise, x2 缩放 1e6 倍
- 目的：验证共线性检测、列顺序、系数解释稳定性
- Stata: `regress y x1 x2`
- Python: `OLS(df, y="y", x=["x1", "x2"]).fit()`
- 比较字段： dropped variables、保留系数、VCE 条件数

#### Experiment S6: factor 交互项 + 缺失改变 base level

- DGP: n=400, g 为 4 水平分类变量，部分 g=1 的 y/x 缺失，使用 `i.g##c.x`
- 目的：验证 factor base level 在缺失筛选后确定，避免 FVAR-001 类错误
- Stata: `regress y i.g##c.x`
- Python: `regress(df, y="y", x=["i.g##c.x"])`
- 比较字段：系数名称/顺序、系数值、nobs、是否删除常数

---

### Task 5: 设计 2 个新真实数据双跑实验

**Files:**
- Create: `tests/audit_v1_3/m01_linear/test_m01_realdata.py`
- Create: `stata/cases/audit_v1_3_m01/realdata_*.do`
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/test-design-register.md`

#### Experiment R1: 公开面板数据上的典型 OLS + robust

- 数据集：`statsmodels` 内置 `grunfeld` 或 `statewise`（需确认可再分发）
- 研究问题：投资 ~ 市场价值 + 资本存量
- Stata: `regress invest mvalue kstock, robust`
- Python: `regress(df, y="invest", x=["mvalue", "kstock"], vce="robust")`
- 记录：数据来源、下载日期、哈希

#### Experiment R2: 多层聚类 / 困难条件下的 cluster

- 数据集：` wooldridge` / `pdmm` / 公开 CSV（如 World Bank 开放数据）
- 研究问题：y ~ x，按国家和年份两路聚类
- Stata: `regress y x, cluster(country) reg y x, cluster(year) reg y x, cluster(country year)`
- Python: 对应 one-way 和 two-way cluster
- 困难条件：不平衡面板、少量 cluster

> 若无法获取合适的公开两路聚类数据，则改为使用公开横截面数据并人工构造 cluster 变量，但需记录构造方式。

---

### Task 6: 设计 3 个 metamorphic/property tests

**Files:**
- Create: `tests/audit_v1_3/m01_linear/test_m01_properties.py`
- Create: `stata/cases/audit_v1_3_m01/property_*.do`
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/test-design-register.md`

#### Property P1: 行顺序不改变估计

- 对同一数据随机重排行，比较系数、VCE、sample mask
- 同时在 Python 和 Stata 验证

#### Property P2: 无关列不影响结果

- 增加一列不参与估计的变量（含缺失），确认 nobs、系数、SE 不变
- Stata: 直接加入数据但不放入回归
- Python: 同上

#### Property P3: 合法尺度变换产生可推导的系数/VCE 变化

- 将 x 乘以 10，验证 β_x 变为 1/10，SE 变为 1/10，VCE 相应缩放
- 同时在 Python 和 Stata 验证

---

### Task 7: 字段级比较与最小复现

**Files:**
- Create: `tests/audit_v1_3/m01_linear/compare_utils.py`
- Create: `docs/audit/modular-revalidation-v1.3/M01-linear/evidence/minimal-reproductions/*.py`
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/findings.md`

- [ ] **Step 7.1: 实现字段级比较函数**

```python
def compare_result(python_result, stata_dict):
    # 比较 nobs, df, r2, rmse, f, coefficients, full VCE
    ...
```

- [ ] **Step 7.2: 对每个偏差构造最小复现**

对于每个 confirmed finding，提供：
- 最小数据（通常 n ≤ 20）
- Python 代码
- Stata `.do` 文件
- 差异输出

---

### Task 8: 撰写 findings / progress / summary

**Files:**
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/findings.md`
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/progress.md`
- Modify: `docs/audit/modular-revalidation-v1.3/M01-linear/summary.md`

每个 finding 必填字段：
- finding ID（如 `M01-LIN-001`）
- severity（P0/P1/P2/P3）
- evidence status（Confirmed-Stata / Confirmed-Math / Confirmed-Code / Suspected / Coverage Gap）
- affected API
- 最小复现步骤
- Stata 17 结果
- Python 结果
- 数学或代码根因分析
- 用户影响
- 受影响范围
- 是否可能为共享基础设施问题
- 当前是否存在旧 issue
- 建议修复方向（但不实施）

---

### Task 9: 运行现有非 golden 测试，确认审查资产无破坏

**Files:**
- 无新增文件

Run:
```bash
pytest tests/ --ignore=tests/golden/ --ignore=tests/benchmarks/ -q
```

Expected: 原有测试通过数不下降，无新增 failures/errors。

---

## 自审检查清单

- [ ] 6 个 synthetic 实验是否检验不同统计机制？
- [ ] 是否未复用旧 golden 的 DGP、种子、数据、脚本或 expected values？
- [ ] 是否每个实验都有现场执行的 Stata 日志？
- [ ] 是否逐字段比较而不仅是系数？
- [ ] 是否检查了边界条件（空矩阵、全缺失、单 cluster、完美拟合）？
- [ ] 是否区分了产品错误、测试错误、parser 错误、runner 错误？
- [ ] 是否未修改 `src/stataflow/` 产品代码？
- [ ] 是否未推送 GitHub？

---

## 执行方式选择

**Plan complete and saved to `docs/audit/modular-revalidation-v1.3/M01-linear/task_plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch fresh subagents per task block, review between tasks, fast iteration.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
