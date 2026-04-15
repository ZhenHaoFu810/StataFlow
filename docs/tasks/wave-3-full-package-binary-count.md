# Wave 3 Full Package：`Binary / Count` 整包任务

## 基本信息

- 任务名称：Wave 3 全包推进：`logit` + `probit` + `poisson` + `ppmlhdfe`
- 所属命令族：`Binary / Count`
- 对应 backlog 条目：
  - `logit`
  - `probit`
  - `poisson`
  - `ppmlhdfe`
- 优先级：P3
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

这是一个**整包 wave 任务**。Claude Code 需要在一个连续任务中完成 Wave 3 的研究、最小实现和真实数据验证，但必须按本任务卡内部的阶段门禁推进，不能跳步。

最终目标：

1. 完成 `logit`、`probit`、`poisson` 的研究、最小实现、synthetic 对齐和真实数据对齐。
2. 完成 `ppmlhdfe` 的研究收束、最小实现、synthetic 对齐和真实数据对齐。
3. 若全部通过，则将 Wave 3 对应条目标记为 `done`，并在回报中明确建议进入下一 wave。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/roadmap.md`
6. `docs/roadmap-execution-rounds.md`
7. `docs/research/stata-source-inventory.md`
8. `docs/research/public-datasets.md`
9. `docs/research/ppmlhdfe.md`
10. 本任务卡

## 总体范围

### 必做

- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- synthetic 黄金样例
- 至少一组真实公开数据样例

### 不做

- `clogit`
- `ologit` / `oprobit`
- `nbreg`
- `zip` / `zinb`
- `margins`
- 多向 cluster
- `ppmlhdfe` 的高阶性能优化

## 执行原则

本任务虽然是一整包，但仍必须按三个内部阶段推进：

1. `Stage A: Research closure`
2. `Stage B: Minimum implementation + synthetic`
3. `Stage C: Real-data validation + hardening`

任何一个阶段未通过，不得在回报中写成整个 Wave 3 完成。

## Stage A：Research closure

### 需要完成

1. 新增或补齐以下研究档案：
   - `docs/research/logit.md`
   - `docs/research/probit.md`
   - `docs/research/poisson.md`
2. 将 `docs/research/ppmlhdfe.md` 从概要文档补成可执行研究档案。
3. 在 `docs/testing/test-case-catalog.md` 预登记以下样例：
   - `w3_logit_basic`
   - `w3_logit_real`
   - `w3_probit_basic`
   - `w3_probit_real`
   - `w3_poisson_basic`
   - `w3_poisson_real`
   - `w3_ppmlhdfe_basic`
   - `w3_ppmlhdfe_cluster`
   - `w3_ppmlhdfe_real_gravity`
4. 明确：
   - `logit` / `probit` / `poisson` 的目标函数、优化路径、收敛标准、结果字段
   - `ppmlhdfe` 与 `poisson` / `reghdfe` 的依赖关系
   - 最小兼容子集
   - 暂不支持的选项面

### 研究结论必须回答

- `logit`、`probit`、`poisson` 是否采用 MLE + IRLS / Newton 路径
- Stata 在这些命令下的 `e(ll)`、`e(N)`、`e(chi2)`、`e(V)` 如何映射
- `ppmlhdfe` 的最小实现是“Poisson + FE 吸收 + cluster”，还是更小子集
- 真实数据样例各自使用哪一组数据

## Stage B：Minimum implementation + synthetic

### `logit`

至少实现：

- `Logit(data, y, x, add_constant=True)`
- `fit(vce="ols")`
- 结果对象至少表达：
  - `nobs`
  - `df_model`
  - `ll`
  - `pseudo_r2` 或等价字段
  - `chi2`
  - 系数与协方差

### `probit`

至少实现：

- `Probit(data, y, x, add_constant=True)`
- `fit(vce="ols")`
- 与 `logit` 相同的最小结果语义

### `poisson`

至少实现：

- `Poisson(data, y, x, add_constant=True)`
- `fit(vce="ols")`
- `fit(vce="cluster", cluster="...")`
- 结果对象至少表达：
  - `nobs`
  - `df_model`
  - `ll`
  - `deviance`
  - `chi2`
  - 系数与协方差

### `ppmlhdfe`

至少实现：

- 在 HDFE 基础上支持最小 PPML 路径
- `absorb` 支持 1-2 个 FE
- `fit(vce="ols")`
- 单 `cluster`
- 默认 singleton drop 口径延续 `reghdfe`

### synthetic 必做样例

- `w3_logit_basic`
- `w3_probit_basic`
- `w3_poisson_basic`
- `w3_ppmlhdfe_basic`
- `w3_ppmlhdfe_cluster`

## Stage C：Real-data validation + hardening

### `logit` / `probit` 真实数据

至少各完成一组公开真实数据样例。优先候选：

- `Mroz` 劳动参与数据
- `Affairs` 或其他标准二元响应教学数据

若本地不存在，可下载到：

- `research/data/public/binary/`

并补数据文档。

### `poisson` 真实数据

至少完成一组公开真实数据样例。优先候选：

- `randhie`
- `docvis`
- 或其他标准计数数据集

若本地不存在，可下载到：

- `research/data/public/count/`

并补数据文档。

### `ppmlhdfe` 真实数据

至少完成一组公开真实 panel / gravity 数据样例。优先候选：

- gravity trade panel

若本地不存在，可下载到：

- `research/data/public/gravity/`

并补数据文档。

允许为了计算验证而构造派生变量，但必须在回报中明确：

- 派生规则
- Stata 与 Python 使用完全相同的样本与变量定义
- 这里的目的只是验证数值实现，不对研究识别作额外承诺

### 必须比对字段

#### `logit` / `probit`

- `nobs`
- `df_model`
- `ll`
- `chi2`
- 系数
- 标准误

#### `poisson`

- `nobs`
- `df_model`
- `ll`
- `deviance`
- `chi2`
- 系数
- 标准误
- `cluster_count`（cluster 时）

#### `ppmlhdfe`

- `nobs`
- `df_model`
- `df_a`
- `ll`
- 系数
- 标准误
- `cluster_count`
- `absorb_vars`

## 允许修改的文件

- `src/statapy/estimators/` 下 Binary / Count / HDFE 相关最小实现
- `src/statapy/results/result.py`
- `src/statapy/__init__.py`
- `src/statapy/estimators/__init__.py`
- `tests/golden/` 下 Wave 3 对应测试
- 必要的测试工具文件
- `docs/research/` 下对应研究档案
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `docs/research/public-datasets.md`
- `workspace/current-task/REPORT.md`

## 禁止事项

- 不得把未完成的子阶段写成整个 Wave 3 完成
- 不得把真实数据失败写成“可接受”直接放行
- 不得顺势扩展到 `nbreg`、`zip`、`zinb`、`margins`
- 不得修改项目章程或公共 API 原则

## 强制验证命令

至少必须运行并在回报中给出结果：

```bash
python -m pytest tests/golden/test_w3_logit_basic.py -v
python -m pytest tests/golden/test_w3_logit_real.py -v
python -m pytest tests/golden/test_w3_probit_basic.py -v
python -m pytest tests/golden/test_w3_probit_real.py -v
python -m pytest tests/golden/test_w3_poisson_basic.py -v
python -m pytest tests/golden/test_w3_poisson_real.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_cluster.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_real_gravity.py -v
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
   - 数据预处理与变量定义
   - Stata 命令
   - Python 调用
   - 对齐字段
   - Wave 3 是否可标记为完成

## Wave 3 通过标准

只有同时满足以下条件，Codex 才会认定整个 Wave 3 完成：

- `logit` synthetic + real-data 全通过
- `probit` synthetic + real-data 全通过
- `poisson` synthetic + real-data 全通过
- `ppmlhdfe` synthetic + real-data 全通过
- 全量回归测试通过
- `docs/backlog.md` 与 `docs/testing/test-case-catalog.md` 状态一致
- 无未解释的关键统计偏差

若任一项不满足，Codex 将只认定已完成的子阶段，不会放行整个 wave。
