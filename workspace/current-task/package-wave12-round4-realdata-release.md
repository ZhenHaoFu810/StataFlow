# Wave 12 Round 4：真实数据验证与 v1.0.0 发布准备

**任务卡编号：** `wave12-round4-realdata-release`
**编制：** StataFlow Roadmaster
**日期：** 2026-04-30
**状态：** 待执行
**前置任务：** Wave 12 Round 1, Round 2, Round 2b/3（均已完成）

---

## Background

Wave 12 是 StataFlow v1.0.0 前的最后一个 wave。Round 1-2b/3 已完成三项核心能力（MAP 迭代内核、个体斜率吸收、Driscoll-Kraay VCE），均通过 correctness-gatekeeper 审核，275 non-golden + 763 golden 测试全部通过。

本轮为 Wave 12 收口轮，目标：为已实现的 slopes 和 DK 能力补充真实数据双跑证据，完成全部文档与元数据的 v1.0.0 迁移，将项目从 Beta (v0.3.0) 推进到 Stable (v1.0.0)。

## Roadmaster 路线重定向

原始 Wave 12 范围还包括 `group(var) individual(var)` FE、3-way+ clustering、LSMR/LSQR 算法评估、`savefe` MAP 路径支持。Roadmaster 评估后决定：**四项全部推迟至 v1.1.0+**。

| 推迟项 | 理由 | v1.1.0 规划状态 |
|--------|------|----------------|
| `group(var) individual(var)` FE | 高复杂度（组级聚合 + 个体 FE），无用户阻塞 | Planned |
| 3-way+ clustering | 2-way 已完整实现；3-way 需 VCE 框架重构 | Planned |
| LSMR/LSQR 算法 | MAP 已解决性能瓶颈（内存降低 2-3 个数量级）| Planned |
| `savefe` MAP 路径 | LSDV 路径 savefe 已完整实现；MAP 路径需额外架构设计 | Planned |

所有推迟项已在 `docs/roadmap.md` 和 `docs/release/known-issues.md` 中明确记录。

## Objective

1. **真实数据 golden 双跑验证**：为 slopes 和 DK 提供 wagepan 真实面板数据集上的 Stata-Python 双跑证据。
2. **命令支持矩阵最终审核**：确保 reghdfe/ivreghdfe/ppmlhdfe 支持矩阵准确反映 v1.0.0 状态。
3. **文档同步**：known-issues、release-candidate-checklist、roadmap、open-source status 更新至 v1.0.0。
4. **版本发布**：版本号 0.3.0 → 1.0.0，Development Status Beta → Production/Stable。

## Why now

- Wave 12 Round 1-2b/3 全部完成并通过 gatekeeper 审核。
- 无阻塞返工包。1,038 测试全部通过。
- 原始 Wave 12 剩余项已推迟至 v1.1.0+。
- v1.0.0 的唯一剩余障碍是真实数据验证与文档收口。
- 推迟四项不会引入回归风险，它们不在当前代码路径中。

## Permitted modification scope

- `tests/golden/test_w12_slopes_real_wagepan.py` — 新增
- `tests/golden/test_w12_dkraay_real_wagepan.py` — 新增
- `docs/command-support-matrix/reghdfe.md` — 最终审核
- `docs/command-support-matrix/ivreghdfe.md` — dkraay 状态审核
- `docs/command-support-matrix/ppmlhdfe.md` — 审核
- `docs/testing/test-case-catalog.md` — 登记真实数据样例
- `docs/release/known-issues.md` — v1.0.0 更新
- `docs/release/release-candidate-checklist.md` — v1.0.0 更新
- `docs/release/open-source-stable-status.md` — 新建
- `docs/roadmap.md` — Wave 12 完成标记 + v1.1.0 条目
- `pyproject.toml` — version 1.0.0, Development Status Stable
- `src/stataflow/__init__.py` — `__version__` 1.0.0
- `tests/test_smoke.py` — 版本号 1.0.0
- `README.md` / `README.zh-CN.md` — 能力描述更新
- `workspace/current-task/REPORT.md` — Round 4 报告

## Prohibited actions

- **禁止修改任何估计器内核代码** — 本轮是验证与文档轮，不是实现轮。
- **禁止修改 `ResultSchema` 公共字段** — 不新增任何字段。
- **禁止更改推迟至 v1.1.0+ 的决策** — 四项推迟项明确不在本轮范围。
- **禁止在未通过真实数据 golden 测试前 bump 版本号** — 真实数据验证是 v1.0.0 的前置门槛。
- **禁止跳过文档一致性检查** — README、support matrix、known-issues、checklist 必须交叉一致。
- **禁止修改 `docs/project-charter.md` 或架构原则**。
- **禁止在 slopes + DK 组合 golden 测试失败时静默接受** — 必须显式记录为已知限制。

## Execution order (mandatory)

```
Step 1: 获取 wagepan.dta 数据（确认项目中已有或从网络获取）
  └── Step 2: 编写 wagepan slopes golden 测试（LSDV 路径）
       └── Step 3: 运行 Stata-Python 双跑，验证字段级一致性
            └── Step 4: 编写 wagepan DK golden 测试
                 └── Step 5: 运行 Stata-Python 双跑，验证字段级一致性
                      └── Step 6: [可选] slopes + DK 组合 golden 测试
                           └── Step 7: 全量回归测试（non-golden + golden）
                                └── Step 8: 命令支持矩阵最终审核
                                     └── Step 9: 更新 known-issues.md
                                          └── Step 10: 更新 release-candidate-checklist.md
                                               └── Step 11: 更新 roadmap.md（Wave 12 完成，v1.1.0 条目）
                                                    └── Step 12: 创建 open-source-stable-status.md
                                                         └── Step 13: 版本号 bump（0.3.0 → 1.0.0）
                                                              └── Step 14: README 更新
                                                                   └── Step 15: 导出脚本 dry-run 验证
                                                                        └── Step 16: 全量最终回归测试 + REPORT.md
```

## Minimum verification requirements

| 验证项 | 方法 | 期望结果 | 检查文件/命令 |
|--------|------|----------|--------------|
| wagepan slopes 真实数据 | `reghdfe lwage exp, absorb(nr##c.year)` on wagepan | 系数/SE rtol < 1e-6 | `tests/golden/test_w12_slopes_real_wagepan.py` |
| wagepan DK 真实数据 | `reghdfe lwage exp, absorb(nr year) vce(dkraay)` on wagepan | 系数 < 1e-6, SE < 1e-4 | `tests/golden/test_w12_dkraay_real_wagepan.py` |
| 全量 non-golden 回归 | `pytest tests/ --ignore=tests/golden/ -q` | 275+ passed, 0 failed | pytest 输出 |
| 全量 golden 回归 | `pytest tests/golden/ -q` | 765+ passed, 0 failed | pytest 输出 |
| 支持矩阵一致性 | 逐文件审核 reghdfe/ivreghdfe/ppmlhdfe.md | supported/planned/unsupported 准确 | 矩阵文件 |
| known-issues 更新 | 与代码状态对照 | reghdfe 行反映 slopes/dkraay 已完成 | `known-issues.md` |
| checklist 更新 | 所有检查项重新确认 | 全部通过 | `release-candidate-checklist.md` |
| 版本一致性 | `python -c "import stataflow; print(stataflow.__version__)"` | 1.0.0 | 版本检查 |
| 导出 dry-run | `python scripts/release/export_open_source.py --dry-run` | 无错误 | 导出脚本 |
| README 一致性 | README 能力描述与矩阵一致 | slopes + dkraay 提及 | README |

## Deliverables

1. `tests/golden/test_w12_slopes_real_wagepan.py` — wagepan 斜率吸收真实数据 golden 测试
2. `tests/golden/test_w12_dkraay_real_wagepan.py` — wagepan DK 真实数据 golden 测试
3. `docs/command-support-matrix/reghdfe.md` — 最终审核（slopes/DK/MAP/savefe 标记准确）
4. `docs/command-support-matrix/ivreghdfe.md` — dkraay status review
5. `docs/command-support-matrix/ppmlhdfe.md` — audit
6. `docs/testing/test-case-catalog.md` — 真实数据样例登记
7. `docs/release/known-issues.md` — v1.0.0 update
8. `docs/release/release-candidate-checklist.md` — v1.0.0 update
9. `docs/release/open-source-stable-status.md` — new stable status doc
10. `docs/roadmap.md` — Wave 12 completed, v1.1.0 entries added
11. `pyproject.toml` — version 1.0.0, Development Status 5 - Production/Stable
12. `src/stataflow/__init__.py` — `__version__` 1.0.0
13. `tests/test_smoke.py` — version 1.0.0
14. `README.md` / `README.zh-CN.md` — capability descriptions updated
15. `workspace/current-task/REPORT.md` — Round 4 report

## Success criteria

- [ ] wagepan slopes real-data golden dual-run: coef/SE rtol < 1e-6
- [ ] wagepan DK real-data golden dual-run: coef < 1e-6, SE < 1e-4
- [ ] Full non-golden regression: 275+ passed, 0 failed
- [ ] Full golden regression: 765+ passed, 0 failed
- [ ] Command support matrices audited and consistent
- [ ] `known-issues.md` updated with slopes/DK completed, deferred items listed
- [ ] `release-candidate-checklist.md` all checks re-verified for v1.0.0
- [ ] `roadmap.md` Wave 12 marked done, v1.1.0 entries added
- [ ] Version 1.0.0 consistent across pyproject.toml, `__init__.py`, test_smoke.py
- [ ] Development Status updated to Production/Stable
- [ ] README capability descriptions match support matrices
- [ ] Export dry-run passes without errors
- [ ] `workspace/current-task/REPORT.md` delivered
