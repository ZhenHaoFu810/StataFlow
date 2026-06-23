# Codex 裁定记录 - StataFlow v1.0.0 审计修缮

**日期**: 2026-06-04  
**提交方**: Claude Code (Implementation Agent)  
**状态**: 本轮不再存在待 Codex 裁定的开放问题；`CODEX_ESCALATION.md` 转为裁定归档

---

## 1. 裁定结论

### 1.1 IV-14: 2-way cluster `_cons` SE 偏差

**最终裁定**: 关闭为已知局限，不再作为本轮未解决开发问题保留。

**理由**:

1. 当前实现已经把 2-way cluster 下的 slope block、`df_resid`、弱工具诊断和 second-stage `fit.f_stat` 收口到 Stata 口径。
2. 剩余偏差仅限于 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 在 **2-way cluster + `_cons`** 场景下的常数项标准误。
3. 现有证据表明，该残差不是普通代码 bug，而是 **LSDV + reported-space PSD fix** 与 Stata `reghdfe` iterative demeaning 框架之间的结构性差异；参见 `docs/adr/ADR-0003-lsdv-cons-se-under-multiway-cluster.md`。
4. 当前 Python 结果已经处在 ADR-0003 约束范围内：
   - synthetic 2-way cluster: `_cons` SE 相对误差约 **2.25%**，低于 Tier 1 上限 `rtol=0.03`
   - real-data 2-way cluster: 已由现有 golden test 约束在 Tier 2 上限 `rtol=0.20` 内
5. 在不重写 HDFE 常数恢复路径为完整 iterative demeaning / MAP-VCV 内核之前，本轮没有证据支持一个局部补丁能把该偏差稳定压到 `< 1%`，且不引入新的 slope VCE 回归。

**对本轮版本的决定**:

- `IV-14` 从“需 Codex 裁定”转为“已知局限”
- 继续保留 runtime warning、ADR-0003 文档说明和 golden test 容忍度门禁
- 不在本轮继续为 `_cons` SE 做高风险局部公式修补

---

## 2. 本轮最终分类

| 类别 | 数量 | 状态 |
|------|------|------|
| 代码修复完成 | 96 项 | 已实现并验证 |
| 已知局限 | 4 项 | 已文档化并有测试/ADR 约束 |
| v1.2.0+ 排期项 | 8 项 | 已明确归档，不属于本轮阻塞 |
| **待裁定开放项** | **0 项** | **本轮已清零** |

本轮 108 项问题现已全部收口到以下三类之一：**已修复 / 已知局限 / 已排期**。

---

## 3. 已知局限清单

| 问题 | 命令族 | 说明 |
|------|--------|------|
| IV-14 | IV / Panel / PPML HDFE | 2-way cluster `_cons` SE 的结构性残差；受 ADR-0003 约束 |
| LINEAR-11 | Linear | `c.x1#c.x2` 列名保留 `#`，这是 Stata 因子变量标准语法 |
| LINEAR-12 | Linear | `xtreg_fe` `df_model` 与 `f_stat` dfn 不一致，属于 Stata 设计选择 |
| PANEL-11 | Panel | `df_a` 使用简化算法而非 pairwise mobility groups，文档已标记 |

---

## 4. 后续版本项

| 问题 | 命令族 | 说明 |
|------|--------|------|
| IV-10 | IV | first-stage AP/SW F 统计量 |
| IV-19 | IV | `level()` 展示层参数 |
| 展示层参数 | 全部 | `noci` / `nopvalues` / `eform` 等完整支持 |

---

## 5. 结论

`docs/audit/revalidation-v1.1` 这一轮审计修缮已完成收口。后续若继续推进，应进入 **v1.2.0+ 功能补齐** 或 **Wave 12 / HDFE 内核重构**，而不是继续把 `IV-14` 当作本轮未完成 bug 保留。

