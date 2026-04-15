# Wave 2 Full Package：`IV / GMM` 整包任务

## 基本信息

- 任务名称：Wave 2 全包推进：`ivregress 2sls` + `ivreghdfe` 最小闭环
- 所属命令族：`IV / GMM`
- 对应 backlog 条目：
  - `ivregress 2sls`
  - `ivreghdfe`
- 优先级：P2
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

这是一个**整包 wave 任务**。Claude Code 需要在一个连续任务中完成 Wave 2 的研究、最小实现和真实数据验证，但必须按本任务卡内部的阶段门禁推进，不能跳步。

最终目标：

1. 完成 `ivregress 2sls` 的研究、最小实现、synthetic 对齐和真实数据对齐。
2. 完成 `ivreghdfe` 的研究收束、最小实现、synthetic 对齐和真实数据对齐。
3. 若全部通过，则将 Wave 2 对应条目标记为 `done`，并在回报中明确建议进入下一 wave。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/roadmap.md`
6. `docs/roadmap-execution-rounds.md`
7. `docs/research/stata-source-inventory.md`
8. `docs/research/public-datasets.md`
9. `docs/research/ivreghdfe.md`
10. 本任务卡

## 总体范围

### 必做

- `ivregress 2sls`
- `ivreghdfe`
- synthetic 黄金样例
- 至少一组真实公开数据样例

### 不做

- `liml`
- `gmm`
- 过度识别/弱工具的完整工具链
- multi-way cluster
- `ppmlhdfe`
- 新的 DID 命令

## 执行原则

本任务虽然是一整包，但仍必须按三个内部阶段推进：

1. `Stage A: Research closure`
2. `Stage B: Minimum implementation + synthetic`
3. `Stage C: Real-data validation + hardening`

任何一个阶段未通过，不得在回报中写成整个 Wave 2 完成。

## Stage A：Research closure

### 需要完成

1. 将 `docs/research/ivreghdfe.md` 从占位文档补成可执行研究档案。
2. 新增或补齐 `docs/research/ivregress-2sls.md`。
3. 在 `docs/testing/test-case-catalog.md` 预登记以下样例：
   - `w2_ivregress_basic`
   - `w2_ivregress_cluster`
   - `w2_ivregress_real_card`
   - `w2_ivreghdfe_basic`
   - `w2_ivreghdfe_cluster`
   - `w2_ivreghdfe_real_panel`
4. 明确：
   - `ivregress 2sls` 的结果字段、第一阶段与第二阶段统计口径
   - `ivreghdfe` 与 `reghdfe` / `ivreg2` 的依赖关系
   - 最小兼容子集
   - 暂不支持的选项面

### 研究结论必须回答

- 2SLS 点估计与协方差的实现路径是什么
- `vce(robust)` 和单 `cluster` 是否纳入本 wave 的最小实现
- `ivreghdfe` 如何复用现有 `AbsorbingOLS` / `reghdfe` 基础
- 真实数据样例使用哪一组数据

## Stage B：Minimum implementation + synthetic

### `ivregress 2sls`

至少实现：

- `IV2SLS(data, y, x_exog, x_endog, instruments, add_constant=True)`
- `fit(vce="ols")`
- `fit(vce="cluster", cluster="...")`
- 结果对象至少表达：
  - `nobs`
  - `df_model`
  - `df_resid`
  - `r2`
  - `rmse`
  - `f_stat`
  - 系数与协方差

### `ivreghdfe`

至少实现：

- 在 HDFE 基础上支持最小 2SLS 路径
- `absorb` 支持 1-2 个 FE
- `fit(vce="ols")`
- 单 `cluster`
- 默认 singleton drop 口径延续 `reghdfe`

### synthetic 必做样例

- `w2_ivregress_basic`
- `w2_ivregress_cluster`
- `w2_ivreghdfe_basic`
- `w2_ivreghdfe_cluster`

## Stage C：Real-data validation + hardening

### `ivregress 2sls` 真实数据

至少完成一组公开真实数据样例。优先候选：

- `Card` returns-to-schooling 数据
- 其他公开可复现的教学 IV 数据

若本地不存在，可下载到：

- `research/data/public/iv/`

并补数据文档。

### `ivreghdfe` 真实数据

至少完成一组公开真实 panel 数据样例。优先候选：

- `wagepan`

允许为了计算验证而构造派生变量（如滞后工具、外生工具变量），但必须在回报中明确：

- 派生规则
- Stata 与 Python 使用完全相同的样本与变量定义
- 这里的目的只是验证数值实现，不对识别有效性作额外承诺

### 必须比对字段

- `nobs`
- `df_model`
- `df_resid`
- `r2`
- `rmse`
- `f_stat`
- 系数
- 标准误
- `cluster_count`（cluster 时）
- `absorb_vars`（`ivreghdfe` 时）

## 允许修改的文件

- `src/statapy/estimators/` 下 IV / HDFE 相关最小实现
- `src/statapy/results/result.py`
- `src/statapy/__init__.py`
- `src/statapy/estimators/__init__.py`
- `tests/golden/` 下 Wave 2 对应测试
- 必要的测试工具文件
- `docs/research/` 下对应研究档案
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `docs/research/public-datasets.md`
- `workspace/current-task/REPORT.md`

## 禁止事项

- 不得把未完成的子阶段写成整个 Wave 2 完成
- 不得把真实数据失败写成“可接受”直接放行
- 不得顺势扩展到 `liml`、`gmm`、多向 cluster、`ppmlhdfe`
- 不得修改项目章程或公共 API 原则

## 强制验证命令

至少必须运行并在回报中给出结果：

```bash
python -m pytest tests/golden/test_w2_ivregress_basic.py -v
python -m pytest tests/golden/test_w2_ivregress_cluster.py -v
python -m pytest tests/golden/test_w2_ivregress_real_card.py -v
python -m pytest tests/golden/test_w2_ivreghdfe_basic.py -v
python -m pytest tests/golden/test_w2_ivreghdfe_cluster.py -v
python -m pytest tests/golden/test_w2_ivreghdfe_real_panel.py -v
python -m pytest tests -v
```

若最终采用不同测试文件名，需在回报中解释并给出实际命令。

## 回报要求

回报必须分三段写：

1. `Stage A`
   - 研究档案改动
   - 数据与样例登记
   - 最小实现边界
2. `Stage B`
   - 实现文件
   - synthetic 对齐结果
   - 尚存统计风险
3. `Stage C`
   - 真实数据来源
   - 数据预处理与工具变量定义
   - Stata 命令
   - Python 调用
   - 对齐字段
   - Wave 2 是否可标记为完成

## Wave 2 通过标准

只有同时满足以下条件，Codex 才会认定整个 Wave 2 完成：

- `ivregress 2sls` synthetic + real-data 全通过
- `ivreghdfe` synthetic + real-data 全通过
- 全量回归测试通过
- `docs/backlog.md` 与 `docs/testing/test-case-catalog.md` 状态一致
- 无未解释的关键统计偏差

若任一项不满足，Codex 将只认定已完成的子阶段，不会放行整个 wave。
