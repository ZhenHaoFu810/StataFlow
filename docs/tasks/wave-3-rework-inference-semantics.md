# Wave 3 Rework：`Binary / Count` 推断语义返工

## 基本信息

- 任务名称：Wave 3 返工：修正 MLE 推断分布、probit sandwich score、`ppmlhdfe` VCE 语义
- 所属命令族：`Binary / Count`
- 优先级：P0
- 执行人：Claude Code
- 审查人：Codex

## 返工背景

Wave 3 当前 **测试全绿但不予放行**。阻塞原因不是系数不对，而是推断层统计口径存在错误：

1. `logit` / `probit` / `poisson` 把 MLE 推断做成了 `t` 分布，而不是 Stata 的 `z` 分布。
2. `probit` 的 robust / cluster meat 没有使用正确的 score。
3. `PPMLHDFE.fit(vce="ols")` 的实现语义与命名不一致。

详细问题见：

- `workspace/current-task/review-wave-3-codex.md`

## 必读文档

1. `workspace/current-task/review-wave-3-codex.md`
2. `docs/research/logit.md`
3. `docs/research/probit.md`
4. `docs/research/poisson.md`
5. `docs/research/ppmlhdfe.md`
6. `docs/tasks/wave-3-full-package-binary-count.md`

## 任务目标

### A. 修正 MLE 推断分布

对以下命令：

- `logit`
- `probit`
- `poisson`

将：

- `p_value`
- `ci_low`
- `ci_high`

改为基于 **标准正态分布** 计算，而不是 `t` 分布。

### B. 修正 `probit` 的 robust / cluster score

在 `Probit._compute_vce()` 中：

- robust meat 必须使用正确的 probit 观测得分
- cluster meat 必须使用按 cluster 聚合的正确 probit score

不得继续使用 `X' (y - mu)` 的简化形式。

### C. 收口 `ppmlhdfe` 的 `vce="ols"` 语义

二选一，但必须明确完成：

1. 严格实现 `vce="ols"` 的 conventional VCE；或
2. 重构 API / 文档 / 元数据，使默认稳健语义与 `vce="ols"` 不再混淆。

不允许继续保持“名字叫 ols，代码跑 robust”的状态。

## 允许修改的文件

- `src/statapy/estimators/glm.py`
- `src/statapy/estimators/ppmlhdfe.py`
- `src/statapy/results/result.py`
- `tests/golden/` 下 Wave 3 相关测试
- 必要的测试工具文件
- `docs/research/ppmlhdfe.md`
- `workspace/current-task/REPORT.md`

## 必须新增或补强的测试

至少新增以下一类：

- `probit` 的 robust 或 cluster golden test
- `logit/probit/poisson` 的 `p_value` / `ci` 字段断言
- `ppmlhdfe` 的 `vcetype` / VCE 语义断言

建议三类都补。

## 强制验证命令

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

如新增新的 golden 测试文件，必须在回报中列出并实际运行。

## 回报要求

回报必须明确说明：

1. MLE 命令的 `z` 分布推断如何实现
2. `probit` score 的公式与实现对应关系
3. `ppmlhdfe` 最终选择了哪种 `vce="ols"` 语义收口方案
4. 哪些测试是这次新增的，覆盖了哪些之前未覆盖的字段
5. 全量测试结果

## 通过标准

只有同时满足以下条件，Codex 才会重新考虑放行 Wave 3：

- `logit` / `probit` / `poisson` 的推断分布改为 `z`
- `probit` 的 robust / cluster sandwich 实现与研究档案一致
- `ppmlhdfe` 的 `vce="ols"` 命名与实现不再冲突
- 新增测试确实覆盖了这次发现的问题
- 全量回归测试通过
