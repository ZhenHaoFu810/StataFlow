# M04 IV / GMM 审查发现 findings.md

## 基线

| 项目 | 值 |
|---|---|
| 模块 | M04 IV / GMM |
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| 核心对象 | `IV2SLS`、`IVAbsorbingOLS`、`ivregress_2sls()`、`ivreghdfe()` |

---

## M04-IV-001：弱工具变量诊断未在 `ResultSchema.diagnostics` 中暴露

- **Severity**: P1
- **Evidence Status**: Confirmed-Code / Confirmed-Stata
- **Affected API**: `IV2SLS`、`IVAbsorbingOLS`（包括 `ivregress_2sls` 和 `ivreghdfe` wrapper）
- **最小复现**: `tests/audit_v1_3/m04_iv_gmm/repro_m04_iv_findings.py::repro_001_missing_weakiv_diagnostics`
- **Stata 17 结果**:
  - `ivreg2 y (x = z), robust` 返回 `e(widstat)`（如 0.736）
  - `ivreghdfe y (x = z), absorb(firm year) cluster(firm)` 返回 `e(widstat)`（如 160.29）
- **Python 结果**:
  - `result.diagnostics.widstat` 为 `None`
  - 无论是 `IV2SLS` 还是 `IVAbsorbingOLS`，无论是 no-FE 还是多 FE，均未暴露 `widstat`
- **根因分析**:
  - 代码实现中 `IVAbsorbingOLS` 计算了 `widstat`/`idstat` 等弱 IV 诊断，但它们没有被写入返回的 `ResultSchema.diagnostics`。
  - `IV2SLS` 完全没有计算弱 IV 诊断，但 `docs/command-support-matrix/ivregress-2sls.md` 等文档声明其已支持。
- **用户影响**: 用户无法从结果对象读取弱工具变量诊断，无法做 Stock-Yogo 阈值比较，与 Stata 输出字段不一致。
- **受影响范围**: 所有 `IV2SLS` 和 `IVAbsorbingOLS` 调用。
- **是否共享基础设施**: 否。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 将 `IVAbsorbingOLS` 内部已计算的 `widstat`/`idstat` 写入 `ResultSchema.diagnostics`；在 `IV2SLS` 中补充弱 IV 诊断计算，或更新支持矩阵说明未实现。

---

## M04-IV-002：LIML 的 SE、RMSE、F 统计量与 Stata 不一致

- **Severity**: P1
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `IVAbsorbingOLS(..., estimator='liml').fit(vce='ols')`
- **最小复现**: `repro_m04_iv_findings.py::repro_002_liml_vce_mismatch`
- **Stata 17 结果**:
  - `ivreg2 y (x = z1 z2), liml`
  - x SE = 0.1344，RMSE = 0.8136，F = 105.20
- **Python 结果**:
  - x SE = 0.1356（+0.8%），RMSE = 0.8170（+0.4%），F = 105.80（+0.6%）
- **根因分析**:
  - LIML VCE 使用 `coviv`-empty 公式，其小样本修正、残差自由度或 LIML k 值可能与 Stata `ivreg2` 不一致。
  - 另外 `IVAbsorbingOLS` 在 LIML 路径下未报告 `_cons`，可能影响拟合统计量的计算基准。
- **用户影响**: LIML/Fuller 置信区间和假设检验不可靠。
- **受影响范围**: 所有 `estimator='liml'` 或 `fuller != 0` 的调用。
- **是否共享基础设施**: 否。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 以 Stata `ivreg2` LIML VCE 为基准，核对 `k` 值、残差计算和 small-sample 因子。

---

## M04-IV-003：`IVAbsorbingOLS` 常数吸收路径不报告 `_cons`

- **Severity**: P2
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `IVAbsorbingOLS(..., absorb='__one' / constant-like FE).fit(...)`
- **最小复现**: `repro_m04_iv_findings.py::repro_003_constant_absorb_no_cons`
- **Stata 17 结果**:
  - `ivreg2 y (x = z), robust` 报告 `x` 和 `_cons`
- **Python 结果**:
  - `IVAbsorbingOLS(..., absorb='__one')` 仅报告 `x`
- **根因分析**:
  - 当吸收变量为常数（所有观测同组）时，代码将常数视为被吸收的 FE，因此在报告的系数列表中省略 `_cons`。
  - 但 Stata 的 `ivreghdfe`/`ivreg2` 在无真实 FE 时仍会报告 `_cons`。
- **用户影响**: 与 Stata 输出字段不一致；通过 wrapper 调用时用户可能预期 `_cons` 存在。
- **受影响范围**: 无真实 FE 或常数 FE 的 `IVAbsorbingOLS` 调用。
- **是否共享基础设施**: 否。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 当吸收变量无实际分组信息时，保留 `_cons` 报告；或在 wrapper 层映射到 `IV2SLS`。

---

## M04-IV-004：真实数据 2SLS robust VCE 存在 5e-6 相对差异

- **Severity**: P2
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `IV2SLS(...).fit(vce='robust')`
- **Stata 17 结果**:
  - `ivregress 2sls invest (mvalue = kstock), robust`
- **Python 结果**:
  - 系数一致，VCE `max_rel_diff = 5.07e-6`，略超 1e-6 容差。
- **根因分析**:
  - 可能是 HC1 小样本修正因子或 residuals 计算与 Stata 存在第 6 位小数差异。
- **用户影响**: 严格复现场景下需要关注，但通常不影响定性结论。
- **受影响范围**: `IV2SLS` robust VCE。
- **是否共享基础设施**: 可能涉及 `_vce_utils`。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 逐元素比较 robust meat 与小样本因子。

---

## 共享基础设施风险登记

### SI-VCE-001：`detect_collinear_columns` tolerance 偏松

- **影响模块**: M01、M02、M03、M04
- **具体表现**: 近共线变量在 OLS/FE/HDFE/IV 中均可能未被正确省略。
- **证据**: M01-LIN-002、M02-FE-006
- **M04 影响**: IV 中如果工具变量、外生变量或 FE 存在近共线性，可能导致与 Stata 不同的变量保留集合。
- **建议**: 统一校准 tolerance，并在 IV 中加强识别秩检查。

---

## 未发现问题的说明

- 常规 2SLS robust/cluster 系数与 SE 在测试 DGP 下与 Stata 一致（S1、S2）。
- 过度识别 Hansen J 在 `IV2SLS` 下与 Stata `ivregress 2sls` 一致（S4）。
- ivreghdfe 2-FE cluster 系数与 SE 与 Stata 一致，仅 widstat 缺失（S5）。
- 工具变量标签重命名、尺度变换、行顺序等性质测试通过（P1-P3）。
