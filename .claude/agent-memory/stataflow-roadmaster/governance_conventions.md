---
name: governance_conventions
description: Governance doc locations, update frequencies, task card templates, and document style continuity rules.
type: project
---

**Governance doc locations and update frequencies:**
- `docs/roadmap.md` — Updated at the start of every new wave, or when wave priorities change.
- `docs/backlog.md` — Updated when any command changes status (planned -> ready -> done).
- `docs/command-support-matrix/*.md` — Updated after every wave completion, or when a new option is added.
- `docs/testing/test-case-catalog.md` — Updated during Round 1 (Research) of every wave.
- `workspace/current-task/INSTRUCTIONS.md` — The sole task switching point; updated when moving to a new package.
- `workspace/current-task/REPORT.md` — Updated on package completion; must include modified files, verification results, risks.

**Task card template (mandatory sections):**
1. Background
2. Objective
3. Why now
4. Permitted modification scope
5. Prohibited actions
6. Execution order
7. Minimum verification requirements
8. Deliverables
9. Success criteria

**Document style continuity:**
- Task cards must be in formal, explicit, executable Chinese.
- No empty talk. No fuzzy words like "try to", "appropriately", "as needed" unless specifying discretion boundaries.
- Command support matrices follow the same markdown structure (Completeness Status, Command Target, Python Entry, Supported Parameters, Supported Result Fields, Factor Variable Support, Postestimation, Planned Parameters, Explicitly Unsupported Parameters, Alignment Evidence, Core Implementation).

**Branch convention:**
- `main` — Stable line.
- `claude/<topic>` — Claude Code implements code and tests.
- `codex/<topic>` — Codex maintains docs, governance, architecture.

**Escalation rules (must stop and report to Codex):**
- Unexplainable deviation between Stata and Python results.
- Public API needs new or changed parameters.
- `ResultSchema` needs new fields.
- Real-data and synthetic alignment conclusions conflict.