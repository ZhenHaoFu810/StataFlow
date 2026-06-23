# M07 DID / Event Study 模块独立审查总结

## 审查目标

对 `stataflow.DIDImputation`、`stataflow.EventStudyInteract`、`stataflow.CSDID` 三个核心估计器及其 Stata 兼容层进行独立、不依赖旧 golden 的双跑审查。本轮禁止修改 `src/stataflow/` 产品代码，仅创建测试、证据与文档。

## 审查范围与资产

- **新建 synthetic 双跑**: 8 个（S1-S8）
- **新建真实数据双跑**: 2 个（R1-R2）
- **新建 property tests**: 3 个（P1-P3）
- **最小复现脚本**: `tests/audit_v1_3/m07_did_event_study/repro_m07_did_findings.py`
- **通用工具**: `tests/audit_v1_3/m07_did_event_study/m07_audit_utils.py`
- **文档**: `findings.md`, `progress.md`, `test-design-register.md`

## 关键结论

### 1. DIDImputation 的核心算法在语义一致时高度对齐 Stata（M07-DID-002）

原始 subagent 报告将 S1-S3/S7/S8 的失败归因于 Python autosample 过于宽松。Root-agent 现场复核后发现，失败主要源于 `first_treat` 编码不一致：Stata `did_imputation` 要求 **缺失值** 表示 never-treated，而 Python 将 **0/负值/缺失** 都视为 never-treated 且会 **删除缺失行**。当 synthetic 面板中避免使用 0/缺失编码 never-treated（所有单元均为正 cohort，或使用末期之后的 cohort 作为伪 never-treated 控制组）时，DIDImputation 的 nobs、sample_mask、tau 系数（<1e-7）和 SE（<2% 残余）均与 Stata 字段级对齐。

### 2. DIDImputation `first_treat` 编码约定与 Stata 不兼容（M07-DID-001/004）

- Python 删除 `first_treat` 缺失的行，Stata 将其作为控制组。
- Python 将 `first_treat=0` 视为 never-treated，Stata 将其视为在第 0 期已处理。
- 该问题导致任何包含 Stata 风格 never-treated（缺失）或 Python 风格 never-treated（0）的数据都无法双跑对齐。`compat.stata.did_imputation` 的 docstring 也错误地声称 0/negative 是合法 never-treated 编码。

### 3. CSDID `notyet=True` 在真实数据上严重偏离 Stata（M07-DID-003）

Stata 的 `csdid, notyet` 选项实际使用 **never-treated + not-yet-treated** 作为控制组，而 Python 当前实现强制仅使用 not-yet-treated 并排除 never-treated。在 ezunem 真实数据上，这导致 ATT(g,t) 量级与符号均不一致（例如 ATT(1984,1981) Python=7943 vs Stata=6459），event 聚合结果也严重偏离。

### 4. EventStudyInteract 基本正确（M07-DID-005）

Sun-Abraham IW 估计器在合成数据中系数与 Stata 高度一致（<1e-7），标准误存在约 0.5–1.5% 的系统残余，对推断无实质影响。

### 5. CSDID 默认/never-treated 路径正确

合成有 never-treated 面板（S4）的 event 聚合与 Stata 字段级对齐（<1e-5）；无 never-treated 时的 notyet 路径（S5）也对齐。

### 6. Python 内部性质稳定

行顺序不变性、无关列不变性、y 缩放不变性在 Python 内部均保持系数/SE 不变；与 Stata 的差异集中在样本编码和特定算法路径。

## 建议后续行动

1. **优先修复 M07-DID-001/004**: 对齐 Stata 的 `first_treat` 编码约定（缺失 = never-treated，保留缺失行），明确 0/负值的处理方式，并更新 wrapper docstring。
2. **优先修复 M07-DID-003**: 将 CSDID `notyet=True` 的控制组改为“never-treated 或 not-yet-treated”，并复核 influence-function scaling 与 event 聚合权重。
3. **评估 M07-DID-005**: 决定 EventStudyInteract SE 残余是否作为已知局限接受。
4. **更新支持矩阵**: 注明当前 `did_imputation` wrapper 的 `window()` 参数依赖 ado 版本（M07-DID-006）。
5. **修复后重跑**: M07-DID-001/003 修复后，重新运行 R1/R2 与 S7。

## 审查完成度

- [x] 8 synthetic 双跑（含调整后的 S1/S2/S8 与 xfail 的 S7）
- [x] 2 真实数据双跑（R1/R2 均为 xfail，分别对应 M07-DID-001 与 M07-DID-003）
- [x] 3 property tests（P1-P3，全部通过）
- [x] 6 confirmed findings（1 P0 + 3 P1 + 1 P2 + 1 P3）
- [x] 全部证据已保存并可复跑
- [x] 全量非 golden 回归测试已执行
- [x] REPORT.md 追加/更新已完成

## 风险与限制

- `did_imputation` 的 `window()` 选项依赖 ado 版本；S2 已改为验证 `allhorizons`。
- DIDImputation 的编码问题会掩盖其他潜在问题（如 pretrend F-test、custom cluster 等），需在编码修复后重新验证。
- CSDID `notyet` 真实数据差异需要算法级复核，可能涉及控制组选择、IF scaling 和 event 聚合的多处调整。
