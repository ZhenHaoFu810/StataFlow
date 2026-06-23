# M03 HDFE 审查进度 progress.md

## 当前状态

- **模块**: M03 HDFE
- **审查轮次**: modular-revalidation-v1.3
- **基线 commit**: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- **reghdfe 版本**: 6.13.1
- **完成时间**: 2026-06-13

## 已完成工作

| # | 任务 | 状态 | 说明 |
|---|---|---|---|
| 1 | 记录基线 commit、Python、Stata、reghdfe 版本 | 完成 | 见 `task_plan.md` |
| 2 | 阅读 public API、support matrix、实现文件 | 完成 | 通过 explore agent 完成 `absorbing_ols.py`、`_absorb_spec.py`、`_vce_utils.py`、`hdfe.py`、`linear.py` 走查 |
| 3 | 建立功能清单与风险清单 | 完成 | 见 `task_plan.md` |
| 4 | 阅读旧测试仅作覆盖地图 | 完成 | 未复用 DGP、脚本、数据 |
| 5 | 编写 `test-design-register.md` | 完成 | 见同目录文件 |
| 6 | 设计并实现 8 个新 synthetic 双跑 | 完成 | `test_m03_synthetic.py` |
| 7 | 独立编写并运行 Stata `.do` | 完成 | 全部现场执行 |
| 8 | 独立运行 Python | 完成 | 全部现场执行 |
| 9 | 字段级差异比较 | 完成 | coefficients、VCE、df、R²、RMSE、F、cluster_count |
| 10 | 设计真实数据实验 | 完成 | Grunfeld 2-FE cluster 与 slope |
| 11 | 执行 metamorphic/property tests | 完成 | 4 个性质测试 |
| 12 | 构造最小复现 | 完成 | `repro_m03_hdfe_findings.py` |
| 13 | 区分产品/测试/runner/parser 根因 | 完成 | 已排除 runner/parser 问题 |
| 14 | 写入 `findings.md` | 完成 | 4 个 confirmed finding + 1 共享基础设施风险 |
| 15 | 运行现有非 golden 测试 | 完成 | `pytest tests/ -v --ignore=tests/golden/`：349 passed |
| 16 | 模块 `summary.md` | 完成 | 见同目录文件 |

## 关键结果统计

- **Synthetic 实验**: 8 个，其中 5 个 PASS，3 个 FAIL
- **真实数据实验**: 2 个，其中 0 个 PASS，2 个 FAIL
- **Property tests**: 4 个，全部 PASS
- **Confirmed findings**: 4 个（3 个 P1，1 个 P2）
- **共享基础设施风险**: 1 个（`detect_collinear_columns` tolerance）

## 未覆盖区域

- `areg()` 单吸收路径未独立穷举（仅通过 `AbsorbingOLS` 模式切换间接覆盖）。
- Driscoll-Kraay VCE 未在本轮做独立真实数据验证。
- 多向 FE + 权重（`aweight`/`fweight`）未审查。
- 高维多向 FE 的 MAP 收敛阈值和运行时间未做大规模压力测试。
- `savefe` 固定效应恢复未审查。

## 阻塞与风险

- 无外部阻塞。
- 主要风险：M03-HDFE-001（嵌套 FE 与 cluster）影响大量典型实证设计，应优先修复。
