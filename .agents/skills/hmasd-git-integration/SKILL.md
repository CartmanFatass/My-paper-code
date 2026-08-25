---
name: hmasd-git-integration
description: Provision, verify, and integrate one assignment-owned HMASD candidate on main using native-host Git.
---

# HMASD Git Integration

Use native Windows Git consistently for this checkout. Never operate a Windows-created worktree with WSL Git.

## Contract

- Sibling root: C:/Projects/HMASD-worktrees.
- Worktree: <direction>-<kind>-<assignment>.
- Branch: omp/<direction>/<kind>/<assignment>.
- Target: main.
- Every provision/integration call includes exact base SHA, direction/CM identity, assignment, and at least one allowed path.

Resolve repository, Git common directory, sibling root, worktree, and candidate paths canonically. Refuse symlink or Windows reparse-point components, dirty target/candidate state, stale base, conflicts, multiple candidate commits, namespace violations, and changed paths outside the assignment.

CM/Implementer may prepare a candidate but do not integrate. Root applies one verified candidate once through scripts/hmasd_worktree.py, rechecks target status and commit identity, and pushes only when the user assignment explicitly includes push. Never stage unrelated user changes or runtime/generated output.
