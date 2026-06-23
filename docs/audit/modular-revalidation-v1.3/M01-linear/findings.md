# M01 Linear 审查问题台账 v1.3

## 审查信息

| 项目 | 值 |
|---|---|
| 模块 | M01 Linear |
| 审查日期 | 2026-06-12 |
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| 审查人 | Kimi Code CLI |
| 性质 | 只读审查，不修改产品代码 |

## 状态定义

- **Confirmed-Stata**：通过本轮新建 Stata 17 双跑稳定复现。
- **Confirmed-Math**：具有可核验的解析真值或严格推导。
- **Confirmed-Code**：由确定的代码路径直接证明，不依赖统计口径争议。
- **Suspected**：存在强烈风险，但尚未完成独立证据闭环。
- **Coverage Gap**：只确认缺少证据，不得写成算法错误。

---

## 问题总表

| ID | 严重性 | 范围 | 证据状态 | 问题摘要 |
|---|---|---:|---|---|
| M01-LIN-001 | P1 | `OLS` / `regress()` aweight | Confirmed-Stata | `aweight=0` 被 Python 硬拒绝，Stata 17 将其视为零权重观测并删除 |
| M01-LIN-002 | P1 | `OLS` 共线性检测 | Confirmed-Stata | 近共线回归变量未被省略，与 Stata 17 的 tolerance 处理不一致 |
| M01-LIN-003 | P1 | `regress()` 两路 cluster VCE | Confirmed-Stata | 两路 cluster 时 Python 报告 cluster-robust Wald F，Stata 17 `e(F)` 为 OLS F-statistic |

---

## M01-LIN-001: aweight=0 处理与 Stata 不一致

### 严重性

P1

### 证据状态

Confirmed-Stata

### 受影响 API

- `stataflow.OLS` (`weights` + `weight_type="aweight"`)
- `stataflow.compat.stata.regress()` (`aweight` 参数)

### 最小复现

文件：`docs/audit/modular-revalidation-v1.3/M01-linear/evidence/minimal-reproductions/m01_lin_001_aweight_zero.py`

```python
import pandas as pd
from stataflow.compat.stata import regress
from stataflow import OLS

df = pd.DataFrame({
    "y": [1.0, 2.0, 3.0, 4.0, 5.0],
    "x": [1.0, 2.0, 3.0, 4.0, 5.0],
    "w": [1.0, 1.0, 0.0, 1.0, 1.0],
})

OLS(df, y="y", x=["x"], weights=df["w"].values, weight_type="aweight").fit()
# -> ValueError: aweight requires all weights > 0

regress(df, y="y", x=["x"], aweight="w")
# -> ValueError: aweight requires all weights > 0
```

对应 Stata 17 命令：

```stata
regress y x [aweight=w]
```

Stata 输出：nobs=4，零权重观测被删除，回归正常完成。

### Python 结果

```text
ValueError: aweight requires all weights > 0
```

### Stata 17 结果

```text
Number of obs   =         4
```

回归成功，零权重行不参与估计。

### 数学/代码根因

`src/stataflow/estimators/ols.py` 第 151 行：

```python
if np.any(weight_arr <= 0):
    raise ValueError("aweight requires all weights > 0")
```

Stata 对 `aweight=0` 的处理是：零权重观测不计入估计样本，但保留在数据集中。Python 在 missing screening 之后、归一化之前显式拒绝所有非正权重，导致合法 Stata 命令无法运行。

### 用户影响

任何使用 `aweight` 且权重可能为 0 的数据集（例如抽样权重、逆概率权重中某些单元权重为 0）会在 Python 端崩溃，而 Stata 可以正常估计。

### 受影响范围

仅影响 `aweight` 类型权重。不影响 `fweight`/`pweight`/`iweight`（尚未支持）。

### 是否为共享基础设施问题

否，问题局限于 `OLS._prepare_data` 的权重校验。

### 当前是否存在旧 issue

v1.2 的 VCE-005 提到加权 sandwich 的权重阶数风险，但未记录零权重处理差异。

### 建议修复方向

将 `aweight=0` 的观测在 missing screening 阶段一并删除（与缺失权重一致），而不是在检测到零权重时抛出异常。删除后仍按 `sum(w) = N` 归一化。

---

## M01-LIN-002: 近共线回归变量未被省略

### 严重性

P1

### 证据状态

Confirmed-Stata

### 受影响 API

- `stataflow.OLS`
- `stataflow.compat.stata.regress()`

### 最小复现

文件：`docs/audit/modular-revalidation-v1.3/M01-linear/evidence/minimal-reproductions/m01_lin_002_near_collinearity.py`

```python
import numpy as np
import pandas as pd
from stataflow import OLS

rng = np.random.default_rng(20260613)
n = 50
x1 = rng.normal(size=n)
x2 = (x1 + rng.normal(scale=1e-7, size=n)) * 1e6
y = 1.0 + 2.0 * x1 + 3.0 * x2 + rng.normal(scale=0.5, size=n)
df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

res = OLS(df, y="y", x=["x1", "x2"], add_constant=True).fit(vce="ols")
print([(c.name, c.beta, c.std_err) for c in res.coefficients])
```

对应 Stata 17 命令：

```stata
regress y x1 x2
```

### Python 结果

```text
correlation(x1, x2) = 0.9999999999999952
coefficients:
  x1: beta=1.19642e+06, se=784257
  x2: beta=1.80359, se=0.784257
  _cons: beta=1.03044, se=0.0717006
dropped_vars: []
```

### Stata 17 结果

```text
note: x1 omitted because of collinearity.
        x2 |   2.98e-06   2.82e-08   ...
     _cons |    1.00321   .0337078   ...
```

### 数学/代码根因

`src/stataflow/estimators/_vce_utils.py` 的 `detect_collinear_columns` 使用 `np.linalg.matrix_rank` 默认 tolerance。当 `x2` 是 `x1` 的近似线性函数但 scaled 到 1e6 时，数值上矩阵仍是满秩，因此 Python 保留两列。

Stata 17 使用更严格的共线性 tolerance（基于变量尺度与条件数），在相关度极高时主动省略一个变量并给出 `note: x1 omitted because of collinearity`。

结果：Python 估计了一个数值病态的双变量模型，x1 系数巨大（1.2e6），x2 系数被扭曲；Stata 估计了稳定的单变量模型。

### 用户影响

在存在近似共线性的真实数据（如高度相关的资产收益率、不同量纲的同一概念度量）中，Python 可能返回不稳定、难以解释的系数，而 Stata 会明确省略冗余变量。

### 受影响范围

所有使用 `OLS` 的回归路径，包括 `regress()`、`xtreg_fe()` 中通过 `OLS` 的部分、`areg()` 中通过 `OLS` 的部分。

### 是否为共享基础设施问题

是。`detect_collinear_columns` 位于 `_vce_utils.py`，被多个估计器共用。但本 finding 在 M01 场景下确认。

### 当前是否存在旧 issue

v1.2 LIN-001 报告了 `FixedEffectsOLS` 的组内共线崩溃，但那是 FE 估计器问题。本 finding 针对 `OLS` 本身，且不是崩溃而是静默产生不稳定系数。

### 建议修复方向

对齐 Stata 的共线性判定 tolerance，或在 `detect_collinear_columns` 中引入条件数/方差膨胀因子检查，对高条件数设计矩阵给出与 Stata 一致的省略行为。需要记录 Stata 具体 tolerance 规则并编写回归测试。

---

## M01-LIN-003: 两路 cluster 时 F 统计量语义与 Stata 不一致

### 严重性

P1

### 证据状态

Confirmed-Stata

### 受影响 API

- `stataflow.OLS.fit(vce="cluster", cluster=[...])`
- `stataflow.compat.stata.regress(..., vce="cluster", cluster=[...])`

### 最小复现

文件：`docs/audit/modular-revalidation-v1.3/M01-linear/evidence/minimal-reproductions/m01_lin_003_twoway_cluster_fstat.py`

```python
import numpy as np
import pandas as pd
from stataflow.compat.stata import regress

rng = np.random.default_rng(20260613)
n_firms, n_years = 30, 20
n = n_firms * n_years
firm = np.repeat(np.arange(n_firms), n_years)
year = np.tile(np.arange(n_years), n_firms)
x = rng.normal(size=n)
y = 1.0 + 2.0 * x + rng.normal(scale=0.5, size=n)
df = pd.DataFrame({"y": y, "x": x, "firm": firm, "year": year})

res = regress(df, y="y", x=["x"], vce="cluster", cluster=["firm", "year"])
print(res.fit.f_stat)
```

对应 Stata 17 命令：

```stata
regress y x, vce(cluster firm year)
```

### Python 结果

```text
nobs=600
f_stat=8616.9017
f_pvalue=0.0
x: beta=1.96608, se=0.02118
_cons: beta=0.989432, se=0.0168435
```

### Stata 17 结果

```text
F(1, 598)       =   3354.19
Prob > F        =    0.0000
E_F=3354.1896
E_DF_R=19
```

### 数学/代码根因

对于单路 cluster，Stata 17 的 `e(F)` 等于 cluster-robust Wald F（即 t^2，使用 cluster df）。

对于两路 cluster，Stata 17 的 `e(F)` 等于 OLS F-statistic（使用残差 df `n - k`），而 `e(df_r)` 仍记录为 `min(G1, G2) - 1`。Python 统一使用 cluster-robust Wald F，因此两路 cluster 下 `f_stat` 与 Stata `e(F)` 不一致。

代码位置：`src/stataflow/estimators/ols.py` 第 464-489 行，`vce == "cluster"` 分支的 Wald F 计算。

### 用户影响

依赖 `ResultSchema.fit.f_stat` 与 Stata `e(F)` 对齐的用户，在两路 cluster 场景下会得到不同数值。虽然 p-value 都接近 0，但字段语义不一致，可能导致报告或下游自动化比较失败。

### 受影响范围

仅 `regress()` 的两路 cluster 路径。单路 cluster F 统计量与 Stata 一致。

### 是否为共享基础设施问题

部分共享。`_vce_utils.compute_multiway_cluster_vce` 只负责 VCE，F 统计量在 `ols.py` 中计算。但该语义选择可能影响 IV/HDFE 等后续模块的两路 cluster F 统计量。

### 当前是否存在旧 issue

v1.2 VCE-002/003/004 记录了 HDFE 多路 cluster 的已知偏差，但未涉及 `OLS` 两路 cluster 的 F 统计量语义。

### 建议修复方向

明确 `ResultSchema.fit.f_stat` 在两路 cluster 下的语义：
- 方案 A：与 Stata `e(F)` 对齐，报告 OLS F-statistic；
- 方案 B：报告 cluster-robust Wald F，并在文档/字段名中明确区分。

无论选择哪种，都需要在 `ResultSchema` 或支持矩阵中记录，并补充双跑测试。

---

## 已验证通过的领域

以下路径在本轮新建实验中字段级对齐（相对误差 < 1e-6）：

- 手工可计算小样本 OLS（S1）
- 异方差 robust VCE（S2）
- 单路 cluster-robust VCE，含极不均衡组大小（S3）
- 含缺失值的 aweight（S4）
- factor 交互项在缺失改变有效 base level 时的参数化（S6）
- 行顺序不变性（P1）
- 无关列不变性（P2）
- 尺度变换可推导性（P3）
- Engel 真实数据 robust OLS（R1）

两路 cluster 的系数/标准误在平衡大 G 场景（S7）中一致，仅 F 统计量语义不同；在小 G 真实数据（R2）中标准误存在 1–3% 差异，与少量 cluster 的小样本调整有关。

---

## 未决/需继续验证事项

1. **v1.2 旧 finding 的独立复现**：本轮未对 v1.2 的 LIN-003（完美拟合除零）进行专门复现。当前代码已加入 `rss == 0` 分支，需设计新实验验证。
2. **aweight + robust/cluster 的权重阶数**：v1.2 VCE-005 提出加权 sandwich 权重阶数风险。S4 验证了缺失值处理，但未专门比较 `aweight + robust/cluster` 的 SE。
3. **predict/margins 样本传播**：M09 负责主要审查，但 M01 范围内 `OLS.predict` 的 newdata + collinearity drops 路径尚未做字段级双跑。
4. **HDFE/FE 路径的共线性**：M01 只审查 `OLS` 本身；`FixedEffectsOLS` / `AbsorbingOLS` 的共线性处理归 M02/M03。
