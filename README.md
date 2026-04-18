# Stata2Python

Stata2Python (`statapy`) is a Python econometrics toolkit that reproduces Stata 17 estimation results with high precision. It provides both a **Stata-compatible command layer** (for researchers migrating from Stata) and a **native Python estimator layer** (for advanced users who want direct control).

## What you can do today

- Run Stata-style commands in Python: `regress`, `reghdfe`, `ivregress 2sls`, `logit`, `ppmlhdfe`, `did_imputation`, `csdid`, `rdrobust`, and more.
- Obtain coefficients, standard errors, t/z-statistics, p-values, and confidence intervals that are field-level verified against Stata 17.
- Work with high-dimensional fixed effects (HDFE), IV/2SLS, binary/count models, and DID/event-study estimators.
- Use Stata-style factor-variable syntax (`i.group##c.post`, `c.x1#c.x2`, `x1##x2`) and space-separated absorb strings directly in wrapper commands. Bare variables inside `#` / `##` are treated as continuous, matching common Stata usage.

## What is not yet supported

- **Multi-way clustering** — only single-cluster robust inference is available.
- **Direct post-estimation on wrapper returns** — the `compat.stata` wrappers return `ResultSchema` result objects. `predict` and `margins` are available on the core estimator layer only.
- **Full command surfaces for community commands** — `reghdfe`, `ivreghdfe`, `ppmlhdfe`, `did_imputation`, `eventstudyinteract`, `csdid`, and `rdrobust` are implemented as **verified high-frequency subsets**, not complete Stata command reproductions. Unsupported options are explicitly rejected rather than silently ignored.

### Completeness legend

- **Stable** — synthetic + real-data dual-run verified; core API is unlikely to change.
- **Alpha** — high-frequency paths are implemented and verified, but the command surface is still a subset of the full Stata community command.
- **Alpha — Partial** — a verifiable implementation exists, but large functional areas are still missing (e.g., fuzzy RD for `rdrobust`, multi-way clustering).

See the [Command Support Matrix](./docs/command-support-matrix/README.md) for the per-command detailed status.

---

## Installation

```bash
pip install -e .
```

Requirements: Python 3.9+, NumPy, pandas, SciPy.

---

## Quick start

### Stata-compatible command layer (recommended)

All `compat.stata` wrappers return a `ResultSchema` object with coefficients, standard errors, and fit statistics. They do **not** expose `.predict()` or `.margins()` directly—use the core estimator layer below for post-estimation.

```python
import pandas as pd
from statapy.compat.stata import regress, reghdfe, ivregress_2sls, logit

# OLS with robust standard errors
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")

# High-dimensional fixed effects (reghdfe)
result = reghdfe(
    df, y="wage", x=["edu", "exper"],
    absorb="firm_id year_id", vce="cluster", cluster="industry"
)

# Factor-variable syntax in HDFE
result = reghdfe(
    df, y="wage", x=["i.industry##c.post"], absorb="firm_id year_id"
)

# 2SLS
result = ivregress_2sls(
    df, y="lwage", x_exog=["edu"], x_endog=["exper"],
    instruments=["age", "kidslt6"], vce="robust"
)

# Logit
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
```

For runnable examples, see the [`examples/`](./examples/) directory:
- [`examples/demo_regress.py`](./examples/demo_regress.py)
- [`examples/demo_reghdfe.py`](./examples/demo_reghdfe.py)
- [`examples/demo_ppmlhdfe.py`](./examples/demo_ppmlhdfe.py)
- [`examples/demo_ivregress_2sls.py`](./examples/demo_ivregress_2sls.py)

### Native Python estimator layer (advanced)

```python
from statapy import OLS, FixedEffectsOLS, AbsorbingOLS, Logit, IV2SLS

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
```

---

## Supported commands

| Command | Python entry | Core capabilities |
|---------|--------------|-------------------|
| `regress` | `statapy.compat.stata.regress` | OLS, robust, cluster, aweight |
| `xtreg, fe` | `statapy.compat.stata.xtreg_fe` | Fixed effects (within), cluster |
| `areg` | `statapy.compat.stata.areg` | Single absorb variable FE |
| `reghdfe` | `statapy.compat.stata.reghdfe` | 1-2 group HDFE, cluster, singleton drop |
| `ivregress 2sls` | `statapy.compat.stata.ivregress_2sls` | 2SLS, robust, cluster |
| `ivreghdfe` | `statapy.compat.stata.ivreghdfe` | IV + 1-2 group HDFE, cluster |
| `logit` | `statapy.compat.stata.logit` | MLE, robust, cluster |
| `probit` | `statapy.compat.stata.probit` | MLE, robust, cluster |
| `poisson` | `statapy.compat.stata.poisson` | MLE, robust, cluster |
| `ppmlhdfe` | `statapy.compat.stata.ppmlhdfe` | PPML + 1-2 group HDFE |
| `did_imputation` | `statapy.compat.stata.did_imputation` | BJS DID imputation |
| `eventstudyinteract` | `statapy.compat.stata.eventstudyinteract` | Sun & Abraham IW estimator |
| `csdid` | `statapy.compat.stata.csdid` | Callaway-Sant'Anna DID (`method="reg"` only) |
| `rdrobust` | `statapy.compat.stata.rdrobust` | Sharp RD local polynomial (`bwselect="mserd"`, `covs`) |

Full details: [`docs/command-support-matrix/README.md`](./docs/command-support-matrix/README.md)

---

## Validation philosophy

Every public command is validated with **two lines of evidence**:

1. **Synthetic / controlled cases** — formula, degrees of freedom, sample screening, edge cases.
2. **Real public datasets** — field-level comparison against Stata 17 on openly available economic/financial data.

A command is considered "done" only when both lines pass and the source-to-Python mapping is documented. We do not accept "statistical equivalence" without explicit mathematical or source-code justification.

### Running tests

```bash
# Unit and integration tests (fast)
pytest tests/ -v --ignore=tests/golden/

# Golden dual-run tests (require Stata 17)
pytest tests/golden/ -v
```

---

## Project structure

- **`src/statapy/estimators/`** — Core Python estimators (`OLS`, `AbsorbingOLS`, `Logit`, `PPMLHDFE`, `DIDImputation`, etc.)
- **`src/statapy/compat/stata/`** — Stata command wrappers (`regress()`, `reghdfe()`, `ivregress_2sls()`, etc.)
- **`docs/research/`** — Source-to-Python mapping documents for community commands
- **`docs/command-support-matrix/`** — Per-command support matrices
- **`tests/golden/`** — Stata-Python dual-run tests
- **`research/vendor/stata_community/`** — Local mirrors of open-source Stata community packages (for research only)

---

## Default target version

**Stata 17**

---

## Documentation

- [Project charter](./docs/project-charter.md)
- [Architecture overview](./docs/architecture/overview.md)
- [Public API specification](./docs/architecture/public-api.md)
- [Command support matrices](./docs/command-support-matrix/README.md)
- [Open-source roadmap](./docs/next-round-open-source-plan.md)

---

## Governance

- **Codex** — project goals, architecture, review gates, and statistical-dispute arbitration.
- **Claude Code** — implementation, testing, and evidence backfill.
