---
name: hmasd-work
description: Orchestrate an explicitly requested or genuinely collaboration-dependent HMASD multi-file core algorithm, trainer, or runtime change through one controller design, one canonical brief, bounded implementers, and one combined reviewer. Do not use for explanations, status or progress, read-only inspection, bounded diagnosis, single-file edits, simple bugs, ordinary Git or documentation, prompt generation, experiment-need decisions, routine continuation, or work the controller can complete efficiently without collaboration.
---

# HMASD Work

Keep the current root task as active controller. Read `memory/CURRENT_WORK.md`
first and do not change another task's controller ownership.

## Activation Boundary

Direct controller work without a Skill announcement, brief, subagent, reviewer,
or plan artifact is the default. Do not activate this Skill for questions,
explanations, status or progress reports, one read-only inspection, reading one
file or result, bounded diagnosis, an explicit single-file edit, a simple bug,
ordinary Git, one documentation update, prompt generation, an experiment-need
decision, or routine continuation.

Activate it only when the user explicitly names `$hmasd-work`, or when a
non-trivial multi-file core algorithm, trainer, or runtime change genuinely
needs a canonical brief and implementer/reviewer separation. Even a complex
task remains direct when the controller can complete it efficiently without
collaboration.

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

1. Give every file one writer and every reviewer read-only access.
2. Use one implementer for one coherent core implementation. Use bounded
   implementers only for genuinely independent work packages with disjoint
   scopes and a controller-frozen interface.
3. Let implementers inherit three to five relevant turns and read the brief.
4. Use one fresh combined reviewer after the complete diff is stable. The
   reviewer inherits one to three relevant turns, reads the same brief, and
   checks fidelity without redesigning the route.
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

Ordinary implementation receives one necessary direct behavioral check. For an
operational failure, locate and repair only the failed boundary. Do not turn a
valid scientific failure into a code defect or parameter rescue. Performance is
ordinary code quality: a reviewer reports obvious scalar CUDA, repeated packing,
unnecessary synchronization, or module duplication directly to the controller.
Do not create an independent performance gate, threshold, smoke, or reviewer.

An implementation ending at `COMPLETE` does not authorize smoke training,
formal experiments, external handoff, staging, or promotion unless that
authority already exists.

## Close the Task

The controller reviews the final diff and direct evidence, updates only the
owning memory file at a real boundary, removes the task's temporary brief, and
stages only intended files. Report the outcome, direct evidence, remaining
risk, and next authorized action.
