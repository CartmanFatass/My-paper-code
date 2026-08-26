---
name: hmasd-git-integration
description: Use when provisioning, verifying, committing, pushing, or mechanically integrating one exact HMASD candidate.
---

# HMASD Git Integration

Use native Windows Git. Worktrees are
`C:/Projects/HMASD-worktrees/<direction>-<kind>-<assignment>` on
`omp/<direction>/<kind>/<assignment>`; integration target is `main`.

Freeze base SHA, CM/direction identity, assignment, paths, and requested Git
Effects. Resolve paths canonically; refuse aliases, dirty/stale/conflicted
state, multiple candidates, and out-of-scope changes. Direction-owned work may
modify, test, commit, and push inside its assignment.

Before any shared-core change, run Work Packet `shared-core-record --packet …`.
Place its exact fence only in the v1 exact-authority allowlist: `AGENTS.md`,
`docs/project/WORKFLOW_PROTOCOL.md`, `docs/research/portfolio/PORTFOLIO.md`,
or the matching direction's `DIRECTION.md`; obtain the user's exact
confirmation there. It binds Action digest, Base SHA, sorted paths,
objective/non-goals, and real typed operations such as
`WORKTREE_APPLY_INTEGRATION` and `WORKTREE_PUSH`. Warn for danger but do not
create a permission service. Root verifies
the record/current base before the Effect, records the candidate SHA afterward,
and mechanically applies one verified candidate. A push with unknown outcome
is fetch/compare observation only, never a resend. Never stage unrelated files
or manually resolve integration conflicts.
