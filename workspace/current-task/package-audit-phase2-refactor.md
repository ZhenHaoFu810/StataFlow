# Package: Audit Phase 2 — 代码质量重构

**Phase:** Audit Phase 2 (post Phase 1)
**日期:** 2026-04-30
**状态:** 进行中
**类型:** 纯结构重构 — 不改变数学公式，不改变 API

---

## 背景

Phase 1 审查确认 StataFlow v1.0.0 的数学基础稳固（24 项确认正确，0 P0 阻断问题）。但代码存在显著的结构问题：cluster meat 循环在 6 个文件中重复、multi-way VCE 在 2 个文件中内联、collinearity detection 重复 5 次、2 个 `fit()` 方法超过 400 行。

在 v1.1.0 新功能开发前重构，防止向臃肿方法添加更多功能。

---

## 目标

### 2.1: 消除代码重复
- **2.1a**: 6 个文件中的 cluster meat 循环 → 统一调用 `_vce_utils.compute_cluster_meat`
- **2.1b**: ols.py + ppmlhdfe.py 内联 multi-way VCE → 统一调用 `compute_multiway_cluster_vce`
- **2.1c**: 5 个文件中的 collinearity detection → 提取共享函数
- **2.1d**: T-matrix 逻辑评估 → 只读评估，不强制提取

### 2.2: 拆分臃肿方法
- **2.2a**: `AbsorbingOLS.fit()` (630 行) → `_fit_map()` + `_fit_lsdv()`
- **2.2b**: `IVAbsorbingOLS.fit()` (441 行) → `_fit_2sls()` + `_fit_gmm2s()` + `_fit_liml()`

### 2.3: 死代码清理
- **2.3a**: 移除 LSDV DK VCE 死代码
- **2.3b**: 移除 Aitken 加速（disabled since impl, wrong convergence for 2-way+ FE）
- **2.3c**: 错误处理一致性审查（只读）

---

## 允许修改范围

- `src/stataflow/estimators/_vce_utils.py` — 扩展共享工具
- `src/stataflow/estimators/ols.py` — cluster meat 统一
- `src/stataflow/estimators/fe.py` — cluster meat 统一
- `src/stataflow/estimators/glm.py` — cluster meat 统一 + collinearity
- `src/stataflow/estimators/absorbing_ols.py` — cluster meat + fit split + dead code
- `src/stataflow/estimators/iv.py` — cluster meat + fit split + collinearity
- `src/stataflow/estimators/ppmlhdfe.py` — multi-way VCE 统一

**禁止修改:** any mathematical formula, public API signatures, golden test expectations, rdrobust.py, eventstudyinteract.py

---

## 执行顺序

1. 2.1a (cluster meat) → 2. 2.1b (multi-way VCE) → 3. 2.1c (collinearity) → 4. 2.3a+b (dead code) → 5. 2.2a (AbsorbingOLS split) → 6. 2.2b (IVAbsorbingOLS split) → 7. 2.1d+2.3c (read-only assessments)

每子阶段后运行 `pytest tests/ --ignore=tests/golden/ -q`。

---

## 成功标准

- [ ] Cluster meat 在 100% estimator 中统一调用 `compute_cluster_meat`
- [ ] Multi-way VCE 在 100% estimator 中统一调用 `compute_multiway_cluster_vce`
- [ ] Collinearity detection 统一为共享函数
- [ ] 无超过 200 行的 `fit()` 方法
- [ ] 全量 275 non-golden + 765 golden 测试通过，0 回归
- [ ] 死代码已移除，Aitken 已移除
