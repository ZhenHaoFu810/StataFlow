# `ppmlhdfe` Separation 检测研究档案

## 命令定位

- 命令族：`Binary / Count`
- 类型：社区贡献命令核心难点
- 规则来源：公开源码优先
- 本地镜像：`research/vendor/stata_community/ppmlhdfe/`

---

## 1. 分离问题（Separation）定义

在泊松伪最大似然（PPML）中，若存在某组 FE 或某条线性组合使得所有 `y = 0`，则理论上对应 FE 的 `η → -∞`，导致部分系数无界。这在贸易引力模型中极为常见（如某些国家对在所有年份均无贸易往来）。

---

## 2. `separation(fe)` 方法原理

### 核心洞察

`ppmlhdfe` 的 `separation(fe)` 方法**复用现有 HDFE 的 singleton 消除机制**，而非构建独立检测器：

1. 创建 HDFE 对象时，将 `iweight` 设为 **因变量 `y`** 本身
2. 此时所有 `y = 0` 的观测权重为 0
3. 在加权 singleton 消除中，权重为 0 的 singleton 组会被自动剔除
4. 被剔除的观测即为存在分离问题的观测

### 为什么正确

- 泊松似然对 `y = 0` 的项为 `-exp(η)`，不发散
- 但若某 FE 组内**所有**观测 `y = 0`，则该组 FE 系数趋向 `-∞`
- 通过 `iweight = y` 使这些观测在加权框架中权重为 0，singleton 消除会将其识别为“无信息”并剔除
- 剩余数据不再存在该类型的分离

### 与其他方法的交互

`separation()` 选项可指定多个方法，按顺序执行：
- `separation(fe)` → 先剔除 `y=0` singleton
- `separation(relu)` → 对剩余数据做 ReLU 迭代边界检测
- `separation(simplex)` → 修改单纯形法检测

**Wave 7 最小实现策略**：仅实现 `separation(fe)`，因为它最简单且覆盖了最常见的分离场景（零贸易流）。

---

## 3. ReLU 方法（补充参考）

对非 singleton 分离：
1. 定义边界集 `u = (y == 0)`
2. 在非边界数据上求解 LS：`xbd = Xβ + FE`
3. 在边界上应用 ReLU：`u = max(xbd, 0)`
4. 迭代直到 `xbd[boundary] >= 0` 或残差满足阈值

**暂不实现**（超出 Wave 7 范围）。

---

## 4. Python 实现路径

### 4.1 `separation(fe)` 最小实现

在 `PPMLHDFE` 的 `fit()` 中：
1. 在构造 `AbsorbingOLS` 准备数据前，检测是否有 `separation="fe"` 参数
2. 若启用，先运行一轮**加权** singleton drop，权重为 `y`
3. 记录被剔除的观测索引
4. 在主 IRLS 循环中使用剔除后的数据
5. 返回结果中附加 `separation_dropped` 字段，标明被剔除的观测数

### 4.2 与 Stata 对齐要点

- Stata 的 `ppmlhdfe, separation(fe)` **默认启用**（若不指定 `separation` 选项，实际行为等价于 `fe`）
- 被剔除观测不计入 `e(N)`
- 若 `keepsingletons` 与 `separation(fe)` 同时指定，行为需参考源码（通常 `separation` 优先）

---

## 5. Synthetic 样例设计

### `w7_ppmlhdfe_separation_fe`

- **数据集**：手工生成面板数据，故意构造 2-3 个 `exporter-importer` 组合在所有时期 `trade = 0`
- **Stata 命令**：`ppmlhdfe trade gdp_o gdp_d dist, absorb(exporter importer) vce(robust) separation(fe)`
- **Python API**：`PPMLHDFE(..., absorb=["exporter","importer"], separation="fe").fit(vce="robust")`
- **风险焦点**：
  - 被剔除观测数是否与 Stata 一致
  - 剩余数据的系数、标准误、对数似然是否与 Stata 字段级对齐
  - 不启用 `separation` 时是否收敛异常或系数偏离

---

## 6. 文献与源码索引

| 内容 | 来源 |
|------|------|
| `separation(fe)` 加权 singleton 机制 | `ppmlhdfe.mata`：`GLM::init_fixed_effects()` |
| ReLU 方法 | `ppmlhdfe_separation_relu.mata`：`relu_fix_separation()` |
| Simplex 方法 | `ppmlhdfe_separation_simplex.mata`：`simplex_fix_separation()` |
| 理论基础 | Correia, Guimarães, Zylkin (2020) — "PPMLHDFE: Fast Poisson Estimation with High-Dimensional Fixed Effects" |
