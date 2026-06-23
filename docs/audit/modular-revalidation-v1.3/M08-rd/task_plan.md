# M08 RD 模块独立审查计划 v1.3

## 执行基线

- **模块**: M08 Regression Discontinuity (RD)
- **审查日期**: 2026-06-13
- **基线 commit**: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- **分支**: `dev` (当前工作树，未修改 `src/stataflow/`)
- **Python**: 3.11.7
- **NumPy**: 1.26.4
- **pandas**: 3.0.2
- **SciPy**: 1.17.1
- **statsmodels**: 0.14.6
- **Stata 17 MP**: `D:\Software\Stata17\StataMP-64.exe`
- **约束**: 本轮为审查轮，禁止修改 `src/stataflow/` 产品代码

## 审查对象

- 核心估计器: `stataflow.estimators.rdrobust.RDRobust`
- Stata 兼容层: `stataflow.compat.stata.rdrobust.rdrobust()`
- 伴随绘图命令: `stataflow.compat.stata.rdplot.rdplot()`
- 共享基础设施在 RD 场景下的使用: `ResultSchema`、`StataRunner`、样本筛选、缺失值处理

## 关键阅读文件

1. `docs/audit/modular-revalidation-v1.3/MASTER_AUDIT_BRIEF.md` — 本轮审查总纲
2. `src/stataflow/estimators/rdrobust.py` — RDRobust 核心实现
3. `src/stataflow/estimators/rdplot.py` — RDPlot 核心实现
4. `src/stataflow/compat/stata/rdrobust.py` — rdrobust() wrapper
5. `src/stataflow/compat/stata/rdplot.py` — rdplot() wrapper
6. `src/stataflow/results/result.py` — ResultSchema 字段契约
7. `tests/test_rdrobust.py` — 现有 RD 测试（仅用于覆盖地图，不复制 DGP/seed）
8. `tests/golden/test_w8_*rdrobust*.py` / `tests/golden/test_v2_c1_8_rd_senate_real.py` — 旧 golden（仅用于覆盖地图）
9. `tests/audit_v1_3/m07_did_event_study/m07_audit_utils.py` — 执行/日志/证据工具模板

## 审查问题 (aligned with MASTER_AUDIT_BRIEF M08)

1. **局部多项式设计矩阵**
   - 左右侧设计矩阵的构造、`p` / `q` 阶数、截距项位置是否与 Stata `rdrobust` 一致？
   - `deriv=0` 时系数提取是否正确？

2. **核函数与权重**
   - triangular / epanechnikov / uniform 核权重公式是否对齐 Stata？
   - 带宽 `h` / `b` 为标量、元组、或自动选择时的解析路径是否正确？

3. **估计量 (sharp / fuzzy)**
   - sharp RD 的 conventional / bias-corrected / robust 估计量是否一致？
   - fuzzy RD 的 Wald 比率、delta-method 偏差修正是否实现且正确？

4. **带宽选择**
   - `bwselect` 九种选择器 (`mserd`, `msesum`, `msetwo`, `msecomb1`, `msecomb2`, `cerrd`, `cersum`, `certwo`, `cercomb1`, `cercomb2`) 是否全部可用？
   - 质点 (mass points) 调整、`bwcheck`、`scaleregul` 是否生效？

5. **方差估计**
   - `vce="nn"` / `"hc0"` / `"cluster"` / `"nncluster"` 的实现与 Stata 的 conventional / robust SE 对应关系？
   - cluster VCE 的小样本修正、聚类层级计数是否一致？

6. **协变量调整 (`covs`)**
   - 局部 FWL / 投影后的 `s` 向量构造是否正确？
   - 存在共线协变量时 `covs_drop` 的行为？

7. **权重 (`weights`)**
   - 频数权重的筛选、归一化、与缺失值组合处理是否对齐 Stata？

8. **质点与稀疏数据**
   - `masspoints` 对 pilot 带宽和 `bwcheck` 的影响？
   - cutoff 附近样本稀疏或单侧支撑不足时的行为？

9. **rdplot 伴随命令**
   - `binselect="esmv"` / `"qsmv"` 的 bin 数量是否与 Stata 一致？
   - `nbins`、多项式拟合、协变量调整的行为？

10. **样本筛选与 ResultSchema**
    - 缺失值、`weights <= 0`、cutoff 不在 range 内的报错与样本 mask 是否一致？
    - `_rd_extras` 字段 (`N_l`, `N_r`, `N_h_l`, `h_l`, `b_l`, `tau_cl`, `se_tau_cl`, `se_tau_rb` 等) 是否完整？

## 交付物清单

- [x] `docs/audit/modular-revalidation-v1.3/M08-rd/task_plan.md`
- [x] `docs/audit/modular-revalidation-v1.3/M08-rd/test-design-register.md`
- [x] `docs/audit/modular-revalidation-v1.3/M08-rd/findings.md`
- [x] `docs/audit/modular-revalidation-v1.3/M08-rd/progress.md`
- [x] `docs/audit/modular-revalidation-v1.3/M08-rd/summary.md`
- [x] `docs/audit/modular-revalidation-v1.3/M08-rd/evidence/synthetic/*`
- [x] `docs/audit/modular-revalidation-v1.3/M08-rd/evidence/real-data/*`
- [x] `docs/audit/modular-revalidation-v1.3/M08-rd/evidence/property/*`
- [x] `tests/audit_v1_3/m08_rd/m08_audit_utils.py` (RD-specific Stata builder/parser/comparison/evidence)
- [x] `tests/audit_v1_3/m08_rd/test_m08_synthetic.py` (≥6 new synthetic dual-run tests)
- [x] `tests/audit_v1_3/m08_rd/test_m08_realdata.py` (≥2 new real-data dual-run tests)
- [x] `tests/audit_v1_3/m08_rd/test_m08_property.py` (≥3 metamorphic/property tests)
- [x] `tests/audit_v1_3/m08_rd/repro_m08_rd_findings.py`
- [x] `stata/cases/audit_v1_3_m08/*.dta` 与 `stata/output/audit_v1_3_m08/*.log`
- [x] `workspace/current-task/REPORT.md` 追加 M08 审查报告
- [x] 运行 `pytest tests/audit_v1_3/m08_rd -v` 并记录结果
- [x] 运行 `pytest tests/ --ignore=tests/golden/ --ignore=tests/benchmarks/` 确认无回归
