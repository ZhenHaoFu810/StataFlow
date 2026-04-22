# Factor Variable Semantics in stataflow

## Scope

This document records the Stata-compatible factor-variable syntax implemented in the `stataflow.compat.stata` wrapper layer.

## Supported Syntax

| Syntax | Meaning | Example expansion |
|--------|---------|-------------------|
| `x1` | bare continuous variable | `x1` |
| `c.x1` | explicit continuous | `x1` |
| `i.g` | categorical indicator (base level omitted) | `2.g`, `3.g`, ... |
| `ib2.g` | categorical indicator with explicit base level | `1.g`, `3.g`, ... (base=2) |
| `b2.g` | synonym for `ib2.g` | `1.g`, `3.g`, ... (base=2) |
| `o2.g` | categorical indicator with explicit omitted level | `3.g`, ... (base=1, omit=2) |
| `c.x1#c.x2` | continuous 脳 continuous interaction | `c.x1#c.x2` |
| `c.x1##c.x2` | full factorial (main effects + interaction) | `x1`, `x2`, `c.x1#c.x2` |
| `i.g1#i.g2` | categorical 脳 categorical interaction | `2.g1#2.g2`, `2.g1#3.g2`, ... |
| `i.g1##i.g2` | full factorial (main effects + interaction) | `2.g1`, `3.g1`, `2.g2`, `2.g1#2.g2`, ... |
| `i.g1#c.x1` | categorical 脳 continuous interaction | `2.g1#c.x1`, `3.g1#c.x1`, ... |
| `i.g1##c.x1` | full factorial (main effects + continuous + interaction) | `2.g1`, `3.g1`, `x1`, `2.g1#c.x1`, ... |
| `c.x1#i.g1` | symmetric mixed interaction | `2.g1#c.x1`, `3.g1#c.x1`, ... |
| `c.x1##i.g1` | symmetric mixed full factorial | `2.g1`, `3.g1`, `x1`, `2.g1#c.x1`, ... |
| `x1#x2` | bare continuous interaction (treated as `c.x1#c.x2`) | `c.x1#c.x2` |
| `x1##x2` | bare continuous full factorial (treated as `c.x1##c.x2`) | `x1`, `x2`, `c.x1#c.x2` |
| `x1#i.g` / `x1##i.g` | bare continuous mixed with categorical | 绛変环浜?`c.x1#i.g` / `c.x1##i.g` |

## Naming Convention

Generated column names follow Stata coefficient naming as closely as possible:

- `i.g` with levels `[1, 2, 3]` 鈫?`2.g`, `3.g` (base level `1` omitted)
- `c.x1#c.x2` 鈫?`c.x1#c.x2`
- `i.g1#i.g2` 鈫?`<level1>.g1#<level2>.g2`
- `i.g1#c.x1` 鈫?`<level>.g1#c.x1`

## Rejected Syntax (ValueError)

The parser hard-rejects the following with a descriptive `ValueError`:

- `ib.<var>` 鈥?base indicators without a level number
- `b.<var>` 鈥?base levels without a level number
- `o.<var>` 鈥?omitted levels without a level number
- `L.x`, `F.x`, etc. 鈥?time-series operators
- Three-way or higher-order interactions (e.g., `c.x1#c.x2#c.x3`)
- Any other unsupported factor term structure

Note: bare variables **inside `#` / `##` are now treated as continuous variables** (`c.`) rather than rejected. This aligns with the most common Stata usage pattern (e.g., `x1##x2` is interpreted as `c.x1##c.x2`).

## Absorb Syntax

`absorb` now accepts both Python-list and Stata-style space-separated string syntax:

```python
reghdfe(df, y="y", x=["x1"], absorb="firm year")  # Stata-style
reghdfe(df, y="y", x=["x1"], absorb=["firm", "year"])  # Python-style
```

`areg` continues to accept only a single absorb variable and validates this explicitly.

## Commands Integrated

The following wrappers automatically expand factor terms before estimation:

- `regress`
- `areg`
- `reghdfe`
- `ivregress_2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`

## Absorbed-FE Collinearity Behavior

When a categorical main effect is fully absorbed by the FE structure, the wrapper correctly drops the collinear dummy columns while keeping interaction terms that retain within-group variation. This matches Stata behavior.

## Dual-Run Evidence

Golden dual-run tests covering factor syntax:

- `tests/golden/test_a2_factor_regress_basic.py` 鈥?`regress y i.g##c.x1`
- `tests/golden/test_a2_factor_regress_bare.py` 鈥?`regress y x1##x2` (Python) aligned with Stata `regress y c.x1##c.x2`
- `tests/golden/test_a2_factor_regress_base.py` 鈥?`regress y ib2.g##c.x1`
- `tests/golden/test_a2_factor_reghdfe_basic.py` 鈥?`reghdfe y i.g##c.x1, absorb(firm year)`
- `tests/golden/test_a2_factor_reghdfe_mixed.py` 鈥?`reghdfe y c.x1##i.g, absorb(firm year)` (mixed-order symmetry)
- `tests/golden/test_a2_factor_reghdfe_bare.py` 鈥?`reghdfe y x1##x2, absorb(firm year)` (Python) aligned with Stata `reghdfe y c.x1##c.x2, absorb(firm year)`
- `tests/golden/test_a2_factor_reghdfe_base.py` 鈥?`reghdfe y ib2.g##c.x1, absorb(firm year)`
- `tests/golden/test_a2_factor_ivreghdfe_basic.py` 鈥?`ivreghdfe y c.x1##i.g (x_endog = z1 z2), absorb(firm year)`
- `tests/golden/test_a2_factor_ppmlhdfe_basic.py` 鈥?`ppmlhdfe y i.g##c.x1, absorb(firm year)`
- `tests/golden/test_a2_factor_logit_basic.py` 鈥?`logit y_bin c.x1##c.x2`
- `tests/golden/test_a2_factor_logit_base.py` 鈥?`logit y_bin ib2.g##c.x1`

All slope coefficient names, estimates, and standard errors align with Stata 17 output to `rtol=1e-6`. `_cons` in multi-FE `reghdfe` shows known algorithm-dependent recovery differences and is tested with relaxed tolerance (`rtol=1e-2` or `5e-2` depending on the specific DGP).
