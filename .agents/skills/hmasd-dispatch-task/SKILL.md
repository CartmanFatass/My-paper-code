---
name: hmasd-dispatch-task
description: Route HMASD work to the registered experiment monitor. Use for monitor delivery or its role callback; local agents include a one-shot read-only Pro completion monitor while BrowserMCP submission and intake remain in the unified Controller session.
---

# HMASD Task Dispatch

Read `docs/project/CURRENT_WORK.md` and
`references/session-roles.json` before sending persistent work. Use only ACTIVE
registered roles; never infer a role from a title, old callback, history, or a
manually copied task ID.

```text
controller -> local OMP task agents
controller -> BrowserMCP Pro submission/capture
controller -> hmasd-pro-monitor -> BrowserMCP wait/snapshot
controller <-> experiment_monitor
```

The Controller owns scientific-to-code translation, executable planning, local
agent decomposition, integration, verification, routing, continuation, Git,
formal-compute authority and direct evidence intake. Under an active autonomous
grant, an accepted result wakes the Controller to route the next
already-authorized action. Stop only on a paused/exhausted grant, genuine
blocker, or protected-scope expansion.

## Local OMP task agents

Local code and record work does not use persistent route resolution. The
Controller dispatches only these project profiles:

```text
hmasd-code-scout   openai-codex/gpt-5.6-luna:high
hmasd-implementer  openai-codex/gpt-5.6-sol:high
hmasd-verifier     openai-codex/gpt-5.6-luna:high
hmasd-reviewer     openai-codex/gpt-5.6-sol:xhigh
hmasd-exp-manager  openai-codex/gpt-5.3-codex-spark:high
hmasd-pro-monitor   openai-codex/gpt-5.3-codex-spark:medium
```

Before implementation, record the current branch, `HEAD` and inherited
working-tree changes in the assignment. Local agents operate on that exact
visible source, preserve unrelated work and never perform Git operations.

Every assignment contains outcome, scientific authority, exact inputs and
scope, protected semantics, exclusions, checks and return semantics. One writer
owns a file scope. Children do not reconstruct Controller history, invoke
unrelated Skills, mutate Git or spawn successors. An unknown project agent is a
workflow blocker; never fall back to a bundled/default agent.

## Resolve before every persistent send

Run `scripts/resolve_task_route.ps1 -Role <role>` immediately before a send.
Require nonempty `hostId`, `threadId`, `model`, and `thinking`, then copy all
four resolved values unchanged into exactly one send. Resolve again afterward;
if identity, model, or thinking changed, report route corruption and do not
resend. Static registry data never stores route metadata.

On this Windows workspace, the resolver may use the project Conda environment's
bundled `sqlite3.exe` when no `sqlite3` command is on `PATH`. That fallback
reads only live route metadata and never adds static route fields to the
registry.

## Experiment Monitor

Use `experiment_monitor` only after a run is already authorized or launched.
The currently registered task is `ARCHIVED_REBUILD_REQUIRED`. Before any formal
run, rebuild exactly one Monitor, require `gpt-5.3-codex-spark` at `medium`, and
atomically update the registry and control plane. Never substitute another
model, role or local task agent. Only then send `MONITOR_ASSIGNMENT` with run ID,
root, authoritative status/progress/result paths, expected terminal condition
and ETA.

The monitor uses `hmasd-experiment-monitor`, owns ETA-based heartbeats, and
returns one terminal `EXPERIMENT_MONITOR` payload to the resolved Controller.
It never launches, restarts, repairs, extends, edits, or interprets the run.

External scientific review is not a persistent dispatch role. The long-lived
Controller starts the pinned `browsermcp-pro` server, then the user connects the
registered Pro tab. The Controller uses `hmasd-browser-pro-exchange` on the
current pushed branch and owns submission, capture, archival and intake. After
submission it may dispatch one `hmasd-pro-monitor`; that local Spark task
receives only BrowserMCP wait/snapshot tools and returns one stability callback.
A disconnected extension or ephemeral OMP process is a blocker, never
permission to route through a former Exchange session.

## Authority boundary

External GPT-5.6 Pro owns scientific direction and evidence meaning. The
Controller owns executable realization inside that direction and every
resource-consuming action. Local agents execute bounded work; BrowserMCP
submission and capture stay in the Controller session; `hmasd-pro-monitor`
observes completion read-only; the persistent Monitor only observes an
authorized experiment. No local or persistent role starts a successor. A
topology change updates `CURRENT_WORK.md`, this Skill, the role registry, local
profiles, external transport configuration and their contract tests in one Git
boundary.
