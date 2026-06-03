# Postestimation Research Archive

**Wave:** 11
**Date:** 2026-04-30
**Scope:** `predict` extensions (`stdp`, `pearson`, `deviance`, `working`) and `estat` ecosystem (`summarize`, `vce`, `ic`)

---

## 1. `predict, stdp` (Standard Error of Linear Prediction)

### Formula

For linear models (OLS, FE, HDFE, IV):

```
stdp_i = sqrt(x_i' * V * x_i)
```

Where:
- `x_i` is the row vector of **reported** regressors for observation i (excludes absorbed FE dummies)
- `V` is the `cov_reported` matrix (variance-covariance of reported coefficients)

In matrix form: `stdp = sqrt(diag(X_reported @ V @ X_reported.T))`

### Stata Behavior Notes

- `stdp` uses only the **reported** coefficients' VCE. Absorbed FE coefficients do not contribute.
- For `reghdfe` with partialling-out, `stdp` is computed on the residualized design matrix.
- For `ivreghdfe`, `stdp` uses the second-stage VCE (same as `reghdfe` on predicted endogenous).

### Edge Cases

- Missing values in prediction variables → missing `stdp`
- Out-of-sample prediction: use the same `x_i` construction as in-sample

---

## 2. GLM Residuals (`pearson`, `deviance`, `working`)

For Poisson / PPML:

### `pearson`

```
pearson_i = (y_i - mu_i) / sqrt(mu_i)
```

Where `mu_i = exp(xb_i)`.

### `deviance`

```
deviance_i = sign(y_i - mu_i) * sqrt(2 * (y_i * log(y_i / mu_i) - (y_i - mu_i)))
```

With the convention: `0 * log(0) = 0`, so when `y_i = 0`:
```
deviance_i = sign(0 - mu_i) * sqrt(2 * (0 - (0 - mu_i)))
           = -sqrt(2 * mu_i)
```

### `working`

```
working_i = (y_i - mu_i) / mu_i
```

Also known as the "response residual" or GLM iterative weight residual.

### Stata Behavior Notes

- `ppmlhdfe predict, pearson/deviance/working` computes residuals after IRLS convergence.
- `mu_i` uses the final fitted values including FE contributions.
- For zero counts, Stata handles `0 * log(0)` as 0 (consistent with GLM theory).

---

## 3. `estat summarize`

### Output Format

Stata `estat summarize` reports for each variable in the model:

| Variable | N | Mean | SD | Min | Max |
|----------|---|------|----|-----|-----|

- Uses `e(sample)` (the estimation sample after missing drop and any singleton drop)
- Includes `y`, all `x_exog`, all `x_endog`, and all `instruments`
- Does **not** include absorbed FE variables or cluster variables by default

### Python Implementation

```python
def estat_summarize(result, data):
    mask = result.sample.mask  # e(sample) boolean array
    variables = [result.dep_var] + result.x_names
    summary = {}
    for var in variables:
        vals = data.loc[mask, var]
        summary[var] = {
            'N': len(vals),
            'mean': vals.mean(),
            'sd': vals.std(ddof=1),
            'min': vals.min(),
            'max': vals.max(),
        }
    return summary
```

---

## 4. `estat vce`

Essentially returns `e(V)` — the variance-covariance matrix of reported coefficients.

Python already has `result.variance.values`.

Can be exposed as:
```python
def estat_vce(result):
    return result.variance.values
```

---

## 5. `estat ic` (Information Criteria)

### Formulas

For models with log-likelihood:

```
AIC = -2 * ll + 2 * k
BIC = -2 * ll + k * ln(N)
```

Where:
- `ll` = log-likelihood (`result.fit.log_likelihood`)
- `N` = number of observations (`result.sample.nobs`)
- `k` = number of parameters

### `k` Definition by Command

| Command | k includes | k excludes |
|---------|-----------|------------|
| `regress` / `reghdfe` | reported coefficients + constant | absorbed FE |
| `ivreghdfe` | reported coefficients + constant | absorbed FE, first-stage coeffs |
| `ppmlhdfe` | reported coefficients + constant | absorbed FE |
| `logit` / `probit` / `poisson` | all coefficients + constant | — |

Note: Stata's `estat ic` for `reghdfe`/`ppmlhdfe` typically counts only **reported** parameters (excluding absorbed FE), matching `e(df_m) + 1` (if constant present).

### Python Implementation

```python
def estat_ic(result):
    ll = result.fit.log_likelihood
    if ll is None or np.isnan(ll):
        return {}
    n = result.sample.nobs
    k = result.fit.df_model + (1 if result.fit.has_constant else 0)
    aic = -2 * ll + 2 * k
    bic = -2 * ll + k * np.log(n)
    return {'aic': aic, 'bic': bic, 'k': k, 'N': n, 'll': ll}
```

---

## 6. References

- Stata Manual: `predict` — [U] 20.15 Obtaining predictions, residuals, and influence statistics
- Stata Manual: `estat summarize` — [R] estat summarize
- Stata Manual: `estat ic` — [R] estat ic
- McCullagh & Nelder (1989), *Generalized Linear Models*, 2nd ed. — Pearson, deviance, working residuals
