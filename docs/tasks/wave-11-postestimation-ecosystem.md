# Wave 11: Postestimation & `estat` Ecosystem

## 背景

Wave 7–10 已全部完成并通过 correctness-gatekeeper 审核。当前 `predict` 已覆盖 OLS/FE/Logit/Probit/Poisson 的高频类型（`xb`, `pr`, `residuals`），`margins` 已覆盖 `dydx` 与 `atmeans`。但以下 postestimation 能力仍缺失，阻塞了从 Beta 到稳定发布的过渡：

1. `reghdfe` / `ivreghdfe` 的 `stdp`（预测值标准误）—— 需要完整的 VCE 矩阵传播
2. `ppmlhdfe` 的 `pearson` / `deviance` / `working` 残差 —— GLM 族特有
3. `estat summarize` —— Stata 用户高频使用的后估计汇总统计
4. `estat vce` / `estat ic` —— 方差矩阵与信息准则查看

## 目标

建立完整的 postestimation 层，使所有已稳定命令族具备与 Stata 对齐的 `predict` 扩展和 `estat` 生态。

## 为什么现在做

- Wave 7–10 全部完成，无阻塞返工包，估计器内核已稳定
- Postestimation 依赖估计结果稳定，必须在核心估计完成后实施
- `stdp` 等需要 VCE 框架成熟，当前多向聚类（Wave 7）和 IV VCE（Wave 10）已稳定
- v0.3.x 发布门槛要求 postestimation 生态完整（见 `docs/roadmap.md`）

## 允许修改范围

- `src/stataflow/estimators/absorbing_ols.py` — 新增 `predict(type="stdp")`
- `src/stataflow/estimators/iv.py` — 新增 `predict(type="stdp")`（复用吸收层 VCE）
- `src/stataflow/estimators/ppmlhdfe.py` — 新增 `predict(type="pearson"/"deviance"/"working")`
- `src/stataflow/results/result.py` — 仅允许新增辅助方法（如 `vce()` 访问器），不允许修改字段结构；若需公共结构变更须走 ADR
- `src/stataflow/compat/stata/*.py` — 透传新 predict 类型参数
- `src/stataflow/postestimation/` — 可新建目录存放 `estat_summarize`, `estat_vce`, `estat_ic`
- `tests/golden/test_w11_*.py` — 新建 golden 双跑测试
- `docs/command-support-matrix/*.md` — 更新 predict / estat 支持状态
- `docs/testing/test-case-catalog.md` — 登记新增样例
- `workspace/current-task/REPORT.md`

## 禁止行为

- 不允许修改 `ResultSchema` 顶层字段结构（如新增 `postestimation` 子对象）
- 不允许引入新的估计器内核或修改现有估计逻辑
- 不允许把 `margins` 扩展到 IV/GLM 的复杂交互（当前基础 `dydx`/`atmeans` 已足够）
- 不允许跳过 synthetic 双跑直接做真实数据
- 不允许把 `test`/`lincom`/`nlcom` 的完整实现纳入本轮（仅允许研究归档和最小原型）
- 不允许修改 `docs/project-charter.md`

## 执行顺序（强制）

```
Step 1: 研究轮 — 阅读 reghdfe_p.ado / ppmlhdfe predict 源码 / Stata estat 手册
  └── Step 2: 设计 synthetic 样例与 real-data 样例，登记到 test-case-catalog.md
       └── Step 3: 实现 predict stdp（reghdfe / ivreghdfe）
            └── Step 4: 实现 predict pearson / deviance / working（ppmlhdfe）
                 └── Step 5: 实现 estat_summarize / estat_vce / estat_ic
                      └── Step 6: 编写 synthetic golden 测试
                           └── Step 7: 编写 real-data golden 测试
                                └── Step 8: 运行 Stata 双跑，验证对齐
                                     └── Step 9: 更新 command-support-matrix 与 backlog
                                          └── Step 10: 更新 REPORT.md
```

## 最小验证要求

| 验证项 | 命令 | 容忍度 | 测试文件 |
|--------|------|--------|----------|
| `stdp` 同方差 | `reghdfe` / `ivreghdfe` | < 1e-6 | `test_w11_reghdfe_stdp_ols.py` |
| `stdp` robust | `reghdfe` / `ivreghdfe` | < 1e-6 | `test_w11_reghdfe_stdp_robust.py` |
| `stdp` cluster | `reghdfe` / `ivreghdfe` | < 1e-6 | `test_w11_reghdfe_stdp_cluster.py` |
| `pearson` residual | `ppmlhdfe` | < 1e-6 | `test_w11_ppmlhdfe_pearson.py` |
| `deviance` residual | `ppmlhdfe` | < 1e-6 | `test_w11_ppmlhdfe_deviance.py` |
| `working` residual | `ppmlhdfe` | < 1e-6 | `test_w11_ppmlhdfe_working.py` |
| `estat summarize` 字段 | 所有命令 | 字段级一致 | `test_w11_estat_summarize.py` |
| `estat ic` AIC/BIC | GLM 族 | < 1e-4 | `test_w11_estat_ic.py` |
| 回归测试 | 全部 | 0 失败 | 现有 950+ 测试 |

## 交付物

1. `src/stataflow/estimators/absorbing_ols.py` — `predict(type="stdp")`
2. `src/stataflow/estimators/iv.py` — `predict(type="stdp")`
3. `src/stataflow/estimators/ppmlhdfe.py` — `predict(type="pearson"/"deviance"/"working")`
4. `src/stataflow/postestimation/estat.py` — `estat_summarize()`, `estat_vce()`, `estat_ic()`
5. `tests/golden/test_w11_*.py` — 至少 8 个 synthetic + 2 个 real-data golden 测试
6. 更新后的 `docs/command-support-matrix/reghdfe.md`, `ivreghdfe.md`, `ppmlhdfe.md`
7. 更新后的 `docs/testing/test-case-catalog.md`
8. `workspace/current-task/REPORT.md`

## 成功标准

- [ ] `stdp` 在 OLS/robust/cluster 三种 VCE 下与 Stata `predict, stdp` 字段级一致（< 1e-6）
- [ ] `pearson` / `deviance` / `working` 与 Stata `predict, pearson/deviance/working` 字段级一致（< 1e-6）
- [ ] `estat_summarize()` 输出与 Stata `estat summarize` 的变量均值/标准差/最小值/最大值字段级一致
- [ ] `estat_ic()` 的 AIC/BIC 与 Stata `estat ic` 字段级一致（GLM 族）
- [ ] 全部现有 950+ 测试无回归
- [ ] 命令支持矩阵已更新
- [ ] REPORT.md 已更新
- [ ] 研究档案已归档（`docs/research/postestimation.md` 或更新现有研究档案）
