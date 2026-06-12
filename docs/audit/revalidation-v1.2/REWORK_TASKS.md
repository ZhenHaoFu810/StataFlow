# Revalidation v1.2 返工任务

目标：关闭 2026-06-12 验收发现，并使干净 checkout 可以独立完成测试和 Stata 验证。

## P1-1 Factor estimation sample

关联：`FVAR-001`、A-001。

- 为 factor parser 提供“提取表达式底层变量”的结构化接口。
- estimation sample 必须包含 `i.g##c.x` 中的 `g`、`x`，以及所有多路交互原子。
- wrapper 不得用表达式字符串冒充真实列名。
- 添加缺失连续交互变量改变 categorical base 的回归测试。
- 与 Stata 17 对比系数名称、base/omitted 标记、常数和 N。

验收：同一最小案例中 Stata 与 Python 都以 2 为 base，不得出现 Python 的 `2.g` 系数。

## P1-2 String factor semantics

关联：`FVAR-002`、A-002。

- 所有 `i.string_var`、`ib#.string_var`、`o#.string_var` 均应在 compat layer 明确拒绝。
- 错误信息说明需要用户预先编码为数值变量。
- 删除“string without explicit base allowed”的错误测试，改为 Stata `r(109)` 对应负测试。

## P1-3 ResultSchema invariants

关联：`SCHEMA-001`、A-003。

强制验证：

- `len(coefficients) == len(row_names)`；
- VCE 行数等于列数；
- 每一行长度一致；
- coefficient names 与 row_names 按顺序完全一致；
- sample mask 长度等于 `n_input_rows`；
- `sum(sample_mask) == nobs`（mask 非空时）；
- `from_dict()` 和 `from_json()` 对非空结果执行校验。

补充真正会先失败的单元测试，不得只测试 estimator 当前恰好生成的合法对象。

## P1-4 DID sample contract

关联：`DID-004`、A-004。

- 将最终 `effective_sample_mask` 映射回原始输入行位置。
- `autosample`、window、minn、不可插补处理后均满足 mask 契约。
- 增加 `sum(sample_mask) == nobs` 回归测试。

## P1-5 Reproducible DID golden fixtures

关联：`EVID-001`、A-005。

- 静态日志测试必须改为测试内调用 `StataRunner` 动态生成，或把可公开、稳定的 golden artifact 放入不被忽略的验证目录。
- 测试不能依赖 `stata/output/` 中的本机残留文件。
- 在一个无 `stata/output/*.log` 的干净副本/worktree 中运行四个 DID real-data tests。

验收：删除全部 ignored output 后，测试仍能自行生成证据并通过。

## P1-6 CSDID cluster sample

关联：A-006。

- cluster 变量必须参与 missing screening。
- 校验 cluster 在 unit 内保持一致；否则明确报错。
- 点估计、IF、nobs、sample mask 和 cluster count 必须来自同一估计样本。
- 添加 missing cluster 和 varying cluster-within-unit 测试，并进行 Stata 双跑。

## P1-7 DID first_treat semantics

关联：`DID-001`、A-007。

- 以目标 Stata 命令的原生输入语义为准，明确 missing、0、负值分别代表什么。
- Python 和 Stata 双跑必须使用相同数据，不得在 Stata `.do` 中临时改码而 Python 使用另一套码。
- 如果需要便利编码，必须在 compat wrapper 显式、文档化地转换，而不是 estimator 静默解释。
- 覆盖 time 包含负值、0 和正值的面板。

## P1-8 Remaining statistical alignment

关联：`VCE-002`、`VCE-003`、`VCE-004`、`RD-002`。

- 完成 HDFE MAP/2-way cluster 的 Stata 对表，不得保留 0.5%、3% 或 20% 容差。
- RD qsmv 应匹配 Stata 17 的 56 bins；若无法匹配，状态必须改回 Open/Known limitation，不能标 Fixed。
- 所有关闭项遵守 `<1e-6`，除非用户正式修改项目验收标准。

## P1-9 HDFE fit statistics and cluster VCE regression

关联：A-011。

- 还原并逐步验证 `AbsorbingOLS` 的 `df_a`、`df_resid`、RMSE denominator 和 adjusted R² 定义。
- 分开处理 areg/reghdfe、nested FE、1-way cluster、2-way cluster、LSDV/MAP，不能用一个未经证明的 `rmse_df` 公式覆盖全部路径。
- 复核 `_cluster_k_eff()` 的 nested adjustment。
- 复核 `_cons` 的 influence mapping 和 PSD 修正顺序。
- 不得恢复旧的 3%、20% 宽容差；应修复实现或保持问题 Open。

最低回归集：

```powershell
pytest tests/golden/test_p3_reghdfe_cluster.py -v
pytest tests/golden/test_p3_reghdfe_real_panel.py -v
pytest tests/golden/test_w7_reghdfe_2way_cluster.py -v
pytest tests/golden/test_w7_reghdfe_2way_cluster_real.py -v
```

验收：adjusted R²、RMSE 和所有 coefficient SE 均满足 `<1e-6`。

## P2-1 Factor-aware margins

关联：`GLM-003`。

- 设计并保留 factor-expansion 元数据。
- factor dummy 使用离散变化，continuous 使用导数。
- 添加 logit/probit/poisson 的 synthetic 与 Stata margins 双跑。

## P2-2 Delivery hygiene

- 删除纯临时输出和构建目录。
- 决定验证脚本、probe 和新增 golden tests 哪些属于正式资产。
- 将正式文件纳入 Git，临时文件纳入 `.gitignore` 或删除。
- 更新 `REMEDIATION_REPORT.md`，不得把仍有超容差或不可重现证据的项目标为 Fixed。

## 最终重新验收

必须从干净工作树/新 worktree 执行：

```powershell
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/benchmarks/
pytest tests/golden/ -v
python -m compileall -q src/stataflow
python -m pip wheel . --no-deps -w dist_acceptance
git diff --check
```

另需逐项运行本文件新增的最小复现，并记录 Stata 17 命令、输出和最大相对误差。
