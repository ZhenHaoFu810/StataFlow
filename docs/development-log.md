# StataFlow 开发运行日志

> **生成日期：** 2026-04-30
> **当前版本：** v1.0.0 (Stable)
> **项目路径：** StataFlow — Python 环境中可扩展的 Stata 17 命令映射平台

---

## 一、项目概览

StataFlow 是一个计量经济学工具包，目标是在 Python 中高精度复现 Stata 17 的估计结果。项目采用四层架构（`stata_runner` → `result_spec` → `estimators` → `testing_harness`），以"命令族 + 研究档案 + synthetic 黄金样例 + 真实公开数据样例"四合一方式推进。

**核心原则：**
- Stata 17 为默认真值来源
- 每个公开能力必须有 Stata-Python 双跑证据
- 源码研究档案先于实现
- correctness-before-completeness（正确性优先于完整度）

---

## 二、开发时间线

### 2026-04-13：项目奠基（Phase 0）

- 仓库初始化，治理文档 bootstrap
- 确立四层架构与双跑验证框架
- `stata_runner` 层：可调用本地 Stata 17 执行 `.do` 文件并收集日志
- `result_spec` 层：统一的结果 schema 定义

### 2026-04-13 ~ 04-15：Wave 0 — 原型验证

- 实现 `regress`（OLS）基本估计
- 验证 `vce(robust)`、`vce(cluster)`、`aweight`
- 验证 `xtreg, fe`（面板固定效应）
- 验证 FE + cluster 组合
- **意义：** 证明 Python 端可在机器可验证框架下复现 Stata 结果

### 2026-04-15 ~ 04-18：Waves 1–6 — 核心命令族（v0.1.x Alpha）

| Wave | 内容 | 关键交付 |
|------|------|----------|
| Wave 1 | Panel / FE / HDFE | `areg`、双向 FE 吸收内核、`reghdfe` 最小子集 |
| Wave 2 | IV / GMM | `ivregress 2sls`、`ivreghdfe` |
| Wave 3 | Binary / Count | `logit`、`probit`、`poisson`、`ppmlhdfe` |
| Wave 4 | DID / Event Study | `did_imputation`、`eventstudyinteract`、`csdid` |
| Wave 5 | Postestimation | `predict` 高频子集、`margins` 子集 |
| Wave 6 | RD / Local Polynomial | `rdrobust` Sharp RD 最小子集 |

- 2026-04-18：首次开源发布准备（`f0adbe6`）
- 2026-04-19：v0.1.0 Alpha 发布准备（`07c5e62`）
- 2026-04-20：README 更新与 PyPI 版本 bump（`070e286`）
- 2026-04-23：v0.1.5（`d162550`）

### 2026-04-28 ~ 04-29：Waves 7–9 — HDFE / RD / DID 加固（v0.2.x Beta）

| Wave | 内容 | 关键交付 |
|------|------|----------|
| Wave 7 | HDFE Hardening | `reghdfe`/`ivreghdfe`/`ppmlhdfe` 2-way cluster、`savefe`、`separation(fe)`、`eform`/`irr`、`first`/`ffirst` 一阶段诊断 |
| Wave 8 | RD Completion | `rdrobust` 完整带宽选择器族（`msetwo`, `msesum`, `msecomb1/2`, `cerrd`, `certwo`, `cersum`, `cercomb1/2`）、fuzzy RD、`weights`、`vce(cluster)`/`vce(nncluster)`、`masspoints`、`rdplot` |
| Wave 9 | DID Hardening | `did_imputation`：`controls`/`unitcontrols`/`timecontrols`、`wtr`/`sum`/`hbalance`、`hetby`/`project`、`pretrends`、`saveestimates`/`saveweights`/`saveresid`；`csdid`：`method="dr"`（双重稳健）、`aggtype`（simple/dynamic/group/calendar） |

### 2026-04-29 ~ 04-30：Waves 10–11 — IV 补全 + 后估计生态（v0.3.x Beta）

| Wave | 内容 | 关键交付 |
|------|------|----------|
| Wave 10 | IV Completion | `gmm2s`/`cue`（GMM 估计器）、`liml`/`kclass`/`fuller`、`weakiv`（Kleibergen-Paap rk LM / rk Wald F + Stock-Yogo 临界值）、`orthog`/`endogtest`/`redundant`、`partial()`/`fwl()`、HAC 标准误 |
| Wave 11 | Postestimation Ecosystem | `predict stdp`（reghdfe/ivreghdfe）、`predict pearson/deviance/working`（ppmlhdfe）、`estat summarize`、`estat vce`、`estat ic` |

- 2026-04-30：v0.3.0 Beta 发布准备完成
  - 版本号同步：0.1.5 → 0.3.0
  - Development Status：3-Alpha → 4-Beta
  - 271 非 golden 测试 + 763 golden 测试全部通过
  - 开源镜像导出验证通过

### 2026-04-30（当天，约 8 小时窗口）：Wave 12 — 高级 HDFE 与性能（v1.0.0 Stable）

**这是项目迄今为止最密集的开发日**，完成了从 Beta 到 Stable 的跨越：

| Round | 内容 | 关键交付 |
|-------|------|----------|
| Unblocker | 性能基准数据集准备 | 3 组大规模合成数据集（N=1M–2M），证实 LSDV 在 >1e6 观测下 OOM |
| Round 1 | 研究轮 | MAP/LSMR 算法、个体斜率语法、Driscoll-Kraay 公式研究档案 |
| Round 2 | MAP 迭代内核 | 纯 NumPy Kaczmarz 顺序投影 + Aitken 加速框架；小样本 rtol < 1e-10；基准数据集内存降低 2-3 个数量级 |
| Round 2b/3 | 个体斜率 + DK | `absorb(var##c.slope)` 斜率吸收；`vce(dkraay)` Driscoll-Kraay 面板 HAC；经 4 轮 correctness-gatekeeper 审查 |
| Round 4 | 真实数据验证 + v1.0.0 发布 | wagepan 真实数据 golden 测试；版本 0.3.0 → 1.0.0；文档全面同步 |

**Round 4 完成标志：**
- 275 non-golden + 763 golden 测试全部通过（总计 1,038）
- 126 个 golden 测试文件
- correctness-gatekeeper 全部审核通过
- 命令支持矩阵全部更新
- known-issues / release-checklist / roadmap / README 全部同步

---

## 三、当前项目状态总览

### 3.1 已实现的命令族（全部通过双跑验证）

| 命令族 | 状态 | 版本 | 核心能力 |
|--------|------|------|----------|
| **Linear Base** | Stable | v1.0.0 | `regress`、robust/cluster VCE、`aweight`、`xtreg, fe` |
| **Panel / FE / HDFE** | Stable | v1.0.0 | `areg`、双向 FE 吸收、`reghdfe`（含 slopes、dkraay） |
| **IV / GMM** | Beta | v1.0.0 | `ivregress 2sls`、`ivreghdfe`（2SLS/GMM2S/LIML/weakiv） |
| **Binary / Count** | Beta | v1.0.0 | `logit`、`probit`、`poisson`、`ppmlhdfe` |
| **DID / Event Study** | Beta | v1.0.0 | `did_imputation`、`eventstudyinteract`、`csdid` |
| **RD / Local Polynomial** | Beta | v1.0.0 | `rdrobust`（完整带宽选择器 + fuzzy RD + cluster） |
| **Postestimation** | Stable | v1.0.0 | `predict`（含 stdp/pearson/deviance/working）、`estat` 生态 |

### 3.2 架构层状态

| 层 | 文件数 | 状态 |
|----|--------|------|
| `stata_runner` | ~5 | 稳定，支持 Stata 17 批量执行与日志解析 |
| `result_spec` | ~3 | 稳定，统一 ResultSchema |
| `estimators` | ~10 | 稳定，含 `AbsorbingOLS`（LSDV + MAP 双路径） |
| `compat/stata` | ~8 | 稳定，Stata 命令兼容包装层 |
| `testing_harness` | ~126 golden + ~30 unit | 稳定，覆盖 synthetic + real-data 双线 |

### 3.3 技术债务与已知限制

| 类别 | 内容 | 严重程度 | 计划 |
|------|------|----------|------|
| 结构偏差 | `reghdfe` 2-way cluster `_cons` SE ~2-16% 偏差 | 已知/ADR-0003 | v1.1.0 不保证修复 |
| 精度边界 | DK SE rtol 1e-4（vs 标准 1e-6） | 已知限制 | 已文档化 |
| 精度边界 | MAP 1-way cluster slope SE ~0.5% | 已知限制 | 已文档化 |
| 精度边界 | PPMLHDFE 残差 ~0.35% | 已知限制 | IRLS/HDFE 收敛差异 |
| 功能缺口 | 3-way+ clustering | 推迟 | v1.1.0+ |
| 功能缺口 | `group/individual` FE | 推迟 | v1.1.0+ |
| 功能缺口 | LSMR/LSQR 算法 | 推迟 | v1.1.0+ |
| 功能缺口 | `savefe` MAP 路径 | 推迟 | v1.1.0+ |
| 功能缺口 | CUE 估计器 | 推迟 | v1.1.0+ |
| 功能缺口 | `orthog`/`endogtest`/`redundant` | 推迟 | v1.1.0+ |
| 功能缺口 | `fweight`/`pweight`/`iweight` | 未计划 | — |

### 3.4 测试覆盖

| 测试类别 | 数量 | 说明 |
|----------|------|------|
| 非 golden 单元/集成测试 | 275 | CI 可运行，不依赖 Stata |
| Golden 双跑测试 | 763 | 需本地 Stata 17，排除在 CI 外 |
| **合计** | **1,038** | 全部通过 |
| Golden 测试文件 | 126 | 覆盖所有命令族 |

### 3.5 文档体系

| 文档 | 状态 |
|------|------|
| 项目章程 (`project-charter.md`) | 稳定 |
| 架构概览 (`architecture/overview.md`) | 稳定 |
| 路线图 (`roadmap.md`) | Wave 12 完成，Wave 13 计划中 |
| 任务池 (`backlog.md`) | 同步至 Wave 12 |
| 版本发布清单 (`release-candidate-checklist.md`) | v1.0.0 全部通过 |
| 已知问题 (`known-issues.md`) | v1.0.0 视角 |
| 命令支持矩阵 (7 个命令) | 全部更新 |
| 研究档案 (`docs/research/`) | 覆盖所有已实现命令 |
| 中英文 README | 同步至 v1.0.0 |

---

## 四、版本演进轨迹

```
v0.1.0-alpha (2026-04-19)
  └── Waves 0–6: 原型验证 + 6 个命令族最小子集
      ├── regress, areg, reghdfe (minimal)
      ├── ivregress 2sls, ivreghdfe (minimal)
      ├── logit, probit, poisson, ppmlhdfe (minimal)
      ├── did_imputation, eventstudyinteract, csdid (minimal)
      ├── predict/margins (高频子集)
      └── rdrobust (Sharp RD minimal)

v0.1.5 (2026-04-23) — 增量修复

v0.2.0-beta (2026-04-29)
  └── Waves 7–9: HDFE/RD/DID 加固
      ├── 2-way cluster (reghdfe/ivreghdfe/ppmlhdfe)
      ├── savefe, separation(fe), eform/irr
      ├── rdrobust 完整带宽选择器 + fuzzy RD
      └── did_imputation controls/pretrends + csdid DR

v0.3.0-beta (2026-04-30 上午)
  └── Waves 10–11: IV 补全 + Postestimation 生态
      ├── gmm2s, liml, weakiv
      ├── predict stdp, pearson/deviance/working
      └── estat summarize/vce/ic

v1.0.0-stable (2026-04-30 下午/晚上)
  └── Wave 12: 高级 HDFE 与性能
      ├── MAP 迭代吸收内核（内存降低 2-3 数量级）
      ├── absorb(var##c.slope) 个体斜率吸收
      ├── vce(dkraay) Driscoll-Kraay 面板 HAC
      └── wagepan 真实数据验证
```

---

## 五、开发节奏统计

| 指标 | 数值 |
|------|------|
| 项目总天数 | 17 天（2026-04-13 ~ 04-30） |
| 完成的 Wave 数 | 13（Wave 0–12） |
| Git commits | 12（大量工作在工作区完成，通过 correctness-gatekeeper 迭代） |
| correctness-gatekeeper 审查轮次 | 估计 15+ 轮（跨所有 wave） |
| 最密集开发日 | 2026-04-30（Wave 10/11/12 全部在同一天完成） |
| 从 Beta 到 Stable | 同一天内（v0.3.0 上午 → v1.0.0 下午） |

---

## 六、下一步：Wave 13 (v1.1.0)

计划中的高级 HDFE 扩展与残余补全：

1. `group(var) individual(var)` FE（团队/个体固定效应）
2. 3-way+ multi-way clustering VCE
3. LSMR/LSQR 迭代算法评估与引入
4. `savefe` MAP 路径支持
5. `ivreghdfe`：`orthog` / `endogtest` / `redundant` / `partial()` / HAC standard errors
6. `ppmlhdfe`：`separation(ir/simplex/mu)` / `d()` / `d2`
7. `doffadjustments()` 精确算法（pairwise / firstpair / clusters / continuous）

优先级与拆分待 Roadmaster 重新评估。

---

## 七、关键架构决策记录（ADR）

| ADR | 主题 | 日期 | 摘要 |
|-----|------|------|------|
| ADR-0003 | LSDV 框架下多向聚类 `_cons` SE 容忍度 | 2026-04-28 | 接受 LSDV vs 迭代去均值框架下 `_cons` SE ~2-16% 结构性偏差，slope SEs 保持 < 1e-6 |

---

*本日志由 Claude Code 于 2026-04-30 根据项目文档、git 历史和 REPORT.md 自动生成。*
