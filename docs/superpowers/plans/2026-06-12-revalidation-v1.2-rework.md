# Revalidation v1.2 返工实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 关闭 `docs/audit/revalidation-v1.2/REWORK_TASKS.md` 全部 P1/P2 项，使干净 checkout 通过非 golden 测试、完整 golden 双跑验收，并满足 `<1e-6` 字段级复现标准。

**Architecture：** 按子系统隔离修复（factor variables、result schema、DID/CSDID、HDFE/VCE、RD、交付卫生），每项任务先写失败回归测试、再最小修改实现、再验证；保持 Stata 17 为唯一 ground truth。

**Tech Stack：** Python 3.10+, NumPy, pandas, SciPy, pytest, local Stata 17 via `StataRunner`。

---

## Phase 0: 基线止血

### Task 0.1: 确认当前 HDFE 回归范围

**Files:**
- Modify: `src/stataflow/estimators/absorbing_ols.py`
- Test: `tests/golden/test_p3_reghdfe_cluster.py`, `tests/golden/test_p3_reghdfe_real_panel.py`, `tests/golden/test_w7_reghdfe_2way_cluster.py`, `tests/golden/test_w7_reghdfe_2way_cluster_real.py`, `tests/golden/test_w12_map_small_sample.py`

- [ ] **Step 1: 运行最小回归集记录当前失败**

Run:
```powershell
pytest tests/golden/test_p3_reghdfe_cluster.py tests/golden/test_p3_reghdfe_real_panel.py tests/golden/test_w7_reghdfe_2way_cluster.py tests/golden/test_w7_reghdfe_2way_cluster_real.py tests/golden/test_w12_map_small_sample.py -v --no-header
```
Expected: 捕获所有失败字段（r2_adj / rmse / _cons SE / slope SE）。

- [ ] **Step 2: 回滚/修正不安全的 rmse_df 改动**

将 `absorbing_ols.py` 中 LSDV 与 MAP 路径的 `rmse_df` 恢复为与 Stata `used_df_r = N - df_a - df_m - df_a_nested` 一致的定义，禁止再用单一 `n - df_model - df_a - cons_penalty` 公式覆盖 reghdfe 2-way cluster 路径。具体实现需分别处理：
- areg 模式 + cluster 嵌套 FE：`used_df_r = N - k_x - 1`（FE 视为冗余）
- reghdfe 模式：`used_df_r = N - df_a - df_m - df_a_nested`（与 Stata 源码一致）
- 非 cluster OLS/robust：维持现有 `N - k_full` 或等效表达

- [ ] **Step 3: 重新运行最小回归集**

Run 同上命令。Expected: 上述 4 个 reghdfe cluster 文件全部 pass，`test_w12_map_small_sample.py` 同时 pass。

- [ ] **Step 4: Commit 基线修复**

```bash
git add src/stataflow/estimators/absorbing_ols.py
git commit -m "fix(hdfe): align rmse_df with Stata used_df_r for reghdfe/areg cluster"
```

---

## Phase 1: Factor Variables (P1-1 / P1-2)

### Task 1.1: FVAR-001 交互项底层变量提取

**Files:**
- Modify: `src/stataflow/compat/stata/factor_variables.py`
- Modify: `src/stataflow/compat/stata/linear.py:59`（screen_vars 构造）
- Test: `tests/test_factor_variables.py`, `tests/golden/test_a2_factor_reghdfe_bare.py`, `tests/golden/test_a2_factor_reghdfe_basic.py`, `tests/golden/test_a2_factor_reghdfe_mixed.py`

- [ ] **Step 1: 添加底层变量提取接口**

在 `factor_variables.py` 实现 `get_underlying_vars(term: str) -> list[str]`，支持：
- `i.g` -> `['g']`
- `c.x` -> `['x']`
- `i.g##c.x` -> `['g', 'x']`
- `i.g#i.h` -> `['g', 'h']`
- `i(1 2).g` -> `['g']`

- [ ] **Step 2: wrapper 使用真实底层变量进行 sample screening**

修改 `linear.py` 中 `screen_vars` 构造逻辑，调用 `get_underlying_vars` 展开 `x` 列表中的 factor 表达式，不再把整串表达式加入 screening。

- [ ] **Step 3: 添加缺失连续交互变量改变 categorical base 的回归测试**

新增测试：数据构造 `g=1` 的行令 `x` 缺失，Python 与 Stata 均应以 `g=2` 为 base，返回 `3.g`、`x`、`3.g#c.x`（无 `2.g`）。

- [ ] **Step 4: 运行 factor 相关测试**

Run:
```powershell
pytest tests/test_factor_variables.py tests/golden/test_a2_factor_reghdfe_*.py -v
```
Expected: PASS，且 Stata 双跑一致。

### Task 1.2: FVAR-002 字符串 factor 拒绝

**Files:**
- Modify: `src/stataflow/compat/stata/factor_variables.py:206`
- Test: `tests/test_factor_variables.py:506`

- [ ] **Step 1: 拒绝所有字符串变量作为 factor**

在 `expand_factor_terms` 中检测 term 对应列的 dtype；若为 object/string/category with string，对 `i.strvar`、`ib#.strvar`、`o#.strvar` 统一抛出 `ValueError("string variables may not be used as factor variables (Stata r(109))")`。

- [ ] **Step 2: 替换旧测试为负测试**

删除“string without explicit base allowed”的通过测试，改为断言 `i.strvar` 触发 `ValueError` 并检查错误信息包含 `r(109)`。

- [ ] **Step 3: 运行测试**

Run: `pytest tests/test_factor_variables.py -v -k string`
Expected: PASS。

---

## Phase 2: Result Schema (P1-3)

### Task 2.1: SCHEMA-001 invariant 校验

**Files:**
- Modify: `src/stataflow/results/result.py:125-160`
- Test: `tests/test_result_schema.py`

- [ ] **Step 1: 增强 `ResultSchema.validate()`**

在 `validate()` 中加入以下硬校验，失败时抛出 `ValueError`：
- `len(coefficients) == len(row_names)`
- VCE 为方阵：`vce.shape[0] == vce.shape[1]`
- VCE 每行长度一致（非 ragged）
- `coefficients` 名称顺序与 `row_names` 完全一致（逐位比较，非集合）
- `len(sample_mask) == n_input_rows`
- `sum(sample_mask) == nobs`（mask 非空时）

- [ ] **Step 2: 在 `from_dict()` / `from_json()` 调用校验**

两个工厂方法构造对象后立即调用 `validate()`，失败抛出异常。

- [ ] **Step 3: 补充先失败再通过的单元测试**

新增 `test_result_schema_validate`，覆盖：
- coefficients 与 row_names 长度不一致
- ragged VCE `[[1,0],[0]]`
- 名称集合相同但顺序不同
- sample mask 长度错误
- `sum(mask) != nobs`

- [ ] **Step 4: 运行测试**

Run: `pytest tests/test_result_schema.py -v`
Expected: PASS。

---

## Phase 3: DID Sample Contract (P1-4 / P1-7)

### Task 3.1: DID-004 sample mask 与 nobs 一致

**Files:**
- Modify: `src/stataflow/estimators/did_imputation.py:130`, `:420-424`
- Test: `tests/test_compat_stata_did.py`, `tests/golden/test_w4_did_imputation_real_ezunem.py`

- [ ] **Step 1: 将最终 effective_sample_mask 映射回原始行**

在 `did_imputation.py` 中，把 `autosample`、window、minn 等筛选后的 `effective_sample_mask`（筛选后 DataFrame 长度）通过保留的 `_stataflow_row_id` 映射回 `n_input_rows` 长度的布尔数组，写入 `ResultSchema.sample_mask`。

- [ ] **Step 2: 添加回归测试**

构造 `n_input_rows=5`、`autosample` 剔除 1 行的最小案例，断言 `sum(sample_mask) == nobs == 4`。

- [ ] **Step 3: 运行测试**

Run: `pytest tests/test_compat_stata_did.py tests/golden/test_w4_did_imputation_real_ezunem.py -v`
Expected: PASS。

### Task 3.2: DID-001 first_treat 原生语义

**Files:**
- Modify: `src/stataflow/estimators/did_imputation.py:107-139`
- Modify: `src/stataflow/compat/stata/did.py`
- Test: `tests/test_compat_stata_did.py`

- [ ] **Step 1: 明确语义**

与 Stata `did_imputation` 原生语义对齐：
- `first_treat` 缺失（NaN/None）：从估计样本删除
- `first_treat == 0` 或负值：视为 never-treated（对照组）
- 禁止在 Stata `.do` 中临时把 `-1` 替换为 missing，Python 与 Stata 使用同一数据

- [ ] **Step 2: 在 compat wrapper 显式转换**

如需把用户输入的某些编码转换为 never-treated，必须在 `did.py` 文档化转换规则，而不是在 estimator 内部静默解释。

- [ ] **Step 3: 覆盖 time 含 0/负值的面板测试**

新增测试：time 包含 -2,-1,0,1,2，first_treat 含 0 与缺失，验证对照组/处理组划分正确。

- [ ] **Step 4: 运行测试**

Run: `pytest tests/test_compat_stata_did.py -v -k first_treat`
Expected: PASS。

---

## Phase 4: CSDID Cluster (P1-6)

### Task 4.1: CSDID custom cluster 缺失值与一致性

**Files:**
- Modify: `src/stataflow/estimators/csdid.py:116`, `:406`
- Test: `tests/test_compat_stata_did.py`, `tests/golden/test_w4_csdid_real_ezunem.py`, `tests/golden/test_w9_csdid_dr_real_ezunem.py`

- [ ] **Step 1: cluster 变量参与 missing screening**

在初始 `dropna()` 中加入用户传入的 cluster 变量，确保 cluster 缺失的行被剔除。

- [ ] **Step 2: 校验 cluster 在 unit 内一致**

在分组前检查每个 `unit` 内的 cluster 值是否唯一；若不一致，抛出 `ValueError("cluster variable varies within unit")`。

- [ ] **Step 3: 确保点估计、IF、nobs、sample mask、cluster count 来自同一估计样本**

`nobs` 与 `sample_mask` 使用同一样本；cluster count 从最终样本计算。

- [ ] **Step 4: 新增缺失 cluster 与 varying cluster 测试**

新增两个单元测试：
- cluster 缺失 -> 删除对应行，nobs 与 mask 一致
- unit 内 cluster 变化 -> 明确报错

- [ ] **Step 5: 运行测试**

Run:
```powershell
pytest tests/test_compat_stata_did.py tests/golden/test_w4_csdid_real_ezunem.py tests/golden/test_w9_csdid_dr_real_ezunem.py -v
```
Expected: PASS。

---

## Phase 5: EVID-001 — Reproducible DID Golden Fixtures (P1-5)

### Task 5.1: DID real-data tests 动态生成 Stata 证据

**Files:**
- Modify: `.gitignore:35`
- Modify: `tests/golden/test_w4_csdid_real_ezunem.py`
- Modify: `tests/golden/test_w4_did_imputation_real_ezunem.py`
- Modify: `tests/golden/test_w4_eventstudyinteract_real_ezunem.py`
- Modify: `tests/golden/test_w9_csdid_dr_real_ezunem.py`

- [ ] **Step 1: 测试内调用 StataRunner 动态生成 log**

将四个测试从读取 `stata/output/*.log` 改为：
1. 调用 `StataRunner.run_do_file()` 生成 `.log`；
2. 使用 `parse_stata_log` 提取结果；
3. 与 Python 结果比较。

- [ ] **Step 2: 把稳定 golden artifact 移入受 Git 管理目录**

若保留静态 fixture，放入 `tests/golden/fixtures/`（已受 Git 管理），而不是 `stata/output/`。

- [ ] **Step 3: 删除对 `stata/output/*.log` 的依赖**

更新 `.gitignore` 不再豁免这些测试依赖的特定文件，或直接删除静态读取路径。

- [ ] **Step 4: 在干净 worktree 验证**

Run:
```powershell
# 删除 stata/output/*.log 后
pytest tests/golden/test_w4_csdid_real_ezunem.py tests/golden/test_w4_did_imputation_real_ezunem.py tests/golden/test_w4_eventstudyinteract_real_ezunem.py tests/golden/test_w9_csdid_dr_real_ezunem.py -v
```
Expected: PASS。

---

## Phase 6: HDFE / VCE Alignment (P1-8 / P1-9)

### Task 6.1: 重新推导并验证 df_a / rmse_df / adjusted R²

**Files:**
- Modify: `src/stataflow/estimators/absorbing_ols.py`
- Test: `tests/golden/test_p3_reghdfe_cluster.py`, `tests/golden/test_p3_reghdfe_real_panel.py`, `tests/golden/test_w7_reghdfe_2way_cluster.py`, `tests/golden/test_w7_reghdfe_2way_cluster_real.py`, `tests/golden/test_w12_map_small_sample.py`

- [ ] **Step 1: 按 Stata 源码为 areg/reghdfe 分别实现 rmse_df**

- areg：
  - 无 cluster：`N - k_full`（等价于 `N - k_x - df_a - 1`）
  - cluster 嵌套 FE：`N - k_x - 1`
- reghdfe：`N - df_a - df_m - df_a_nested`（`df_a_nested` 为嵌套在 cluster 中的 FE levels 数）

- [ ] **Step 2: 复核 `_cluster_k_eff()` 的 nested adjustment**

确保 2-way cluster small-sample 调整使用 `k_x + df_a + nested_adj`，与 Stata `reghdfe` 一致；不恢复旧的 `k_full - nested_params` 错误公式。

- [ ] **Step 3: 运行回归集**

Run:
```powershell
pytest tests/golden/test_p3_reghdfe_cluster.py tests/golden/test_p3_reghdfe_real_panel.py tests/golden/test_w7_reghdfe_2way_cluster.py tests/golden/test_w7_reghdfe_2way_cluster_real.py tests/golden/test_w12_map_small_sample.py -v
```
Expected: 所有 adjusted R²、RMSE、SE 满足 `<1e-6`。

### Task 6.2: VCE-002 / VCE-003 / VCE-004

**Files:**
- Modify: `src/stataflow/estimators/absorbing_ols.py`
- Test: 对应 golden tests

- [ ] **Step 1: 对表 Stata 明确偏差来源**

若修复需要重构 MAP 常数项方差算法（稀疏/分块 LSDV 协方差）或 2-way cluster PSD 修复逻辑，评估工作量；若无法在合理时间内关闭，按治理流程改为 Open/Known limitation 并写入 ADR，**不能标 Fixed**。

- [ ] **Step 2: 不得使用宽松容差**

所有关闭项必须满足 `<1e-6`；未关闭项保持 Open，禁止把 0.5%/3%/20% 容差写入测试。

---

## Phase 7: RD-002 (P1-8)

### Task 7.1: RD qsmv 残差处理

**Files:**
- Modify: `src/stataflow/estimators/rdplot.py`
- Modify: `tests/test_rdrobust.py`
- Modify: `docs/audit/revalidation-v1.2/REMEDIATION_REPORT.md`

- [ ] **Step 1: 确认 56 vs 59 的根本原因**

判断是数值算法差异（Cholesky/pinv/qr）还是 Stata 版本实现差异；记录 R 与 Stata 的偏差证据。

- [ ] **Step 2: 若无法匹配，状态改回 Open/Known limitation**

按项目标准，`<1e-6` 不适用于整数 bin 计数，但若相对偏差约 5% 不能关闭，则：
- 测试断言改为 match Stata 56，允许当前实现 fail 并 xfail/mark as known limitation；或
- 把 RD-002 状态从 Fixed 改回 Open，并写入 ADR。

- [ ] **Step 3: 禁止把 5% 偏差标为 Fixed**

更新 `REMEDIATION_REPORT.md` 中的 RD-002 状态与风险说明。

---

## Phase 8: 交付卫生 (P2-2)

### Task 8.1: 清理临时文件与正式化资产

**Files:**
- Delete: `Rplots.pdf`, `golden_output.txt`, `golden_full_output.txt`, `vce005_output.txt`
- Delete: `dist_tmp/` 中临时 wheel（保留最终 `dist_acceptance/` 产物）
- Delete: 未追踪的 `stata/cases/*probe*.py`
- Modify: `.gitignore`
- Modify: `docs/audit/revalidation-v1.2/REMEDIATION_REPORT.md`

- [ ] **Step 1: 清理纯临时输出和构建目录**

```bash
git rm --cached Rplots.pdf golden_output.txt golden_full_output.txt vce005_output.txt
rm -rf dist_tmp/*probe*.py
# 保留正式测试、脚本和文档，将其 git add
```

- [ ] **Step 2: 决定验证脚本与新增 golden tests 归属**

将应保留的测试、脚本纳入 Git；临时诊断文件纳入 `.gitignore` 或删除。

- [ ] **Step 3: 更新 REMEDIATION_REPORT.md**

- 仅把真正满足 `<1e-6` 或通过验收的项目标为 Fixed
- Open 项保留 Open 并说明原因与风险
- 不将仍有超容差或不可重现证据的项目标为 Fixed

---

## Phase 9: 最终验收

### Task 9.1: 干净工作树完整回归

**Files:** 全部修改文件

- [ ] **Step 1: 在干净工作树/worktree 执行**

```powershell
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/benchmarks/
pytest tests/golden/ -v
python -m compileall -q src/stataflow
python -m pip wheel . --no-deps -w dist_acceptance
git diff --check
```

- [ ] **Step 2: 逐项运行最小复现并记录**

对每项 P1 关闭的问题，记录 Stata 17 命令、输出和最大相对误差。

- [ ] **Step 3: 更新 `docs/audit/revalidation-v1.2/REMEDIATION_REPORT.md` 最终状态**

- [ ] **Step 4: Commit 并关闭任务**

```bash
git add -A
git commit -m "fix(revalidation-v1.2): close all rework tasks"
```

---

## 验收标准

- 非 golden 测试：`pytest tests/ -v --ignore=tests/golden/ --ignore=tests/benchmarks/` 全部 PASS
- 完整 golden：`pytest tests/golden/ -v` 全部 PASS（或仅有已审批的 Open known limitation xfail）
- 字段级比较：系数、标准误、t/z、R²、RMSE、F、自由度相对误差 `<1e-6`
- 干净 checkout 可复现：删除 `stata/output/*.log` 后测试仍能自行生成证据并通过
- `python -m compileall -q src/stataflow` 通过
- wheel 构建通过
- `git diff --check` 无 whitespace 错误
