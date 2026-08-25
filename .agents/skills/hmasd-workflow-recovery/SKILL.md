---
name: hmasd-workflow-recovery
description: Recover one scoped HMASD failure from durable facts without replaying unknown effects.
---

# HMASD Workflow Recovery

Use for one observed scope only: pure research, manager task, partial
code/worktree, running run/process, memory refusal, Git/push, external send,
late output, Dashboard projection, runtime mapping, or local evidence failure.
Read its existing authority revision, effect/run/worktree facts, and Work Packet
refs before any action.

1. Classify the observed failure and scope; never use bare `BLOCKED` as a
   workflow control signal.
2. Reconstruct missing runtime references once from durable facts after
   compaction. Reuse a matching manager identity; report duplicate or ambiguous
   identity rather than creating another one.
3. For an actual effect, observe its receipt, any running process, remote, or
   operation first.
   `UNKNOWN` run, push, and external-send outcomes are observe-only: never replay
   and never resend.
4. Repair one bounded local cause when evidence supports it. A new authority
   revision or material evidence may create a new immutable Work Packet; do not
   repeat the same packet against unchanged facts.
5. Record only in the existing authority/result contract, reconcile once, and
   return a precise resume condition. Unrelated scopes continue.

Pure research is also a scoped failure. A late output whose generation or
checkpoint does not match is superseded evidence; newer authority always wins.
Work Packet delivery is at-least-once for the same `work_id`, so intake must be
idempotent. Actual effects remain at-most-once.

Do not create a recovery FSM, global route budget, duplicate recovery ledger,
or new durable authority. Preserve bytes on revision, generation, checkpoint,
or schema conflict and report the exact affected scope.

Do not count materially distinct routes or keep a three-route budget; duplicate
attempts, budget exhaustion, and a generic user-visible blocker are retired
controls.
