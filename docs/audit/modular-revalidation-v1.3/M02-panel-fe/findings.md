# M02 Panel / FE 审查发现 findings.md

## 基线

| 项目 | 值 |
|---|---|
| 模块 | M02 Panel / FE |
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| 核心对象 | `FixedEffectsOLS`、`xtreg_fe`、`areg` 单吸收路径 |

---

## M02-FE-001：FE 整体 F 统计量 p-value 使用错误的 `df_model`

- **Severity**: P1
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `FixedEffectsOLS(..., add_constant=True).fit(vce='ols')`
- **最小复现**: `tests/audit_v1_3/m02_panel_fe/repro_m02_fe_findings.py::repro_001_f_pvalue_df_model`
- **Stata 17 结果**:
  - `e(df_m) = 3`（= G + k - 1，G=3 entities，k=1 slope）
  - `Ftail(e(df_m), e(df_r), e(F))` 报告 p-value（如 S1 中为 `9.532e-08`）
- **Python 结果**:
  - `df_model = 3`（与 Stata 一致）
  - `f_pvalue` 使用 `dfn = k = 1` 计算（S1 中为 `7.85e-07`），与 Stata 不一致
- **根因分析**:
  - 代码中 F 统计量分子自由度可能错误地使用了斜率个数 `k`，而不是 Stata 的 `e(df_m)=G+k-1`。
  - 这导致 FE 模型整体 F 检验的 p-value 系统性偏小（更显著）。
- **用户影响**: 用户如果依赖 `ResultSchema.fit.f_pvalue` 做模型显著性判断，会得到错误的显著性结论。
- **受影响范围**: 所有含 FE 且 `add_constant=True` 的 conventional VCE 路径。
- **是否共享基础设施**: 否，问题局限于 `FixedEffectsOLS` 的 F 检验实现。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 在 `fe.py` 中让 `f_pvalue` 的分子自由度等于 `df_model`（即 `G + k - 1`），与 Stata `e(F_p)` 语义一致。

---

## M02-FE-002：`add_constant=True` 时组内共线变量删除后 VCE 维度不匹配导致崩溃

- **Severity**: P0
- **Evidence Status**: Confirmed-Code / Confirmed-Stata
- **Affected API**: `FixedEffectsOLS(..., add_constant=True).fit(...)`
- **最小复现**: `repro_m02_fe_findings.py::repro_002_collinear_drop_crash`
- **Stata 17 结果**:
  - `xtreg y x z, fe` 正常完成，自动省略 `z`。
- **Python 结果**:
  - `FixedEffectsOLS(df, y='y', x=['x','z'], fe='entity', add_constant=True).fit(vce='ols')` 抛出 `LinAlgError: Singular matrix`。
- **根因分析**:
  - `fe.py` 在 within transformation 后调用 `detect_collinear_columns` 删除共线列，但删除后未更新 `k`。
  - 随后 `add_constant=True` 路径按原始 `k` 扩展 VCE，导致 `X_full` 维度与 `row_names` / `beta` 长度不一致，最终解正规方程时奇异。
- **用户影响**: 任何包含组内共线变量（如实体不变变量、重复测量构造的变量）且请求常数项的 FE 模型都会崩溃。
- **受影响范围**: `FixedEffectsOLS` 的 `add_constant=True` 路径。
- **是否共享基础设施**: `detect_collinear_columns` 是共享函数，但崩溃根因在于 `fe.py` 使用其返回值后未同步更新维度。
- **旧 issue**: 与 M01-LIN-002 同源（近共线性 tolerance），但在 FE 中表现为崩溃而非错误系数。
- **建议修复方向**: 删除共线列后同步更新 `k`、`self.x`、系数名，并确保 `_cons` VCE 扩展基于实际保留的斜率维度。

---

## M02-FE-003：非平衡面板 + singleton 下 `_cons` 系数与标准误偏离 Stata

- **Severity**: P1
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `FixedEffectsOLS(..., add_constant=True).fit(vce='ols')`
- **最小复现**: `repro_m02_fe_findings.py::repro_003_unbalanced_cons`
- **Stata 17 结果**:
  - `_cons` beta = `0.1932`，SE = `0.2113`
- **Python 结果**:
  - `_cons` beta = `0.1435`，SE = `0.2170`
- **根因分析**:
  - `add_constant=True` 时 Python 通过 LSDV 扩展 VCE 来恢复 `_cons` 的系数与方差。
  - 在非平衡面板或 singleton entity 场景下，FE 虚拟变量矩阵不满秩或 `_cons` 与实体均值的加权平均不一致，导致恢复公式与 Stata 的 LSDV 结果产生偏差。
- **用户影响**: 使用 `add_constant=True` 解释整体均值时，常数项置信区间错误。
- **受影响范围**: 非平衡面板、含 singleton 的 FE 模型。
- **是否共享基础设施**: 否，问题在 `_cons` 恢复逻辑。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 检查 `_cons` 恢复使用的均值权重是否与 Stata LSDV 一致（按实体有效观测数加权），并验证 singleton 的处理。

---

## M02-FE-004：cluster FE 下 `df_model`、`r2_adj` 与 Stata 不一致，F p-value 缺失

- **Severity**: P1
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `FixedEffectsOLS(...).fit(vce='cluster', cluster=...)`
- **最小复现**: `repro_m02_fe_findings.py::repro_004_cluster_df_model`
- **Stata 17 结果**:
  - `e(df_m) = 0`
  - `e(r2_a) = 0.0131`
  - cluster VCE 下不输出模型 F p-value
- **Python 结果**:
  - `df_model = 1`
  - `r2_adj = -0.1682`（与 Stata 方向相反且幅度大）
  - `f_pvalue` 被计算出来（但 Stata 此时不报告）
- **根因分析**:
  - Python 在 cluster VCE 下仍按 `k` 设置 `df_model=1`，而 Stata `xtreg, fe cluster()` 将 `e(df_m)` 设为 0。
  - `r2_adj` 的分母自由度因此不同，导致大幅偏离。
  - Python 未识别 cluster FE 下不报告 F p-value 的语义。
- **用户影响**: cluster-robust FE 结果中的模型自由度、调整 R² 和 F 检验不可信。
- **受影响范围**: 所有 `vce='cluster'` 的 FE 估计。
- **是否共享基础设施**: 否。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 对齐 Stata cluster FE 的 `df_model` 语义；在 cluster VCE 下按 Stata 约定处理 `r2_adj` 和 `f_pvalue`（可设为 `None` 或按 Stata 公式）。

---

## M02-FE-005：`xtreg_fe()` wrapper 默认 `constant=False`，与 Stata `xtreg, fe` 默认行为不一致

- **Severity**: P1
- **Evidence Status**: Confirmed-Code
- **Affected API**: `stataflow.compat.stata.xtreg_fe(...)`
- **最小复现**: `repro_m02_fe_findings.py::repro_005_wrapper_default_constant`
- **Stata 17 结果**:
  - `xtreg y x, fe` 始终报告 `_cons`。
- **Python 结果**:
  - `xtreg_fe(df, y='y', x=['x'], fe='entity')` 返回的系数名只有 `['x']`，默认不报告 `_cons`。
- **根因分析**:
  - `xtreg_fe` wrapper 的函数签名默认 `constant=False`。
  - Stata `xtreg, fe` 没有 `noconstant` 选项，始终估计 `_cons`（整体均值）。
- **用户影响**: 默认调用 `xtreg_fe()` 得到的结果与 Stata 输出字段不一致，脚本迁移时容易遗漏 `_cons`。
- **受影响范围**: `xtreg_fe()` wrapper 默认调用。
- **是否共享基础设施**: 否。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 将 `xtreg_fe()` 的 `constant` 默认值改为 `True`，与 Stata `xtreg, fe` 行为一致。

---

## M02-FE-006：组内近共线变量未被省略

- **Severity**: P1
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `FixedEffectsOLS(...).fit(vce='ols')`
- **最小复现**: `repro_m02_fe_findings.py::repro_006_within_collinear_not_dropped`
- **Stata 17 结果**:
  - `xtreg y x w, fe` 报告 `w` 为 `o.w`（omitted）。
- **Python 结果**:
  - Python 保留 `w`，报告巨大系数和 SE（近奇异）。
- **根因分析**:
  - `detect_collinear_columns` 的 tolerance 太松，无法识别 within-transformed 后的近共线关系。
  - 与 M01-LIN-002 共享根因：共享基础设施 `_vce_utils.py` 的 QR/伪逆秩判定阈值未对齐 Stata。
- **用户影响**: 用户可能在回归中保留实际上与已有变量组内共线的变量，得到数值不稳定的系数和错误推断。
- **受影响范围**: 所有使用 `detect_collinear_columns` 的模块：M01 Linear、M02 FE、M03 HDFE、M04 IV 等。
- **是否共享基础设施**: **是**（`detect_collinear_columns` / `_vce_utils.py`）。
- **旧 issue**: M01-LIN-002 已记录。
- **建议修复方向**: 统一收紧/校准共享共线性检测的 tolerance，并在 within transformation 后再次检查条件数。

---

## M02-FE-007：实体内部不变变量未被删除（或导致崩溃）

- **Severity**: P1
- **Evidence Status**: Confirmed-Code / Confirmed-Stata
- **Affected API**: `FixedEffectsOLS(...).fit(vce='ols')`
- **最小复现**: `repro_m02_fe_findings.py::repro_007_entity_invariant_not_dropped`
- **Stata 17 结果**:
  - `xtreg y x z, fe` 自动删除 `z`。
- **Python 结果**:
  - 当 `z` 完全实体不变时，`add_constant=True` 导致 `LinAlgError: Singular matrix`；加极小扰动时保留 `z` 并给出巨大估计。
- **根因分析**:
  - within transformation 后实体不变列应全为 0，但代码未在 transformation 前识别并删除这类变量。
  - 结果导致设计矩阵奇异或近奇异。
- **用户影响**: 与 M02-FE-002 类似，任何实体层面变量（如区域固定属性）进入 FE 模型都会失败或给出错误结果。
- **受影响范围**: 所有 FE 路径。
- **是否共享基础设施**: 否，问题在于 `FixedEffectsOLS._prepare_data` / within transformation 前的变量筛选。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 在 within transformation 之前检查每个 `x` 在 `fe` 组内的方差；方差为 0 或近 0 的列应标记为 omitted 并从模型中删除。

---

## 共享基础设施风险登记

### SI-VCE-001：`detect_collinear_columns` tolerance 偏松

- **影响模块**: M01、M02、M03、M04
- **具体表现**: 近共线变量在 OLS/FE/HDFE/IV 中均未被正确省略。
- **证据**: M01-LIN-002、M02-FE-006
- **建议**: 在共享基础设施层面统一校准 QR/SVD tolerance，并在各估计器中补充 post-drop 维度一致性校验。

---

## 未发现问题的说明

- 平衡面板、常规 VCE 下的 slope 系数与 SE 在 1e-6 内可复现 Stata（S2、R2）。
- 实体标签重命名、时间重排、尺度变换等性质测试通过（P1、P2、P4）。
