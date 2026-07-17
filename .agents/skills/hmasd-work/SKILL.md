---
name: hmasd-work
description: Execute HMASD research design, implementation, diagnosis, focused verification, bounded multi-agent work, combined review, or collaboration setup through one active controller and one canonical task brief. Use for project code or algorithm work that may need planning, disjoint implementers, a repair pass, or evidence-backed completion. Do not use it to launch training merely because implementation is complete.
---

# HMASD Work

Keep the current root task as active controller. Read `memory/CURRENT_WORK.md`
first and do not change another task's controller ownership.

## Choose the Smallest Execution Shape

- Work directly for one bounded read, command, obvious edit, or tightly serial
  change.
- Use one implementer for coupled files or a short core change.
- Use two or three implementers only when exact write scopes are disjoint and
  parallel work saves material time.
- Use one combined reviewer after the complete stable diff exists.
- Do not create a mapper by default. If an unknown cross-repository boundary
  makes mapping necessary, write its conclusions into the existing brief.

Never parallelize competing algorithms or formal experiments. Never change the
controller or another conversation's model.

## Create One Canonical Brief

For non-trivial work, create only:

```text
.codex/collaboration/active/<task-id>/BRIEF.md
```

Read `references/brief-template.md` and include only the facts needed to execute
the current task. Do not create manifests, leases, handoff files, heartbeat
files, result files, or review files.

Use this priority:

```text
current user instruction
> BRIEF.md
> current repository contract
> inherited conversation context
```

Return `BLOCKED` on a real conflict or missing authority.

## Dispatch and Integrate

Read `references/collaboration-protocol.md` before delegating.

1. Give every file one writer and every reviewer read-only access.
2. Let implementers inherit three to five relevant turns and read the brief.
3. Let a reviewer inherit one to three relevant turns and read the same brief.
4. Let implementers exchange direct interface messages; the controller should
   not relay routine progress.
5. Accept only `BLOCKED`, `PACKAGE_READY`, `REVIEW_READY`, or `COMPLETE` as task
   states.
6. Route concrete review findings to the original file owner. Permit one repair
   and re-review pass, then let the controller adjudicate.

The controller alone edits root memory, integrates Git, authorizes experiments,
interprets scientific evidence, and reports to the user.

## Preserve the Research Boundary

Before algorithm, reward, or experiment design, read the sources named by
`AGENTS.md`. Preserve tensor shapes, probability support, likelihood replay,
gradient and detach semantics, clocks, masks, reward scale, advantage meaning,
checkpoint compatibility, and collector behavior.

Use the smallest direct behavioral check needed for the completion claim. For
an operational failure, locate and repair only the failed boundary. Do not turn
a valid scientific failure into a code defect or parameter rescue.

An implementation ending at `COMPLETE` does not authorize smoke training,
formal experiments, external handoff, staging, or promotion unless that
authority already exists.

## Close the Task

The controller reviews the final diff and direct evidence, updates only the
owning memory file at a real boundary, removes the task's temporary brief, and
stages only intended files. Report the outcome, direct evidence, remaining
risk, and next authorized action.
