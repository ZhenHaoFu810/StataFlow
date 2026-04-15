# Wave 4 Completion: DID / Event Study Stage B/C 收口任务

## 基本信息

- 任务名称：Wave 4 收口任务
- 执行人：Claude Code
- 审查人：Codex

## 目标

在现有 synthetic 最小实现基础上，**完成整个 Wave 4 的剩余部分并正式收口**。

本轮不是重新做 Stage A，而是补齐：

- `Stage B` 缺失的实现整理与测试登记
- `Stage C` 的真实公开数据双跑与状态回填

完成后，`Wave 4` 才能进入 `done`。

## 必做范围

必须覆盖三个命令：

- `did_imputation`
- `eventstudyinteract`
- `csdid`

每个命令都必须至少补齐：

1. 1 个真实公开数据双跑样例
2. 1 份可复核的 Stata 命令记录
3. 1 份 Python 调用记录
4. 字段级对齐说明

## 真实数据要求

优先使用本地已经落地、并能构造 staggered adoption 结构的公开数据；如确实不足，可新增一个本地公开政策面板数据集，但必须：

- 下载到本地研究目录
- 写入数据文档
- 保证可复现

至少要在文档中写清：

- 数据来源
- 下载方式
- 清洗步骤
- 处理变量定义
- 单位与时间维度
- Stata 命令
- Python 命令

## 测试要求

本轮至少新增并运行：

```powershell
python -m pytest tests/golden/test_w4_did_imputation_basic.py -v
python -m pytest tests/golden/test_w4_eventstudyinteract_basic.py -v
python -m pytest tests/golden/test_w4_csdid_basic.py -v
python -m pytest tests/golden/test_w4_did_imputation_real*.py -v
python -m pytest tests/golden/test_w4_eventstudyinteract_real*.py -v
python -m pytest tests/golden/test_w4_csdid_real*.py -v
python -m pytest tests -v
```

如果文件名不同，必须在报告里逐项列出实际命令。

## 允许修改的文件

- `src/statapy/estimators/` 下与 Wave 4 相关文件
- `tests/golden/` 下新增或调整的 Wave 4 测试
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `docs/research/public-datasets.md`
- `workspace/current-task/REPORT.md`

## 禁止事项

- 不要推进到 `Wave 5`
- 不要扩展到 `drdid`、`did2s`、`bacondecomp`、`honestdid`
- 不要引入多向 cluster、复杂 bootstrap 或图形输出
- 不要把缺失真实数据验证的命令标成 `done`
- 不要把未解释的统计偏差写成“可接受”

## 通过标准

只有同时满足以下条件，Codex 才会放行整个 Wave 4：

1. 三个命令都保留 synthetic 黄金样例并通过。
2. 三个命令都至少新增 1 个真实公开数据双跑样例并通过。
3. `docs/testing/test-case-catalog.md` 状态与实际完成情况一致。
4. `docs/backlog.md` 状态与 catalog 一致。
5. `workspace/current-task/REPORT.md` 按 Stage A/B/C 完整回报。
6. 全量测试通过。
