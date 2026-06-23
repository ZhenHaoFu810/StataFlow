# M07 DID / Event Study 独立审查发现

## 执行基线

- 模块: M07 DID / Event Study
- 审查日期: 2026-06-13
- 基线分支: `dev`
- 基线 commit: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- Python: 3.11.7, NumPy 1.26.4, pandas 3.0.2, SciPy 1.17.1, statsmodels 0.14.6
- Stata 17 MP: `D:\Software\Stata17\StataMP-64.exe`
- 本轮未修改 `src/stataflow/` 产品代码

---

## M07-DID-001: DIDImputation 未遵循 Stata 的 `first_treat` 编码约定

- **Finding ID**: M07-DID-001
- **Severity**: P1
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `stataflow.DIDImputation.fit(...)` / `stataflow.compat.stata.did_imputation(...)`
- **最小复现**: `tests/audit_v1_3/m07_did_event_study/test_m07_synthetic.py::TestM07S7FirstTreatSemantics` 与 `test_m07_realdata.py::TestM07R1EzunemDidImputationControls`
- **Stata 17 语义（Borusyak `did_imputation` ado, Nov 2023）**:
  - `first_treat` 为 **缺失** 表示 never-treated（控制组）。
  - `first_treat = 0` 被解析为在第 0 期接受治疗（`K = t - 0 >= 0`），因此所有对应观测被划入处理组，而非控制组。
  - 负值同样被解析为已处理（`K = t - (-1) > 0`）。
- **Python 当前语义**:
  - 样本筛选会 **删除** `first_treat` 缺失的行（`key_vars` 包含 `first_treat`，`dropna` 处理）。
  - `first_treat <= 0`（包括 0 与负值）被解释为 never-treated。
- **根因分析**: 两种语义在“缺失 vs. 0/负值”上正交。使用 Stata 约定（缺失为 never-treated）的数据在 Python 中会丢失全部控制组；使用 Python 约定（0 为 never-treated）的数据在 Stata 中会把 never-treated 单元误判为处理组。因此任何包含 never-treated 单元的 `did_imputation` 双跑都会失败。
- **用户影响**: 用户无法同时满足 Stata 兼容层与 Python 原生层的语义；`autosample`、nobs、sample_mask、tau 系数/SE 全部不可比。
- **受影响范围**: 所有使用 `did_imputation` 且存在 never-treated 单元（以 Stata 缺失或 Python 0 编码）的调用。
- **共享基础设施问题**: 否，属于 `DIDImputation` 自身样本筛选与编码约定。
- **旧 issue**: 未发现已登记的同类问题；wrapper docstring 反而声称“zero or negative values identify never-treated units”，与 Stata ado 实现不符。
- **建议修复方向**:
  1. 在 `DIDImputation.fit()` 中保留 `first_treat` 缺失的行，并将其视为 never-treated（与 Stata 一致）。
  2. 明确 `first_treat <= 0` 的行为：要么在 wrapper 中拒绝，要么统一 recode 为缺失。
  3. 更新 `compat.stata.did_imputation` 的 docstring 以匹配 Stata 约定。

---

## M07-DID-002: DIDImputation 核心算法在相同语义下可字段级对齐

- **Finding ID**: M07-DID-002
- **Severity**: P1（已降级为测试设计问题，非核心算法缺陷）
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `stataflow.DIDImputation.fit(...)`
- **最小复现**: 当 synthetic 面板中 **不存在 0/缺失 first_treat**（所有单元均为正 cohort，或使用超出末期的 cohort 作为伪 never-treated 控制组）时，S1/S2/S3/S8 均通过。
- **Stata 17 结果（S1, no-never-treated）**: tau beta = 1.962036, SE = 0.090837
- **Python 结果（S1, no-never-treated）**: tau beta = 1.962036, SE = 0.090610
- **根因分析**: 原始 S1-S3/S7/S8 失败主要源于 `first_treat=0` 在 Stata 中被错误地视为处理组，而不是 Python 的 imputability 判定过于宽松。在消除编码差异后，nobs/sample_mask、系数（<1e-7 相对误差）和 SE（<2% 残余，主要来自 cluster VCE 的小样本自由度调整）均高度一致。
- **用户影响**: 在修复 M07-DID-001 的编码约定后，autosample 与核心估计公式本身可能只需少量调整即可对齐。
- **建议修复方向**: 优先修复 M07-DID-001；修复后重新运行 R1 与 S7 确认残余差异。

---

## M07-DID-003: CSDID `notyet=True` 控制组定义与 Stata 不一致

- **Finding ID**: M07-DID-003
- **Severity**: P0
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `stataflow.CSDID.fit(method="reg", cluster=..., notyet=True).estat_event()`
- **最小复现**: `tests/audit_v1_3/m07_did_event_study/test_m07_realdata.py::TestM07R2EzunemCsdidNotyetEvent`
- **Stata 17 结果（R2）**:
  - nobs = 198
  - Pre_avg beta = 3165.482, SE = 5921.608
  - Post_avg beta = -9375.683, SE = 18480.53
  - ATT(1984,1981) = 6459.312
- **Python 结果（R2）**:
  - nobs = 50
  - Pre_avg beta = 13381.194, SE = 11125.181
  - Post_avg beta = -43924.333, SE = 18013.734
  - ATT(1984,1981) = 7943.000
- **根因分析**: Stata 的 `csdid, notyet` 选项将 **never-treated 与 not-yet-treated 单元同时作为控制组**（结果表下方显示 “Control: Not yet Treated”，但 help 文件与实测数据表明 never-treated 也被包含）。Python 当前实现将 `notyet=True` 理解为“强制仅使用 not-yet-treated 控制组并忽略 never-treated”，导致控制组规模偏小、ATT(g,t) 数值与 SE 均发生显著偏差。以 ATT(1984,1981) 为例，手动计算使用“仅 1985 队列”得到 7943，与 Python 一致；使用“1985 队列 + never-treated”得到 6459.31，与 Stata 一致。
- **用户影响**: 在真实面板中使用 `notyet=True` 会得到错误的经济/统计结论。
- **受影响范围**: CSDID 的 `notyet=True` 路径，尤其是同时存在 never-treated 单元时。
- **建议修复方向**: 将 `notyet=True` 的控制组改为“`first_treat == 0` 或 `first_treat > max(g, t)`”，并复核 influence-function scaling 与 event 聚合权重。

---

## M07-DID-004: DIDImputation `first_treat` 负值/零值语义与 Stata 冲突

- **Finding ID**: M07-DID-004
- **Severity**: P1（与 M07-DID-001 同源）
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `stataflow.DIDImputation.fit(...)`
- **最小复现**: `tests/audit_v1_3/m07_did_event_study/test_m07_synthetic.py::TestM07S7FirstTreatSemantics`
- **Stata 17 结果**: 当部分单元 `first_treat` 被设为 0、-1 或缺失时，Stata 将 0 与 -1 视为已处理，缺失视为 never-treated；Python 将 0 与 -1 视为 never-treated，缺失则直接删除。
- **根因分析**: 见 M07-DID-001。两种实现使用互不兼容的 never-treated 编码。
- **用户影响**: 使用负值编码 never-treated 时，Python 与 Stata 结果不可比；wrapper 的 docstring 误导用户认为 0/negative 是合法 never-treated 编码。
- **建议修复方向**: 对齐 Stata 约定（缺失为 never-treated），并在 wrapper 中对 0/负值 first_treat 给出明确错误或自动 recode。

---

## M07-DID-005: EventStudyInteract 系数对齐良好但 SE 存在约 0.5–1.5% 残余

- **Finding ID**: M07-DID-005
- **Severity**: P3
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `stataflow.EventStudyInteract.fit(vce="cluster", cluster=...)`
- **最小复现**: `tests/audit_v1_3/m07_did_event_study/test_m07_synthetic.py::TestM07S6EventStudyInteract`
- **Stata 17 结果**: 例如 Dm2 SE = 0.1045991
- **Python 结果**: Dm2 SE = 0.1045138
- **根因分析**: 系数完全一致（<1e-7），说明 IW 权重与交互回归系数正确。SE 的微小差异可能来自：1) 加权残差或 meat 矩阵的小样本修正；2) 迭代 demeaning 收敛阈值；3) 协方差中 cohort-share 估计的加权方式。
- **用户影响**: 残余 <2%，对推断结论无实质影响。
- **受影响范围**: EventStudyInteract 的 cluster VCE。
- **建议修复方向**: 若需严格 1e-5 对齐，可进一步比较中间残差和 meat 矩阵；当前可接受为已知残余并文档化。

---

## M07-DID-006: `did_imputation` 当前 ado 不支持 `window()` 选项

- **Finding ID**: M07-DID-006
- **Severity**: P2
- **Evidence Status**: Confirmed-Stata
- **Affected API**: N/A（Stata 命令层面）
- **最小复现**: S2 原始命令 `did_imputation ..., allhorizons window(-1 3) ...` 报 `option window() not allowed`。
- **根因分析**: 当前安装的 Borusyak `did_imputation` 版本（Nov 2023）未实现 `window()`。
- **用户影响**: 无法通过 wrapper 直接映射 Stata 的 `window()` 语义。
- **受影响范围**: `did_imputation` wrapper 的 `window` 参数。
- **建议修复方向**: 在 wrapper 中检测 ado 版本，或文档化 `window` 参数的支持边界。S2 已改为仅验证 `allhorizons`。

---

## 已验证通过的路径

- DIDImputation basic / allhorizons / controls+pretrends / custom cluster，在消除 `first_treat` 编码差异后（S1-S3, S8）：nobs、tau 系数/SE 字段级对齐（beta <1e-7，SE <2%）。
- CSDID reg event 聚合（S4）：nobs、全部 event 系数/SE 与 Stata 字段级对齐。
- CSDID reg notyet event 聚合在合成无 never-treated 面板（S5）：字段级对齐。
- EventStudyInteract IW 事件研究（S6）：系数高度对齐，SE 残余 <2%。
- Python 内部性质（P1-P3）：行顺序、无关列、y 缩放均保持系数/SE 不变。
