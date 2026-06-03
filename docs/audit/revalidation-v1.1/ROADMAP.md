# StataFlow v1.0.0 修缮路线图

**生成日期**: 2026-06-03  
**基础**: Phase 1 源码审查（90 项问题）+ Phase 2 真实数据双跑验证（18 项新问题）  
**总计**: **108 项问题**（6 Blocker + 19 Critical + 42 Major + 41 Minor）  
**已修复**: **13 项**（PANEL-01, NEW-IV-01, LINEAR-01, GLM-01, GLM-02, RD-01, DID-004, DID-001, DID-011, DID-002, IV-02, DID-005, RD-02）  
**待修复**: **95 项**

---

## 1. 版本里程碑

### v1.0.1 — 热修复（预计 1-2 周）
目标：修复所有 Blocker 和最高优先级 Critical，使核心功能可用。

### v1.1.0 — 功能补齐（预计 4-6 周）
目标：修复剩余 Critical 和 Major，使全部命令族达到生产可用状态。

### 后续版本
目标：修复 Minor 问题，完善边缘 case，视实际需求迭代（v1.1.1, v1.2.0 等）。当前不做远期版本号承诺。

---

## 2. 已修复问题（Phase 2 期间）

| # | 问题 | 命令族 | 修复文件 | 验证状态 |
|---|------|--------|----------|----------|
| 1 | **PANEL-01**: MAP 路径完全崩溃（stats NameError + UnboundLocalError） | Panel | `absorbing_ols.py` | ✅ 修复后 MAP 路径成功执行，数值与 LSDV/Stata 完全一致 |
| 2 | **NEW-IV-01**: 2-way cluster weakiv 字符串拼接崩溃 | IV | `iv.py` | ✅ `.astype(str) + "__"` → list comprehension |
| 3 | **LINEAR-01**: `detect_collinear_columns` n<p 时错误丢弃独立列 | Linear | `_vce_utils.py` | ✅ 新增宽矩阵 rank-increment 回归测试；相关 IV/HDFE/factor 测试子集通过 |
| 4 | **GLM-01**: Logit/Poisson robust VCE 缺失 `n/(n-1)` | GLM | `glm.py` | ✅ 新增 robust VCE 修正测试；Logit/Poisson robust+cluster Stata golden 通过 |
| 5 | **GLM-02**: PPMLHDFE `eform` z/p 计算错误 | GLM | `ppmlhdfe.py` | ✅ eform 保留 raw-scale z/p；PPMLHDFE eform Stata golden 覆盖 z/p 并通过 |
| 6 | **RD-01**: `rdrobust` 默认未启用 `bwselect="mserd"` | RD | `rdrobust.py` | ✅ core 和 wrapper 默认等价于 `bwselect="mserd"`；RD 单元测试与 bandwidth-selector Stata golden 通过 |
| 7 | **DID-004**: `did_imputation allhorizons=True` 完全未生效 | DID | `did_imputation.py` | ✅ allhorizons 现在新增 Stata 风格 calendar omitted horizons（如 `tau1980`-`tau1988`）；DID wrapper 与 synthetic Stata golden 通过 |
| 8 | **DID-001 + DID-011**: `csdid()` wrapper 返回值阻断二次分析，pretrend 返回 dict/NaN | DID | `did.py`, `csdid.py` | ✅ wrapper 默认返回 fitted `CSDID`，显式 `aggtype` 返回 `ResultSchema`；`estat_pretrend()` 返回 ResultSchema 且修复 numpy integer 事件键 |
| 9 | **DID-002**: `csdid` kwargs 硬拒绝 Stata 合法参数 | DID | `did.py`, `csdid.py` | ✅ `notyet=True` 在 `method="reg"` 下真实支持；`window/minn/gtcontrol/longdiff` 改为显式 `NotImplementedError` |
| 10 | **IV-02**: `fix_psd_reghdfe` 错误假设 `_cons` 存在 | IV | `_vce_utils.py`, `iv.py` | ✅ PSD helper 支持 `constant_index=None`；ivreghdfe 无 `_cons` 的 reported VCE 不再把最后一个 slope 当 constant |
| 11 | **DID-005**: CSDID 不平衡面板 ATT(g,t) NaN 静默传播 | DID | `csdid.py` | ✅ `_fit_reg` 跳过 treated/control 在 t/base 任一为空的 ATT(g,t)，不再输出 NaN 系数 |
| 12 | **RD-02**: Cluster VCE 带宽选择未考虑聚类结构 | RD | `rdrobust.py` | ✅ 带宽选择阶段传入 cluster id 并使用 cluster sandwich 权重；pilot range 与 Stata cutoff 口径对齐；RD cluster real-data Stata golden 通过 |

---

## 3. v1.0.1 热修复清单（P0 — 立即修复）

### 3.1 Blocker（剩余 3 项）

| 优先级 | 问题 | 命令族 | 影响 | 预计工作量 |
|--------|------|--------|------|-----------|
### 3.2 Critical（最高优先级 6 项）

| 优先级 | 问题 | 命令族 | 影响 | 预计工作量 |
|--------|------|--------|------|-----------|

### 3.3 热修复依赖关系

```
DID-001 ──┬──→ 需修改 csdid() wrapper 返回值类型
          └──→ 依赖 DID-011（pretrend 返回类型统一）

DID-002 ──→ 需扩展 kwargs 白名单（notyet/window/gtcontrol）

IV-02 ────┬──→ 需修改 fix_psd_reghdfe 识别 _cons 的逻辑
          └──→ 或让 ivreghdfe 明确报告 _cons 位置

LINEAR-01 ──→ 已修复：detect_collinear_columns 改为按列顺序的 rank-increment 检测
          └──→ 影响所有使用共享共线性检测的估计器，已用 focused regression 覆盖
```

---

## 4. v1.1.0 功能补齐清单（P1 — 短期修复）

### 4.1 Critical（剩余 13 项）

| # | 问题 | 命令族 | 说明 |
|---|------|--------|------|
| 11 | DID-003 | DID | CSDID DR 无 never-treated 时崩溃 |
| 12 | GLM-02 | GLM | PPMLHDFE eform（已在 P0，此处为完整列表） |
| 13 | RD-03 | RD | rdplot 协变量调整使用全局 OLS + bin 选择差异 |
| 14 | LINEAR-02 | Linear | 2-way cluster 分隔符 `__` 冲突 |
| 15 | LINEAR-03 | Linear | `regress` wrapper 不支持 `vce(cluster var)` 语法 |
| 16 | LINEAR-04 | Linear | 三路因子交互被硬拒绝 |
| 17 | IV-01 | IV | GMM2S cluster VCE 主/fallback 路径不一致 |
| 18 | IV-03 | IV | ivregress 2sls 全场景 z-统计量（应为 t for ols） |
| 19 | PANEL-02 | Panel | MAP 未收敛静默继续 |
| 20 | PANEL-03 | Panel | savefe + slopes 错位 |
| 21 | DID-008 | DID | did_imputation pretrends 未用 cluster-robust VCE |
| 22 | DID-006+007 | DID | cluster_var 始终 None，df_resid 计数错误 |
| 23 | NEW-DID-002 | DID | `_can_impute` 样本筛选与 Stata 严重不符 |
| 24 | NEW-DID-003 | DID | cluster SE 与非 cluster SE 数值完全一致 |
| 25 | NEW-IV-02~05 | IV | F-stat 数值不稳定、first-stage df 错误、2-way rank deficiency、df_resid 公式 |
| 26 | NEW-RD-01~03 | RD | bin 选择算法、covs 警告、cluster 双重问题 |
| 27 | NEW-LINEAR-01~04 | Linear | Wald F 不稳定、noconstant F-stat 跳过、predict 未暴露、分隔符冲突 |

### 4.2 Major（38 项中优先级较高的）

| # | 问题 | 命令族 | 说明 |
|---|------|--------|------|
| 28 | DID-010 | DID | eventstudyinteract 不支持 weights/covariates |
| 29 | IV-05 | IV | 多内生变量 weakiv 完全未实现 |
| 30 | GLM-03+04 | GLM | wrapper 返回 model + weight 支持 |
| 31 | PANEL-04+09 | Panel | MAP 支持 slopes + predict xbd |
| 32 | PANEL-11 | Panel | df_a 简化算法 → pairwise mobility groups |

---

## 5. v1.2.0+ 深度优化（P2/P3）

- 全部 Minor 级别问题（41 项）
- `level()`/`eform`/`noci`/`nopvalues` 等展示层参数支持
- 三路及以上因子交互完整实现
- RD bin 选择算法与 Stata 完全对齐
- `xtreg_fe` RMSE 定义与 Stata `e(sigma)` 对齐
- savefe 固定效应数值体系文档化

---

## 6. 跨命令族修缮建议顺序

### 第 1 波（v1.0.1，1-2 周）
1. **LINEAR-01**: 修复 collinearity 检测（影响所有估计器）— 已完成
2. **GLM-01**: 添加 `n/(n-1)`（一行修复，影响 Logit/Poisson）— 已完成
3. **GLM-02**: 修复 PPMLHDFE eform z/p（一行修复）— 已完成
4. **RD-01**: 默认 `bwselect='mserd'`（一行修复）— 已完成
5. **DID-004**: 修复 `allhorizons` 参数传递 — 已完成
6. **DID-001 + DID-011**: 统一 csdid 返回值类型 — 已完成
7. **DID-002**: 扩展 kwargs 白名单 — 已完成
8. **IV-02**: 修复 fix_psd_reghdfe 的 _cons 假设 — 已完成

### 第 2 波（v1.1.0，前 2-3 周）
9. **DID-003 + DID-005**: CSDID 稳定性（never-treated + NaN 处理）— DID-005 已完成
10. **RD-02**: Cluster VCE 带宽选择 — 已完成
11. **IV-01**: GMM2S cluster VCE 一致性
12. **IV-03**: z→t 统计量切换
13. **NEW-DID-002+003**: did_imputation 样本筛选 + cluster SE

### 第 3 波（v1.1.0，后 2-3 周）
14. **PANEL-02+03**: MAP 收敛检测 + savefe/slopes
15. **GLM-03+04**: wrapper 返回 model + weight
16. **DID-010**: eventstudyinteract 补齐
17. **LINEAR-02+03+04**: cluster 分隔符、语法兼容、因子交互
18. **NEW-IV-02~05 + NEW-RD-01~03 + NEW-LINEAR-01~04**

### 后续版本（视需求迭代）
19. 全部 Minor 级别问题
20. 展示层参数（level/eform/noci/nopvalues）
21. 三路及以上因子交互
22. RD bin 选择算法完全对齐

---

## 7. 风险与依赖

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `fix_psd_reghdfe` 修复可能引入新的 VCE 偏差 | IV/Panel 所有 cluster 场景 | 增加 regression test 覆盖 1-way/2-way/cluster+slopes |
| `detect_collinear_columns` 重写可能影响现有测试 | 所有估计器 | 在修复前运行全量测试基线 |
| csdid 返回值类型变更破坏下游代码 | DID 用户 | 提供迁移文档，保留旧 API 作为 deprecated 别名 |
| did_imputation `_can_impute` 逻辑重对齐可能改变样本量 | DID 结果可比性 | 与 Stata 逐观测对比样本标记 |

---

## 8. 建议的 git 工作流

```
main (v1.0.0)
  ├── hotfix/v1.0.1-linear-collinearity     → LINEAR-01
  ├── hotfix/v1.0.1-glm-robust-se           → GLM-01
  ├── hotfix/v1.0.1-ppmlhdfe-eform          → GLM-02
  ├── hotfix/v1.0.1-rd-bwselect-default     → RD-01
  ├── hotfix/v1.0.1-did-allhorizons         → DID-004
  ├── hotfix/v1.0.1-did-csdid-return        → DID-001/011
  ├── hotfix/v1.0.1-did-kwargs              → DID-002
  └── hotfix/v1.0.1-iv-psd-fix              → IV-02
        ↓
    release/v1.0.1  (合并全部 hotfix)
        ↓
    develop/v1.1.0  (功能补齐)
        ↓
    release/v1.1.0
        ↓
    develop/v1.2.0  (长期优化)
```

---

*路线图版本: 1.0*  
*关联文件: summary.md, 6×REV-*.md, 6×VAL-*.md, 5×NEW-*.md*
