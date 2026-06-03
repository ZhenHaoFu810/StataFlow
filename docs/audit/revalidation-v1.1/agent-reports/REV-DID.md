# REV-DID-001

## 元信息
- **命令**: `csdid` / `did_imputation` / `eventstudyinteract`
- **命令族**: `DID / Event Study Extensions`
- **审查类型**: 源码审查 / API设计 / 边界case
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

---

## 问题 1：csdid() wrapper 直接返回 estat() 结果，不返回 fitted model，阻断二次分析工作流

### 问题摘要
- **严重度**: Blocker
- **问题类型**: API设计缺陷

### 现象描述
`stataflow.compat.stata.csdid()` 在内部调用 `model.fit(...)` 后，直接 `return model.estat(aggtype=aggtype)`。用户拿到的是 `ResultSchema` 对象，而非 `CSDID` 模型实例。这意味着：
1. 用户无法访问底层 `ATT(g,t)` 矩阵；
2. 无法先执行 `event` 聚合，再执行 `simple` 或 `group` 聚合；
3. 无法调用 `estat_pretrend()` 进行诊断检验后再查看系数表。

这与 Stata 工作流（`csdid` → `csdid_estat event` → `csdid_estat simple` → `csdid_estat pretrend`）完全脱节。

### 最小复现代码
```python
from stataflow.compat.stata import csdid
import pandas as pd, numpy as np

df = pd.DataFrame({
    "id": [1,1,2,2], "time": [1,2,1,2],
    "y": [1.0,2.0,3.0,4.0],
    "first_treat": [2,2,0,0]
})
res = csdid(df, y="y", id="id", time="time", first_treat="first_treat", aggtype="event")
# res 是 ResultSchema，不是 CSDID 实例
# 以下全部报错：
# res.estat("simple")        # AttributeError
# res._group_time_att        # AttributeError
# res.estat_pretrend()       # AttributeError
```

### 根因分析
`src/stataflow/compat/stata/did.py` 第170–173行：
```python
model.fit(method=method, vce=vce, cluster=cluster)
if aggtype is None:
    aggtype = "event"
return model.estat(aggtype=aggtype)
```
设计上将“拟合”和“后估计”耦合为一次调用，未暴露模型对象。

### 涉及文件
- `src/stataflow/compat/stata/did.py` (L170–173)

### 影响评估
- **影响范围**: `csdid` 单一命令，但阻断所有真实 staggered adoption 分析工作流
- **用户workaround**: 无（用户必须直接调用 `CSDID` 类，但 wrapper 的设计意图是 Stata 兼容层）
- **是否阻塞实际使用**: **是**

### 修复建议
修改 `csdid()` wrapper，使其返回一个包含 `.result` 和 `.model` 的复合对象，或者改返回 `model` 实例本身（用户再调用 `model.estat(...)`）。
预计工作量：小（1–2小时，需更新测试和文档）。

### 关联项
- 与 Stata `csdid` → `csdid_estat` 两阶段工作流不一致
- 用户明确报告 "csdid 无法使用"

---

## 问题 2：csdid() **kwargs 硬拒绝所有 Stata 合法参数（notyet / window / gtcontrol / longdiff 等）

### 问题摘要
- **严重度**: Blocker
- **问题类型**: 参数缺失 / 硬拒绝

### 现象描述
`csdid()` wrapper 对任何未显式声明的 `**kwargs` 直接抛出 `ValueError`（L159–160）。Stata `csdid` 中大量常用选项（`notyet`、`window()`、`minn()`、`gtcontrol`、`longdiff`）传入即崩溃。用户在真实数据中几乎不可避免地会使用这些选项，导致命令完全不可用。

### 最小复现代码
```python
from stataflow.compat.stata import csdid
# 以下调用在 Stata 中完全合法，但在 Python 中直接崩溃
csdid(df, y="y", id="id", time="time", first_treat="first_treat",
      notyet=True, window=[-3, 3])
# ValueError: Unsupported arguments: ['notyet', 'window']
```

### 根因分析
`src/stataflow/compat/stata/did.py` L159–160：
```python
if kwargs:
    raise ValueError(f"Unsupported arguments: {list(kwargs.keys())}")
```
`notyet`、`window`、`minn`、`gtcontrol`、`longdiff` 等均未在参数列表中声明，也未在 estimator 中实现，因此全部被拒绝。

### 涉及文件
- `src/stataflow/compat/stata/did.py` (L159–160)
- `src/stataflow/estimators/csdid.py` (缺少参数实现)

### 影响评估
- **影响范围**: `csdid` 单一命令
- **用户workaround**: 无（必须直接使用底层 `CSDID` 类，且底层同样不支持）
- **是否阻塞实际使用**: **是**

### 修复建议
1. 短期：将 `notyet`、`window`、`minn` 加入显式参数列表，对未实现的参数给出更有意义的错误信息（如 `"window not yet implemented"` 而非 `"Unsupported arguments"`）；
2. 中期：实现 `notyet`（控制组策略切换）、`window`（事件窗口裁剪）、`minn`（最小样本量过滤）。
预计工作量：中（4–8小时）。

---

## 问题 3：csdid method="drimp"/"dripw" 在无 never-treated 组时硬崩溃，不支持 not-yet-treated 控制组

### 问题摘要
- **严重度**: Critical
- **问题类型**: 边界case崩溃 / 参数缺失

### 现象描述
CSDID 的 `_fit_reg` 在无 never-treated 组时会自动回退到 not-yet-treated 控制组（L99–107），但 `_fit_dr`（drimp/dripw）在检测到无 never-treated 组时直接抛出 `ValueError`（L314–315）。这与 Stata `csdid, method(drimp)` 的行为不一致——Stata 支持 not-yet-treated 作为 DR 的控制组。对于真实 staggered adoption 数据（多 cohort、无 never-treated），DR 方法完全不可用。

### 最小复现代码
```python
from stataflow.compat.stata import csdid
import pandas as pd, numpy as np
rng = np.random.default_rng(42)
n = 60
units = np.repeat(np.arange(n), 5)
times = np.tile(np.arange(5), n)
ft = np.repeat(rng.choice([2,3], size=n), 5)  # 无 never-treated
y = 1.0 + rng.normal(size=n*5)
df = pd.DataFrame({"id": units, "time": times, "y": y, "first_treat": ft})

# regression 方法可运行
res_reg = csdid(df, y="y", id="id", time="time", first_treat="first_treat", method="reg")

# DR 方法直接崩溃
csdid(df, y="y", id="id", time="time", first_treat="first_treat",
      method="drimp", xvars=["x"])
# ValueError: method='drimp' requires never-treated units
```

### 根因分析
`src/stataflow/estimators/csdid.py` L312–315：
```python
has_never_treated = (df[ft] == 0).any()
if not has_never_treated:
    raise ValueError("method='drimp' requires never-treated units")
```

### 涉及文件
- `src/stataflow/estimators/csdid.py` (L312–315)

### 影响评估
- **影响范围**: `csdid` DR 模式
- **用户workaround**: 只能使用 `method="reg"`
- **是否阻塞实际使用**: 是（对于无 never-treated 的真实数据）

### 修复建议
扩展 `_fit_dr`，支持 `notyet=True` 时的 not-yet-treated 控制组逻辑：将控制组定义为 `df[ft] > max(g, t)`，并相应调整倾向得分模型（以 `G=g` vs `G>max(g,t)` 拟合 PS）。
预计工作量：中（4–6小时）。

---

## 问题 4：did_imputation allhorizons=True 完全不生效，始终只报告非负 horizon

### 问题摘要
- **严重度**: Critical
- **问题类型**: 数学偏差 / 参数未实现

### 现象描述
`DIDImputation.fit()` 中 `allhorizons` 参数被完全忽略。无论 `allhorizons=True` 还是 `False`，代码始终只计算 `h >= 0` 的 horizon（L238–240）。Stata `did_imputation, allhorizons` 会报告负向（pretreatment）horizon 的系数，这是事件研究诊断 pretrend 的关键功能。

### 最小复现代码
```python
from stataflow.compat.stata import did_imputation
res = did_imputation(df, y="y", id="id", time="time", first_treat="first_treat",
                     allhorizons=True)
names = [c.name for c in res.coefficients]
# 永远不会出现 "tau-1", "tau-2" 等负向 horizon
```

### 根因分析
`src/stataflow/estimators/did_imputation.py` L238–240：
```python
horizons = sorted(
    [h for h in df.loc[ever_treated_mask, "_K"].dropna().unique() if h >= 0]
)
```
硬编码 `h >= 0`，未使用 `allhorizons` 参数。测试文件 `test_compat_stata_did.py` L271–282 甚至错误地断言 `allhorizons=True` "should produce non-negative event-study horizons"，说明该 bug 被测试固化。

### 涉及文件
- `src/stataflow/estimators/did_imputation.py` (L238–240)
- `tests/test_compat_stata_did.py` (L271–282, L284–303)

### 影响评估
- **影响范围**: `did_imputation`
- **用户workaround**: 无（无法通过该命令获得 pretreatment 系数）
- **是否阻塞实际使用**: 是（事件研究无法诊断 pretrend）

### 修复建议
修改 horizon 生成逻辑：
```python
if allhorizons:
    horizons = sorted(df.loc[ever_treated_mask, "_K"].dropna().unique())
else:
    horizons = sorted([h for h in df.loc[ever_treated_mask, "_K"].dropna().unique() if h >= 0])
```
预计工作量：小（30分钟，含测试修复）。

---

## 问题 5：CSDID 未处理面板不平衡导致的 ATT(g,t) NaN 静默传播

### 问题摘要
- **严重度**: Critical
- **问题类型**: 边界case崩溃 / 数学偏差

### 现象描述
在 `_fit_reg` 中，若某个 cohort `g` 在某个时期 `t` 没有观测（unbalanced panel），`df.loc[treated_mask & (df[time] == t), y].mean()` 返回 `NaN`，导致 `att = NaN`。该 `NaN` 被存入 `att_gt` 并在 `_finalize_fit` 中传播至事件研究聚合，最终产生全 `NaN` 的系数表，且全程无警告或错误。用户面对 "全 NaN 输出" 无法诊断原因。

### 最小复现代码
```python
from stataflow.estimators import CSDID
import pandas as pd, numpy as np

df = pd.DataFrame({
    "id": [1, 1, 2, 2, 3, 3],
    "time": [1, 2, 1, 2, 1, 2],
    "y": [1.0, np.nan, 3.0, 4.0, 5.0, 6.0],  # id=1, t=2 缺失
    "first_treat": [2, 2, 2, 2, 0, 0]
})
model = CSDID(df, y="y", id="id", time="time", first_treat="first_treat")
model.fit(method="reg")
# 若 id=1 的 base 或 t 期缺失，att 可能为 NaN
```

### 根因分析
`src/stataflow/estimators/csdid.py` L127–130：
```python
mu_g_t = df.loc[treated_mask & (df[time] == t), y].mean()
...
att = (mu_g_t - mu_c_t) - (mu_g_base - mu_c_base)
```
未检查 `treated_mask & (df[time] == t)` 是否为空。此外 L91 `df.pivot(index=uid, columns=time, values=y)` 在存在重复 `(uid, time)` 时会直接抛出 `ValueError: Index contains duplicate entries, cannot reshape`，也未被捕获。

### 涉及文件
- `src/stataflow/estimators/csdid.py` (L91, L127–130, L162)

### 影响评估
- **影响范围**: `csdid`
- **用户workaround**: 无（用户需手动平衡面板）
- **是否阻塞实际使用**: 是（真实面板数据常有不平衡）

### 修复建议
1. 在计算 `mu_g_t` 前检查观测数，若 `N_g_t == 0` 则跳过该 `(g,t)` 对；
2. 在 `pivot` 前检查重复 `(uid, time)`，给出清晰错误；
3. 对 `NaN` ATT 进行断言或警告。
预计工作量：小（1–2小时）。

---

## 问题 6：CSDID ResultSchema 中 cluster_var 始终为 None，不记录实际聚类变量

### 问题摘要
- **严重度**: Major
- **问题类型**: 输出正确性 / API设计缺陷

### 现象描述
`CSDID.estat_event()` 和 `_make_result_schema()` 中硬编码 `cluster_var=None`（L533, L767）。即使用户传入 `cluster="county_id"`，返回的 `ResultSchema` 也不记录该变量。这导致：
1. 结果对象无法追溯使用了哪个聚类变量；
2. 下游测试或报告生成无法正确标注 cluster SE 的来源。

### 根因分析
`src/stataflow/estimators/csdid.py` L533：
```python
model=ModelInfo(
    command="csdid",
    estimator_family="csdid",
    vcetype="cluster",
    cluster_var=None,
),
```
`fit()` 方法接受 `cluster` 参数但从未将其保存为实例属性，因此 `estat_*` 方法无法访问。

### 涉及文件
- `src/stataflow/estimators/csdid.py` (L533, L767)

### 影响评估
- **影响范围**: `csdid`
- **用户workaround**: 无
- **是否阻塞实际使用**: 否（结果数值正确，但元信息缺失）

### 修复建议
在 `fit()` 中将 `cluster` 保存为 `self.cluster_var`，并在所有 `estat_*` 和 `_make_result_schema` 中使用该值。
预计工作量：小（15分钟）。

---

## 问题 7：CSDID df_resid 使用 n_clust - 1，当 cluster 参数与 id 不一致时计数错误

### 问题摘要
- **严重度**: Major
- **问题类型**: 数学偏差

### 现象描述
`CSDID` 的 `_fit_reg` 和 `_fit_dr` 中 `self._n_clust = n_units`（L184, L446），即始终使用 `id` 变量的唯一值数作为聚类数，完全忽略用户传入的 `cluster` 参数。若用户指定 `cluster="state"`（state 数 < unit 数），`df_resid` 会被高估，标准误的 small-sample 调整也会错误。

### 根因分析
`src/stataflow/estimators/csdid.py` L184：
```python
self._n_clust = n_units
```
未根据 `cluster` 参数重新计算聚类数量。

### 涉及文件
- `src/stataflow/estimators/csdid.py` (L184, L446)

### 影响评估
- **影响范围**: `csdid`
- **用户workaround**: 无（必须保证 cluster 变量与 id 变量层级相同）
- **是否阻塞实际使用**: 否（大多数用户以 id 为 cluster）

### 修复建议
在 `fit()` 中：若 `cluster` 为 None，则 `self._n_clust = n_units`；否则 `self._n_clust = df[cluster].nunique()`。
预计工作量：小（15分钟）。

---

## 问题 8：did_imputation pretrends 联合检验未使用 cluster-robust 协方差矩阵

### 问题摘要
- **严重度**: Major
- **问题类型**: 数学偏差

### 现象描述
`DIDImputation` 的 `pretrends` 检验中，SE 和 F 统计量基于 `_fit_twfe_covariates` 返回的 `cov = sigma2 * xtx_inv`（L691），即同方差 OLS 协方差矩阵。然而当用户传入 `cluster` 参数时，主估计量的标准误是 cluster-robust 的，但 pretrend 的联合检验却仍使用同方差 VCE。这与 Stata `did_imputation, pretrends(N) cluster(var)` 的行为不一致（Stata 的 pretrend 检验同样使用 cluster-robust）。

### 根因分析
`src/stataflow/estimators/did_imputation.py` L685–691：
```python
sigma2 = np.dot(resid, resid) / df_resid
xtx_inv = np.linalg.pinv(X.T @ X)
cov = sigma2 * xtx_inv
```
未根据 `cluster` 参数计算 cluster-robust 协方差矩阵。

### 涉及文件
- `src/stataflow/estimators/did_imputation.py` (L685–691, L449–461)

### 影响评估
- **影响范围**: `did_imputation` + `pretrends`
- **用户workaround**: 无
- **是否阻塞实际使用**: 否（pretrend p 值可能偏差，但不影响主估计量）

### 修复建议
在 `_fit_twfe_covariates` 中增加 `cluster` 参数支持，当 `cluster` 不为 None 时计算 cluster-robust VCE（CR1 或 CR2）。
预计工作量：中（3–4小时）。

---

## 问题 9：did_imputation autosample=False 时 controls/unitcontrols 可能导致不可 impute 但未被检测

### 问题摘要
- **严重度**: Major
- **问题类型**: 边界case / 数学偏差

### 现象描述
`_can_impute` 的判定仅检查 unit/time 是否在 control 样本中出现过（L221–226）。但当使用 `unitcontrols` 时，每个 unit 需要足够多的 control 观测才能估计 unit-specific slope；当使用 `timecontrols` 时，每个 time 也需要足够多的 control 观测。当前检查无法捕获“存在但 rank 不足”的情况，导致后续 `RuntimeError` 或错误的 Y0 预测。

此外，`unitcontrols`/`timecontrols` 的共线性检查完全缺失——仅 `controls` 有共线性检查（L621–627）。

### 根因分析
`src/stataflow/estimators/did_imputation.py` L221–226：
```python
unit_has_control = df.loc[control_mask, self.id_var].unique()
time_has_control = df.loc[control_mask, self.time_var].unique()
df["_can_impute"] = (
    df[self.id_var].isin(unit_has_control)
    & df[self.time_var].isin(time_has_control)
).astype(int)
```
未考虑 `unitcontrols` 引入的 rank 要求。

### 涉及文件
- `src/stataflow/estimators/did_imputation.py` (L221–226, L621–627)

### 影响评估
- **影响范围**: `did_imputation` + controls
- **用户workaround**: 始终使用 `autosample=True`
- **是否阻塞实际使用**: 否（有 workaround）

### 修复建议
1. 对 `unitcontrols`/`timecontrols` 增加共线性检查；
2. 改进 `_can_impute`：统计每个 unit/time 的 control 观测数，若少于参数个数+1 则标记为不可 impute。
预计工作量：中（3–4小时）。

---

## 问题 10：eventstudyinteract 不支持 weights 和 covariates，与 Stata 命令差距大

### 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失 / 与Stata差异

### 现象描述
Stata `eventstudyinteract` 支持 `[weight=var]` 和协变量（`controls()` / `absorb()` 之外）。Python 实现完全不支持权重，也不支持在 IW 回归中加入额外协变量。这导致：
1. 用户无法复现使用 `aweight`/`pweight` 的 Stata 结果；
2. 缺少协变量控制时，估计量可能不一致（若协变量与处理相关）。

### 根因分析
`EventStudyInteract.fit()` 的签名中只有 `vce`、`cluster`、`alpha`，无 `weights` 或 `covariates` 参数。wrapper 层同样未暴露这些参数。

### 涉及文件
- `src/stataflow/estimators/eventstudyinteract.py`
- `src/stataflow/compat/stata/did.py`

### 影响评估
- **影响范围**: `eventstudyinteract`
- **用户workaround**: 手动在 Y 和 X 上回归出残差再传入（复杂且 SE 不正确）
- **是否阻塞实际使用**: 否

### 修复建议
在 `fit()` 中增加 `weights` 参数，在 Step 1（cohort share）和 Step 3（interaction regression）中引入加权最小二乘。
预计工作量：中（4–6小时）。

---

## 问题 11：csdid estat_pretrend() 返回 dict 而非 ResultSchema，破坏 API 一致性

### 问题摘要
- **严重度**: Major
- **问题类型**: API设计缺陷

### 现象描述
`csdid()` wrapper 对 `aggtype="pretrend"` 返回 `model.estat(aggtype="pretrend")`，而 `estat_pretrend()` 返回一个 `dict`（`{"f_stat": ..., "p_value": ..., "df": ...}`）。这与 `aggtype="event"/"simple"/"group"/"calendar"` 返回的 `ResultSchema` 类型不一致，导致下游代码无法统一处理。

### 根因分析
`src/stataflow/estimators/csdid.py` L702–733：
```python
def estat_pretrend(self):
    ...
    return {"f_stat": f_stat, "p_value": p_value, "df": df}
```

### 涉及文件
- `src/stataflow/estimators/csdid.py` (L702–733)

### 影响评估
- **影响范围**: `csdid`
- **用户workaround**: 调用方手动判断返回类型
- **是否阻塞实际使用**: 否

### 修复建议
将 `estat_pretrend` 改为返回 `ResultSchema`，系数行为 pretrend F 统计量（或作为 `diagnostics` 附加到默认 event ResultSchema 上）。
预计工作量：小（1小时）。

---

## 问题 12：did_imputation wrapper 返回 ResultSchema 但 saveestimates/saveweights 存于 model 局部变量，用户无法访问

### 问题摘要
- **严重度**: Major
- **问题类型**: API设计缺陷

### 现象描述
`did_imputation()` wrapper 在内部创建 `model = DIDImputation(...)`，调用 `model.fit(...)` 后返回 `ResultSchema`。若用户传入 `saveestimates="effect"` 或 `saveweights=True`，这些结果存储在 `model.saveestimates_` / `model.saveweights_` 上，但 `model` 是局部变量，wrapper 返回后就被垃圾回收，用户完全无法访问保存的估计值和权重。

### 最小复现代码
```python
res = did_imputation(df, ..., saveestimates="effect", saveweights=True)
# res 是 ResultSchema，没有 saveestimates_ 属性
# 无法获取 imputation weights
```

### 根因分析
`src/stataflow/compat/stata/did.py` L41–63：
```python
model = DIDImputation(...)
return model.fit(...)
```
未返回 model 实例。

### 涉及文件
- `src/stataflow/compat/stata/did.py` (L41–63)

### 影响评估
- **影响范围**: `did_imputation`
- **用户workaround**: 直接使用 `DIDImputation` 类
- **是否阻塞实际使用**: 否（有 workaround）

### 修复建议
与问题 1 一致：wrapper 应返回包含 model 实例和 result 的复合对象，或至少暴露 model。
预计工作量：小（与问题 1 一并修复）。

---

## 问题 13：csdid() 不支持 notyet 参数，用户无法强制使用 not-yet-treated 控制组

### 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失

### 现象描述
Stata `csdid` 的 `notyet` 选项允许用户在存在 never-treated 组时，仍强制使用 not-yet-treated 作为控制组。这在某些研究设计中是必要的（如 never-treated 组与 treated 组不可比）。Python 实现中 `_fit_reg` 自动选择控制组策略，但用户无法覆盖。

### 根因分析
`src/stataflow/estimators/csdid.py` L98–107 自动选择逻辑：
```python
has_never_treated = (df[ft] == 0).any()
...
if has_never_treated:
    control_mask = df[ft] == 0
else:
    control_mask = df[ft] > max(g, t)
```
无 `notyet` 参数介入。

### 涉及文件
- `src/stataflow/estimators/csdid.py` (L98–107)
- `src/stataflow/compat/stata/did.py`

### 影响评估
- **影响范围**: `csdid`
- **用户workaround**: 手动从数据中删除 never-treated 组后再运行
- **是否阻塞实际使用**: 否（有 workaround，但极不便利）

### 修复建议
在 `CSDID.fit()` 和 `csdid()` 中增加 `notyet: bool = False` 参数。
预计工作量：小（30分钟）。

---

## 问题 14：csdid estat_pretrend() 对奇异协方差矩阵使用 pinv 但无警告

### 问题摘要
- **严重度**: Minor
- **问题类型**: 数学偏差 / 鲁棒性

### 现象描述
`estat_pretrend()` 在协方差矩阵奇异时回退到 `np.linalg.pinv`（L724–725），但用户不会收到任何警告。使用伪逆会降低检验功效，且用户可能误以为 pre-trend 系数是独立的。Stata 在类似情况下通常会给出 rank-deficiency 提示。

### 根因分析
`src/stataflow/estimators/csdid.py` L720–725：
```python
try:
    inv_cov = np.linalg.inv(cov)
    wald = float(pre_est @ inv_cov @ pre_est)
except np.linalg.LinAlgError:
    inv_cov = np.linalg.pinv(cov)
    wald = float(pre_est @ inv_cov @ pre_est)
```
无警告输出。

### 涉及文件
- `src/stataflow/estimators/csdid.py` (L720–725)

### 影响评估
- **影响范围**: `csdid` pretrend 检验
- **用户workaround**: 无
- **是否阻塞实际使用**: 否

### 修复建议
在 `except` 分支中加入 `warnings.warn("Covariance matrix is singular; using pseudoinverse. Pretrend test may have reduced power.")`。
预计工作量：极小（5分钟）。

---

## 问题 15：eventstudyinteract auto-generation 在存在 gaps 时可能生成错误 dummy

### 问题摘要
- **严重度**: Minor
- **问题类型**: 边界case / 与Stata差异

### 现象描述
`eventstudyinteract` auto-generation 模式通过 `rel_time = df[time] - df[first_treat]` 计算相对时间。若面板存在 gaps（某些 unit 在某些 period 无观测），生成的 dummy 仍基于 `first_treat` 而非实际观测的 period。虽然缺失行在后续 screening 中被删除，但 never-treated 单位的 `rel_time` 被强制设为 `-1000`（L115），这假设了 `time` 变量不会取到 `-1000`。虽然极罕见，但这是一个魔术数字。

### 根因分析
`src/stataflow/compat/stata/did.py` L114–115：
```python
rel_time = df[time] - df[first_treat]
rel_time = rel_time.where(df[first_treat] > 0, -1000)
```

### 涉及文件
- `src/stataflow/compat/stata/did.py` (L114–126)

### 影响评估
- **影响范围**: `eventstudyinteract` auto-generation
- **用户workaround**: 使用预生成 `event_dummies`
- **是否阻塞实际使用**: 否

### 修复建议
使用 `pd.NA` 或 `np.nan` 而非魔术数字 `-1000`。
预计工作量：极小（5分钟）。

---

## 问题 16：did_imputation ResultSchema 中 cluster_var 在默认情况下为 None，与内部实际 cluster 变量不一致

### 问题摘要
- **严重度**: Minor
- **问题类型**: 输出正确性

### 现象描述
`did_imputation()` 的 `fit()` 方法在 `cluster=None` 时默认使用 `self.id_var` 作为 cluster 变量（L96–97），但返回的 `ResultSchema` 中 `cluster_var` 被设为 `None`（L486：`cluster_var=cluster if cluster else None`）。这使得结果对象声称无聚类，但实际计算了以 `id_var` 为聚类的标准误。

### 根因分析
`src/stataflow/estimators/did_imputation.py` L96–97, L486：
```python
if cluster is None:
    cluster = self.id_var
...
cluster_var=cluster if cluster else None,
```

### 涉及文件
- `src/stataflow/estimators/did_imputation.py` (L96–97, L486)

### 影响评估
- **影响范围**: `did_imputation`
- **用户workaround**: 无
- **是否阻塞实际使用**: 否

### 修复建议
将 `cluster_var` 设为实际使用的 cluster 变量名（即 `cluster` 在默认值设定后的值）。
预计工作量：极小（5分钟）。

---

## 问题 17：CSDID 的 _fit_reg 中 df.pivot 在重复 (uid, time) 时直接崩溃，无友好错误信息

### 问题摘要
- **严重度**: Minor
- **问题类型**: 边界case崩溃

### 现象描述
若输入数据中存在重复的单位-时间观测（例如重复横截面被错误地当作面板输入），`df.pivot(index=uid, columns=time, values=y)` 会抛出 `ValueError: Index contains duplicate entries, cannot reshape`。错误信息对普通用户不够友好，无法指出问题是数据中存在重复 `(id, time)`。

### 根因分析
`src/stataflow/estimators/csdid.py` L91：
```python
df_wide = df.pivot(index=uid, columns=time, values=y)
```

### 涉及文件
- `src/stataflow/estimators/csdid.py` (L91)

### 影响评估
- **影响范围**: `csdid`
- **用户workaround**: 手动去重
- **是否阻塞实际使用**: 否

### 修复建议
在 `pivot` 前检查重复：
```python
dups = df[[uid, time]].duplicated().any()
if dups:
    raise ValueError(f"Duplicate (id, time) pairs found in data. CSDID requires panel data with unique (id, time).")
```
预计工作量：极小（10分钟）。

---

## 问题 18：did_imputation nobs 与 df_resid 使用不同的样本量定义，内部不一致

### 问题摘要
- **严重度**: Minor
- **问题类型**: 输出正确性

### 现象描述
`DIDImputation.fit()` 中，`nobs_all` 是 effective sample（经 autosample 调整后），但 `df_resid` 计算使用的 `nobs` 是原始 control 观测数 `int((df["_D"] == 0).sum())`（L479）。这导致当 `autosample=True` 且大量观测被删除时，`df_resid` 与 `nobs_all` 不匹配。

### 根因分析
`src/stataflow/estimators/did_imputation.py` L479, L496：
```python
nobs = int((df["_D"] == 0).sum())
...
df_resid=float(nobs - 1) if cluster else float(nobs),
```

### 涉及文件
- `src/stataflow/estimators/did_imputation.py` (L479, L496)

### 影响评估
- **影响范围**: `did_imputation`
- **用户workaround**: 无
- **是否阻塞实际使用**: 否

### 修复建议
统一使用 `nobs_all` 作为 `df_resid` 的分母基础。
预计工作量：极小（5分钟）。

---

# 汇总表格

| 序号 | 问题简述 | 严重度 | 类型 | 阻塞使用 | 预计工作量 |
|------|---------|--------|------|---------|-----------|
| 1 | csdid wrapper 返回 ResultSchema 而非 model，阻断二次分析 | Blocker | API设计缺陷 | 是 | 小 |
| 2 | csdid **kwargs 硬拒绝所有 Stata 合法参数 | Blocker | 参数缺失/硬拒绝 | 是 | 中 |
| 3 | csdid drimp 无 never-treated 时硬崩溃 | Critical | 边界case崩溃 | 是 | 中 |
| 4 | did_imputation allhorizons 完全未生效 | Critical | 数学偏差 | 是 | 小 |
| 5 | CSDID 面板不平衡导致 NaN 静默传播 | Critical | 边界case/数学偏差 | 是 | 小 |
| 6 | CSDID cluster_var 始终为 None | Major | 输出正确性 | 否 | 极小 |
| 7 | CSDID df_resid 忽略 cluster 参数 | Major | 数学偏差 | 否 | 极小 |
| 8 | did_imputation pretrends 未使用 cluster-robust VCE | Major | 数学偏差 | 否 | 中 |
| 9 | did_imputation controls 缺乏 rank 不足检测 | Major | 边界case/数学偏差 | 否 | 中 |
| 10 | eventstudyinteract 不支持 weights/covariates | Major | 参数缺失 | 否 | 中 |
| 11 | csdid estat_pretrend 返回 dict 破坏一致性 | Major | API设计缺陷 | 否 | 小 |
| 12 | did_imputation wrapper 无法访问 saveestimates/saveweights | Major | API设计缺陷 | 否 | 小 |
| 13 | csdid 不支持 notyet 参数 | Major | 参数缺失 | 否 | 小 |
| 14 | csdid pretrend 奇异矩阵无警告 | Minor | 数学偏差 | 否 | 极小 |
| 15 | eventstudyinteract auto-gen 使用魔术数字 | Minor | 边界case | 否 | 极小 |
| 16 | did_imputation cluster_var 默认值与实际不一致 | Minor | 输出正确性 | 否 | 极小 |
| 17 | CSDID pivot 重复观测错误信息不友好 | Minor | 边界case | 否 | 极小 |
| 18 | did_imputation nobs/df_resid 定义不一致 | Minor | 输出正确性 | 否 | 极小 |

### 按严重度统计
- **Blocker**: 2 项
- **Critical**: 3 项
- **Major**: 8 项
- **Minor**: 5 项
- **总计**: 18 项

### 按类型统计
- **API设计缺陷**: 4 项
- **参数缺失/硬拒绝**: 4 项
- **边界case崩溃/数学偏差**: 7 项
- **输出正确性**: 3 项
