# M04 IV / GMM 审查进度 progress.md

## 当前状态

- **模块**: M04 IV / GMM
- **审查轮次**: modular-revalidation-v1.3
- **基线 commit**: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- **完成时间**: 2026-06-13

## 已完成工作

| # | 任务 | 状态 |
|---|---|---|
| 1 | 记录基线 commit、Python、Stata、ivreghdfe/ivreg2 版本 | 完成 |
| 2 | 阅读 public API、support matrix、实现文件 | 完成（通过 explore agent） |
| 3 | 建立功能清单与风险清单 | 完成 |
| 4 | 阅读旧测试仅作覆盖地图 | 完成 |
| 5 | 编写 `test-design-register.md` | 完成 |
| 6 | 设计并实现 6 个新 synthetic 双跑 | 完成 |
| 7 | 独立编写并运行 Stata `.do` | 完成 |
| 8 | 独立运行 Python | 完成 |
| 9 | 字段级差异比较 | 完成 |
| 10 | 设计真实数据实验 | 完成 |
| 11 | 执行 metamorphic/property tests | 完成 |
| 12 | 构造最小复现 | 完成 |
| 13 | 区分产品/测试/runner/parser 根因 | 完成 |
| 14 | 写入 `findings.md` | 完成 |
| 15 | 运行现有非 golden 测试 | 完成（349 passed） |
| 16 | 模块 `summary.md` | 完成 |

## 关键结果统计

- **Synthetic 实验**: 6 个，3 PASS，3 FAIL
- **真实数据实验**: 2 个，0 PASS，2 FAIL
- **Property tests**: 3 个，全部 PASS
- **Confirmed findings**: 4 个（2 P1，2 P2）
- **共享基础设施风险**: 1 个

## 未覆盖区域

- GMM2S 独立真实数据验证（仅 synthetic S4 涉及 Hansen J）
- 多内生变量 weak-IV 诊断细节
- HAC / HC2 / HC3 / 权重 IV
- `ivregress_2sls` 的 `first` 输出字段完整核对
- LIML/Fuller 的 Stock-Yogo 临界值

## 阻塞与风险

- 无外部阻塞。
- 主要风险：弱 IV 诊断未暴露影响所有 IV 路径的可用性。
