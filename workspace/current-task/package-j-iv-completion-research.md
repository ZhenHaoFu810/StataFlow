# Wave 10 — IV Completion: Round 1 Research

## 背景

Wave 7（HDFE Hardening）、Wave 8（RD Completion）、Wave 9（DID Hardening）已全部完成并通过 golden dual-run 验证。当前 `ivreghdfe` 实现为 2SLS + FE + robust/cluster VCE + first-stage diagnostics 子集，缺失 GMM2S、LIML、k-class、弱工具变量检验等核心 IV 生态功能。

Wave 10 目标是将 `ivreghdfe` 从 2SLS 子集推进到完整 IV 生态（GMM/LIML/weakiv）。Round 1 为纯研究包：阅读源码、锁定公式、设计样例，不修改实现代码。

## 目标

完成 `ivreghdfe` GMM/LIML/weakiv 分支的源码阅读与研究档案建立，明确 Python 实现路径，设计 synthetic 与 real-data 样例，为 Round 2（Min Implementation）提供可执行边界。

## 为什么现在

- Wave 7-9 全部完成，无阻塞返工包。917 测试全部通过。
- `ivreghdfe` 是 IV 命令族的核心，GMM/LIML 是应用微观计量高频请求。
- GMM/LIML 估计器内核与现有 2SLS 路径独立，不影响已有功能稳定性。
- 研究先行可降低 Round 2 实现风险（`ivreg2` Mata 源码复杂，需提前锁定公式）。

## 允许修改范围

- `docs/research/ivreghdfe.md`：追加 GMM/LIML/weakiv 研究收束章节。
- `docs/research/ivreghdfe-gmm.md`（新建）：GMM2S / CUE / LIML 算法详解。
- `docs/research/ivreghdfe-weakiv.md`（新建）：弱工具变量检验公式与 Stock-Yogo 临界值。
- `docs/testing/test-case-catalog.md`：预登记 Wave 10 synthetic 与 real-data 样例。
- `workspace/current-task/REPORT.md`：记录研究结论与 Round 2 建议边界。

## 禁止动作

- 禁止修改 `src/stataflow/estimators/iv.py` 或任何实现代码。
- 禁止修改 `ResultSchema` 或公共 API。
- 禁止修改其他命令族（reghdfe、ppmlhdfe、rdrobust、did_imputation、csdid 等）。
- 禁止跳过源码阅读直接写实现代码。
- 禁止未在 `test-case-catalog.md` 预登记就设计样例。

## 执行顺序（强制）

```
Step 1: 阅读 ivreghdfe.ado 中 GMM/LIML/weakiv 分支
  └── Step 2: 阅读 ivreg2 Mata 源码中 GMM2S、CUE、LIML 实现
       └── Step 3: 研究弱工具变量检验（Kleibergen-Paap rk Wald F、Stock-Yogo）
            └── Step 4: 设计 synthetic 样例与 real-data 样例
                 └── Step 5: 撰写研究档案与 test-case-catalog 预登记
                      └── Step 6: 更新 REPORT.md
```

## 每步交付要求

### Step 1: ivreghdfe.ado GMM/LIML/weakiv 分支

**目标：** 定位 `ivreghdfe.ado` 中处理 `gmm2s`、`gmm`、`cue`、`liml`、`kclass`、`fuller`、`weakiv` 的代码分支，记录：
- 这些选项如何被解析并传递给 `ivreg2` Mata 库。
- `ivreghdfe` 本身是否对 GMM/LIML 做额外处理（如 FE 吸收后的自由度修正）。
- `weakiv` 输出是否由 `ivreg2` 直接生成，还是 `ivreghdfe` 额外包装。

**验证：** 在 `docs/research/ivreghdfe.md` 中追加 "Wave 10 研究收束：GMM/LIML/weakiv 分支定位" 章节，列出关键行号与函数名。

### Step 2: ivreg2 Mata 源码阅读

**目标：** 阅读 `research/vendor/stata_community/ivreghdfe/` 或 `ivreg2/` 中 Mata 源码：
- GMM2S 两阶段估计：权重矩阵构造、迭代、收敛条件。
- CUE（Continuously Updated GMM）：目标函数、数值优化。
- LIML / k-class：特征值问题、Fuller 修正。
- 与 2SLS 的差异点：VCE 计算、小样本修正、过度识别检验。

**验证：** 在 `docs/research/ivreghdfe-gmm.md` 中记录：
- GMM2S 权重矩阵公式（初始权重、最优权重）。
- LIML 估计量的特征值表达式。
- k-class 估计量与 2SLS/LIML 的关系。
- CUE 与 GMM2S 的数值等价条件。

### Step 3: 弱工具变量检验研究

**目标：** 研究 Kleibergen-Paap rk Wald F 统计量、Stock-Yogo 临界值表：
- Kleibergen-Paap F 的公式（与 Cragg-Donald F 的差异）。
- Stock-Yogo 临界值的查表/插值方法。
- `weakiv` 在 `ivreg2` 中的实现路径。

**验证：** 在 `docs/research/ivreghdfe-weakiv.md` 中记录公式、自由度规则、与 Stata 输出字段的映射。

### Step 4: Synthetic 样例设计

**目标：** 为 Round 2 设计至少 3 个 synthetic 样例：

1. **GMM2S 过度识别**
   - 数据集：手工 panel，1 内生变量 + 2 工具变量 + 1 外生变量。
   - Stata：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) gmm2s`
   - Python：`ivreghdfe(..., estimator="gmm2s")`
   - 风险焦点：GMM2S 与 2SLS 在恰好识别时的等价性；过度识别时权重矩阵差异。

2. **LIML 弱工具**
   - 数据集：手工 panel，弱工具变量设定（低第一阶段 F）。
   - Stata：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) liml`
   - Python：`ivreghdfe(..., estimator="liml")`
   - 风险焦点：LIML 与 2SLS 的系数差异、偏差方向。

3. **weakiv 检验**
   - 数据集：同上弱工具设定。
   - Stata：`ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) weakiv`
   - Python：`ivreghdfe(..., weakiv=True)`
   - 风险焦点：Kleibergen-Paap F 字段级对齐、Stock-Yogo 临界值一致。

### Step 5: Real-data 样例设计

**目标：** 为 Round 3 设计至少 1 个 real-data 样例：

- **Card 教育回报数据**
  - 数据集：`research/data/public/iv/card.dta`
  - Stata：`ivreghdfe lwage exper expersq (educ = nearc4), absorb(south) gmm2s`
  - Python：`ivreghdfe(..., estimator="gmm2s")`
  - 风险焦点：真实数据下 GMM2S 系数/SE 与 Stata 对齐。

### Step 6: test-case-catalog 预登记

在 `docs/testing/test-case-catalog.md` 中新增 "Wave 10 预登记样例（IV Completion）" 章节，登记上述样例，状态设为 `planned`。

## 最小验证要求

- [ ] `docs/research/ivreghdfe.md` 已追加 Wave 10 研究收束章节，含源码行号定位。
- [ ] `docs/research/ivreghdfe-gmm.md` 已创建，含 GMM2S/CUE/LIML/k-class 公式。
- [ ] `docs/research/ivreghdfe-weakiv.md` 已创建，含 Kleibergen-Paap F 与 Stock-Yogo 公式。
- [ ] `docs/testing/test-case-catalog.md` 已登记至少 3 个 synthetic + 1 个 real-data 样例。
- [ ] `workspace/current-task/REPORT.md` 已更新为 Wave 10 Round 1 研究结论报告。

## 成功标准

- [ ] `ivreghdfe.ado` 中 GMM/LIML/weakiv 分支的代码路径已完全定位并记录。
- [ ] `ivreg2` Mata 中 GMM2S、CUE、LIML 的核心算法已阅读并公式化。
- [ ] 弱工具变量检验的公式与 Stata 实现差异已明确。
- [ ] Synthetic 样例设计覆盖 GMM2S、LIML、weakiv 三个核心场景。
- [ ] Real-data 样例已选定（Card 数据或等效公开数据集）。
- [ ] 全部研究档案已写入 `docs/research/`。
- [ ] `test-case-catalog.md` 已预登记。

## 交付物

1. `docs/research/ivreghdfe.md`（追加 Wave 10 章节）
2. `docs/research/ivreghdfe-gmm.md`（新建）
3. `docs/research/ivreghdfe-weakiv.md`（新建）
4. `docs/testing/test-case-catalog.md`（追加 Wave 10 预登记）
5. `workspace/current-task/REPORT.md`（Wave 10 Round 1 研究结论报告）

## 入口条件

- Wave 7、Wave 8、Wave 9 全部完成。
- `ivreghdfe` 2SLS 子集稳定（已有 golden dual-run 证据）。
- `research/vendor/stata_community/ivreghdfe/` 本地源码镜像存在。

## 出口条件

- 全部研究档案完成并通过自检（公式可推导、源码路径可复现）。
- `test-case-catalog.md` 预登记完成。
- `REPORT.md` 已更新。

## 风险记录

| 风险 | 说明 | 缓解 |
|------|------|------|
| `ivreg2` Mata 源码复杂度高 | GMM/CUE/LIML 共用大量内部函数，阅读耗时 | 聚焦与 Stata 输出直接相关的顶层函数，不深究所有数值优化细节 |
| GMM2S 权重矩阵与 Stata 差异 | 初始权重、迭代收敛条件可能不同 | 记录 Stata 默认行为（如 `wmatrix(robust)`），在 Round 2 中逐字段对比 |
| LIML 特征值计算数值稳定性 | 不同线性代数库特征值结果可能有微小差异 | 在 Round 2 中设定合理容忍度（如 rtol=1e-5） |
| weakiv 临界值表版权 | Stock-Yogo 表为学术发表内容，直接嵌入可能涉及版权 | 使用公开文献中的插值公式，或运行时从已知表插值 |
