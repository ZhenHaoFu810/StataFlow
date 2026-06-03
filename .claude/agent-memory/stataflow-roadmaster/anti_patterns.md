---
name: anti_patterns
description: Common anti-patterns seen in execution agent deliveries that must be avoided.
type: feedback
---

**Anti-pattern 1: Document drift**
- **What:** Updating README or summary docs but forgetting to update command matrix footers, cookbook examples, or release notes.
- **Why it happens:** Multiple files claim the same capability; execution agent stops at the first file.
- **How to avoid:** Any wording change must be accompanied by a full-text search for the old wording across `docs/`, `README.md`, `docs/command-support-matrix/`, `docs/release/`, and `docs/cookbook*.md`.

**Anti-pattern 2: "Tests pass" != "mathematically correct"**
- **What:** Execution agent sees pytest green and moves on, without verifying field-level alignment against Stata.
- **Why it happens:** pytest only checks Python-internal consistency; golden tests require Stata 17.
- **How to avoid:** Every new statistical feature must have at least one golden test (Stata-Python dual-run) before being marked done.
- **Wave 9 example:** Round 2 delivered 251 synthetic unit tests passing, but zero golden dual-run tests for controls/pretrends/dr. This is exactly Anti-pattern 2 in action.

**Anti-pattern 3: Scope creep within a package**
- **What:** A task card specifies "fix savefe wording" and the agent also rewrites the entire HDFE implementation.
- **Why it happens:** Agent sees related code and "while I'm here" expands scope.
- **How to avoid:** Task cards must have explicit "Prohibited actions" section. Agent must not modify implementation code during documentation-only tasks.

**Anti-pattern 4: Hard-rejecting without research**
- **What:** Agent sees an unsupported option and raises ValueError without documenting why or what the Stata behavior is.
- **Why it happens:** Faster to reject than to research.
- **How to avoid:** Every hard-rejected option must have a comment citing the Stata source (ado file line number or manual section) and a note in the command support matrix.

**Anti-pattern 5: Ignoring the 3-round rule**
- **What:** Agent tries to do Research + Implementation + Real-data validation in a single session.
- **Why it happens:** Desire to complete quickly.
- **How to avoid:** Roadmaster must enforce the 3-round split (Research -> Min Implementation -> Real-data Validation). Codex reviews each round separately.
- **Wave 9 example:** Round 2 completed all 5 Phases of implementation. Round 3 (golden dual-run) was explicitly deferred in INSTRUCTIONS.md. Roadmaster must now ensure Round 3 executes before Wave 10.

**Anti-pattern 6: Forgetting export validation**
- **What:** Agent changes docs but never runs the open-source export script to verify the mirror is consistent.
- **Why it happens:** Export is seen as a separate "release" task.
- **How to avoid:** Any document change that affects public-facing content must be followed by `python scripts/release/export_open_source.py --force` and a file-count check.

**Anti-pattern 7: Declaring a wave "done" when exit criteria are unmet**
- **What:** Agent or Roadmaster marks a wave as complete because implementation code is merged and synthetic tests pass, even though backlog exit criteria (golden dual-run, real-data validation, command matrix update) remain unchecked.
- **Why it happens:** Implementation feels "done"; validation is seen as follow-up cleanup.
- **How to avoid:** Roadmaster must read `docs/backlog.md` exit criteria before declaring any wave complete. If exit criteria are unmet, the wave status must remain "in_progress" and the next task must close the gap.
- **Wave 9 example:** Round 2 is complete, but Wave 9 is NOT done because backlog exit criteria 3/3 are unchecked. Roadmaster must deploy Round 3 before Wave 10.

**Anti-pattern 8: "First fix was enough" assumption (NEW — Wave 10 Rework 2 trigger)**
- **What:** Execution agent applies fixes for a rejection, resubmits without re-reading the source code from scratch, and misses that some errors persist or new errors were introduced.
- **Why it happens:** Agent works from memory of the first rejection rather than re-verifying against primary source (Stata ado/Mata code).
- **How to avoid:**
  - Rework tasks must explicitly require re-reading the primary source (ado/Mata) for every disputed formula.
  - Task card must list each P1 blocker with its specific source evidence requirement (e.g., "attach s_liml L57xx screenshot").
  - Gatekeeper should reject any rework that does not cite fresh source line numbers.
- **Wave 10 example:** Round 1 first rejection had 4 P1 blockers. Agent fixed some, resubmitted. Gatekeeper found W/W1 still wrong, new transpose error in VCE, docstring still misleading. Second rejection required a formal rework package with stricter source-citation rules.

**Anti-pattern 9: Matrix formula without dimension annotations**
- **What:** Research docs present complex matrix expressions (VCE, GMM weights, LIML lambda) without annotating the dimension of each intermediate matrix.
- **Why it happens:** Formula looks "obviously correct" to the author; dimension errors are caught late by gatekeeper or implementation.
- **How to avoid:** Every matrix equation in research docs must have inline dimension annotations for every term. Task cards must make this a mandatory success criterion.
- **Wave 10 example:** LIML VCE formula had a transpose error that produced LxL instead of KxK. Dimension annotations would have caught this immediately.

**Anti-pattern 10: Absolute equivalence claims without evidence**
- **What:** Docstrings or research docs claim "equivalent to Stata X" or "equivalent to ranktest" when the implementation is actually an approximation.
- **Why it happens:** Author believes the approximation is good enough and overstates confidence.
- **How to avoid:**
  - Any "equivalent to" claim must be backed by either (a) mathematical proof in the doc, or (b) a note explaining the approximation and its conditions.
  - Task cards must require explicit docstring review for absolute language.
- **Wave 10 example:** `_ranktest_wald` docstring claimed "equivalent to reduced-form Wald for excluded IV joint significance" but the code did separate per-endogenous-variable Wald tests and summed them — only equivalent under diagonal error covariance.
