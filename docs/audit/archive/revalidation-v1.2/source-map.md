# Revalidation v1.2 源码定位

以下行号对应 2026-06-11 审查时的 `dev` 分支，用于后续 Agent 快速定位，不代表修复建议。

| ID | 主要位置 | 观察点 |
|---|---|---|
| LIN-001 | `src/stataflow/estimators/fe.py:210` | within 后直接 `np.linalg.solve` |
| LIN-002 | `ols.py:182`, `glm.py:161`, `fe.py:144` | 空列列表直接 `np.column_stack` |
| LIN-003 | `src/stataflow/estimators/ols.py:409` | F 统计量未处理 `rss == 0` |
| LIN-004 | `src/stataflow/estimators/fe.py:417-440` | coefficients 加 `_cons`，VCE 仍仅使用 slope names |
| SAMP-001 | `absorbing_ols.py:773`, `iv.py:649` | 用 index membership 重建布尔 mask |
| POST-001 | `src/stataflow/postestimation.py:49` | 读取 `sample.mask` 而非 `sample.sample_mask` |
| FVAR-001 | `factor_variables.py:127-163`, wrappers 的 `expand_factor_terms(...)` 调用 | level 在 estimator sample screening 前确定 |
| FVAR-002 | `factor_variables.py:56-86` | 非数值 level 的 1-based position fallback |
| VCE-001 | `ols.py:380-384`, `fe.py:273`, `glm.py:307-354`, `iv.py:1246` | `G<=1` 时 correction 退化为 1，未拒绝 |
| VCE-002 | `absorbing_ols.py:466-580`, `absorbing_ols.py:1104` | 大规模 FE 常数方差近似路径和运行时 warning |
| VCE-003 | `absorbing_ols.py:1519-1520` 及对应 golden warnings | 多路聚类常数项偏差 |
| VCE-005 | `ols.py:251`, `glm.py:282-295`, `ppmlhdfe.py:304` | 加权 score 的平方根权重实现 |
| IV-001 | `src/stataflow/estimators/iv.py:231-248` 及 first-stage diagnostics | 缺少显式 identification/rank gate |
| IV-002 | `src/stataflow/estimators/iv.py:649` | 与 SAMP-001 同源 |
| GLM-001 | `src/stataflow/estimators/glm.py:110-170` | sample preparation 未检查 outcome 支持域 |
| GLM-002 | `src/stataflow/estimators/glm.py:199-245`, `glm.py:438-439` | 不收敛只追加字符串 warning，仍返回结果 |
| GLM-003 | `src/stataflow/postestimation.py:127-223` | factor dummy 与连续变量共用导数公式 |
| DID-001 | `src/stataflow/estimators/did_imputation.py:104-136` | 代码和 warning 明示 `<=0` 的不同语义 |
| DID-002 | `csdid.py:217-220`, `csdid.py:231`, `csdid.py:274`, `csdid.py:499-503` | cluster 只用于计数；SE 仍按 unit IF |
| DID-003 | `src/stataflow/estimators/csdid.py:575-601`, `csdid.py:856-882` | 输出 VCE 仅填对角线 |
| DID-004 | `did_imputation.py:525`, `eventstudyinteract.py:331`, `csdid.py:592` | `n_input_rows` 被有效样本数覆盖 |
| DID-005 | `src/stataflow/estimators/csdid.py:110`, `csdid.py:356` | cohort 使用 `groupby(uid)[ft].first()` |
| DID-006 | `eventstudyinteract.py:230-232` | 只索引 absorb[0]、absorb[1] |
| DID-007 | `eventstudyinteract.py:171-184` | 固定 10000 次上限，无未收敛报告 |
| SCHEMA-001 | `src/stataflow/results/result.py:90-220` | 构造和反序列化均无 shape invariant 校验 |
| SCHEMA-002 | `src/stataflow/results/result.py:278-281` | 所有 family 固定显示 t 标签 |
| RD-001 | `src/stataflow/estimators/rdrobust.py:770-815`, `rdrobust.py:1253-1258` | 筛选后只存 nobs/n_input，无 sample mask |
| RD-002 | `src/stataflow/estimators/rdplot.py:79-202`, `docs/release/known-issues.md:29` | 简化 IMSE 分箱公式；文档仍承认 2–3 倍差异 |
| DOC-001 | `docs/architecture/public-api.md` | 导入示例仍为旧包名 |

## Golden 资产位置

以下测试直接读取预生成日志，文件不存在时 fixture error：

- `tests/golden/test_w4_csdid_real_ezunem.py`
- `tests/golden/test_w4_did_imputation_real_ezunem.py`
- `tests/golden/test_w4_eventstudyinteract_real_ezunem.py`
- `tests/golden/test_w9_csdid_dr_real_ezunem.py`
