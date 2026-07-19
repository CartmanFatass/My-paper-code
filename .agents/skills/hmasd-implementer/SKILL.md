---
name: hmasd-implementer
description: Use only in a temporary HMASD implementation or implementation-fix subagent whose assignment names this Skill. It grants bounded code-edit authority and isolates algorithm, trainer, runtime, replay, checkpoint, analyzer, and experiment-code work from controller, persistent sessions, review, monitoring, Git, and route-selection context.
---

# HMASD Implementer

## Entry Contract

Require one bounded subagent assignment naming:

```text
task_id=<stable id>
role=implementer
role_skill=.agents/skills/hmasd-implementer/SKILL.md
objective=<one bounded outcome>
authority=<allowed mutation class>
inputs=<explicit paths>
working_scope=<one or more project directories>
protected_changes=<exact protected files/symbols or none>
forbidden=<explicit exclusions>
completion=<one focused check and observable handoff>
```

Read, in order:

1. this Skill;
2. the assignment;
3. `docs/project/ALGORITHM_PRINCIPLES.md`;
4. `references/engineering-principles.md`;
5. only assignment-listed inputs and immediate callers needed to edit the named
   symbols.

The assignment supplies a bounded working directory and enumerates every
protected algorithm or normative file/symbol it permits changing. Ordinary
helpers, runners, analyzers, tests, transient files, and non-normative documents
inside that working scope need not be listed individually.

Do not load `CURRENT_WORK.md`, `IMPLEMENTATION_PLAN.md`, `ExpRecord.md`,
external reviews, archives, logs, another role Skill, or the controller
conversation unless the assignment explicitly lists one path as input. The
assignment, not nearby repository text, is the executable design.

Return `TASK_BLOCKED` before editing when the assignment is incomplete,
contradicts a required principle, needs work outside the assigned working
scope, or would change an ungranted protected semantic or normative file.

## Granted Authority

Within the assigned working scope:

- locate the named symbols and immediate interfaces;
- implement the frozen design;
- create, replace, or delete ordinary helper code, runners, analyzers, tests,
  transient files, and non-normative documents without seeking per-file
  approval;
- replace superseded active code rather than add compatibility branches;
- preserve all stated probability, gradient, RNG, recurrent-state, replay,
  mask, clock, checkpoint, and output invariants;
- run the single focused check named by the assignment.

Do not choose an algorithm, reward, budget, threshold, evidence gate, model,
experiment, or successor. Do not change an ungranted protected algorithm
semantic, project control, external-review state, automations, task routing, or
files outside the working scope. Do not commit, push, launch training, create
another task, invoke `$hmasd-task-router`, contact a persistent session, or
invoke another role Skill.

## Terminal Return

Return exactly one terminal result:

```text
TASK_COMPLETE
task_id=<id>
changed=<files and symbols>
check=<command and result>
risk=<one concrete remaining engineering risk or none>
```

or:

```text
TASK_BLOCKED
task_id=<id>
reason=<exact missing contract, conflict, or scope expansion>
```

Return this terminal message through the native subagent result channel. Do not
send it to a Codex session or wait for a task-router delivery receipt.
