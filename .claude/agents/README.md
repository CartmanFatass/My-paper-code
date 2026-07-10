# Claude Code Project Agents (HMASD Subagent Workflow)

This directory contains the HMASD project-local Claude Code subagents. It is the
Claude-side clone of the Codex subagent workflow defined in root `AGENTS.md` and
`.codex/agents/`. It is separate from `.codex/`: do not edit `.codex/` files or
`AGENTS.md` for Claude-only workflow changes, and do not edit `.claude/` files
for Codex-only workflow changes. When a rule must change in both workflows,
change both sides deliberately.

The runtime sources are the agent definitions in `.claude/agents/*.md`
(frontmatter: `name`, `description`, optional `tools`, `model`; body: the
agent's system prompt). Claude Code loads project agents automatically; a new
agent file may require a new session to be picked up. If a required project
agent is not available to the Agent tool, stop delegation and tell the user the
project subagent config is not loaded; do not substitute the built-in
`general-purpose`, `Explore`, or `Plan` agents for a project role.

When a Superpowers skill is active, Superpowers defines the process shape:
task briefs, report files, progress ledger, review packages, status handling,
and review loops. HMASD project rules only map those steps onto these project
subagents and project memory boundaries. Do not invent a parallel workflow that
contradicts an active Superpowers skill.

`docs/subagents/hmasd-subagent-workflow-reference.md` remains an optional,
lower-priority living reference for Superpowers-style subagent techniques.

## Roles And Model Tiers

The Codex workflow selects cost by explicit model + reasoning tiers. The Claude
clone maps those tiers onto Claude model classes:

| Codex tier | Claude `model` |
| --- | --- |
| `gpt-5.3-codex-spark` (spark, any effort) | `haiku` |
| `gpt-5.4-mini` (mini) | `haiku` |
| `gpt-5.4` (standard) | `sonnet` |
| `gpt-5.5` at `high` (frontier execution) | `opus` |
| `gpt-5.5` at `xhigh` (frontier judgment) | `fable` |

| Agent | Model | Sandbox intent | Role |
| --- | --- | --- | --- |
| `codebase-scout` | haiku | read-only | Focused codebase mapping and evidence gathering. |
| `simple-patcher` | haiku | write, no shell | Trivial single-file mechanical fixes. |
| `spark-implementer` | haiku | write | Cost-controlled non-core mechanical implementation from briefs. |
| `plan-implementer` | opus | write | High-tier core implementation from accepted plans; precise execution, not redesign. |
| `plan-implementer-frontier` | fable | write | Rare bounded core tasks requiring architecture/algorithm judgment while editing. |
| `implementation-reviewer-fast` | haiku | read-only | Small isolated mechanical-diff reviews. |
| `implementation-reviewer` | sonnet | read-only | Standard multi-file / judgment-heavy task reviews. |
| `implementation-reviewer-frontier` | fable | read-only | Architecture, high-risk, shared-state, API/data-contract, and final whole-branch reviews. |
| `test-runner` | haiku | run tests | Focused tests and failure triage. |
| `exp-manager` | haiku | write + run | Experiment operations, progress checks, factual `memory/ExpRecord.md` updates. |
| `result-analyst` | sonnet | write extracts | Bounded metric/gate extraction from existing run artifacts. |
| `external-review-manager` | haiku | write memory | Raw external-review archiving and handoffs. |
| `long-time-memory-manager` | haiku | write memory | Memory-only steward for compact records and LTM archives. |
| `workflow-auditor` | haiku | read-only | Subagent/workflow-document consistency audits. |
| `marl-peer-reviewer` | sonnet | run Codex CLI + write review archive | Cross-validation peer review of MARL algorithm design decisions via the Codex plugin (GPT-tier external model). |

Intent notes carried over from the Codex config:

- `plan-implementer` is intentionally high-tier (opus) for accepted-plan core
  implementation: once the controller has decided the plan, the worker should
  execute precisely rather than overthinking or redesigning. Use
  `plan-implementer-frontier` (fable — one tier above the default implementer,
  mirroring Codex's gpt-5.5 high-vs-xhigh split) only for rare bounded core
  tasks whose brief explicitly requires architecture or algorithm judgment
  while editing. The two fable roles (frontier implementer and frontier
  reviewer) are the premium tier; their infrequency is the cost control.
- Reviewer cost is controlled by explicit reviewer tiers, not by skipping
  review gates. The final whole-branch review always uses
  `implementation-reviewer-frontier`.
- `long-time-memory-manager` is intentionally cheap because it is a
  memory-only service; escalate its model (per-call `model` override) only when
  the user explicitly asks for a deep memory audit or schema repair.
- `exp-manager` is intentionally cheap because experiment operations are
  context-heavy factual coordination, not deep algorithm design. The model
  choice does not relax the strict file-based status and context-budget
  contract.
- `result-analyst` is intentionally a stronger tier than exp-manager because
  artifact parsing and gate reads have proven error-prone, but it is still not
  an experiment launcher or record owner.
- `marl-peer-reviewer` is the automated counterpart of the copy-paste external
  review workflow: it runs one read-only round through the Codex plugin's
  companion runtime so Claude-made MARL design decisions are cross-validated by
  a non-Claude reviewer. The external reviewer is pinned explicitly to
  `gpt-5.5` at `xhigh` effort — the same frontier tier the Codex workflow uses
  for architecture/final reviews — and does not rely on the user's Codex config
  defaults; the dispatch brief may override it for low-stakes sanity checks.
  The local agent is sonnet because its own work (prompt composition,
  archiving, verdict mapping) is mechanical; the reviewing intelligence is the
  external model.

## Controller Protocol

The active Claude Code session is the main controller. Do not create a separate
MainAgent subagent. The controller owns user communication, task understanding,
subagent delegation, result integration, user reporting, and subagent lifetime.

The controller must:

- remain directly responsible to the user for task understanding, execution,
  explanation, and final decisions;
- clarify user intent, scope, completion criteria, and uncertainty before
  delegation when the task is ambiguous;
- decide what to do locally and what to delegate;
- implement core code locally by default when there is no clear parallelism,
  isolation, or review-throughput benefit from a subagent handoff;
- actively look for Superpowers-style parallel waves: independent domains,
  disjoint write scopes, file-based handoffs, and same-response dispatch;
- spawn subagents only for bounded work that materially advances the task;
- integrate subagent reports before presenting conclusions to the user;
- proactively translate experiment state, result facts, plan transitions, and
  subagent reports into user-facing situation, meaning, next plan,
  recommendation, core MARL impact, and remaining gates or blockers;
- report which subagents were used, what they did, important results, changed
  files, and remaining risk;
- maintain `.superpowers/sdd/progress.md` during superpowers execution-plan
  work so completed tasks are not re-dispatched after compaction or resume.

Memory delegation is not governance delegation. The controller may ask
`long-time-memory-manager` to maintain memory, but must not outsource
user-intent understanding, algorithm discussion, code/execution decisions,
subagent coordination, or user-facing interpretation.

## Controller Communication Contract

The main controller is the user's orchestrator, not only a dispatcher. Whenever
experiment state, result evidence, plan state, or subagent reports change what
the user should understand, the controller must proactively provide a compact
handoff with:

- Situation: what is running, done, blocked, or waiting, and which experiment,
  seed, artifact, or plan item matters.
- Meaning: what the facts imply for the current hypothesis or gate, separating
  factual evidence from controller interpretation.
- Next plan: what to wait for, inspect, run, change, or avoid next, including
  what action follows each likely outcome.
- Recommendation: the controller's current advice, including "wait and do not
  change the algorithm" when that is the best action.
- Core MARL impact: whether the next action touches reward, q_A/q_D/q_d,
  policy or critic architecture, optimizer/loss/advantage logic, collector
  semantics, environment dynamics, credit assignment, team intent, latent skill
  semantics, or other core algorithm behavior.
- Open gates and blockers: which metric, review, null control, or user decision
  must pass before reward, algorithm, experiment-scale, or implementation
  changes are allowed.

Do not make the user ask "what does this mean?". If the correct state is
waiting, name exactly what is being waited on, which metrics decide the next
branch, and what should not be changed while waiting.

## Experiment Communication Hard Gate

Every controller response that launches, packages, checks, summarizes, stops,
resumes, compares, or recommends a meaningful experiment must include an
explicit experiment-meaning block before or alongside commands and file paths:

```text
Experiment meaning:
- Hypothesis:
- Mechanism path:
- Core MARL impact:
- Metrics/gates:
- Time cost / device:
- Decision tree:
- Do not change yet:
- Status source:
```

Time-cost and device rule (user directive, 2026-07-09): every experiment or
compute-bearing analysis proposal MUST state its expected wall-clock cost to
the user BEFORE launch (per-arm breakdown for batches; use measured pace from
prior runs when available, and say so when the number is a guess). Training,
probe fitting, and analyzer runs default to CUDA. Never silently degrade to
CPU: if the GPU is occupied by a live run, present the conflict and the time
cost of each option (wait for GPU / share GPU / CPU) and let the user decide.

Cloud handoff rule (user directive, 2026-07-09): compute-intensive tasks (long
training, multi-seed batches, heavy analysis) default to the user's cloud
server. Protocol: tell the user directly with the time cost; write a
self-contained bash runner under `scripts/` per existing cloud-runner
conventions; commit and push it to the remote (this push is standing-authorized
for cloud runners specifically); the user pulls and launches server-side;
record launch commands and expected artifacts in `memory/ExpRecord.md`. Local
GPU is reserved for smokes and small diagnostics. Runner-writing is
spark-implementer or exp-manager work with a brief; the user-facing handoff
brief (what to run, what it answers, what to watch) remains mandatory.

If the controller gives only a command, package path, log path, or raw metric
table for a meaningful experiment, the response is incomplete unless the turn is
explicitly marked as a narrow mechanical answer where no experiment
interpretation was requested and no experiment state changed.

## Spawn And Lifetime Rules (Claude Code Runtime)

Spawn project agents with the Agent tool, `subagent_type` set to the agent
name from the table above. Runtime semantics differ from Codex:

- Subagents run in the background by default; the controller is notified when
  one completes. Use `run_in_background: false` only when the result is needed
  before the next critical-path step.
- Dispatch a whole wave by making all the Agent calls in the same response;
  one spawn per turn makes the workflow serial.
- A subagent's final message returns to the controller only; relay what matters
  to the user.
- There is no `close_agent`. A completed agent stays continuable: use
  `SendMessage` with its id/name to continue it with context intact (e.g.
  re-review after fixes, ExpManager follow-up phases). A fresh Agent call
  starts cold. Prefer continuing an existing reviewer/manager over respawning
  when the context is still valid; spawn fresh when the old context is stale,
  superseded, or checkpointed to files.
- There is no `wait_agent` timeout, but the equivalent rule still applies to
  long-running delegated work: silence is not failure. Before duplicating a
  dispatch or falling back to direct work, inspect the subagent's status/report
  files (`runner_status.txt`, `expmanager_checkpoint.md`, report paths),
  expected outputs, and process/file freshness. If they show progress, report
  that the work is in flight instead of re-dispatching.

Record per dispatched agent, in controller working notes for the turn: agent
name, task id, brief path, status returned, and whether it is expected to be
continued via SendMessage.

## Terminal Status Protocol

Every project subagent result must start with one status:

- `DONE`: work complete, artifact/report written, no controller action required
  beyond integration and normal checks.
- `DONE_WITH_CONCERNS`: work useful and mostly complete, but caveats, partial
  evidence, skipped checks, or residual risk remain.
- `NEEDS_CONTEXT`: a specific missing file, threshold, requirement, permission,
  command result, or decision is required before useful progress can continue.
- `BLOCKED`: the task cannot proceed without a changed plan, changed owner,
  runtime availability, permission, model/tier escalation, or corrected input.

Required short reply fields:

```text
Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Artifact/report: path or none
Changed files: list or none
Commands/tests: concise pass/fail summary or none
Concerns/blockers: concise or none
Next owner: controller | named subagent | user | none
```

Subagents must not paste large logs, full CSVs, giant diffs, long transcripts,
or traceback clusters into chat. Write those to bounded evidence files and
return the paths.

Controller response is status-driven:

- `DONE`: integrate, run required checks, update the progress ledger when
  applicable, record the lifetime decision.
- `DONE_WITH_CONCERNS`: integrate useful results; decide whether the concern is
  acceptable, needs a batch review, or needs a follow-up task; record it.
- `NEEDS_CONTEXT`: provide the specific missing context or split the task; do
  not resend the same prompt unchanged.
- `BLOCKED`: no blind retry. Change at least one of: supply new context, split
  the task smaller, change owner, escalate model/tier, inspect file-based
  status, revise the plan, or ask the user. Do not retry with the same model
  and same context unchanged.

## Mandatory Dispatch Brief Gate

No project subagent may be spawned until the controller has created or
identified an explicit dispatch brief, review package, experiment status
request, or compact dispatch block. For non-trivial work, prefer a file path
(template: `.claude/agents/templates/subagent-task-brief.md`) over chat-only
instructions.

The dispatch artifact or block must specify:

- task id and short goal;
- assigned agent, model tier, and (when overridden) per-call model;
- requirements source: user request, accepted plan, task brief, review package,
  experiment record, artifact path, or controller brief;
- owned files/directories, read-only scope, run directory, package path, memory
  row, or artifact set;
- log/artifact root for any command that may write runtime output, preferred
  default `logs/<experiment-id-or-run-id>/...`; existing `logs_*` roots only
  when an existing script or ExpRecord path requires them, named explicitly;
- forbidden files/directories/actions;
- output path: report, status/checkpoint file, package handoff, metric extract,
  review package, archive entry, or explicit `none`;
- required checks, commands, artifact inspections, or explicit `none`;
- dependencies, conflict scan, and whether parallel dispatch is allowed;
- terminal status contract;
- expected next owner and lifetime policy after the result is captured.

If the controller cannot state these fields, it must not spawn the subagent:
do the work locally, write the missing brief first, split the task, inspect the
required files, or ask the user. Do not rely on a subagent to infer ownership
boundaries or completion criteria from broad chat context.

## Runtime Output Contract

Log and artifact placement is part of subagent ownership. Any dispatch that may
run commands, create packages, write transcripts, or produce experiment
artifacts must name the runtime output root and whether new directories may be
created.

Default new experiment runs to `logs/<experiment-id-or-run-id>/...`. Existing
named roots such as `logs_r24_*` may be kept only when the brief names them for
compatibility. Loose root-level runtime files (`*.log`, `*.out`, `*.err`,
transient CSVs, ad hoc JSON status files) are forbidden unless the user
explicitly asks for that exact root path. If a subagent discovers a command
would write runtime output to the repository root or an unspecified log
directory, it must stop before launch when possible and return `NEEDS_CONTEXT`
or `BLOCKED` with the exact command. After subagent-run experiments, the
controller checks for unexpected root-level runtime files before finalizing.

Test hygiene: persistent automated tests belong under `tests/`; put pytest
basetemp/fixture output under `tests/.pytest_tmp/<task-id>` and clean up when
checks pass. No new root-level `test_*.py`, `*_test.py`, or scratch dirs.

## Workflow-Level Authorization And Throttling

Spawn subagents only when the user explicitly asks for subagents, delegation,
or parallel agent work. A user-approved subagent workflow is a standing
explicit authorization for the routine fixed hooks inside that workflow: once
the user authorizes a plan execution, experiment workflow, external review
archive workflow, memory synchronization workflow, or workflow-configuration
audit to use the project subagent system, the controller may run the routine
`long-time-memory-manager`, `exp-manager`, `result-analyst`, or
`external-review-manager` handoffs (or a `workflow-auditor` check inside an
authorized audit) without re-asking at every hook.

This automation does not transfer governance: the controller still owns user
intent, code direction, algorithm discussion, experiment interpretation,
external-advice disposition, git boundaries, integration, and final
explanation.

Throttle automatic hooks:

- `long-time-memory-manager`: batch memory impact at
  plan/code/result/external-review boundaries; one sync per implementation wave
  or completed turn; not after every small edit.
- `exp-manager`: meaningful experiment launches, packages, commands, factual
  log/result records, and `memory/ExpRecord.md` updates — not ordinary code
  edits. Experiment status/progress queries are exp-manager-owned: process
  state, log freshness, latest update/eval rows, error scans, key metric
  extracts, factual ExpRecord updates. When exp-manager generates or verifies
  facts that change experiment state, it updates the factual portions of
  `memory/ExpRecord.md` by default; make the handoff read-only only for
  explicit dry-run/status-only probes, and route a follow-up record update if a
  probe becomes record-worthy. Every exp-manager dispatch names the run/log
  root.
- `result-analyst`: metric-heavy extraction, threshold/gate tables, anomaly
  extracts, typical-step comparisons from existing artifacts. It does not
  launch runs, manage processes, package experiments, update ExpRecord by
  default, or decide scientific acceptance.
- Non-core but time-consuming experiment operations are cheap-tier work, not
  controller busywork: script running, quiet-job watching, process/log reading
  → `exp-manager`; gate tables from written artifacts → `result-analyst`;
  bounded mechanical script/metric-field edits → `spark-implementer`.
- `external-review-manager`: when raw outside-model text is pasted or an
  inbox/archive/index handoff is needed. It preserves evidence; it does not
  decide acceptance.
- `workflow-auditor`: read-only consistency checks after subagent/workflow
  config changes, before relying on a complex setup, or on suspected drift.
  For narrow edits the controller may validate directly and say no audit was
  needed.
- `marl-peer-reviewer`: the MARL Design Cross-Validation Gate is standing user
  authorization — run it once per design decision at the decision boundary,
  not per edit or per discussion turn. It consumes the user's Codex/OpenAI
  runtime; batch related design questions into one review package when they
  belong to the same decision.
- Implementation review gates are mandatory for subagent-driven implementation:
  every implementation task gets a task review, the final whole-branch review
  is required, and accepted findings go through fix → re-review. Do not reduce
  review frequency to save cost; select the reviewer tier instead.
- Git and publish work stays controller-owned by default, batched at
  finalization or explicit user request. No high-frequency git subagents.

If an automatic hook would launch a long-running process, spend external money,
touch remote systems, publish, push, or exceed the authorized scope, ask the
user first.

## Core Vs Non-Core Implementation Routing

Classify implementation tasks before dispatch. When uncertain, treat the task
as core.

**Core-implementation model floor (user directive, 2026-07-09): core algorithm
implementation is NEVER assigned to a haiku-tier agent — no exceptions.** Core
code (the list below, plus any numerical/quantitative logic whose correctness
is quality-critical) is implemented by the controller directly or by
`plan-implementer` (opus) / `plan-implementer-frontier` (fable). Haiku agents
(spark-implementer, simple-patcher, exp-manager) are restricted to operational
scripts, packaging, docs, and status plumbing, and must escalate the moment a
task touches algorithm or numerical semantics.

Core or high-risk work is controller-owned by default when serial: algorithm
mechanisms, training loops, reward and intrinsic-reward paths, model/policy
architecture, optimizer/loss/advantage/value logic, collector semantics,
environment dynamics, credit assignment, team-intent and q_A/q_D logic,
transition/effect discovery targets, checkpoint semantics, and shared config
flags that change algorithm behavior. `ha_ctse_process/standalone_agent.py`,
`ha_ctse_process/train.py`, and core modules under `ha_ctse_process/` are core
unless the controller explicitly scopes a purely mechanical edit.

Use `plan-implementer` for core work only with an accepted plan or
controller-written task brief that defines scope, owned files, forbidden files,
responsibilities, and verification target — and only when the handoff is worth
its communication cost. Use `plan-implementer-frontier` only with a concrete
work package and a stated reason why normal high-tier execution is
insufficient (unresolved architecture tradeoffs inside the implementation,
risky algorithm semantics reasoned through while editing, implementation as
part of the design proof).

Use `spark-implementer` directly, inside an authorized workflow, for non-core
mechanical work: experiment runners, packaging scripts, dist manifests,
documentation or memory formatting, plotting/CSV/TensorBoard field propagation
with exact fields specified, small tests for already-specified behavior, and
isolated wrapper/config text changes. `simple-patcher` remains only for trivial
single-file mechanical fixes. A cheap-tier worker must stop and escalate if the
task expands into core code or algorithm judgment.

Do not ask the user a vague "should I use an implementer?" question. Present
the concrete work package (scope, files, responsibilities, tier, why a
subagent helps, verification gates) or keep the work local.

## MARL Design Cross-Validation Gate (mandatory)

Any MARL algorithm design decision in this project requires cross-validation by
an independent, non-Claude model before it is accepted. This covers: new or
changed reward and intrinsic-reward semantics, q_A/q_D/q_d design, team-intent
and latent-skill semantics, policy/critic architecture choices, credit
assignment, duration/lifetime mechanisms, transition/effect discovery targets,
changes to diagnostic gate criteria, and changes to
`memory/ALGORITHM_PRINCIPLES.md`. Purely mechanical implementation of an
already cross-validated design does not re-trigger the gate.

Procedure:

1. The controller writes a design-review package: decision + motivation,
   mechanism path, alternatives considered, evidence vs. speculation, binding
   principles, and exact review questions.
2. Dispatch `marl-peer-reviewer` with that package. It runs one read-only
   review round through the Codex plugin runtime, archives the raw reply in
   `memory/LTM/external_reviews/` (evidence rule: raw before summary), and
   returns a verdict: SUPPORTS, SUPPORTS_WITH_CONDITIONS, CHALLENGES, or
   INSUFFICIENT_EVIDENCE.
3. The controller dispositions the advice explicitly (accept / reject / defer,
   with reasons), reports it to the user in the
   situation/meaning/next-plan/recommendation format, and routes
   `long-time-memory-manager` to sync the accepted conclusion and the INDEX.md
   "Memory Decision" column.
4. A CHALLENGES or INSUFFICIENT_EVIDENCE verdict does not veto the design, but
   overriding it requires the controller to state the counter-argument to the
   user before proceeding. Silence is not a disposition.

The copy-paste external review workflow (`external-review-manager`, user-pasted
Claude/GPT/Gemini rounds) remains available and satisfies this gate when the
pasted round addresses the same design decision. `marl-peer-reviewer` and
`external-review-manager` write the same archive files — never run them in the
same wave.

## Wave Plan Hard Gate

For any non-trivial task that may involve implementation, experiment launch,
packaging, result analysis, log/progress inspection, external review archiving,
memory synchronization, workflow auditing, or any subagent dispatch, create a
compact Wave Plan before starting execution. Show it to the user or write it to
a task brief when the work is substantial, risky, experiment-changing, or
subagent-driven; for small routine actions a compact controller note suffices,
but it must exist before dispatch.

```text
Wave Plan
- Objective:
- Requirements source:
- Local controller work:
- Subagent tasks:
  1. Agent:
     Task:
     Owns:
     Forbids:
     Output:
     Checks:
  2. ...
- Parallelism: yes/no and why
- Conflict scan: files, run dirs, memory rows, shared processes, unresolved decisions
- Core vs non-core routing:
- Experiment meaning block required? yes/no
- Expected user-facing report:
```

If the controller chooses not to use subagents where they would normally apply,
state the reason (single-threaded core code, task too small for overhead, no
safe file boundary, agents unavailable, blocked on local inspection). Using
subagents without a Wave Plan, or without explicit owned files, forbidden
scope, output path, and next owner, is an invalid workflow — correct it before
continuing.

Default routing for common HMASD work:

- Experiment status, launch, runner/package facts, ExpRecord factual updates →
  `exp-manager`.
- Metric-heavy reads from existing artifacts, gate tables, anomaly extracts →
  `result-analyst`.
- Mechanical non-core runner/package/doc/field-propagation edits →
  `spark-implementer`.
- Core algorithm, reward, q_A/q_D/q_d, training-loop, checkpoint, collector, or
  policy/critic semantics → controller by default, or `plan-implementer` with a
  concrete accepted work package.
- Outside-model text archiving → `external-review-manager`.
- MARL algorithm design decision pending acceptance → `marl-peer-reviewer`
  cross-validation round (mandatory gate above).
- Compact memory/plan/principle synchronization → `long-time-memory-manager`.
- Workflow and subagent configuration consistency audits → `workflow-auditor`.

## Pre-Flight Wave Review

Before dispatching a wave, build a compact pre-flight table in controller notes
or a task brief (not pasted into every subagent prompt):

| Task | Agent | Requirements | Owns | Must not touch | Output | Checks | Dependencies | Conflict risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Do not launch until predictable conflicts are resolved: overlapping write
scope, shared run directories, shared package paths, shared
`memory/ExpRecord.md` rows, shared processes, incompatible tests, missing
thresholds, missing task briefs, unresolved architecture decisions. Batch any
user questions before dispatch — do not discover predictable conflicts one
subagent at a time.

## Parallel Execution

Superpowers-style throughput comes from four rules:

1. Group by independent domain: different files, tests, scripts, metrics, docs,
   or run artifacts with no shared mutable state.
2. Hand off context as files: task brief, report file, review package, metric
   extract, status file, error extract. Do not paste long plan history or large
   outputs into subagent prompts.
3. Dispatch the whole wave in one response (multiple Agent calls in the same
   response run concurrently).
4. Wait sparingly. Continue non-overlapping local work; block on a result only
   when the next critical-path step needs it.

Tasks share a wave only with disjoint write scopes, no sequential dependency,
and no shared mutable runtime (same training process, package path, experiment
record row, or core module). Dispatch the full clean wave at once; use smaller
waves only when scopes are fuzzy or integration risk is high. Sidecar read-only
tasks (`codebase-scout` mapping, `result-analyst` on existing artifacts,
`exp-manager` process facts, `test-runner` verification, `workflow-auditor`
drift checks) can join a wave when they do not share written state.
`exp-manager` and `result-analyst` share an evidence wave only when
result-analyst reads artifacts that already exist and neither writes the same
run directory, package path, or ExpRecord row; otherwise run them sequentially.

After a wave returns: integrate reports, check for file conflicts, run the
union of required tests, update the progress ledger, record lifetime decisions,
then dispatch the required task reviewers at the appropriate tier. Independent
task reviews may run in parallel when their packages do not overlap.

## Progress Ledger

For superpowers execution-plan work, the controller owns
`.superpowers/sdd/progress.md` — a compact execution ledger, not long-term
memory and not an LTM-owned file. Read it before dispatching any wave; treat
tasks marked complete as done and do not re-dispatch them. If it is missing,
reconstruct status from task reports, `git log`, and file state first.

For each dispatched task, pass a task brief path and a report path; the worker
writes the full report file and returns only short status. After integration
and tests, update the ledger with task id, status, commits or file changes,
report path, tests, integration notes, and lifetime state. After compaction or
resume, trust the ledger plus git/file state over chat memory.

## Review Packages And Batch Fixes

For every task review and final whole-branch review, prepare a review package
file or compact review package entry before spawning the selected reviewer.
Trivial mechanical diffs may use a short package; the review is not skipped.

Minimum review package fields: review goal and risk level; reviewer tier
selected and why; user request or accepted plan path; task brief and report
paths; changed files and ownership scope; bounded diff package or excerpt
prepared by the controller; commands/tests run; known concerns and residual
risk; exact review questions; forbidden scope.

The reviewer reads the prepared diff exactly once, stays read-only, does not
run `git diff`/`git show`/`git log`, and does not broaden beyond the package
scope. Its report includes both `Spec Compliance` and `Code Quality` verdicts.
The controller decides which findings are accepted and sends one batch-fix
brief to one suitable implementer — never one fixer per finding — then runs
focused checks and routes a re-review of the affected package (prefer
SendMessage to the original reviewer when its context is still valid).

## Fixed Workflow Hooks

A hook means "make the routing decision deliberately"; it does not force a
spawn when there is no persistent state change.

- Plan accepted/changed/completed/abandoned: sync
  `memory/IMPLEMENTATION_PLAN.md`, `memory/CURRENT_WORK.md`, and relevant LTM
  entries directly or via `long-time-memory-manager`.
- Code changes verified: memory sync via `long-time-memory-manager` if project
  direction, algorithm behavior, experiment workflow, known risks, or next
  actions changed; otherwise state that no memory update is needed.
- Meaningful experiment launch: `exp-manager` creates/updates the factual
  record, command, package, handoff. `long-time-memory-manager` only if the
  launch changes objective, plan stage, principle state, or archive-worthy
  context.
- Experiment handoff ready: brief the user explicitly (experiment names,
  round/gate answered, reason, exact command, key flags, metrics to watch,
  pass/fail criteria, follow-up per outcome) — not only a memory record.
- Experiment logs/results reviewed: `exp-manager` records factual status in
  `memory/ExpRecord.md`; the controller owns interpretation and gives the user
  a situation/meaning/next-plan/recommendation readout stating whether the
  result permits or keeps blocked any reward/core-MARL change;
  `long-time-memory-manager` syncs accepted conclusions.
- Metric-heavy result reads: `result-analyst` produces bounded tables and
  run-local extracts; `exp-manager` keeps process/run-state facts and ExpRecord
  updates; the controller keeps scientific interpretation.
- Experiment result records are two-layer: exp-manager owns factual fields;
  controller interpretation persists only as a clearly labeled
  decision/interpretation field after the factual update, or through an LTM
  sync.
- Long-running or quiet-console exp-manager work uses the file-based status
  contract (`runner_status.txt`, `runner_output.log`, atomic phases,
  `expmanager_checkpoint.md` before each major phase) and the context-budget
  contract (bounded reads; large evidence to files). If context pressure
  appears, exp-manager checkpoints and exits cleanly; spawn a fresh
  continuation from the checkpoint.
- MARL algorithm design decision reached (by the controller or emerging from an
  implementation/review discussion): run the MARL Design Cross-Validation Gate
  via `marl-peer-reviewer` before treating the design as accepted, then
  disposition and sync as described in that section.
- External review pasted: `external-review-manager` archives raw text first;
  `long-time-memory-manager` may update memory only after reading the raw
  archive entry (summaries are indexes, not evidence; if raw text is missing,
  ask for recovery or mark the update incomplete). The controller decides
  accept/reject/defer.
- Subagent/workflow config changed: run or consider a `workflow-auditor`
  read-only check when the change is broad, risky, or spans protocol files;
  for narrow edits, validate directly and say no audit subagent was needed.

Before the final response of a subagent-using turn, report whether memory was
updated, which subagents were used, and any continuation decisions.

## Memory And Handoffs

Compact current memory: `memory/CURRENT_WORK.md`,
`memory/ALGORITHM_PRINCIPLES.md`, `memory/IMPLEMENTATION_PLAN.md`,
`memory/ExpRecord.md`. Historical records: `memory/LTM/`. Do not reintroduce
legacy attention-pointer semantics.

Handoff templates:

- `.claude/agents/templates/subagent-task-brief.md`
- `.claude/agents/templates/subagent-report.md`
- `.claude/agents/templates/expmanager-checkpoint.md`
