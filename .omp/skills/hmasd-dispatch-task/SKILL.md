---
name: hmasd-dispatch-task
description: Route HMASD work to the registered experiment monitor. Local OMP agents are dispatched directly; Luna-high hmasd-exchange-review owns one bounded mechanical BrowserMCP exchange.
---

# HMASD Task Dispatch

Read `docs/project/CURRENT_WORK.md` and `references/session-roles.json` before
sending persistent work. Use only ACTIVE registered roles; never infer a role
from a title, old callback, history, or manually copied task ID.

```text
controller -> local OMP task agents
controller -> hmasd-exchange-review -> BrowserMCP Pro exchange
controller <-> experiment_monitor
```

The preserved end-to-end loop is external Pro scientific review -> Controller
intake and frozen plan -> local OMP implementation plus the collective
Reviewer/Verifier gate -> authorized run observed by `experiment_monitor` ->
Controller result intake -> external Pro result review. The Controller is the
only transition owner between stages.

The Controller owns scientific-to-code translation, executable planning, local
agent decomposition, integration, verification, routing, continuation, Git,
formal-compute authority, and direct evidence intake. The Luna-high
`hmasd-exchange-review` agent owns only frozen BrowserMCP mechanics. External
scientific authority remains with GPT-5.6 Pro. Failed transport must not be
substituted locally, and no automation Skill is active.

## Local OMP task agents

Local code, record and external-exchange work does not use persistent route
resolution. The Controller dispatches only these eight project profiles:

```text
hmasd-code-scout       openai-codex/gpt-5.6-luna:high
hmasd-review-scout     openai-codex/gpt-5.6-luna:high
hmasd-exchange-review  openai-codex/gpt-5.6-luna:high
hmasd-implementer      openai-codex/gpt-5.6-sol:high
hmasd-frontier-implementer  openai-codex/gpt-5.6-sol:max
hmasd-verifier         openai-codex/gpt-5.6-luna:high
hmasd-reviewer         openai-codex/gpt-5.6-sol:xhigh
hmasd-exp-manager      openai-codex/gpt-5.3-codex-spark:high
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

## External review transport

The BrowserMCP automation Skill `hmasd-browser-pro-exchange` remains disabled.
The user-approved Luna-high `hmasd-exchange-review` project agent executes one
Controller-frozen mechanical exchange assignment without routine human steps.
It verifies identity and the pushed boundary, submits only the deterministic
one-line dispatch, publishes the no-clobber receipt, observes in bounded waits,
captures two stable snapshots, clicks the latest page-provided `Copy response`
button and atomically archives the exact copied marked response. It never uses
`browser_type`, keyboard-copy shortcuts, another conversation, a local reviewer,
or an alternate scientific authority.

`hmasd-review-scout` retains factual transport experience but does not operate
the browser. The Controller alone writes questions, reconciles facts, performs
scientific intake, updates CDC records and starts successors. A receipt forbids
resubmission; a raw response forbids all browser work.

## Authority boundary

External GPT-5.6 Pro owns scientific direction and evidence meaning. The
Controller owns executable realization inside that direction and every
resource-consuming action. Local agents execute bounded work; only
`hmasd-exchange-review` may perform BrowserMCP submission, observation,
page-copy capture and archival. It returns evidence to the Controller, which
alone performs intake and successor routing. The persistent experiment Monitor
only observes an authorized run. A topology change updates the Controller
control plane, this Skill, the role registry, local profiles, external transport
registry and focused contract tests in one Git boundary.
