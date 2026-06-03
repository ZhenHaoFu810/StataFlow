# 当前任务

**Audit Phase 3 Wave 1：真实数据双跑验证 — P0 实验 + 立即可用数据**

**状态：** 完成（2026-04-30）— 25 passed, 1 xfailed, 0 regression
**任务卡：** `workspace/current-task/package-audit-phase3-real-data-wave1.md`

**前置条件：**
- [x] Waves 0-12 全部完成，v1.0.0 Stable
- [x] Phase 1 数学审查完成（24 项确认正确，5 P1 待验证）
- [x] Phase 2 代码重构完成（6/8 子项交付，0 regression）
- [x] 5 个目标数据集全部在项目中可用（零外部下载）

---

## 背景

StataFlow v1.0.0 已完成 765 个 golden 双跑测试。然而，现有真实数据测试存在覆盖深度不足（通常仅 `vce="ols"` 单一路径）和缺乏结构化实验文档两个结构性缺口。

Phase 3 Wave 1 通过 5 个金融经济学实验填补这些缺口。所有数据已在本项目中。

---

## 实验清单（执行顺序）

| 序号 | 实验 | 优先级 | 命令 | 数据 |
|------|------|--------|------|------|
| 1 | C1.1 CAPM/FF3 因子回归 | P0 | `regress`, vce(ols/robust/cluster) | FF3 daily returns |
| 2 | C1.4 Card IV 教育回报率 | P0 | `ivreghdfe` 2SLS/GMM2S/LIML, vce(ols/robust/cluster) | card.csv |
| 3 | C1.6 引力模型 PPMLHDFE | P0 | `ppmlhdfe`, vce(robust/cluster), eform, separation | EXAMPLE_TRADE_FTA_DATA.dta |
| 4 | C1.7 DID 政策评估 | P1 | `did_imputation` + `csdid` reg/dripw, controls, pretrends | ezunem |
| 5 | C1.8 政治 RD 断点回归 | P2 | `rdrobust` 全部带宽选择器, sharp/fuzzy, cluster | senate |

---

## 执行顺序

```
3.1.0 基础设施 → 数据可用性确认
  → 3.1.1 C1.1 CAPM/FF3 (OLS)
    → 3.1.2 C1.4 Card IV (IV)
      → 3.1.3 C1.6 Gravity PPML (PPMLHDFE)
        → 3.1.4 C1.7 DID Policy (DID)
          → 3.1.5 C1.8 RD Senate (RD)
            → 3.1.6 汇总与文档更新
```

每子阶段完成后运行 `pytest tests/ --ignore=tests/golden/ -q` 确认 0 回归。

---

## 核心护栏

- **每个实验必须 Stata 双跑验证** — 每个 VCE/estimator 组合都必须有 Stata 输出
- **禁止以 "统计等价" 替代字段级比对** — 所有字段必须通过 `tolerance_close`
- **禁止修改 estimator 数学公式**
- **禁止修改 public API signatures**
- **禁止修改已有 golden test expectations**
- **禁止跳过 `data_prep.py`** — 数据预处理必须是可复现脚本
- **若发现偏差，先理解根因再决定处理方式** — 不盲目放宽容忍度，不盲目修改代码

---

## 许可修改范围

- `research/experiments/c1_*/` — 新建实验包（README、data_prep、analysis.do/py、results.md）
- `tests/golden/test_v2_c1_*_real.py` — 新建综合 golden 测试
- `tests/data/` — 按需新增预处理数据
- `stata/cases/` — 新增 .do 和 .dta
- `docs/testing/test-case-catalog.md` — 登记新样例
- `docs/command-support-matrix/*.md` — 更新验证状态
- `docs/release/known-issues.md` — 记录新发现偏差
- `src/stataflow/estimators/*.py` — 仅修复实验中发现的 bug（需记录根因）

---

## 成功标准

- [ ] 5 个实验全部完成（每个有完整 5 文件包 + README）
- [ ] 5 个 golden 测试文件全部通过
- [ ] 全量回归测试通过（0 regression）
- [ ] 所有 VCE/estimator 组合都有 Stata 双跑输出
- [ ] C1.6 PPMLHDFE VCE 修正验证完成
- [ ] C1.7 CSDID DR SE 偏差根因分析完成
- [ ] C1.8 RD 真实数据带宽偏差量化完成
- [ ] test-case-catalog.md 和支持矩阵已更新
