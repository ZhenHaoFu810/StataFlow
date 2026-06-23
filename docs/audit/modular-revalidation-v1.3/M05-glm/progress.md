# M05 GLM 审查进度

## 审查基线

- 基线分支: `dev`
- 基线 commit: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- 审查开始: 2026-06-12

## 已完成工作

| 阶段 | 状态 | 交付物 |
|---|---|---|
| 目录结构建立 | ✅ | `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/*`、`tests/audit_v1_3/m05_glm/`、`stata/cases/audit_v1_3_m05/` |
| 审查计划 | ✅ | `task_plan.md` |
| 测试设计登记册 | ✅ | `test-design-register.md`（初始版本，已填入执行结果） |
| 支持边界核对与代码走查 | ✅ | 已阅读 `glm.py`、`compat/stata/glm.py`、`result.py`、`postestimation.py`、支持矩阵、研究档案 |
| Synthetic 双跑实验 | ✅ | S1-S8 共 13 个测试函数，全部执行并保存证据 |
| 真实数据双跑实验 | ✅ | R1-R4 共 5 个测试函数，全部执行并保存证据 |
| Property / Metamorphic Tests | ✅ | P1-P3 共 3 个测试函数，全部执行并保存证据 |
| 最小复现脚本 | ✅ | `repro_m05_glm_findings.py`（4 个 finding 的最小复现） |
| Findings | ✅ | `findings.md`（5 个 finding） |
| Summary | ✅ | `summary.md` |

## Synthetic 实验汇总

| ID | 设计目标 | 结果 |
|---|---|---|
| S1 | 手工小样本 logit | 通过，Python 与 Stata 完全一致 |
| S2 | logit ols/robust/cluster VCE | 通过；robust/cluster 的系数、SE、VCE 与 Stata 一致；发现 df_resid 和 chi2 字段语义差异 |
| S3 | 稀有事件 / 近分离 logit | 通过；两者均返回大系数，Python 收敛但系数绝对值较大 |
| S4 | probit ols/robust/cluster VCE | 通过；数值 Hessian 路径与 Stata 一致 |
| S5 | 过度离散 Poisson | 通过；ols/robust/cluster 系数、SE、VCE、deviance 与 Stata 一致 |
| S6 | 缺失值 + 共线性 | 通过；样本筛选和变量删除一致 |
| S7 | 加权 logit/poisson | 通过（使用 Stata `iweight` 与 Python aweight 归一化后比较） |
| S8 | 完全分离边界 | 通过；记录 Python 与 Stata 错误行为差异 |

## Real-Data 实验汇总

| ID | 数据来源 | 模型 | 结果 |
|---|---|---|---|
| R1 | `webuse mroz` | logit/probit `inlf` ~ `age educ kidslt6 kidsge6`, robust | 通过（放宽 VCE atol 至 1e-6 以容纳小方差元素的浮点差异） |
| R2 | `webuse fish` | Poisson `count` ~ `livebait camper persons child`, robust | 通过 |
| R3 | `sysuse nlsw88` | logit `collgrad` ~ `age grade tenure married smsa`, cluster(industry) | 通过（放宽 rtol/atol 至 1e-4） |
| R4 | `webuse ovary` | Poisson `follicles` ~ `sin1 cos1 stime`, cluster(mare) | 通过 |

## Property Tests 汇总

| ID | 性质 | 结果 |
|---|---|---|
| P1 | 行顺序不变性 | 通过 |
| P2 | 连续变量尺度变换 | 通过 |
| P3 | 冗余共线变量删除 | 通过 |

## 发现清单

- M05-GLM-001 (P1): GLM 包装器 `aweight` 与 Stata 命令不兼容
- M05-GLM-002 (P2): cluster VCE 下 `df_resid` 语义不一致
- M05-GLM-003 (P2): robust/cluster VCE 下 `f_stat` 字段语义不一致
- M05-GLM-004 (P2): 完全分离检测与错误处理不一致
- M05-GLM-005 (P3): NLSW88 行业聚类 logit VCE 2e-5 相对残余

## 未决/后续工作

- 本轮未修改产品代码；所有发现需进入后续修复阶段。
- 共享基础设施 `detect_collinear_columns` 容差问题已在 M01-M04 登记，建议全局统一处理。
- `margins` 和 `predict` 的完整双跑覆盖未在本次独立审查中深入展开；可作为 M09 Postestimation 或后续补充审查内容。
