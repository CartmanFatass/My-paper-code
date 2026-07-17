# HMASD Collaboration Protocol

## Controller and Context

Use one active root controller in the project directory. The controller owns
root memory, Git, scientific interpretation, experiment authority, and the
user-facing result.

- Implementer context: three to five recent relevant turns plus `BRIEF.md`.
- Reviewer context: one to three relevant turns plus the same `BRIEF.md`.
- Exclude retired routes, unrelated experiments, and old workflow discussion.
- Use only models exposed by the live spawn surface. Specify a model only when
  creating a subagent and the task requires it; never mutate an existing task's
  model.

## Work Shapes

For coupled work, use one implementer. For parallel work, limit the first phase
to two or three disjoint writers, lock their shared interface in the brief, and
give integration files to one later owner. One file never has two writers.

A mapper is exceptional: cross-repository work, unknown entry points, or a large
independent interface inventory. Its stable output is an edit to the existing
brief, not a new artifact or a message relay chain.

## Reviewer

Use one fresh combined reviewer for the complete stable diff, focused evidence,
brief, and necessary contract. The reviewer is read-only and returns either
`APPROVED` or findings tied to paths and contract clauses. Send accepted
findings directly to the owning implementer. Allow one repair/re-review loop.

Use multiple reviewers only when two independent high-risk cores genuinely
require separate expertise.

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
