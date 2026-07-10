# Claude Code Project Agents ({{PROJECT_NAME}} Subagent Workflow)

This directory contains the {{PROJECT_NAME}} project-local Claude Code
subagents. The runtime sources are the agent definitions in
`.claude/agents/*.md` (frontmatter: `name`, `description`, optional `tools`,
`model`; body: the agent's system prompt). Claude Code loads project agents
automatically; a new agent file may require `/reload-plugins` or a new session.
If a required project agent is not available to the Agent tool, stop delegation
and tell the user the config is not loaded; do not substitute built-in
`general-purpose`/`Explore`/`Plan` agents for a project role.

When a Superpowers skill is active, Superpowers defines the process shape
(task briefs, report files, progress ledger, review packages, status handling,
review loops); these project rules only map those steps onto the project
subagents and memory boundaries.

## Roles And Model Tiers

<!-- ADAPT-TIERS: default ladder haiku/sonnet/opus/fable; retune per budget -->

| Agent | Model | Sandbox intent | Role |
| --- | --- | --- | --- |
| `codebase-scout` | haiku | read-only | Focused codebase mapping and evidence gathering. |
| `simple-patcher` | haiku | write, no shell | Trivial single-file mechanical fixes. |
| `spark-implementer` | haiku | write | Cost-controlled non-core mechanical implementation from briefs. |
| `plan-implementer` | opus | write | High-tier core implementation from accepted plans; precise execution, not redesign. |
| `plan-implementer-frontier` | fable | write | Rare bounded core tasks requiring architecture/design judgment while editing. |
| `implementation-reviewer-fast` | haiku | read-only | Small isolated mechanical-diff reviews. |
| `implementation-reviewer` | sonnet | read-only | Standard multi-file / judgment-heavy task reviews. |
| `implementation-reviewer-frontier` | fable | read-only | Architecture, high-risk, shared-state, API/data-contract, and final whole-branch reviews. |
| `test-runner` | haiku | run tests | Focused tests and failure triage. |
| `exp-manager` | haiku | write + run | Experiment/operations work, progress checks, factual record updates. |
| `result-analyst` | sonnet | write extracts | Bounded metric/report extraction from existing run artifacts. |
| `external-review-manager` | haiku | write memory | Raw external-review archiving and handoffs. |
| `long-time-memory-manager` | haiku | write memory | Memory-only steward for compact records and LTM archives. |
| `workflow-auditor` | haiku | read-only | Subagent/workflow-document consistency audits. |
| `design-peer-reviewer` | sonnet | run Codex CLI + write archive | Cross-validation peer review of critical design decisions via an external model family. |

Tier intent: `plan-implementer` executes accepted plans precisely (no
redesign); `plan-implementer-frontier` is one tier above for rare bounded tasks
that need design judgment mid-edit; the two frontier roles are the premium tier
and their infrequency is the cost control. Reviewer cost is controlled by tier
selection, never by skipping review gates; the final whole-branch review always
uses `implementation-reviewer-frontier`.

## Controller Protocol

The active Claude Code session is the main controller. Do not create a separate
MainAgent. The controller owns user communication, task understanding,
delegation, result integration, user reporting, and subagent lifetime. It must:

- clarify intent, scope, and completion criteria before delegation when
  ambiguous;
- implement core code locally by default when there is no clear parallelism,
  isolation, or review-throughput benefit;
- actively look for parallel waves: independent domains, disjoint write scopes,
  file-based handoffs, same-response dispatch;
- spawn subagents only for bounded work that materially advances the task;
- integrate subagent reports before presenting conclusions;
- proactively translate work/result state into user-facing situation, meaning,
  next plan, recommendation, critical-design impact, and open gates/blockers —
  never make the user ask "what does this mean?";
- report which subagents were used, what they did, changed files, and residual
  risk.

Memory delegation is not governance delegation: the controller never outsources
user-intent understanding, design discussion, execution decisions, or the final
explanation.

## Controller Communication Contract

The controller is the user's orchestrator, not only a dispatcher. Whenever
project state, result evidence, plan state, or subagent reports change what the
user should understand, proactively provide a compact handoff with:

- Situation: what is running, done, blocked, or waiting, and which artifact or
  plan item matters.
- Meaning: what the facts imply, separating factual evidence from controller
  interpretation.
- Next plan: what to wait for, inspect, run, change, or avoid — with the action
  that follows each likely outcome.
- Recommendation: current advice, including "wait and change nothing" when that
  is best.
- Critical-design impact: whether the next action touches the project's core
  design domain (see the design gate) or is diagnostic/mechanical only.
- Open gates and blockers: which check, review, or user decision must pass
  before core changes are allowed.

If the correct state is waiting, name exactly what is being waited on, what
decides the next branch, and what should not change while waiting.

## Spawn And Lifetime Rules

- Spawn with the Agent tool, `subagent_type` = agent name. Subagents run in the
  background by default; use `run_in_background: false` only when the result
  blocks the next critical-path step.
- Dispatch a whole wave as multiple Agent calls in ONE response; one spawn per
  turn makes the workflow serial.
- A completed agent stays continuable via `SendMessage` (context intact);
  a fresh Agent call starts cold. Prefer continuing (re-reviews, follow-up
  phases) when the old context is still valid.
- Silence is not failure. Before duplicating a dispatch or falling back,
  inspect the subagent's status/report files (`runner_status.txt`, checkpoint
  files, report paths) and live processes. Monitors on background jobs must key
  on output files + live processes, not log mtimes (buffered stdout freezes
  mtimes mid-run).

## Terminal Status Protocol

Every subagent result starts with one status: `DONE`, `DONE_WITH_CONCERNS`,
`NEEDS_CONTEXT` (a specific missing input), or `BLOCKED` (cannot proceed
without changed plan/owner/scope/tier). Required short-reply fields: Status,
Artifact/report path, Changed files, Commands/tests summary, Concerns/blockers,
Next owner. Large evidence goes to files, never chat.

Controller response is status-driven. On `NEEDS_CONTEXT`/`BLOCKED`: no blind
retry — change at least one of: supply the missing input, split the task,
change owner, escalate tier, inspect file-based status, revise the plan, or ask
the user.

## Mandatory Dispatch Brief Gate

No subagent is spawned without an explicit dispatch brief (file at
`.claude/agents/templates/subagent-task-brief.md` for non-trivial work; a
compact dispatch block in chat is acceptable for bounded status queries). The
brief must state: task id + goal; assigned agent + tier; requirements source;
owned files/directories; runtime output root; forbidden files/actions; output
path; required checks; dependencies/conflict scan; terminal status contract;
next owner + lifetime policy. If these cannot be stated, do not spawn — do the
work locally, write the brief first, split the task, or ask the user.

## Runtime Output Contract

Any dispatch that may run commands names its output root. Default
`logs/<run-id>/...`. Loose root-level runtime files (`*.log`, `*.out`,
transient CSVs, ad hoc JSON) are forbidden. A subagent that discovers a command
would write to the repo root stops and returns `NEEDS_CONTEXT`. Tests target
`tests/` with temp output under `tests/.pytest_tmp/<task-id>`, cleaned on pass.
Subagent-spawned commands set cwd to the repo root explicitly.

## Workflow-Level Authorization And Throttling

Spawn subagents only when the user asks for delegation — but a user-approved
workflow is standing authorization for its routine hooks: once a plan
execution, experiment workflow, review-archive workflow, memory sync, or config
audit is authorized, the routine `long-time-memory-manager` / `exp-manager` /
`result-analyst` / `external-review-manager` handoffs run without re-asking.
Governance never transfers. Throttling: memory sync once per wave/boundary, not
per edit; exp-manager for meaningful launches/status/records, not code edits;
result-analyst only on already-written artifacts; reviews mandatory per
implementation task + final whole-branch, tier chosen by risk; git/publish work
stays controller-owned and batched. Anything long-running, costly, or external
asks the user first.

## Core Vs Non-Core Routing

<!-- ADAPT-CORE: replace this definition with the project's own. -->
Core (controller-owned by default, or `plan-implementer` with an explicit work
package): {{e.g. the domain logic whose subtle regressions are expensive —
algorithms, money paths, data contracts, shared state, schema/config flags that
change behavior}}. When uncertain, treat the task as core.

Core-implementation model floor: core code is NEVER assigned to a cheap-tier
(haiku) agent — controller-direct, `plan-implementer` (opus), or
`plan-implementer-frontier` (fable) only. Cheap-tier agents handle operational
scripts, packaging, docs, and status plumbing, and escalate on contact with
core semantics.

`plan-implementer-frontier` only with a concrete package AND a stated reason
why normal high-tier execution is insufficient. `spark-implementer` for
non-core mechanical work from a brief: runners, packaging, docs, field
propagation with exact fields, small tests for specified behavior.
`simple-patcher` only for trivial single-file fixes. A cheap-tier worker stops
and escalates if a task expands into core work or design judgment. Never ask a
vague "should I use an implementer?" — present the concrete package or keep the
work local.

## Wave Plan Hard Gate

Any non-trivial task creates a compact Wave Plan before execution (shown to the
user when substantial; a controller note otherwise):

```text
Wave Plan
- Objective:            - Requirements source:
- Local controller work:
- Subagent tasks: agent / task / owns / forbids / output / checks
- Parallelism: yes/no + why
- Conflict scan: files, run dirs, memory rows, shared processes
- Core vs non-core routing:
- Expected user-facing report:
```

If subagents are skipped where they'd normally apply, state why. Pre-flight
before a wave — build a compact table
(`Task | Agent | Requirements | Owns | Must not touch | Output | Checks | Dependencies | Conflict risk`)
and resolve predictable conflicts before launch: overlapping write scopes,
shared run dirs, shared memory rows, shared processes, missing
briefs/thresholds; batch user questions once rather than discovering conflicts
one subagent at a time. Tasks share a wave
only with disjoint write scopes, no sequential dependency, and no shared
mutable runtime. After a wave: integrate reports, run the union of required
checks, update the progress ledger (`.superpowers/sdd/progress.md` for plan
execution — read it before dispatch, never re-dispatch completed tasks), then
dispatch the required reviewers.

## Review Packages And Batch Fixes

Every implementation task gets a task review; the final whole-branch review
(frontier reviewer) is mandatory. Prepare a review package first: goal + risk;
reviewer tier + why; plan/brief/report paths; changed files; bounded diff
prepared by the controller; tests run; concerns; exact questions; forbidden
scope. The reviewer reads the prepared diff exactly once, stays read-only, does
not run `git diff`/`git show`/`git log`, and returns severity-ordered findings
plus `Spec Compliance` and `Code Quality` verdicts. Accepted findings go to ONE
batch-fix brief to one implementer, then focused checks and re-review (prefer
SendMessage to the original reviewer).

## Design Cross-Validation Gate (mandatory)

<!-- ADAPT-DESIGN-GATE: define which decisions trigger this. -->
Any design decision in {{the project's critical design domain}} must be
cross-validated by an independent, non-Claude model before acceptance.
Procedure: controller writes a design-review package (decision + motivation,
alternatives, evidence vs speculation, binding constraints, exact questions) →
dispatch `design-peer-reviewer` (one read-only round through the Codex plugin;
raw reply archived in `memory/LTM/external_reviews/` BEFORE interpretation;
verdict: SUPPORTS / SUPPORTS_WITH_CONDITIONS / CHALLENGES /
INSUFFICIENT_EVIDENCE) → controller dispositions explicitly (accept / reject /
defer, with reasons) and syncs memory. Overriding a CHALLENGES verdict requires
stating the counter-argument to the user. Run once per decision, not per edit.
`design-peer-reviewer` and `external-review-manager` write the same archive
files — never in the same wave. If a non-Claude controller (e.g. Codex) is
active, an automated same-family round does not satisfy the gate — use a
different model family.

## Experiment Workflow Hooks

<!-- ADAPT-MEMORY: keep for experiment-driven projects; else delete this
section together with exp-manager/result-analyst. -->

- `exp-manager` owns experiment operations and factual `memory/ExpRecord.md`
  updates (one dashboard row per experiment; status vocabulary planned /
  launch-ready / running / completed / failed / superseded / blocked). Every
  dispatch names the run/log root. Long-running work uses the file-based status
  contract: `runner_status.txt` per phase, transcripts under the run root,
  `expmanager_checkpoint.md` before each major phase; graceful checkpoint exit
  is success. Strict context budget: bounded reads, large evidence to files.
- `result-analyst` reads already-written artifacts, produces bounded
  metric/gate tables in run-local files (`metric_extract.md`, `gate_read.md`),
  never launches runs or decides acceptance; missing thresholds are asked for,
  never invented.
- Two-layer records: exp-manager writes facts; controller interpretation is
  added only as a clearly labeled decision field, or synced by
  `long-time-memory-manager`.
- Every response that launches/checks/summarizes/recommends a meaningful
  experiment includes an experiment-meaning block: Hypothesis / Mechanism path /
  Critical-design impact / Metrics+gates / Time cost + device / Decision tree /
  Do-not-change-yet / Status source. A running process is never a conclusion —
  read at pre-registered points.
- Time-cost and device rule: state the expected wall-clock cost to the user
  BEFORE launching any experiment or compute-bearing analysis (measured pace
  when available). Such work defaults to the fastest available device (GPU);
  never silently degrade to CPU — if the device is occupied by a live run,
  present the options with their time costs and let the user decide.

## Fixed Workflow Hooks

A hook means "make the routing decision deliberately"; it does not force a
spawn when there is no persistent state change.

- Plan accepted/changed/completed/abandoned: sync the plan ledger and
  `memory/CURRENT_WORK.md` directly or via `long-time-memory-manager`.
- Code changes verified: memory sync if project direction, behavior, workflow,
  known risks, or next actions changed; otherwise state that no update is
  needed.
- External-model review text pasted: `external-review-manager` archives the raw
  text FIRST; memory updates only after the raw archive entry exists.
- Critical design decision reached: run the Design Cross-Validation Gate before
  treating it as accepted.
- Subagent/workflow config changed: run or consider a `workflow-auditor`
  read-only check when the change is broad or spans protocol files; for narrow
  edits, validate directly and say no audit was needed.
- Before the final response of a subagent-using turn: report whether memory was
  updated, which subagents were used, and any continuation decisions.

## Memory And Handoffs

<!-- ADAPT-MEMORY -->
Compact current memory: `memory/CURRENT_WORK.md` (objective, next actions,
controller-handoff block), `memory/IMPLEMENTATION_PLAN.md`,
`memory/ExpRecord.md`. History: `memory/LTM/`; raw external-review text in
`memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` (newest-first; raw text is
evidence, summaries are pointers) + `INDEX.md`. Sync memory at
plan/code/result/review boundaries — the memory state must let the next
session (or another controller) continue without this chat.

Handoff templates: `.claude/agents/templates/subagent-task-brief.md`,
`subagent-report.md`, `expmanager-checkpoint.md`.
