---
name: hmasd-root-control
description: Reconcile and orchestrate HMASD work from the Root top-level task without making Portfolio, scientific, or engineering decisions.
---

# HMASD Root Control

Root is the low-cost operational orchestrator. It has the tools needed to route, wait, recover, validate archives, and integrate Git, but material decisions remain with User, Portfolio, EM, or CM.

## Inputs

Read the durable Portfolio/registry, direction states, run manifests, Agentify references, Git/worktree state, and ignored .codex/runtime/tasks.json when present. Treat live task/thread/host/cursor IDs only as reconstructable runtime references.

During the runtime transition, `.codex/runtime/worktrees.json` is the canonical
Root-owned journal. A missing canonical journal may be initialized from
`.omp/runtime/worktrees.json` only after the state CLI validates schema, receipt,
and Git/path facts; the legacy source remains read-only. Canonical-only state is
valid. If both documents exist, use canonical: a canonical revision ahead of
legacy is normal forward progress, equal revisions require matching rows/facts,
and a legacy-ahead revision or same-revision conflict fails closed. Never write
the legacy journal. `runtime_agents` is retired; native task listing plus
`runtime_tasks` replaces that map.

Consume a Decision Packet only after validating its sender identity, generation, authority paths, revisions, checkpoint SHA, scope, owned paths, and requested action. A packet is evidence and routing input, not an approval token.

## One bounded wake

1. Reconcile durable state, existing project tasks, runtime refs, worktrees, manifests, external operations, and Git once.
2. Classify every observation as current, stale, missing, conflicted, or materially changed.
3. Route validated work to an existing matching Portfolio, EM, or CM top-level task using task coordination tools when available.
4. Creating a user-owned Codex task requires an explicit user request. If the required peer task does not exist and no such request is present, return that exact creation request instead of spawning a manager subagent.
5. Use only direct leaf subagents allowed by hmasd-root-task; never spawn Portfolio, EM, or CM.
6. Wait with bounded, cursor-aware task snapshots or one owned process session. Do not repeatedly ingest full transcripts or poll with model turns.
7. Apply only mechanical in-scope choices. Route any change in direction value, science, engineering design, or material scope back to its decision owner.
8. Perform exact Root-owned archive/Git/runtime effects, checkpoint the observed result, and stop at IDLE, COMPLETE, one user/owner decision, or an exhausted safe recovery route.

## Owned writes

Root writes ignored Codex task/worktree runtime refs and invokes existing CLIs. Root validates exact external archive bytes and performs final Git integration. Root does not write Portfolio conclusions, direction research/engineering state, Agentify commitment, or run manifests.

A runtime map can cache logical identity, kind, direction ID, generation, task title, thread/host/cursor references, project root, worktree ref, checkpoint SHA, lifecycle, and last-seen time. It is never identity authority and its absence never permits blind duplicate work.

## Failure handling

Unknown run or send outcome is observe-only. Missing runtime mapping is reconstructed once from durable facts and task listings. Duplicate or ambiguous task identity fails closed. One wake permits one safe reproduction and one materially distinct recovery route.
