# Revalidation v1.2 开发验收报告

验收日期：2026-06-12  
验收对象：当前 `dev` 工作树中的未提交修缮  
结论：**不通过，需返工后重新验收**

## 总体判断

本轮开发修复了多项原始问题，非 golden 测试、编译和 wheel 构建均能通过；但当前状态仍不满足“32 项问题全部完成”或“严格复现 Stata 17”的验收条件。

主要原因：

1. 修缮报告明确保留 `VCE-002`、`VCE-003`、`VCE-004`、`GLM-003` 为 Open。
2. `FVAR-001`、`FVAR-002`、`SCHEMA-001`、`DID-004` 和 `EVID-001` 被标为 Fixed，但验收复现证明尚未关闭。
3. `RD-002` 仍有约 5% 的 Stata 差异，却被标为 Fixed，与项目 `<1e-6` 验收标准冲突。
4. CSDID 自定义聚类仍未遵守 cluster 缺失值必须退出 estimation sample 的硬规则。
5. 完整 golden 当前实际有 10 项失败，修缮报告中的“812 passed”已经不是当前工作树的真实结果。

## 验收发现

### A-001 P1：FVAR-001 在交互项中仍然存在

位置：

- `src/stataflow/compat/stata/linear.py:59`
- `src/stataflow/compat/stata/factor_variables.py:403`

wrapper 把 `x=["i.g##c.x"]` 原样加入 `screen_vars`。`expand_factor_terms()` 只保留与真实列名完全匹配的项，因此没有从表达式中提取底层变量 `g` 和 `x`。

最小数据中，`g=1` 只出现在 `x` 缺失的行。Python 仍以 1 为 base，返回：

```text
['2.g', '3.g', 'x', '2.g#c.x']
```

Stata 17 在同一有效样本上以 2 为 base，报告 `3.g`、`x`、`3.g#c.x` 和 `_cons`。因此参数化仍错误。

### A-002 P1：FVAR-002 未按 Stata 语义修复

位置：

- `src/stataflow/compat/stata/factor_variables.py:206`
- `tests/test_factor_variables.py:506`

当前只拒绝字符串变量上的显式 `ib#.`/`o#.`，仍明确允许 `i.string_var`。

Stata 17 实测：

```text
s: string variables may not be used as factor variables
STRING_RC=109
```

项目目标是 Stata-compatible command layer，不能以“用户可以先 encode”为理由静默扩展 `i.strvar` 语义。

### A-003 P1：SCHEMA-001 的 invariant 校验仍不成立

位置：`src/stataflow/results/result.py:125-160`

已复现：

- 2 个 coefficients 配 1 个 `row_name` 和 `1x1` VCE，`validate()` 不报错。
- `[[1, 0], [0]]` 这种 ragged matrix 不报错。
- 名称检查使用集合，不能保证 VCE 行顺序与 coefficients 顺序一致。
- `from_dict()`/`from_json()` 不调用校验。

修缮报告声称新增 `test_result_schema_validate`，但当前 `tests/test_result_schema.py` 没有该测试，并保留了一个 1 个系数配 2×2 VCE 的序列化样例。

### A-004 P1：DID-004 的 sample mask 与 nobs 不一致

位置：

- `src/stataflow/estimators/did_imputation.py:130`
- `src/stataflow/estimators/did_imputation.py:420-424`

实现把初始 missing-screening mask 写入结果，但 `nobs` 使用后续 `effective_sample_mask`。当 `autosample` 剔除不可插补观测时，两者不一致。

验收复现：

```text
n_input_rows = 5
nobs = 4
sum(sample_mask) = 5
```

这违反 `sum(sample_mask) == sample.nobs` 的结果契约。

### A-005 P1：EVID-001 仍依赖本机不可移植状态

位置：

- `.gitignore:35`
- `tests/golden/test_w4_csdid_real_ezunem.py:12,80`
- `tests/golden/test_w4_did_imputation_real_ezunem.py:11,51`
- `tests/golden/test_w4_eventstudyinteract_real_ezunem.py:12,94`
- `tests/golden/test_w9_csdid_dr_real_ezunem.py:11,77`

这些测试直接读取 `stata/output/*.log`。整个 `stata/output/` 被 `.gitignore` 排除，相关日志不受 Git 管理，测试本身也没有生成 fixture。

因此完整 golden 在当前机器通过，只能证明本机残留日志存在，不能证明干净 checkout 可重现。EVID-001 不能标记为 Fixed。

### A-006 P1：CSDID custom cluster 未正确筛除 cluster 缺失值

位置：`src/stataflow/estimators/csdid.py:116,406`

`dropna()` 没有包含用户传入的 cluster 变量。包含 cluster 缺失的单位仍进入点估计、`nobs` 和 sample mask，但在 IF 聚类聚合时因 cluster 为 `None/NaN` 被排除。

验收复现中，含 cluster 缺失的输入仍报告：

```text
nobs = 8
sum(sample_mask) = 8
cluster_count = 2
```

这使点估计样本与方差样本不一致。

### A-007 P1：DID-001 仍未接受 Stata 原生 never-treated 编码

位置：`src/stataflow/estimators/did_imputation.py:107-139`

Stata dual-run 中把 never-treated 的 `first_treat=-1` 临时替换为 missing；Python 实现则把任何 `<0` 值定义为 never-treated，并在初始 `dropna` 中删除真正 missing 的 `first_treat`。

这说明 Python 和 Stata 实际使用的输入编码仍不同。负处理期在包含 0 或负时间的面板中并不等价于 missing。需要明确、统一并双跑验证原生 Stata 输入语义。

### A-008 P1：RD-002 不满足关闭标准

位置：

- `tests/test_rdrobust.py` 的 Senate qsmv 测试
- `docs/audit/revalidation-v1.2/REMEDIATION_REPORT.md` 的 RD-002 记录

报告承认 Stata 17 为 56 bins、Python 为 59 bins，约 5% 偏差。测试断言的是 Python 的 59，而不是 Stata 的 56。

这可以作为已知限制，但不能在当前项目 `<1e-6` 的严格复现标准下标记 Fixed。

### A-009 P1/P2：原报告仍有四项未完成

- `VCE-002`：Open
- `VCE-003`：Open
- `VCE-004`：Open
- `GLM-003`：Open

只要这些项目仍为 Open，就不能宣布本轮“开发已经结束并通过验收”。

### A-010 P2：工作树尚未达到可交付状态

当前存在大量未提交实现修改以及调试/构建产物，包括：

- `Rplots.pdf`
- `golden_output.txt`、`golden_full_output.txt`、`vce005_output.txt`
- `dist_tmp/`、验收生成的临时 wheel 目录
- 多个 `stata/cases/*probe*.py`
- 未追踪的 golden tests 和验证脚本

需要区分正式证据与临时诊断资产，清理临时文件，并将应保留的测试、脚本和文档纳入明确提交。

### A-011 P1：HDFE 改动引入 10 个 golden 回归

完整 golden 实际结果：

```text
10 failed, 802 passed, 4 skipped
```

失败集中在：

- `test_p3_reghdfe_cluster.py`：adjusted R²、RMSE；
- `test_p3_reghdfe_real_panel.py`：adjusted R²、RMSE；
- `test_w7_reghdfe_2way_cluster.py`：adjusted R²、RMSE、`_cons` SE；
- `test_w7_reghdfe_2way_cluster_real.py`：adjusted R²、RMSE、`_cons` SE。

代表性偏差：

```text
synthetic cluster r2_adj: Python 0.938298 vs Stata 0.916521, rel 2.38%
synthetic cluster rmse:   Python 0.890502 vs Stata 1.035796, rel 14.0%
real panel r2_adj:        Python 0.619567 vs Stata 0.565090, rel 9.64%
real panel rmse:          Python 0.328510 vs Stata 0.351244, rel 6.47%
synthetic 2-way _cons SE: Python 0.015478 vs Stata 0.014335, rel 7.98%
real 2-way _cons SE:      Python 0.007808 vs Stata 0.008346, rel 6.44%
```

主要可疑路径是 `AbsorbingOLS` 新增的 `rmse_df`、`_cluster_k_eff()` 和常数项 influence/VCE 映射。必须按 Stata 的自由度定义重新推导，不能用调整测试容差处理。

## 已通过的验收项

- 非 golden：`322 passed, 0 failed`。
- 完整 golden：`802 passed, 4 skipped, 10 failed`。
- `python -m compileall -q src/stataflow`：通过。
- wheel build：通过，生成 `stataflow-1.1.0-py3-none-any.whl`。
- `git diff --check`：无 whitespace error，只有 LF/CRLF 提示。

除上述 10 个明确失败外，即使未来在当前机器全绿，也不能消除 A-005 的 clean-checkout 可重复性问题。

## 最终结论

当前版本不应提交为“revalidation-v1.2 全部修复完成”。应先执行 `REWORK_TASKS.md`，完成后重新进行独立验收。
