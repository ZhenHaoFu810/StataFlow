# M02 Panel / FE 模块独立审查计划 v1.3

**Goal:** 对 StataFlow 的 M02 Panel / FE 模块（`FixedEffectsOLS`、`xtreg_fe()`、单吸收 `areg()` 路径、within transformation、组内共线性、cluster-robust FE VCE、预测与常数项传播）进行独立审查，发现数学错误、统计语义偏差、代码缺陷、边界条件错误、结果字段错误和 Stata 17 复现失败。本轮只记录问题，不修改产品代码。

**Architecture:** 每个实验独立设计新的 DGP / 面板结构，独立编写新的 Stata 17 `.do` 文件和新的 Python 审查脚本，现场执行字段级双跑。审查资产保存在 `docs/audit/modular-revalidation-v1.3/M02-panel-fe/evidence/` 下。

**Tech Stack:** Python 3.11, NumPy, pandas, SciPy, statsmodels, Stata 17, project `stataflow` package.

---

## 审查基线

| 项目 | 值 |
|---|---|
| 基线分支 | `dev` |
| 基线 commit SHA | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| Stata | 17 |

---

## 纳入审查的 API

- 核心估计器：`stataflow.FixedEffectsOLS`
- Stata 兼容层：`stataflow.compat.stata.xtreg_fe`、`areg` 中的 FE 相关路径
- within transformation、组内共线性检测、cluster-robust FE VCE
- `add_constant` 与 `_cons` VCE 扩展
- `predict`（xb/residuals）

---

## 关键风险领域

1. **within transformation 与 LSDV 等价性**
2. **组内不变 / 组内共线变量的删除**
3. **不平衡面板、singleton、缺失期**
4. **FE 自由度、常数项、df_model/df_resid**
5. **FE 内聚类 vs FE 外聚类**
6. **`xtreg_fe()` 与 `areg()` 的语义差异**
7. **`add_constant=True` 时 `_cons` 的 VCE 扩展**
8. **weights 不支持但文档未明确边界**

---

## 实验设计

### Synthetic

1. **S1**: 手工小面板（n=12, 3 entities × 4 periods），验证 within 系数与 LSDV 等价
2. **S2**: 中等样本随机面板，验证 conventional FE VCE
3. **S3**: 组内不变变量（z_i）应被删除
4. **S4**: 不平衡面板 + singleton entity
5. **S5**: FE + cluster，cluster 与 panel id 不一致
6. **S6**: `add_constant=True`，验证 `_cons` 系数与 VCE
7. **S7**: 近共线 within 变量（M01-LIN-002 的 FE 版本）

### Real-Data

1. **R1**: Grunfeld 面板数据，`xtreg invest mvalue, fe cluster(firm_id)`（cluster-robust FE，与旧 golden 的 conventional VCE 规格不同）
2. **R2**: Grunfeld 面板数据，`xtreg invest mvalue i.year, fe`（entity FE + time dummies 两向 within）

### Property Tests

1. **P1**: 实体标签重命名不影响估计
2. **P2**: 时间重排不影响估计
3. **P3**: within transformation 后增加组内不变列应被删除
4. **P4**: 合法尺度变换下斜率估计不变

---

## 交付物

- `task_plan.md`（本文件）
- `test-design-register.md`
- `findings.md`
- `progress.md`
- `summary.md`
- `evidence/synthetic/`
- `evidence/real-data/`
- `evidence/minimal-reproductions/`
- Python 审查脚本：`tests/audit_v1_3/m02_panel_fe/`
  - `audit_utils.py`
  - `test_m02_synthetic.py`
  - `test_m02_realdata.py`
  - `test_m02_property.py`
  - `repro_m02_fe_findings.py`
- Stata `.do` 文件：`stata/cases/audit_v1_3_m02/`
