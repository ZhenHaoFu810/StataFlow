# REV-GLM-01

## 元信息
- **命令**: `logit` / `poisson` (GLMBase 共用路径)
- **命令族**: Binary / Count
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 数学偏差

## 现象描述
`Logit` 与 `Poisson` 的 `vce="robust"` 未施加 Stata 要求的小样本修正 `n/(n-1)`，导致 robust SE 与 Stata 17 存在系统性偏差。

`Probit` 在子类中单独实现了 `_compute_vce` 并正确添加了 `n_adj = n/(n-1)`（第 558 行），但 `GLMBase` 中的默认路径（被 `Logit`、`Poisson` 继承）完全遗漏该修正。

## 最小复现代码
```python
import numpy as np
import pandas as pd
from scipy.stats import norm
from stataflow.estimators import Logit, Poisson

np.random.seed(1)
n = 50
x = np.random.normal(0, 1, n)
eta = 0.5 + 0.3 * x
p = 1 / (1 + np.exp(-eta))
y = (np.random.rand(n) < p).astype(float)
df = pd.DataFrame({"y": y, "x": x})

# Python robust SE（无 n/(n-1)）
res_py = Logit(df, y="y", x=["x"]).fit(vce="robust")
se_py = res_py.coefficients[0].std_err

# 手动添加 n/(n-1) 修正后的 SE
n_adj = n / (n - 1)
se_expected = se_py * np.sqrt(n_adj)
# 与 Stata 17 logit, vce(robust) 相比，Python SE 偏小约 sqrt((n-1)/n)
```

## 根因分析
`GLMBase._compute_vce`（`glm.py` 第 244–248 行）在 `vce == "robust"` 分支直接计算三明治矩阵，未乘 `n/(n-1)`：
```python
elif vce == "robust":
    residuals = y - mu
    meat = (X * residuals[:, np.newaxis]).T @ (X * residuals[:, np.newaxis])
    cov_beta = XtX_inv @ meat @ XtX_inv   # ← 缺少 n_adj
```
项目研究文档 `docs/research/logit.md`、`docs/research/poisson.md` 均明确记录 Stata 使用 `n_adj = n/(n-1)`。

## 涉及文件
- `src/stataflow/estimators/glm.py`（第 244–248 行）

## 影响评估
- **影响范围**: 命令族（Logit、Poisson）
- **用户workaround**: 无（需修改源码）
- **是否阻塞实际使用**: 是（robust SE 字段级精度不达标）

## 修复建议
在 `GLMBase._compute_vce` 的 `robust` 分支追加：
```python
if n > 1:
    cov_beta *= n / (n - 1)
```
预计工作量：5 分钟。

## 关联项
- `docs/research/logit.md`（VCE 小样本修正说明）
- `docs/research/poisson.md`（VCE 小样本修正说明）

---

# REV-GLM-02

## 元信息
- **命令**: `ppmlhdfe`
- **命令族**: Binary / Count / PPMLHDFE
- **审查类型**: 源码审查
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Critical
- **问题类型**: 数学偏差

## 现象描述
当 `eform=True` 时，`PPMLHDFE.fit` 在 delta-method 变换后错误地重新计算了 z-statistic 与 p-value，导致 `eform` 模式下的显著性检验结果与 Stata 不符。

Stata 的 `eform`（及 `irr`）选项仅对**系数**、**标准误**和**置信区间**做指数变换，z-statistic 与 p-value 保留线性尺度（即 `z = beta / SE_beta`）。当前代码在变换后计算 `z_stats = exp(beta) / SE_exp(beta)`，数值上等于 `1 / SE_beta`，与原始 z 完全不同。

## 最小复现代码
```python
import numpy as np, pandas as pd
from stataflow.estimators.ppmlhdfe import PPMLHDFE

np.random.seed(1)
n = 100
x = np.random.normal(0, 1, n)
mu = np.exp(0.2 + 0.5 * x)
y = np.random.poisson(mu)
df = pd.DataFrame({"y": y, "x": x, "g": np.repeat(np.arange(10), 10)})

model = PPMLHDFE(df, y="y", x=["x"], absorb="g")
r_raw = model.fit(vce="robust", eform=False)
r_eform = model.fit(vce="robust", eform=True)

raw_z = r_raw.coefficients[0].t_stat
eform_z = r_eform.coefficients[0].t_stat
# eform_z 应等于 raw_z，但实际 eform_z = raw_z / beta（近似）
print(f"raw_z={raw_z:.4f}, eform_z={eform_z:.4f}")  # 两者差异巨大
```

## 根因分析
`ppmlhdfe.py` 第 452–463 行：
```python
if eform:
    D = np.diag(np.exp(beta_reported))
    beta_reported = np.exp(beta_reported)
    cov_reported = D @ cov_reported @ D
    ...
    se = np.sqrt(diag_cov)
    z_stats = beta_reported / se          # ← 错误：应为原始 z_stats
    p_values = 2 * (1 - norm_dist.cdf(np.abs(z_stats)))  # ← 同上
    ci_low = np.exp(ci_low)
    ci_high = np.exp(ci_high)
```
应保留变换前的 `z_stats` 与 `p_values`，仅对 CI 做 `exp()`。

## 涉及文件
- `src/stataflow/estimators/ppmlhdfe.py`（第 452–463 行）

## 影响评估
- **影响范围**: 单一命令（ppmlhdfe）
- **用户workaround**: 无（eform 模式下无法获得正确的显著性检验）
- **是否阻塞实际使用**: 是（报告了错误的 z/p）

## 修复建议
在 `eform` 分支中保留线性尺度的 `z_stats` 与 `p_values`：
```python
if eform:
    z_stats_orig = z_stats.copy()
    p_values_orig = p_values.copy()
    D = np.diag(np.exp(beta_reported))
    beta_reported = np.exp(beta_reported)
    cov_reported = D @ cov_reported @ D
    ...
    se = np.sqrt(diag_cov)
    z_stats = z_stats_orig      # 保留原始 z
    p_values = p_values_orig    # 保留原始 p
    ci_low = np.exp(ci_low)
    ci_high = np.exp(ci_high)
```
预计工作量：10 分钟；需更新 golden test `test_w7_ppmlhdfe_eform.py` 追加 z/p 断言。

## 关联项
- `tests/golden/test_w7_ppmlhdfe_eform.py`

---

# REV-GLM-03

## 元信息
- **命令**: `logit` / `probit` / `poisson` / `ppmlhdfe`（wrapper 层）
- **命令族**: Binary / Count / PPMLHDFE
- **审查类型**: API 设计缺陷
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: API 设计缺陷

## 现象描述
`compat.stata` wrapper 层（`logit()`, `probit()`, `poisson()`, `ppmlhdfe()`）直接返回 `ResultSchema` 对象，而非模型实例。这导致用户在 wrapper 层无法调用 `predict()`、`margins()`、`estat_ic()` 等后估计方法，必须回退到核心估计器层手动实例化，API 断裂感严重。

支持矩阵文档（`logit.md` 第 44–46 行）已注明此限制，但未提供便利桥接。

## 最小复现代码
```python
from stataflow.compat.stata import logit
import pandas as pd, numpy as np

df = pd.DataFrame({"y": [0,1,0,1], "x": [1,2,3,4]})
result = logit(df, y="y", x=["x"], vce="robust")

# 以下全部失败
result.predict(type="pr")      # AttributeError
result.margins(type="dydx")    # AttributeError
```

## 根因分析
Wrapper 函数总是以 `return model.fit(vce=..., cluster=...)` 结尾，丢失了 `model` 实例。例如 `src/stataflow/compat/stata/glm.py` 第 39 行、`hdfe.py` 第 105 行。

## 涉及文件
- `src/stataflow/compat/stata/glm.py`（第 11–40、42–70、73–108 行）
- `src/stataflow/compat/stata/hdfe.py`（第 63–105 行）

## 影响评估
- **影响范围**: 命令族
- **用户workaround**: 有（手动实例化核心估计器）
- **是否阻塞实际使用**: 否（有绕路，但体验差）

## 修复建议
引入一个轻量级的 `StataResult` 包装类（或让 `ResultSchema` 可选地持有模型引用），使得 wrapper 返回的对象同时具备字典式字段访问和后估计方法代理。最小侵入方案：
```python
class StataResult(ResultSchema):
    def __init__(self, result: ResultSchema, model):
        super().__setattr__("_model", model)
        # 复制所有字段...
    def predict(self, **kwargs): return self._model.predict(**kwargs)
    def margins(self, **kwargs): return self._model.margins(**kwargs)
```
预计工作量：半天至一天；需评估对现有测试的兼容性。

## 关联项
- `docs/command-support-matrix/logit.md`（Postestimation 说明）
- `docs/command-support-matrix/ppmlhdfe.md`（Postestimation 说明）

---

# REV-GLM-04

## 元信息
- **命令**: `logit` / `probit` / `poisson` / `ppmlhdfe`（wrapper 层）
- **命令族**: Binary / Count / PPMLHDFE
- **审查类型**: 参数缺失
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失

## 现象描述
所有 GLM / PPMLHDFE wrapper 完全不支持 Stata 的 `weight`、`aweight`、`fweight`、`iweight` 参数。Stata 的 `logit`、`probit`、`poisson`、`ppmlhdfe` 均原生支持加权估计，这是计量经济学常见需求（如人口加权调查数据）。

## 最小复现代码
```python
from stataflow.compat.stata import logit, poisson, ppmlhdfe
import pandas as pd

df = pd.DataFrame({
    "y": [0,1,0,1],
    "x": [1,2,3,4],
    "w": [1.5, 2.0, 1.0, 3.0]
})

# 以下全部报错：Unsupported arguments
logit(df, y="y", x=["x"], weight="w")
poisson(df, y="y", x=["x"], aweight="w")
ppmlhdfe(df, y="y", x=["x"], absorb="x", fweight="w")
```

## 根因分析
Wrapper 函数签名未声明任何权重参数，且 `**kwargs` 被硬拒绝为 `Unsupported arguments`。核心估计器 `GLMBase`、`PPMLHDFE` 的 `_irls_fit` 和 `_compute_vce` 也未预留权重接口。

## 涉及文件
- `src/stataflow/compat/stata/glm.py`
- `src/stataflow/compat/stata/hdfe.py`
- `src/stataflow/estimators/glm.py`
- `src/stataflow/estimators/ppmlhdfe.py`

## 影响评估
- **影响范围**: 命令族
- **用户workaround**: 无（需自行对数据做频率展开或加权最小二乘近似）
- **是否阻塞实际使用**: 是（加权估计是标准需求）

## 修复建议
1. 在 `GLMBase._irls_fit` 和 `PPMLHDFE._irls_fit` 中增加 `weights` 参数；
2. 在 `_compute_vce` 中相应调整 robust/cluster 的 meat 计算（加权得分）；
3. wrapper 层按 Stata 语义解析 `aweight` / `fweight` / `iweight` / `pweight`，转换为统一权重向量传入核心层。
预计工作量：2–3 天（含 dual-run 验证）。

## 关联项
- `docs/research/logit.md`（ Planned Parameters 中未提及 weight，但属于基础功能）

---

# REV-GLM-05

## 元信息
- **命令**: `ppmlhdfe`
- **命令族**: PPMLHDFE
- **审查类型**: 参数缺失 / 边界 case 处理不足
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失

## 现象描述
`ppmlhdfe()` 的 `separation` 参数仅实现了 `fe` 方法（按 FE 组内 `sum(y)==0` 删除观测），未实现 Stata 社区版支持的 `ir`、`simplex`、`mu` 方法。在存在更复杂分离模式（如交互 FE 中的 MU 分离）的数据上，Python 实现可能收敛失败或产生 Inf 系数，而 Stata 可通过 `separation(mu)` 自动识别并剔除。

## 最小复现代码
```python
import pandas as pd, numpy as np
from stataflow.compat.stata import ppmlhdfe

# 构造一个 FE 组内并非全 0，但存在 mu-separation 的场景
df = pd.DataFrame({
    "y": [0, 0, 1, 2],
    "x": [1, 2, 3, 4],
    "fe": ["A", "A", "B", "B"]
})

# 以下报错：Unsupported arguments
ppmlhdfe(df, y="y", x=["x"], absorb="fe", separation="mu")
# 即使使用 separation="fe"，也可能无法识别非 sum(y)==0 的分离
```

## 根因分析
`ppmlhdfe.py` 第 332–350 行仅处理 `self.separation == "fe"`：
```python
if self.separation == "fe":
    grouped = df.groupby(var)[self.y].sum()
    sep_levels = grouped[grouped == 0].index
```
无 `ir`、`simplex`、`mu` 分支。

## 涉及文件
- `src/stataflow/estimators/ppmlhdfe.py`（第 332–350 行）
- `src/stataflow/compat/stata/hdfe.py`（第 78 行，仅透传）

## 影响评估
- **影响范围**: 单一命令
- **用户workaround**: 有（手动清洗数据）
- **是否阻塞实际使用**: 否（对多数无分离数据不影响）

## 修复建议
参照 Correia, Guimarães, Zylkin (2020) 的迭代算法或 Stata `ppmlhdfe` 源码中的 `check_separation` 逻辑，逐步实现 `ir`、`simplex`、`mu` 方法。`fe` 方法作为默认已满足基础场景，建议 backlog 中标记为 P1。
预计工作量：3–5 天（含 dual-run）。

## 关联项
- `docs/research/ppmlhdfe.md`（第 74–78 行：Phase A 推荐延后实现完整分离检测）
- `docs/command-support-matrix/ppmlhdfe.md`（separation 参数说明）

---

# REV-GLM-06

## 元信息
- **命令**: `ppmlhdfe`
- **命令族**: PPMLHDFE
- **审查类型**: 参数缺失
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失

## 现象描述
Stata `ppmlhdfe` 支持 `d`（显示迭代日志）和 `d2`（详细迭代信息）选项，对调试收敛问题至关重要。当前 `stataflow` 的 wrapper 与核心估计器均未暴露这两个参数，用户无法追踪 IRLS 迭代过程。

## 最小复现代码
```python
from stataflow.compat.stata import ppmlhdfe
import pandas as pd, numpy as np

df = pd.DataFrame({"y": [1,2], "x": [1,2], "fe": ["A","B"]})
# 以下报错：Unsupported arguments
ppmlhdfe(df, y="y", x=["x"], absorb="fe", d=True)
```

## 根因分析
Wrapper 与 `PPMLHDFE.__init__` / `fit` 均未声明 `d` 或 `d2` 参数。

## 涉及文件
- `src/stataflow/compat/stata/hdfe.py`
- `src/stataflow/estimators/ppmlhdfe.py`

## 影响评估
- **影响范围**: 单一命令
- **用户workaround**: 有（手动在源码中添加 print）
- **是否阻塞实际使用**: 否

## 修复建议
在 `PPMLHDFE` 的 `_irls_fit` 中增加 `verbose` / `d` / `d2` 级别控制，输出迭代序号、对数似然、最大参数变化。Wrapper 层透传 `d` / `d2`。
预计工作量：半天。

---

# REV-GLM-07

## 元信息
- **命令**: `logit` / `probit` / `poisson`
- **命令族**: Binary / Count
- **审查类型**: 参数缺失 / 后估计
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 参数缺失

## 现象描述
`Logit`、`Probit`、`Poisson` 的 `predict()` 方法不支持 `stdp`（线性预测标准误）。Stata 的 `predict xb, stdp` 是标准后估计命令，用于计算 `SE(xb)`。当前 `predict` 仅支持 `xb`、`pr`/`mu`。

## 最小复现代码
```python
from stataflow.estimators import Logit
import pandas as pd, numpy as np

df = pd.DataFrame({"y": [0,1,0,1], "x": [1,2,3,4]})
model = Logit(df, y="y", x=["x"])
model.fit(vce="robust")
# 以下报错
try:
    model.predict(type="stdp")
except ValueError as e:
    print(e)  # type='stdp' not supported
```

## 根因分析
`GLMBase.predict`（`glm.py` 第 384–406 行）的允许类型白名单不包含 `stdp`：
```python
if type not in ("xb", "pr", "mu"):
    raise ValueError(...)
```

## 涉及文件
- `src/stataflow/estimators/glm.py`（第 388–389 行）

## 影响评估
- **影响范围**: 命令族
- **用户workaround**: 有（手动计算 `sqrt(diag(X @ V @ X.T))`）
- **是否阻塞实际使用**: 否

## 修复建议
在 `predict` 中增加 `stdp` 分支：
```python
if type == "stdp":
    if newdata is not None:
        X = ...  # 同现有逻辑
    else:
        X = self._design_matrix
    return np.sqrt(np.maximum(np.sum(X @ self._cov_beta * X, axis=1), 0))
```
预计工作量：30 分钟。

---

# REV-GLM-08

## 元信息
- **命令**: `ppmlhdfe`
- **命令族**: PPMLHDFE
- **审查类型**: 参数缺失
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 参数缺失 / API 不便利

## 现象描述
`ppmlhdfe()` wrapper 仅支持 `eform` 布尔参数，未支持 `irr`（Incidence Rate Ratio）别名。Stata `poisson` 和 `ppmlhdfe` 用户更习惯使用 `irr` 而非 `eform`。当前用户传入 `irr=True` 会收到 `Unsupported arguments` 错误。

## 根因分析
`hdfe.py` 第 77 行声明 `eform: bool = False`，未将 `irr` 纳入签名。

## 涉及文件
- `src/stataflow/compat/stata/hdfe.py`（第 77 行）

## 影响评估
- **影响范围**: 单一命令
- **用户workaround**: 有（改用 `eform=True`）
- **是否阻塞实际使用**: 否

## 修复建议
在 wrapper 签名中增加 `irr: bool = False`，并在内部映射为 `eform = eform or irr`。
预计工作量：5 分钟。

---

# REV-GLM-09

## 元信息
- **命令**: `logit` / `probit`
- **命令族**: Binary / Count
- **审查类型**: 边界 case 崩溃 / 数值稳定性
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Major
- **问题类型**: 边界 case 处理不足

## 现象描述
当 `y` 全为 0 或全为 1 时，`Logit` / `Probit` 的 MLE 系数趋向无穷（完全分离），但代码未做任何检测或特殊处理。IRLS 会迭代至 `max_iter` 后报告 "IRLS did not converge"，不提示分离原因。Stata `logit` 在这种情况下会报告 `(note: ... omitted because of no variation)` 并自动剔除完美预测观测或给出明确诊断。

## 最小复现代码
```python
from stataflow.estimators import Logit
import pandas as pd

df = pd.DataFrame({"y": [1,1,1,1], "x": [1,2,3,4]})
model = Logit(df, y="y", x=["x"])
res = model.fit(vce="robust")
print(res.diagnostics.warnings)  # 仅 ['IRLS did not converge']，无分离提示
```

## 根因分析
`GLMBase._irls_fit`（第 157–217 行）无任何分离检测逻辑。`_null_loglik`（第 476–481、580–585 行）在 `n1==0 or n0==0` 时返回 0.0，虽避免了 `ll_null` 除零，但未触发上层警告。

## 涉及文件
- `src/stataflow/estimators/glm.py`（`_irls_fit` 第 157–217 行、`_null_loglik` 第 476–481、580–585 行）

## 影响评估
- **影响范围**: 命令族（Logit、Probit）
- **用户workaround**: 有（自行检查 y 的变异）
- **是否阻塞实际使用**: 否（对正常数据不影响）

## 修复建议
1. 在 `_prepare_data` 后检查 `y` 的方差，若 `var(y)==0` 直接抛出 `ValueError` 并提示 "dependent variable has no variation"。
2. 在 IRLS 迭代中监测系数爆炸（如 `np.max(np.abs(beta)) > 1e6`）并提前终止，追加 "possible complete separation" 警告。
预计工作量：半天。

## 关联项
- `docs/command-support-matrix/logit.md`（Planned Parameters: `asis`）
- `docs/command-support-matrix/probit.md`（Planned Parameters: `asis`）

---

# REV-GLM-10

## 元信息
- **命令**: `logit` / `probit` / `poisson`
- **命令族**: Binary / Count
- **审查类型**: 数值稳定性
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: API 设计缺陷 / 数值稳定性

## 现象描述
`GLMBase` 默认收敛容差 `tol=1e-8`（第 57 行），严于 Stata 默认 `1e-6`。研究文档 `docs/research/logit.md`、`docs/research/probit.md`、`docs/research/poisson.md` 均建议采用 `1e-6` 以匹配 Stata。过严的容差导致不必要的迭代，对大规模数据影响性能。

## 根因分析
`GLMBase.__init__`（`glm.py` 第 57 行）：
```python
tol: float = 1e-8
```

## 涉及文件
- `src/stataflow/estimators/glm.py`（第 57 行）

## 影响评估
- **影响范围**: 命令族
- **用户workaround**: 有（手动传入 `tol=1e-6`）
- **是否阻塞实际使用**: 否

## 修复建议
将默认值改为 `tol=1e-6`，与 Stata 17 对齐。
预计工作量：5 分钟。

---

# REV-GLM-11

## 元信息
- **命令**: `ppmlhdfe`
- **命令族**: PPMLHDFE
- **审查类型**: 数值稳定性
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 数值稳定性

## 现象描述
`PPMLHDFE` 默认 `max_iter=100`（第 61 行）。在复杂多 FE、低收敛速度的真实数据（如 gravity 贸易流）上，100 次迭代可能不足，导致误报 "IRLS did not converge"。Stata `ppmlhdfe` 默认最大迭代通常更高（社区版源码中常见 `maxiter(1600)`）。

## 根因分析
`PPMLHDFE.__init__`（`ppmlhdfe.py` 第 61 行）：
```python
max_iter: int = 100
```

## 涉及文件
- `src/stataflow/estimators/ppmlhdfe.py`（第 61 行）
- `src/stataflow/compat/stata/hdfe.py`（第 75 行，`maxiter=100`）

## 影响评估
- **影响范围**: 单一命令
- **用户workaround**: 有（手动传入更大的 `maxiter`）
- **是否阻塞实际使用**: 否

## 修复建议
将默认值提升至 `max_iter=1000` 或 `1600`，与 Stata 社区版默认对齐；或在文档中明确提示用户在高维 FE 场景下手动调大。
预计工作量：5 分钟。

---

# REV-GLM-12

## 元信息
- **命令**: `ppmlhdfe`
- **命令族**: PPMLHDFE
- **审查类型**: 数学偏差（设计选择）
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 数学偏差（已文档化）

## 现象描述
`PPMLHDFE` 的 cluster VCE 仅应用 `G/(G-1)` 修正，未应用 `(N-1)/(N-k)` 小样本修正。这与项目研究文档 `docs/research/ppmlhdfe.md` 中明确的 "asymptotic mode" 设计一致，但偏离了线性模型（如 `reghdfe`）的完整小样本调整。Audit checklist 要求对此进行确认。

经审查，该行为是故意的：PPMLHDFE 的 VCE 计算采用 `vce_asymptotic` 语义，与研究文档一致。但代码注释与文档未在 `ppmlhdfe.py` 近处显式说明，新开发者可能误以为是遗漏。

## 根因分析
`ppmlhdfe.py` 第 292–294 行：
```python
g_adj = cluster_count / (cluster_count - 1) if cluster_count > 1 else 1.0
cov_full = g_adj * XtX_inv @ meat @ XtX_inv
```
无 `n_adj`。

## 涉及文件
- `src/stataflow/estimators/ppmlhdfe.py`（第 292–294 行）

## 影响评估
- **影响范围**: 单一命令
- **用户workaround**: 无（设计选择）
- **是否阻塞实际使用**: 否

## 修复建议
在代码注释中增加显式说明：
```python
# PPMLHDFE uses vce_asymptotic mode (per docs/research/ppmlhdfe.md):
# only G/(G-1) adjustment is applied, no (N-1)/(N-k) correction.
```
预计工作量：5 分钟。

---

# REV-GLM-13

## 元信息
- **命令**: `probit`
- **命令族**: Binary / Count
- **审查类型**: 数学偏差（待验证）
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: Minor
- **问题类型**: 数学偏差（待验证）

## 现象描述
`Probit` 的 robust VCE 使用了 `n/(n-1)` 小样本修正（`glm.py` 第 558 行），而 `Logit`/`Poisson` 共用路径缺失该修正。Audit Phase 1 曾标记 Probit 的 `n/(n-1)` "而非标准修正"。

经审查，项目研究文档 `docs/research/probit.md` 明确记载 Stata `probit, vce(robust)` 使用 `n/(n-1)`。因此 Probit 的实现与 Stata 17 一致，**并非 bug**。差异在于 OLS 的 HC1 使用 `n/(n-k)`，而 MLE robust 使用 `n/(n-1)`。为避免后续审计混淆，建议在代码处添加注释。

## 根因分析
Phase 1 审计可能将 OLS 的 HC1 标准误套用到 MLE 模型上。

## 涉及文件
- `src/stataflow/estimators/glm.py`（第 555–559 行）

## 影响评估
- **影响范围**: 单一命令
- **用户workaround**: 无
- **是否阻塞实际使用**: 否

## 修复建议
在 `Probit._compute_vce` 的 robust 分支增加注释：
```python
# n/(n-1) matches Stata 17 probit, vce(robust); differs from OLS HC1 (n/(n-k)).
```
预计工作量：5 分钟。

---

# 汇总表格

| 序号 | 命令 | 严重度 | 问题类型 | 简要描述 | 状态 |
|------|------|--------|----------|----------|------|
| REV-GLM-01 | logit / poisson | **Critical** | 数学偏差 | Robust VCE 缺失 `n/(n-1)` 小样本修正 | 待修复 |
| REV-GLM-02 | ppmlhdfe | **Critical** | 数学偏差 | `eform=True` 时 z-statistic / p-value 计算错误 | 待修复 |
| REV-GLM-03 | logit / probit / poisson / ppmlhdfe | **Major** | API 设计缺陷 | Wrapper 层返回 ResultSchema，predict/margins 不可用 | 待修复 |
| REV-GLM-04 | logit / probit / poisson / ppmlhdfe | **Major** | 参数缺失 | 完全不支持 weight / aweight / fweight | 待修复 |
| REV-GLM-05 | ppmlhdfe | **Major** | 参数缺失 | `separation` 仅实现 `fe`，`ir`/`simplex`/`mu` 缺失 | 待实现 |
| REV-GLM-06 | ppmlhdfe | **Major** | 参数缺失 | `d` / `d2` 迭代日志选项未实现 | 待实现 |
| REV-GLM-07 | logit / probit / poisson | **Major** | 参数缺失 | `predict(type="stdp")` 不支持 | 待修复 |
| REV-GLM-08 | ppmlhdfe | **Minor** | API 不便利 | `irr` 别名未支持（仅 `eform`） | 待修复 |
| REV-GLM-09 | logit / probit | **Major** | 边界 case | 完全分离（complete separation）无检测 | 待实现 |
| REV-GLM-10 | logit / probit / poisson | **Minor** | 数值稳定性 | 默认 `tol=1e-8` 严于 Stata 默认 `1e-6` | 待修复 |
| REV-GLM-11 | ppmlhdfe | **Minor** | 数值稳定性 | 默认 `max_iter=100` 可能不足 | 待修复 |
| REV-GLM-12 | ppmlhdfe | **Minor** | 数学偏差（设计选择） | Cluster VCE 仅 `G/(G-1)`，无 `(N-1)/(N-k)` | 需加注释 |
| REV-GLM-13 | probit | **Minor** | 数学偏差（已对齐） | `n/(n-1)` 已匹配 Stata，但与 OLS HC1 不同 | 需加注释 |

## 按严重度 / 类型分布

| 严重度 | 数量 | 涉及类型 |
|--------|------|----------|
| Critical | 2 | 数学偏差 (2) |
| Major | 6 | API 设计缺陷 (1)、参数缺失 (3)、边界 case (1)、后估计 (1) |
| Minor | 5 | 数值稳定性 (2)、API 不便利 (1)、数学偏差/设计选择 (2) |

| 问题类型 | 数量 |
|----------|------|
| 数学偏差 | 4 |
| 参数缺失 | 4 |
| API 设计缺陷 | 1 |
| 边界 case 处理不足 | 1 |
| 数值稳定性 | 2 |
| API 不便利 | 1 |
