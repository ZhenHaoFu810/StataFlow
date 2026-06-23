# M10-FACTOR-001 最小复现

## 问题

Python 因子变量结果未包含 Stata 中的基期/省略系数行。

## 复现步骤

```python
import pandas as pd
from stataflow.compat.stata.linear import regress

df = pd.DataFrame({
    "y": [1, 2, 3, 4, 5, 6],
    "x": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
    "g": [1, 1, 2, 2, 3, 3],
})
res = regress(df, "y", ["i.g##c.x"])
print([c.name for c in res.coefficients])
```

输出仅包含非基期项，例如 `['2.g', '3.g', 'x', '2.g#c.x', '3.g#c.x', '_cons']`。

## Stata 17 对照

```stata
regress y i.g##c.x
matrix list e(b)
```

`e(b)` 包含 `1b.g`、`1b.g#co.x` 等基期行（系数为 0）。

## 证据文件

- `evidence/synthetic/M10-S01.json`
- `evidence/real-data/M10-R01.json`
