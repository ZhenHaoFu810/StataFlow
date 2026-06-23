# StataFlow 模块审查问题复核与修缮总任务书 v1.3

## 1. 目的

本文档用于指导后续 Agent 对 `modular-revalidation-v1.3` 审查发现的问题进行二次复核、根因确认、代码修复、Stata 17 双跑和回归验收。

本轮目标不是机械地把 `findings.md` 中的每个编号改成“已修复”，而是：

1. 确认 finding 在当前基线上真实存在；
2. 区分算法错误、识别规则错误、推断语义错误、API 契约问题、结果 schema 问题、测试工具问题和纯数值残余；
3. 合并同源问题，避免多个 Agent 重复或冲突修改同一基础逻辑；
4. 先建立失败测试和理论/Stata 真值，再修改产品代码；
5. 对修复产生的跨模块影响进行完整回归；
6. 最终明确哪些功能已经恢复严格 Stata 17 兼容，哪些只能作为已知限制保留。

---

## 2. 基线与输入材料

### 2.1 审查基线

- 分支：本地 `dev`
- Commit：`2c7db1ca095e03d29c471e8d523fdaa943306174`
- Stata：17 MP
- Stata executable：`D:\Software\Stata17\StataMP-64.exe`

所有 M01-M10 审查均基于上述 commit，当前 `dev` HEAD 也仍为该 commit。

### 2.2 必读材料

开始任何修复前必须阅读：

1. `AGENTS.md`
2. `docs/audit/modular-revalidation-v1.3/MASTER_AUDIT_BRIEF.md`
3. 本文档
4. 对应模块的 `findings.md`
5. 对应模块的 `summary.md`
6. 对应模块的 `test-design-register.md`
7. finding 指向的 evidence 与最小复现
8. 对应 estimator、compat wrapper、ResultSchema 和 support matrix

不得只阅读模块 `summary.md` 后直接改代码。

### 2.3 工作区安全

当前工作区包含尚未纳入基线的审查资产：

- `docs/audit/modular-revalidation-v1.3/`
- `tests/audit_v1_3/`
- `stata/cases/audit_v1_3_m01/` 至 `audit_v1_3_m07/`
- 已修改的 `workspace/current-task/REPORT.md`

后续 Agent 必须：

- 不执行 `git reset --hard`、`git clean` 或覆盖式 checkout；
- 不删除审查 evidence；
- 不把未追踪资产误判为垃圾文件；
- 提交时使用显式路径，不使用未经检查的 `git add -A`；
- 在创建隔离 worktree 前先确认审查资产已被安全保存；
- 不向公开 GitHub `main` 直接推送内部审查资料。

---

## 3. 对审查结果的归一化理解

审查共产生 41 个编号条目，但编号条目不等于 41 个独立产品 bug。

### 3.1 不应作为独立 bug 修复的条目

| 条目 | 处理方式 | 原因 |
|---|---|---|
| `M07-DID-002` | 作为正向验证证据保留 | 证明统一 treatment 编码后 DIDImputation 核心算法基本对齐，不是产品缺陷 |
| `M07-DID-004` | 合并至 `M07-DID-001` | 都是 `first_treat` 的 missing/0/negative 编码冲突 |
| `M06-PPMLHDFE-006` | 先做 schema 契约裁决 | Stata 保留 omitted 参数零行/列、Python 删除；属于结果表达差异，不能直接在 PPML estimator 内硬补 |

### 3.2 需要先裁决语义、不能直接改实现的条目

- `M01-LIN-003`：两路 cluster 下 `f_stat` 应严格复制 Stata `e(F)`，还是保留 robust Wald F 并增加独立字段。
- `M05-GLM-001`、`M06-PPMLHDFE-001`：不得未经证明把 `aweight` 自动映射为 `pweight` 或 `iweight`。
- `M05-GLM-002/003`、`M06-PPMLHDFE-005`：需要明确 GLM/PPML 的 z 推断、`df_resid`、LR/Wald statistic 在 `ResultSchema` 中的字段语义。
- `M10-FACTOR-001`：需要决定 ResultSchema 是否完整镜像 Stata omitted/base 行，或只返回 active parameters。
- `M08-RD-001`：需要决定在 `<1%` 且推断结论不变时继续追求逐位一致，还是经正式裁决记录为已知数值残余。

涉及公共字段和默认参数的决策，应先写 ADR 或在现有 ADR 中补充裁决，不得由执行 Agent自行决定。

### 3.3 跨模块共同根因

#### C01：共线性、秩与参数集合

关联 finding：

- `M01-LIN-002`
- `M02-FE-002`
- `M02-FE-006`
- `M02-FE-007`
- M03-M05 中登记的共享风险

核心问题包括两层：

1. `_vce_utils.detect_collinear_columns()` 的尺度敏感 tolerance 与 Stata 不一致；
2. `FixedEffectsOLS` 删除变量后没有同步维度、名称和 VCE 映射。

第二层是确定性 P0 崩溃，不能等待第一层 tolerance 研究完成。两者必须分别测试和修复。

#### C02：FE 自由度、嵌套与退化设计

关联 finding：

- `M02-FE-001/003/004`
- `M03-HDFE-001/002/003`
- `M06-PPMLHDFE-007`

这些问题共同影响：

- `df_model`
- `df_resid`
- `df_a`
- `k_eff`
- small-sample correction
- RMSE
- adjusted R-squared
- F/Wald 检验
- `_cons` 恢复

不得只修改一个输出标量。必须先建立统一的自由度定义表，再分别验证 FE、areg、reghdfe、ivreghdfe 和 ppmlhdfe。

#### C03：整体检验与 ResultSchema 语义

关联 finding：

- `M01-LIN-003`
- `M02-FE-001/004`
- `M05-GLM-002/003`
- `M06-PPMLHDFE-005`

Linear 的 F、cluster Wald F、GLM 的 LR chi2、robust Wald chi2 不是同一统计量。不得继续把不同检验统一塞入一个字段而不记录类型。

#### C04：吸收模型预测语义

关联 finding：

- `M06-PPMLHDFE-004`
- `M09-FE-001`

两者都涉及 FE，但 Stata 命令语义不同：

- `xtreg, fe` 后 `predict, xb` 包含实体效应；
- `ppmlhdfe` 后 `predict, xb` 不包含吸收 FE，而 `mu` 包含完整线性预测器。

禁止抽象出一个“所有 FE 模型统一 include_fe”的规则。必须按命令定义分别实现并命名。

#### C05：命令级权重契约

关联 finding：

- `M01-LIN-001`
- `M05-GLM-001`
- `M06-PPMLHDFE-001`

三个 finding 不应被一个全局“权重修复”覆盖：

- `regress` 接受 aweight，零权重应退出 estimation sample；
- Stata `logit/probit/poisson` 不接受 aweight；
- Stata `ppmlhdfe` 接受 pweight，不接受 aweight/iweight。

每个 wrapper 必须执行命令特定的合法性检查。

---

## 4. 总体执行顺序

建议按以下 Wave 执行，而不是简单按 M01-M10 顺序。

| Wave | 主题 | 主要 finding | 原因 |
|---|---|---|---|
| R0 | 验证基础设施加固 | `M10-RUNNER-001` | 后续所有 Stata 双跑必须能可靠识别运行时失败 |
| R1 | P0 阻断修复 | `M02-FE-002`, `M06-PPMLHDFE-002/003`, `M07-DID-003` | 崩溃、无意义结果或错误 ATT，优先处理 |
| R2 | 参数集合与共线性 | `M01-LIN-002`, `M02-FE-006/007` | 先稳定估计参数集合，后续 VCE/schema 才有意义 |
| R3 | FE/HDFE 自由度体系 | `M02-FE-001/003/004`, `M03-HDFE-001/002/003`, `M06-PPMLHDFE-007` | 同一数学体系，需统一处理 |
| R4 | DID treatment 语义 | `M07-DID-001/004`, `M07-DID-006` | treatment 编码属于识别定义 |
| R5 | IV 推断与诊断 | `M04-IV-001/002/003` | 弱 IV、LIML 和常数报告 |
| R6 | GLM/PPML schema 与推断 | `M05-GLM-002/003/004`, `M06-PPMLHDFE-004/005/006` | 统一区分 LR/Wald、z/df 与预测类型 |
| R7 | API 与表现层兼容 | `M01-LIN-001/003`, `M02-FE-005`, `M05-GLM-001`, `M06-PPMLHDFE-001`, `M09-FE-001`, `M10-FACTOR-001`, `M08-RD-002` | 多数涉及公共行为，需要迁移测试 |
| R8 | 数值残余调查 | `M03-HDFE-004`, `M04-IV-004`, `M05-GLM-005`, `M06-PPMLHDFE-005(SE)`, `M07-DID-005`, `M08-RD-001` | 不应干扰高严重性修复，统一最后裁决 |
| R9 | 全量复验与发布裁决 | 全部 | 新审查测试、旧 golden、真实数据、文档和 public sync |

除非依赖关系明确允许，一个 Agent 一次只执行一个 Wave 内的一个任务包。

---

## 5. 标准问题处理协议

每个任务必须遵循以下步骤。

### 阶段 A：复核 finding

1. 记录当前 commit 与工作区状态。
2. 运行 finding 的最小复现。
3. 现场重新运行对应 Stata `.do`，不得只读取旧 JSON。
4. 确认 Stata 命令版本和 ado 来源。
5. 比较原始样本、参数集合、完整 VCE 和关键统计量。
6. 判断 finding 属于：
   - estimator algorithm；
   - identification/sample rule；
   - VCE/inference；
   - wrapper/API；
   - ResultSchema；
   - runner/parser；
   - test-design error；
   - numerical residual。
7. 如果 finding 不能稳定复现，先更新 finding 状态，不得修改产品代码。

### 阶段 B：建立失败测试

修复前至少建立：

- 一个最小 deterministic regression test；
- 一个本轮 audit DGP 的 Stata 双跑测试；
- 一个受影响邻近路径的不变性测试；
- 对共享函数，至少覆盖两个调用模块。

测试必须在修复前因正确原因失败。

### 阶段 C：数学与契约确认

在编码前写清：

- 目标 estimand 或统计量；
- 样本定义；
- 公式与自由度；
- Stata 字段语义；
- omitted/base 参数是否属于报告参数集合；
- 是否改变公共 API、默认参数或序列化 schema。

涉及公共行为时先完成 ADR 决策。

### 阶段 D：最小修复

- 只修改根因所在层；
- 不通过放宽 tolerance 隐藏算法差异；
- 不让 estimator 读取测试 gold values；
- 不复制 Stata 输出常数；
- 不顺手重构不相关模块；
- 保持 core 与 compat wrapper 的职责边界。

### 阶段 E：验证

依次运行：

1. 新增最小回归测试；
2. 对应模块 `tests/audit_v1_3/<module>/`；
3. 对应旧 unit/integration tests；
4. 对应旧 golden tests；
5. 全量非 golden tests；
6. 全量 golden tests（有 Stata 环境时）；
7. `python -m compileall -q src/stataflow`；
8. `python -m pip wheel . --no-deps -w <isolated-output>`；
9. `git diff --check`。

修复后必须重新现场生成 Stata evidence，不得只证明 Python 测试通过。

---

## 6. Wave R0：Stata 验证基础设施

### R0-T01：识别 Stata log 内的运行时错误

**Finding**：`M10-RUNNER-001`

**代码范围**：

- `src/stataflow/stata_runner/runner.py`
- `tests/test_stata_runner.py`
- `tests/audit_v1_3/m10_shared_infrastructure/`

**复核重点**：

- Stata `/e do` 在 `r(111)` 等运行时错误后进程仍返回 0；
- log 尾部是否存在稳定的 `r(<number>);` 模式；
- 不得把普通输出中的历史字符串误判为当前错误；
- `capture`、预期错误测试和用户主动清除错误时如何处理。

**推荐设计**：

- 在 `StataResult` 中保留原始 process exit code；
- 增加独立的 Stata return code / execution status；
- 提供 `raise_on_stata_error` 或等价显式行为；
- 解析应聚焦 do-file 终止状态，不使用宽泛关键词如 `not found` 单独判错。

**验收**：

- 成功 do-file 不误报；
- `r(111)`、语法错误、用户 `exit 9` 可区分；
- 后续 audit harness 不再仅依赖 OS exit code。

---

## 7. Wave R1：P0 阻断问题

### R1-T01：FE 共线删除后的维度同步

**Finding**：`M02-FE-002`

**代码范围**：`src/stataflow/estimators/fe.py`

**必须分开验证**：

- exact within-collinearity；
- entity-invariant regressor；
- `add_constant=True/False`；
- OLS、robust、cluster VCE；
- coefficient names、dropped variables、VCE row names 和 matrix shape。

**修复要求**：删除列后同步实际 `k`、保留索引、系数名、设计矩阵、VCE 映射和预测输入映射。

### R1-T02：PPML 默认分离与不收敛处理

**Finding**：`M06-PPMLHDFE-002`

**代码范围**：`src/stataflow/estimators/ppmlhdfe.py`

**核心判断**：

- Stata 默认是组合式 separation 检测，不等同于仅 `separation="fe"`；
- 若暂时不能实现 simplex/relu，必须明确缩小支持声明；
- 任何未收敛模型不得仅添加 warning 后返回看似完整的推断结果。

**验收**：

- y=0 FE 组的 sample 与 Stata 对齐；
- `separation=None` 的默认语义明确；
- 发散、overflow、max_iter 均产生不可误用的失败状态；
- `sample_mask`、nobs、系数、VCE 同时验证。

### R1-T03：PPML offset/exposure

**Finding**：`M06-PPMLHDFE-003`

**代码范围**：

- `src/stataflow/estimators/ppmlhdfe.py`
- `src/stataflow/compat/stata/hdfe.py`

**已定位风险**：`_build_t_matrix` 当前再次减去 offset 的加权平均。

**修复要求**：

- 明确模型 `log(mu_i)=x_i beta + a_i + offset_i`；
- offset 系数固定为 1，不参与估计或 constant recovery；
- exposure 只转换为 `log(exposure)`；
- IRLS working response、eta、mu、常数恢复、ll、deviance 和 predict 使用同一约定。

**验收**：S7 与 R1 必须在 coefficients、完整 VCE、ll、deviance 和 predictions 上对齐。

### R1-T04：CSDID not-yet-treated 控制组

**Finding**：`M07-DID-003`

**代码范围**：`src/stataflow/estimators/csdid.py`

**识别规则**：当 `notyet=True` 且存在 never-treated 时，控制组应包含 never-treated 与在比较期尚未处理的单位。

**修复要求**：同时修改 `_fit_reg` 与 `_fit_dr`，并复核：

- ATT(g,t) control mask；
- base period；
- eligible units；
- influence functions；
- event/simple/group/calendar aggregations；
- custom cluster covariance；
- nobs/sample mask。

只修改一个 `control_mask` 表达式而不重跑影响函数是不充分的。

---

## 8. Wave R2：共线性与参数集合

### R2-T01：共享共线性判定规则

**Findings**：`M01-LIN-002`, `M02-FE-006`

**代码范围**：`src/stataflow/estimators/_vce_utils.py`

**研究要求**：

- 不以相关系数阈值简单代替秩判断；
- 分析 Stata 在尺度差异、QR pivot、machine precision 下的省略规则；
- 规则必须在变量缩放后保持可解释行为；
- 明确 exact collinearity 与 near-collinearity 的边界。

**回归矩阵**：OLS、within FE、HDFE、IV、GLM 至少各一个调用路径。

### R2-T02：FE 实体不变变量预筛选

**Finding**：`M02-FE-007`

**代码范围**：`src/stataflow/estimators/fe.py`

必须按 estimation sample 计算组内变异，不能在 missing screening 前判断。被 omitted 的变量必须在结果元数据中可追踪。

---

## 9. Wave R3：FE/HDFE 自由度与常数

### R3-T01：FixedEffectsOLS 自由度和整体检验

**Findings**：`M02-FE-001`, `M02-FE-004`

建立 conventional 与 cluster 的独立字段真值表，分别核对 Stata：

- `e(df_m)`；
- `e(df_r)`；
- `e(F)` / p-value；
- within/overall adjusted R-squared。

不得根据单一 DGP 写 if/else 常数。

### R3-T02：非平衡面板 `_cons` 恢复

**Finding**：`M02-FE-003`

**代码范围**：`src/stataflow/estimators/fe.py`

验证 Stata 常数定义、实体效应 normalization、按观测还是按实体加权，以及 singleton 对 normalization 的影响。

### R3-T03：HDFE 嵌套 FE

**Findings**：`M03-HDFE-001`, `M06-PPMLHDFE-007`

**代码范围**：`src/stataflow/estimators/absorbing_ols.py` 及 PPML 调用路径。

嵌套判断必须基于取值映射，而不是变量名相等。明确方向：FE 是否为 cluster 的细分层级，并验证多 FE、多 cluster 和缺失样本。

### R3-T04：Slope absorption df

**Finding**：`M03-HDFE-002`

核对每组 intercept/slope 参数数、reference constraints、rank deficiency、connected components 和 cluster nesting。修复后必须验证 MAP/LSDV 路径是否仍一致。

### R3-T05：退化 df 输出

**Finding**：`M03-HDFE-003`

当统计量数学上未定义时返回 `None/NaN`，不得返回有意义外观的 `0.0`。同时检查 FE、HDFE、IV-HDFE、PPMLHDFE 的同类输出。

---

## 10. Wave R4：DID 语义

### R4-T01：DIDImputation treatment-time 编码

**Findings**：`M07-DID-001` + `M07-DID-004`

**代码范围**：

- `src/stataflow/estimators/did_imputation.py`
- `src/stataflow/compat/stata/did.py`
- support matrix 与 docstring

**目标语义**：compat layer 必须按目标 ado 版本处理 missing 为 never-treated。对 0/负值必须明确拒绝或显式转换，不得继续静默赋予不同含义。

**注意**：core Python API 是否继续允许另一种编码属于 API 决策。如果 core 与 compat 语义不同，必须在入口完成显式转换并记录 provenance。

### R4-T02：`window()` 支持边界

**Finding**：`M07-DID-006`

这是版本/兼容契约任务。先确认目标 ado 版本是否有该选项，再决定：

- 删除或拒绝 wrapper 参数；
- 固定目标 ado 版本；
- 或将其定义为 Python-only extension，不能声称直接 Stata 映射。

---

## 11. Wave R5：IV/GMM

### R5-T01：弱工具变量诊断暴露

**Finding**：`M04-IV-001`

**代码范围**：

- `src/stataflow/estimators/iv.py`
- `src/stataflow/results/result.py`

先设计 diagnostics schema，再写入已有 `widstat/idstat/iddf/idp`。同时明确：

- conventional、robust、cluster 对应的统计量名称；
- 单/多内生变量；
- Stock-Yogo critical values 的适用条件；
- 不可计算时使用 None/NaN 和 warning。

### R5-T02：LIML/Fuller 推断

**Finding**：`M04-IV-002`

从 k-class estimating equation、LIML k、residual definition 和 VCE bread/meat 开始核对。SE、RMSE、F 不得分别打补丁，因为它们可能共享残差或 df 根因。

### R5-T03：无真实 FE 时的 `_cons`

**Finding**：`M04-IV-003`

区分“常数变量被传入 absorb”与“真正存在 FE”。必要时 wrapper 应路由到 `IV2SLS`，而不是让吸收器静默删除 `_cons`。

---

## 12. Wave R6：GLM、PPML 与结果语义

### R6-T01：GLM LR/Wald 与 df

**Findings**：`M05-GLM-002`, `M05-GLM-003`, `M06-PPMLHDFE-005` 的 df 部分

优先裁决 `FitInfo` 是否需要新增 statistic type 或独立字段。最低要求是 summary、serialization 与 Stata-style output 不得把 LR chi2 标成 Wald chi2。

### R6-T02：GLM separation

**Finding**：`M05-GLM-004`

针对 Logit/Probit 建立完全与准完全分离检测；Poisson 的 separation 机制应独立研究，不得照搬二元响应规则。任何数值裁剪必须保留诊断信号。

### R6-T03：PPML predict 类型

**Finding**：`M06-PPMLHDFE-004`

明确并测试：

- `xb`：不含吸收 FE；
- 完整 eta：需要独立、清晰命名；
- `mu=exp(eta+offset)`；
- residuals、pearson、deviance 的 Stata 定义；
- eform 不得改变 prediction scale。

### R6-T04：Omitted/base 参数 schema

**Findings**：`M06-PPMLHDFE-006`, `M10-FACTOR-001`

这是全局 ResultSchema 设计任务。候选方案：

1. coefficients 与 VCE 完整镜像 Stata，包括 omitted/base 零行；
2. 保持 active-only，但新增完整 parameter map；
3. active-only 并明确不承诺 `e(b)` 维度兼容。

必须评估 margins、summary、serialization、所有 estimator 和既有测试后再决策。

---

## 13. Wave R7：API 与表现层

### R7-T01：命令级权重规则

**Findings**：`M01-LIN-001`, `M05-GLM-001`, `M06-PPMLHDFE-001`

- OLS：0 权重行退出 estimation sample，负权重拒绝；删除后再归一化。
- GLM wrapper：按 Stata 命令合法权重重新定义 API；不支持的 aweight 必须硬报错。
- PPML wrapper：研究并实现 pweight，或删除不真实的 aweight 兼容声明。

### R7-T02：两路 cluster F 契约

**Finding**：`M01-LIN-003`

经 ADR 决定是否镜像 Stata `e(F)`。若保留 robust Wald F，必须给它独立字段/名称，不能伪装成 Stata `e(F)`。

### R7-T03：`xtreg_fe` 默认常数

**Finding**：`M02-FE-005`

这是默认行为变化。需要：

- API 兼容评估；
- wrapper regression test；
- changelog/迁移说明；
- core `FixedEffectsOLS` 默认值是否保持 Python-native 语义的独立决定。

### R7-T04：FE prediction

**Finding**：`M09-FE-001`

现有 estimator 已保存 `_entity_effects`。修复时必须定义：

- in-sample 已见 entity；
- newdata 中已见 entity；
- unseen entity；
- missing entity；
- residual prediction；
- `xb` 与不含 FE 的线性部分如何分别命名。

### R7-T05：RD 小有效样本 guardrail

**Finding**：`M08-RD-002`

先从 rdrobust 源码确定阈值，而不是根据一个 n=12 案例猜测。warning、NaN coefficient 和 VCE matrix 必须保持一致。

---

## 14. Wave R8：数值残余

以下 finding 进入统一调查队列：

| Finding | 差异量级 | 初始处理 |
|---|---:|---|
| `M03-HDFE-004` | `1.99e-6` | 比较 cluster meat、df factor、求和顺序 |
| `M04-IV-004` | `5e-6` | 比较 robust residual/meat 与小样本因子 |
| `M05-GLM-005` | `~2e-5` | 检查非对角 VCE、累加精度 |
| `M06-PPMLHDFE-005` SE 部分 | `~2e-6` | 在 df/FE 修复后重测，可能自动消失 |
| `M07-DID-005` | `0.5-1.5%` | 比较 influence scaling、cluster correction |
| `M08-RD-001` | `~0.3% bandwidth` | 对照 rdrobust 源码边界/质点规则 |

调查顺序：

1. 先重跑高优先级修复后的同一案例；
2. 输出中间矩阵，而不是只比较最终 SE；
3. 排除 parser 精度和显示截断；
4. 排除数据排序、dtype 和 BLAS 差异；
5. 确认是否改变统计结论；
6. 若无法在不破坏其他路径的情况下消除，提交 Codex 裁决，不得自行放宽全局 tolerance。

---

## 15. 每个模块的最终状态要求

### M01 Linear

- 修复零 aweight、near-collinearity 和两路 cluster F 契约；
- 补充 aweight + robust/cluster；
- 重新验证完美拟合与 prediction sample propagation。

### M02 Panel / FE

- 所有 P0/P1 finding 必须关闭；
- exact/near/entity-invariant 共线场景不崩溃；
- conventional/cluster df 与统计量字段明确；
- 非平衡/singleton `_cons` 对齐；
- wrapper 默认行为和 FE prediction 与 Stata 一致。

### M03 HDFE

- 嵌套 FE 和 slope df 修复；
- MAP/LSDV 均通过；
- degenerate statistic 返回缺失而非伪值；
- 真实数据 cluster 残余得到修复或正式裁决。

### M04 IV/GMM

- weak-IV diagnostics 可访问且命名正确；
- LIML/Fuller VCE 与 fit statistics 重新验证；
- 常数/无真实 FE 参数集合对齐；
- 新增 GMM2S 真实数据和多 endogenous 覆盖。

### M05 GLM

- 权重 API 不再伪兼容；
- z/df 与 LR/Wald 语义明确；
- separation 有清晰、快速、可靠的失败行为；
- predict/margins 在 M09 范围内联动复验。

### M06 PPMLHDFE

- 两个 P0 必须关闭；
- 默认分离和收敛状态不可误用；
- offset/exposure 全字段对齐；
- predict 类型、df、nested FE 和 omitted schema 得到处理；
- 增加 2-way cluster 独立证据。

### M07 DID/Event Study

- DIDImputation encoding 与目标 ado 一致；
- CSDID notyet 的控制组、IF 和 aggregation 对齐；
- `window` 支持边界真实；
- EventStudyInteract SE 残余得到解释或修复。

### M08 RD

- 小有效样本 guardrail 对齐；
- two-sided bandwidth residual 有源码级结论；
- 补充 fuzzy、weights、masspoints 真实数据验证。

### M09 Postestimation

- FE `xb`/residuals 对齐；
- unseen entity 行为明确；
- discrete margins 的 factor/continuous 语义写入支持矩阵；
- `estat_vce/ic` 增加直接字段级验证。

### M10 Shared Infrastructure

- runner 能识别 Stata runtime failure；
- factor/base parameter contract 完成裁决；
- ResultSchema 不变量和序列化兼容测试完整。

---

## 16. 修复任务报告模板

每个任务完成后在对应 remediation 目录写报告：

```markdown
# <Task ID> Remediation Report

## Baseline
- start commit:
- end commit:
- Stata/ado version:

## Findings addressed
- IDs:
- status before:
- status after:

## Reproduction
- Python command:
- Stata command:
- pre-fix result:

## Mathematical/semantic decision
- estimand/statistic:
- sample rule:
- formula/df:
- API/schema decision:

## Changes
- files:
- root-cause fix:
- intentionally unchanged behavior:

## Verification
- focused tests:
- audit tests:
- old golden:
- full regression:
- fresh Stata evidence:

## Residual risks
- unresolved fields:
- numerical residuals:
- follow-up task:
```

---

## 17. Git 与提交策略

- 每个任务包使用独立 `codex/<topic>` 或约定的实现分支；
- 一个 commit 只处理一个可解释根因；
- 测试与实现可以同 commit，但不得混入审查资料整理；
- API/ADR 决策应先于实现 commit；
- 不 force-push `main`；
- 内部 `dev` 不再推送到公开仓库；
- 对公开仓库同步继续使用从 `public-main` 创建的白名单分支；
- PR 前执行内部资料泄漏检查。

推荐提交顺序：

1. failing regression tests；
2. minimal implementation；
3. fresh Stata evidence / audit status；
4. documentation/support matrix；
5. 必要时单独 public-safe sync。

---

## 18. 全局验收门槛

全部修缮完成必须同时满足：

- [ ] 所有 P0 已关闭并有新 Stata 17 证据；
- [ ] 所有 P1 已修复或经正式 ADR 降级/限制支持范围；
- [ ] P2/P3 均有明确的修复、限制或数值裁决；
- [ ] 同源 finding 已统一根因，不存在互相矛盾的局部补丁；
- [ ] M01-M10 新 audit tests 达到预期结果，不靠删除 xfail 隐藏问题；
- [ ] 原有 unit/integration tests 全部通过；
- [ ] 原有 golden tests 全部通过或每个环境性 skip 有解释；
- [ ] 新增真实数据与 synthetic 证据可重复生成；
- [ ] ResultSchema 行名、系数和 VCE matrix 不变量全部通过；
- [ ] sample mask 与 Stata `e(sample)` 在受影响模块中复验；
- [ ] 文档、support matrix、known issues 与实际行为一致；
- [ ] wheel 构建和 examples smoke tests 通过；
- [ ] 公共同步不包含 audit、workspace、golden、Stata logs 或内部计划；
- [ ] 独立验收 Agent 复核通过。

---

## 19. 后续 Agent 使用 Prompt

> 严格执行 `docs/audit/modular-revalidation-v1.3/REMEDIATION_MASTER_PLAN.md`，只处理指定的 `<Wave/Task ID>`。开始前阅读对应模块的 findings、summary、test-design-register 和 evidence，并在当前 commit 上重新运行最小复现与 Stata 17 双跑。先建立因正确原因失败的回归测试，再确认计量公式、样本规则、自由度和 ResultSchema/API 语义，之后实施最小根因修复。不得顺手处理其他 finding，不得通过放宽 tolerance 掩盖差异，不得删除审查资产，不得推送内部 dev 到公开 GitHub。完成后运行 focused、audit、旧 golden、全量回归、compileall 和 wheel 验证，并撰写 remediation report，列出 fresh Stata evidence 与剩余风险。

建议按 R0 → R1 → R2 → R3 → R4 → R5 → R6 → R7 → R8 → R9 顺序安排独立 Agent。每个任务完成后先由审查 Agent复核，再开始依赖它的后续任务。
