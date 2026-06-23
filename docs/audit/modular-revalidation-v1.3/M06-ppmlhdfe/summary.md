# M06 PPMLHDFE 模块独立审查总结

**审查模块**: M06 PPMLHDFE  
**审查基线**: `dev` @ `2c7db1ca095e03d29c471e8d523fdaa943306174`  
**审查日期**: 2026-06-13  
**Stata 环境**: Stata 17 MP (`D:\Software\Stata17\StataMP-64.exe`)，ppmlhdfe 2.3.3

---

## 1. 目标与范围

本次审查仅针对 `stataflow.PPMLHDFE` 与 `stataflow.compat.stata.ppmlhdfe`，未修改 `src/stataflow/` 任何产品代码。全部测试、证据与文档均为本轮新建，DGP、随机种子、Stata `.do` 脚本均未复用旧 golden 资产。

---

## 2. 执行结果概览

### 2.1 M06 专项测试

```text
pytest tests/audit_v1_3/m06_ppmlhdfe -v
13 collected / 8 passed / 5 failed
```

| 测试 | 结果 | 说明 |
|---|---|---|
| S1 小样本 robust | PASS | 系数、SE、VCE、ll、deviance 全部字段级一致 |
| S2 双向 FE robust | PASS | 使用 `separation(none)` 后一致 |
| S3 缺失值筛选 | PASS | nobs、sample_mask、df_a、系数一致 |
| S4 FE 内共线性 | PASS | 系数/SE 一致；VCE 因 omitted 变量未全矩阵比对 |
| S5 分离检测 | FAIL | Python `separation=None` 发散；`separation="fe"` 与 Stata 默认一致 |
| S6 cluster + singleton | FAIL | 点估计一致，cluster SE 残余 ~2e-6 差异 |
| S7 weights + offset | FAIL | offset/weights 处理严重偏离 Stata |
| S8 eform + predict | FAIL | raw 系数/eform 一致；predict `xb` 语义与 Stata 不一致 |
| R1 ships exposure | FAIL | exposure 处理严重偏离 Stata |
| R2 medpar provider cluster | PASS | 高维 FE + cluster 字段级一致 |
| P1 行顺序不变性 | PASS | Python/Stata 均满足 |
| P2 无关列不变性 | PASS | Python/Stata 均满足 |
| P3 x 尺度变换 | PASS | Python/Stata 均满足 |

### 2.2 全量非 golden 回归

```text
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/benchmarks/
378 passed, 5 failed (all M06 audit failures)
```

无既有测试回归。

---

## 3. 关键确认发现

1. **M06-PPMLHDFE-001（P2）**: Stata `ppmlhdfe` 仅接受 `pweight`，`aweight`/`iweight` 返回 `r(101)`。wrapper 的 `aweight` 参数无法直接映射到 Stata。
2. **M06-PPMLHDFE-002（P0）**: Python `separation=None` 不处理分离；在存在 y=0 FE 组时 IRLS 发散且无明确警告。`separation="fe"` 可与 Stata 默认基本对齐。
3. **M06-PPMLHDFE-003（P0）**: `offset`/`exposure` 实现存在根因错误，常数项恢复时多减了 offset 加权平均，导致系数、SE、ll、deviance 全面偏离 Stata。
4. **M06-PPMLHDFE-004（P1）**: `predict(type="xb")` 返回包含 FE 的线性预测器，而 Stata `predict, xb` 不包含 FE；导致 residuals/pearson/deviance 统计量不一致。
5. **M06-PPMLHDFE-005（P2）**: cluster VCE 下 SE 有 ~2e-6 残余差异；`df_resid` 语义不同（Stata GLM 不报告 `e(df_r)`，Python 使用 `G-1`）。
6. **M06-PPMLHDFE-006（P2）**: Stata `e(V)` 在 omitted 变量位置保留 0 行/列，与 Python 直接剔除不一致。
7. **M06-PPMLHDFE-007（P2）**: Stata 将嵌套在 cluster 变量中的 FE 视为冗余（不计入 `df_a`），Python 未做该修正。

---

## 4. 残余数值差异

- 无 offset/weights/separation 的干净设计（S1–S3、P1–P3、R2）可达到 1e-6 以内字段级一致。
- cluster SE 在 S6 出现 ~2e-6 相对差异，超出默认容差但量级很小。
- predict 类型（除 `mu` 均值外）均因 `xb` 语义差异而存在 1e-3 ~ 1e-1 级别差异。

---

## 5. 未覆盖区域

- 2-way cluster VCE 未独立验证。
- Stata `ppmlhdfe ..., eform` 输出未直接比对（本次用 raw 系数 delta-method 间接验证）。
- IRLS 达到 `max_iter` 时的失败行为未系统测试。
- MAP/LSDV 不同求解路径在 ppmlhdfe 中的等价性未测试。

---

## 6. 建议后续工作

1. 修复 `offset`/`exposure` 的常数项恢复逻辑（P0）。
2. 实现与 Stata 一致的默认分离检测，并对未收敛/分离场景给出明确错误/警告（P0）。
3. 统一 `predict` 语义：提供不含 FE 的 `xb`（与 Stata 对齐）并检查 residuals/pearson/deviance（P1）。
4. 明确文档化 `aweight` 与 `pweight` 的兼容性差异（P2）。
5. 研究 cluster SE 残余差异根因，决定是否需要调整 meat 计算（P2）。
6. 增加 2-way cluster 与直接 `eform` 输出比对的独立证据。
