# Wave 10 Round 1 Rework 2: IV Completion — Research Document Correction

## 背景

Wave 10 Round 1（纯研究包，阅读 `ivreghdfe` GMM/LIML/weakiv 源码并撰写研究档案）已被 correctness-gatekeeper **连续拒绝两次**。

- **第一次拒绝**：4 P1 correctness blockers + 3 P2 issues。执行代理完成第一轮修复后重新提交。
- **第二次拒绝**：gatekeeper 重新审阅后发现 **第一轮修复未完全消除 P1 错误**，部分文档仍保留错误公式，且新增发现 transpose error 和 misleading docstring。

本 rework 任务为 **第二轮修正**，目标是将 `docs/research/ivreghdfe-gmm.md`、`docs/research/ivreghdfe.md`、`docs/research/ivreghdfe-weakiv.md` 中的全部 P1 和 P2 问题彻底修正，确保研究档案的数学公式与 `ivreghdfe.ado` / `ivreg2` Mata 源码严格一致。

---

## 目标

修正以下研究文档中的全部 correctness 问题，使其数学公式、矩阵维度、源码注释与 Stata `ivreghdfe.ado` Mata 源码完全一致。

---

## 为什么现在做

- Wave 10 Round 2（Min Implementation）依赖 Round 1 研究档案作为唯一实现依据。
- 若研究档案中的 LIML W/W1 矩阵定义、VCE 公式、ranktest 等价性声明存在错误，Round 2 的实现代码将直接继承这些错误，导致后续 golden dual-run 无法通过，返工成本远高于现在修正文档。
- correctness-gatekeeper 已连续两次拒绝，说明问题具有系统性，需要更严格的源码交叉验证。

---

## 允许修改范围

仅限以下三个研究文档中的**文字、公式、伪代码、注释**：

1. `docs/research/ivreghdfe-gmm.md`
2. `docs/research/ivreghdfe.md`（Wave 10 研究收束章节）
3. `docs/research/ivreghdfe-weakiv.md`

允许在文档中新增“修正记录”或“与源码对照”小节，以证明已交叉验证。

---

## 禁止行为

- **禁止修改任何 Python 实现代码**（`src/stataflow/estimators/iv.py` 等）
- **禁止修改 `ResultSchema` 或公共 API**
- **禁止修改测试文件**
- **禁止修改其他命令族文档**
- **禁止以“近似等价”“文献惯例”为由保留错误公式**——必须与 `ivreghdfe.ado` Mata 源码逐行对照
- **禁止在未重新阅读 `ivreghdfe.ado` 对应 Mata 函数的情况下凭记忆修改**

---

## Gatekeeper 发现清单（必须全部解决）

### P1 Correctness Blockers（4 项）

#### P1-1: LIML W 和 W1 矩阵定义错误

**问题描述**：`ivreghdfe-gmm.md` 第 2.1 节和 `ivreghdfe.md` Wave 10 第 3.1 节将 W 定义为投影矩阵 `W = Y'Z(Z'Z)^-1Z'Y`，但 Stata `s_liml` 实际使用的是**残差矩阵**（annihilator / residual-form）：

```
W = Y' M_Z Y   where M_Z = I - Z(Z'Z)^-1Z'
W1 = Y' M_Z2 Y  where M_Z2 = I - Z2(Z2'Z2)^-1Z2'
```

**影响**：lambda 计算基于 `W^(-1/2) * W1 * W^(-1/2)` 的特征值。若 W 使用投影矩阵而非残差矩阵，特征值问题的数学结构完全改变，lambda 值将错误。

**修复要求**：
1. 在 `ivreghdfe-gmm.md` 和 `ivreghdfe.md` 中，将 W/W1 的定义修正为残差矩阵形式。
2. 明确写出 `M_Z = I - Z(Z'Z)^-1Z'` 和 `M_Z2 = I - Z2(Z2'Z2)^-1Z2'`。
3. 同步修正 Python 伪代码（`fit_liml` 函数中 `W` 和 `W1` 的计算）。
4. 提供 `ivreghdfe.ado` 中 `s_liml` 对应源码行号作为证据。

---

#### P1-2: LIML VCE "等价矩阵形式" transpose error

**问题描述**：`ivreghdfe-gmm.md` 第 2.2 节在 `coviv` 为空的情况下写出：

```
V = 1/N * QXZ' * Qh^-1 * QZZ^-1 * omega * QZZ^-1 * Qh^-1 * QXZ
```

**维度分析**：
- `QXZ'` 是 L×K
- `Qh^-1` 是 K×K
- `QZZ^-1` 是 L×L
- `omega` 是 L×L
- 最终乘积为 L×L

但 V 应该是 K×K（回归量数 × 回归量数）。该式维度不匹配，原因是 transpose 顺序错误。

**修复要求**：
1. 重新从 `s_liml` Mata 源码推导正确的矩阵形式。
2. 确保最终 V 的维度为 K×K。
3. 在文档中显式标注每个中间矩阵的维度，作为自检。
4. 若源码中实际使用的是 `aux5 = solve(Qh, QXZ)` 和 `aux9 = solve(QZZ, aux5')` 的逐步计算形式，则优先保留逐步形式，将“等价矩阵形式”作为辅助说明，并确保其数学正确。

---

#### P1-3: `ivreghdfe-weakiv.md` 中 ranktest Wald 伪代码 docstring 误导

**问题描述**：`_ranktest_wald` 函数的 docstring 声称：

```
"""
计算 Kleibergen-Paap rk Wald 统计量。
等价于约简型中检验被排除 IV 联合显著性的 Wald 统计量。
"""
```

但下方实现是**对每个内生变量单独跑第一阶段回归，累加 Wald 统计量**。这不是 Kleibergen-Paap rk Wald 的精确实现：
- Kleibergen-Paap rk Wald 基于**多变量约简型**的协方差矩阵，使用分块矩阵公式同时处理所有内生变量。
- 单独累加各内生变量的 Wald 统计量仅在误差协方差矩阵对角化时近似成立，不是精确等价。

**修复要求**：
1. 修改 docstring，删除“等价于”的绝对化表述。
2. 改为准确描述：`"近似实现：对每个内生变量分别计算被排除 IV 的 Wald 统计量并累加。注意：这与 Kleibergen-Paap (2006) 基于多变量约简型的精确 rk Wald 统计量不同，在存在多个内生变量且误差相关时仅为近似。"`
3. 在文档正文中补充说明：精确实现需要构造多变量约简型的协方差矩阵并使用分块回归公式，或调用 `ranktest` 命令的 SVD 算法。

---

#### P1-4: `aux5 = solve(Qh, QXZ)` 维度注释需核实

**问题描述**：gatekeeper 指出 `aux5 = solve(Qh, QXZ)` 被注释为 `Qh^-1 * QXZ (K×L)`。若 Qh 为 K×K，QXZ 为 K×L，则 `solve(Qh, QXZ)` 结果确实是 K×L，维度正确。但需要确认 gatekeeper 的具体质疑点——是否在其他地方（如 `aux9` 或后续矩阵乘法）存在维度不匹配。

**修复要求**：
1. 重新检查 `s_liml` 中 VCE 计算的全部中间变量维度链：
   - `aux5 = solve(Qh, QXZ)` → K×L ?
   - `aux9 = solve(QZZ, aux5')` → L×K ?
   - `V = 1/N * aux9' * omega * aux9` → K×K ?
2. 在文档中显式写出每一步的维度注释。
3. 若发现任何一步维度不匹配，修正公式或注释。

---

### P2 Issues（3 项）

#### P2-1: GMM VCE 公式中 ambiguous notation

**问题描述**：`ivreghdfe-gmm.md` 第 1.3 节中 `V = 1/N * [X'Z · W · Z'X]^-1` 的 `X'Z` 维度在不同上下文中可能指 `K×L` 或 `L×K`，容易引起混淆。

**修复要求**：
1. 统一使用 `QXZ = X'Z / N`（K×L）和 `QZX = Z'X / N`（L×K）的符号体系。
2. 将 VCE 公式改写为基于 Q 矩阵的形式，消除歧义。

#### P2-2: `ivreghdfe.md` 中 LIML 公式速查的 W/W1 与 `ivreghdfe-gmm.md` 不一致

**问题描述**：`ivreghdfe.md` Wave 10 第 3.1 节和 `ivreghdfe-gmm.md` 第 2.1 节的 LIML W/W1 公式应完全一致，但需确认两者是否同步。

**修复要求**：
1. 修正后确保两个文件中的 LIML 公式逐字一致。
2. 若存在表述差异，统一为同一版本。

#### P2-3: `m_omega` 说明中缺少对 `vcvo` 结构的解释

**问题描述**：文档中多次出现 `m_omega(vcvo)`，但未解释 `vcvo` 对象包含哪些字段（如 `robust`、`cluster`、`clustvar`、`bw` 等），导致 Round 2 实现者需要回头阅读源码。

**修复要求**：
1. 在 `ivreghdfe-gmm.md` 第 3 节中补充 `vcvo` 结构说明（基于 `ivreghdfe.ado` 中的 `vcvo` 定义）。
2. 列出关键字段：`omega_type`（homoskedastic/robust/cluster/HAC）、`cluster_var`、`N_clust`、`bw`、`kernel`、`dofminus`、`sdofminus` 等。

---

## 执行顺序（强制）

```
Step 1: 重新打开 ivreghdfe.ado，定位 s_liml 函数（L5724 附近），逐行阅读 W/W1/VCE 计算
  └── Step 2: 修正 ivreghdfe-gmm.md 中 LIML 章节的 W/W1 定义、VCE 公式、Python 伪代码
       └── Step 3: 修正 ivreghdfe.md Wave 10 第 3.1 节 LIML 公式速查，确保与 ivreghdfe-gmm.md 一致
            └── Step 4: 修正 ivreghdfe-weakiv.md 中 ranktest Wald docstring 和等价性声明
                 └── Step 5: 补充 vcvo 结构说明，统一 GMM VCE 符号体系
                      └── Step 6: 全文自检：矩阵维度标注、公式一致性、源码行号引用
                           └── Step 7: 更新 REPORT.md，记录本轮修正内容
```

---

## 最小验证要求

1. **源码对照**：每修正一个公式，必须在文档中标注对应的 `ivreghdfe.ado` Mata 源码行号（如 `s_liml L57xx`）。
2. **维度自检**：每个矩阵表达式旁边必须标注维度（如 `QXZ (K×L)`、`Qh^-1 * QXZ (K×L)`）。
3. **文件间一致性**：`ivreghdfe.md` 和 `ivreghdfe-gmm.md` 中同一公式必须逐字一致。使用 diff 工具或手动比对确认。
4. **无代码修改验证**：运行 `git diff --name-only`，确保没有 `src/stataflow/` 或 `tests/` 下的文件被修改。
5. **回归测试**：`pytest tests/ --ignore=tests/golden/` 和 `pytest tests/golden/` 必须全部通过（本轮为文档修改，不应影响任何测试）。

---

## 交付物

1. `docs/research/ivreghdfe-gmm.md`（修正后）
2. `docs/research/ivreghdfe.md`（Wave 10 章节修正后）
3. `docs/research/ivreghdfe-weakiv.md`（修正后）
4. `workspace/current-task/REPORT.md`（追加 rework 修正记录）

---

## 成功标准

- [ ] P1-1：LIML W/W1 已修正为残差矩阵 `Y' M_Z Y` 形式，Python 伪代码同步修正，附源码行号
- [ ] P1-2：LIML VCE 矩阵形式维度正确（K×K），或删除错误“等价形式”仅保留逐步计算
- [ ] P1-3：ranktest Wald docstring 已删除绝对化“等价于”表述，改为准确近似说明
- [ ] P1-4：`aux5/aux9/V` 维度链已完整标注并验证无矛盾
- [ ] P2-1：GMM VCE 公式符号统一为 Q 矩阵体系，消除 `X'Z` 歧义
- [ ] P2-2：`ivreghdfe.md` 与 `ivreghdfe-gmm.md` 的 LIML 公式已逐字一致
- [ ] P2-3：`vcvo` 结构已在文档中说明
- [ ] 全部修改仅限于 `docs/research/` 和 `workspace/current-task/REPORT.md`
- [ ] 全部测试通过（917 passed, 0 failed）

---

## 升级规则

若在阅读 `s_liml` 源码时发现以下情况，立即停止并报告：
- W/W1 的定义与“残差矩阵”或“投影矩阵”均不完全匹配，存在第三种形式
- VCE 公式涉及尚未文档化的中间矩阵（如 `m_omega` 返回值的特殊缩放）
- `ranktest` 的精确算法无法通过现有 Python 线性代数库复现

这些情况需要 Codex 介入判断数学路径。
