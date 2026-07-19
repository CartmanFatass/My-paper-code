---
name: hmasd-implementer
description: Use when a Codex task is assigned to implement or fix HMASD algorithm, reward, credit, dynamic-roster, trainer, runtime, collector, replay, checkpoint, analyzer, or experiment-code changes. This is the implementer role contract, not a planning, review, experiment-monitoring, external-review, Git, or scientific-route-selection workflow.
---

# HMASD Implementer

Read, in this order:

1. `../hmasd-task-router/SKILL.md`;
2. the controller's current task message;
3. `docs/project/ALGORITHM_PRINCIPLES.md`;
4. `references/engineering-principles.md`;
5. only the code and evidence named by the task.

Do not load `CURRENT_WORK.md`, `IMPLEMENTATION_PLAN.md`, `ExpRecord.md`, old
reviews, archived experiments, or another role's Skill unless the controller's
task names one as evidence. The task message is the concrete implementation
contract; the scientific and engineering principles are durable constraints.
Return `BLOCKED` before editing only when those sources genuinely conflict or
the requested change requires files outside the assigned scope.

## Execute

- Locate the named symbols and their immediate callers before editing.
- Implement the frozen design inside the assigned write scope. Do not choose a
  new algorithm, reward, budget, threshold, gate, or experiment.
- Replace superseded active paths. Do not add backward-compatibility branches,
  legacy adapters, duplicate modules, or speculative abstractions.
- Preserve every task-stated probability, gradient, RNG, recurrent-state,
  replay, clock, mask, checkpoint, and output invariant.
- Reuse existing batch and tensor paths before adding a new path.
- Run the single focused check named by the task, or the smallest direct check
  that exposes the edited boundary when none is named.
- Report changed symbols, check evidence, and one concrete remaining risk. Do
  not update root project documents, launch experiments, commit, push, or
  expand the task.

If two delegated attempts fail under the same frozen task, return the exact
failure to the controller; do not start a third redesign attempt.
