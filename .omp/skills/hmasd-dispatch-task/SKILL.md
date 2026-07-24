---
name: hmasd-dispatch-task
description: Route HMASD local research/code agents dynamically and resolve the registered experiment monitor when an authorized run exists.
---

# HMASD Task Dispatch

## Active topology

```text
Controller -> local OMP research/code agents
Controller -> BrowserMCP Pro directly when optional open review is justified
Controller -> registered experiment_monitor for one authorized run
experiment_monitor -> invoking Controller on the same assignment channel
```

The Controller owns research synthesis, next-action selection, executable
planning, integration, Git and resource authority. External Pro is an optional
open scientific reviewer, not a mandatory approval hop. Browser transport is
never delegated.

Active local profiles:

```text
hmasd-code-scout
hmasd-research-scout
hmasd-implementer
hmasd-frontier-implementer
hmasd-reviewer
hmasd-verifier
hmasd-exp-manager
```

Children do not spawn successors and never perform Git operations.

## Research waves

When a scientific question has several independent approaches, dispatch a
single wave spanning genuinely different mechanism families. Do not allocate a
fixed number of agents to one favored route and do not tell most early agents
which route is favored.

Each assignment names:

- the exact conjecture or implication under attack;
- one approach family;
- frozen evidence semantics and prohibited information;
- the concrete required output: lemma, equation, construction,
  counterexample, minimal implementation or measurement;
- the exact condition for `SUPPORTED`, `REFUTED`, `BLOCKED` or
  `NON_IDENTIFYING`.

Route open-exploration derivation, literature and counterexample work to
`hmasd-research-scout` only when the Controller assigns exactly one approach
family and one bounded question. Require a concrete conjecture, lemma, equation,
construction or counterexample, or an explicit `NON_IDENTIFYING` finding. The
scout remains read-only: it does not implement, compute, select or accept
science, schedule successors, mutate Git or spawn agents. Assignment diversity,
not route-specific profiles or fixed agent counts, supplies the wave's
independence.

After the wave, the Controller groups results by scientific idea, attacks the
strongest claims, redirects capacity toward underexplored families and launches
another wave only when a new mechanism or unresolved family warrants it.
Status-only reports are rejected.

Use `hmasd-code-scout` for bounded read-only interface mapping,
`hmasd-implementer` for one frozen implementation slice and
`hmasd-exp-manager` for factual experiment records. Review and repair follow
`docs/project/RESEARCH_WORKFLOW.md`.

## Experiment monitor

Use the one registered route only for an already-authorized run. The Controller
resolves `experiment_monitor` through
`.omp/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1` and
`references/session-roles.json`. An archived monitor must be rebuilt under the
current user authority before assignment; `ARCHIVED_REBUILD_REQUIRED` permits
neither rebuild nor assignment by this Skill.

The Controller initiates one complete `MONITOR_ASSIGNMENT` on that resolved
monitor route. Progress and terminal return stay on that assignment. The
Monitor emits exactly one terminal payload as the natural reply/result on the
same Controller-initiated `MONITOR_ASSIGNMENT` channel. This same-assignment
result return targets the invoking Controller through channel ownership; the
Monitor never resolves or stores a separate Controller route. There is one
monitor route and no fallback.

The Monitor may report progress and ETA before its one terminal result. It does
not launch, restart, repair, extend or scientifically interpret a run.

## Git and evidence

Git branch and commit identify source and evidence. Do not compute per-file
hashes or create handoff receipts, manifest validators or topology contract
tests. Exact paths and the resulting Controller commit are sufficient.
