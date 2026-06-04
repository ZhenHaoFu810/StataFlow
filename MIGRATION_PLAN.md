# StataFlow Monorepo Branch Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `executing-plans` or an equivalent step-by-step execution workflow. Do not execute destructive cleanup until every verification gate in this plan is green.

**Goal:** Replace the current two-physical-repository workflow with one GitHub repository that has a clean public `main` branch and a full internal `dev` branch.

**Architecture:** `dev` is the complete development branch and source of truth. `main` is the public release branch, synchronized from `dev` by an explicit whitelist plus a public-branch leakage audit. Local development may still use Git worktrees during migration; the goal is one GitHub repository and one shared Git object store, not blind deletion of the public folder.

**Tech Stack:** Git, GitHub, Python package layout under `src/stataflow`, pytest, GitHub Actions.

---

## 0. Current Relationship Between the Two Folders

There are two local folders:

| Folder | Role | Current branch | Remote situation |
|--------|------|----------------|------------------|
| `D:/OneDrive - SAIF/PhD3/StataFlow` | Full internal development repository | `fix/v1.0.1-hotfix` | `origin` points to legacy `Statapy.git`; `stataflow` points to `StataFlow.git` |
| `D:/OneDrive - SAIF/PhD3/StataFlow_open_source` | Public export repository | `update/v1.1.0-sync` | `origin` points to `StataFlow.git` |

Important facts verified from the current worktree:

- Internal repo `fix/v1.0.1-hotfix` is ahead of its local `main` by 17 commits.
- Internal repo `fix/v1.0.1-hotfix` is ahead of `stataflow/main` by 21 commits.
- Internal repo `origin` is **not** the intended StataFlow remote; it is `https://github.com/ZhenHaoFu810/Statapy.git`.
- Public repo `update/v1.1.0-sync` is one commit ahead of public `main`.
- Both folders currently have uncommitted changes. Migration must not push, merge, or delete anything until those changes are explicitly handled.

This means the original plan's broad idea is correct, but the exact execution order is unsafe unless remotes, dirty worktrees, and public-folder uniqueness are handled first.

---

## 1. Final Target

Remote repository:

```text
https://github.com/ZhenHaoFu810/StataFlow.git
```

Branch model:

| Branch | Contents | Purpose |
|--------|----------|---------|
| `main` | Public package only: source, non-golden tests, examples, public datasets, user docs, CI | PyPI / open-source release view |
| `dev` | Full internal project: all docs, audit evidence, golden tests, Stata artifacts, scripts, workspace files | Development source of truth |

Recommended local layout after migration:

```text
D:/OneDrive - SAIF/PhD3/StataFlow/          # dev worktree, full internal view
D:/OneDrive - SAIF/PhD3/StataFlow_public/   # optional main worktree, public view
```

`StataFlow_open_source/` should be kept as a backup until the public branch has been verified and pushed.

---

## 2. Non-Negotiable Safety Gates

Do not proceed past Phase 0 unless all of these are true:

- `StataFlow` dirty worktree has been committed, stashed, or intentionally documented.
- `StataFlow_open_source` dirty worktree has been committed, stashed, or intentionally documented.
- No command will push to legacy `Statapy.git`.
- Public `main` has been checked for internal files before push.
- `StataFlow_open_source/` is not deleted until public `main` and `dev` are both present on `StataFlow.git`.

Use explicit remote names until remotes are normalized:

- In `StataFlow`, use `stataflow` for `https://github.com/ZhenHaoFu810/StataFlow.git`.
- Do not use `origin` in `StataFlow` unless it has first been renamed or repointed.

---

## 3. Phase 0: Snapshot and Freeze

**Goal:** Preserve both folders before any branch surgery.

1. Record current status:

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' status --short --branch
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' remote -v

Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_open_source"
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_open_source' status --short --branch
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_open_source' remote -v
```

2. Create filesystem backups outside Git:

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item -Recurse -LiteralPath "StataFlow" -Destination "StataFlow.backup.$stamp"
Copy-Item -Recurse -LiteralPath "StataFlow_open_source" -Destination "StataFlow_open_source.backup.$stamp"
```

3. Handle dirty worktrees:

```powershell
# In StataFlow: commit or stash current development/revalidation changes.
# In StataFlow_open_source: commit or stash the did_imputation.py change before merging.
```

Expected result:

- No uncommitted changes in either repository, or every remaining change is intentionally documented and not part of migration execution.

---

## 4. Phase 1: Normalize Remotes in the Internal Repository

**Goal:** Prevent accidental pushes to `Statapy.git`.

Current internal remotes are:

```text
origin    https://github.com/ZhenHaoFu810/Statapy.git
stataflow https://github.com/ZhenHaoFu810/StataFlow.git
```

Recommended cleanup after the dirty worktree is safe:

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git remote rename origin statapy-legacy
git remote rename stataflow origin
git remote -v
```

Expected result:

```text
origin          https://github.com/ZhenHaoFu810/StataFlow.git
statapy-legacy  https://github.com/ZhenHaoFu810/Statapy.git
```

If you do not want to rename remotes yet, every command in later phases must use `stataflow` explicitly.

---

## 5. Phase 2: Finalize the Current Public Sync Branch

**Goal:** Make the existing public `update/v1.1.0-sync` branch safe before it becomes `main`.

In `StataFlow_open_source`:

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_open_source"
git status --short --branch
```

The current dirty file is:

```text
src/stataflow/estimators/did_imputation.py
```

That change matches the internal `NEW-DID-002` aggregate sample-screening fix and should either be committed into `update/v1.1.0-sync` or regenerated from the internal repo. Do not merge `update/v1.1.0-sync` into `main` while it is dirty.

Then merge:

```powershell
git checkout main
git merge --ff-only update/v1.1.0-sync
git push origin main
```

If `--ff-only` fails, stop and inspect the graph. Do not use `--no-ff` merely to force progress; the public branch should stay simple unless there is a documented reason for a merge commit.

Verification:

```powershell
git status --short --branch
git log --oneline --decorate -5
```

---

## 6. Phase 3: Create and Push the Full `dev` Branch

**Goal:** Put the complete internal development state on the same GitHub repository.

In `StataFlow`, after remotes are normalized:

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git checkout fix/v1.0.1-hotfix
git status --short --branch
git branch dev
git push -u origin dev
```

If the local branch `dev` already exists, use:

```powershell
git branch -f dev fix/v1.0.1-hotfix
git push -u origin dev
```

Verification:

```powershell
git ls-remote --heads origin main dev
```

Expected result:

- `refs/heads/main` exists and points to the public branch.
- `refs/heads/dev` exists and points to the full internal branch.

---

## 7. Phase 4: Replace Local Public Folder With a Git Worktree

**Goal:** Keep an optional public view without duplicating Git objects or relying on export scripts.

Do not delete `StataFlow_open_source` yet. First create a new public worktree:

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git worktree add "../StataFlow_public" main
```

Verify public structure:

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git status --short --branch
Test-Path docs/audit
Test-Path scripts
Test-Path stata
Test-Path tests/golden
```

Expected result:

- `docs/audit`, `scripts`, `stata`, and `tests/golden` are absent in `StataFlow_public`.

Only after this verification and a successful push should `StataFlow_open_source` be archived or deleted.

---

## 8. Phase 5: Define the Public Sync Procedure

**Goal:** Replace export scripts with an explicit public sync workflow.

The public branch should be rebuilt from a whitelist and then audited. Do not rely on partial checkout alone, because it does not remove files that were previously public but later removed from the whitelist.

Recommended sync algorithm, executed from the public `main` worktree:

1. Start from clean `main`.
2. Restore public files from `dev`.
3. Remove forbidden paths.
4. Run a leakage audit.
5. Run public tests.
6. Commit and push.

Public whitelist:

```text
README.md
README.zh-CN.md
LICENSE
pyproject.toml
.gitignore
VALIDATION.md
.github/workflows/ci.yml
src/stataflow/
examples/
tests/
research/data/public/
research/results/validation/
docs/USER_GUIDE.md
docs/USER_GUIDE.zh-CN.md
docs/cookbook.md
docs/cookbook.zh-CN.md
```

Forbidden paths on `main`:

```text
AGENTS.md
CLAUDE.md
.claude/
docs/architecture/
docs/audit/
docs/operations/
docs/research/
docs/tasks/
docs/project-charter.md
docs/backlog.md
scripts/
stata/
workspace/
tests/golden/
research/vendor/
session_restore/
debug_*.py
extract_cdsy.py
golden_test_results.txt
*.zip
```

Use a small script in `dev`, for example `scripts/release/sync_public.ps1`, to encode this workflow. The script itself must not be present on `main`.

---

## 9. Phase 6: CI and Branch Protection

**Goal:** Make leakage difficult after the migration.

Update CI so `main` includes a public-structure audit:

```yaml
- name: Verify no internal files in public branch
  if: github.ref == 'refs/heads/main'
  run: |
    test ! -d docs/audit
    test ! -d docs/architecture
    test ! -d docs/operations
    test ! -d scripts
    test ! -d stata
    test ! -d workspace
    test ! -d tests/golden
    test ! -d research/vendor
    test ! -f AGENTS.md
    test ! -f CLAUDE.md
```

Recommended GitHub branch protection:

- Protect `main`.
- Require PR before merging.
- Require CI to pass.
- Disable force pushes.
- Require review for changes touching `pyproject.toml`, `.github/`, or release metadata.

---

## 10. Rollback Plan

Rollback is only safe if backups and branch pointers are preserved.

If migration fails before deleting `StataFlow_open_source`:

```powershell
# Continue using the old open-source folder.
# Delete only the newly created worktree if needed:
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git worktree remove "../StataFlow_public"
```

If `dev` was pushed incorrectly:

```powershell
# Do not force-push until the bad ref and correct ref are written down.
git ls-remote --heads origin dev
git log --oneline --decorate -5 dev
```

Then decide whether to delete the remote branch or push a corrected one.

---

## 11. Execution Checklist

- [ ] Commit or stash dirty changes in `StataFlow`.
- [ ] Commit or stash dirty changes in `StataFlow_open_source`.
- [ ] Back up both folders.
- [ ] Normalize internal remotes so `origin` points to `StataFlow.git`, or use `stataflow` explicitly.
- [ ] Merge `update/v1.1.0-sync` into public `main` only after the public repo is clean.
- [ ] Push public `main`.
- [ ] Create and push full `dev` from `fix/v1.0.1-hotfix`.
- [ ] Create `StataFlow_public` worktree from `main`.
- [ ] Verify public branch contains no forbidden paths.
- [ ] Add or update public sync script on `dev`.
- [ ] Add CI public-structure audit.
- [ ] Run `pytest tests/ -v --ignore=tests/golden/ --ignore=tests/benchmarks/` on public branch.
- [ ] Run example smoke scripts on public branch.
- [ ] Keep `StataFlow_open_source` backup for at least 2-4 weeks before deletion.

---

## 12. Recommendation

The optimal path is **single GitHub repository + two branches + optional Git worktree**, not immediate deletion of the open-source folder and not branch switching inside a dirty internal worktree.

This keeps the public branch clean, preserves the internal branch as the source of truth, avoids duplicate Git object storage, and gives a reversible migration path.

