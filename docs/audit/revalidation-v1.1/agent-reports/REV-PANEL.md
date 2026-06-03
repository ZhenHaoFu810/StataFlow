# REV-PANEL — Panel / FE / HDFE 命令族源码深度审查报告

**审查范围**: `fe.py`, `absorbing_ols.py`, `linear.py`, `hdfe.py`, `factor_variables.py`, 及相关支持矩阵文档  
**审查版本**: stataflow 1.0.0  
**审查日期**: 2026-06-03  
**审查Agent**: 子Agent-源码审查  

---

# REV-PANEL-01

## 元信息
- **命令**: `reghdfe`, `areg` (MAP路径)
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Blocker
- **问题类型**: 边界case崩溃 / 未定义变量

## 现象描述
`AbsorbingOLS` 的 MAP (Method of Alternating Projections) 迭代路径在**任何**场景下都会直接崩溃：
1. `_fit_map` 内部引用了未定义的 `stats` 变量（`stats.t.cdf`, `stats.t.ppf`, `stats.f.cdf`）。
2. `fit()` 方法在 MAP 分支结束后，试图将局部变量 `beta_full`、`cov_full`、`T` 赋给 `self`，但这三个变量在 MAP 分支中**从未被定义**为局部变量，导致 `UnboundLocalError`。

因此，只要触发 MAP 路径（`technique="map"`、自动选择 `>5000` FE levels、或 `vce="dkraay"`），模型必然抛出异常，无法返回任何结果。

## 最小复现代码
```python
import numpy as np
import pandas as pd
from stataflow.estimators.absorbing_ols import AbsorbingOLS

# 场景A: dkraay 强制 MAP
np.random.seed(99999)
N, T = 50, 10
n = N * T
firm_id = np.repeat(np.arange(N), T)
year = np.tile(np.arange(T), N)
x = np.random.normal(0, 1, n)
y = 1 + 0.5 * x + np.random.normal(0, 1, n)
df = pd.DataFrame({"y": y, "x": x, "firm_id": firm_id, "year": year})

model = AbsorbingOLS(data=df, y="y", x=["x"], absorb=["firm_id", "year"], add_constant=True)
model.fit(vce="dkraay", timevar="year")
# NameError: name 'stats' is not defined

# 场景B: 大规模 FE 自动触发 MAP
np.random.seed(42)
N = 6000
fe = np.repeat(np.arange(N), 2)
x = np.random.normal(0, 1, N * 2)
y = 1 + 0.5 * x + np.random.normal(0, 1, N * 2)
df2 = pd.DataFrame({"y": y, "x": x, "fe": fe})
model2 = AbsorbingOLS(data=df2, y="y", x=["x"], absorb=["fe"], add_constant=True)
model2.fit(vce="ols")
# NameError: name 'stats' is not defined
```

## 根因分析
- `absorbing_ols.py` 顶部只做了 `from scipy.stats import t as t_dist, f as f_dist`，**没有** `import scipy.stats as stats`。
- `_fit_map` 的作者在编写 MAP 路径的 p-value / F-stat 计算时，误用了 `stats.t.cdf` / `stats.f.cdf`（LSDV 路径正确使用了 `t_dist` / `f_dist`）。
- `fit()` 方法的末尾（line 1537–1544）有一段**共享代码**，试图把 `beta_full`、`cov_full`、`T` 写回实例属性。LSDV 分支定义了这三个局部变量，但 MAP 分支只把它们打包进 `mr` 字典返回，没有在 `fit()` 的局部作用域中定义。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 1101: `p_values = 2 * (1 - stats.t.cdf(...))`
  - line 1102: `t_crit = stats.t.ppf(...)`
  - line 1113: `f_pvalue = 1 - stats.f.cdf(...)`
  - line 1122: `f_pvalue = 1 - stats.f.cdf(...)`
  - line 1539: `self._beta_full = beta_full` (UnboundLocalError)
  - line 1540: `self._cov_full = cov_full`
  - line 1541: `self._T = T`

## 影响评估
- **影响范围**: 命令族（所有使用 MAP 路径的命令：`reghdfe`、`areg` 大规模场景、`vce(dkraay)`）
- **用户workaround**: 无。即使手动指定 `technique="lsdv"`，`vce="dkraay"` 仍会强制覆盖为 `use_map=True`。
- **是否阻塞实际使用**: 是。Wave 12 核心能力（>10K FE）完全不可用。

## 修复建议
1. 在 `_fit_map` 中把 `stats.t.cdf` 替换为 `t_dist.cdf`，`stats.t.ppf` 替换为 `t_dist.ppf`，`stats.f.cdf` 替换为 `f_dist.cdf`。
2. 在 `fit()` 的 MAP 分支末尾，补充提取 `beta_full`、`cov_full`、`T`（或直接从 `_fit_map` 设置的实例属性中读取，避免重复赋值）。
3. 添加一条 golden test，强制使用 `technique="map"` 并覆盖 `>5000` 阈值，防止回归。

## 关联项
- `docs/command-support-matrix/reghdfe.md` — Wave 12 MAP 能力声明
- `tests/golden/test_w12_dkraay_basic.py` — 当前因该错误无法通过

---

# REV-PANEL-02

## 元信息
- **命令**: `reghdfe`, `areg` (MAP路径)
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 边界case处理不足 / 静默错误结果

## 现象描述
MAP 内核 `_map_partial_out` 在达到 `max_iter` 仍未收敛时，**不会发出任何警告**，直接返回当前迭代结果。注释写着 "warn but continue"，但代码体只有 `pass`。

对于极端数据（非常稀疏的 FE、弱连通的多-way FE），Kaczmarz 迭代可能收敛极慢。用户在不知情的情况下会拿到未收敛的系数，导致与 LSDV / Stata 的结果出现系统性偏差。

## 最小复现代码
```python
# 构造一个 MAP 收敛极慢的 2-way FE 实例（需先修复 REV-PANEL-01 才能观察到）
import numpy as np
import pandas as pd
from stataflow.estimators.absorbing_ols import AbsorbingOLS

np.random.seed(1)
# 每个 obs 几乎独占一个组合，导致投影顺序极度病态
n = 2000
fe1 = np.arange(n) % 1000
fe2 = np.arange(n) // 1000
x = np.random.normal(0, 1, n)
y = 1 + 0.5 * x + np.random.normal(0, 1, n)
df = pd.DataFrame({"y": y, "x": x, "fe1": fe1, "fe2": fe2})

model = AbsorbingOLS(data=df, y="y", x=["x"], absorb=["fe1", "fe2"], technique="map")
# 将 max_iter 调小以强制触发未收敛（需手动 monkey-patch）
model._map_partial_out = lambda y, X, fe_info, max_iter=5, tol=1e-12, accel_freq=1_000_000: \
    AbsorbingOLS._map_partial_out(model, y, X, fe_info, max_iter=5, tol=tol, accel_freq=accel_freq)

result = model.fit(vce="ols")
# 无警告，结果静默返回
```

## 根因分析
- `absorbing_ols.py` line 397–399 的 `for...else` 结构中，`else` 分支仅有 `pass`，未调用 `warnings.warn`。
- 缺少收敛状态外显机制（如返回 `converged` flag），`fit()` 上层无法在 `ResultSchema.diagnostics.warnings` 中注入未收敛提示。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 368–399: `_map_partial_out` 的迭代与收敛检查

## 影响评估
- **影响范围**: MAP 路径所有命令
- **用户workaround**: 无。用户无法得知迭代是否收敛。
- **是否阻塞实际使用**: 是（可能给出错误结果而不自知）

## 修复建议
1. 在 `else` 分支中发出 `warnings.warn("MAP did not converge within max_iter ...", RuntimeWarning)`。
2. 将收敛标志通过 `mr` 字典返回，`fit()` 将其写入 `result.diagnostics.warnings`。
3. 考虑暴露 `max_iter` 和 `tol` 到 `reghdfe()` / `AbsorbingOLS.__init__`。

## 关联项
- `docs/research/wave12-map-lsmr.md` — MAP 收敛性研究文档

---

# REV-PANEL-03

## 元信息
- **命令**: `reghdfe` (LSDV + slopes)
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 边界case处理不足 / 数学偏差

## 现象描述
在 LSDV 路径下，当 `absorb` 包含 slope 语法（如 `firm_id##c.time`）且 `savefe=True` 时，`save_fixed_effects()` 方法**不区分 intercept dummy 与 slope interaction dummy**，导致 slope 系数被错误地（或静默地）丢弃，而 intercept alpha 数组可能接收到错误位置的系数。

具体表现：
- `_dummy_info` 中 slope dummies 的 `column_types` 标记为 `("slope", var)`，但 `save_fixed_effects()` 完全未读取该字段。
- 对于 `firm_id##c.time`，slope dummies 的 reduced indices 被遍历后，因 `level_idx` 越界而被 `if 0 <= level_idx < num_levels` 跳过，最终返回的 `alphas` 只包含 intercept 部分，slope 信息彻底丢失。

## 最小复现代码
```python
import numpy as np
import pandas as pd
from stataflow.estimators.absorbing_ols import AbsorbingOLS

np.random.seed(88888)
N, T = 50, 10
n = N * T
firm_id = np.repeat(np.arange(N), T)
time = np.tile(np.arange(T), N)
x = np.random.normal(0, 1, n)
firm_fe = np.repeat(np.random.normal(0, 2, N), T)
firm_slope = np.repeat(np.random.normal(0, 0.5, N), T)
eps = np.random.normal(0, 1, n)
y = 1 + 0.5 * x + firm_fe + firm_slope * time + eps

df = pd.DataFrame({"y": y, "x": x, "firm_id": firm_id, "time": time})
model = AbsorbingOLS(data=df, y="y", x=["x"], absorb="firm_id##c.time", add_constant=True)
result = model.fit(vce="ols", savefe=True)

# 查看 savefe 输出
fe = result.fixed_effects["firm_id"]
print(fe.head())
# 只有 intercept alphas，slope 系数完全丢失；且 alphas 中可能混入错误值
```

## 根因分析
- `save_fixed_effects()`（line 1608–1653）假设 `_dummy_info` 中只有 intercept dummies。
- Slope absorption 在 LSDV 构建阶段为每个 slope 变量额外创建了交互 dummy 列（line 804–824），但 `save_fixed_effects()` 没有根据 `column_types` 做分支处理。
- 此外，`savefe` 在 MAP 路径会正确抛出 `NotImplementedError`，但在 LSDV + slopes 场景下既不报错也不正确，属于最危险的“静默失败”。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 1608–1653: `save_fixed_effects()`
  - line 804–824: slope dummy 构建逻辑

## 影响评估
- **影响范围**: `reghdfe` LSDV + slope absorption + `savefe=True`
- **用户workaround**: 无。用户无法从返回的 dict 中恢复 slope FE。
- **是否阻塞实际使用**: 是（给出不完整/错误的 FE 估计）

## 修复建议
1. 在 `save_fixed_effects()` 中读取 `column_types`，对 `("intercept",)` 和 `("slope", var)` 分别处理。
2. 返回结构需要扩展：当前返回 `dict[str, pd.Series]`，slope 场景应返回 `dict[str, dict]` 或新增 `result.fixed_effects_slopes` 字段（需 ADR）。
3. 在修复前，应在 LSDV + slopes + savefe 场景下也抛出 `NotImplementedError`，避免静默错误。

## 关联项
- `tests/golden/test_w12_slopes_basic.py` — 仅验证系数，未覆盖 savefe
- `docs/command-support-matrix/reghdfe.md` — savefe 与 MAP 不兼容的说明

---

# REV-PANEL-04

## 元信息
- **命令**: `reghdfe`
- **命令族**: Panel / FE / HDFE
- **审查类型**: API设计缺陷
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失 / API设计缺陷

## 现象描述
`reghdfe()` wrapper 的函数签名中**完全缺失 `technique` 参数**。底层 `AbsorbingOLS` 已支持 `technique="lsdv" / "map" / "auto"`，但 wrapper 没有暴露该参数，导致：
- 用户无法手动强制 LSDV（例如内存充裕时希望获得与 Stata 完全一致的结果）。
- 用户无法手动强制 MAP（例如调试收敛行为）。
- 相关参数 `max_iter`、`tol`、`accel_freq` 同样未暴露。

此外，`reghdfe()` wrapper 也未暴露 `aweight` / `fweight` / `pweight` 参数，与 Stata 原生 `reghdfe` 的高频用法存在差距。

## 最小复现代码
```python
from stataflow.compat.stata import reghdfe
import inspect

sig = inspect.signature(reghdfe)
print(list(sig.parameters.keys()))
# ['data', 'y', 'x', 'absorb', 'vce', 'cluster', 'missing', 'keepsingletons', 'noconstant', 'savefe', 'timevar', 'kwargs']
# technique / max_iter / tol / aweight 均不存在
```

## 根因分析
- `src/stataflow/compat/stata/hdfe.py` line 11–25 的 `reghdfe()` 签名未包含 `technique` 等参数，也未将其传递给 `AbsorbingOLS(...)`。
- `AbsorbingOLS.__init__` 虽接受 `technique`，但 wrapper 未传递；`max_iter`/`tol` 甚至未进入 `AbsorbingOLS.__init__`（仅在 `_map_partial_out` 中硬编码）。

## 涉及文件
- `src/stataflow/compat/stata/hdfe.py`
  - line 11–25: `reghdfe()` 签名与参数透传
- `src/stataflow/estimators/absorbing_ols.py`
  - line 49–59: `AbsorbingOLS.__init__` 未暴露 max_iter / tol

## 影响评估
- **影响范围**: `reghdfe()` wrapper 用户
- **用户workaround**: 直接使用 `AbsorbingOLS` 类，但无法通过 Stata-compatible wrapper 控制。
- **是否阻塞实际使用**: 否，但严重降低大规模 FE 场景的可用性。

## 修复建议
1. 在 `reghdfe()` 签名中增加 `technique: str = "auto"`，并透传给 `AbsorbingOLS`。
2. 在 `AbsorbingOLS.__init__` 中增加 `max_iter: int = 10000`、`tol: float = 1e-12`，并透传给 `_map_partial_out`。
3. 增加 `aweight` 参数（需同步在 `AbsorbingOLS` 中实现权重逻辑，工作量较大，可拆分为独立 backlog）。

## 关联项
- `docs/command-support-matrix/reghdfe.md` — 支持矩阵已声明 technique="map"/"auto"

---

# REV-PANEL-05

## 元信息
- **命令**: `areg`
- **命令族**: Panel / FE / HDFE
- **审查类型**: API设计缺陷 / 边界case处理不足
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失 / 边界case处理不足

## 现象描述
`areg()` wrapper 存在两项与 Stata 17 `areg` 不一致的设计缺陷：
1. **静默删除 singleton 观测**：Stata 的 `areg` **不**删除 singleton，但 wrapper 未传递 `drop_singletons=False`，继承了 `AbsorbingOLS` 的默认值 `True`。用户在使用 `areg()` 时样本量可能 silently 减少。
2. **不支持 `noconstant`**：Stata `areg` 支持 `noconstant` 选项，但 wrapper 硬编码 `add_constant=True`，且未在签名中暴露该参数。

## 最小复现代码
```python
import numpy as np
import pandas as pd
from stataflow.compat.stata.linear import areg

np.random.seed(1)
fe = np.array([1, 1, 2, 3])  # group 3 只有 1 个 obs（singleton）
x = np.random.normal(0, 1, 4)
y = 1 + 0.5 * x + np.random.normal(0, 1, 4)
df = pd.DataFrame({"y": y, "x": x, "fe": fe})

result = areg(df, y="y", x=["x"], absorb="fe")
print(result.sample.nobs)  # 输出 3，singleton 被静默删除

# noconstant 不被支持
# areg(df, y="y", x=["x"], absorb="fe", noconstant=True)
# TypeError: areg() got an unexpected keyword argument 'noconstant'
```

## 根因分析
- `src/stataflow/compat/stata/linear.py` line 117–124：`areg()` 创建 `AbsorbingOLS(..., add_constant=True, missing=missing)`，未指定 `drop_singletons=False`，也未接受 `noconstant`。

## 涉及文件
- `src/stataflow/compat/stata/linear.py`
  - line 117–124: `areg()` wrapper 实现

## 影响评估
- **影响范围**: `areg()` wrapper 用户
- **用户workaround**: 直接使用 `AbsorbingOLS(..., drop_singletons=False)`，但失去 Stata-compatible 语义。
- **是否阻塞实际使用**: 否，但导致与 Stata 行为不一致，影响复现性。

## 修复建议
1. `areg()` 中显式传入 `drop_singletons=False`。
2. `areg()` 签名增加 `noconstant: bool = False`，并改为 `add_constant=not noconstant`。
3. 补充 golden test：比较 `areg(...)` 与 Stata `areg, absorb(fe)` 的样本量一致性。

## 关联项
- `docs/command-support-matrix/areg.md` — 未提及 singleton 处理差异

---

# REV-PANEL-06

## 元信息
- **命令**: `xtreg, fe`
- **命令族**: Panel / FE / HDFE
- **审查类型**: API设计缺陷
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: API设计缺陷 / 参数缺失

## 现象描述
`xtreg_fe()` wrapper 存在三项偏差：
1. **默认不报告 `_cons`**：`FixedEffectsOLS` 默认 `add_constant=False`，但 wrapper 未暴露该参数。Stata `xtreg, fe` **默认报告** `_cons`（grand mean of entity effects）。通过 wrapper 调用的用户默认看不到常数项，与 Stata 输出不一致。
2. **不支持 `robust` VCE**：`FixedEffectsOLS.fit()` 硬拒绝 `vce="robust"`（仅允许 `"ols"` / `"cluster"`）。Stata `xtreg, fe robust` 是常用语法。
3. **不支持 `noconstant`**：wrapper 签名未暴露 `noconstant`。

## 最小复现代码
```python
import numpy as np
import pandas as pd
from stataflow.compat.stata.linear import xtreg_fe

np.random.seed(1)
entity = np.repeat(np.arange(10), 5)
x = np.random.normal(0, 1, 50)
y = 1 + 0.5 * x + np.random.normal(0, 1, 50)
df = pd.DataFrame({"y": y, "x": x, "entity": entity})

# 1) 默认无 _cons
result = xtreg_fe(df, y="y", x=["x"], fe="entity")
print([c.name for c in result.coefficients])  # ['x']，缺少 '_cons'

# 2) robust 被拒绝
# xtreg_fe(df, y="y", x=["x"], fe="entity", vce="robust")
# ValueError: vce='robust' not supported for FE. Use 'ols' or 'cluster'.
```

## 根因分析
- `linear.py` line 51–84：`xtreg_fe()` 未传递 `add_constant`，继承底层默认值 `False`。
- `fe.py` line 190–191：`fit()` 中 `vce not in ("ols", "cluster")` 硬拒绝 `robust`。

## 涉及文件
- `src/stataflow/compat/stata/linear.py`
  - line 51–84: `xtreg_fe()` wrapper
- `src/stataflow/estimators/fe.py`
  - line 190–191: `fit()` vce 校验

## 影响评估
- **影响范围**: `xtreg_fe()` wrapper 用户
- **用户workaround**: 直接使用 `FixedEffectsOLS(..., add_constant=True)`，但 `robust` 完全无 workaround。
- **是否阻塞实际使用**: `robust` 缺失对实际使用有较大影响；`_cons` 默认缺失影响输出一致性。

## 修复建议
1. `xtreg_fe()` 默认改为 `add_constant=True`（或暴露 `noconstant` 参数）。
2. 在 `fe.py` 中实现 HC1 robust VCE（增量工作量小，可复用 `AbsorbingOLS` 的 robust 逻辑）。
3. 补充 golden test 验证 `xtreg, fe robust` 与 Stata 的一致性。

## 关联项
- `docs/command-support-matrix/xtreg-fe.md` — 支持矩阵未列出 robust

---

# REV-PANEL-07

## 元信息
- **命令**: `reghdfe`
- **命令族**: Panel / FE / HDFE
- **审查类型**: API设计缺陷
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: API设计缺陷

## 现象描述
`parse_absorb()` 声称支持 tuple 形式的 slope 语法（如 `[("firm_id", "time_trend")]` 或 `[("firm_id", ["x1", "x2"])]`），但实际实现会把 tuple 直接 `str()` 化成字符串，导致变量名错误，最终引发 `KeyError`。

## 最小复现代码
```python
from stataflow.compat.stata.factor_variables import parse_absorb

# 文档声称支持的 tuple API
print(parse_absorb([("firm_id", "time_trend")]))
# [AbsorbSpec(var="('firm_id', 'time_trend')", slopes=[], has_intercept=True)]
# 变量名变成了 Python 的 tuple 字符串表示，后续会 KeyError

print(parse_absorb([("firm_id", ["x1", "x2"])]))
# [AbsorbSpec(var="('firm_id', ['x1', 'x2'])", slopes=[], has_intercept=True)]
```

## 根因分析
- `factor_variables.py` line 417–420：当 `value` 为 list 时，执行 `raw_terms = [str(v) for v in value]`。若 `v` 是 tuple，则变成 `str(tuple)`，后续 `_parse_slope_term` 无法匹配任何正则，被当作 plain variable 处理。

## 涉及文件
- `src/stataflow/compat/stata/factor_variables.py`
  - line 407–420: `parse_absorb()`

## 影响评估
- **影响范围**: `reghdfe()` 使用 tuple API 的用户
- **用户workaround**: 使用字符串语法 `absorb="firm_id##c.time"` 或 `absorb=["firm_id##c.time"]`。
- **是否阻塞实际使用**: 否，但文档与实现不一致。

## 修复建议
1. 在 `parse_absorb()` 中检测 list 元素类型：若为 `AbsorbSpec` 直接透传；若为 tuple，按 `(var, slopes..., has_intercept)` 解析。
2. 若不打算支持 tuple，应从支持矩阵和 docstring 中删除相关描述，避免误导。

## 关联项
- `docs/command-support-matrix/reghdfe.md` — absorb 参数文档

---

# REV-PANEL-08

## 元信息
- **命令**: `reghdfe`, `areg`
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 边界case处理不足

## 现象描述
`_drop_singletons()` 仅基于 `absorb_vars` 的原始出现次数判断 singleton，**完全不考虑 slope 变量**。对于 slope absorption（如 `absorb(firm_id##c.time)`），若某 firm 有 2 个观测但它们的 `time` 值完全相同，则该 firm 的 slope 参数实际上不可识别，但不会被当作 singleton 处理。这可能导致后续 LSDV 矩阵奇异或 df 计算错误。

## 最小复现代码
```python
import numpy as np
import pandas as pd
from stataflow.estimators.absorbing_ols import AbsorbingOLS

# firm 0 有两个观测，但 time 完全相同
df = pd.DataFrame({
    "y": [1.0, 2.0, 3.0],
    "x": [1.0, 2.0, 3.0],
    "firm": [0, 0, 1],
    "time": [5, 5, 10],  # firm 0 的 time 无 within-group 变异
})

model = AbsorbingOLS(data=df, y="y", x=["x"], absorb="firm##c.time", add_constant=True)
result = model.fit(vce="ols")
# 可能通过（lstsq 兜底），但 df_a 和识别条件不正确
```

## 根因分析
- `absorbing_ols.py` line 130–157：仅对 `self.absorb_vars` 做 `value_counts()`，未检查 `spec.slopes` 在每个组内的变异度。
- Stata `reghdfe` 的 singleton 判定基于 effective observation（即该组对某个参数是否有贡献），而非原始频数。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 130–157: `_drop_singletons()`

## 影响评估
- **影响范围**: `reghdfe` / `AbsorbingOLS` 使用 slope absorption 的场景
- **用户workaround**: 无自动手段；用户需手动预处理数据保证 slope 变量在每组内有变异。
- **是否阻塞实际使用**: 否，但可能导致不可识别的 slope 参数未被剔除。

## 修复建议
1. 在 `_drop_singletons()` 中，对带有 slopes 的 FE group，检查每组内 slope 矩阵 `[1, s1, s2, ...]` 的秩。若秩亏（如所有 slope 值相同），则将该组所有观测标记为待删除。
2. 或者将 slope-specific singleton 检测后移至 `_prepare_data` 的 dummy 构建阶段，利用 `detect_collinear_columns` 自动处理。

## 关联项
- `tests/golden/test_w12_slopes_zero.py` — 仅测试零斜率组不报错，未测试 singleton 识别

---

# REV-PANEL-09

## 元信息
- **命令**: `reghdfe`, `areg` (MAP路径)
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 数学偏差 / 边界case处理不足

## 现象描述
在 MAP 路径下，`predict(type="xbd")`、`predict(type="d")`、`predict(type="residuals")` 的结果**不包含 absorbed FE 的贡献**。原因是 `_fit_map` 将 `self._design_matrix` 设为仅含 `[1, X_partial]`（或仅 `X_partial`），而非完整的 LSDV 设计矩阵（含 FE dummies）。

具体：
- `type="xbd"` 返回 `_cons + X_partial @ beta_x`，缺失 FE alpha。
- `type="d"` 因此接近 0，完全错误。
- `type="residuals"` 在数值上可能近似正确（因为 `y_partial` 已去除了 FE），但 `type="xbd"` 和 `type="d"` 已严重失真。

## 最小复现代码
```python
# 需先修复 REV-PANEL-01 的 NameError 才能运行
import numpy as np
import pandas as pd
from stataflow.estimators.absorbing_ols import AbsorbingOLS

np.random.seed(42)
N = 6000
fe = np.repeat(np.arange(N), 2)
x = np.random.normal(0, 1, N * 2)
fe_effect = np.repeat(np.random.normal(0, 5, N), 2)
y = 1 + 0.5 * x + fe_effect + np.random.normal(0, 1, N * 2)
df = pd.DataFrame({"y": y, "x": x, "fe": fe})

model = AbsorbingOLS(data=df, y="y", x=["x"], absorb=["fe"], add_constant=True)
result = model.fit(vce="ols")  # 触发 MAP

xbd = model.predict(type="xbd")
d_pred = model.predict(type="d")
print("d mean:", np.mean(d_pred))  # 应接近 fe_effect 均值，实际接近 0
```

## 根因分析
- `_fit_map` line 1078–1084：`self._design_matrix = X_ols`，其中 `X_ols = np.column_stack([np.ones(n), X_partial])`。
- LSDV 路径的 `_design_matrix` 是完整的 `X_full`（含 FE dummies），因此 `predict("xbd")` 自然包含 FE。
- MAP 路径未存储 FE 投影信息到 `self._design_matrix`，导致 post-estimation 预测语义断裂。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 1078–1084: `_fit_map` 中 `_design_matrix` 的赋值
  - line 1551–1593: `predict()` 方法

## 影响评估
- **影响范围**: MAP 路径的所有 post-estimation 预测
- **用户workaround**: 无。MAP 路径下无法正确生成含 FE 的预测值。
- **是否阻塞实际使用**: 是（对于需要 `xbd` / `d` 预测的用户）。

## 修复建议
1. 在 `_fit_map` 中保存 `fe_cum`（各 FE 组的累计系数）到实例属性。
2. 在 `predict()` 中，若为 MAP 路径，利用 `fe_cum` 重构 FE 贡献：
   ```python
   fe_contrib = sum(fe_cum[0][g][levels[g], 0] for g in range(num_fe))
   ```
3. 或者将 MAP 路径的 `predict` 限制为仅支持 `"xb"` 和 `"residuals"`，对 `"xbd"` / `"d"` 抛出 `NotImplementedError`（短期兜底）。

## 关联项
- `docs/command-support-matrix/reghdfe.md` — predict 支持矩阵未区分 MAP/LSDV 路径差异

---

# REV-PANEL-10

## 元信息
- **命令**: `reghdfe`
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 边界case处理不足 / 用户体验缺陷

## 现象描述
当数据集规模很大、FE levels 众多，用户未指定 `technique="map"` 时，LSDV 路径会尝试构建 `N × sum(G_g)` 的稠密 dummy 矩阵。若内存不足，NumPy 直接抛出 `MemoryError`，没有任何提示引导用户切换到 MAP 路径。

## 根因分析
- `absorbing_ols.py` line 851–877：LSDV 矩阵构建通过 `np.column_stack(matrix_pieces)` 一次性完成，无 `try/except MemoryError` 捕获。
- 用户（尤其是不熟悉内部实现的用户）收到 `MemoryError` 后，无法从错误信息中得知应使用 `technique="map"`。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 851–877: LSDV dummy 矩阵构建

## 影响评估
- **影响范围**: 大规模面板数据的 LSDV 路径用户
- **用户workaround**: 直接调用 `AbsorbingOLS(..., technique="map")`（但 REV-PANEL-01 导致 MAP 目前也无法使用）。
- **是否阻塞实际使用**: 是（大规模场景下无清晰错误引导）。

## 修复建议
1. 在 `np.column_stack` 前估算内存占用（`N * total_dummy_cols * 8 bytes`），若超过系统可用内存的某个阈值，提前抛出带引导信息的错误：
   ```python
   raise MemoryError(
       f"LSDV dummy matrix requires ~{required_gb:.1f} GB. "
       f"Use technique='map' to avoid materializing dummies."
   )
   ```
2. 或者捕获 `MemoryError` 后重新抛出带有操作提示的异常。

## 关联项
- REV-PANEL-01（MAP 路径不可用，使该问题的 workaround 暂时失效）

---

# REV-PANEL-11

## 元信息
- **命令**: `reghdfe`
- **命令族**: Panel / FE / HDFE
- **审查类型**: API设计缺陷
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: API不便利

## 现象描述
`reghdfe()` wrapper 要求用户将 cluster 变量单独传入 `cluster=` 参数，不支持 Stata 原生的 `vce(cluster var)` 字符串语法。对于习惯 Stata 语法的用户，这是一项不便。

## 涉及文件
- `src/stataflow/compat/stata/hdfe.py`
  - line 11–25: `reghdfe()` 签名

## 修复建议
1. 在 `reghdfe()` 中增加对 `vce="cluster(varname)"` 的解析，自动提取 `varname` 并设置 `vce="cluster"`。
2. 同理可扩展 `vce="cluster(var1 var2)"` 以支持 2-way clustering 的字符串写法。

---

# REV-PANEL-12

## 元信息
- **命令**: `reghdfe`, `areg` (MAP路径)
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: API不便利 / 资源浪费

## 现象描述
当用户在 MAP 路径下设置 `savefe=True` 时，`NotImplementedError` 直到 `_fit_map` 执行完所有 Kaczmarz 迭代、OLS 估计、VCE 计算之后才被抛出。对于大规模模型，这意味着数秒甚至数分钟的计算被浪费。

## 最小复现代码
```python
# 大规模数据，MAP 路径，savefe=True
model = AbsorbingOLS(data=large_df, y="y", x=["x"], absorb=["fe1", "fe2"])
model.fit(savefe=True)  # 计算完成后才报错
```

## 根因分析
- `absorbing_ols.py` line 1095–1096：`if savefe: raise NotImplementedError(...)` 位于 `_fit_map` 的末尾。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 1095–1096: `_fit_map` 末尾的 savefe 检查

## 修复建议
1. 将 `savefe` 的兼容性检查前移至 `fit()` 方法的开头（line 1193 之后），在 `_fit_map` 调用前即抛出异常。

---

# REV-PANEL-13

## 元信息
- **命令**: `reghdfe` (2-way cluster)
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查 / 数学偏差
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 数学偏差 / 文档不一致

## 现象描述
支持矩阵已记录：2-way cluster VCE 下 `_cons` 的 SE 存在已知 ~2–16% 的结构性偏差。但代码在运行时**未发出任何警告**。用户可能在未阅读支持矩阵的情况下，误以为 `_cons` 的 SE 与 slope SE 一样精确到 `<1e-6`。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 1404–1418: LSDV 路径的 2-way cluster _cons 修正
  - line 1067–1076: MAP 路径的 2-way cluster _cons 修正
- `docs/command-support-matrix/reghdfe.md`
  - 已文档化该偏差

## 修复建议
1. 当 `vce="cluster"` 且 `len(cluster_arrs) > 1` 且 `self.add_constant` 时，在 `result.diagnostics.warnings` 中追加运行时警告：
   ```python
   warnings.append(
       "2-way cluster VCE: _cons SE may deviate from Stata by ~2-16%. "
       "See docs/command-support-matrix/reghdfe.md for details."
   )
   ```

---

# REV-PANEL-14

## 元信息
- **命令**: `reghdfe`
- **命令族**: Panel / FE / HDFE
- **审查类型**: 源码审查 / 数学偏差
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 数学偏差

## 现象描述
`_compute_df_a()` 使用简单的 level 计数（`sum(num_levels * params_per_level)`）并做常数项/多 FE 修正，**未计算 mobility groups**（连通分量）。对于 2-way FE 中稀疏交叠的面板（如 employer-employee 匹配数据），真实 df_a 应由 FE 设计矩阵的秩决定（即 `N - mobility_groups`），当前简化计数会高估 df_a。

## 涉及文件
- `src/stataflow/estimators/absorbing_ols.py`
  - line 926–950: `_compute_df_a()`

## 修复建议
1. 在 `_compute_df_a()` 中，对 multi-way FE 场景使用 union-find 计算 mobility groups，按 `N - mobility_groups` 计算真实秩。
2. 若短期内不实现，应在支持矩阵和 docstring 中明确标注为 "known limitation"。

## 关联项
- `docs/command-support-matrix/reghdfe.md` — 已声明 "mobility-group DoF... remain missing"

---

# REV-PANEL-15

## 元信息
- **命令**: `areg`
- **命令族**: Panel / FE / HDFE
- **审查类型**: API设计缺陷
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 文档不一致

## 现象描述
`areg()` wrapper 的 docstring 声称仅支持 `vce="ols"` / `"cluster"`，但底层 `AbsorbingOLS.fit()` 实际接受 `"robust"`。wrapper 不会拦截 `vce="robust"`，因此调用 `areg(..., vce="robust")` 可以工作，但属于未文档行为，可能在未来版本中被误伤。

## 涉及文件
- `src/stataflow/compat/stata/linear.py`
  - line 97: `areg()` docstring

## 修复建议
1. 更新 docstring，明确列出 `"robust"` 为支持项；或显式在 wrapper 中校验并拒绝 `"robust"`（若不想支持）。
2. 若选择支持，补充 golden test 验证 `areg, robust` 与 Stata 的一致性。

---

# 汇总表

| 序号 | 严重度 | 问题类型 | 命令 | 核心问题 | 状态 |
|------|--------|----------|------|----------|------|
| REV-PANEL-01 | Blocker | 崩溃 | reghdfe / areg (MAP) | MAP 路径多处未定义变量 (`stats`, `beta_full`, `cov_full`, `T`)，完全不可用 | 待修复 |
| REV-PANEL-02 | Critical | 静默错误 | reghdfe / areg (MAP) | MAP 迭代未收敛时不发出警告，可能返回错误结果 | 待修复 |
| REV-PANEL-03 | Critical | 静默错误 | reghdfe (LSDV+slopes) | `savefe=True` + slope absorption 时 slope 系数被静默丢弃/错位 | 待修复 |
| REV-PANEL-04 | Major | 参数缺失 | reghdfe | wrapper 未暴露 `technique` / `max_iter` / `tol` / `aweight` | 待修复 |
| REV-PANEL-05 | Major | 参数缺口 / 行为偏差 | areg | 静默删除 singletons；不支持 `noconstant` | 待修复 |
| REV-PANEL-06 | Major | 参数缺口 / 行为偏差 | xtreg_fe | 默认无 `_cons`；不支持 `robust` / `noconstant` | 待修复 |
| REV-PANEL-07 | Major | API缺陷 | reghdfe | `parse_absorb` 的 tuple API 实现与文档不符 | 待修复 |
| REV-PANEL-08 | Major | 边界case | reghdfe | `_drop_singletons` 不处理 slope-specific singletons | 待修复 |
| REV-PANEL-09 | Major | 数学偏差 | reghdfe / areg (MAP) | `predict("xbd")` / `predict("d")` 在 MAP 路径遗漏 FE 贡献 | 待修复 |
| REV-PANEL-10 | Major | 用户体验 | reghdfe / areg | 大规模 LSDV 内存溢出时无 MAP 路径引导 | 待修复 |
| REV-PANEL-11 | Minor | API不便利 | reghdfe | 不支持 `vce(cluster var)` 字符串语法 | 待修复 |
| REV-PANEL-12 | Minor | 资源浪费 | reghdfe / areg (MAP) | `savefe` 的 `NotImplementedError` 在计算完成后才抛出 | 待修复 |
| REV-PANEL-13 | Minor | 文档/警告 | reghdfe (2-way cluster) | 2-way cluster `_cons` SE 已知偏差无运行时警告 | 待修复 |
| REV-PANEL-14 | Minor | 数学偏差 | reghdfe | `_compute_df_a` 未使用 mobility groups | 已知限制 |
| REV-PANEL-15 | Minor | 文档不一致 | areg | docstring 未声明实际可用的 `robust` VCE | 待修复 |

**按严重度分布**：Blocker × 1，Critical × 2，Major × 8，Minor × 4。  
**按类型分布**：崩溃/未定义变量 × 1，静默错误结果 × 2，参数缺失/API缺陷 × 5，边界case处理不足 × 4，数学偏差 × 2，文档/警告 × 3。
