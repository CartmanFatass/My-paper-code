---
name: hmasd-work
description: Orchestrate an explicitly requested or genuinely collaboration-dependent HMASD multi-file core algorithm, trainer, or runtime change through one controller design, one canonical brief, bounded implementers, and one combined reviewer. Do not use for explanations, status or progress, read-only inspection, bounded diagnosis, single-file edits, simple bugs, ordinary Git or documentation, prompt generation, experiment-need decisions, routine continuation, or work the controller can complete efficiently without collaboration.
---

# HMASD Work

Keep the current root task as active controller. Read `memory/CURRENT_WORK.md`
first and do not change another task's controller ownership.

## Activation Boundary

Direct controller work is the default. Do not activate for explanation, status,
bounded inspection or diagnosis, one-file work, simple bugs, ordinary Git/docs,
prompt generation, experiment-need decisions, or routine continuation. Activate
only when the user names `$hmasd-work` or a multi-file core change genuinely
benefits from a brief plus implementer/reviewer separation.

Never parallelize competing algorithms or formal experiments. Never change the
controller or another conversation's model.

## Freeze the Controller Design

The active controller uses the strongest available model and decides before
delegation:

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

Use one writer per file, one implementer for a coherent change, and bounded
implementers only for independent disjoint packages. After the stable combined
diff, use one fresh read-only reviewer and at most one repair/re-review pass.
Task states are only `BLOCKED`, `PACKAGE_READY`, `REVIEW_READY`, and `COMPLETE`.

The controller alone edits root memory, integrates Git, authorizes experiments,
interprets scientific evidence, and reports to the user.

## Preserve the Research Boundary

Apply the research and runtime invariants from `AGENTS.md`. Do not copy generic
rules into the brief; record only the task-specific invariants needed to prevent
semantic drift. Ordinary implementation gets one necessary direct behavioral
check. Repair only a concrete failed boundary and never reinterpret a valid
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
