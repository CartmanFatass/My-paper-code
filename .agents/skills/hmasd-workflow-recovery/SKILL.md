---
name: hmasd-workflow-recovery
description: Use when recovering one scoped HMASD project, direction, feature, or Effect failure from observed durable facts.
---

# HMASD Workflow Recovery

Classify and return one failure as `project`, `direction`, `feature`, or
`effect`, with its exact ref and `resume_condition`; never propagate bare
`BLOCKED`. Before an Effect, read the cited authority revision, packet/return,
runtime observation, and receipt. Runtime maps are reconstructable local
handles, not authority: after compaction reconstruct once from durable sources.

| Failure class | Bounded recovery |
| --- | --- |
| Pure research task failed | Preserve partial prose as unaccepted; make a new attempt only with a materially distinct assignment. |
| Manager missing after resume | Read durable logical identity/generation; revive that matching generation or reconstruct once, never blindly duplicate a manager. |
| Partial code work / worktree | Inspect the existing receipt/worktree; resume or retain it for recovery, never apply the patch or provision twice. |
| Running result | Reconcile the manifest once. If process identity is unproven, mark/retain `UNKNOWN`; never relaunch or execute the command again. |
| Memory refusal | Reduce, batch, or shard; never request approval for overcommit. |
| Git conflict or stale base | Preserve bytes and return to Root for a new integration plan; never auto-resolve a semantic conflict. |
| Push outcome unknown | Fetch the remote tip and compare; never resend the push. |
| External commitment unknown | Observe/verify the existing operation and import an exact archive idempotently; never resend. |
| Late specialist result | Compare generation, checkpoint, revision, and compaction facts read-only; reconcile before effectful work. A lower-generation or mismatched-checkpoint result is superseded evidence under newer state, never overwrite it. |
| Dashboard failure | Restart the read-only projection or run without Dashboard; it never blocks workflow. |

Typed Effect observation uses the existing kind/resource/operation contract.
`UNKNOWN` send, creation, run, push, and external commitment are observe-only;
never replay, resend, or create a semantic replacement. Clerk handles only an
exact program defect or legacy incompatibility, never ordinary recovery.

For a terminal task without return, use the same `work_id` and fresh native
history. Deduplicate `(effect_class, assignment_id, route)`: an identical route
does not consume budget; only a materially distinct route does. At most three
distinct routes are allowed. On exhaustion emit one scope-specific
`RECOVERY_EXHAUSTED` user-visible blocker with `failure_class` and
`resume_condition`, then request the user decision; unrelated scopes continue.

Do not add a recovery FSM, queue, ledger, gate, daemon, or new durable
authority.
