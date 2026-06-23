# Pre-Public-Sync Git Index Checklist

Before pushing the open-source mirror or tagging a public release, ensure the following tracked paths are removed from the main repository's git index. They are already excluded by `.gitignore` and the export manifest, but if they remain tracked they will still appear in the public git history.

## Paths to remove from git index

```bash
git rm -r --cached .claude
rm -rf .claude

git rm -r --cached session_restore
rm -rf session_restore

git rm -r --cached workspace/current-task
# Keep only README.md if desired:
# git checkout HEAD -- workspace/current-task/README.md
# git add workspace/current-task/README.md
rm -rf workspace/current-task/*

git rm -r --cached scripts/internal
rm -rf scripts/internal

# Empty directories left over from Phase 1.5 archival
git rm -r --cached docs/audit/revalidation-v1.1 docs/audit/revalidation-v1.2
rmdir docs/audit/revalidation-v1.1 docs/audit/revalidation-v1.2

# Optional: remove modular-revalidation-v1.3 from index if it was ever tracked
# git rm -r --cached docs/audit/modular-revalidation-v1.3
```

## Verify before release

```bash
python scripts/release/export_open_source.py --dry-run
# Confirm no .claude/, session_restore/, workspace/, scripts/internal/, docs/audit/ files are copied.
```

## Files intentionally kept public

- `workspace/current-task/README.md` (harmless landing page)
- `docs/audit/audit-findings.md`, `dof-audit.md`, `next-development-plan.md`, `project-gaps.md`, `special-paths-audit.md`, `summary-feature-plan.md`, `v1.0.0-comprehensive-audit-plan.md`, `vce-formula-audit.md` (public audit methodology docs)
- `scripts/release/*` (release tooling, including this checklist)
