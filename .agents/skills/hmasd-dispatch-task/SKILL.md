---
name: hmasd-dispatch-task
description: Route nontrivial HMASD work to the registered native Codex Project Manager, experiment monitor, or Open-Pro Exchange. Use whenever a task needs persistent-session delivery, external review, algorithm realization, monitoring, or a role callback; do not use for ordinary controller edits or explanation.
---

# HMASD Task Dispatch

Read `docs/project/CURRENT_WORK.md` and
`references/session-roles.json` before sending work. Use only ACTIVE registered
roles; never infer a role from a title, old callback, history, or a manually
copied task ID.

```text
controller <-> project_manager
controller <-> experiment_monitor
controller <-> open_divergent_exchange
```

The Controller owns routing, continuation, Git, formal-compute authority, and
direct evidence intake. Under an active autonomous grant, an accepted callback
wakes the Controller to route the next already-authorized action. Stop only on
a paused/exhausted grant, genuine blocker, or protected-scope expansion.

## Resolve before every send

Run `scripts/resolve_task_route.ps1 -Role <role>` immediately before a send.
Require nonempty `hostId`, `threadId`, `model`, and `thinking`, then copy all
four resolved values unchanged into exactly one send. Resolve again afterward;
if identity, model, or thinking changed, report route corruption and do not
resend. Static registry data never stores route metadata.

On this Windows workspace, the resolver may use the project Conda
environment's bundled `sqlite3.exe` when no `sqlite3` command is on `PATH`.
That fallback reads only live route metadata and never adds static route fields
to the registry.

## Project Manager

Use `project_manager` for an authorized implementation realization, WIP audit,
focused verification, or package acceptance. Before each assignment, run
`scripts/resolve_source_boundary.ps1`; send only:

```text
source_boundary=local_and_remote_aggressive_tip
```

Never hand-copy a source SHA. The Manager resolves and records its own source
commit; a local/remote mismatch is `SOURCE_BOUNDARY_DIVERGED`, not an invitation
to guess a nearby SHA.

The assignment includes objective, external-Pro scientific direction, evidence
inputs, exact scope, protected semantics, exclusions, checks, and return
contract. The Manager owns decomposition and native child-agent use. It does
not change science, Git, project control, external review, or formal-compute
authority.

Before `IMPLEMENTATION_READY` or `RESEARCH_MANAGER_BLOCKED`, the Manager resolves
`controller` and calls `codex_app__send_message_to_thread` once with one complete
terminal payload to that exact route. A
failed delivery is `PROJECT_MANAGER_DELIVERY_BLOCKED`; it never authorizes a
guessed retry or successor.

## Experiment Monitor

Use `experiment_monitor` only after a run is already authorized or launched.
Before its first assignment, confirm the live route is `gpt-5.3-codex-spark` at
`medium`; do not silently fallback. Send `MONITOR_ASSIGNMENT` with run ID, root,
authoritative status/progress/result paths, expected terminal condition, and ETA.

The monitor uses `hmasd-experiment-monitor`, owns ETA-based heartbeats, and
returns one terminal `EXPERIMENT_MONITOR` payload to the resolved Controller. It
never launches, restarts, repairs, extends, edits, or interprets the run.

## Open-Pro Exchange

Use `open_divergent_exchange` only for registered external-Pro transport. The
role owns one neutral handoff, natural-response capture, exact raw archival, and
its heartbeat. It never chooses science, code, compute, Git, or a successor.

Accept a callback only after matching its registered source role, round,
handoff ID, and raw path. `REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED`
wakes the Controller for direct evidence intake and next-action routing.

## Authority boundary

Assignments contain outcome, authority, inputs, scope, exclusions, completion,
and return semantics—not controller history. No role starts a successor. A
topology change updates `CURRENT_WORK.md`, this Skill, the role registry, and
their contract tests in one Git boundary.
