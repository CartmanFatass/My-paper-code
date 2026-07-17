# HMASD Collaboration Protocol

## Controller and Context

Use one active root controller in the project directory. The controller owns
root memory, Git, scientific interpretation, experiment authority, and the
user-facing result.

Direct controller work is the default. When collaboration is justified, the
controller uses the strongest available model and retains all decisions about
the algorithm, architecture, causal route, reuse/replacement/deletion, data and
gradient flow, invariants, stability targets, and evidence boundary. These
decisions are frozen in the brief before implementation.

- Implementer context: three to five recent relevant turns plus `BRIEF.md`.
- Reviewer context: one to three relevant turns plus the same `BRIEF.md`.
- Exclude retired routes, unrelated experiments, and old workflow discussion.
- Use only models exposed by the live spawn surface. Specify a model only when
  creating a subagent and the task requires it; never mutate an existing task's
  model.

## Work Shapes

Use one implementer for a coherent core implementation. The implementer has
engineering judgment inside the frozen design, but does not select the route,
add mechanisms, reinterpret the experiment, or expand scope. A real mismatch
between design and code returns `BLOCKED` to the controller.

Use bounded implementers only for genuinely independent work packages with
disjoint files and a controller-frozen interface. One file never has two
writers. Do not create a mapper or automatic delegation stage.

## Reviewer

Use one fresh combined reviewer for the complete stable diff, focused evidence,
brief, and necessary contract. The reviewer is read-only and returns either
`APPROVED` or findings tied to paths and contract clauses. Send accepted
findings directly to the owning implementer. Allow one repair/re-review loop.

The reviewer checks fidelity, probability, gradient, RNG, replay, clock,
checkpoint, stability risks, scope, and obvious code-quality regressions. It
does not redesign the algorithm or start another process. Obvious scalar CUDA,
repeated packing, unnecessary synchronization, or module duplication is
reported directly to the controller; it does not create a performance gate or
additional reviewer.

## States

- `BLOCKED`: contract conflict, missing authority, file collision, or required
  scope expansion.
- `PACKAGE_READY`: one disjoint package is stable for integration.
- `REVIEW_READY`: the combined diff and direct evidence are stable.
- `COMPLETE`: the controller integrated and closed the task.

Do not send heartbeat, unchanged-state, or ordinary file-completion messages.
Direct messages should carry only interfaces, findings, or one of these states.

## Local Runtime State

Use `.codex/collaboration/active/<task-id>/BRIEF.md` as the only task artifact.
The local conversation registry may retain persistent monitor and external-
review conversation identities, but it stores no prompts, responses,
credentials, decisions, progress, or file leases. Remove the task brief at the
completion boundary.
