# M01 Linear 审查进度与基线

## 审查基线

| 项目 | 值 |
|---|---|
| 审查日期 | 2026-06-12 |
| 基线分支 | `dev` |
| 基线 commit SHA | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| NumPy | 1.26.4 |
| pandas | 3.0.2 |
| SciPy | 1.17.1 |
| statsmodels | 0.14.6 |
| Stata 可执行文件 | `D:\Software\Stata17\StataMP-64.exe`（存在） |

## 执行命令记录

```bash
# 记录环境
python --version
python -c "import numpy, pandas, scipy, statsmodels; print(...)"
git rev-parse HEAD
git status --short
ls -la "D:/Software/Stata17/StataMP-64.exe"

# 创建审查目录
mkdir -p docs/audit/modular-revalidation-v1.3/M01-linear/evidence/synthetic
mkdir -p docs/audit/modular-revalidation-v1.3/M01-linear/evidence/real-data
mkdir -p docs/audit/modular-revalidation-v1.3/M01-linear/evidence/minimal-reproductions
mkdir -p tests/audit_v1_3/m01_linear
mkdir -p stata/cases/audit_v1_3_m01
mkdir -p stata/output/audit_v1_3_m01
```

## 支持边界核对结果

| API | 参数 | 声明状态 | 实际行为 | 备注 |
|---|---|---|---|---|
| `OLS` | `add_constant`, `weights`, `weight_type`, `missing` | 已支持 | 已支持 | `weight_type` 仅支持 `aweight` |
| `OLS.fit` | `vce`, `cluster`, `alpha` | 已支持 | 已支持 | `vce` 支持 `ols`/`robust`/`cluster`；`cluster` 支持单变量或两变量列表 |
| `regress` | `vce`, `cluster`, `aweight`, `noconstant`, `missing`, `level` | 已支持 | 已支持 | `level` 通过 `kwargs` 解析为 `alpha` |
| `regress` | `beta`, `eform` | 已知未实现 | 抛出 `NotImplementedError` | 符合支持矩阵 |
| `regress` | 未知参数 | 硬拒绝 | 抛出 `ValueError` | 符合 public-api.md |
| `xtreg_fe` | `fe`, `vce`, `cluster`, `constant`, `missing`, `level` | 已支持 | 已支持 | 多路 cluster 硬拒绝 |
| `xtreg_fe` | 未知参数 | 硬拒绝 | 抛出 `ValueError` | 符合 |
| `areg` | `absorb`, `vce`, `cluster`, `aweight`, `noconstant`, `missing`, `level` | 已支持 | 已支持 | 多路 cluster 硬拒绝；仅支持单个 absorb |
| `areg` | 未知参数 | 硬拒绝 | 抛出 `ValueError` | 符合 |

### 边界发现

- `regress` 对 `vce="cluster varname"` 字符串语法的解析在 wrapper 层完成，但不支持更复杂的 Stata `vce(cluster var, ...)` 选项。
- `aweight` 传入数组 vs 变量名时行为一致（字符串从 `data` 取列，数组直接传入）。
- `level` 选项未在 `OLS.fit` 签名中显式声明，仅通过 `kwargs` 透传；这不是缺陷，但属于 wrapper 层的隐式支持。


## 实验执行结果

### Synthetic

| 实验 | 结果 | 备注 |
|---|---|---|
| S1_hand_computable | PASS | 解析真值与 Stata 一致 |
| S2_heteroskedastic | PASS | robust VCE 一致 |
| S3_imbalanced_cluster | PASS | 单路 cluster 一致 |
| S4_aweight_missing | PASS | 缺失权重删除一致 |
| S4b_aweight_zero | FAIL | Python 拒绝零权重；Stata 删除 → M01-LIN-001 |
| S5_near_collinearity | FAIL | Stata 省略 x1，Python 保留 → M01-LIN-002 |
| S6_factor_missing_changes_base | PASS | factor base 按有效样本重确定 |
| S7_two_way_cluster_balanced | 部分 FAIL | 系数/SE/VCE 一致，F-stat 语义不同 → M01-LIN-003 |

### Real-Data

| 实验 | 结果 | 备注 |
|---|---|---|
| R1_engel_robust | PASS | Engel 数据 robust OLS 一致 |
| R2_modechoice_two_way_cluster | FAIL | SE 1–3% 差异，F-stat 语义不同；与 M01-LIN-003 和小 G 调整有关 |

### Property Tests

| 实验 | 结果 | 备注 |
|---|---|---|
| P1_row_order_invariance | PASS | 行重排不影响结果 |
| P2_irrelevant_column | PASS | 无关缺失列不影响结果 |
| P3_scale_transformation | PASS | 尺度变换系数/SE 可推导 |

### 执行命令

```bash
# Synthetic
python tests/audit_v1_3/m01_linear/test_synthetic.py

# Real-data
python tests/audit_v1_3/m01_linear/test_realdata.py

# Property tests
python tests/audit_v1_3/m01_linear/test_properties.py

# Minimal reproductions
python docs/audit/modular-revalidation-v1.3/M01-linear/evidence/minimal-reproductions/m01_lin_001_aweight_zero.py
python docs/audit/modular-revalidation-v1.3/M01-linear/evidence/minimal-reproductions/m01_lin_002_near_collinearity.py
python docs/audit/modular-revalidation-v1.3/M01-linear/evidence/minimal-reproductions/m01_lin_003_twoway_cluster_fstat.py
```

## 最终测试基线

```bash
pytest tests/ --ignore=tests/golden/ --ignore=tests/benchmarks/ -q
```

结果：**349 passed, 56 warnings in 62.44s**

审查资产未破坏既有非 golden 测试套件。

