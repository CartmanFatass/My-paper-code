---
name: hmasd-root-control
description: Reconcile and advance the durable HMASD workflow from the Root session.
---

# HMASD Root Control

## Purpose

Keep one user-facing Root session aligned with the durable Portfolio, direction,
run, external-review, runtime, worktree, and Git authorities. Root owns dispatch,
reconciliation, user boundaries, and final integration; a role, review, Advisor,
or Dashboard never becomes a second authority.

## Inputs

- `docs/research/portfolio/PORTFOLIO.md` and
  `docs/research/portfolio/workflow/registry.json` references.
- `.omp/runtime/agents.json` and `.omp/runtime/worktrees.json` when present.
- Active Hub jobs, process exits, local run manifests, Agentify operation/archive
  references, and the exact `omp/workflow` Git state.
- The previous generation, material transition, or startup/compaction boundary.

Tracked paths are repository-relative POSIX references. Concrete handles, PIDs,
absolute worktree paths, and local tab mappings remain in ignored runtime state.

## Bounded cycle

1. On start, resume, or a detected compaction boundary, read the Root goal from
   `PORTFOLIO.md`; never recover it from a prompt summary or Dashboard.
2. Reconcile registry, runtime mappings, Hub jobs, worktrees, manifests,
   external references, and Git once. Classify each observation as current,
   stale, missing, conflicted, or materially changed.
3. Reuse a matching Portfolio/EM/CM logical session and generation. Otherwise
   dispatch only the required non-blocking child with its documented contract;
   send only material transitions to a revived manager.
4. Dispatch Portfolio and required CM work, then wait on Hub completion, process
   exit, an observed file change, or one bounded reassessment. Never continuously
   poll or create a successor merely because an observation is delayed.
5. Apply one safe recovery route when needed. Stop with `IDLE`, `COMPLETE`, an
   explicit user decision request, or an exhausted recovery result.

The cycle has one reconciliation pass and at most one bounded reassessment per
wake-up. A new wake-up is required for another cycle.

## State writes

- Write only Root-owned `.omp/runtime/agents.json` and
  `.omp/runtime/worktrees.json` through `scripts/hmasd_state.py` with an
  expected-revision compare-and-swap.
- Invoke the documented worktree, run, external-review, and Git CLIs; do not
  import private functions or duplicate their state writers.
- Root may create the verified candidate commit on `omp/workflow`; it does not
  rewrite Portfolio, direction, research, engineering, or Agentify ledger facts.

## Returned result envelope

Return the common v1 envelope with:

```json
{
  "schema_version": 1,
  "role": "root",
  "logical_identity": "Root",
  "generation": 1,
  "assignment_id": "<wake-id>",
  "status": "COMPLETED",
  "materiality": "NONE",
  "summary": "<observed reconciliation outcome>",
  "changed_paths": [],
  "state_refs": [],
  "artifact_refs": [],
  "checkpoint_sha": null,
  "decision_requests": [],
  "next_action": null,
  "payload": {
    "kind": "root",
    "wake_reason": "<startup|resume|completion|file-change|compaction>"
  }
}
```

Use `PARTIAL`, `BLOCKED`, or `FAILED` only for the observed condition. A user
decision request must bind the exact affected direction/run/operation and frozen
references; an Advisor or review output is never the token.

## Failure handling

Classify the failure before acting. Re-read the authoritative source, preserve
bytes on stale revision or unsupported schema, and record a materially distinct
attempt. Never replay an unknown run or external send, never accept late output
against a newer checkpoint, and never silently reinterpret scientific or Git
facts. If no safe route remains, return the precise user blocker and stop.

## Deletion condition

Delete this Skill when Root no longer owns durable reconciliation and dispatch,
all state and lifecycle transitions have an approved replacement authority, and
that replacement preserves the same stop, recovery, and no-polling boundaries.
