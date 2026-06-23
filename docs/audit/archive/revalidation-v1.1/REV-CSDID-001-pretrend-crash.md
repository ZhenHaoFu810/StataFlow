# REV-CSDID-001

## 元信息
- **命令**: `csdid`
- **命令族**: DID / Event Study
- **审查类型**: 真实数据复现 / API设计
- **stataflow 版本**: 1.0.0
- **日期**: 2026-06-03

## 问题摘要
- **严重度**: **Blocker**
- **问题类型**: API设计缺陷 + 边界case崩溃

## 现象描述
`csdid()` wrapper 在 `aggtype="pretrend"` 时直接崩溃，抛出 `AttributeError`。

复现代码：
```python
import pandas as pd
from stataflow.compat.stata import csdid

df = pd.read_stata('research/data/public/did/ezunem_prepared.dta')
result = csdid(
    df, y='uclms', id='city', time='year',
    first_treat='first_treat', method='reg',
    cluster='city', aggtype='pretrend'
)
```

错误：
```
AttributeError: 'dict' object has no attribute 'coefficients'
```

## 根因分析
1. `csdid()` wrapper (`src/stataflow/compat/stata/did.py:170-173`) 直接调用 `model.estat(aggtype=aggtype)` 并返回其结果。
2. `estat_pretrend()` (`src/stataflow/estimators/csdid.py:702-733`) 返回一个 `dict`：`{"f_stat": ..., "p_value": ..., "df": ...}`。
3. 而 `csdid()` wrapper 的返回类型注解是 `-> object`，调用方期望的是 `ResultSchema`（有 `.coefficients` 属性）。
4. 更严重的是：由于 wrapper 直接返回 `.estat()` 结果，用户**永远无法访问底层 fitted model**，无法进行：
   - 先 fit 再选择 aggtype
   - 访问 ATT(g,t) 矩阵
   - 进行二次分析（如先 event 再 simple）
   - 检查模型拟合诊断信息

## 涉及文件
- `src/stataflow/compat/stata/did.py:140-173` — `csdid()` wrapper
- `src/stataflow/estimators/csdid.py:702-733` — `estat_pretrend()`

## 影响评估
- **影响范围**: 单一命令（`csdid` wrapper）
- **用户workaround**: 无。用户必须使用底层 `CSDID` 类才能避免此问题，但wrapper是主要API入口。
- **是否阻塞实际使用**: **是**。任何需要 pretrend 检验的用户都会遇到崩溃。

## 修复建议

### 短期修复（解决崩溃）
在 `csdid()` wrapper 中处理 `pretrend` 返回类型：
```python
if aggtype == "pretrend":
    return model.estat(aggtype=aggtype)  # 直接返回dict
return model.estat(aggtype=aggtype)  # 返回ResultSchema
```
但这不改变API设计问题。

### 长期修复（推荐）
1. **新增 `csdid()` 的 `return_model` 参数** 或 **改变默认行为**：
   ```python
   def csdid(data, ..., return_full=False):
       model = CSDID(...)
       model.fit(...)
       if return_full:
           return model  # 返回 fitted model，用户可调用 .estat()
       return model.estat(aggtype=aggtype)
   ```
2. 或者将 `csdid()` 的行为改为 Stata 风格：**默认返回 fitted model**，`.estat()` 作为后估计调用：
   ```python
   model = csdid(data, ...)
   result_event = model.estat("event")
   result_pretrend = model.estat("pretrend")
   ```

**推荐方案2**，因为这更符合 Stata 用户的直觉（`csdid` 后接 `csdid_estat`）。

## 关联项
- `docs/research/csdid-aggtype.md` — 研究档案中已预见此问题
- `docs/audit/revalidation-v1.1/REV-CSDID-002.md` — 关联：API设计缺陷（csdid wrapper不返回model）
