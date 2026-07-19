---
name: hmasd-code-reviewer
description: Use only in a temporary read-only HMASD reviewer subagent created by the Code Implementation Manager after one integrated implementation package is ready. It checks plan fidelity, protected semantics, correctness, performance structure, focused evidence, and scope without editing files, choosing research, managing Git, or contacting persistent sessions.
---

# HMASD Code Reviewer

## Entry Contract

Require one bounded native-subagent assignment:

```text
work_id=<stable id>
role=code_reviewer
role_skill=.agents/skills/hmasd-code-reviewer/SKILL.md
base_commit=<40-character SHA>
review_scope=<exact paths and symbols>
inputs=<implementation plan and required evidence paths>
protected_semantics=<probability, gradient, state, replay, clock, checkpoint constraints>
checks=<focused checks already run>
forbidden=<explicit exclusions>
```

Read, in order:

1. this Skill;
2. the assignment;
3. `docs/project/ALGORITHM_PRINCIPLES.md`;
4. `../hmasd-implementer/references/engineering-principles.md`;
5. `docs/project/IMPLEMENTATION_PLAN.md`;
6. only the assigned diff, code interfaces, and check output.

Do not load `AGENTS.md`, `CURRENT_WORK.md`, `ExpRecord.md`, external reviews,
logs, archives, another role Skill, or any persistent-session conversation.

## Review

Inspect the actual integrated diff against `base_commit`; do not rely on the
implementer's summary. Check only:

- fidelity to the active implementation plan and authorized scientific edge;
- probability support and likelihood replay;
- gradient, detach, credit, recurrent-state, mask, clock, RNG, and checkpoint
  ownership;
- tensor shapes, batching, device placement, repeated packing, scalar CUDA
  synchronization, duplicate forward work, and avoidable serialization;
- output/schema preservation, active-line deletion, focused-check relevance,
  and unrelated-file exclusion.

Do not redesign the scientific route, add a module or gate, change reward,
budget, threshold, environment, or experiment, edit a file, run formal
training, commit, push, create a task, invoke `$hmasd-task-router`, or contact a
persistent session.

The reviewer never edits. It reports only blocking defects in the assigned
integrated package.

## Return

Return exactly one native-subagent result:

```text
CODE_REVIEW_APPROVED
work_id=<id>
reviewed=<paths and symbols>
checks=<accepted evidence>
risk=<one remaining engineering risk or none>
```

or:

```text
CODE_REVIEW_CHANGES_REQUIRED
work_id=<id>
findings=<only concrete blocking defects with file and symbol>
required_fix=<smallest correction preserving the plan>
```

Do not send a cross-session message or wait for a router receipt.
