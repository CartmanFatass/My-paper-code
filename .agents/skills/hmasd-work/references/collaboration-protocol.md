# HMASD Collaboration Protocol

## Controller and Context

Use one active root controller in the project directory. The controller owns
root memory, Git, scientific interpretation, experiment authority, and the
user-facing result.

Direct controller work is the default. Collaboration exists only when the user
explicitly invokes the Skill or the controller delegates a coupled change that
writes at least two implementation files and uses a combined reviewer. The
current user-selected controller model is fixed; it is never changed or replaced
automatically. The controller retains all decisions about
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

Use one implementer by default. The implementer has
engineering judgment inside the frozen design, but does not select the route,
add mechanisms, reinterpret the experiment, or expand scope. A real mismatch
between design and code returns `BLOCKED` to the controller.

Use multiple implementers only when the brief lists mutually disjoint exclusive
file sets and a controller-frozen interface for each package. One file never has
two writers. Do not create a mapper or automatic delegation stage.

## Reviewer

Start review only after every writer has stopped and the controller has listed
the complete intended diff and check evidence. Use one fresh combined reviewer
for that diff, brief, and necessary contract. The reviewer is read-only and returns either
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
- `PACKAGE_READY`: the package changed only its exclusive files and its
  registered check exited zero, or the brief explicitly says `Check: none`.
- `REVIEW_READY`: every package is `PACKAGE_READY`, no writer remains active,
  and the controller listed the complete intended diff and check evidence.
- `COMPLETE`: the reviewer returned `APPROVED` or the controller disposed every
  finding, the controller inspected the final diff/evidence, and the temporary
  brief was removed.

Do not send heartbeat, unchanged-state, or ordinary file-completion messages.
Direct messages should carry only interfaces, findings, or one of these states.

## Local Runtime State

Use `.codex/collaboration/active/<task-id>/BRIEF.md` as the only task artifact.
The local conversation registry may retain persistent monitor and external-
review conversation identities, but it stores no prompts, responses,
credentials, decisions, progress, or file leases. Remove the task brief at the
completion boundary.
