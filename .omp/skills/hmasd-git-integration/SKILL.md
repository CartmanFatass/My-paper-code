---
name: hmasd-git-integration
description: Verify and integrate one assignment-owned candidate on omp/workflow.
---

# HMASD Git Integration

## Purpose

Keep Git integration direction-scoped and fail-closed. Resolve canonical paths,
the exact `omp/workflow` base, assignment ownership, and one verified candidate
commit. Root owns shared-authority/recovery integration; a matching EM or CM
owns its orthogonal direction checkpoint without gaining cross-direction
authority.

## Inputs
- Canonical repository root, target `omp/workflow` branch, exact base SHA, and
  actor `root | em:<direction> | cm:<direction>`.
- Provisioned assignment worktree, one candidate commit, assignment-owned path
  set, direction ID, and worktree kind `research | engineering`.
- Focused verification references and current target/remote observations.

## Bounded cycle

1. Resolve repository, worktree, target, and receipt paths canonically. Refuse
   symlinks, destructive ambiguity, dirty target/worktree state, non-OMP target
   branches, and out-of-scope paths.
2. Verify the candidate is one non-merge commit directly descended from the
   declared base and every changed path is assignment-owned. The actor must be
   Root or exactly `em:<direction>` for a research worktree or
   `cm:<direction>` for an engineering worktree.
3. Prepare and apply the clean candidate to `omp/workflow` once. Before push,
   fetch and compare the remote tip. Push only when the observed remote remains
   the candidate's predecessor. A stale base, non-fast-forward, mixed
   ownership, dirty target, or conflict stops unchanged and returns exact
   evidence to Root; the manager never rebases, merges, or retries it blindly.
4. Root uses the same primitive for shared-authority and recovery integration.
   Direction managers batch ordinary intermediate events into one
   cycle-completion checkpoint rather than requesting Root commits after every
   transition.

One bounded cycle permits one candidate/apply/push attempt. No automatic retry,
conflict loop, or multi-candidate merge is permitted.

## State writes

- Git alone is authoritative for candidate and integration commits.
- EM writes only its provisioned research worktree; CM writes only its
  provisioned engineering worktree. Root writes shared/recovery checkpoints.
- Do not stage unowned paths, generated runtime data, raw runs, secrets,
  unverified source, or unrelated user changes. Never use `git add -A`.
- Runtime worktree registry/receipt updates remain helper-owned bookkeeping;
  they do not grant scientific or integration authority.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-git-integration"` and payload:

```json
{
  "kind": "git",
  "direction_id": "<direction-id>",
  "base_sha": "<exact-base-sha>",
  "candidate_sha": "<candidate-sha>",
  "integrated_sha": "<integrated-commit-sha>",
  "changed_paths": [],
  "actor": "root | em:<direction> | cm:<direction>"
}
```

A refusal is `status: "BLOCKED"` or `"FAILED"` with the exact
path/base/conflict reference and no partial integration.

## Failure handling

Refuse dirty worktrees, stale bases, conflicts, multiple commits, mismatched
actor/direction/kind, target-branch violations, canonical path failures,
out-of-scope files, focused-check failures, and non-fast-forward pushes. Leave
the target unchanged on pre-apply refusal. After an unknown push outcome, fetch
before any retry. Return exit code `4` for stale base, `5` for ownership/path
refusal, `6` for observed conflict, and `1` for another directly observed
failure.

## Deletion condition

Delete this Skill when an approved integration primitive enforces canonical
paths, one-commit assignment ownership, actor/direction/kind matching, exact
base, target namespace, and unchanged-on-refusal semantics without returning
direction-owned routine commits to Root.
