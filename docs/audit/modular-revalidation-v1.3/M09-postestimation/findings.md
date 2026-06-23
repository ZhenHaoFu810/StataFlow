# M09 Postestimation — Findings

## M09-FE-001 — `xtreg_fe()` / `FixedEffectsOLS.predict(type="xb")` does not include entity fixed effects

| Field | Value |
|---|---|
| **Finding ID** | `M09-FE-001` |
| **Severity** | P1 |
| **Evidence status** | Confirmed-Stata |
| **Affected API** | `stataflow.compat.stata.xtreg_fe()`, `stataflow.estimators.FixedEffectsOLS.predict(type="xb")`, `ResultSchema.predict(type="xb")` |
| **First observed** | `S02` synthetic test |

### Minimal reproduction

```python
import numpy as np
import pandas as pd
from stataflow.compat.stata.linear import xtreg_fe

rng = np.random.default_rng(202602)
N, G = 80, 8
df = pd.DataFrame({"id": np.repeat(np.arange(G), N // G), "x": rng.normal(size=N)})
group_effects = rng.normal(0, 1, size=G)
df["y"] = group_effects[df["id"]] + 1.5 * df["x"] + rng.normal(0, 0.3, size=N)

result = xtreg_fe(df.iloc[:60], "y", ["x"], fe="id")
py_xb_in = result.predict(type="xb", newdata=df.iloc[:60])
print(float(np.mean(py_xb_in)))  # ~0.4892
```

Equivalent Stata:

```stata
xtset id
xtreg y x if _n<=60, fe
predict xb_s, xb
summarize xb_s if !missing(xb_s) & _n<=60
```

Stata mean: **0.40991336**.

### Stata 17 results

- In-sample `predict, xb` mean: `0.40991336`
- In-sample `predict, xb` sd:   `1.7615262`
- Out-of-sample (rows 66–80) `predict, xb` mean: `-0.32942964`

### Python results

- In-sample `predict(type="xb")` mean: `0.4892045908`
- In-sample `predict(type="xb")` sd:   `1.7615261848`
- Out-of-sample `predict(type="xb")` mean: `-0.2501384130`

### Root cause

`FixedEffectsOLS.predict(type="xb")` returns only `X @ beta`. When `add_constant=False` (the `xtreg_fe` wrapper default), it does **not** add back the entity-specific fixed effect. Stata's `predict, xb` after `xtreg, fe` returns `X @ beta + u_i` (the fixed effect for each entity), so the predictions sum to the dependent variable mean over the estimation sample and produce zero-mean residuals. Python's predictions therefore have a non-zero mean residual and differ from Stata by approximately the entity fixed effect.

The same gap exists for out-of-sample rows: Python applies the grand mean of entity effects only when `add_constant=True`; it does not use the estimated entity-specific effect for each observation.

### User impact

- Any post-estimation workflow that relies on `xtreg_fe(...).predict("xb")` to reproduce Stata fitted values will obtain systematically shifted predictions.
- Residuals computed from `predict("residuals")` are not idiosyncratic errors and do not sum to zero, breaking diagnostics that assume standard FE residuals.

### Affected range

- `FixedEffectsOLS.predict` with `type="xb"` and `type="residuals"`.
- `ResultSchema.predict` delegates to the model, so it inherits the same behavior.

### Shared infrastructure issue?

No. The issue is specific to the FE estimator's prediction method, not to `ResultSchema`, `StataRunner`, or the VCE layer.

### Existing issue?

No previously filed issue identified during this audit.

### Recommendation

Do not modify product code during this audit. For a future fix:

1. Store the estimated entity effect `u_i` per observation after `fit()`.
2. In `predict(type="xb")`, add `u_i` to `X @ beta` by default (matching Stata).
3. Introduce a separate `type="xbu"` if users need predictions excluding fixed effects, or make the inclusion/exclusion explicit via the `type` argument.
4. Update the docstring to match the implemented Stata semantics.

---

*Findings will be updated as additional synthetic, real-data, and property tests are executed.*
