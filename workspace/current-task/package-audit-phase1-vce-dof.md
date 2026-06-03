# Package: Audit Phase 1 — 数学正确性审查

**Wave:** Audit → v1.1.0 前置研究
**日期:** 2026-04-30
**状态:** 进行中
**类型:** 只读审查（不修改任何代码）

---

## 背景

StataFlow v1.0.0 已发布（Waves 0-12 全部完成，1,040 tests pass）。在进入 v1.1.0 新功能开发之前，必须对现有 15 个 estimator 的数学实现进行系统性审查。

探索审计发现 7 个高优先级风险项：
1. CSDID DR SE 偏差达 20%（全项目最大 golden test 容差）
2. _cons SE 2-way cluster 偏差 2-16%（ADR-0003 文档化，但未根本解决）
3. PPMLHDFE cluster VCE 缺少 (N-1)/(N-k) 小样本修正
4. IV2SLS 使用渐近 VCE（无小样本修正）
5. Probit VCE 使用数值 Hessian（唯一子类 override）
6. GMM2S 权重矩阵奇异回退路径
7. 多内生变量 weakiv 未完整实现（idstat = np.nan）

单一事实来源：`docs/audit/v1.0.0-comprehensive-audit-plan.md`

---

## 目标

对 7 个核心 estimator 进行三维度数学审查：

### 维度 1：VCE 公式审查（A1.1 - A1.4）
- A1.1：小样本修正一致性（OLS/FE/AbsorbingOLS/IV2SLS/IVAbsorbingOLS/GLM/PPMLHDFE）
- A1.2：PSD fix 应用范围与层级
- A1.3：T-matrix _cons 恢复与方差
- A1.4：Driscoll-Kraay VCE 数学验证

### 维度 2：DoF 计算审查（A2.1 - A2.2）
- A2.1：df_a 计算（nested FE、singleton、keepsingletons、noconstant、slopes）
- A2.2：df_model 与 df_resid（跨 estimator 一致性）

### 维度 3：特殊路径审查（A3.1 - A3.4）
- A3.1：Probit 数值 Hessian VCE
- A3.2：GMM2S 权重矩阵奇异回退
- A3.3：RD Robust 带宽选择器收敛
- A3.4：IV Weak-Identification 诊断

---

## 为什么现在做

- Phase 1 是零风险起点：只读审查，无代码修改，无回归风险
- Phase 1 结果门槛 Phase 2（重构）和 Phase 3（真实数据验证）
- 如果 Phase 1 发现 VCE bug，必须在重构前修复，防止错误被固化
- Top 4 最高风险项全部属于 Phase 1 范围
- Roadmaster 原则："数学正确性 > 路线一致性 > 文档同步 > 完整度 > 发布节奏"

---

## 允许修改范围

**仅允许写入：**
- `docs/audit/vce-formula-audit.md` — VCE 公式审查报告
- `docs/audit/dof-audit.md` — DoF 计算审查报告
- `docs/audit/special-paths-audit.md` — 特殊路径审查报告
- `workspace/current-task/REPORT.md` — 更新审查进度

**允许读取：**
- `src/stataflow/estimators/*.py` — 所有 estimator 源代码
- `research/vendor/stata_community/*/` — Stata 社区命令源码
- `tests/golden/test_*.py` — Golden test 容差记录
- `docs/command-support-matrix/*.md` — 支持矩阵
- `docs/adr/*.md` — 架构决策记录

---

## 禁止行为

- **禁止修改任何 `.py` 文件** — 这是只读审查
- **禁止修改任何测试文件**
- **禁止修改 `docs/` 下除 `docs/audit/` 以外的任何文件**
- **禁止运行 Stata** — 审查基于源码阅读和已有 golden test 证据
- **禁止引入新依赖或修改配置**
- **禁止跳过任何一个 estimator 的审查**

---

## 执行顺序（强制）

```
Step 1: VCE 公式审查 — 小样本修正
  └── 逐个 estimator 追踪 VCE 计算路径，记录每个修正因子
       └── 与 Stata 官方文档/源码对照
            └── Step 2: VCE 公式审查 — PSD fix 应用范围与层级
                 └── 跟踪所有 fix_psd / fix_psd_reghdfe 调用
                      └── 对照 reghdfe.mata 源码
                           └── Step 3: VCE 公式审查 — T-matrix _cons 恢复与方差
                                └── 审查所有 T-matrix 构建和 _cons override 路径
                                     └── Step 4: VCE 公式审查 — Driscoll-Kraay 数学
                                          └── 验证 Bartlett kernel, bandwidth, DOF adjustment
                                               └── Step 5: DoF 计算审查
                                                    └── 验证 df_a, df_model, df_resid 在所有路径下
                                                         └── Step 6: 特殊路径审查
                                                              └── Probit Hessian → GMM fallback → RD bandwidth → Weak-IV
                                                                   └── Step 7: 撰写审查报告 + 更新 REPORT.md
```

---

## 最小验证要求

| 验证项 | 方法 | 通过标准 |
|--------|------|---------|
| VCE 公式审查 | 逐 estimator 源码追踪 + Stata 文档/源码对照 | 每个 estimator 的每个 VCE 类型的修正因子都已解释 |
| PSD fix 审查 | 追踪所有 fix_psd 调用 + 对照 reghdfe.mata | 确认操作层级和 slope restore 策略正确 |
| _cons 方差审查 | 验证 delta-method 公式 + T-matrix 全传播 | 确认 OLS/robust/cluster/DK 下 _cons 方差来源 |
| DK VCE 审查 | 逐行验证 Bartlett kernel + bandwidth + DOF | 与 reghdfe Mata 源码一致 |
| DoF 审查 | 验证所有 df_a / df_model / df_resid 计算 | 每个 estimator 与 Stata e(df_*) 输出一致 |
| 特殊路径审查 | 逐路径源码追踪 + Stata 原理对照 | 每个路径的数学正确性已验证或偏差已量化 |

---

## 交付物

1. `docs/audit/vce-formula-audit.md` — VCE 公式审查报告
2. `docs/audit/dof-audit.md` — DoF 计算审查报告
3. `docs/audit/special-paths-audit.md` — 特殊路径审查报告
4. `workspace/current-task/REPORT.md` — Phase 1 完成报告

---

## 成功标准

- [ ] 所有 7 个 estimator 的 VCE 公式已审查，修正因子已解释
- [ ] 所有 PSD fix 调用的数学正确性已验证
- [ ] T-matrix _cons 恢复路径（普通 OLS、斜率吸收、robust、cluster）已审查
- [ ] Driscoll-Kraay VCE（Bartlett 核、带宽、DOF 修正）已验证
- [ ] 所有 df_a / df_model / df_resid 计算路径已审查
- [ ] Probit 数值 Hessian、GMM 奇异回退、RD 带宽、Weak-IV 已审查
- [ ] 所有发现的偏差已量化、文档化、分级（P0/P1/P2）
- [ ] 3 份审查报告已写入 `docs/audit/`
- [ ] REPORT.md 已更新
- [ ] 审查结论可支撑 Phase 2（重构）和 Phase 3（真实数据验证）的优先排序
