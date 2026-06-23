# StataFlow 分模块独立全面审查任务书 v1.3

## 1. 文档用途

本文档用于指导后续 AI Agent 对 StataFlow 当前已经实现并公开声明支持的功能进行新一轮严格审查。

本轮工作的唯一目标是：

> 通过彼此独立、重新设计的计量实验，发现当前实现中仍然存在的数学错误、统计语义偏差、代码缺陷、边界条件错误、结果字段错误和 Stata 17 复现失败。

本轮不是开发轮，不新增功能，不修复代码，不扩大 API，不为已有实现寻找辩护。Agent 必须把每个命令族当作一个需要重新验证的独立研究对象。

审查基准为本地 `dev` 分支当前状态。开始工作前必须记录完整 commit SHA，不得用分支名称代替审查基线。

---

## 2. 核心原则：全新的独立验证

### 2.1 禁止把旧测试重复运行当作新证据

本轮双跑不得直接复用此前已经反复使用的测试设计，包括但不限于：

- 现有 `tests/golden/` 中的样本生成函数；
- 现有 `.do` 文件及其轻微改名版本；
- 现有固定随机种子、参数值和数据维度；
- 现有 `stata/cases/` 中的数据文件；
- 现有真实数据实验的相同模型规格；
- 从旧测试复制后只增加一列、改一个变量名或调整样本量；
- 读取旧 Stata 日志并把其中数值作为新的 expected value；
- 使用 Python 当前实现生成“真值”，再检查 Python 自己；
- 只运行现有测试并根据通过情况宣布功能正确。

旧测试、旧审查报告和旧 findings 只能用于：

1. 了解已声明的支持边界；
2. 查找可能遗漏的风险区域；
3. 避免重复报告已知问题；
4. 设计更强、更不同的新实验。

它们不能作为本轮结论的主要验证证据。

### 2.2 什么叫“新的测试方式”

每个模块必须重新完成以下工作：

1. 从计量原理出发提出新的数据生成过程（DGP）或经验研究设计；
2. 独立编写新的 Stata 17 `.do` 文件；
3. 独立编写新的 Python 测试或审查脚本；
4. 使用新的随机种子、样本结构、参数和退化场景；
5. 明确写出理论上应该成立的性质；
6. 同时检查 Stata 与 Python 的完整结果字段，而不只比较系数；
7. 对发现的偏差构造最小复现案例；
8. 保存可重复执行的原始输入、日志和结构化差异结果。

可以复用项目的通用执行基础设施，例如 `StataRunner`、日志解析器和数值比较辅助函数，但不得复用旧实验的经济设计、数据、命令脚本或 expected values。

### 2.3 测试独立性登记

每个新实验都必须在报告中回答：

- 它与哪个已有测试最相近？
- 数据、模型规格和目标字段与旧测试有什么实质差异？
- 为什么这个实验能够发现旧测试不容易发现的问题？
- Stata 输出是否由本轮现场执行产生？

如果无法说明实质差异，该实验不得计入本轮有效证据。

---

## 3. 审查组织方式

### 3.1 一个模块一次独立执行

每个 Agent 或每个 goal 只负责一个模块。不得在同一轮中同时审查 Linear、HDFE、IV 等多个模块。

每个模块必须拥有独立的：

- 审查计划；
- 新测试设计；
- Stata 双跑文件；
- 执行日志；
- findings；
- 结论与未决事项。

共享基础设施问题可以登记为 Shared finding，但不得因此停止当前模块审查。Agent 应同时说明该共享问题如何影响本模块。

### 3.2 模块清单

| 编号 | 模块 | 主要对象 |
|---|---|---|
| M01 | Linear | `OLS`、`regress()`、权重、robust/cluster VCE |
| M02 | Panel / FE | `FixedEffectsOLS`、`xtreg_fe()`、`areg()` |
| M03 | HDFE | `AbsorbingOLS`、`reghdfe()`、MAP/LSDV、斜率吸收 |
| M04 | IV / GMM | `IV2SLS`、`IVAbsorbingOLS`、`ivregress_2sls()`、`ivreghdfe()` |
| M05 | GLM | `Logit`、`Probit`、`Poisson` 及 wrappers |
| M06 | PPMLHDFE | `PPMLHDFE`、`ppmlhdfe()`、分离与吸收 |
| M07 | DID / Event Study | `DIDImputation`、`EventStudyInteract`、`CSDID` |
| M08 | RD | `RDRobust`、`rdrobust()`、`rdplot()` |
| M09 | Postestimation | `predict`、`margins`、`estat`、结果传播 |
| M10 | Shared Infrastructure | factor variables、VCE、ResultSchema、sample mask、StataRunner |

M01-M10 均应独立执行。不得因为某个上游模块通过，就推断下游模块正确。

---

## 4. 每个模块必须完成的审查层次

### 4.1 支持边界核对

逐项核对：

- public API、compat wrapper 和文档声明是否一致；
- 参数默认值是否符合 Stata；
- 已知但未实现的选项是否明确报错；
- 未知参数是否硬拒绝；
- 核心 estimator 与 wrapper 是否产生相同统计语义；
- `ResultSchema` 是否完整表达该命令的返回结果；
- 文档是否夸大当前支持范围。

### 4.2 数学与计量原理审查

Agent 必须自己推导或查证：

- 目标函数或 estimating equations；
- 系数估计公式；
- 样本筛选规则；
- 常数项处理；
- 共线性和秩判定；
- 权重语义与归一化；
- 方差协方差矩阵；
- 小样本修正；
- 自由度；
- 整体检验统计量；
- 聚类层级；
- 迭代收敛与失败条件；
- 对应 Stata `e()` / `r()` 字段的定义。

不能仅凭“公式看起来合理”判定正确。关键公式必须和 Stata 17 官方手册、公开社区命令源码或权威论文建立明确对应。

### 4.3 代码实现审查

必须沿完整调用链检查：

`compat wrapper -> 数据准备 -> estimator -> VCE -> ResultSchema -> postestimation`

重点寻找：

- 错误样本被纳入或正确样本被剔除；
- 索引重排、重复索引和 merge 导致错位；
- 输入 DataFrame 被意外修改；
- NaN、Inf、空组和单元素组处理错误；
- 常数项或虚拟变量顺序不一致；
- 丢弃共线变量后名称、系数和协方差矩阵错位；
- 不收敛仍返回可用结果；
- 伪逆掩盖识别失败；
- 数值裁剪掩盖负方差或非 PSD 问题；
- wrapper 静默忽略参数；
- schema 字段由近似值、错误样本或错误自由度生成；
- Stata 风格输出与结构化结果互相矛盾。

### 4.4 新 synthetic 双跑

每个模块至少建立 6 个全新 synthetic 设计，建议覆盖：

1. 手工可计算的小样本；
2. 中等样本随机 DGP；
3. 缺失值与 estimation sample；
4. 共线性、弱识别或近奇异设计；
5. robust/cluster/多维 cluster 或模块适用的 VCE；
6. 极端尺度、稀有事件、单元格稀疏或数值病态场景。

不得六个实验只改变随机种子。它们必须检验不同的统计机制。

### 4.5 新真实数据双跑

每个模块至少设计 2 个新的真实数据实验：

- 优先使用公开、可追溯、允许再分发的数据；
- 不得重复此前同一数据集上的同一回归规格；
- 即使使用已有数据，也必须提出新的研究问题、变量构造或识别设计；
- 必须保存数据来源、下载日期、哈希和预处理脚本；
- 至少一个实验应接近该模块的典型实证用途；
- 至少一个实验应主动施加困难条件，例如不平衡面板、多层聚类、稀有事件或弱工具变量。

真实数据结果不能替代 controlled synthetic 验证。

### 4.6 变形与性质测试

除直接数值双跑外，每个模块至少设计 3 个 metamorphic/property tests，例如：

- 行顺序改变不应改变结果；
- 分类变量标签的一一重命名不应改变估计；
- 合法尺度变换应产生可推导的系数与 VCE 变化；
- 增加不参与估计的无关列不应改变结果；
- 重复索引不应导致样本错位；
- 等价参数化应保持 fitted values 或目标统计量不变；
- 聚类标签置换不应改变 cluster VCE；
- 吸收 FE 与显式虚拟变量在适用条件下应等价。

这些性质必须同时在 Python 与 Stata 端验证，或给出明确的理论真值。

---

## 5. 各模块最低审查问题

### M01 Linear

- OLS 正规方程、QR/伪逆路径和秩判定；
- 常数项、`df_model`、`df_resid`；
- RSS/TSS/MSS、R2、adjusted R2、RMSE、F；
- HC 类 robust VCE 与 cluster 小样本修正；
- aweight 的样本筛选和归一化；
- 单 cluster、完全拟合、常数因变量和极端尺度；
- factor variables、交互项和 base level。

建议新设计：异方差结构已知的 DGP、组大小高度不均衡的 cluster DGP、带零/缺失权重的设计、近共线缩放实验。

### M02 Panel / FE

- within transformation 与 LSDV 等价；
- 组内无变异变量的删除；
- 不平衡面板、singleton、缺失期；
- FE 自由度、常数项和 overall/within/between 统计量；
- FE 内聚类与 FE 外聚类；
- `xtreg_fe()` 与 `areg()` 的语义差异。

建议新设计：不同组长度的动态面板形状、组内零方差 regressor、cluster 与 panel id 不一致的层级设计。

### M03 HDFE

- 多向吸收的投影数学；
- MAP/LSDV/LSMR 一致性与收敛；
- disconnected FE graph 与冗余自由度；
- nested FE 与 cluster 修正；
- singleton 递归删除；
- heterogeneous slopes；
- 多维 cluster inclusion-exclusion 与 PSD 处理；
- `_cons`、savefe、sample mask 和重复索引。

建议新设计：非连通二部图、FE 高度嵌套、交叉分类、病态斜率吸收、不同量纲下的 PSD 修复。

### M04 IV / GMM

- 2SLS、GMM2S、LIML、k-class 公式；
- 排除限制、rank condition 和 underidentification；
- 弱工具变量诊断；
- 第一阶段字段与主方程样本一致性；
- robust、cluster、HAC 与 HDFE VCE；
- endogenous/exogenous/instrument 缺失筛选；
- 多 endogenous、多 instrument 和恰好识别；
- overidentification、first-stage F 和自由度。

建议新设计：可控制 concentration parameter 的 DGP、多内生变量、近秩亏、聚类冲击与工具变量强度异质设计。

### M05 GLM

- log-likelihood、score、Hessian 和信息矩阵；
- logit/probit link、Poisson mean；
- 因变量合法域；
- 完全/准完全分离；
- 不收敛、迭代上限和错误状态；
- robust/cluster VCE；
- log likelihood、deviance、pseudo R2、整体检验；
- predict 与 margins 所使用的样本和协方差。

建议新设计：稀有事件 logit、近分离 probit、过度离散但均值正确的 Poisson、offset/exposure 边界（仅在声明支持时）。

### M06 PPMLHDFE

- IRLS/牛顿迭代与吸收步骤；
- separation 检测和样本删除；
- 零 outcome、高维 FE 和 singleton；
- robust/cluster/multiway cluster VCE；
- eform、predict 与固定效应恢复；
- 收敛阈值和缩放敏感性。

建议新设计：大量零值贸易流、结构性零与抽样零并存、分离由 FE 或连续变量触发、极端均值尺度。

### M07 DID / Event Study

- cohort、never-treated、not-yet-treated 定义；
- base period 与 event-time 编码；
- anticipation、缺失期和不平衡面板；
- ATT(g,t) 权重与 aggregation；
- influence function 与 custom cluster；
- pretrend joint test；
- covariates、DR/RA/IPW 路径；
- 重复 unit-time、变化的 first_treat 和无有效对照组。

建议新设计：处理效应按 cohort/event time 异质、选择进入处理、缺失面板、cluster 跨多个 unit、无 never-treated 的 staggered adoption。

### M08 RD

- 局部多项式设计矩阵；
- kernel 权重；
- sharp/fuzzy estimand；
- bandwidth selection；
- bias correction 与 conventional/robust inference；
- mass points、cluster、weights、covariates；
- cutoff 附近稀疏和单侧支持不足；
- `rdplot` bin selection 与绘图数据。

建议新设计：曲率不对称、密度跳跃、离散 running variable、弱 fuzzy first stage、clustered running variable。

### M09 Postestimation

- predict 类型与模型族匹配；
- estimation sample 与样本外预测；
- stdp、残差、线性预测和响应尺度；
- margins 的离散变化、导数和 delta method；
- factor/interactions 的支持边界；
- `estat summarize/vce/ic` 字段来源；
- 行重排、重复索引、缺失数据后的结果传播。

建议新设计：相同模型的手工 delta-method 校验、离散变量 average marginal effect、样本外新 factor level、协方差含非零交叉项。

### M10 Shared Infrastructure

- factor parser 与 Stata base/operator 语义；
- VCE 公共函数的维度、秩和修正；
- ResultSchema 的行名与矩阵不变量；
- sample mask 与原始行映射；
- StataRunner 路径、日志、返回码和并发安全；
- parser 对科学计数法、无前导零、缺失值和本地化输出的处理；
- exports、版本和文档支持矩阵一致性。

建议新设计：包含空格/Unicode 的路径、重复索引、空模型、零维协方差矩阵、失败 Stata 进程和残缺日志。

---

## 6. 双跑比较字段

适用时必须逐字段比较：

- estimation sample 和 `nobs`；
- coefficient names/order；
- coefficients；
- 完整 VCE matrix，而不只是标准误；
- standard errors；
- t/z statistics；
- p-values 和 confidence intervals；
- `df_model`、`df_resid`；
- RSS/TSS/MSS/RMSE/R2；
- F/Wald/LR statistics 及 p-value；
- cluster count、FE count、singleton count；
- log likelihood、deviance、information criteria；
- first-stage、weak-IV、pretrend 或 bandwidth 等模块字段；
- sample mask；
- predict、margins 和 estat 输出；
- warning/error behavior。

默认相对误差标准为 `< 1e-6`。任何放宽都必须记录字段、数量级、理论原因和 Stata/Python 原始值，不得以“统计上差不多”直接关闭。

---

## 7. 问题分级与证据等级

### 7.1 严重性

- **P0**：结果方向、样本、识别或推断严重错误；可能无提示返回错误结果。
- **P1**：核心字段或常用路径与 Stata 明显不一致；崩溃；错误 VCE/df。
- **P2**：边界条件、次要字段、错误类型、文档/API 契约问题。
- **P3**：低风险可维护性、诊断信息或测试证据缺口。

### 7.2 证据状态

- **Confirmed-Stata**：新 Stata 17 双跑稳定复现。
- **Confirmed-Math**：具有可核验的解析真值或严格推导。
- **Confirmed-Code**：确定的代码不变量破坏，可用最小案例复现。
- **Suspected**：存在强烈风险，但尚未完成独立证据闭环。
- **Coverage Gap**：只确认缺少证据，不得写成算法错误。

每个 finding 必须明确区分“已经证明错误”和“尚未充分验证”。

---

## 8. 目录与交付物

每个模块使用独立目录：

```text
docs/audit/modular-revalidation-v1.3/
  MASTER_AUDIT_BRIEF.md
  M01-linear/
  M02-panel-fe/
  M03-hdfe/
  M04-iv-gmm/
  M05-glm/
  M06-ppmlhdfe/
  M07-did-event-study/
  M08-rd/
  M09-postestimation/
  M10-shared-infrastructure/
```

每个模块至少交付：

```text
Mxx-module/
  task_plan.md
  test-design-register.md
  findings.md
  progress.md
  summary.md
  evidence/
    synthetic/
    real-data/
    minimal-reproductions/
```

可执行的新测试资产应放在项目既有测试/验证目录中，并采用 `v1_3` 或 `modular_revalidation` 标识，避免和产品回归测试混淆。Agent 必须在模块报告中列出全部新增资产路径。

### `test-design-register.md` 必填字段

每个实验记录：

- test ID；
- 审查问题；
- DGP 或经验设计；
- 理论预期；
- 新颖性说明；
- Stata 命令；
- Python API；
- 比较字段；
- 数据来源/seed/hash；
- 执行结果；
- evidence 路径。

### `findings.md` 必填字段

每个问题记录：

- finding ID，例如 `M03-HDFE-001`；
- severity；
- evidence status；
- affected API；
- 最小复现步骤；
- Stata 17 结果；
- Python 结果；
- 数学或代码根因分析；
- 用户影响；
- 受影响范围；
- 是否可能为共享基础设施问题；
- 当前是否存在旧 issue；
- 建议修复方向，但本轮不得实施修复。

---

## 9. 标准执行流程

每个模块严格按以下顺序执行：

1. 记录基线 commit、Python、依赖和 Stata 版本；
2. 阅读对应 public API、support matrix、研究档案和实现文件；
3. 建立模块功能清单与数学公式清单；
4. 阅读旧测试，仅用于覆盖地图，不复制测试；
5. 编写 `test-design-register.md`；
6. 先完成手工真值和 synthetic 设计；
7. 独立编写并运行 Stata `.do`；
8. 独立运行 Python；
9. 生成字段级差异；
10. 设计真实数据实验；
11. 执行 metamorphic/property tests；
12. 对每个异常构造最小复现；
13. 检查是否为测试、parser、runner 或 estimator 本身的问题；
14. 写入 `findings.md`；
15. 运行现有非 golden 测试，确认审查资产没有破坏仓库；
16. 写出模块 `summary.md`，明确通过项、失败项和未验证项。

---

## 10. Stata 执行规范

本机 Stata 17：

```text
D:\Software\Stata17\StataMP-64.exe
```

批处理基准：

```text
StataMP-64.exe /e do <new-audit-file.do>
```

要求：

- 所有 `.do` 文件必须由本轮新建；
- 日志必须保留命令、版本、样本数和关键 `e()`/`r()` 字段；
- 不得从旧日志复制结果；
- 每次执行保存时间、退出状态和日志哈希；
- Stata 执行失败必须先判断是脚本、依赖命令、路径还是产品问题；
- 社区命令版本必须记录 `which` 输出和 ado 路径；
- 双跑资产不得包含 Stata 许可证或不可公开数据。

---

## 11. 本轮禁止事项

Agent 不得：

- 修改 `src/stataflow/` 中的产品代码；
- 为使测试通过而调整容差；
- 修改旧 golden expected values；
- 把旧测试包装一层后声称是新实验；
- 只比较 coefficients 而忽略 VCE、df 和 sample；
- 把 parser 错误直接归因于 estimator；
- 把测试缺口写成 confirmed bug；
- 因已有审查声称“已修复”而跳过独立验证；
- 因现有测试通过而关闭新发现；
- 在未保存 Stata 原始证据时写 `Confirmed-Stata`；
- 同时修复发现的问题；
- 推送、创建 PR 或合并到 GitHub，除非用户另行明确授权。

若审查必须临时编写辅助代码，只能用于测试、数据生成、日志解析和证据整理，并必须与产品实现隔离。

---

## 12. 模块完成门槛

一个模块只有在以下条件全部满足后才可标记为审查完成：

- [ ] 当前支持能力逐项建立审查矩阵；
- [ ] 关键数学公式与 Stata 语义已核对；
- [ ] 至少 6 个实质不同的新 synthetic 双跑；
- [ ] 至少 2 个新的真实数据实验；
- [ ] 至少 3 个 metamorphic/property tests；
- [ ] 关键结果使用完整字段级比较；
- [ ] 所有异常均已区分产品、测试、runner 和 parser 根因；
- [ ] 每个 confirmed finding 均有最小复现；
- [ ] 未复现或未验证部分明确列出，不得默认通过；
- [ ] `findings.md`、`progress.md`、`test-design-register.md` 和 `summary.md` 完整；
- [ ] 本轮没有修改产品代码；
- [ ] 审查资产可以从干净环境重复执行。

“未发现问题”不能仅由测试全部通过得出。Agent 必须说明检查了哪些输入域、哪些数学机制和哪些未覆盖区域。

---

## 13. 推荐的 Agent goal

每次只启动一个模块，可使用以下任务表达：

> 严格执行 `docs/audit/modular-revalidation-v1.3/MASTER_AUDIT_BRIEF.md`，仅审查模块 `Mxx`。本轮只发现和记录问题，不修改产品代码。必须设计全新的 synthetic、真实数据和性质测试，不得复用旧 golden 测试的 DGP、脚本、数据、随机种子或 expected values。使用本地 Stata 17 现场完成字段级双跑，并将全部计划、测试登记、证据、findings、进度和总结写入该模块目录。不要开始其他模块，不要推送 GitHub。

建议为 M01-M10 分别启动独立 goal 或独立 Agent 会话。一个模块完成并经过人工复核后，再开始下一个模块。

---

## 14. 最终总验收

所有模块结束后，另行安排一个不参与模块审查的总审查 Agent：

1. 检查 M01-M10 是否满足完成门槛；
2. 合并重复 finding，但保留各模块原始证据；
3. 识别跨模块共同根因；
4. 检查严重性和证据等级是否一致；
5. 形成全局问题清单和后续修复任务，而不是直接修改代码；
6. 明确哪些公开功能仍不能宣称严格复现 Stata 17。

本轮最终产物应是一组相互独立、可复跑、能经受反证的模块审查证据，而不是对旧测试套件的再次确认。
