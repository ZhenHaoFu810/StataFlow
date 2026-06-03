---
name: ivreghdfe GMM/LIML notation patterns
description: Recurring scaled/unscaled matrix notation issues in ivreghdfe research docs
type: project
---

**Pattern:** `ivreghdfe` Mata source uses Q-matrices (scaled by 1/N) internally, but research docs repeatedly drift into unscaled notation (X'Z, Z'Z) when writing formulas. This causes systematic dimension mismatches when 1/N factors are dropped or double-counted.

**Root cause:** The Stata source defines `QZZ = ZZ/N` and `QZZinv = ZZinv*N` (note: `QZZinv = inv(QZZ)`, not `inv(QZZ)/N`). Formulas in docs must use either all-Q or all-unscaled consistently. Mixed notation is the primary source of P1 rejections in this research track.

**Verified correct forms (from Stata source):**
- `Qh = (1-k)*QXX + k*QXZ*QZZ^-1*QXZ'` (L5871)
- `beta = Qh^-1 * [(1-k)*QXy + k*QXZ*QZZ^-1*QZy]` (equivalent to L5870-5876)
- `V = 1/N * sigmasq * Qh^-1` (homoskedastic, L5891)
- `V = 1/N * aux9' * omega * aux9` where `aux9 = QZZ^-1 * QXZ' * Qh^-1` (inefficient, L5913-5914)
- `V = 1/N * aux11 * omega * aux11'` where `aux11 = aux10^-1 * aux3'` and `aux10 = QXZ*QZZ^-1*QXZ'` (coviv, L5920-5923)
- `beta_2s = [QXZ*omega^-1*QXZ']^-1 * QXZ*omega^-1*QZy` (overid test, L5929-5932)
- `j = N * gbar' * omega^-1 * gbar` where `gbar = Z'e/N` (J stat, L5598-5599)

**How to apply:** When reviewing future ivreghdfe research docs or implementation, verify every formula against these verified forms. Flag any mixed notation immediately.