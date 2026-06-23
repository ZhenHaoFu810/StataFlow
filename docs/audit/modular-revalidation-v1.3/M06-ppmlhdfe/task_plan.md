# M06 PPMLHDFE 模块独立审查计划

## 审查基线

- 项目根目录：`D:/OneDrive - SAIF/PhD3/StataFlow`
- 基线分支：`dev`
- 基线 commit：`2c7db1ca095e03d29c471e8d523fdaa943306174`
- Python 3.11.7，NumPy 1.26.4，pandas 3.0.2，SciPy 1.17.1，statsmodels 0.14.6
- Stata 17 MP：`D:\Software\Stata17\StataMP-64.exe`
- 审查遵循：`docs/audit/modular-revalidation-v1.3/MASTER_AUDIT_BRIEF.md`
- 本轮禁止修改 `src/stataflow/` 产品代码

## 审查对象

- 核心估计器：`stataflow.PPMLHDFE`
- Stata 兼容层：`stataflow.compat.stata.ppmlhdfe`
- 复用的共享基础设施：`AbsorbingOLS._prepare_data`、`_vce_utils` 中 cluster/PSD 函数、`factor_variables`、`ResultSchema`
- Postestimation：`PPMLHDFE.predict`（xb/mu/residuals/pearson/deviance/working）与 `PPMLHDFE.margins`

## 关键风险领域

1. **IRLS 收敛与初始值**：起始猜测、步长折半、收敛阈值是否导致 Stata/Python 路径差异。
2. **分离检测（separation）**：Python `separation=None` 与 Stata 默认 `separation(fe)` 的样本差异。
3. **高维 FE / singleton drop**：与 Stata `ppmlhdfe` 复用同一 `reghdfe` 内核的 singleton 删除规则是否一致。
4. **VCE 与自由度**：`robust`/`cluster`/`ols` VCE、小样本修正、cluster VCE 下 `df_resid` 语义（Python 用 `G-1`，Stata GLM 不定义 `e(df_r)`）。
5. **权重与 offset/exposure**：`aweight` 映射、`exposure` 取对数、offset 加入线性预测器后的常数项恢复。
6. **结果字段**：`ll`、`deviance`、`pseudo_r2`、`df_a`、`df_model`、`df_resid`、`cluster_count`、`sample_mask`。
7. **eform 与 predict**：eform beta/SE/z/p 的语义；predict 各类型与 Stata `predict` 输出。

## 审查任务清单

- [ ] 支持边界核对与代码走查
- [ ] 设计并登记 8 个新 synthetic 双跑实验
- [ ] 设计并登记 2 个新真实数据双跑实验
- [ ] 设计并登记 3 个 metamorphic/property tests
- [ ] 实现通用执行与日志解析工具 `tests/audit_v1_3/m06_ppmlhdfe/m06_audit_utils.py`
- [ ] 实现 synthetic 测试 `test_m06_synthetic.py`
- [ ] 实现真实数据测试 `test_m06_realdata.py`
- [ ] 实现 property 测试 `test_m06_property.py`
- [ ] 构造最小复现脚本 `repro_m06_ppmlhdfe_findings.py`
- [ ] 字段级比较并记录差异
- [ ] 撰写 `findings.md`、`progress.md`、`summary.md`、`test-design-register.md`
- [ ] 运行现有非 golden 测试，确认审查资产未破坏仓库

## 预期交付物

```text
docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/
  task_plan.md
  test-design-register.md
  findings.md
  progress.md
  summary.md
  evidence/
    synthetic/
    real-data/
    property/
    minimal-reproductions/

tests/audit_v1_3/m06_ppmlhdfe/
  m06_audit_utils.py
  test_m06_synthetic.py
  test_m06_realdata.py
  test_m06_property.py
  repro_m06_ppmlhdfe_findings.py

stata/cases/audit_v1_3_m06/
  *.do
  *.csv

stata/output/audit_v1_3_m06/
  *.log
  *_diff.json
```

## 时间规划

1. 计划与工具实现（本 turn）
2. Synthetic 双跑实验实现与执行
3. 真实数据实验与 property tests
4. 差异分析、最小复现与文档撰写
5. 测试基线验证与收尾
