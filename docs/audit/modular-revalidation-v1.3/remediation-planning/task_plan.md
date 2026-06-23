# Modular Revalidation v1.3 Remediation Planning

## Goal

Read and reconcile all M01-M10 audit outputs, understand each confirmed or suspected issue, and produce a rigorous downstream problem-verification and remediation guide without changing product code.

## Phases

- [completed] Inventory all module deliverables and findings.
- [completed] Analyze M01-M05 findings and evidence.
- [completed] Analyze M06-M10 findings and evidence.
- [completed] Deduplicate cross-module findings and identify shared root causes.
- [completed] Build remediation ordering, verification gates, and task templates.
- [completed] Write and validate the final remediation master document.

## Constraints

- Do not modify product code.
- Do not treat unverified suspicions as confirmed defects.
- Preserve module finding IDs and evidence paths.
- Require fresh reproductions before every fix.
- Separate statistical correctness from API, schema, runner, and coverage issues.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| PowerShell wildcard paths passed directly to `rg` produced OS error 123 | 1 | Search the whole audit directory with `-g` filters instead. |
| First Markdown section-extraction script assumed every regex match had capture group 1 | 1 | Replaced it with line-oriented section extraction and successfully extracted the required root-cause summaries. |
