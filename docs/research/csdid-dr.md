# `csdid` method="dr"（双重稳健）研究档案

## 命令定位

- 命令族：`DID / Event Study Extensions`
- 类型：`csdid` 的估计方法扩展
- 规则来源：Callaway & Sant'Anna (2021) Section 3.2 + `drdid` Stata 包
- 关联命令：`drdid`（`csdid` 内部调用 `drdid` 来计算 DR ATT）

## 核心洞察

当前 `csdid` 仅支持 `method="reg"`（回归调整），即：

$$
\widehat{ATT}(g,t) = (\bar{Y}_{g,t} - \bar{Y}_{g,g-1}) - (\bar{Y}_{c,t} - \bar{Y}_{c,g-1})
$$

`method="dr"` 引入**双重稳健（Doubly Robust）**估计量，结合：
1. **倾向得分（Propensity Score, PS）**：$p_g(X) = P(G=g \mid X)$
2. **结果回归（Outcome Regression, OR）**：$m_{g,t}(X) = \mathbb{E}[Y_t - Y_{g-1} \mid X, G=g]$

DR 的核心优势：**只要 PS 或 OR 中有一个正确设定，估计量就是一致的**。

## 数学公式

### 识别假设（Callaway-Sant'Anna 2021）

1. **无预期效应**：$\mathbb{E}[Y_t(0) - Y_{g-1}(0) \mid G=g, X] = \mathbb{E}[Y_t(0) - Y_{g-1}(0) \mid D=0, X]$ for $t \geq g$
2. **重叠条件（Overlap）**：$0 < p_g(X) < 1$ almost surely
3. **条件平行趋势**：在以 $X$ 为条件的反事实结果上，处理组和对照组满足平行趋势

### DR ATT(g,t) 估计量

对 cohort $g$ 和时期 $t \geq g$：

$$
\widehat{ATT}_{DR}(g,t) = \mathbb{E}_n\left[ \hat{\psi}_{g,t}(Y, X, G) \right]
$$

其中影响函数（influence function）$\hat{\psi}_{g,t}$ 为：

$$
\hat{\psi}_{g,t} = \frac{G_g}{\hat{p}_g(X)} \left( (Y_t - Y_{g-1}) - \hat{m}_{g,t}(X) \right) - \frac{1-G_g}{1-\hat{p}_g(X)} \hat{m}_{g,t}(X) + \hat{m}_{g,t}(X)
$$

等价形式（更易实现）：

$$
\hat{\psi}_{g,t} = \frac{G_g}{\hat{p}_g(X)} (Y_t - Y_{g-1}) - \left( \frac{G_g - \hat{p}_g(X)}{\hat{p}_g(X)(1-\hat{p}_g(X))} \right) \hat{m}_{g,t}(X)
$$

其中：
- $G_g = \mathbf{1}(G = g)$：属于 cohort $g$ 的指示变量
- $G_c = \mathbf{1}(G = 0)$：从未处理（或 not-yet-treated）的指示变量
- $\hat{p}_g(X)$：倾向得分估计（通常用 logit/probit）
- $\hat{m}_{g,t}(X)$：结果回归估计（通常用 OLS）

### 倾向得分模型

对 cohort $g$，在**所有未处理单元**（never-treated 或 not-yet-treated）上估计：

$$
\text{logit}(p_g(X)) = \alpha + \beta' X
$$

预测 $\hat{p}_g(X_i)$ 对每个观测 $i$。

**关键：**
- 训练样本包括 cohort $g$ 的单元（$G=g$，正例）和未处理单元（$G=0$，负例）
- 不包括其他 cohort 的单元（$G \neq g, 0$）

### 结果回归模型

对 cohort $g$ 和时期 $t$，在**cohort $g$ 的单元**上估计：

$$
Y_{it} - Y_{i,g-1} = \alpha + \beta' X_i + \varepsilon_{it}
$$

预测 $\hat{m}_{g,t}(X_i)$ 对所有观测（包括未处理单元）。

**关键：**
- 训练样本仅包括 cohort $g$ 的单元
- 因变量是**差分** $Y_t - Y_{g-1}$，不是水平 $Y_t$
- 对未处理单元，$\hat{m}_{g,t}(X_i)$ 被用作反事实预测

## 与 method="reg" 的关系

| 维度 | method="reg" | method="dr" |
|------|---------------|-------------|
| 需要协变量 | 否（当前实现） | 是 |
| 一致性要求 | OR 正确 | OR 正确 **或** PS 正确 |
| 效率 | 一般 | 更高（若两者都正确） |
| 计算复杂度 | 低 | 高（需拟合 PS + OR） |
| 小样本行为 | 稳定 | 可能不稳定（PS 接近 0/1） |

当 OR 正确时，DR 退化为回归调整；当 PS 正确时，DR 退化为 IPW。

## `drdid` 包的方法映射

`csdid` 内部调用 `drdid` 包，`drdid` 提供以下方法：

| `drdid` 方法 | 说明 | `csdid` 对应 |
|-------------|------|-------------|
| `drimp` | DR imputation（默认） | `csdid, method(drimp)` |
| `dripw` | DR IPW | `csdid, method(dripw)` |
| `reg` | 回归调整 | `csdid, method(reg)` |
| `ipw` | 逆概率加权 | `csdid, method(ipw)` |
| `stdipw` | 标准化 IPW | `csdid, method(stdipw)` |

### `drimp` vs `dripw`

两者都是 DR 估计量，但影响函数形式不同：

- **`drimp`**：基于 **imputation** 的 DR
  $$
  \hat{\psi}_{DRimp} = \frac{G_g}{\hat{p}_g} (\Delta Y - \hat{m}) + \hat{m} - \frac{1-G_g}{1-\hat{p}_g} \hat{m}
  $$

- **`dripw`**：基于 **IPW** 的 DR
  $$
  \hat{\psi}_{DRipw} = \frac{G_g}{\hat{p}_g} \Delta Y - \frac{G_g - \hat{p}_g}{\hat{p}_g(1-\hat{p}_g)} \hat{m}
  $$

数值上两者等价（影响函数的期望相同），但小样本表现可能不同。`drimp` 更稳定，因为当 $\hat{p} \approx 1$ 时第一项不会爆炸。

## Python 实现路径（Round 2 参考）

### 最小实现：`method="drimp"`

1. **输入**：`data`, `y`, `id`, `time`, `first_treat`, `xvars`（协变量列表）
2. **对每个 (g, t) 组合**：
   a. 构造训练样本：
      - PS 样本：`G=g` 或 `G=0`（从未处理）
      - OR 样本：`G=g`
   b. 拟合 PS：`Logit(G=g ~ X)` 在 PS 样本上
   c. 拟合 OR：`OLS(Y_t - Y_{g-1} ~ X)` 在 OR 样本上
   d. 预测：`p_hat`（全样本），`m_hat`（全样本）
   e. 构造影响函数 `psi`（对每个单元）
   f. `ATT(g,t) = mean(psi)`
   g. `SE(g,t) = sqrt(sum(psi^2)) / N`

3. **聚合**：与 `method="reg"` 相同，使用 `aggte()`

### 关键代码结构

```python
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression

class CSDIDDR:
    def _fit_ps(self, df, g, xvars):
        """Fit propensity score for cohort g."""
        ps_mask = (df['first_treat'] == g) | (df['first_treat'] == 0)
        ps_df = df.loc[ps_mask].copy()
        ps_df['treat'] = (ps_df['first_treat'] == g).astype(int)
        model = LogisticRegression(max_iter=1000)
        model.fit(ps_df[xvars], ps_df['treat'])
        return model.predict_proba(df[xvars])[:, 1]

    def _fit_or(self, df, g, t, xvars):
        """Fit outcome regression for cohort g, period t."""
        or_mask = df['first_treat'] == g
        or_df = df.loc[or_mask].copy()
        # Construct delta Y: Y_t - Y_{g-1}
        or_df['delta_y'] = or_df[f'y_{t}'] - or_df[f'y_{g-1}']
        model = LinearRegression()
        model.fit(or_df[xvars], or_df['delta_y'])
        return model.predict(df[xvars])

    def _compute_dr_if(self, df, g, t, p_hat, m_hat):
        """Compute DR influence function."""
        G_g = (df['first_treat'] == g).astype(float)
        delta_Y = df[f'y_{t}'] - df[f'y_{g-1}']
        # DRimp formula
        psi = (G_g / p_hat) * (delta_Y - m_hat) + m_hat
        # Subtract control contribution
        G_c = (df['first_treat'] == 0).astype(float)
        psi -= (G_c / (1 - p_hat)) * m_hat
        return psi
```

### 数值稳定性处理

1. **Trimming（截断）**：当 $\hat{p} < 0.01$ 或 $\hat{p} > 0.99$ 时，设置为 0.01 / 0.99
2. **完美分离**：logit 的完美分离会导致 $\hat{p} = 0$ 或 $1$，需要检测并回退到 `method="reg"`
3. **小样本**：当 cohort $g$ 的样本量 < 30 时，PS 估计不稳定，建议报错或回退

## 标准误计算

DR 的 SE 基于影响函数：

$$
\widehat{SE}_{DR}(g,t) = \sqrt{\frac{1}{N^2} \sum_{i=1}^{N} \hat{\psi}_{i,g,t}^2}
$$

如果指定 `cluster`，则按 cluster 聚合：

$$
\widehat{SE}_{DR,cluster}(g,t) = \sqrt{\frac{1}{N^2} \sum_{c=1}^{C} \left( \sum_{i \in c} \hat{\psi}_{i,g,t} \right)^2}
$$

**注意：** 这是 "plug-in" SE，没有考虑 PS 和 OR 估计的第一阶段误差。在标准 `drdid` 实现中，这是可接受的近似。

## Synthetic 样例设计

### `w9_csdid_dr_basic`

- **数据集**：500 单元 × 11 年，3 个 cohort + never-treated
- **协变量**：`x1`（影响处理概率和结果），`x2`（仅影响结果）
- **Stata 命令**：
  ```stata
  csdid y x1 x2, ivar(id) time(year) gvar(first_treat) method(drimp) vce(cluster id)
  csdid_estat event
  ```
- **对齐焦点**：
  - `ATT(g,t)` 与 `method(reg)` 的差异（应接近但不同）
  - 标准误的比较（DR SE 通常更小）
  - 事件研究动态效应的方向一致性

### `w9_csdid_dr_vs_reg`

- **数据集**：同上，但 OR 模型正确设定（线性）
- **设计**：验证当 OR 正确时，`drimp` 和 `reg` 的结果接近
- **预期**：点估计差异 < 1%，SE 差异 < 5%

## 风险

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| PS 完美分离 | HIGH | trimming + 回退到 reg |
| 小 cohort 样本 | MEDIUM | 设置最小样本量阈值 |
| 协变量过多 | MEDIUM | 正则化或降维 |
| 计算成本高 | LOW | 缓存 PS/OR 模型结果 |
| 与 Stata 的 logit 差异 | MEDIUM | 使用相同优化器和容差 |

## 与现有代码的衔接

当前 `CSDID.fit()` 的 `method="reg"` 路径需要扩展：

1. 在 `fit()` 中添加 `xvars` 参数
2. 添加 `method` 分支：`"reg"` | `"drimp"` | `"dripw"`
3. 对 `method="drimp"`：
   - 在 `_compute_att_gt` 中调用 `_fit_ps` 和 `_fit_or`
   - 构造 DR 影响函数
   - 复用现有的 `aggte` 聚合逻辑

**关键改动点：**
- `CSDID.__init__`：可能需要接受 `xvars`
- `CSDID.fit`：分支逻辑
- 新增 `CSDID._fit_ps`, `CSDID._fit_or`, `CSDID._compute_dr_if`
