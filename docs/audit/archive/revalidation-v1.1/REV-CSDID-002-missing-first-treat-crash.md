# REV-CSDID-002

## 元信息
- **命令**: `csdid`
- **命令族**: DID / Event Study
- **审查类型**: 真实数据复现 / 边界case
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: **Critical**
- **问题类型**: 边界case崩溃 / 缺失值处理缺陷

## 现象描述
当 `first_treat` 变量包含缺失值（NaN）时，`csdid()` 直接崩溃。

复现代码：
```python
import pandas as pd
import numpy as np
from stataflow.compat.stata import csdid

df = pd.DataFrame({
    'id': [0,0,0,1,1,1],
    'time': [1,2,3,1,2,3],
    'first_treat': [2.0, 2.0, 2.0, np.nan, np.nan, np.nan],
    'y': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
})

result = csdid(df, y='y', id='id', time='time',
               first_treat='first_treat', method='reg',
               cluster='id', aggtype='event')
```

错误：
```
ValueError: invalid literal for int() with base 10: '4.0'
```

## 根因分析
1. `CSDID._fit_reg()` 第81行确实调用了 `df = df.dropna(subset=[y, uid, time, ft])`，应该已经删除了缺失值行。
2. 但崩溃发生在更后面的代码中。初步判断：
   - `df[ft].unique()` 在缺失值删除前被调用，或
   - 缺失值以某种方式进入了 `cohorts` 列表，后续代码尝试将其转换为整数时失败。
3. 具体来说，`cohorts = sorted([g for g in df[ft].unique() if g > 0])` — 如果 `df[ft].unique()` 返回了包含 `NaN` 的数组（在dropna之前），`NaN > 0` 在 pandas/numpy 中可能返回 `True`（行为不确定），导致 `NaN` 进入排序列表。
4. 或者，缺失值被删除后，`cohort_map = df.groupby(uid)[ft].first()` 可能返回了 `NaN`，后续使用时出错。

**更深层问题：** Stata 的 `csdid` 在遇到缺失值时会**自动删除缺失行并继续运行**。Python 实现虽然也有 `dropna`，但可能在某些路径上缺失值处理不完整。

## 涉及文件
- `src/stataflow/estimators/csdid.py` — `_fit_reg()` 和 `_fit_dr()`

## 影响评估
- **影响范围**: 单一命令（`csdid`）
- **用户workaround**: 用户必须在使用前手动 `df = df.dropna(subset=[...])`，但这不是Stata的行为。
- **是否阻塞实际使用**: **是**。真实数据几乎总有缺失值，用户不应在使用前手动清洗。

## 修复建议
1. 在 `CSDID.__init__()` 或 `fit()` 入口进行严格的缺失值筛查，确保**所有**涉及变量（y, id, time, first_treat, xvars, cluster）的缺失行都在任何计算前被删除。
2. 对 `first_treat` 的数据类型进行显式检查：确保其为数值型（int/float），并将 `NaN` 正确标记为缺失。
3. 添加防御性代码：在 `cohorts` 计算前显式过滤 `NaN` 和 `inf`。

```python
# 建议在 fit() 入口添加
df = self.data.copy()
required_cols = [self.y_name, self.id_name, self.time_name, self.first_treat_name]
if self.xvars:
    required_cols.extend(self.xvars)
df = df.dropna(subset=required_cols)
# 然后确保所有后续计算使用这个清洗后的 df
```

## 关联项
- REV-CSDID-001: API设计缺陷
