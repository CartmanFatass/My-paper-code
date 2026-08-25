---
name: hmasd-git-integration
description: Provision, verify, and mechanically integrate one assignment-owned HMASD candidate on main.
---

# HMASD Git Integration

Use native Windows Git only. Sibling worktrees live in
`C:/Projects/HMASD-worktrees`, use `<direction>-<kind>-<assignment>`, and keep
the branch namespace `omp/<direction>/<kind>/<assignment>`; target is `main`.

Every operation includes exact base SHA, direction/CM identity, assignment, and
allowed paths. Resolve all paths canonically and refuse reparse aliases, dirty
state, stale base, conflicts, multiple candidate commits, namespace violations,
or changed paths outside the assignment.

Direction-owned assignments may modify, test, commit, and push if the exact
assignment authorizes it. Shared-core changes require one user confirmation
bound to the exact action, enforced by Root. Path tier policy only classifies
and records; it is additive, never widens `allowed_paths`, and does not create
an approval service. The existing Markdown confirmation records Action digest,
Base SHA, sorted exact paths, objective/non-goals, and allowed Git effects.
Root canonicalizes those fields as JSON and verifies its SHA-256 before the
effect and before commit; once available, it appends the candidate SHA result
ref. An implementation folder name may differ from direction ID: ownership is
the Work Packet's exact `owned_paths` plus authority refs, while path policy
only classifies paths.

Root mechanically applies one verified candidate once with
`scripts/hmasd_worktree.py`, rechecks target status and commit identity, and
does not edit conflicts. A push is at-most-once: unknown outcome is observed by
fetch/compare, never blindly resent. Never stage unrelated user or runtime
output.
