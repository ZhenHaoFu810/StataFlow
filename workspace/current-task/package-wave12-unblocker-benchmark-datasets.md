# Wave 12 Unblocker：性能基准数据集准备

**任务编号：** wave12-unblocker-benchmark-datasets
**日期：** 2026-04-30
**编制：** StataFlow Roadmaster
**执行者：** Claude Code
**状态：** 待执行

---

## 背景

Wave 12（Advanced HDFE & Performance）是 `docs/roadmap.md` 中 v1.0.0 对应的唯一剩余 wave，目标为解决极高维 FE 的性能瓶颈并补充高级吸收语法（MAP/LSMR 迭代内核、个体斜率吸收、Driscoll-Kraay 标准误）。

Wave 12 的入口标准之一是"已有明确的性能瓶颈数据集（>1e6 观测，>1e4 FE 级别）"。该数据集可通过 Python 合成生成，无需外部数据，是 Wave 12 启动前的最后一个阻塞项。本任务卡定义该 Unblocker 的完整执行边界。

## 目标

1. 合成生成至少 3 组性能基准数据集，覆盖不同 FE 结构和高维场景。
2. 在 Stata 17 上运行基准 `reghdfe` 命令，记录运行时间、内存占用和估计结果。
3. 在 Python 当前 LSDV 实现上运行相同模型，记录运行时间、内存占用和估计结果。
4. 生成性能基准报告，确认 LSDV 在当前规模下的瓶颈，为 MAP/LSMR 迭代内核的必要性提供量化依据。

## 为什么现在做

- v0.3.0 已发布，Waves 7-11 全部完成，无阻塞返工包，主线必须继续推进。
- Wave 12 是 roadmap 中唯一剩余 wave，对应 v1.0.0 稳定发布目标。
- 性能数据集是 Wave 12 的硬性入口标准，缺失则无法启动 Round 1（研究轮）。
- 数据集合成是低风险的独立任务，不涉及估计器内核修改，适合作为 Unblocker 快速完成。
- `/loop` 指令要求"未全部完成前不允许停止任务"，停滞等待不符合项目节奏。

## 允许修改范围

- `tests/benchmarks/` — 新增数据集生成脚本、基准测试脚本、结果记录文件
- `stata/cases/benchmark_*.do` — Stata 基准命令脚本
- `stata/output/benchmark_*.log` — Stata 执行输出日志
- `docs/research/wave12-benchmark-datasets.md` — 数据集设计与基准结果研究档案
- `workspace/current-task/REPORT.md` — 记录基准测试结果

## 禁止行为

- 不允许修改任何估计器内核代码（本阶段只准备数据集和基准测试）。
- 不允许引入新的功能性代码（如 MAP/LSMR 内核、个体斜率吸收）。
- 不允许修改 `ResultSchema` 或公共 API。
- 不允许修改 `docs/project-charter.md` 或架构原则。
- 不允许跳过 Stata-Python 双跑一致性检查（即使本阶段只关注性能，系数/SE 仍需字段级一致以确认数据集有效性）。

## 执行顺序（强制）

```
Step 1: 设计数据集规格（FE 结构、变量分布、样本量层级）
  └── Step 2: 编写 Python 合成数据生成脚本
       └── Step 3: 生成 3 组数据集并保存为 .dta
            └── Step 4: 编写 Stata 基准命令脚本（reghdfe, absorb, cluster）
                 └── Step 5: 执行 Stata 脚本并记录时间/内存/结果
                      └── Step 6: 编写 Python 基准脚本（当前 LSDV 实现）
                           └── Step 7: 执行 Python 基准并记录时间/内存/结果
                                └── Step 8: 对比 Stata-Python 估计结果一致性（系数/SE < 1e-4）
                                     └── Step 9: 生成性能基准报告
                                          └── Step 10: 更新 REPORT.md 与 INSTRUCTIONS.md，标记 Unblocker 完成
```

## 数据集规格（建议）

### Dataset A：单高维 FE（1M obs, 10K FE levels）

- N = 1,000,000
- 单 FE：`firm_id` ~ Uniform(1, 10,000)
- 连续变量：`x1`, `x2` ~ N(0, 1)，与 FE 部分相关
- 因变量：`y = 0.5*x1 + 0.3*x2 + firm_fe + eps`，其中 `firm_fe ~ N(0, 1)`，`eps ~ N(0, 1)`
- 目的：测试单高维 FE 吸收性能

### Dataset B：双向 FE（1M obs, 5K + 200 FE levels）

- N = 1,000,000
- FE1：`firm_id` ~ Uniform(1, 5,000)
- FE2：`year_id` ~ Uniform(1, 200)
- 连续变量：`x1`, `x2` ~ N(0, 1)
- 因变量：`y = 0.5*x1 + 0.3*x2 + firm_fe + year_fe + eps`
- 目的：测试双向 FE（应用微观最常见场景）

### Dataset C：不平衡面板 + 聚类（2M obs, 20K FE levels）

- N = 2,000,000
- FE1：`worker_id` ~ Uniform(1, 20,000)
- FE2：`firm_id` ~ Uniform(1, 5,000)
- 聚类变量：`cluster_id` = `firm_id`（嵌套聚类）
- 连续变量：`x1`, `x2` ~ N(0, 1)
- 因变量：`y = 0.5*x1 + 0.3*x2 + worker_fe + firm_fe + eps`
- 缺失值：随机缺失 5% 的 `x1` 和 `y`
- 目的：测试不平衡面板 + 聚类 VCE 的性能

## 最小验证要求

| 验证项 | 命令/方法 | 期望结果 | 检查文件 |
|--------|-----------|----------|----------|
| 数据集生成 | `python tests/benchmarks/generate_datasets.py` | 3 组 .dta 文件生成成功 | `tests/benchmarks/data/*.dta` |
| Stata 基准执行 | `cmd /c "cd /d stata/output && StataMP-64.exe /e do benchmark_reghdfe.do"` | 无报错，日志完整 | `stata/output/benchmark_reghdfe.log` |
| Python 基准执行 | `python tests/benchmarks/run_python_benchmark.py` | 无报错，结果保存 | `tests/benchmarks/results/python_*.json` |
| 估计一致性 | 对比 Stata 与 Python 的系数/SE | 相对误差 < 1e-4 | 控制台输出或对比脚本 |
| 性能报告 | `tests/benchmarks/generate_report.py` | Markdown 报告生成 | `docs/research/wave12-benchmark-datasets.md` |

## 交付物

1. `tests/benchmarks/generate_datasets.py` — 合成数据生成脚本
2. `tests/benchmarks/data/benchmark_*.dta` — 3 组基准数据集（>1e6 obs, >1e4 FE levels）
3. `stata/cases/benchmark_reghdfe.do` — Stata 基准命令脚本
4. `stata/output/benchmark_reghdfe.log` — Stata 执行输出
5. `tests/benchmarks/run_python_benchmark.py` — Python 基准脚本
6. `tests/benchmarks/results/stata_*.json` — Stata 时间/内存/结果记录
7. `tests/benchmarks/results/python_*.json` — Python 时间/内存/结果记录
8. `docs/research/wave12-benchmark-datasets.md` — 数据集设计与基准结果研究档案
9. `workspace/current-task/REPORT.md` — Unblocker 完成报告

## 成功标准

- [ ] 3 组数据集均满足 >1e6 观测且至少一组满足 >1e4 FE 级别
- [ ] Stata 17 基准脚本执行成功，日志完整，估计结果可解析
- [ ] Python 基准脚本执行成功，估计结果与 Stata 字段级一致（系数/SE 相对误差 < 1e-4）
- [ ] 性能基准报告生成，明确记录 LSDV 在当前规模下的时间/内存瓶颈
- [ ] `docs/research/wave12-benchmark-datasets.md` 已归档
- [ ] `workspace/current-task/REPORT.md` 已更新
- [ ] INSTRUCTIONS.md 已切换至 Wave 12 Round 1（研究轮）

## 下一步（Unblocker 完成后）

Wave 12 Round 1（研究轮）：
- MAP/LSMR 算法研究（Guimaraes-Portugal 2010）
- 个体斜率吸收语法 `absorb(var##c.slope)` 研究
- Driscoll-Kraay 标准误公式研究
- 研究档案归档至 `docs/research/wave12-map-lsmr.md`、`docs/research/wave12-slopes.md`、`docs/research/wave12-dkraay.md`
