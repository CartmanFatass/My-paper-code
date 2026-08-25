---
name: hmasd-root-control
description: Reconcile, prioritize, and advance the durable HMASD workflow from the Root session.
---

# HMASD Root Control

## Purpose

Keep one user-facing Root session aligned with the durable Portfolio, direction,
run, external-review, runtime, worktree, and Git authorities. Root directly owns
cross-direction ranking, lifecycle, resource attention, EM/CM dispatch,
reconciliation, user boundaries, and final integration. There is no Portfolio
manager session; `PORTFOLIO.md` remains the durable scientific authority rather
than an agent identity.

## Inputs

- `docs/research/portfolio/PORTFOLIO.md` as the sole persistent scientific goal,
  ranking, synthesis, and lifecycle-reason authority.
- `docs/research/portfolio/workflow/registry.json` as the sole lifecycle and
  dependency authority.
- Candidate `DIRECTION.md` references and hashes, direction research and
  engineering states, and settled EM/CM envelopes.
- `.omp/runtime/agents.json` and `.omp/runtime/worktrees.json` when present.
- Active Hub jobs, process exits, local run manifests, Agentify operation/archive
  references, and the exact `omp/workflow` Git state.
- Exact proposed-command estimates when resource cost affects priority: absolute
  peak memory, wall-clock time, storage, accelerator needs, and current
  workstation capacity. A relative multiplier alone is not a resource estimate.
- The previous generation, material transition, or startup/compaction boundary.

Tracked paths are repository-relative POSIX references. Concrete handles, PIDs,
absolute worktree paths, and local tab mappings remain in ignored runtime state.

## Bounded cycle

1. On start, resume, or a detected compaction boundary, read the Root goal from
   `PORTFOLIO.md`; never recover it from a prompt summary or Dashboard.
2. Mechanically validate the registry, resolve every referenced Portfolio and
   direction path and hash, then reconcile runtime mappings, Hub jobs,
   worktrees, manifests, external references, and Git once. Classify each
   observation as current, stale, missing, conflicted, or materially changed.
3. Rank eligible directions from current authorities and newest cited handoffs.
   Qualify work by expected discriminative information, specificity, portfolio
   leverage, dependencies, and executable next action. Target 2–8 ACTIVE
   directions only when justified; zero is a valid `IDLE` result.
4. Separate scientific qualification from resource scheduling. Missing command
   estimates create preparation work, never a parking reason. Schedule exact
   commands within safe workstation capacity when estimated at most 7200
   seconds. Above 7200 seconds, attempt a performance-reasonableness review and
   request explicit user approval. Unsafe memory is refused mechanically and
   reduced, batched, or sharded.
5. Record every create, activate, park, merge, close, or reactivate reason in
   `PORTFOLIO.md`, then replace the registry through `scripts/hmasd_state.py`
   using expected-revision CAS and the authority writer `Portfolio`. Never use a
   relative cost multiplier or absent estimate as the sole parking reason.
6. Reuse one stable `EM-<direction>` or `CM-<direction>` logical session while
   its role, identity, assignment-owned paths, and frozen checkpoint remain
   compatible. Hub may update compatible managers in place. Dispatch EMs and
   CMs directly from Root; no intermediate Portfolio session exists.
7. Keep the task tree at two subagent levels: Root → EM/CM → specialist. EM and
   CM are the only project spawn-capable managers; specialists are leaves.
   Ordinary worker target is 28, preserving four Root/review/recovery slots.
8. Treat a completed research or engineering round, accepted-result promotion,
   terminal-run evidence promotion, external prompt/archive readiness,
   Portfolio lifecycle change, or schema migration as a material checkpoint.
   The trigger is event-driven, not a timer or recurring poller.
   Before dispatching work that consumes it or stopping Root, validate every
   changed path, stage only Root-owned authority paths and assignment-owned
   paths named by settled envelopes, commit the checkpoint, and attempt its
   push to `omp/workflow`. Never use `git add -A` for automatic checkpoints;
   leave unrelated changes unstaged and return a conflict when one path mixes
   ownership. Exclude runtime maps, raw runs, generated logs, secrets, and
   unverified source.
9. Fetch and compare the remote tip before a checkpoint push. Reconcile an
   unknown push outcome by fetching before retry. Ordinary intermediate events
   may batch into the next checkpoint, but no completed material checkpoint may
   cross a Root wake-cycle boundary uncommitted.
10. Wait on Hub completion, process exit, an observed file change, or one
   bounded reassessment. Never continuously poll or create a successor merely
   because an observation is delayed. Apply one safe recovery route when
   needed.
11. Stop only at `IDLE`, `COMPLETE`, an explicit user decision request, or an
   exhausted safe recovery result.

The cycle has one reconciliation pass and at most one bounded reassessment per
wake-up. A new wake-up is required for another cycle.

## State writes

- Write lifecycle reasons and cross-direction synthesis only to
  `PORTFOLIO.md`.
- Replace `registry.json` only through `scripts/hmasd_state.py` with
  expected-revision CAS and writer `Portfolio`; the writer names the durable
  authority, not a separate agent.
- Write Root-owned `.omp/runtime/agents.json` and
  `.omp/runtime/worktrees.json` only through the state CLI with expected
  revision.
- Invoke documented worktree, run, external-review, and Git CLIs; do not import
  private functions or duplicate their state writers.
- Do not write direction research/engineering state, Agentify ledgers, or run
  manifests. Root may create and integrate one verified candidate on
  `omp/workflow` through the Git contract.

## Returned result envelope

Return the common v1 envelope with role `root`, logical identity `Root`, and
payload kind `root` for ordinary reconciliation. When the cycle changes or
reassesses portfolio lifecycle, Root may return payload kind `portfolio` with
`direction_actions`, the exact `portfolio_ref`, and `registry_revision`; that
payload remains Root-owned.

```json
{
  "schema_version": 1,
  "role": "root",
  "logical_identity": "Root",
  "generation": 1,
  "assignment_id": "<wake-id>",
  "status": "COMPLETED",
  "materiality": "PORTFOLIO",
  "summary": "<observed reconciliation and direction outcome>",
  "changed_paths": [],
  "state_refs": [],
  "artifact_refs": [],
  "checkpoint_sha": null,
  "decision_requests": [],
  "next_action": null,
  "payload": {
    "kind": "portfolio",
    "direction_actions": [],
    "portfolio_ref": "docs/research/portfolio/PORTFOLIO.md",
    "registry_revision": 1
  }
}
```

Use `PARTIAL`, `BLOCKED`, or `FAILED` only for the observed condition. A user
decision request binds the exact direction, run, or operation and frozen
references; an Advisor, review, Dashboard, hash, or historical record is never
the token.

## Failure handling

Re-read the authoritative source and classify the failure before acting.
Preserve exact bytes on stale revision or unsupported schema and record only a
materially distinct recovery attempt. Never replay an unknown run or external
send, accept late output against a newer checkpoint, silently reinterpret
scientific or Git facts, manufacture lifecycle states, activate weak work for a
quota, or turn missing resource information into a scientific veto. A missing
estimate requires an estimate-producing next action. If no safe route remains,
return the precise user blocker and stop.

## Deletion condition

Delete this Skill when Root no longer owns durable portfolio selection,
lifecycle, resource attention, reconciliation, direct EM/CM dispatch, and Git
integration, and an approved replacement preserves the same authorities,
two-level task tree, recovery, and no-polling boundaries.
