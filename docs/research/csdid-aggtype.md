# `csdid` aggtype 研究档案

## 命令定位

- 命令族：`DID / Event Study Extensions`
- 类型：`csdid` 的后估计聚合子系统
- 规则来源：Callaway & Sant'Anna (2021) Section 4 + `csdid` Stata 帮助文档
- 关联命令：`csdid_estat`（Stata 后估计命令）

## 核心洞察

`csdid` 估计的是**组-时间 ATT** $\widehat{ATT}(g,t)$，这是一个矩阵（cohort × time）。用户通常关心的是更低维度的聚合量：

| aggtype | 聚合维度 | 公式 | 用途 |
|---------|---------|------|------|
| `simple` | 无 | $\frac{1}{\sum N_g} \sum_{g,t} N_g \cdot ATT(g,t)$ | 总体平均处理效应 |
| `dynamic` / `event` | 相对时间 $e = t-g$ | $\sum_{g,t: t-g=e} w_{g,t} \cdot ATT(g,t)$ | 事件研究动态效应 |
| `group` | 处理组 $g$ | $\sum_{t \geq g} w_{g,t} \cdot ATT(g,t)$ | 组特定效应 |
| `calendar` | 日历时间 $t$ | $\sum_{g \leq t} w_{g,t} \cdot ATT(g,t)$ | 时间特定效应 |

当前实现仅支持 `event`（通过 `.estat_event()`），需要扩展全部四种。

## 数学公式

### 通用聚合框架

所有聚合都可以写成：

$$
\hat{\theta} = \sum_{(g,t) \in \mathcal{S}} \hat{w}_{g,t} \cdot \widehat{ATT}(g,t)
$$

其中 $\mathcal{S}$ 是符合条件的 $(g,t)$ 集合，$\hat{w}_{g,t}$ 是权重。

### `simple` — 简单平均

$$\hat{\theta}_{simple} = \frac{1}{\sum_{g,t} N_g} \sum_{g,t} N_g \cdot \widehat{ATT}(g,t)$$

权重：$w_{g,t} = N_g / \sum_{g,t} N_g$

**特点：**
- 所有有效的 $(g,t)$ 组合等权（按 cohort 大小加权）
- 不关心时间结构
- 最简洁的总体效应度量

### `group` — 按处理组聚合

对每个 cohort $g$：

$$\hat{\theta}_g = \sum_{t \geq g} \hat{w}_{g,t} \cdot \widehat{ATT}(g,t)$$

其中权重 $w_{g,t} = N_{g,t} / N_g$（cohort $g$ 在时期 $t$ 的观测占比）。

**特点：**
- 回答 "cohort $g$ 的处理效应是多少"
- 不同 cohort 可以有不同的效应轨迹
- 输出是一个向量 $[\theta_{g_1}, \theta_{g_2}, \ldots]$

### `calendar` — 按日历时间聚合

对每个时期 $t$：

$$\hat{\theta}_t = \sum_{g \leq t} \hat{w}_{g,t} \cdot \widehat{ATT}(g,t)$$

其中权重 $w_{g,t} = N_{g,t} / N_t$（时期 $t$ 中 cohort $g$ 的观测占比）。

**特点：**
- 回答 "时期 $t$ 的平均处理效应是多少"
- 捕捉处理效应随日历时间的变化
- 输出是一个向量 $[\theta_{t_1}, \theta_{t_2}, \ldots]$

### `dynamic` / `event` — 按相对时间聚合

对每个事件时间 $e = t - g$：

$$\hat{\theta}_e = \sum_{(g,t): t-g=e} \hat{w}_{g,t} \cdot \widehat{ATT}(g,t)$$

其中权重 $w_{g,t} = N_{g,t} / N_e$（事件时间 $e$ 中 cohort $g$ 的观测占比）。

**特点：**
- 回答 "处理后 $e$ 期的平均效应是多少"
- 标准的事件研究图
- 当前已实现（`.estat_event()`）

## 标准误的 Delta 方法

聚合后的标准误需要使用 **delta 方法**，因为权重 $w_{g,t}$ 也是样本估计量。

### 影响函数的聚合

Callaway-Sant'Anna (2021) 的核心结果：聚合估计量的影响函数可以写成 `ATT(g,t)` 影响函数的线性组合：

$$
\hat{\psi}_{\theta} = \sum_{g,t} \hat{w}_{g,t} \cdot \hat{\psi}_{g,t} + \sum_{g,t} \widehat{ATT}(g,t) \cdot \hat{\psi}_{w,g,t}
$$

其中 $\hat{\psi}_{w,g,t}$ 是权重的影响函数。

### 简化：Stata 的实现

Stata 的 `csdid_estat` 使用一种**简化的 delta 方法**：

1. 构造 **RIF（Recentered Influence Function）** 矩阵：
   - `rifgt[(g,t), i]` = 单元 $i$ 的 $ATT(g,t)$ RIF
   - `rifwt[(g,t), i]` = 单元 $i$ 的 $ATT(g,t)$ 权重 RIF

2. 对每种聚合，调用 `aggte(rifgt, rifwt)`：
   ```mata
   function aggte(rifgt, rifwt) {
       mn_attg = mean(rifgt)
       mn_wgt = mean(rifwt)
       atte = sum(mn_attg .* mn_wgt) / sum(mn_wgt)
       wgtw = mn_wgt :/ sum(mn_wgt)
       attw = mn_attg :/ sum(mn_wgt)
       r1 = wgtw :* (rifgt - mn_attg)
       r2 = attw :* (rifwt - mn_wgt)
       r3 = (rifwt - mn_wgt) :* (atte / sum(mn_wgt))
       rif_event = rowsum(r1 + r2 - r3) :+ atte
       return(atte, rif_event)
   }
   ```

3. 标准误：
   $$SE = \sqrt{\frac{1}{N^2} \sum_{i=1}^{N} (\text{rif}_{\theta,i} - \hat{\theta})^2}$$

### 当前实现分析

当前 `csdid.py` 中的 `_aggte` 方法已经实现了上述 `aggte` 逻辑：

```python
def _aggte(self, ag_rif, ag_wt):
    mn_attg = ag_rif.mean(axis=0)
    mn_wgt = ag_wt.mean(axis=0)
    atte = np.sum(mn_attg * mn_wgt) / np.sum(mn_wgt)
    wgtw = mn_wgt / np.sum(mn_wgt)
    attw = mn_attg / np.sum(mn_wgt)
    r1 = wgtw * (ag_rif - mn_attg)
    r2 = attw * (ag_wt - mn_wgt)
    r3 = (ag_wt - mn_wgt) * (atte / np.sum(mn_wgt))
    rif_event = np.sum(r1 + r2 - r3, axis=1) + atte
    return atte, rif_event
```

**关键：** 只要正确构造 `rifgt` 和 `rifwt`，`_aggte` 可以复用于所有聚合类型。

## 各 aggtype 的 RIF 构造

### `simple`

对所有 $(g,t)$ 组合：
- `rifgt`：所有 $ATT(g,t)$ 的 RIF（一列一个 $(g,t)$）
- `rifwt`：所有 $N_g$ 的 RIF（权重就是 cohort 大小）

**注意：** `simple` 的权重不依赖于时间，所以 `rifwt` 的 delta-method 项可能简化。

### `group`

对每个 cohort $g$：
- `rifgt`：该 cohort 的所有 $ATT(g,t)$ RIF
- `rifwt`：该 cohort 在各时期的观测占比 RIF

### `calendar`

对每个时期 $t$：
- `rifgt`：该时期的所有 $ATT(g,t)$ RIF
- `rifwt`：该时期各 cohort 的观测占比 RIF

### `dynamic` / `event`

已实现的逻辑：
```python
for e, pairs in event_map.items():
    k = len(pairs)
    ag_rif = np.zeros((n_units, k))
    ag_wt = np.zeros((n_units, k))
    for j, p in enumerate(pairs):
        for i, u in enumerate(units):
            ag_rif[i, j] = rifgt[p][u]
            ag_wt[i, j] = rifwt[p][u]
    atte, rif_event = _aggte(ag_rif, ag_wt)
```

## `csdid_estat` 的 Stata 语法

```stata
csdid_estat simple
csdid_estat group
csdid_estat calendar
csdid_estat event        // 当前已实现
csdid_estat pretrend     // 事件前趋势检验（joint test of pre_e = 0）
```

### `pretrend` 子命令

对所有 $e < 0$ 的 `event` 估计做联合 Wald 检验：

$$H_0: \theta_{e} = 0 \text{ for all } e < 0$$

需要 `event` 估计的协方差矩阵（不仅仅是方差）。

## Python API 设计（Round 2 参考）

### 扩展现有接口

```python
def estat(self, aggtype="event"):
    """
    Post-estimation aggregation.

    Parameters
    ----------
    aggtype : str
        - "simple": simple average of all ATT(g,t)
        - "group": average by cohort
        - "calendar": average by calendar time
        - "event": average by event time (default)
        - "pretrend": joint test of pre-trends
    """
    if aggtype == "event":
        return self._estat_event()
    elif aggtype == "simple":
        return self._estat_simple()
    elif aggtype == "group":
        return self._estat_group()
    elif aggtype == "calendar":
        return self._estat_calendar()
    elif aggtype == "pretrend":
        return self._estat_pretrend()
    else:
        raise ValueError(f"Unknown aggtype: {aggtype}")
```

### `_estat_simple` 实现

```python
def _estat_simple(self):
    pairs = list(self._group_time_att.keys())
    k = len(pairs)
    ag_rif = np.zeros((self._n_units, k))
    ag_wt = np.zeros((self._n_units, k))
    for j, p in enumerate(pairs):
        for i, u in enumerate(self._units):
            ag_rif[i, j] = self._rifgt[p][u]
            ag_wt[i, j] = self._rifwt[p][u]
    atte, rif_simple = self._aggte(ag_rif, ag_wt)
    se = np.sqrt(np.sum((rif_simple - atte)**2)) / self._n_units
    return {"simple": atte, "se": se}
```

### `_estat_group` 实现

```python
def _estat_group(self):
    cohorts = sorted(set(g for g, t in self._group_time_att.keys()))
    results = {}
    for g in cohorts:
        pairs = [(g, t) for g_c, t in self._group_time_att.keys() if g_c == g]
        # ... 对每个 cohort 调用 _aggte ...
        results[f"g{int(g)}"] = atte
    return results
```

### `_estat_pretrend` 实现

```python
def _estat_pretrend(self):
    pre_events = [e for e in self._event_est if isinstance(e, int) and e < 0]
    # 构造 pre-event 估计的协方差矩阵
    # 使用 event RIF 的样本协方差
    pre_rifs = np.array([self._event_rif[e] for e in pre_events])
    pre_est = np.array([self._event_est[e] for e in pre_events])
    cov = np.cov(pre_rifs, rowvar=False) / self._n_units
    f_stat = pre_est.T @ np.linalg.inv(cov) @ pre_est / len(pre_events)
    from scipy.stats import f
    p_value = 1 - f.cdf(f_stat, len(pre_events), self._n_units)
    return {"f_stat": f_stat, "p_value": p_value, "df": len(pre_events)}
```

## Synthetic 样例设计

### `w9_csdid_agg_simple`

- **数据集**：500 单元 × 11 年，3 个 cohort + never-treated
- **Stata 命令**：
  ```stata
  csdid y, ivar(id) time(year) gvar(first_treat) method(reg)
  csdid_estat simple
  ```
- **对齐焦点**：`simple` 估计值是否等于所有 `ATT(g,t)` 的加权平均

### `w9_csdid_agg_group`

- **Stata 命令**：
  ```stata
  csdid_estat group
  ```
- **对齐焦点**：每个 cohort 的 group-specific 效应

### `w9_csdid_agg_calendar`

- **Stata 命令**：
  ```stata
  csdid_estat calendar
  ```
- **对齐焦点**：每个 calendar year 的 time-specific 效应

### `w9_csdid_agg_pretrend`

- **数据集**：引入轻微 pretreatment trend
- **Stata 命令**：
  ```stata
  csdid_estat pretrend
  ```
- **对齐焦点**：`f_stat` 和 `p_value`

## 与现有代码的衔接

当前 `.estat_event()` 已经实现了 `dynamic`/`event` 聚合。扩展步骤：

1. 将 `_aggte` 提升为公共方法（已是）
2. 在 `fit()` 中保存 `rifgt` 和 `rifwt`（当前已保存）
3. 新增 `.estat_simple()`, `.estat_group()`, `.estat_calendar()`, `.estat_pretrend()`
4. 每个方法构造正确的 `ag_rif` 和 `ag_wt`，调用 `_aggte`
5. 返回 `ResultSchema`

**最小改动点：**
- `csdid.py`：新增 4 个 `estat_*` 方法
- `compat/stata/did.py`：`csdid` wrapper 新增 `estat` 参数或后估计调用

## 风险

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| 协方差矩阵奇异 | MEDIUM | 检测并降维处理 |
| 小样本聚合 | LOW | 大样本近似足够 |
| 权重为 0 的 (g,t) | LOW | 跳过这些组合 |
| 与 Stata 权重定义差异 | MEDIUM | 对照 Stata 输出验证 |
