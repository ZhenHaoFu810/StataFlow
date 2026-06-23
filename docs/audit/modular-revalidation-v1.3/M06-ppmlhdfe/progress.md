# M06 PPMLHDFE 模块独立审查 — 进度清单

审查基线：`dev` @ `2c7db1ca095e03d29c471e8d523fdaa943306174`

## 已完成

- [x] 阅读 `MASTER_AUDIT_BRIEF.md` 与 M06 任务计划
- [x] 阅读 `stataflow.PPMLHDFE`、`stataflow.compat.stata.ppmlhdfe`、`ResultSchema` 实现
- [x] 阅读现有 `tests/audit_v1_3/m06_ppmlhdfe/m06_audit_utils.py`
- [x] 设计并登记 8 个新 synthetic 双跑实验（S1–S8）
- [x] 设计并登记 2 个新真实数据双跑实验（R1–R2）
- [x] 设计并登记 3 个 metamorphic/property tests（P1–P3）
- [x] 实现 `tests/audit_v1_3/m06_ppmlhdfe/m06_dgp.py`（新 DGP，不重用旧 golden）
- [x] 实现 `tests/audit_v1_3/m06_ppmlhdfe/test_m06_synthetic.py`
- [x] 实现 `tests/audit_v1_3/m06_ppmlhdfe/test_m06_realdata.py`
- [x] 实现 `tests/audit_v1_3/m06_ppmlhdfe/test_m06_property.py`
- [x] 实现 `tests/audit_v1_3/m06_ppmlhdfe/repro_m06_ppmlhdfe_findings.py`
- [x] 完成所有 Stata 17 现场双跑并保存日志
- [x] 保存所有证据 JSON 到 `docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/`
- [x] 撰写 `findings.md`
- [x] 撰写 `summary.md`
- [x] 更新 `test-design-register.md` 执行结果
- [x] 运行全量非 golden 回归测试，确认未破坏既有测试

## 测试执行结果

### M06 专项测试

```text
pytest tests/audit_v1_3/m06_ppmlhdfe -v
13 collected
8 passed, 5 failed
```

失败项（均为已记录 finding，未修改产品代码）：

- `test_s5_separation_fe` — Python `separation=None` 在分离数据下发散
- `test_s6_cluster_singleton` — cluster-robust SE 残余 ~2e-6 差异
- `test_s7_weights_offset` — offset + weights 处理严重偏离 Stata
- `test_s8_eform_predict` — `predict.xb` 语义与 Stata 不一致
- `test_r1_ships_exposure` — exposure 处理严重偏离 Stata

### 全量非 golden 回归

```text
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/benchmarks/
378 passed, 5 failed (all M06 audit failures)
```

未引入既有测试回归。

## 证据目录结构

```text
docs/audit/modular-revalidation-v1.3/M06-ppmlhdfe/evidence/
├── synthetic/
│   ├── S1_SMALL_PANEL_OLS_ROBUST/
│   ├── S2_TWO_WAY_FE_ROBUST/
│   ├── S3_MISSING_SAMPLE_SCREENING/
│   ├── S4_COLLINEAR_WITHIN_FE/
│   ├── S5_SEPARATION_FE_DEFAULT/
│   ├── S5_SEPARATION_FE_NONE/
│   ├── S6_CLUSTER_SINGLETON/
│   ├── S7_WEIGHTS_OFFSET/
│   ├── S8_EFORM_PREDICT_RAW/
│   ├── S8_EFORM_PREDICT_EFORM/
│   └── S8_EFORM_PREDICT_PREDICT/
├── real-data/
│   ├── R1_SHIPS_EXPOSURE/
│   └── R2_MEDPAR_PROVIDER_CLUSTER/
├── property/
│   ├── P1_ROW_ORDER_INVARIANCE_ORIG/
│   ├── P1_ROW_ORDER_INVARIANCE_SHUF/
│   ├── P2_IRRELEVANT_COLUMN_ORIG/
│   ├── P2_IRRELEVANT_COLUMN_NOISE/
│   ├── P3_SCALE_TRANSFORMATION_ORIG/
│   └── P3_SCALE_TRANSFORMATION_SCALED/
└── minimal-reproductions/
    ├── A_WeightSyntaxRejected.json
    ├── B_SeparationSampleDifference.json
    ├── C_RobustSEResidual.json
    └── D_DfResidSemantic.json
```

## 未开始 / 未验证

- [ ] 2-way cluster VCE 独立验证
- [ ] Stata `ppmlhdfe ..., eform` 输出直接比对
- [ ] IRLS 收敛失败边界行为测试
- [ ] MAP vs LSDV 路径一致性测试
