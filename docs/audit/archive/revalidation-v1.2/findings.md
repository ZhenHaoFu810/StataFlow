# Revalidation v1.2 问题台账

审查日期：2026-06-11  
审查分支：`dev`  
原则：本轮只记录问题，不修改实现、测试预期或支持范围。

## 状态定义

- **已复现**：通过最小数据或完整测试直接触发。
- **代码确认**：由确定的代码路径直接证明，不依赖统计口径争议。
- **已声明偏差**：实现或测试已经承认与 Stata 存在超容差偏差。
- **高风险待双跑**：数学实现与 Stata 语义存在明显冲突，但本轮未取得新的 Stata 17 对照输出。
- **证据缺口**：支持声明缺少可重复验证资产，不能据此断言算法错误。

## 问题总表

| ID | 严重性 | 范围 | 状态 | 问题摘要 |
|---|---:|---|---|---|
| LIN-001 | P1 | `FixedEffectsOLS` | 已复现 | 组内不变或组内共线变量未被 omit，直接触发 `Singular matrix` |
| LIN-002 | P3 | OLS/GLM/FE | 已复现 | 空设计矩阵落入 NumPy 底层异常，缺少公开 API 输入校验 |
| LIN-003 | P1 | OLS | 已复现 | 完美拟合时 F 统计量计算发生除零，合法数据无法返回结果 |
| LIN-004 | P1 | `FixedEffectsOLS` | 已复现 | 报告 `_cons` 时，系数为 2 个但 VCE 仍为 `1x1` |
| SAMP-001 | P1 | HDFE/IV-HDFE | 已复现 | 重复 DataFrame 索引导致 estimation-sample mask 把已删除行重新标为 `True` |
| POST-001 | P1 | `estat_summarize` | 已复现 | 读取不存在的 `sample.mask`，真实结果对象始终退化为全样本统计 |
| FVAR-001 | P1 | 所有 factor wrappers | 已复现 | base/omitted level 在缺失值筛选前确定，可能改变参数化并删除常数 |
| FVAR-002 | P2 | factor variables | 已复现 | 字符串列被接受为 `i.`/`ib#.` 因子，并把 `#` 解释为排序位置 |
| FVAR-003 | P3 | 文档 | 代码确认 | 代码支持 3+ 路交互，模块说明与支持矩阵仍称硬拒绝 |
| VCE-001 | P1 | OLS/GLM/IV/PPML | 已复现 | 单一聚类被接受，产生 0 自由度、近零标准误和 `p=0` 等伪推断 |
| VCE-002 | P1 | HDFE MAP | 已声明偏差 | 大 FE 模型常数项方差使用近似，运行时明确警告可能偏离 Stata |
| VCE-003 | P1 | HDFE 2-way cluster | 已声明偏差 | 常数项聚类标准误允许约 3% 偏差，远超项目 `<1e-6` 标准 |
| VCE-004 | P1 | HDFE MAP cluster | 已声明偏差 | golden 测试接受约 0.5% 的 cluster slope 差异，与严格验收标准冲突 |
| VCE-005 | P1 | 加权 robust/cluster | 高风险待双跑 | 多处分数贡献使用 `sqrt(weight)*x*e`，可能少乘一阶权重 |
| IV-001 | P1 | `IV2SLS` | 已复现 | 欠识别模型没有清晰 rank/识别检查，抛出 `IndexError` |
| IV-002 | P1 | `IVAbsorbingOLS` | 已复现 | 与 HDFE 相同的重复索引 sample-mask 错误 |
| GLM-001 | P1 | Logit/Probit/Poisson | 已复现 | 不校验因变量支持域：非二元二项模型、负 Poisson 计数仍返回结果 |
| GLM-002 | P1 | Logit/Probit/Poisson | 已复现 | IRLS 不收敛仍返回带 NaN/无穷/巨量系数的正常 `ResultSchema` |
| GLM-003 | P2 | margins + factor vars | 代码确认 | 所有虚拟变量均按连续变量导数处理，未实现 Stata 的离散变化 |
| DID-001 | P1 | `DIDImputation` | 代码确认 | `first_treat=0` 被当作从未处理，与 Stata 命令语义明确不一致 |
| DID-002 | P1 | `CSDID` | 代码确认 | 自定义 `cluster=` 只改变元数据和聚类数，方差没有按该变量聚合 IF |
| DID-003 | P2 | `CSDID` | 代码确认 | `estat_event()` 只构造对角 VCE，丢失事件期估计间协方差 |
| DID-004 | P2 | DID 全家族 | 代码确认 | 多个结果把有效样本数同时写为 `n_input_rows`，且不返回 sample mask |
| DID-005 | P2 | `CSDID` | 代码确认 | 同一 id 的 `first_treat` 一致性未校验，`groupby(...).first()` 静默决定 cohort |
| DID-006 | P2 | EventStudyInteract | 代码确认 | 自由度实现硬编码前两个 absorb 变量，未验证必须恰好两个 FE |
| DID-007 | P2 | EventStudyInteract | 代码确认 | 迭代去均值达到 10000 次仍可静默继续，没有收敛状态或警告 |
| EVID-001 | P1 | DID golden | 已复现 | 完整 golden 套件有 16 个 error，四组真实数据测试依赖缺失 `.log` 文件 |
| SCHEMA-001 | P2 | ResultSchema | 代码确认 | 不验证系数数目、VCE 维度和 `row_names` 一致性，无法阻止 LIN-004 |
| SCHEMA-002 | P3 | ResultSchema display | 代码确认 | GLM/PPML 仍显示 `t` 和 `P>|t|`，实际使用正态 `z` 推断 |
| RD-001 | P2 | RDRobust | 代码确认 | 删除缺失值、权重和带宽外观测后不返回 sample mask，无法恢复 `e(sample)` |
| RD-002 | P1 | RDPlot | 已声明偏差 | 自动 bin selection 在真实数据上与 Stata 相差约 2–3 倍，且仍被列为已实现命令 |
| DOC-001 | P3 | API 文档 | 代码确认 | `public-api.md` 仍使用旧包名 `statapy` |

## 关键复现证据

### LIN-001：组内共线崩溃

构造 4 个实体、每个实体 3 期，并加入实体内不变变量 `z`。调用：

```python
FixedEffectsOLS(df, "y", ["x", "z"], "id").fit()
```

结果为 `LinAlgError: Singular matrix`。根因是 within transformation 后直接求解正规方程，没有执行与 OLS/HDFE 一致的列秩筛选。

### LIN-003：完美拟合除零

`y=x` 且带常数的简单 OLS 在计算 `(mss/df_model)/(rss/df_resid)` 时因 `rss=0` 抛出 `ZeroDivisionError`，而不是返回无限 F 或 Stata 对应结果。

### LIN-004：FE 系数与 VCE 维度不一致

随机面板的实际输出：

```text
coefficients: ['x', '_cons']
variance.row_names: ['x']
variance.values shape: (1, 1)
```

因此 `_cons` 的报告标准误无法从统一 VCE 中恢复，`estat_vce` 与系数表不满足同一 schema。

### SAMP-001 / IV-002：重复索引污染 sample mask

输入 12 行，其中两行索引均为 `0`，第二行因 `y` 缺失被删除。HDFE/IV-HDFE 使用 `idx in df.index` 重建 mask，结果：

```text
sample_mask sum = 12
reported nobs   = 11
```

mask 长度虽然正确，但内容与估计样本矛盾。

### POST-001：`estat_summarize` 忽略估计样本

真实字段为 `result.sample.sample_mask`，实现读取 `result.sample.mask`。在只有 4 行共同有效样本的数据上，`estat_summarize` 对 `y` 和 `x` 各报告 `N=5`，证明它分别 drop missing，而不是使用共同 estimation sample。

### FVAR-001：错误 base level 改变模型

当 `g=1` 的行全部因 `y` 缺失被删除时，factor 展开仍在完整数据上把 1 选为 base，生成 `2.g`、`3.g`。有效样本中两列虚拟变量与常数完全共线，顺序筛选最终删除 `_cons`，但 `model.has_constant` 仍为 `True`。

### VCE-001：单一聚类产生伪精确推断

Logit 和 IV2SLS 在所有观测属于同一 cluster 时均成功返回。Logit 示例得到 `df_resid=0`、约 `1e-14` 的标准误和 `p=0`；IV2SLS 返回近零标准误且未给警告。此时 cluster-robust 推断不可定义，应拒绝或明确失败。

### IV-001：欠识别错误类型

两个内生变量、一个排除工具变量的模型没有得到“equation not identified”类错误，而是内部列表访问产生 `IndexError: list index out of range`。

### GLM-001 / GLM-002：无效结果被正常返回

最小复现结果：

```text
Logit(y in {0,1,2})   -> beta=NaN, warning='IRLS did not converge'
Probit(y in {0,1,2})  -> beta magnitude about 1e16
Poisson(y contains -1)-> ll=-inf
perfect separation    -> beta=NaN, se=NaN
```

这些对象仍以正常拟合结果返回；调用方若不主动检查字符串 warning，可能继续使用无效估计。

### DID-002：自定义 cluster 未进入方差计算

`CSDID._fit_reg/_fit_dr` 仅在结束时计算 `df[cluster_col].nunique()` 并记录 `_cluster_var`。`_finalize_fit` 的标准误始终对 unit-level IF 逐项平方求和，没有按 `cluster_col` 汇总。因此 `cluster=` 改变报告的聚类数，却不改变应改变的 meat。

### EVID-001：golden 基线并非全绿

2026-06-11 完整执行：

```text
788 passed, 4 skipped, 16 errors, 74 warnings
```

16 个 error 来自：

- `test_w4_csdid_real_ezunem.py`
- `test_w4_did_imputation_real_ezunem.py`
- `test_w4_eventstudyinteract_real_ezunem.py`
- `test_w9_csdid_dr_real_ezunem.py`

直接原因是测试在 fixture 中读取 `stata/output/realdata_*.log`，文件不存在。它们不是断言失败，但意味着当前 checkout 无法独立复现 DID 真实数据验证。

## 高风险数学项

### VCE-005：加权 sandwich 的权重阶数

OLS、GLM、PPML 和部分 cluster 分支用 `sqrt(weight) * x * residual` 构造 score。对于加权估计方程，常见 sandwich score 是 `weight * x * residual`，外积后对应二次权重。当前代码在不同估计器中并不一致：部分 HDFE cluster 路径使用完整权重，其他路径使用平方根权重。该项应视为高风险不一致，必须逐命令与 Stata 17 的 `aweight + robust/cluster` 双跑后裁定。

## 已声明但仍未达到项目验收标准的偏差

- HDFE MAP 在大量 FE 参数时，用 grand-mean approximation 计算常数项方差。
- 两路 cluster 的常数项标准误代码警告可能与 Stata 偏离约 3%。
- MAP benchmark 测试中存在约 0.5% 的 cluster slope 差异并被测试注释接受。
- `rdplot` 自动分箱在 Senate 数据上曾得到 Python `5/16` 对 Stata `15/35`，当前 release known-issues 仍承认 2–3 倍差异且没有 golden 双跑闭环。

这些可以作为“已知限制”管理，但不能同时计为满足项目章程所写的字段级 `<1e-6` 复现。

## 本轮未判定为实现错误的事项

- DID 真实数据 golden 的 16 个 error 当前是验证资产缺失，不能单独证明点估计错误。
- `NotImplementedError` 若与支持矩阵明确一致，不作为缺陷；只有支持声明超出实现时才记文档问题。
- StataRunner 的 `shell=True` 已在项目安全文档中限制为内部生成 `.do` 内容；本轮未发现新的可直接利用路径，故未升级为安全缺陷。
