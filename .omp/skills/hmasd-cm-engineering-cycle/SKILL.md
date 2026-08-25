---
name: hmasd-cm-engineering-cycle
description: Coordinate one bounded engineering scope from frozen direction evidence.
---

# HMASD CM Engineering Cycle

## Purpose

Advance one `CM-<direction>` logical identity through scope freeze,
implementation, focused verification, and one assignment-owned Git checkpoint.
CM coordinates work; it never silently redefines science, grants approval, or
integrates outside its provisioned engineering worktree.

## Inputs

- The active registry direction and `DIRECTION.md` heading/SHA references.
- A frozen engineering scope, acceptance references, base `omp/workflow` SHA,
  assignment-owned paths, and current engineering state revision.
- Existing worktree/run references and bounded specialist assignments.

## Bounded cycle

1. Freeze scope and acceptance references from `DIRECTION.md`; map files,
   interfaces, exported symbols, and ownership before decomposing work.
2. Dispatch two specialists by default and at most six when contracts are
   disjoint, ownership is explicit, and each result is independently useful.
3. Require Implementer LSP references before exported-symbol edits and LSP rename
   for cross-file renames. Keep Reviewer and Verifier advisory and focused.
4. Request observed runs only through the Result Run Skill. Collect exact
   verification evidence. A scientific ambiguity or missing principle is a
   durable `next_action.owner=EM` research request to Root, never a CM
   reinterpretation. Runnable code or verification remains owner `CM`; one
   frozen result-bearing command becomes owner `EXPERIMENT_OPERATOR`.
5. At cycle completion, use the provisioned engineering worktree and Git
   Integration Skill to stage only assignment-owned paths, create/apply one
   commit as `cm:<direction>`, fetch/compare, and push `omp/workflow`. Report
   stale base, dirty target, non-fast-forward, mixed ownership, or conflict to
   Root without resolving it. Return one bounded result with an explicit next
   owner.

A cycle has one frozen scope, one specialist wave at a time, and one candidate
boundary. A parent wake-up is required for a new scope or material checkpoint;
CM never polls or creates successor Implementers for delayed evidence.

## State writes

- Write engineering scope/progress only to the assigned direction's
  `workflow/engineering/state.json` through the state CLI and expected revision.
- Write source only inside assignment-owned paths in the provisioned worktree.
- Invoke run and Git CLIs; do not write run manifests, Portfolio/EM state,
  external ledgers, or Root runtime registries.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-cm"`, logical identity
`CM-<direction-id>`, and payload:

```json
{
  "kind": "cm",
  "direction_id": "<direction-id>",
  "scope_ref": "<repo-relative-scope-reference>",
  "base_sha": "<sha256>",
  "candidate_sha": null,
  "verification_refs": [],
  "integrated_sha": null
}
```

A candidate is evidence, not integration. `integrated_sha` remains `null` until
Root verifies and applies the single candidate on `omp/workflow`.

## Failure handling

Refuse dirty worktrees, stale bases, conflicts, out-of-scope paths, missing LSP
rename evidence, and unsafe resource plans. Preserve source and state bytes on
CAS conflict. Never reinterpret scientific claims, run a successor for a missing
result, or treat Reviewer/Advisor/Verifier output as permission. Return the
precise resume condition or user boundary.

## Deletion condition

Delete this Skill when a reviewed engineering coordinator owns the same frozen
scope, assignment paths, LSP evidence, bounded specialist fan-out, and Root-only
integration boundary without duplicating engineering state.
