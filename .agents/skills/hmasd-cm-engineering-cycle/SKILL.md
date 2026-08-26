---
name: hmasd-cm-engineering-cycle
description: Use when an HMASD CM task must complete one bounded engineering slice from frozen authority.
---

# HMASD CM Engineering Cycle

Validate the packet, engineering state, worktree, base SHA, exact owned paths,
and Effects. Decompose only across disjoint owned paths and give each direct
leaf the frozen goal, non-goals, interfaces, refs, and paths.

CM directly assigns each result-bearing command to one Experiment Operator via
`hmasd-result-run`. Direction-owned work may modify, test, commit, and push
within its exact assignment; shared-core follows `hmasd-git-integration`.

Keep review, same-scope repair, tests, verification/SANCheck, and candidate
preparation in this assignment. Update engineering state for its terminal
disposition and return through `hmasd-slice-interface`. Refuse stale/conflicted
worktrees and out-of-scope paths; unknown Effects are observe-only and do not
block unrelated directions.
