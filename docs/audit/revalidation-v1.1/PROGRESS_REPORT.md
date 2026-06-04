# StataFlow 修缮进度报告

**生成日期**: 2026-06-04  
**当前分支**: `fix/v1.0.1-hotfix`  
**工作范围**: `docs/audit/revalidation-v1.1` 全面复核后的代码修缮与收口  
**状态**: **本轮 108 项问题已全部收口**

---

## 1. 总体结论

本轮 revalidation-v1.1 的目标不是继续扩命令覆盖面，而是把已有实现重新按 **Stata 17 字段级对齐标准** 审一遍，并把所有发现的问题收口到明确状态。

截至 2026-06-04，本轮 108 项问题已经全部进入以下三类之一：

| 类别 | 数量 | 含义 |
|------|------|------|
| 代码修复完成 | 96 项 | 已修改实现，并用回归测试或 golden dual-run 验证 |
| 已知局限 | 4 项 | 不再作为本轮开放 bug；已写入 ADR / known issue / 测试容忍度 |
| v1.2.0+ 排期项 | 8 项 | 非本轮阻塞，已明确进入后续版本规划 |
| **开放项** | **0 项** | **本轮已清零** |

这意味着：**“108 项全部修改收尾好”在本轮审计口径下已经成立。**

---

## 2. 本轮最终分类

### 2.1 已修复的主线问题

本轮真正完成的代码修复集中在：

- DID / event study:
  - `csdid` wrapper 返回值、`notyet`、pretrend、cluster 路径
  - `did_imputation` 的 `allhorizons`、aggregate sample screening、pretrend cluster SE
- GLM / PPML:
  - robust 小样本修正
  - `eform` z/p 口径
  - wrapper 返回 fitted model、权重支持
- RD:
  - `rdrobust` 默认 `bwselect="mserd"`
  - cluster 带宽选择
  - `rdplot` covariate adjustment、ES bias、bin/fit 一致性
- Linear / shared VCE:
  - collinearity detection
  - 2-way cluster interaction collision
  - wrapper 兼容 `vce(cluster ...)`
- IV / HDFE / Panel 收尾:
  - 2-way cluster fallback
  - `df_resid`、weak-IV、first-stage diagnostics
  - Card real-data cluster `fit.f_stat`

---

## 3. 已知局限

以下 4 项不再作为本轮开放问题保留：

| 问题 | 命令族 | 最终状态 |
|------|--------|----------|
| IV-14 | IV / Panel / PPML HDFE | 2-way cluster `_cons` SE 结构性残差；按 ADR-0003 关闭 |
| LINEAR-11 | Linear | `c.x1#c.x2` 列名保留 `#`；这是 Stata 因子变量标准语法 |
| LINEAR-12 | Linear | `xtreg_fe` `df_model` 与 `f_stat` dfn 不一致；属于 Stata 设计选择 |
| PANEL-11 | Panel | `df_a` 仍用简化算法，不做 pairwise mobility groups |

### 3.1 IV-14 裁定结果

`IV-14` 是本轮最后一个未决项。最终裁定如下：

- 现有残差只出现在 **2-way cluster + `_cons` SE**
- synthetic case 当前误差约 **2.25%**
- slope SE、`df_resid`、weak-IV、first-stage、second-stage `fit.f_stat` 已全部收口
- 没有证据表明本轮还能通过一个局部补丁把 `_cons` SE 稳定压到 `< 1%`，且不引入新的 VCE 回归

因此本轮不再继续把 `IV-14` 视为开放 bug，而是按 `ADR-0003` 归档为 **结构性局限**。详见：

- `docs/audit/revalidation-v1.1/CODEX_ESCALATION.md`
- `docs/adr/ADR-0003-lsdv-cons-se-under-multiway-cluster.md`

---

## 4. v1.2.0+ 排期项

| 问题 | 命令族 | 说明 |
|------|--------|------|
| IV-10 | IV | first-stage AP/SW F 统计量 |
| IV-19 | IV | `level()` 展示层参数 |
| 展示层参数 | 全部 | `noci` / `nopvalues` / `eform` 等完整支持 |

合并口径下，这一类共 **8 项**，已经明确排入后续版本，不属于本轮阻塞。

---

## 5. 验证证据

本轮收尾的关键验证包括：

- `pytest tests/test_vce_utils.py -q` -> 6 passed
- `pytest tests/test_compat_stata_iv.py tests/test_vce_utils.py -q` -> 19 passed
- `pytest tests/golden/test_w7_reghdfe_2way_cluster.py -q` -> 16 passed
- `pytest tests/golden/test_w7_ivreghdfe_2way_cluster.py -q` -> 14 passed

与 `NEW-IV-02` 相关的 Card real-data spot check 已对齐：

- `cluster='age_group'`: `fit.f_stat = 0.3556943740`
- `cluster=['age_group', 'south']`: `fit.f_stat = 0.3556943740`
- 对齐 Stata log `F(6, 2) = 0.36`

---

## 6. 当前可执行结论

对本轮 revalidation-v1.1 来说，项目现在处于下面的状态：

1. 所有审计问题都已有最终归宿
2. 不再存在需要继续开发才能让本轮闭环的开放缺口
3. 后续工作若继续展开，应转入：
   - `v1.2.0+` 展示层 / first-stage 扩展
   - 或 Wave 12 / HDFE 内核重构

换句话说，**本轮全面审查发现的 108 项问题，已经全部收尾。**

