---
name: recurring_blockers
description: Recurring correctness gaps, Stata-Python divergence patterns, and dependency chains that cause delays.
type: project
---

**Recurring correctness gaps:**
1. **Document wording drift:** After expanding FE support from "1-2 FEs" to "1+ FEs", summary tables were updated but command matrix footers were missed (Package G rework trigger).
   - **Why:** Multiple files claim the same capability; updating one does not update others.
   - **How to apply:** Any capability wording change must include a full-text search for the old wording across `docs/`, `README.md`, and `docs/command-support-matrix/`.

2. **Encoding corruption in markdown:** Cookbook and research docs occasionally contain corrupted characters (e.g., U+8133 "脳" instead of "x").
   - **Why:** Files were edited in mixed encoding environments.
   - **How to apply:** Before claiming a document fix complete, run a non-ASCII scan and verify only expected characters remain.

3. **Export file count drift:** The open-source export script produces a slightly different file count over time (166 -> 167).
   - **Why:** New files are added but the baseline in checklists is not updated.
   - **How to apply:** After any export, re-count with `find ../StataFlow_open_source -type f | grep -v '/\.git/' | wc -l` and update all references.

**Stata-Python divergence patterns:**
1. **Cluster correction formulas:** Stata applies a small-sample correction to cluster-robust VCE that depends on whether the model has a constant. Python must mirror this exactly.
2. **aweight normalization:** Stata normalizes aweights so sum(w) = N after missing drop. Python must do the same before estimation.
3. **Log parsing:** Stata displays numbers < 1 as `.9318` (no leading zero). The parser must add the leading zero for numeric conversion.
4. **LSDV vs iterative demeaning _cons SE structural deviation:** In LSDV framework, the constant term's variance-covariance is structurally different from reghdfe's iterative demeaning. On synthetic data delta-method correction reduces error to ~2.25%; on real data with non-zero x means and binary variables, the correction can fail (up to ~16% deviation).
   - **Why:** LSDV includes FE dummies directly in the design matrix; reghdfe sweeps them out. The T matrix transformation for LSDV propagates uncertainty differently.
   - **How to apply:** All HDFE commands (reghdfe, ivreghdfe, ppmlhdfe) with 2-way cluster must use 3% _cons SE tolerance for synthetic data, 20% for real data. Slope SEs always maintain < 1e-6 hard standard. Do not spend cycles trying to eliminate this deviation — it is structural, not a bug. Document it as a known limitation in each affected command's support matrix.
   - **MAP kernel impact:** Once MAP kernel replaces LSDV for large samples, this structural deviation may change or disappear because MAP uses iterative demeaning (same framework as reghdfe). Monitor _cons SE alignment after MAP implementation.
5. **IRLS/HDFE convergence precision residual:** PPMLHDFE predict residuals (pearson/deviance/working) show ~0.35% max residual due to IRLS partial-out algorithm differences, not formula error.
   - **How to apply:** Use rtol=5e-3 for PPMLHDFE residual tests and document the source in test comments.

**Dependency chains that cause delays:**
1. **VCE framework changes block multiple commands:** Any change to cluster/robust VCE must be tested across `regress`, `reghdfe`, `ivreghdfe`, `ppmlhdfe`, `logit`, `probit`, `poisson`.
2. **ResultSchema changes block all estimators:** Adding a new field to `ResultSchema` requires updating every estimator and every golden test.
3. **Export mechanism depends on manifest:** The open-source export script uses a manifest file; any new file type must be added to the manifest or it will be silently excluded.
4. **MAP kernel is foundational for Wave 12 advanced features:** Individual slope absorption (`absorb(var##c.slope)`) and Driscoll-Kraay (`vce(dkraay)`) both depend on the MAP partial-out framework. MAP must be verified before these can be built.
   - **Why:** Slopes modify the projection operator within MAP iteration; DK VCE operates on MAP-partial-out residuals.
   - **How to apply:** Do not start Round 2b (slopes) or Round 3 (DK) until MAP small-sample equivalence (< 1e-10) and benchmark dataset success are confirmed.
