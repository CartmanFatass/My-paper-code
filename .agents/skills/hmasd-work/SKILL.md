---
name: hmasd-work
description: Orchestrate an HMASD core implementation only when the user explicitly invokes $hmasd-work or the controller will delegate a coupled change spanning at least two implementation files to an implementer and one combined reviewer. Do not use for direct controller work, explanations, status, read-only diagnosis, one-file changes, Git/docs, prompts, result interpretation, or routine continuation.
---

# HMASD Work

Keep the current root task as active controller. Read `memory/CURRENT_WORK.md`
first and do not change another task's controller ownership.

## Activation Boundary

Direct controller work is the default. Activate only when either condition is
true:

1. the user explicitly names `$hmasd-work`; or
2. the controller will delegate a coupled core change that writes at least two
   implementation files to an implementer and will use one combined reviewer.

Otherwise do not create a brief, implementer or reviewer. A documentation-only
change never satisfies condition 2; explicit user invocation still satisfies
condition 1.

Never parallelize competing algorithms or formal experiments. Never change the
controller or another conversation's model.

## Freeze the Controller Design

The current user-selected controller model is fixed. Never change it or select a
replacement automatically. The active controller decides before delegation:

- the core algorithm and causal hypothesis;
- the network and training architecture;
- what existing implementation is reused, replaced, or deleted;
- the data and gradient flow;
- probability, clock, RNG, credit, replay, mask, and checkpoint invariants;
- expected behavior, stability, and evidence boundary;
- the implementer's exact write scope.

An implementer may locate concrete interfaces and exercise engineering
judgment inside that design, but does not fill in missing core design, select a
route, add a mechanism, redefine the experiment, or expand scope. A real
conflict returns `BLOCKED` to the controller.

## Create One Canonical Brief

For a qualifying collaboration task, create only:

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

Use one writer per file and one implementer by default. Multiple implementers
are allowed only when `BRIEF.md` gives them disjoint exclusive file lists and
frozen interfaces. After every writer has stopped, use one fresh read-only
reviewer and at most one repair/re-review pass.

Task states have these exact conditions:

- `BLOCKED`: a named contract conflict, missing authority, file collision or
  required scope expansion prevents the assigned work;
- `PACKAGE_READY`: the package changed only its exclusive files and its one
  registered check exited zero or the brief explicitly registered `Check: none`;
- `REVIEW_READY`: every package is `PACKAGE_READY`, no writer remains active,
  and the controller has listed the complete intended diff and check evidence;
- `COMPLETE`: the reviewer returned `APPROVED` or the controller disposed every
  finding, inspected the final diff/evidence, removed the temporary brief and
  performed only an already-authorized project boundary action.

The controller alone edits root memory, integrates Git, authorizes experiments,
interprets scientific evidence, and reports to the user.

## Preserve the Research Boundary

Apply the research and runtime invariants from `AGENTS.md`. Do not copy generic
rules into the brief; record only the task-specific invariants needed to prevent
semantic drift. The default is no new test. Register exactly one focused command
only when the brief names a concrete corruption or wrong-experiment risk that
the next authorized run cannot expose cheaply; otherwise write `Check: none`.
Repair only a concrete failed boundary and never reinterpret a valid
scientific failure as an engineering rescue. Performance remains ordinary code
quality, not a separate gate or reviewer.

An implementation ending at `COMPLETE` does not authorize smoke training,
formal experiments, external handoff, staging, or promotion unless that
authority already exists.

## Close the Task

The controller reviews the final diff and direct evidence, updates only the
owning memory file at a real boundary, removes the task's temporary brief, and
stages only intended files. Report the outcome, direct evidence, remaining
risk, and next authorized action.
