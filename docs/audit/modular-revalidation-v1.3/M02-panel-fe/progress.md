# M02 Panel / FE 审查进度 progress.md

## 当前状态

- **模块**: M02 Panel / FE
- **审查轮次**: modular-revalidation-v1.3
- **开始时间**: 2026-06-13
- **完成时间**: 2026-06-13
- **审查者**: Claude Code Agent
- **基线 commit**: `2c7db1ca095e03d29c471e8d523fdaa943306174`

## 已完成工作

| # | 任务 | 状态 | 说明 |
|---|---|---|---|
| 1 | 记录基线 commit、Python、Stata 版本 | 完成 | 见 `task_plan.md` 与 `summary.md` |
| 2 | 阅读 public API、support matrix、实现文件 | 完成 | 重点阅读 `src/stataflow/estimators/fe.py`、`src/stataflow/compat/stata/linear.py` |
| 3 | 建立功能清单与数学公式清单 | 完成 | 见 `task_plan.md` |
| 4 | 阅读旧测试仅作覆盖地图 | 完成 | 未复用 DGP、脚本、数据或 expected values |
| 5 | 编写 `test-design-register.md` | 完成 | 见同目录 `test-design-register.md` |
| 6 | 设计并实现 7 个新 synthetic 双跑 | 完成 | `test_m02_synthetic.py` |
| 7 | 独立编写并运行 Stata `.do` | 完成 | 所有 `.do` 由 `audit_utils.run_stata_do` 现场生成执行 |
| 8 | 独立运行 Python | 完成 | 全部现场执行 |
| 9 | 字段级差异比较 | 完成 | coefficients、VCE、df、R²、RMSE、F 等 |
| 10 | 设计真实数据实验 | 完成 | Grunfeld 数据集的 cluster FE 与两向 FE |
| 11 | 执行 metamorphic/property tests | 完成 | 4 个性质测试 |
| 12 | 构造最小复现 | 完成 | `repro_m02_fe_findings.py` |
| 13 | 区分产品/测试/runner/parser 根因 | 完成 | 已排除 runner/parser 问题 |
| 14 | 写入 `findings.md` | 完成 | 7 个 confirmed finding + 1 共享基础设施风险 |
| 15 | 运行现有非 golden 测试 | 完成 | `pytest tests/ -v --ignore=tests/golden/`：349 passed |
| 16 | 模块 `summary.md` | 完成 | 见同目录 `summary.md` |

## 关键结果统计

- **Synthetic 实验**: 7 个，其中 2 个 PASS，5 个 FAIL
- **真实数据实验**: 2 个，其中 1 个 PASS，1 个 FAIL
- **Property tests**: 4 个，其中 3 个 PASS，1 个 FAIL
- **Confirmed findings**: 7 个（6 个 P1，1 个 P0）
- **共享基础设施风险**: 1 个（`detect_collinear_columns` tolerance）

## 未开始 / 未验证项

- `areg()` 单吸收 FE 路径未在本轮单独穷举；仅在 `xtreg_fe` 与 `FixedEffectsOLS` 对比中覆盖。
- 非 `add_constant=True` 路径下的 `_cons` 语义未与 Stata 做逐项字段比较。
- 权重（`aweight`、`fweight`）在 FE 中的行为未审查（当前实现可能不支持）。
- `predict` / 残差 / savefe 等 postestimation 未纳入本轮。

## 阻塞与风险

- 无外部阻塞。
- 主要风险：共享基础设施 `detect_collinear_columns` 的 tolerance 问题可能同时影响后续 M03/M04 审查，建议优先处理。
