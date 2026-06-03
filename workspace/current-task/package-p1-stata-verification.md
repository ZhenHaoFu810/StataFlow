# Package: P1 Stata VCE 验证

**Phase:** Audit Phase 1 → v1.1.0 前置验证
**日期:** 2026-04-30
**状态:** 进行中
**类型:** Stata-Python 双跑验证（可修改 code 以添加 golden tests，不修改 estimator 代码）

---

## 背景

Phase 1 数学正确性审查发现 4 项独立 P1 验证项。这些项均涉及 VCE 修正因子——当前实现可能是正确的（与 Stata 约定一致），但需要 Stata 双跑输出确认。现有 golden 测试覆盖缺口：

- PPMLHDFE: 无 1-way cluster golden test，无 robust VCE golden test
- GLM (logit/poisson): 无 robust VCE golden test，无 cluster VCE golden test
- Probit robust VCE: 已有 golden test 通过 (rtol=1e-6)

---

## 目标

为每个 P1 项创建 Stata-Python 双跑验证，确认当前 VCE 修正因子与 Stata 17 一致。

| ID | 验证内容 | Stata 命令 | N 要求 |
|----|---------|-----------|--------|
| VCE-P1-1 | PPMLHDFE 1-way cluster 修正 | `ppmlhdfe y x, absorb(FE) vce(cluster FE)` | N≤200, G≥10 |
| VCE-P1-2 | PPMLHDFE robust 修正 | `ppmlhdfe y x, absorb(FE) vce(robust)` | N≤200 |
| VCE-P1-3a | Logit robust 修正 | `logit y x, vce(robust)` | N≤200 |
| VCE-P1-3b | Poisson robust 修正 | `poisson y x, vce(robust)` | N≤200 |
| VCE-P1-3c | Logit cluster 修正 | `logit y x, vce(cluster g)` | N≤200, G≥10 |
| VCE-P1-4 | Probit robust 修正 | 已有 golden test — 仅需文档确认 | N/A |

---

## 允许修改范围

- `tests/golden/test_p1v_*.py` (新增 5-6 个 golden test 文件)
- `stata/cases/p1v_*.dta` (Stata 数据文件)
- `stata/output/` (Stata 输出)
- `docs/audit/vce-formula-audit.md` (更新验证结论)
- `workspace/current-task/REPORT.md`

**禁止修改:** 任何 estimator `.py` 源码、现有 golden test、支持矩阵、README

---

## 执行顺序

1. PPMLHDFE 1-way cluster → 2. PPMLHDFE robust → 3. Logit robust + cluster → 4. Poisson robust + cluster → 5. Probit 文档确认 → 6. 汇总 + 更新审计报告

---

## 成功标准

- [ ] 所有 6 个 P1 子项已验证（确认或否定）
- [ ] 新增 golden 测试全部通过
- [ ] 审计报告 P1 项状态已更新
- [ ] 验证结论明确：全部通过 / 需修正 / 无法确定
