---
name: hmasd-dispatch-task
description: Route HMASD work to the registered experiment monitor. Use for experiment-monitor delivery or its role callback. Local OMP code agents are dispatched directly; external review remains entirely inside the active Controller's BrowserMCP state machine.
---

# HMASD Task Dispatch

Read `docs/project/CURRENT_WORK.md` and `references/session-roles.json` before
sending persistent work. Use only ACTIVE registered roles; never infer a role
from a title, old callback, history, or manually copied task ID.

```text
controller -> local OMP task agents
controller -> BrowserMCP Pro submission/observation/capture
controller <-> experiment_monitor
```

The preserved end-to-end loop is external Pro scientific review -> Controller
intake and frozen plan -> local OMP implementation plus the collective
Reviewer/Verifier gate -> authorized run observed by `experiment_monitor` ->
Controller result intake -> external Pro result review. The Controller is the
only transition owner between stages.

The Controller owns scientific-to-code translation, executable planning, local
agent decomposition, integration, verification, routing, continuation, Git,
formal-compute authority, the complete BrowserMCP state machine, and direct
evidence intake. Under an active autonomous grant, an accepted result wakes the
Controller to route the next already-authorized action. Stop only on a
paused/exhausted grant, genuine blocker, or protected-scope expansion.

## Local OMP task agents

Local code and record work does not use persistent route resolution. The
Controller dispatches only these six project profiles:

```text
hmasd-code-scout   openai-codex/gpt-5.6-luna:high
hmasd-implementer  openai-codex/gpt-5.6-sol:high
hmasd-frontier-implementer  openai-codex/gpt-5.6-sol:max
hmasd-verifier     openai-codex/gpt-5.6-luna:high
hmasd-reviewer     openai-codex/gpt-5.6-sol:xhigh
hmasd-exp-manager  openai-codex/gpt-5.3-codex-spark:high
```

Before implementation, record the current branch, `HEAD`, and inherited
working-tree changes in the assignment. Local agents operate on that exact
visible source, preserve unrelated work, and never perform Git operations.

Every assignment contains outcome, scientific authority, exact inputs and
scope, protected semantics, exclusions, checks, and return semantics. One writer
owns a file scope. Children do not reconstruct Controller history, invoke
unrelated Skills, mutate Git, or spawn successors. An unknown project agent is a
workflow blocker; never fall back to a bundled/default agent.

The Controller/main conversation alone performs implementation design and
writes the frozen plan. It inspects context, states requirements and success
criteria, compares 2-3 approaches, selects the smallest sound option, and
records exact files, interfaces, invariants, red/green commands, and expected
outputs in `docs/project/IMPLEMENTATION_PLAN.md`. Local agents execute that plan
and may report a blocker; they never author, broaden, or redesign it.

Do not dispatch review after individual child tasks, files, Frontier attempts,
or intermediate failures. Once the complete planned package and bounded repairs
are integrated and Controller-focused checks are green, dispatch exactly one
`hmasd-reviewer` and one `hmasd-verifier` in parallel with assignment marker
`FINAL_IMPLEMENTATION_ROUND_REVIEW`. Re-review only when a resulting repair
materially changes protected semantics or the frozen plan contract.

Use `hmasd-frontier-implementer` only for one bounded reproduced bug after an
ordinary implementation or verification path exposes a concrete failure. It
follows systematic debugging: establish a fast red-capable loop, minimise, rank
falsifiable hypotheses, instrument one prediction at a time, and make at most
five repair attempts. One attempt is one hypothesis/probe/candidate-change/
focused-verdict cycle. Success requires the minimal loop and original reproducer
to become green. After five unsuccessful attempts it returns `BUG_UNRESOLVED`
with the attempt ledger, exact failure evidence, and ranked next actions. It
never substitutes a slow retry for diagnosis or changes scientific evidence
meaning.

Every Frontier checkpoint and final report starts with four decision fields:
problem source; problem type exactly `CODE_ENGINEERING` or
`SCIENTIFIC_DECISION`; approximate scale across files, interfaces, semantics,
and expensive execution; and one recommended solution marked for automatic
adoption. Apply a recommendation automatically only inside the frozen assignment
and active grant. Anything that changes scientific meaning stops at the
external-Pro authority boundary.

## Resolve before every persistent send

Run `scripts/resolve_task_route.ps1 -Role <role>` immediately before a persistent
send. Require nonempty `hostId`, `threadId`, `model`, and `thinking`, then copy
all four resolved values unchanged into exactly one send. Resolve again
afterward; if identity, model, or thinking changed, report route corruption and
do not resend. Static registry data never stores route metadata.

On this Windows workspace, the resolver may use the project Conda environment's
bundled `sqlite3.exe` when no `sqlite3` command is on `PATH`. That fallback reads
only live route metadata and never adds static route fields to the registry.

## Experiment Monitor

Use `experiment_monitor` only after a run is already authorized or launched.
The currently registered task is `ARCHIVED_REBUILD_REQUIRED`. Before any formal
run, rebuild exactly one Monitor, require `gpt-5.3-codex-spark` at `medium`, and
atomically update the registry and Controller-owned control plane. Never
substitute another model, role, or local task agent. Only then send
`MONITOR_ASSIGNMENT` with run ID, root, authoritative status/progress/result
paths, expected terminal condition, and ETA.

The monitor uses `hmasd-experiment-monitor`, owns ETA-based heartbeats, and
returns one terminal `EXPERIMENT_MONITOR` payload to the resolved Controller. It
never launches, restarts, repairs, extends, edits, or interprets the run.

## External review is not dispatch

External scientific review is not a persistent role and has no local observer
profile. The long-lived Controller starts the singular pinned `browsermcp-pro`
server, the user connects the registered Pro tab, and the Controller executes
`hmasd-browser-pro-exchange` inline from validation through immutable receipt,
20-second wait observation, two-snapshot capture, archival, and intake. Each
round requires a live preflight; the registry never claims a durable live
connection. A disconnected extension or indeterminate page state is a blocker,
never permission to dispatch a child or use a former Exchange session.

## Authority boundary

External GPT-5.6 Pro owns scientific direction and evidence meaning. The
Controller owns executable realization inside that direction and every
resource-consuming action. Local agents execute bounded work; BrowserMCP
submission, observation, capture, archival, and intake remain in the Controller
session; the persistent experiment Monitor only observes an authorized run. No
local or persistent role starts a successor. A topology change updates the
Controller control plane, this Skill, the role registry, local profiles,
external transport registry, and focused contract tests in one Git boundary.
