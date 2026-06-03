# Wave 9 Round 3: Golden Dual-Run Validation for DID Hardening

## 背景

Wave 9 Round 2 已完成 did_imputation controls/pretrends/options 和 csdid dr/aggtype 的实现，全部 synthetic 单元测试通过（251 passed, 0 failed）。但 Wave 9 的出口标准明确要求 golden dual-run 证据（Stata-Python 字段级对齐），目前尚未创建任何针对 Round 2 新功能的 golden 测试。

## 目标

创建 5–6 个 golden dual-run 测试文件，使 Wave 9 新增功能全部具备 Stata 17 字段级对齐证据，满足 Wave 9 出口标准。

## 为什么现在做

1. **出口标准未达成**：`docs/backlog.md` Wave 9 出口标准 3 项均未勾选。
2. ** correctness-first 原则**：synthetic 单元测试只验证内部一致性，不验证 Stata 对齐。没有 golden 双跑，无法声称功能正确。
3. **Wave 10 阻塞**：IV Completion 的入口标准虽只要求 Wave 7 完成，但项目节奏要求 wave 顺序完成。Wave 9 未完成前不应启动 Wave 10。

## 允许修改范围

- `tests/golden/test_w9_*.py`：新建 golden 双跑测试文件（5–6 个）
- `stata/cases/` 和 `stata/output/`：Stata 执行生成的 `.do` / `.log` / `.dta` 文件
- `docs/testing/test-case-catalog.md`：更新样例状态
- `docs/backlog.md`：勾选 Wave 9 出口标准

## 禁止动作

- 禁止修改 `src/stataflow/estimators/did_imputation.py` 或 `csdid.py`（除非发现实现 bug，需先记录再修复）
- 禁止修改 `ResultSchema`
- 禁止修改其他命令族的代码或测试
- 禁止跳过 Stata 双跑步骤，仅用 synthetic 单元测试替代
- 禁止放宽容差标准超过规定上限（DR SE 最多 5e-3，其余 1e-3）

## 执行顺序

```
Step 1: test_w9_di_controls_basic.py
  └── Step 2: test_w9_di_pretrends_basic.py
       └── Step 3: test_w9_di_controls_pretrends_combo.py
            └── Step 4: test_w9_csdid_dr_basic.py
                 └── Step 5: test_w9_csdid_dr_real_ezunem.py
                      └── Step 6: test_w9_di_real_ezunem_controls.py（可选）
```

每步必须：生成数据 → 写 Stata `.do` → 执行 Stata → 解析 log → 写 Python 测试 → 运行通过 → 再下一步。

## 最小验证要求

### Step 1: did_imputation controls synthetic
- Stata 命令：`did_imputation y id year first_treat, controls(x1 x2) cluster(id) allhorizons autosample`
- Python 调用：`DIDImputation(...).fit(cluster="id", allhorizons=True, autosample=True, controls=["x1","x2"])`
- 验证字段：nobs, coefficients (beta), std_err
- 容差：beta <1e-5, SE <1e-3

### Step 2: did_imputation pretrends synthetic
- Stata 命令：`did_imputation y id year first_treat, pretrends(3) cluster(id) allhorizons autosample`
- Python 调用：`DIDImputation(...).fit(cluster="id", allhorizons=True, autosample=True, pretrends=3)`
- 验证字段：nobs, tau coefficients, pre1/pre2/pre3 coefficients, pre_F, pre_p
- 容差：beta <1e-5, SE <1e-3, pre_F <1e-3

### Step 3: did_imputation controls + pretrends combo synthetic
- Stata 命令：`did_imputation y id year first_treat, controls(x1) pretrends(3) cluster(id) allhorizons autosample`
- Python 调用：`DIDImputation(...).fit(..., controls=["x1"], pretrends=3)`
- 验证字段：同上，同时验证 controls 和 pretrends 系数共存
- 容差：同上

### Step 4: csdid drimp synthetic
- Stata 命令：`csdid y x1 x2, ivar(id) time(year) gvar(first_treat) method(drimp)` + `csdid_estat event`
- Python 调用：`CSDID(...).fit(method="drimp", xvars=["x1","x2"]).estat_event()`
- 验证字段：nobs, event-study coefficients (pre_avg, post_avg, tm*, tp*), SE
- 容差：beta <1e-5, SE <5e-3（DR 方法允许更宽松）

### Step 5: csdid drimp real-data (ezunem)
- Stata 命令：`csdid uclms pop, ivar(city) time(year) gvar(first_treat) method(drimp)` + `csdid_estat event`
- Python 调用：`CSDID(data=ezunem, y="uclms", id="city", time="year", first_treat="first_treat").fit(method="drimp", xvars=["pop"]).estat_event()`
- 验证字段：同上
- 容差：beta <1e-5, SE <5e-3

### Step 6: did_imputation controls real-data (ezunem)（可选）
- Stata 命令：`did_imputation uclms city year first_treat, controls(pop) cluster(city) allhorizons autosample`
- Python 调用：`DIDImputation(data=ezunem, ...).fit(..., controls=["pop"])`
- 验证字段：nobs, coefficients, SE
- 容差：beta <1e-5, SE <1e-3

## 交付物

1. `tests/golden/test_w9_di_controls_basic.py`
2. `tests/golden/test_w9_di_pretrends_basic.py`
3. `tests/golden/test_w9_di_controls_pretrends_combo.py`
4. `tests/golden/test_w9_csdid_dr_basic.py`
5. `tests/golden/test_w9_csdid_dr_real_ezunem.py`
6. `tests/golden/test_w9_di_real_ezunem_controls.py`（可选）
7. 对应的 `stata/cases/` 和 `stata/output/` 文件
8. 更新后的 `docs/testing/test-case-catalog.md`
9. 更新后的 `docs/backlog.md`
10. `workspace/current-task/REPORT.md`（完成报告）

## 成功标准

- [ ] 全部 5–6 个 golden 测试 `pytest` 通过
- [ ] 主仓非 golden 测试继续通过：`pytest tests/ --ignore=tests/golden/ -q` → 251 passed, 0 failed
- [ ] 既有 golden 测试无回归
- [ ] `docs/testing/test-case-catalog.md` 中 Wave 9 样例状态更新为 `done`
- [ ] `docs/backlog.md` Wave 9 出口标准全部勾选
- [ ] `workspace/current-task/REPORT.md` 已更新为完成报告

## 升级条件

以下情况必须停止并 escalate 到 Codex：
- 任何字段出现不可解释的 Stata-Python 偏差（>5% 对于 DR，>1% 对于其他）
- 需要修改 `ResultSchema` 才能通过测试
- 真实数据与 synthetic 数据的对齐结论冲突
- 发现 Round 2 实现存在需要公共 API 变更的 bug
