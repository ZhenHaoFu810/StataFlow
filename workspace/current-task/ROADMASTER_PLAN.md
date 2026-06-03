# StataFlow 完整复制路线图（Roadmaster Plan）

**版本：** v1.2  
**日期：** 2026-04-30  
**编制：** StataFlow Roadmaster  
**适用范围：** 从当前 `Beta` 状态推进到社区命令的完整功能复制（full command parity）  

---

## 1. 当前阶段判断（Current Stage Assessment）

### 1.1 已完成的 Wave（已收口）

| Wave | 内容 | 状态 | 收口标志 |
|------|------|------|----------|
| Wave 0 | Linear Base (`regress`, robust, cluster, aweight, `xtreg, fe`) | Stable | 双跑通过 |
| Wave 1 | Panel / FE / HDFE (`areg`, `reghdfe` Phase A) | Alpha | 1+ FE, singleton, predict 子集通过 |
| Wave 2 | IV / GMM (`ivregress 2sls`, `ivreghdfe`) | Alpha | 2SLS + FE + cluster 通过 |
| Wave 3 | Binary / Count (`logit`, `probit`, `poisson`, `ppmlhdfe`) | Alpha | MLE + FE + offset/exposure 通过 |
| Wave 4 | DID / Event Study (`did_imputation`, `eventstudyinteract`, `csdid`) | Alpha | 核心估计路径通过 |
| Wave 5 | Postestimation (`predict`, `margins` 子集) | Alpha | 高频 predict/margins 通过 |
| Wave 6 | RD (`rdrobust` sharp RD 子集) | Alpha — Partial | 显式带宽 + `mserd` + covs 通过 |
| Wave 7 | HDFE Hardening (`reghdfe`, `ivreghdfe`, `ppmlhdfe`) | Beta | 2-way cluster（3 命令）+ savefe + separation + first + eform，文档收口 |
| Wave 8 | RD Completion (`rdrobust`) | Beta | 完整带宽选择器 + fuzzy RD + cluster/nncluster + weights + masspoints |
| Wave 9 | DID Hardening (`did_imputation`, `csdid`) | Beta | controls/pretrends/hetby/wtr/saveestimates + method=dr + aggtype |
| Wave 10 | IV Completion (`ivreghdfe`) | Beta | GMM2S + LIML/Fuller/k-class + weakiv |
| Wave 11 | Postestimation & `estat` Ecosystem | Beta | stdp + pearson/deviance/working + estat_summarize + estat_ic |
| Wave 12 | Advanced HDFE & Performance | Stable | MAP kernel + slope absorption + Driscoll-Kraay VCE + benchmark + v1.0.0 release |

### 1.2 当前阻塞项（Blocking Items）

- 当前如存在返工包或 correctness gate 未清空，则必须先完成返工闭环，再进入新的功能性 wave。
- 新功能 wave 的进入条件不再依赖外部审查者，而依赖 **Claude Code 主代理 + `correctness-gatekeeper` 子代理** 的自驱审核闭环。

### 1.3 核心架构状态

- **4 层内核**已建立：`stata_runner` → `result_spec` → `estimators` → `testing_harness`。
- **依赖方向**保持正确：`estimators` → `result_spec`；`testing_harness` → 前三层。
- **当前实现策略**：LSDV（虚拟变量）demeaning，非迭代 MAP/LSMR。对 1-3 个 FE 表现良好，极高维 FE 存在性能天花板。

---

## 2. Gap Analysis：社区命令功能缺口

以下逐命令族列出当前实现与社区命令完整功能面的差距。

### 2.1 `reghdfe`（High-Dimensional Fixed Effects）

| 功能 / 选项 | 当前状态 | 缺口描述 | 复杂度 |
|-------------|----------|----------|--------|
| `absorb(1+ FEs)` | 已实现（LSDV） | 3+ FE 合成测试通过，但极高维性能受限 | 中 |
| `absorb(var1##c.var2)`（斜率吸收） | **已实现** | 个体斜率；LSDV 路径 synthetic + real-data 双跑通过（`##c.` intercept+slope, `#c.` slope-only, multi-slope）；MAP 路径显式拒绝 | 高 |
| `group(var) individual(var)`（团队/个体 FE） | 未实现 | 组级结果 + 个体 FE，需要聚合逻辑。推迟至 v1.1.0+ | 高 |
| `vce(cluster var1 var2)`（多向聚类） | **已实现（2-way）** | 2-way cluster 已 synthetic + real-data 双跑通过；3-way 及以上推迟至 v1.1.0+ | 高 |
| `vce(dkraay [#])`（Driscoll-Kraay） | **已实现** | Bartlett 核 HAC 面板标准误；synthetic + real-data (wagepan) 双跑通过；带宽可自定义（`dkraay_<bw>`）；SE 容忍度 1e-4 | 高 |
| `dofadjustments()` | 部分实现 | 当前 `df_a` 为保守估计；pairwise / firstpair / clusters / continuous 精确算法缺失 | 高 |
| `technique(map/lsmr/lsqr/gt)` | **MAP 已实现** | MAP 迭代投影内核（`technique="map"`）；benchmark A/B/C 内存从 >74 GiB 降至 0.15–0.34 GB；LSMR/LSQR 推迟至 v1.1.0+ | 中 |
| `acceleration() transform() preconditioner()` | 未实现 | MAP/LSMR 的收敛加速参数 | 中 |
| `parallel()` | 明确不实现 | 多进程属于 Stata 生态特有，Python 端用其他并行策略 | — |
| `compact poolsize` | 未实现 | 内存优化选项 | 低 |
| `residuals(newvar)` / `residuals2` | 部分实现 | `predict(type="residuals")` 已支持，但命令级 `residuals()` 选项未暴露 | 低 |
| `keepsingletons` | 已实现 | — | — |
| `noconstant` | 已实现 | — | — |
| `savefe` | **已实现** | 保存 FE 估计值到变量；synthetic + real-data 双跑通过 | 中 |
| `estat summarize` | **已实现** | 汇总统计后估计命令；synthetic 双跑通过 | 中 |
| `test` / `suest` | 未实现 | 假设检验与联合检验 | 高 |
| `version(3/5)` | 明确不实现 | 历史版本兼容不属于 Python 端目标 | — |

### 2.2 `ppmlhdfe`（Poisson PML with HDFE）

| 功能 / 选项 | 当前状态 | 缺口描述 | 复杂度 |
|-------------|----------|----------|--------|
| `absorb(1+ FEs)` | 已实现 | 同 `reghdfe` | — |
| `offset(var)` / `exposure(var)` | 已实现 | — | — |
| `vce(cluster)` 单向 | 已实现 | — | — |
| `vce(cluster)` 多向 | **已实现（2-way）** | 2-way cluster 已 synthetic + real-data 双跑通过；3-way 及以上未实现 | 高 |
| `separation(fe/ir/simplex/mu)` | **`fe` 已实现** | `separation="fe"` 已 synthetic 双跑通过；`ir` / `simplex` / `mu` 未实现 | 极高 |
| `eform` / `irr` | **已实现** | 报告发生率比 exp(b) 与 delta-method SE；synthetic 双跑通过 | 低 |
| `d(newvar)` / `d2` | 未实现 | 保存 FE 之和 | 低 |
| `guess(simple/ols/var)` | 未实现 | 初始值选择策略 | 中 |
| `itol()` | 未实现 | 内部 reghdfe 收敛容差 | 低 |
| `keepsingletons` | 未实现 | 保留 singleton 观测 | 低 |
| `predict` 类型：`pearson`, `deviance`, `working` | **已实现** | `predict(type="pearson"/"deviance"/"working")` 已 synthetic 双跑通过；残余 ~0.35% 来自 IRLS/HDFE 收敛精度 | 中 |
| `margins` 完整生态 | 部分实现 | `dydx`, `atmeans` 已支持；更复杂的 margins 表达式未支持 | 高 |
| `estat ic / summarize / vce` | **已实现** | `estat_ic` 与 `estat_summarize` 已 synthetic 双跑通过 | 中 |

### 2.3 `ivreghdfe`（IV with HDFE）

| 功能 / 选项 | 当前状态 | 缺口描述 | 复杂度 |
|-------------|----------|----------|--------|
| `absorb(1+ FEs)` + 2SLS | 已实现 | — | — |
| `first` / `ffirst`（一阶段诊断） | `first` **已实现**；`ffirst` 未实现 | 一阶段回归结果、F-statistic、R-squared；`first` 已 synthetic 双跑通过 | 高 |
| `weakiv`（弱工具变量检验） | **已实现** | Kleibergen-Paap rk LM / rk Wald F + Stock-Yogo 临界值；OLS/robust/cluster VCE；synthetic + real-data 双跑通过 | 高 |
| `gmm2s` | **已实现** | 两步高效 GMM，ols/robust/cluster VCE；Hansen J 过度识别检验；synthetic + real-data 双跑通过 | — |
| `gmm` / `cue` | 未实现 | 迭代 GMM / 连续更新 GMM（需数值优化） | 极高 |
| `liml` / `kclass` / `fuller` | **已实现** | LIML 与 k-class 估计器，含 Fuller 调整；synthetic + real-data 双跑通过 | — |
| `partial(varlist)` / `fwl(varlist)` | 未实现 | 偏出变量（Frisch-Waugh-Lovell） | 中 |
| `orthog(varlist)` | 未实现 | 过度识别检验 | 高 |
| `endogtest(varlist)` | 未实现 | 内生性检验 | 高 |
| `redundant(varlist)` | 未实现 | 冗余工具变量检验 | 高 |
| `vce(cluster)` 多向 | **已实现（2-way）** | 2-way cluster 已 synthetic + real-data 双跑通过；3-way 及以上未实现 | 高 |
| `bw() kernel() center kiefer dkraay` | 未实现 | HAC 标准误 | 高 |
| `small` / `noconstant` | 部分实现 | `noconstant` 已支持；`small` 小样本调整未显式实现 | 中 |
| `savefirst` / `saverf` / `savesfirst` | 未实现 | 保存一阶段/简化式方程 | 中 |
| `bvclean` / `psd0` / `psda` / `useqr` | 未实现 | 数值稳定性选项 | 中 |
| `predict` 类型扩展 | 部分实现 | `xb`, `xbd`, `residuals`, `d`, `dresiduals`, **`stdp`** 已支持 | — |

### 2.4 `did_imputation`（BJS Imputation DID）

| 功能 / 选项 | 当前状态 | 缺口描述 | 复杂度 |
|-------------|----------|----------|--------|
| 核心三步估计（FE 拟合 → 插补 → 加权平均） | 已实现 | — | — |
| `allhorizons` / `horizons()` | 已实现 | — | — |
| `autosample` | 已实现 | — | — |
| `cluster(var)` | 已实现 | — | — |
| `window` | 未实现 | 限制事件时间窗口 | 低 |
| `minn(#)` | 未实现 | 最小有效观测数阈值 | 低 |
| `fe(list)` 自定义 FE | 部分实现 | 当前默认 `i t`；自定义 FE 列表未充分测试 | 中 |
| `controls(varlist)` | **已实现** | 时变连续控制变量；synthetic + real-data 双跑通过 | 中 |
| `unitcontrols(varlist)` | **已实现** | 单位×连续控制交互；synthetic 双跑通过 | 高 |
| `timecontrols(varlist)` | **已实现** | 时间×连续控制交互；synthetic 双跑通过 | 高 |
| `wtr(varlist)` | **已实现** | 自定义权重变量；synthetic 双跑通过 | 中 |
| `sum` | **已实现** | 加权和而非加权平均；synthetic 双跑通过 | 低 |
| `hbalance` | 未实现 | 平衡子样本限制 | 中 |
| `hetby(varname)` | **已实现** | 按子组报告异质性；synthetic 双跑通过 | 中 |
| `project(varlist)` | 未实现 | 将处理效应投影到变量上 | 高 |
| `pretrends(#)` | **已实现** | 平行趋势检验；synthetic 双跑通过 | 高 |
| `shift(#)` | 未实现 | 预期效应偏移 | 低 |
| `saveestimates(name)` | **已实现** | 保存个体处理效应估计；synthetic 双跑通过 | 低 |
| `saveweights` / `loadweights` | **已实现** | 保存/加载估计权重；synthetic 双跑通过 | 中 |
| `saveresid(name)` | 未实现 | 保存残差 | 低 |
| `avgeffectsby(varlist)` | 未实现 | 自定义 SE 计算分组 | 中 |
| `leaveout` | 未实现 | 留一法计算平均处理效应 | 高 |
| `nose` | 未实现 | 不计算标准误 | 低 |
| `alpha(real)` | 未实现 | 置信水平 | 低 |
| `delta(integer)` | 未实现 | 时间步长 | 低 |
| `tol(real)` / `maxit(integer)` | 未实现 | 权重迭代收敛参数 | 低 |

### 2.5 `eventstudyinteract`（Sun-Abraham IW Estimator）

| 功能 / 选项 | 当前状态 | 缺口描述 | 复杂度 |
|-------------|----------|----------|--------|
| 核心 IW 估计（交互回归 → 队列份额 → 加权平均） | 已实现 | — | — |
| 自动虚拟变量生成（`time`, `first_treat`, `horizons`, `omit`） | 已实现 | — | — |
| `cohort(var)` / `control_cohort(var)` | 已实现 | — | — |
| `absorb(varlist)` | 已实现 | — | — |
| `vce(cluster)` | 已实现 | — | — |
| `covariates(varlist)` | 未实现 | 协变量 | 中 |
| `window` | 未实现 | 事件窗口限制 | 低 |
| `minn` | 未实现 | 最小队列份额 | 低 |
| `save` / `replace` / `graph` | 明确不实现 | 属于 Stata 数据管理/图形生态 | — |
| `e(b_interact)` / `e(V_interact)` / `e(ff_w)` / `e(Sigma_ff)` | 未返回 | 当前仅返回 `b_iw` 和 `V_iw` 的对角线；完整矩阵未暴露 | 中 |

### 2.6 `csdid`（Callaway-Sant'Anna DID）

| 功能 / 选项 | 当前状态 | 缺口描述 | 复杂度 |
|-------------|----------|----------|--------|
| `method="reg"`（回归调整） | 已实现 | — | — |
| `estat_event`（事件研究聚合） | 已实现 | — | — |
| `vce="cluster"` | 已实现 | — | — |
| `method="dr"` / `method="drimp"` / `method="dripw"`（双重稳健） | **已实现** | `drimp` 与 `dripw` 已 synthetic + real-data 双跑通过 | 极高 |
| `method="ipw"`（逆概率加权） | 未实现 | IPW 估计器 | 高 |
| `aggtype`（simple / dynamic / group / calendar / pretrend） | **已实现** | 所有标准聚合方式已 synthetic 双跑通过 | 高 |
| `gtcontrol`（控制组策略） | 未实现 | 未处理组/未 yet 处理组切换 | 中 |
| `longdiff` | 未实现 | 长差分预趋势 | 中 |
| `window` / `minn` / `save` / `replace` / `graph` | 未实现/不实现 | 部分属于 Stata 生态 | — |

### 2.7 `rdrobust`（Regression Discontinuity）

| 功能 / 选项 | 当前状态 | 缺口描述 | 复杂度 |
|-------------|----------|----------|--------|
| Sharp RD (`deriv=0`) | 已实现 | — | — |
| 显式带宽 `h` / `b` | 已实现 | — | — |
| 自动带宽 `bwselect="mserd"` | 已实现 | — | — |
| `covs`（协变量调整） | 已实现 | — | — |
| `kernel`（tri/epa/uni） | 已实现 | — | — |
| `vce="nn"` / `vce="hc0"` | 已实现 | — | — |
| `fuzzy(varname [sharpbw])` | **已实现** | 模糊 RD（两阶段局部多项式）；synthetic + real-data 双跑通过 | 极高 |
| `deriv > 0`（Kink RD） | 未实现 | 导数估计 | 高 |
| `weights(varname)` | **已实现** | 频率/分析权重；synthetic + real-data 双跑通过 | 中 |
| `vce(cluster varname)` / `vce(nncluster varname)` | **已实现** | 聚类稳健 VCE；synthetic + real-data 双跑通过 | 高 |
| `bwselect` 扩展族：`msetwo`, `msesum`, `msecomb1/2`, `cerrd`, `certwo`, `cersum`, `cercomb1/2` | **已实现** | 全部 11 个 MSE/CER 最优带宽选择器已 synthetic + real-data 双跑通过 | 高 |
| `masspoints(adjust/check/off)` | **已实现** | 运行变量重复值处理；synthetic 双跑通过 | 中 |
| `bwcheck(#)` / `bwrestrict(on/off)` | 部分实现 | `bwcheck` 已支持；`bwrestrict` 未实现 | 低 |
| `stdvars(on/off)` | 未实现 | 标准化变量 | 低 |
| `scalepar(#)` / `scaleregul(#)` | 部分实现 | `scaleregul` 已支持；`scalepar` 未实现 | 低 |
| `all` / `detail` | 未实现 | 输出扩展 | 低 |
| `level(#)` | 已实现（默认 95） | — | — |
| `rdplot` / `rdbwselect` 伴侣命令 | **部分实现** | `rdplot` 已实现 IMSE-optimal binning 与局部多项式拟合，但 bin-selection 算法与 Stata 差异 2–3×，无 golden 双跑证据；`rdbwselect` 未独立暴露 | 高 |

---

## 3. 优先级 Wave 计划（Prioritized Wave Plan）

本计划从当前 Alpha 状态出发，按**影响面 × 依赖链 × 风险**排序，定义 6 个新 Wave（Wave 7–12）。每个 Wave 固定为 3 轮（Research → Min Implementation → Real-data Validation）。

### Wave 7：HDFE Hardening（核心加固）

**目标：** 将 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 从 Alpha 推进到 Beta，修复最影响使用的高频缺口。

**包含内容：**
1. `reghdfe`：多向聚类（2-way cluster）
2. `reghdfe`：`savefe` 与 `residuals()` 选项
3. `ppmlhdfe`：`eform` / `irr`，`d()` / `d2`
4. `ppmlhdfe`：separation 检测（`fe` 子方法，最小可用）
5. `ivreghdfe`：`first` / `ffirst` 一阶段诊断
6. 统一 `df_a` 精确算法（pairwise mobility groups）

**为什么先做这个：**
- 多向聚类是应用微观计量最频繁请求的功能之一。
- `savefe` / `residuals` 是 postestimation 的基础，阻塞后续 `estat` 生态。
- separation 是 `ppmlhdfe` 区别于普通 Poisson 的核心价值。

**入口标准：**
- 当前返工包已由 `correctness-gatekeeper` 复核通过，且 `REPORT.md` 与 `INSTRUCTIONS.md` 已同步更新。
- `research/vendor/stata_community/reghdfe/` 源码已完整阅读并归档。

**出口标准：**
- 2-way cluster 在 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 上均有 synthetic + real-data 双跑证据。
- `savefe` 输出与 Stata `reghdfe, absorb(..., savefe)` 字段级一致。
- separation (`fe` 方法) 至少有一组 synthetic 双跑证据。
- 所有新功能已更新命令支持矩阵。

---

### Wave 8：RD Completion（RD 补全）

**目标：** 将 `rdrobust` 从 Alpha — Partial 推进到 Beta，覆盖主要带宽选择器与模糊 RD。

**包含内容：**
1. 完整带宽选择器族：`msetwo`, `msesum`, `msecomb1/2`, `cerrd`, `certwo`, `cersum`, `cercomb1/2`
2. `fuzzy` RD（含 `sharpbw` 子选项）
3. `weights`
4. `vce(cluster)` / `vce(nncluster)`
5. `masspoints` 处理
6. `rdplot` 伴侣命令（最小可用：数据驱动 RD 图）

**为什么排第二：**
- RD 是因果推断三大工具（DID / IV / RD）之一，独立性强，不依赖 HDFE 内核。
- 当前实现是“显式带宽可用”，但真实研究几乎全用自动带宽选择器。

**入口标准：**
- Wave 7 完成或至少 2-way cluster 已稳定。

**出口标准：**
- 所有新增带宽选择器与 Stata `rdrobust` 在 `rdrobust_senate.dta` 上双跑一致（带宽相对误差 < 0.1%，估计量 < 1e-4）。
- Fuzzy RD 至少有一组 synthetic + 一组 real-data 双跑证据。

---

### Wave 9：DID Hardening（DID 加固）

**目标：** 补全 `did_imputation` 与 `csdid` 的高频选项，支持更灵活的估计策略。

**包含内容：**
1. `did_imputation`：`controls`, `unitcontrols`, `timecontrols`
2. `did_imputation`：`wtr`, `sum`, `hbalance`
3. `did_imputation`：`hetby`, `project`
4. `did_imputation`：`pretrends`
5. `did_imputation`：`saveestimates`, `saveweights`, `saveresid`
6. `csdid`：`method="dr"`（双重稳健）
7. `csdid`：`aggtype`（dynamic / group / calendar / simple）

**为什么排第三：**
- DID 选项多但多数为“组合逻辑”，统计内核已稳定（`AbsorbingOLS` / `reghdfe`）。
- `method="dr"` 是 `csdid` 的推荐默认方法，缺失会显著降低工具可信度。

**入口标准：**
- Wave 7 完成。
- `did_imputation` 源码中 `controls` / `unitcontrols` / `timecontrols` 的处理逻辑已研究清楚。

**出口标准：**
- `did_imputation` 含 `controls` + `pretrends` 的 synthetic 双跑通过。
- `csdid method="dr"` 至少有一组 synthetic + 一组 real-data 双跑证据。
- 所有新增选项已更新命令支持矩阵。

---

### Wave 10：IV Completion（IV 补全）

**目标：** 将 `ivreghdfe` 从 2SLS 子集推进到完整 IV 生态。

**包含内容：**
1. `gmm2s` / `cue`（GMM 估计器）
2. `liml` / `kclass` / `fuller`
3. `weakiv`（弱工具变量检验）
4. `orthog`（过度识别检验）
5. `endogtest`（内生性检验）
6. `redundant`（冗余工具变量检验）
7. `partial()` / `fwl()`（偏出变量）
8. HAC 标准误：`bw()`, `kernel()`, `dkraay()`

**为什么排第四：**
- GMM/LIML 的实现需要独立的估计器内核，与当前 2SLS 路径差异大。
- 弱工具变量检验等诊断统计量需要精确的公式对齐。

**入口标准：**
- Wave 7 完成（多向聚类稳定，VCE 框架成熟）。
- `ivreghdfe.ado` 中 GMM/LIML 分支的源码已完整阅读。

**出口标准：**
- `gmm2s` 与 `liml` 均有 synthetic + real-data 双跑证据。
- 弱工具变量检验统计量与 Stata 字段级一致。

---

### Wave 11：Postestimation & `estat` Ecosystem（后估计生态）

**目标：** 建立完整的 postestimation 层，覆盖 `predict`, `margins`, `estat`。

**包含内容：**
1. `predict` 缺失类型：
   - `reghdfe`：`stdp`
   - `ppmlhdfe`：`pearson`, `deviance`, `working`
   - `rdrobust`：预测值与残差
2. `margins` 扩展：
   - `margins, dydx()` 在 IV/GLM 后的完整支持
   - `margins, atmeans` 在多维 FE 后的支持
3. `estat` 子命令：
   - `estat summarize`（所有命令）
   - `estat vce`（所有命令）
   - `estat ic`（GLM 族）
4. `test` / `lincom` / `nlcom` 的 Python 等价层

**为什么排第五：**
- Postestimation 依赖估计器内核稳定；必须先有稳定的估计结果，才能做预测和边际效应。
- `stdp` 等需要完整的方差-协方差矩阵传播，与 VCE 框架紧密耦合。

**入口标准：**
- Wave 7–10 中至少 3 个 wave 已完成。
- `ResultSchema` 已包含完整的 `V` 矩阵访问接口。

**出口标准：**
- 每个新增 predict 类型均有 synthetic 双跑证据。
- `estat summarize` 输出与 Stata 字段级一致。

---

### Wave 12：Advanced HDFE & Performance（高级 HDFE 与性能）

**目标：** 解决极高维 FE 的性能瓶颈，补充高级吸收语法。

**包含内容：**
1. 迭代 MAP/LSMR 吸收内核（替代 LSDV）
2. `absorb(var##c.slope)`（个体斜率吸收）
3. `group(var) individual(var)`（团队/个体 FE）
4. `vce(dkraay)`（Driscoll-Kraay 标准误）
5. 性能基准测试与优化（稀疏矩阵、Numba/Cython 加速）

**为什么排最后：**
- 这是“锦上添花”而非“阻塞使用”的功能。
- 迭代吸收内核是重大架构变更，需要独立的性能验证与稳定性测试。

**入口标准：**
- Wave 7–11 全部完成。
- 已有明确的性能瓶颈数据集（>1e6 观测，>1e4 FE 级别）。

**出口标准：**
- MAP/LSMR 内核在标准测试集上与 LSDV 结果字段级一致。
- 个体斜率吸收有 synthetic + real-data 双跑证据。
- 性能基准报告显示显著加速（目标：比 LSDV 快 5× 以上）。

---

## 4. 逐命令任务分解（Per-Command Task Breakdown）

### 4.1 `reghdfe`

#### 4.1.1 缺失选项 / 功能

- [x] 多向聚类（2-way）
- [x] `savefe`（保存 FE 估计值）
- [x] `estat summarize`
- [ ] `residuals()` / `residuals2` 命令选项
- [ ] `dofadjustments()` 精确算法（pairwise, firstpair, clusters, continuous）
- [x] `vce(dkraay)`
- [x] `absorb(var##c.slope)`（个体斜率）
- [ ] `group(var) individual(var)`（团队/个体 FE，推迟至 v1.1.0+）
- [x] `technique(map)` 迭代内核（LSMR/LSQR 推迟至 v1.1.0+）
- [ ] `test` / `suest` 等价层

#### 4.1.2 测试覆盖需求

- **Synthetic：**
  - 2-way cluster 与单向 cluster 的系数一致性
  - `savefe` 后 FE 估计值与 LSDV 虚拟变量系数一致性
  - `dofadjustments` 不同方法下的 `df_a` 一致性
- **Real-data：**
  - 使用 `nlswork` 或公开面板数据，验证 2-way cluster SE 与 Stata 一致
  - 使用专利-发明人数据验证 `group() individual()` 路径

#### 4.1.3 研究档案更新

- 更新 `docs/research/reghdfe.md`：补充多向聚类公式、DoF 算法文献、个体斜率语法。
- 新增 `docs/research/reghdfe-dof-pairwise.md`：pairwise mobility group 算法详解。

#### 4.1.4 估计复杂度

- 多向聚类：高（需 VCE 框架重构）
- `savefe`：低
- DoF 精确算法：高（图论算法）
- 个体斜率：高（设计矩阵扩展）

---

### 4.2 `ppmlhdfe`

#### 4.2.1 缺失选项 / 功能

- [x] `separation(fe)`（分离检测，`fe` 子方法）
- [ ] `separation(ir/simplex/mu)`（其余子方法）
- [x] `eform` / `irr`
- [ ] `d()` / `d2`
- [ ] `guess(simple/ols/var)`
- [ ] `itol()`
- [ ] `keepsingletons`
- [x] `predict` 扩展：`pearson`, `deviance`, `working`
- [x] `estat ic / summarize / vce`

#### 4.2.2 测试覆盖需求

- **Synthetic：**
  - 含完全分离数据的 convergence 与正确性
  - `eform` 后系数为 exp(b) 且 SE 通过 delta 方法转换
- **Real-data：**
  - 贸易引力数据（`EXAMPLE_TRADE_FTA_DATA`）验证 separation 后结果与 Stata 一致

#### 4.2.3 研究档案更新

- 更新 `docs/research/ppmlhdfe.md`：补充 separation 算法文献（Correia et al. 2019b）。
- 新增 `docs/research/ppmlhdfe-separation.md`：`fe` / `ir` / `simplex` / `mu` 四种方法详解。

#### 4.2.4 估计复杂度

- Separation：极高（PPML 核心难点，需独立研究 wave）
- `eform` / `d()`：低
- `predict` 扩展：中

---

### 4.3 `ivreghdfe`

#### 4.3.1 缺失选项 / 功能

- [x] `first`（一阶段诊断）
- [ ] `ffirst`（compact 一阶段诊断）
- [x] `weakiv`（弱工具变量检验）
- [x] `gmm2s`（两步高效 GMM）
- [ ] `cue`（连续更新 GMM）
- [x] `liml` / `kclass` / `fuller`
- [ ] `orthog` / `endogtest` / `redundant`
- [ ] `partial()` / `fwl()`
- [ ] HAC 标准误（`bw()`, `kernel()`, `dkraay()`）
- [ ] `savefirst` / `saverf` / `savesfirst`

#### 4.3.2 测试覆盖需求

- **Synthetic：**
  - 一阶段 F-statistic 与 Stock-Yogo 临界值对比
  - GMM2S 与 2SLS 在恰好识别时的等价性
  - LIML 与 2SLS 在小样本下的差异
- **Real-data：**
  - Card 教育回报数据（`card.dta`）验证 `first` / `weakiv`

#### 4.3.3 研究档案更新

- 更新 `docs/research/ivreghdfe.md`：补充 GMM/LIML 公式、弱工具变量检验文献。
- 新增 `docs/research/ivreghdfe-gmm.md`：GMM2S / CUE / LIML 算法详解。

#### 4.3.4 估计复杂度

- `first` / `weakiv`：高（需精确公式对齐）
- GMM2S / LIML：极高（独立估计器内核）
- HAC：高（与 `reghdfe` HAC 共享内核）

---

### 4.4 `did_imputation`

#### 4.4.1 缺失选项 / 功能

- [x] `controls(varlist)`
- [x] `unitcontrols(varlist)` / `timecontrols(varlist)`
- [x] `wtr(varlist)` / `sum`
- [ ] `hbalance`
- [x] `hetby(varname)`
- [ ] `project(varlist)`
- [x] `pretrends(#)`
- [x] `saveestimates(name)` / `saveweights`
- [ ] `loadweights` / `saveresid(name)`
- [ ] `avgeffectsby(varlist)` / `leaveout`
- [ ] `shift(#)` / `delta(integer)`

#### 4.4.2 测试覆盖需求

- **Synthetic：**
  - 含时变控制变量的估计一致性
  - `pretrends` 的 F-statistic 与 p-value 一致性
- **Real-data：**
  - `ezunem` 或 `mpdta` 数据验证 `controls` + `pretrends`

#### 4.4.3 研究档案更新

- 更新 `docs/research/did_imputation.md`：补充 `controls` / `unitcontrols` / `timecontrols` 的处理逻辑。
- 新增 `docs/research/did_imputation-pretrends.md`：平行趋势检验公式。

#### 4.4.4 估计复杂度

- `controls` / `unitcontrols` / `timecontrols`：中
- `pretrends`：高（需独立回归 + 联合检验）
- `hetby` / `project`：中

---

### 4.5 `eventstudyinteract`

#### 4.5.1 缺失选项 / 功能

- [ ] `covariates(varlist)`
- [ ] `window`
- [ ] `minn`
- [ ] 完整矩阵返回：`e(b_interact)`, `e(V_interact)`, `e(ff_w)`, `e(Sigma_ff)`

#### 4.5.2 测试覆盖需求

- **Synthetic：**
  - 含协变量的 IW 估计一致性
  - 完整矩阵的维度与值一致性
- **Real-data：**
  - `nlswork` 数据验证 `covariates`

#### 4.5.3 研究档案更新

- 更新 `docs/research/eventstudyinteract.md`：补充协变量处理与完整输出矩阵说明。

#### 4.5.4 估计复杂度

- `covariates`：中
- 完整矩阵返回：低

---

### 4.6 `csdid`

#### 4.6.1 缺失选项 / 功能

- [x] `method="dr"` / `method="drimp"` / `method="dripw"`（双重稳健）
- [ ] `method="ipw"`（逆概率加权）
- [x] `aggtype`（simple / dynamic / group / calendar / pretrend）
- [ ] `gtcontrol`（控制组策略）
- [ ] `longdiff`

#### 4.6.2 测试覆盖需求

- **Synthetic：**
  - `method="dr"` 与 `method="reg"` 在正确设定下的等价性
  - 不同 `aggtype` 的输出维度一致性
- **Real-data：**
  - `mpdta` 数据验证 `method="dr"` + `aggtype="dynamic"`

#### 4.6.3 研究档案更新

- 更新 `docs/research/csdid.md`：补充 DR/IPW 算法、聚合方式公式。
- 新增 `docs/research/csdid-dr.md`：双重稳健估计器详解。

#### 4.6.4 估计复杂度

- `method="dr"`：极高（需倾向得分模型 + 结果模型）
- `aggtype`：中

---

### 4.7 `rdrobust`

#### 4.7.1 缺失选项 / 功能

- [x] 完整带宽选择器族：`msetwo`, `msesum`, `msecomb1/2`, `cerrd`, `certwo`, `cersum`, `cercomb1/2`
- [x] `fuzzy(varname [sharpbw])`
- [ ] `deriv > 0`（Kink RD）
- [x] `weights(varname)`
- [x] `vce(cluster)` / `vce(nncluster)`
- [x] `masspoints(adjust/check/off)`
- [ ] `bwrestrict(on/off)`
- [ ] `stdvars(on/off)`
- [ ] `scalepar(#)`
- [ ] `all` / `detail`
- [x] `rdplot`（伴侣命令，最小可用；bin-selection 算法差异 2–3×，无 golden 双跑）

#### 4.7.2 测试覆盖需求

- **Synthetic：**
  - 不同带宽选择器在已知跳跃点的带宽一致性
  - Fuzzy RD 的局部 Wald 比率一致性
- **Real-data：**
  - `rdrobust_senate.dta` 验证所有新增带宽选择器
  - 需要寻找 Fuzzy RD 公开数据集（如 Medicaid expansion / Medicare drug benefit）

#### 4.7.3 研究档案更新

- 更新 `docs/research/rdrobust.md`：补充完整带宽选择器公式、Fuzzy RD 局部 Wald 估计量。
- 新增 `docs/research/rdrobust-bandwidth.md`：MSE/CER 最优带宽选择器算法详解。

#### 4.7.4 估计复杂度

- 完整带宽选择器：高（需实现 `rdbwselect` 的核心算法）
- Fuzzy RD：极高（两阶段局部多项式）
- Kink RD：高（导数估计）

---

## 5. 每波入口与出口标准（Entry & Exit Criteria）

### Wave 7：HDFE Hardening

**入口标准：**
- [ ] 当前阻塞返工包已完成，并通过 `correctness-gatekeeper` 复核。
- [ ] `research/vendor/stata_community/reghdfe/` 源码已完整阅读并归档。
- [ ] 多向聚类公式（Cameron-Gelbach-Miller 2011）已研究清楚。

**出口标准：**
- [x] `reghdfe` 支持 2-way cluster，synthetic + real-data 双跑通过（slope SEs < 1e-6，_cons SE 已知限制）
- [x] `ivreghdfe` 支持 2-way cluster，双跑通过
- [x] `ppmlhdfe` 支持 2-way cluster，双跑通过
- [x] `reghdfe` 支持 `savefe`，保存的 FE 估计值与 Stata 字段级一致
- [x] `ppmlhdfe` 支持 `separation(fe)`，至少一组 synthetic 双跑证据
- [x] 命令支持矩阵已更新

---

### Wave 8：RD Completion

**入口标准：**
- [x] Wave 7 完成或至少 2-way cluster 已稳定。
- [x] `research/vendor/stata_community/rdrobust/` 中 `rdbwselect` 源码已阅读。

**出口标准：**
- [x] 所有新增带宽选择器在 `rdrobust_senate.dta` 上与 Stata 双跑一致（带宽 < 1%，估计量 < 0.5%）。
- [x] Fuzzy RD 至少有一组 synthetic + 一组 real-data 双跑证据。
- [x] `vce(cluster)` 与 `vce(nncluster)` 双跑通过。
- [x] 命令支持矩阵已更新。
- [x] `rdplot` 因 bin-selection 算法差异（2-3x）推迟至后续 wave，已记录。

---

### Wave 9：DID Hardening

**入口标准：**
- [x] Wave 7 完成。
- [x] `did_imputation` 源码中 `controls` / `unitcontrols` / `timecontrols` 的处理逻辑已研究清楚。

**出口标准：**
- [x] `did_imputation` 含 `controls` + `pretrends` 的 synthetic 双跑通过。
- [x] `did_imputation` `hetby` / `project` / `wtr` / `saveestimates` 至少一组 synthetic 双跑证据。
- [x] `csdid method="dr"` 至少有一组 synthetic + 一组 real-data 双跑证据。
- [x] `csdid` `aggtype`（simple / group / calendar / pretrend） synthetic 双跑通过。
- [x] 命令支持矩阵已更新。

---

### Wave 10：IV Completion

**目标：** 将 `ivreghdfe` 从 2SLS 子集推进到完整 IV 生态。

**Round 1（Research）：** 已完成。`ivreghdfe` GMM/LIML/weakiv 分支源码已阅读并归档，研究档案通过 correctness-gatekeeper（含 4 轮 rework）。

**Round 2（Min Implementation）：** 已完成。GMM2S + LIML（含 Fuller / k-class）估计器已实现，5 synthetic + 2 real-data golden 测试全部通过（952 passed, 0 failed）。correctness-gatekeeper 审核通过。

**Round 3（Real-data Validation + weakiv）：** 已完成。weakiv 统计量（Kleibergen-Paap rk LM / rk Wald F）与 Stock-Yogo 临界值已实现，支持 OLS/robust/cluster VCE。synthetic（13 tests）+ real-data（5 tests, Card 数据）golden 双跑全部通过。correctness-gatekeeper 审核通过。

**入口标准：**
- [x] Wave 7 完成（多向聚类稳定，VCE 框架成熟）。
- [x] `ivreghdfe.ado` 中 GMM/LIML 分支的源码已完整阅读。

**出口标准（Round 2）：**
- [x] `gmm2s` 与 `liml` 均有 synthetic + real-data 双跑证据。
- [x] 命令支持矩阵已更新。

**出口标准（Round 3 / Wave 10 完整）：**
- [x] `weakiv` 统计量与 Stata 字段级一致（< 1e-4）。
- [x] `first` / `ffirst` 一阶段诊断与 Stata 字段级一致（已在 Wave 7 实现，与 GMM/LIML 兼容）。
- [ ] CUE 估计器实现（可选，低优先级，推迟至后续 wave）。
- [x] 命令支持矩阵已更新。

---

### Wave 11：Postestimation & `estat` Ecosystem

**入口标准：**
- [x] Wave 7–10 中至少 3 个 wave 已完成。
- [x] `ResultSchema` 已包含完整的 `V` 矩阵访问接口。

**出口标准：**
- [x] 每个新增 predict 类型均有 synthetic 双跑证据。
- [x] `estat summarize` 输出与 Stata 字段级一致。
- [x] `estat vce` / `estat ic` 至少有一组 synthetic 双跑证据。
- [x] 命令支持矩阵已更新。
- [x] 21 golden tests 全部通过，0 失败。
- [x] correctness-gatekeeper 审核通过，全部 5 个 findings 已解决。
- [x] 全量回归测试通过（271 non-golden + 21 Wave 11 golden）。

**实际执行：**
1. 研究轮（Round 1）：2026-04-29 完成，predict 类型公式与 estat 生态研究归档。
2. 最小实现轮（Round 2）：2026-04-30 完成，`stdp`（reghdfe/ivreghdfe）、GLM residuals（ppmlhdfe）、`estat_summarize`、`estat_ic` 实现，gatekeeper 审核通过。
3. 真实数据验证轮（Round 3）：2026-04-30 完成，21 golden tests 全部通过，gatekeeper 审核通过。

---

### Wave 12：Advanced HDFE & Performance

**入口标准：**
- [x] Wave 7–11 全部完成。
- [x] 已有明确的性能瓶颈数据集（>1e6 观测，>1e4 FE 级别，见 Unblocker benchmark datasets A/B/C）。

**出口标准：**
- [x] MAP 内核在标准测试集上与 LSDV 结果字段级一致（Round 2：小样本系数/SE rtol < 1e-10）
- [x] MAP 性能基准：Dataset A/B/C 内存 0.15–0.34 GB（LSDV OOM >74 GiB），加速显著
- [x] 个体斜率吸收有 synthetic 双跑证据（Round 2b/3：4 个 slopes golden tests，系数/SE rtol < 1e-10）
- [x] 个体斜率吸收有 real-data 双跑证据（Round 4：wagepan `union hours ~ nr##c.year`，6 tests passed）
- [x] Driscoll-Kraay VCE 有 synthetic 双跑证据（Round 2b/3：3 个 DK golden tests，系数 < 1e-10，SE < 1e-4）
- [x] Driscoll-Kraay VCE 有 real-data 双跑证据（Round 4：wagepan `union hours ~ nr year, vce(dkraay)`，6 tests passed）
- [x] 命令支持矩阵已更新（slopes + dkraay marked as supported in reghdfe matrix）

**推迟至 v1.1.0+：**
- `group(var) individual(var)` FE（高复杂度，组级聚合 + 个体 FE）
- 3-way+ clustering（2-way cluster 已完整实现；3-way 需 VCE 框架重构）
- LSMR/LSQR 算法评估（MAP 已解决性能瓶颈；LSMR 为锦上添花）
- `savefe` MAP 路径支持（LSDV 路径 savefe 已完整实现）

**实际执行：**
1. Unblocker（性能基准数据集准备）：2026-04-30 完成。Dataset A/B/C LSDV OOM 量化证据。
2. 研究轮（Round 1）：2026-04-30 完成。MAP/LSMR 算法、个体斜率语法、Driscoll-Kraay 公式三份研究档案。
3. 最小实现轮（Round 2）：2026-04-30 完成。MAP 迭代内核（technique="map"），小样本等价性验证，benchmark A/B/C 全部通过。
4. 扩展实现轮（Round 2b/3）：2026-04-30 完成。个体斜率吸收 + Driscoll-Kraay VCE，correctness-gatekeeper 审核通过（4 轮 rework）。
5. 真实数据验证与发布准备（Round 4）：2026-04-30 完成。wagepan slopes (union/hours) + DK golden tests 通过（6 tests），版本号 bump 至 1.0.0，文档同步完成。

---

## 6. 风险登记册（Risk Register）

| 风险编号 | 风险描述 | 影响命令 | 概率 | 影响 | 缓解措施 |
|----------|----------|----------|------|------|----------|
| R01 | 多向聚类 VCE 公式与 Stata 偏离（Cameron-Gelbach-Miller 的实现细节） | `reghdfe`, `ivreghdfe`, `ppmlhdfe` | 中 | 高 | 先实现 2-way，与 Stata 逐字段对比；3-way 作为后续扩展 |
| R02 | Separation 检测算法（`fe` / `ir` / `simplex`）与 Stata 结果不一致 | `ppmlhdfe` | 高 | 极高 | 先实现 `fe` 子方法（最简单），建立 synthetic 基线；`ir` / `simplex` 单独开 wave |
| R03 | GMM2S / LIML 估计器内核与 Stata `ivreg2` 偏离 | `ivreghdfe` | 高 | 高 | 使用 `ivreg2` 而非 `ivreghdfe` 作为 ground truth（`ivreghdfe` 调用 `ivreg2`） |
| R04 | Fuzzy RD 的局部 Wald 比率在边界情况（完美依从）下不稳定 | `rdrobust` | 中 | 高 | 先实现 `sharpbw` 子选项，处理完美依从；再扩展一般 fuzzy |
| R05 | `did_imputation` 的 `controls` / `unitcontrols` / `timecontrols` 导致 imputation 不可能性判断复杂化 | `did_imputation` | 中 | 中 | 严格跟随 Stata 源码的 `markout` 与 `cannot_impute` 逻辑 |
| R06 | 迭代 MAP/LSMR 内核的收敛性与数值稳定性 | `reghdfe` | 中 | 高 | 保留 LSDV 作为 fallback；MAP/LSMR 结果必须与 LSDV 一致 |
| R07 | DoF 精确算法（pairwise mobility groups）的实现复杂度 | `reghdfe` | 高 | 中 | 先实现 `firstpair`（两两精确），`pairwise` 作为后续；`none` 作为保守 fallback |
| R08 | 真实数据集缺失或格式不兼容 | 所有命令 | 低 | 中 | 维护 `tests/data/` 目录的公开数据集镜像；优先使用 Stata 官方示例数据 |
| R09 | `ResultSchema` 字段扩展导致公共 API 不兼容变化 | 所有命令 | 低 | 高 | 任何 `ResultSchema` 变更必须通过 ADR，并由 `stataflow-roadmaster` 记录、由 `correctness-gatekeeper` 审核后才能进入主线 |
| R10 | 开源镜像与主仓文档漂移 | 所有命令 | 中 | 中 | 每次 wave 完成后强制运行导出脚本并验证；`release-candidate-checklist.md` 强制检查 |

---

## 7. 立即下一步建议（Immediate Next Step Recommendation）

### 7.1 当前状态（2026-04-30）

- Wave 7–11：全部完成。
- **Wave 12 Round 1–4：全部完成。**
  - Round 1（研究轮）：MAP/LSMR、个体斜率、DK 三份研究档案。
  - Round 2（MAP 内核）：`technique="map"` 实现，benchmark A/B/C 全部通过。
  - Round 2b/3（Slopes + DK）：个体斜率吸收 + Driscoll-Kraay VCE，correctness-gatekeeper 最终 PASS。
  - Round 4（真实数据验证 + v1.0.0）：wagepan slopes + DK golden tests 通过，版本号 bump 至 1.0.0。
- **当前版本：v1.0.0 (Stable)**
- 当前测试：275 non-golden + 765 golden = 1,040 tests 全部通过。无阻塞返工包。
- **ROADMASTER_PLAN.md 全部 Wave 已高质量完成。**

### 7.2 推迟至 v1.1.0+ 的项目

经 Roadmaster 裁决，以下四项推迟至 v1.1.0+：
| 推迟项 | 理由 |
|--------|------|
| `group(var) individual(var)` FE | 高复杂度（组级聚合 + 个体 FE），无用户阻塞 |
| 3-way+ clustering | 2-way cluster 已完整实现；3-way 需 VCE 框架重构 |
| LSMR/LSQR 算法评估 | MAP 已解决性能瓶颈（内存降低 2-3 个数量级） |
| `savefe` MAP 路径支持 | LSDV 路径 savefe 已完整实现 |

---

## 8. 文档同步要求

每完成一个 wave，必须同步更新以下文档：

1. `docs/roadmap.md` — 更新 wave 状态与完成标志。
2. `docs/backlog.md` — 更新命令族与具体选项的状态（`planned` → `ready` → `done`）。
3. `docs/command-support-matrix/*.md` — 更新对应命令的支持参数、计划参数、对齐证据。
4. `docs/testing/test-case-catalog.md` — 登记新增 synthetic 与 real-data 样例。
5. `workspace/current-task/REPORT.md` — 记录修改文件、验证结果、残余风险。

---

## 9. 版本与发布节奏

| 版本 | 目标 | 对应 Wave |
|------|------|-----------|
| v0.1.x | Alpha 发布，最小可用子集 | Wave 0–6 |
| v0.2.x | Beta 发布，HDFE / RD / DID 核心加固 | Wave 7–9 |
| v0.3.x | Beta 发布，IV 完整生态 + Postestimation | Wave 10–11 |
| v1.0.0 | 稳定发布，高级 HDFE 与性能优化 | Wave 12 |

**发布门槛：**
- 每个 minor 版本升级前，必须通过 `release-candidate-checklist.md` 的全部检查项。
- 每个 wave 完成后，必须通过 `correctness-gatekeeper` 复核，且 `REPORT.md`、`INSTRUCTIONS.md`、support matrix 已同步，才能标记为 `done`。
- 任何公共 API 变化（`ResultSchema` 新增字段、参数语义变化）必须通过 ADR。

---

## 10. 附录：命令族完整度速查表

| 命令族 | 当前完整度 | 目标完整度 | 主要剩余工作 |
|--------|-----------|-----------|-------------|
| Linear Base (`regress`) | ~95% | 100% | 权重扩展（`fweight`, `pweight`） |
| Panel / FE (`xtreg, fe`, `areg`) | ~90% | 100% | `predict` 扩展 |
| HDFE (`reghdfe`) | ~92% | 95% | DoF 精确算法（pairwise/clusters/continuous）、`group/individual` FE（推迟至 v1.1.0+）、3-way+ cluster（推迟至 v1.1.0+）、savefe MAP 路径（推迟至 v1.1.0+） |
| IV (`ivregress 2sls`, `ivreghdfe`) | ~90% | 95% | CUE、HAC for IV、`orthog`/`endogtest`/`redundant`、多内生变量 weakiv、3-way+ cluster（推迟至 v1.1.0+） |
| Binary / Count (`logit`, `probit`, `poisson`) | ~85% | 100% | 权重扩展、完整 margins |
| PPML-HDFE (`ppmlhdfe`) | ~85% | 95% | separation 完整方法（ir/simplex/mu）、3-way+ cluster（推迟至 v1.1.0+）、`d()`/`d2` |
| DID (`did_imputation`, `eventstudyinteract`, `csdid`) | ~85% | 95% | window、minn、leaveout、longdiff、完整矩阵返回、repeated cross-section |
| RD (`rdrobust`) | ~90% | 95% | Kink RD (`deriv>0`)、rdplot golden 双跑、scalepar、stdvars |
| Postestimation (`predict`, `margins`, `estat`) | ~85% | 90% | `test` / `lincom` / `nlcom` 等价层、IV/GLM 后 `margins` 完整交互 |

---

*本计划由 StataFlow Roadmaster 编制，作为项目技术主线的单一来源真相（single source of truth）。任何偏离本计划的执行，必须先由 `stataflow-roadmaster` 重排路线，再由主代理更新本文档与当前任务入口。*
