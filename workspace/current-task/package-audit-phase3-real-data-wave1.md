# Audit Phase 3 Wave 1: 真实数据双跑验证 — P0 实验 + 立即可用数据

**日期：** 2026-04-30
**版本：** v1.0.0
**阶段：** Phase 3.1 — 真实数据双跑验证第一波
**前置条件：** Phase 1（数学审查完成）、Phase 2（代码重构完成，6/8 交付）

---

## 背景

StataFlow v1.0.0 已完成 12 个 Wave 的功能开发和 765 个 golden 双跑测试。然而，现有真实数据测试存在两个结构性缺口：

1. **覆盖深度不足：** 现有 real-data golden 测试通常只覆盖 `vce="ols"` 单一路径，未覆盖 robust、cluster、multi-way cluster、DK 等 VCE 类型，也未覆盖全部 estimator 变体（如 IV 的 2SLS/GMM2S/LIML）。
2. **缺乏结构化实验文档：** 现有测试是孤立的 `.py` 文件，缺少数据来源说明、研究问题背景、完整 Stata-Python 比对报告。

Phase 3 旨在通过 10 个金融经济学实验填补这两个缺口。每个实验生成完整的可复现研究包。

本 Wave 1 聚焦于**数据已在本项目内的实验**，共 5 个实验（3 个 P0 + 2 个用户指定 P1/P2），无需外部数据下载。

---

## 目标

为 5 个实验各自生成完整的研究包，每个包含：

1. **`README.md`** — 实验描述、数据来源、研究问题、预期结果
2. **`data_prep.py`** — 数据加载、清洗、预处理（输出标准格式 CSV/DTA）
3. **`analysis.do`** — Stata 17 命令序列（覆盖所有目标 VCE 和 estimator 变体）
4. **`analysis.py`** — Python等价代码（使用 StataFlow public API）
5. **`results.md`** — 字段级比对结果与偏差分析
6. **`tests/golden/test_v2_<exp_id>_real.py`** — 可重复运行的 golden 双跑测试

---

## 实验清单

### Experiment C1.1: CAPM/FF3 因子回归（P0）

| 维度 | 内容 |
|------|------|
| **数据** | `research/data/public/finance/fama_french/ff3/F-F_Research_Data_Factors.csv` |
| **研究问题** | 使用 OLS 估计 CAPM beta 和 Fama-French 3-factor loadings |
| **命令覆盖** | `regress` (OLS 基础)、`vce(robust)` (HC1)、`vce(cluster time)` (cluster by year/month) |
| **StataFlow API** | `OLS(...).fit(vce="ols")`, `OLS(...).fit(vce="robust")`, `OLS(...).fit(vce="cluster", cluster="time_id")` |
| **比对字段** | coefficients, SEs, t-stats, R², adjusted R², RMSE, F-statistic, df_model, df_resid |
| **现有覆盖** | 无（test-case-catalog 中 `real_ff3_time_series` 标记为 ready 但未实现） |
| **特殊要点** | 时间序列数据需构造 cluster 变量（年份聚类）；处理 FF3 数据中的日期格式 |

### Experiment C1.4: 教育回报率 IV 估计 — Card 1995（P0）

| 维度 | 内容 |
|------|------|
| **数据** | `research/data/public/iv/card.csv` |
| **研究问题** | IV 估计教育回报率：`lwage ~ educ + exper + expersq + black + smsa + south`，工具变量 `nearc4` |
| **命令覆盖** | `ivregress 2sls` (2SLS 基础)、`ivreghdfe` (2SLS + GMM2S + LIML)、`vce(ols/robust/cluster)`、`first` (一阶段 F)、`weakiv` (弱工具检验)、`estat overid` (Hansen J) |
| **StataFlow API** | `IV2SLS(...).fit(vce="ols/robust/cluster")`, `IVAbsorbingOLS(...).fit(vce="ols/robust/cluster", estimator="2sls/gmm2s/liml", first=True)` |
| **比对字段** | coefficients, SEs, first-stage F, Shea partial R², Hansen J, KP rk Wald F, Stock-Yogo critical values |
| **现有覆盖** | `test_w2_ivregress_real_card.py`（仅 `vce="ols"` on `IV2SLS`，238 行）— 缺口：无 GMM2S/LIML、无 robust/cluster VCE、无 weak-IV、无 first-stage |
| **特殊要点** | `nearc4` 为二元工具变量；需验证恰好识别下的 GMM2S=2SLS 等价性；south 作为 region FE 吸收 |

### Experiment C1.6: 引力模型 PPMLHDFE（P0）

| 维度 | 内容 |
|------|------|
| **数据** | `research/vendor/stata_community/ppmlhdfe/ppmlhdfe-master/examples/EXAMPLE_TRADE_FTA_DATA.dta`（1MB，真实贸易+FTA 数据） |
| **研究问题** | PPML 估计双边贸易流量的引力方程：`trade ~ distance + contiguity + common_language + FTA`，吸收 exporter + importer + year FE |
| **命令覆盖** | `ppmlhdfe` (PPML 基础)、`vce(robust/cluster)`、`eform` (IRR)、`separation` 检测、`predict` (mu/xb/pearson/deviance) |
| **StataFlow API** | `PPMLHDFE(...).fit(vce="robust/cluster")` |
| **比对字段** | coefficients (eform), SEs, ll, deviance, pseudo-R², IRLS iterations, residuals |
| **现有覆盖** | `test_w3_ppmlhdfe_real_gravity.py`（countymurders 县级面板，仅 `vce="robust"`）— 缺口：无 cluster VCE、无 eform、无 separation 测试 |
| **特殊要点** | PPMLHDFE 是最高风险 estimator（Phase 1 审查发现 2 个 P1 VCE 修正问题）；需验证 zero-trade 处理与 Stata 一致 |

### Experiment C1.7: DID 政策评估 — 最低工资与就业（P1，用户指定）

| 维度 | 内容 |
|------|------|
| **数据** | `research/data/public/did/ezunem_prepared.dta`（Wooldridge ezunem，22 cities x 9 years） |
| **研究问题** | Staggered adoption DID：最低工资法提高对就业的影响 |
| **命令覆盖** | `did_imputation` (basic + controls + pretrends + allhorizons)、`eventstudyinteract` (IW estimator)、`csdid` (reg + dripw) |
| **StataFlow API** | `DIDImputation(...).fit(cluster="city", controls=["pop"], pretrends=3, allhorizons=True)`, `EventStudyInteract(...).fit(vce="cluster", cluster="city")`, `CSDID(...).fit(method="reg/dripw", vce="cluster", cluster="city")` |
| **比对字段** | ATT(g,t), event-study coefficients, pretrend F-test, SEs, horizons |
| **现有覆盖** | `test_w4_did_imputation_real_ezunem.py`、`test_w4_eventstudyinteract_real_ezunem.py`、`test_w4_csdid_real_ezunem.py`、`test_w9_csdid_dr_real_ezunem.py` — 缺口：无 controls/pretrends 测试、无 CSDID dripw 方法 |
| **特殊要点** | CSDID DR SE 偏差达 20%（已知最高风险项 #1）；需分析偏差来源并文档化 |

### Experiment C1.8: 政治 RD — 参议院在职优势（P2，用户指定）

| 维度 | 内容 |
|------|------|
| **数据** | `tests/data/rdrobust_senate.dta` 或 `research/data/public/rdrobust_senate_with_z.dta`（Cattaneo et al. 2015, 1390 obs） |
| **研究问题** | Sharp RD: 在职优势 — 得票率在 50% 附近的跳跃效应 |
| **命令覆盖** | `rdrobust` (Sharp RD + Fuzzy RD)、全部 11 个带宽选择器（`mserd/msesum/msetwo/cerrd/cersum/certwo`）、`kernel(triangular/epanechnikov/uniform)`、`covs(.)`、`cluster(.)`、`bwselect(.)` |
| **StataFlow API** | `rdrobust(df, y="vote_share", x="margin", bwselect="mserd", kernel="triangular", covs=["past_vote"])` |
| **比对字段** | tau (treatment effect), SE tau, bias-corrected tau, robust SE, bandwidth (h_l, h_r), effective N (N_h_l, N_h_r) |
| **现有覆盖** | `test_w8_rdrobust_bwselect_all_real_senate.py`（193 行，覆盖 6 个带宽选择器）、`test_w8_rdrobust_fuzzy_real_senate.py`、`test_w8_rdrobust_cluster_real_senate.py` — 相对完整，但缺乏结构化实验文档 |
| **特殊要点** | 带宽选择器在真实数据上误差可达 10%（synthetic 中 < 5%）；需分析真实数据偏差来源 |

---

## 为何现在执行

1. **Phase 1 确认数学正确，Phase 2 清理代码结构。** 现在是可以安全添加复杂测试的窗口。
2. **真实数据覆盖是 v1.0.0 最薄弱的证据环节。** 当前仅 ~30% 的 golden 测试使用真实数据，且覆盖深度有限。
3. **5 个实验使用的数据全部已在本项目中。** 零外部下载，可以立即开始执行。
4. **实验 C1.6（PPMLHDFE）直接验证 Phase 1 发现的 P1 风险项**（PPMLHDFE cluster VCE 修正），为 v1.1.0 开发提供决策依据。
5. **实验 C1.7（CSDID DR SE 偏差）直接验证已知最高风险项**，应优先获得真实数据证据。

---

## 许可修改范围

### 允许新建/修改

| 类别 | 路径 | 说明 |
|------|------|------|
| 实验目录 | `research/experiments/c1_*/` | README.md, data_prep.py, analysis.do, analysis.py, results.md |
| Golden 测试 | `tests/golden/test_v2_c1_*_real.py` | 每实验 1 个综合 golden 测试文件 |
| 测试目录 | `tests/data/` | 如需要新增预处理后的数据文件 |
| Stata 用例 | `stata/cases/` | 新增 .do 文件和 .dta 数据 |
| Stata 输出 | `stata/output/` | Stata 执行输出 |
| 测试样例目录 | `docs/testing/test-case-catalog.md` | 登记新的测试样例 |
| 支持矩阵 | `docs/command-support-matrix/*.md` | 更新真实数据验证状态 |
| 已知问题 | `docs/release/known-issues.md` | 记录新发现的偏差 |

### 允许修改但需谨慎

| 类别 | 路径 | 条件 |
|------|------|------|
| Estimator 代码 | `src/stataflow/estimators/*.py` | **仅修复 Phase 3 实验中发现的 bug**；修复前必须在 REPORT.md 中记录根因和修复内容 |
| 数据预处理工具 | `src/stataflow/compat/stata/*.py` | 仅限数据加载便利函数，不修改 API 语义 |

### 禁止修改

- **Public API signatures** — `OLS.fit()`, `IVAbsorbingOLS.fit()`, `PPMLHDFE.fit()` 等的参数签名
- **ResultSchema fields** — 不新增/删除/重命名 schema 字段（除非通过 ADR）
- **Math / VCE formulas** — 不修改任何数学公式（除非发现 bug 且通过 Codex 审批）
- **已有 golden test expectations** — 不修改已有 golden 测试的容忍度
- **`docs/project-charter.md`** — 架构原则
- **`CLAUDE.md`** — 项目指令（除非发现事实错误）

---

## 禁止行为

1. **禁止跳过 Stata 双跑验证** — 每个实验的每个 VCE/estimator 组合都必须有对应的 Stata 输出
2. **禁止以 "统计等价" 替代字段级比对** — 所有字段必须通过 `tolerance_close` 严格比对
3. **禁止在没有 Codex 审批的情况下放宽容忍度** — 若发现真实数据偏差 > 1e-6，必须记录到 `results.md` 并评估是否需要 ADR
4. **禁止修改 estimator 代码以 "通过测试"** — 若发现偏差，必须先理解根因，再决定是测试容忍度问题还是代码 bug
5. **禁止在一个 golden 测试文件中混合多个不相关实验** — 每实验一个独立 golden 测试文件
6. **禁止使用硬编码的偏差容忍度** — 所有容忍度必须有注释解释其来源（机器精度/已知 ADR/新发现待审）
7. **禁止跳过 `data_prep.py`** — 每个实验的数据预处理必须是可复现脚本，不是手工操作

---

## 执行顺序

```
Phase 3.1.0: 基础设施
  └── 确认所有 5 个数据集可加载、字段完整
       └── 输出: data_availability_report.md

Phase 3.1.1: C1.1 CAPM/FF3
  ├── data_prep.py: 加载 FF3 CSV，解析日期，构造 year/month cluster 变量
  ├── analysis.do: Stata regress with vce(ols/robust/cluster year)
  ├── analysis.py: Python OLS with vce(ols/robust/cluster)
  ├── 双跑验证: 3 VCE 类型 x 1 estimator = 3 个比对场景
  └── results.md: 字段级比对表 + 偏差分析

Phase 3.1.2: C1.4 Card IV
  ├── data_prep.py: 加载 card.csv，验证字段，构造 south region dummy
  ├── analysis.do: Stata ivregress 2sls + ivreghdfe (2SLS/GMM2S/LIML) x vce(ols/robust/cluster)
  ├── analysis.py: Python IV2SLS + IVAbsorbingOLS with all estimators and VCE types
  ├── 双跑验证: 3 VCE x 3 estimators = 9 个比对场景 + first-stage + weak-IV + Hansen J
  └── results.md: 字段级比对表 + 偏差分析

Phase 3.1.3: C1.6 Gravity PPML
  ├── data_prep.py: 加载 EXAMPLE_TRADE_FTA_DATA.dta，验证 trade/gravity 变量
  ├── analysis.do: Stata ppmlhdfe with vce(robust/cluster) + eform + separation
  ├── analysis.py: Python PPMLHDFE with vce(robust/cluster)
  ├── 双跑验证: 2 VCE x 1 estimator = 2 个比对场景 + residuals + eform
  └── results.md: 字段级比对表 + VCE 修正验证 + P1 风险项评估

Phase 3.1.4: C1.7 DID Policy
  ├── data_prep.py: 加载 ezunem_prepared.dta，验证 panel 结构
  ├── analysis.do: Stata did_imputation (controls + pretrends) + csdid (reg + dripw)
  ├── analysis.py: Python DIDImputation + CSDID
  ├── 双跑验证: did_imputation (basic + controls + pretrends) + csdid (reg + dripw)
  └── results.md: ATT 比对表 + CSDID DR SE 偏差根因分析

Phase 3.1.5: C1.8 RD Senate
  ├── data_prep.py: 加载 rdrobust_senate.dta，构造 fuzzy RD running variable
  ├── analysis.do: Stata rdrobust with 全部带宽选择器 + cluster + fuzzy
  ├── analysis.py: Python rdrobust with 全部带宽选择器 + cluster + fuzzy
  ├── 双跑验证: 11 带宽选择器 x 2 RD 类型 (sharp/fuzzy) = 关键组合
  └── results.md: tau/SE/bandwidth 比对表 + 真实数据带宽偏差分析

Phase 3.1.6: 汇总
  └── 更新 test-case-catalog.md、支持矩阵、known-issues.md
       └── 输出: Phase 3 Wave 1 完成报告
```

每个子阶段完成后必须：
1. 运行该实验的 golden 测试确认通过
2. 运行全量回归测试确认 0 regression：`pytest tests/ --ignore=tests/golden/ -q`

---

## 最小验证要求

### 每实验通用要求

| 验证项 | 命令/方法 | 通过标准 |
|--------|----------|---------|
| 数据可加载 | `python data_prep.py` | 无异常，输出行数/列数与预期一致 |
| Stata 可执行 | 运行 `.do` 文件 | Stata 正常退出，无 error 代码 |
| Python 可执行 | `python analysis.py` | 无异常，返回 ResultSchema |
| Golden 测试通过 | `pytest tests/golden/test_v2_c1_*_real.py -v` | 全部 passed |
| 全量回归通过 | `pytest tests/ --ignore=tests/golden/ -q` | 0 failed |

### C1.1 CAPM/FF3 专项验证

| 场景 | 比对字段 | rtol |
|------|---------|------|
| `regress, vce(ols)` | coef, SE, t, R², RMSE, F, df | < 1e-6 |
| `regress, vce(robust)` | coef, robust SE, t | < 1e-6 |
| `regress, vce(cluster year)` | coef, cluster SE, t | < 1e-6 |

### C1.4 Card IV 专项验证

| 场景 | 比对字段 | rtol |
|------|---------|------|
| `ivregress 2sls, vce(ols)` | coef, SE, R², RMSE | < 1e-6 |
| `ivregress 2sls, vce(robust)` | coef, robust SE | < 1e-6 |
| `ivregress 2sls, vce(cluster south)` | coef, cluster SE | < 1e-6 |
| `ivreghdfe, 2sls, absorb(south)` | coef, SE | < 1e-6 |
| `ivreghdfe, gmm2s, absorb(south)` | coef, SE, Hansen J | < 1e-6 |
| `ivreghdfe, liml, absorb(south)` | coef, SE | < 1e-6 |
| `first` 选项 | first-stage F, Shea partial R² | < 1e-4 |
| `weakiv` 选项 | KP rk Wald F, Stock-Yogo critical values | < 1e-4 |

### C1.6 Gravity PPML 专项验证

| 场景 | 比对字段 | rtol |
|------|---------|------|
| `ppmlhdfe, vce(robust)` | coef, SE, ll, deviance, pseudo-R² | < 1e-4 (coef/SE); < 1e-3 (ll/deviance) |
| `ppmlhdfe, vce(cluster pair_id)` | coef, cluster SE | < 1e-4 |
| `ppmlhdfe, eform` | IRR, SE | < 1e-4 |
| `predict, mu` | mu (predicted mean) | < 5e-3 (IRLS 收敛差异) |
| `predict, pearson` | pearson residuals | < 5e-3 |
| `predict, deviance` | deviance residuals | < 5e-3 |
| `separation` 检测 | separated regressors 列表 | 精确匹配 |

### C1.7 DID Policy 专项验证

| 场景 | 比对字段 | rtol |
|------|---------|------|
| `did_imputation, basic` | ATT, SE, event-time coef | < 1e-6 |
| `did_imputation, controls + pretrends` | ATT, SE, pretrend F | < 1e-6 |
| `csdid, reg` | ATT(g,t), aggregated ATT | < 1e-6 |
| `csdid, dripw` | ATT(g,t), SE | < 0.2 (已知偏差) |

### C1.8 RD Senate 专项验证

| 场景 | 比对字段 | rtol |
|------|---------|------|
| `rdrobust, sharp, 各 bwselect` | tau, SE, bandwidth h | < 5e-3 (带宽); < 1e-6 (tau/SE 给定 h) |
| `rdrobust, fuzzy` | tau, SE | < 1e-6 |
| `rdrobust, cluster(state)` | tau, cluster SE | < 1e-4 |

---

## 交付物清单

### 新增文件（每个实验 ~6 个，共 ~30 个）

```
research/experiments/
├── c1_1_capm_ff3/
│   ├── README.md
│   ├── data_prep.py
│   ├── analysis.do
│   ├── analysis.py
│   └── results.md
├── c1_4_card_iv/
│   ├── README.md
│   ├── data_prep.py
│   ├── analysis.do
│   ├── analysis.py
│   └── results.md
├── c1_6_gravity_ppml/
│   ├── README.md
│   ├── data_prep.py
│   ├── analysis.do
│   ├── analysis.py
│   └── results.md
├── c1_7_did_ezunem/
│   ├── README.md
│   ├── data_prep.py
│   ├── analysis.do
│   ├── analysis.py
│   └── results.md
└── c1_8_rd_senate/
    ├── README.md
    ├── data_prep.py
    ├── analysis.do
    ├── analysis.py
    └── results.md

tests/golden/
├── test_v2_c1_1_capm_ff3_real.py
├── test_v2_c1_4_card_iv_real.py
├── test_v2_c1_6_gravity_ppml_real.py
├── test_v2_c1_7_did_ezunem_real.py
└── test_v2_c1_8_rd_senate_real.py

stata/cases/  (按需)
└── v2_c1_*_data.dta, v2_c1_*.do
```

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `docs/testing/test-case-catalog.md` | 登记 v2_c1_* 测试样例（status: done） |
| `docs/command-support-matrix/regress.md` | 更新真实数据验证状态 |
| `docs/command-support-matrix/ivreghdfe.md` | 更新真实数据验证状态 |
| `docs/command-support-matrix/ppmlhdfe.md` | 更新真实数据验证状态 |
| `docs/command-support-matrix/did-imputation.md` | 更新真实数据验证状态 |
| `docs/command-support-matrix/csdid.md` | 更新真实数据验证状态 |
| `docs/command-support-matrix/rdrobust.md` | 更新真实数据验证状态 |
| `docs/release/known-issues.md` | 记录新发现的偏差 |
| `workspace/current-task/REPORT.md` | Phase 3 Wave 1 完成报告 |

---

## 成功标准

- [ ] **5 个实验全部完成**，每个有完整的 README + data_prep + analysis.do/py + results.md
- [ ] **5 个 golden 测试文件全部通过**：`pytest tests/golden/test_v2_c1_*_real.py -v` 0 failed
- [ ] **全量回归测试通过**：`pytest tests/ --ignore=tests/golden/ -q` 0 failed（与执行前一致）
- [ ] **所有 VCE/estimator 组合都有 Stata 双跑输出**，无跳过
- [ ] **C1.6 PPMLHDFE 实验包含 P1 VCE 修正验证结论**（与 Stata 一致/不一致 + 证据）
- [ ] **C1.7 CSDID DR SE 偏差有根因分析**
- [ ] **C1.8 RD 带宽选择器在真实数据上的偏差已量化并文档化**
- [ ] **所有不可解释的偏差已通过 ADR 或在 results.md 中记录**
- [ ] **test-case-catalog.md 已更新**，新增样例登记
- [ ] **支持矩阵已更新**，真实数据验证状态反映实验结果

---

## 后续 Waves

Phase 3 Wave 1 完成后，进入以下后续阶段：

| Wave | 实验 | 数据状态 |
|------|------|---------|
| Wave 2 | C1.9 DK HAC (wagepan)、C1.10 Slopes (wagepan)、C1.3 CEO/wagepan、C1.5 Mroz | wagepan + mroz 已在项目中 |
| Wave 3 | C1.2 Compustat（需外部获取） | 需要 Kaggle/WRDS 访问 |

---

*本任务卡定义 Phase 3 Wave 1 的完整范围。执行过程中发现的新风险项应记录在 REPORT.md 中，不阻塞当前 wave 推进。*
