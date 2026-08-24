---
name: hmasd-git-integration
description: Verify and integrate one assignment-owned candidate on omp/workflow.
---

# HMASD Git Integration

## Purpose

Keep Git integration small and Root-owned. Resolve canonical paths and the exact
`omp/workflow` base, enforce assignment ownership, and apply one verified
candidate commit without granting authority to tests, reviews, hashes, leases,
or historical documents.

## Inputs

- Canonical repository root, target `omp/workflow` branch, and exact base SHA.
- Candidate worktree, candidate commit/patch, assignment-owned path set, and
  expected direction/CM identity.
- Focused verification references and current target worktree status.

## Bounded cycle

1. Resolve repository and candidate paths canonically. Refuse symlinks,
   destructive ambiguity, dirty target state, non-OMP target branches, and
   out-of-scope paths.
2. Verify the candidate has one commit, the declared base SHA is exact, and the
   changed paths are a subset of the assignment-owned set. Run only the exact
   focused checks named by the assignment.
3. Apply the verified candidate to `omp/workflow` once. Re-read target status and
   commit identity; push only when Root's assignment explicitly includes it.
4. Batch ordinary intermediate events and create a material checkpoint reference
   for Root. Stop after this one integration boundary.

A new Root wake-up is required for another candidate. No automatic retry,
conflict loop, or multi-candidate merge is permitted.

## State writes

- Git alone is authoritative for candidate and integration commits.
- Root may update the durable checkpoint reference after the Git operation; the
  Skill does not write Portfolio, direction, run, external, Dashboard, or agent
  state.
- Do not stage unowned paths, generated runtime data, raw runs, secrets, or
  unrelated user changes.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-git-integration"` and payload:

```json
{
  "kind": "git",
  "direction_id": "<direction-id>",
  "base_sha": "<exact-base-sha>",
  "candidate_sha": "<candidate-sha>",
  "integrated_sha": "<integrated-commit-sha>",
  "changed_paths": []
}
```

A refusal is `status: "BLOCKED"` or `"FAILED"` with the exact path/base/conflict
reference and no partial integration.

## Failure handling

Refuse dirty worktrees, stale bases, conflicts, multiple commits, target-branch
violations, canonical path failures, out-of-scope files, and focused-check
failures. Leave the target unchanged on refusal. Return exit code `4` for stale
base, `5` for ownership/path refusal, `6` for observed conflict, and `1` for
another directly observed failure.

## Deletion condition

Delete this Skill when Root has an approved integration primitive that enforces
canonical paths, single-candidate ownership, exact base, target namespace, and
unchanged-on-refusal semantics without a second Git authority.
