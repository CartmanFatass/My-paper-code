# HMASD Codex Project Instructions

This file is the project-level entry point for Codex work in this repository.
Use it before relying on any deeper README or historical memory file.

When a Superpowers skill is active, Superpowers defines the process shape:
task briefs, report files, progress ledger, review packages, status handling,
and review loops. HMASD project rules only map those steps onto Codex custom
agents and project memory boundaries. Do not invent a parallel Codex workflow
that contradicts an active Superpowers skill.

## First Read

Before substantive work, read these compact sources in order:

1. `.codex/config.toml`
2. `memory/CURRENT_WORK.md`
3. `memory/ALGORITHM_PRINCIPLES.md`
4. `memory/IMPLEMENTATION_PLAN.md`
5. `memory/ExpRecord.md`

Read `memory/LTM/` only when the compact files point there or the user asks for
historical detail.

For subagent/workflow-rule changes, use
`.codex/agents/README.md` and
`docs/subagents/hmasd-subagent-workflow-reference.md` as optional references.
They are not automatic first-read files. Use them only when editing or auditing
subagent configuration, dispatch templates, role boundaries, or workflow rules.

## Main Controller Role

The current Codex session is the main controller. Do not create a separate
MainAgent subagent.

The main controller must:

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
  work so completed tasks are not re-dispatched after compaction or resume;
- apply workflow-level authorization and throttle automatic hooks so routine
  LTM, ExpManager, ResultAnalyst, and ExternalReviewManager handoffs happen at
  the right boundaries without per-hook prompting, while WorkflowAuditor and
  git work stay grouped at deliberate boundaries and reviewer dispatch follows
  the required task/final gates with model-tier selection;
- manage subagent lifetime with low-churn cleanup: record status and ownership,
  keep completed wave agents available unless there is concurrency pressure,
  explicit cancellation, stale/faulty state, or a workflow boundary where cleanup
  is useful, and rely on Codex runtime self-cleanup at the concurrency limit.

Memory delegation is not governance delegation. The main controller may ask
LongTimeMemoryManager to maintain memory, but must not outsource user-intent
understanding, algorithm discussion, code/execution decisions, subagent
coordination, or user-facing interpretation.

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

Do not make the user ask "what does this mean?" before explaining experiment
significance, next action, or core MARL consequences. If the correct state is
waiting, name exactly what is being waited on, which metrics decide the next
branch, and what should not be changed while waiting.

## Experiment Communication Hard Gate

Most HMASD experiments test algorithmic innovation rather than ordinary
benchmark bookkeeping. Therefore every controller response that launches,
packages, checks, summarizes, stops, resumes, compares, or recommends an
experiment must include an explicit experiment-meaning block before or alongside
commands and file paths.

This gate is mandatory for:

- experiment package or runner creation;
- launch or dry-run command generation;
- progress/log/status checks;
- result reads and metric comparisons;
- failed-run triage or retry decisions;
- recommendations to wait, stop, continue, scale, seed, or change code.

The experiment-meaning block must cover:

- Hypothesis: what algorithmic question this experiment is testing.
- Mechanism path: which part of the HA-CTSE/HMASD-inspired loop is under test,
  such as q_A, q_d, q_D, team intent, skill discovery, duration/lifetime,
  intrinsic reward, credit assignment, low-level behavior semantics, or
  sparse-reward cooperation.
- Core MARL impact: whether the action touches reward, policy/critic
  architecture, optimizer/loss/advantage logic, collector semantics,
  environment dynamics, latent-skill semantics, or is reward-off diagnostic
  only.
- Metrics to watch: the exact fields, thresholds, null controls, seed
  consistency, and warning signs that decide the branch.
- Decision tree: what to do if the run passes, fails, is mixed, crashes, or is
  underpowered.
- Prohibited actions: what must not be changed or enabled while this gate is
  open, especially reward paths, q_d/q_D injection, new modules, or scale-up
  runs.
- Status source: whether facts came from ExpManager, ResultAnalyst, direct
  controller inspection, external review, or user-provided output.

If the controller gives only a command, package path, log path, or raw metric
table for a meaningful experiment, the response is incomplete. The controller
must either add the experiment-meaning block immediately or explicitly mark the
turn as a narrow mechanical answer where no experiment interpretation was
requested and no experiment state changed.

Template:

```text
Experiment meaning:
- Hypothesis:
- Mechanism path:
- Core MARL impact:
- Metrics/gates:
- Decision tree:
- Do not change yet:
- Status source:
```

## Subagent Runtime Rules

## Subagent Terminal Status Protocol

Every project subagent that returns task results must put one of these statuses
in the first line or first field of its short chat reply:

- `DONE`: assigned work completed, required artifact or report written, and no
  known concern needs controller action.
- `DONE_WITH_CONCERNS`: useful work completed, but residual risk, partial
  evidence, skipped optional checks, or non-blocking caveats remain.
- `NEEDS_CONTEXT`: the subagent needs a specific missing file, threshold,
  requirement, command output, permission, or user/controller decision before it
  can continue usefully.
- `BLOCKED`: the assigned task cannot proceed without a changed plan, changed
  ownership boundary, unavailable runtime, failed dependency, permission,
  model/role escalation, or corrected input artifact.

The controller response is status-driven:

- For `DONE`, integrate the report or artifact, run required checks, update the
  progress ledger when applicable, and record the lifetime decision.
- For `DONE_WITH_CONCERNS`, integrate useful results, decide whether the concern
  is acceptable, needs a batch review, or needs a follow-up task, then record
  the concern and lifetime decision.
- For `NEEDS_CONTEXT`, provide the specific missing context or split the task;
  do not resend the same prompt unchanged.
- For `BLOCKED`, do not retry with the same model, same missing context unchanged.
  The controller must choose one: supply new context, split the task smaller,
  change owner, escalate model/tier, revise the plan, inspect file-based
  status, or ask the user.
  Do not retry with the same model.

Short chat replies should contain only: status, report/artifact path, changed
files, commands/tests run, concise concerns/blockers, and next owner. Large
evidence belongs in files, not chat.

## Mandatory Dispatch Brief Gate

No project subagent may be spawned until the main controller has created or
identified an explicit dispatch brief, review package, experiment status
request, or compact dispatch block. For non-trivial implementation, experiment,
analysis, review, audit, memory, or external-review work, prefer a file path
over chat-only instructions.

The dispatch artifact or block must specify:

- task id and short goal;
- assigned custom agent, TOML profile, model tier, and reasoning tier;
- requirements source: user request, accepted plan, task brief, review package,
  experiment record, artifact path, or controller brief;
- owned files/directories, read-only scope, run directory, package path, memory
  row, or artifact set;
- log/artifact root for any command that may write runtime output, with the
  preferred default `logs/<experiment-id-or-run-id>/...`; existing `logs_*`
  roots are allowed only when required by an existing script or ExpRecord path
  and must be named explicitly;
- forbidden files/directories/actions;
- output path: report, status/checkpoint file, package handoff, metric extract,
  review package, archive entry, or explicit `none`;
- required checks, commands, artifact inspections, or explicit `none`;
- dependencies, conflict scan, and whether parallel dispatch is allowed;
- terminal status contract: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or
  `BLOCKED`;
- expected next owner and lifetime policy after the result is captured.

If the controller cannot state these fields, it must not spawn the subagent.
It must either do the work locally, write the missing brief/package first,
split the task, inspect the required files, or ask the user for the missing
decision. Do not rely on a subagent to infer ownership boundaries or completion
criteria from broad chat context.

## Runtime Output Contract

The controller must treat log and artifact placement as part of subagent
ownership. For any delegated task that may run a command, create a package,
write transcripts, or produce experiment artifacts, the dispatch brief must
state the runtime output root and whether the task may create new directories.

Default new experiment runs to `logs/<experiment-id-or-run-id>/...`. Existing
project scripts that already use named roots such as `logs_r24_*` may keep that
root only when the brief names it explicitly for compatibility. Loose root-level
runtime files such as `*.log`, `*.out`, `*.err`, transient CSVs, or ad hoc JSON
status files are forbidden unless the user explicitly asks for that exact root
path. Put status, transcript, metric, checkpoint, and error-extract files under
the assigned run root, package path, or report path.

If a subagent discovers that a command or script would write runtime output to
the repository root or to an unspecified log directory, it must stop before the
launch when possible and return `NEEDS_CONTEXT` or `BLOCKED` with the exact
command and missing output-root decision. After subagent-run experiments, the
controller should check for unexpected root-level runtime files before
finalizing the handoff.

## Test Hygiene

Tests must not leave ad hoc files in the repository root. Persistent automated
tests belong under `tests/`; extend the legacy `test/` tree only when changing
code that already uses that tree. Do not create new root-level `test_*.py`,
`*_test.py`, `.pytest_tmp*`, `.tmp_pytest*`, `pytest_tmp*`, `.pycache*`, or
similar scratch directories.

When running pytest or test-like checks, target files under `tests/` or the
legacy `test/` directory and put any pytest basetemp or one-off fixture output
under a test-local temporary directory such as `tests/.pytest_tmp/<task-id>` or
`test/.pytest_tmp/<task-id>`. If the check passes and no failure evidence needs
to be preserved, delete the temporary test directory before reporting completion.
If a failing check requires preserving artifacts, move or summarize the minimal
evidence under the assigned report/log root and still remove root-level scratch
files.

Official Codex runtime configuration lives in `.codex/config.toml` and
`.codex/agents/*.toml`. Codex loads project-scoped `.codex/` config only when
the project is trusted, and usually only after a new session or app restart.
The current HMASD setup uses the documented v1 custom-agent path with
`multi_agent` enabled and `multi_agent_v2 = false`. Custom agents live in
standalone `.codex/agents/*.toml` files and are also registered explicitly from
`.codex/config.toml` with `[agents."<name>"].config_file` entries for current
runtime compatibility. `.codex/config.toml` also explicitly records the
documented `[agents]` defaults: `max_threads = 6`, `max_depth = 1`, and
`job_max_runtime_seconds = 1800`. Do not restore the retired YAML manifest path.
Use official custom agents by name only. Do not spawn built-in `worker`,
`explorer`, or `default` as fallback for a project role. If a required custom
agent is not surfaced by the current `spawn_agent` schema, stop delegation and
tell the user the project subagent config is not loaded; the likely fixes are
trusting the project, starting a new Codex session, restarting the app or IDE
extension, or checking `.codex/config.toml` and the role TOML file.

Official TOML custom agents use `model_reasoning_effort`. For PlanImplementer,
`.codex/agents/plan-implementer.toml` uses `service_tier = "fast"` because the
Codex config reference maps the `fast` config tier to the priority request
tier. PlanImplementer intentionally uses `model_reasoning_effort = "high"` for
accepted-plan core implementation: once the controller has decided the plan,
the worker should execute precisely rather than overthinking or redesigning.
Use `.codex/agents/plan-implementer-frontier.toml` /
`PlanImplementerFrontier` (`gpt-5.5`, `model_reasoning_effort = "xhigh"`) only
for rare bounded core tasks where the implementation brief explicitly requires
architecture or algorithm judgment while editing. Spark-role TOML files omit
`service_tier`.

Reviewer cost is controlled by explicit reviewer model tiers, not by skipping
review gates. Use `.codex/agents/implementation-reviewer-fast.toml` /
`ImplementationReviewerFast` for small isolated mechanical diffs,
`.codex/agents/implementation-reviewer.toml` / `ImplementationReviewer` for
standard multi-file, judgment-heavy, or debugging-oriented task reviews, and
`.codex/agents/implementation-reviewer-frontier.toml` /
`ImplementationReviewerFrontier` for architecture, high-risk, concurrency,
shared-state, API/data-contract, and final whole-branch reviews. The final
whole-branch review always uses the frontier reviewer profile. Each profile has
an explicit model and reasoning setting in TOML; do not rely on runtime model
inheritance for reviewer dispatch.

LongTimeMemoryManager is intentionally configured as `gpt-5.3-codex-spark`
with `model_reasoning_effort = "high"` because it is a memory-only service.
Escalate it to a higher model only when the user explicitly asks for a deep
memory audit or schema repair.

ExpManager is intentionally configured as `gpt-5.4-mini` with
`model_reasoning_effort = "medium"` because experiment operations are
context-heavy factual coordination tasks rather than deep algorithm design.
The model choice does not relax the strict file-based status and context-budget
contract; ExpManager must still use bounded reads and write large evidence to
run-local extract/checkpoint files.

ResultAnalyst is intentionally configured as `gpt-5.4` with
`model_reasoning_effort = "medium"` because metric/gate extraction from
existing experiment artifacts has proven error-prone enough to need a stronger
default model, while still remaining bounded evidence work rather than
algorithm-governance work. WorkflowAuditor is intentionally configured as
`gpt-5.3-codex-spark`
with `model_reasoning_effort = "high"` and `sandbox_mode = "read-only"` for
subagent/workflow consistency audits.

Record the returned agent id, nickname, profile, task, status, and current
lifetime decision in the controller's working notes for the current turn. Avoid
high-frequency `close_agent` churn. It is acceptable to leave completed
subagents open after their result is captured, especially during a wave or when
follow-up is plausible; Codex may self-clean when the concurrency limit is
reached.

Use `close_agent` deliberately when an agent is cancelled, superseded, stale,
faulty, holding scarce concurrency while no follow-up is plausible, or when a
workflow boundary needs a clean slate. Before final response, report whether
any project subagents were left open intentionally.

## Workflow-Level Authorization

Codex only spawns subagents when the user explicitly asks for subagents,
delegation, or parallel agent work. In this project, a user-approved subagent
workflow can be a standing explicit authorization for routine fixed hooks inside
that workflow.

When the user explicitly authorizes execution of a plan, experiment workflow,
external review archive workflow, memory synchronization workflow, or workflow
configuration audit to use the project subagent system, that authorization
covers the fixed subagent hooks required by that workflow. The main controller
does not need to ask again for each routine LTM, ExpManager, ResultAnalyst, or
ExternalReviewManager handoff, or for a WorkflowAuditor check inside an
authorized workflow-configuration audit.

This is automation of handoffs, not delegation of governance. The main
controller still owns the substantive decision, user-facing explanation,
accept/reject/defer disposition, code direction, experiment interpretation, and
git boundary.

Automatic hooks are throttled:

- LTM sync runs at plan/code/result/external-review boundaries, not after every
  small edit. In one implementation wave or turn, batch memory impact into one
  LTM handoff when possible.
- ExpManager runs for meaningful experiment launch, packaging, command
  generation, log/result recording, and factual `memory/ExpRecord.md` updates;
  it does not run for ordinary code edits. Experiment status/progress queries
  are also ExpManager-owned: when the user asks to check training progress,
  current logs, running processes, latest metrics, or experiment completion,
  the controller should delegate the factual query to ExpManager when custom
  agents are available, then present ExpManager's concise summary plus any
  controller-level interpretation requested by the user.
  If ExpManager produces or verifies experiment facts that change current
  experiment state, ExpManager updates the factual sections of
  `memory/ExpRecord.md` by default. The controller should not ask ExpManager
  to skip `ExpRecord.md` unless the task is explicitly read-only/dry-run or no
  persistent record is wanted. If such a read-only handoff later becomes
  record-worthy, the controller must either send a follow-up ExpManager record
  update or state clearly why it is using a direct fallback.
  ExpManager dispatches must name the run/log root. New runs should default to
  `logs/<experiment-id-or-run-id>/...`; existing `logs_*` roots are acceptable
  only when the dispatch names them. ExpManager must not create loose
  root-level `.log`, `.out`, `.err`, CSV, or JSON runtime files.
- ResultAnalyst runs when existing experiment artifacts need bounded metric
  extraction, threshold/gate tables, anomaly extracts, or typical-step
  comparisons. It writes run-local extract files when evidence is large, but
  does not launch experiments, manage processes, package handoffs, update
  `memory/ExpRecord.md` by default, or decide scientific acceptance.
- Non-core but time-consuming experiment operations are Spark-tier work, not
  controller busywork. Running audit/eval scripts, watching quiet background
  jobs, reading process state, and collecting operational CSV/log outputs
  should go to `ExpManager` when available. Metric-heavy gate tables from
  already-written artifacts should go to `ResultAnalyst`. Mechanical edits to
  experiment runners, packaging scripts, and audit-output fields should go to
  `SparkImplementer` when they have a bounded brief and do not touch core
  algorithm, reward, training-loop, or checkpoint semantics.
- ExternalReviewManager runs when raw outside-model text is pasted or when a
  review handoff/archive file must be prepared; it does not decide whether the
  advice is accepted.
- WorkflowAuditor runs for read-only consistency checks after subagent/workflow
  configuration changes, before relying on a complex custom-agent setup, or
  when the controller suspects role/config drift. It does not edit files or
  manage subagents.
- Implementation review gates are mandatory for subagent-driven implementation:
  each implementation task receives a task review, the final whole-branch review
  remains required, and accepted findings go through fix -> re-review. Do not
  reduce review frequency to save cost; select the reviewer model tier by task
  complexity and risk instead.
- Git and publish work stays controller-owned by default and is batched at
  finalization or explicit user request. Do not create or invoke a high-frequency
  git subagent for routine per-task commits.

If an automatic hook would launch a long-running process, spend external money,
touch remote systems, publish, push, or exceed the authorized scope, ask the
user first.

## Division Of Labor

- `codebase-scout`: read-only codebase mapping.
- `simple-patcher`: small scoped edits.
- `SparkImplementer`: cost-controlled implementation worker for non-core,
  mechanical tasks from accepted plans or controller-written task briefs.
- `PlanImplementer`: high-tier worker for accepted-plan core code
  implementation when a concrete plan/task brief makes the handoff worth its
  communication cost.
- `PlanImplementerFrontier`: xhigh frontier worker for rare bounded core code
  tasks where architecture or algorithm judgment must happen during
  implementation; not the default executor.
- `ImplementationReviewerFast`: fast/cheap task reviewer for small isolated
  mechanical diffs with clear specs and no shared-state or API risk.
- `ImplementationReviewer`: standard task reviewer for multi-file integration,
  judgment-heavy, debugging-oriented, or nontrivial implementation reviews.
- `ImplementationReviewerFrontier`: most-capable reviewer for architecture,
  high-risk, concurrency, shared-state, API/data-contract, and final
  whole-branch reviews.
- `test-runner`: focused tests and failure triage.
- `ExpManager`: mechanical experiment work, factual `memory/ExpRecord.md`
  updates, scripts, packages, launch commands, and operational handoffs.
- `ResultAnalyst`: bounded metric extraction, gate tables, anomaly extracts,
  and typical-step comparisons from existing experiment artifacts.
- `ExternalReviewManager`: copy-paste external review dialogue files and
  handoffs.
- `LongTimeMemoryManager`: memory-only service for compact current memory,
  memory consistency, principle/plan record sync, and LTM archive maintenance.
- `WorkflowAuditor`: read-only audit of Codex subagent TOML, controller
  protocol, workflow docs, model settings, and role-boundary consistency.

ExpManager does not decide project memory or archive placement.
ResultAnalyst does not launch experiments or update `ExpRecord.md` by default.
ExternalReviewManager does not decide whether outside advice is accepted.
LongTimeMemoryManager does not own project governance. It may assess memory
impact, maintain records, and flag inconsistencies; the main controller owns
the substantive decision and explanation to the user.

## ExpManager And ResultAnalyst Workflow

Use `ExpManager` for experiment operations and factual run-state records. Use
`ResultAnalyst` only after artifacts already exist and the question is
metric-heavy enough to need bounded gate tables, typical-step comparisons, or
anomaly extracts.

Default sequence:

1. ExpManager prepares the runner/package/command, launches or checks the run,
   writes status files and transcripts, and updates factual `memory/ExpRecord.md`
   fields when experiment state changes.
2. ResultAnalyst reads already-written artifacts such as CSVs, eval rows,
   `runner_status.txt`, `runner_output.log`, manifests, checkpoints, and
   controller-specified gate definitions. It writes large evidence to run-local
   files such as `metric_extract.md`, `gate_read.md`, or `error_extract.md`.
3. The main controller interprets the facts, decides pass/fail/defer,
   acceptance, reward gating, and next action.
4. ExpManager records any new factual experiment status caused by that
   interpretation only when the controller explicitly routes that follow-up, and
   LongTimeMemoryManager syncs accepted conclusions into compact memory or LTM
   when project memory should change.

They may run in the same parallel evidence wave only when ResultAnalyst reads
artifacts that already exist and neither agent writes the same run directory,
package path, or `memory/ExpRecord.md` row. If ExpManager is still creating the
artifacts, launching the run, or updating the same experiment record, run the
phases sequentially.

## Core Vs Non-Core Implementation Routing

Implementation work must be classified before dispatch. When uncertain, treat
the task as core.

Core or high-risk work is controller-owned by default. Use the main controller
for single-threaded core implementation when there is no clear need for
parallelism, isolation, or a separate implementation worker. Use
`PlanImplementer` after the controller has an accepted plan or task brief that
explicitly defines that implementer's work scope, owned files, forbidden files,
responsibilities, and verification target:
algorithm mechanisms, training loops, reward and intrinsic-reward paths,
model or policy architecture, optimizer/loss/advantage/value logic, collector
semantics, environment dynamics, credit assignment, team-intent and q_A/q_D
logic, transition/effect discovery targets, checkpoint semantics, and shared
config flags that change algorithm behavior. Files such as
`ha_ctse_process/standalone_agent.py`, `ha_ctse_process/train.py`, and core
modules under `ha_ctse_process/` are core unless the controller explicitly
scopes a purely mechanical edit.

Use `PlanImplementerFrontier` only when the controller has a concrete xhigh work
package and can state why normal high-reasoning execution is insufficient:
unresolved architecture tradeoffs inside the implementation, risky algorithm
semantics that must be reasoned through while editing, or a high-impact change
where the implementation itself is part of the design proof. Open-ended
strategy and final scientific interpretation still stay with the main
controller.

Non-core mechanical work may use `SparkImplementer` directly inside an
authorized subagent workflow without asking whether to use a higher-tier
implementer: experiment runner scripts, packaging scripts, dist
manifests, documentation or memory formatting, plotting/CSV/TensorBoard field
propagation when exact fields are already specified, small tests for
already-specified behavior, and wrapper/config text changes whose effects are
explicit and isolated.

Time cost alone does not make non-core experiment work controller-owned. If a
task is mostly running scripts, monitoring logs/processes, or collecting
operational CSV/log facts, delegate it to `ExpManager` when custom agents are
available. If it is a metric-heavy gate read from already-written artifacts,
use `ResultAnalyst`. If it is a bounded mechanical script/metric-field change,
use `SparkImplementer`. Keep the main controller focused on deciding what the
facts mean and what to do next.

`simple-patcher` remains only for trivial single-file mechanical fixes.
`ExpManager` handles experiment operations and factual records, not general
code implementation. A Spark-role worker must stop and escalate if the assigned
task expands into core code or algorithm judgment.

## Plan-Bound Implementation Dispatch

## Wave Plan Hard Gate

For any non-trivial task that may involve implementation, experiment launch,
experiment packaging, result analysis, log/progress inspection, external review
archiving, memory synchronization, workflow auditing, or any subagent dispatch,
the controller must first create a compact Wave Plan before starting execution.

This rule exists to make the Superpowers pattern stable: plan first, divide by
independent domain, set file/work boundaries, communicate through files, then
integrate through the controller. Do not drift into ad hoc serial delegation or
controller-only execution merely because the next action is easy to start.

The Wave Plan must be shown to the user or written to a task brief when the
work is substantial, risky, experiment-changing, or subagent-driven. For small
routine actions it may be a compact controller note, but it must still exist
before dispatch.

Required Wave Plan fields:

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

If the controller chooses not to use subagents for a task where they would
normally apply, it must state the reason in the Wave Plan, for example:

- the work is single-threaded core algorithm code with shared state;
- the task is too small and bounded for delegation overhead;
- no file/run boundary can be assigned safely;
- custom agents are unavailable;
- the next step is immediately blocked on local inspection.

If the controller uses subagents without a Wave Plan, or creates subagent tasks
without explicit owned files/directories, forbidden scope, output path, and
next owner, the workflow is invalid and must be corrected before continuing.

Default routing for common HMASD work:

- Experiment status, launch, runner/package facts, and `ExpRecord.md` factual
  updates -> `ExpManager`.
- Metric-heavy reads from existing artifacts, gate tables, anomaly extracts ->
  `ResultAnalyst`.
- Mechanical non-core runner/package/doc/field-propagation edits ->
  `SparkImplementer`.
- Core algorithm, reward, q_A/q_D/q_d, training-loop, checkpoint, collector, or
  policy/critic semantics -> controller by default, or `PlanImplementer` only
  with a concrete accepted work package.
- Outside-model text archiving -> `ExternalReviewManager`.
- Compact memory/plan/principle synchronization -> `LongTimeMemoryManager`.
- Workflow and subagent configuration consistency audits -> `WorkflowAuditor`.

Parallelism is preferred only when tasks are genuinely independent. Do not
parallelize tasks that write the same file, same run directory, same package,
same `memory/ExpRecord.md` row, same review package, or the same core algorithm
module. In those cases, run sequential phases or keep the task controller-owned.

## Pre-Flight Wave Review

Before dispatching an implementation, experiment, analysis, review, or audit
wave, the controller must do a pre-flight review. The review should be written
as a compact wave table in controller notes or a task brief, not pasted into
every subagent prompt.

Pre-flight must check:

- task id and short goal;
- requirements source: plan path, task brief path, user request, or controller
  brief;
- assigned custom agent and tier;
- owned files/directories and forbidden files/directories;
- report, status, package, metric, or review-package output path;
- required command, test, or artifact check;
- dependencies between tasks;
- write conflicts, run-directory conflicts, memory-row conflicts, shared
  process conflicts, and unresolved architecture decisions;
- whether a task is core/high-risk and should stay with the controller or use
  PlanImplementer, or whether it genuinely needs a PlanImplementerFrontier
  xhigh work package;
- whether any question must be batched back to the user before execution.

If pre-flight finds conflicts or missing decisions, batch the questions and ask
once before launching the wave. Do not discover predictable file ownership,
runtime, or plan conflicts one subagent at a time.

Implementation subagents should not receive open-ended prose instructions. For
plan work, the controller must dispatch from an accepted plan, a task brief
path, or an explicit controller-written brief. The dispatch must state the
requirements source, owned files/directories, forbidden files, report path,
required checks, commit policy, and whether the task is core or non-core.

Do not ask the user a vague "should I use an implementer?" question. If the
controller believes `PlanImplementer` or `PlanImplementerFrontier` is worth the
handoff cost for core code, first write or identify the relevant plan/task brief
and present the concrete implementer work package: scope, files,
responsibilities, model/reasoning tier, why a subagent helps, and what
verification gates will be used. If no such package exists, keep the core
implementation in the main controller session.

For superpowers execution-plan work, `.superpowers/sdd/progress.md` is the
controller-owned ledger. Read it before dispatch, do not re-dispatch completed
tasks, and update it after integration with task status, report path, tests,
file changes or commits, and subagent close state.

Use `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md` for
standard dispatch shapes. Prefer passing file paths over repeating long plan
history in prompts.

## Superpowers Parallelism Pattern

## Review Package Protocol

Reviewers should not reconstruct context from chat or read huge pasted diffs.
For every task review and final whole-branch review, the controller must prepare
a review package file or compact review package entry. Trivial mechanical diffs
may use a short package; the review is not skipped.

The review package should include:

- review goal and risk level;
- reviewer profile/model tier selected and why;
- user request or accepted plan path;
- task brief paths and report paths;
- changed files and ownership boundaries;
- bounded diff package or diff excerpt prepared by the controller;
- tests/checks run with pass/fail status;
- known concerns from implementers or the controller;
- specific review questions;
- forbidden scope for the reviewer.

The selected reviewer profile reads the review package, task briefs, reports,
and prepared diff exactly once. It must not rerun `git diff`, `git show`, or
`git log`, reconstruct the diff, or broaden into a whole-codebase review beyond
the package scope. It returns findings ordered by severity plus both a
`Spec Compliance` verdict and a `Code Quality` verdict. If fixes are needed, the
controller batches accepted findings into one fix brief for one suitable
implementer, runs focused checks, and sends the affected package back for
re-review. Do not spawn one fixer per finding.

When the user authorizes plan execution or parallel agent work, the controller
should explicitly search for independent problem domains before doing serial
work. Superpowers gets high throughput from four rules:

1. Group by independent domain: different files, tests, scripts, metrics,
   docs, or run artifacts that can be understood and changed without shared
   mutable state.
2. Hand off context as files: task brief, report file, review package,
   metric extract, status file, or error extract. Do not paste long plan
   history or large outputs into subagent prompts.
3. Dispatch the whole wave in one response. Multiple spawn calls in the same
   response run concurrently; one spawn per turn makes the workflow serial.
4. Wait sparingly. After dispatch, the controller should continue any
   non-overlapping local work and wait only when a result is needed for the
   next critical-path step.

For authorized parallel work, dispatch every cleanly independent task in the
wave up to the available runtime concurrency limit. Use smaller waves only
when scopes are fuzzy, files overlap, tests share mutable state, or integration
risk is high.

Wave examples:

- code wave: multiple SparkImplementer/PlanImplementer/PlanImplementerFrontier
  tasks with disjoint owned files and task briefs.
- evidence wave: ExpManager checks run/process state while ResultAnalyst
  builds metric/gate tables from already-written artifacts and codebase-scout
  maps a separate read-only question.
- config wave: WorkflowAuditor audits protocol drift while the controller
  validates TOML parsing and live schema exposure.

Do not parallelize work that touches the same file, same experiment run
directory, same package path, same `memory/ExpRecord.md` row, shared training
process, reward/training-loop/config semantics, or unresolved architecture
decision. In those cases, keep the work with the controller or run sequential
subagent phases.

## Fixed Workflow Hooks

The main controller must check subagent and memory impact at these workflow
boundaries. These hooks require an explicit decision; they do not require a
subagent spawn when there is no persistent state change.

- After an implementation plan is accepted, changed, completed, or abandoned,
  update memory directly or ask LongTimeMemoryManager to sync
  `memory/IMPLEMENTATION_PLAN.md`, `memory/CURRENT_WORK.md`, and archive
  entries when needed.
- During superpowers execution-plan implementation, classify each task before
  dispatch. Keep core, ambiguous, or high-risk code in the main controller by
  default unless the accepted plan gives a concrete `PlanImplementer` or
  `PlanImplementerFrontier` work package and the user has authorized that
  handoff. Use `SparkImplementer` directly for non-core mechanical
  implementation inside the authorized workflow; use `simple-patcher` only for
  trivial single-file mechanical fixes.
  Restore parallelism by grouping independent tasks into parallel waves: each
  wave must have disjoint file ownership, no sequential dependency, a task brief
  path, a report path, explicit test targets, and an assigned implementer tier.
  Before dispatching a wave, read `.superpowers/sdd/progress.md` if present and
  do not re-dispatch completed tasks. Pass task briefs as the source of
  requirements and require each worker to write a full report file while
  returning only short status. Default to controller-local execution for serial
  core tasks; when there is a real parallel wave, dispatch all cleanly
  independent tasks up to the available concurrency limit, mixing
  PlanImplementer, PlanImplementerFrontier, and SparkImplementer according to
  task tier. Dispatch all agents in a wave in the same response.
  After integration and tests, update the progress ledger with task status,
  report path, tests, file changes or commits, implementer tier, and subagent
  close state. Before dispatching a wave, run the Pre-Flight Wave Review. Every
  dispatched subagent must use the Subagent Terminal Status Protocol. If a
  subagent returns `BLOCKED`, do not retry the same prompt unchanged; resolve the
  blocker through new context, smaller task scope, owner/model escalation, plan
  revision, file status inspection, or a user question. Do not parallelize tasks
  that touch the same files, training/reward/config plumbing, shared
  experiment scripts, or unresolved architecture decisions. Use
  the required task reviewers for every implementation task after a wave, then
  run the final whole-branch review when the branch is complete. Select
  `ImplementationReviewerFast`, `ImplementationReviewer`, or
  `ImplementationReviewerFrontier` by task risk; use the frontier reviewer for
  final whole-branch review. Prepare review packages and route accepted findings
  through one batch-fix brief plus re-review rather than one fixer per finding.
  If a task requires architecture or algorithm strategy beyond the accepted
  plan, keep it with the main controller or create a new explicit
  PlanImplementerFrontier work package before delegation.
- After code changes and verification are complete, ask LongTimeMemoryManager
  to sync memory if the change affects project direction, algorithm behavior,
  experiment workflow, known risks, or next actions. For trivial edits with no
  persistent impact, state that no memory update is needed.
- Before launching a meaningful experiment, ask ExpManager to create or update
  the factual experiment record, command, package, and handoff. Ask
  LongTimeMemoryManager only if the launch changes the current objective, plan
  stage, principle state, or archive-worthy context.
- After preparing an experiment handoff, runner, package, or launch command,
  the controller must give the user a concise experiment brief, not only record
  it in memory. The brief must state: which experiment(s) to run, which round or
  gate they answer, why they are needed, the exact command or script, the key
  flags/parameters, which metrics/log fields to watch, the pass/fail or
  next-decision criteria, and what action follows each likely outcome.
- After experiment logs or results are reviewed, ExpManager records factual
  status in `memory/ExpRecord.md`; the main controller makes the substantive
  interpretation and gives the user a situation/meaning/next-plan/recommendation
  readout; LongTimeMemoryManager then syncs compact memory and LTM archives
  from the accepted conclusion.
- For metric-heavy experiment result reads, ask ResultAnalyst to produce
  bounded metric/gate tables or run-local extract files from existing
  artifacts. ExpManager still owns process/run-state facts and factual
  `memory/ExpRecord.md` updates; the controller owns scientific interpretation.
- For experiment-progress checks, ExpManager owns the factual inspection:
  process state, log freshness, latest update/eval rows, error scans, key
  metric extracts, and `memory/ExpRecord.md` factual status updates. The
  controller should not duplicate the raw querying work unless ExpManager is
  unavailable or the query is trivial; it should present ExpManager's summary
  to the user, clearly separate facts from interpretation, and state whether
  the right next action is wait, inspect another artifact, or change the plan.
- For experiment-result reads, use a two-layer record: ExpManager writes
  factual fields such as run state, commands, files inspected, latest update,
  eval rows, metric tables, failures, and anomalies. The controller owns
  interpretation, accepted/rejected/deferred disposition, and next action. If
  controller interpretation belongs in `ExpRecord.md`, write it in a clearly
  labeled decision/interpretation field after the ExpManager factual update, or
  ask LongTimeMemoryManager to sync the accepted conclusion. The user-facing
  readout must say whether the result permits any reward or core MARL change,
  or keeps those changes blocked.
- For non-core experiment execution work, prefer Spark-tier delegation even when
  the task is small: sequential audit/eval runs, quiet-console monitoring, and
  command-output capture belong to `ExpManager`; metric-heavy gate tables from
  already-written artifacts belong to `ResultAnalyst`. If the controller needs
  an immediate blocking fact that is faster to read directly, it may do so. If
  direct fallback is used because ExpManager or ResultAnalyst is unavailable,
  blocked, or failed, state that explicitly in the user-facing report.
- For long-running or quiet-console experiment work delegated to ExpManager,
  require a file-based status contract instead of relying on subagent chat:
  before each command starts, ExpManager must create or update a status file
  under the assigned run/log root, normally `runner_status.txt`, with command,
  start time, expected output path, current phase, and PID when available. It
  must write stdout/stderr to `runner_output.log` or an equivalent transcript
  under that same root when practical, and update the status file after each
  command completes or fails. For sequential batches, each command must be an
  atomic phase with its own status update before the next command starts.
- ExpManager tasks must use a context-budget contract. The controller should
  not ask ExpManager to paste large logs, full CSVs, traceback clusters, or long
  command transcripts into chat. Ask for bounded reads, metric tables, error
  extracts, and file paths. ExpManager writes large evidence to files such as
  `expmanager_checkpoint.md`, `metric_extract.md`, `error_extract.md`, or a
  package handoff under the run/package directory, then returns only a compact
  status.
- Split ExpManager work into atomic phases: package/runner preparation, launch,
  progress check, metric extraction, and ExpRecord update. For multi-phase or
  long-running work, ExpManager must update `expmanager_checkpoint.md` before
  moving to the next major phase. If context grows too large or compaction risk
  appears, ExpManager should checkpoint and exit cleanly; the controller should
  spawn a fresh ExpManager continuation from the checkpoint instead of waiting
  for the old chat to fail.
- Controller waits on long-running or evidence-heavy subagent tasks with
  bounded soft timeouts. A `wait_agent` timeout means only that chat has not
  returned yet; it is not evidence of failure, completion, or abandonment.
  In particular, do not duplicate the query merely because the chat wait timed
  out.
  Before fallback, duplicate dispatch, or close, inspect the subagent's
  status/report files, expected outputs, process/file freshness, and any
  run-local checkpoint. If these show progress or a plausible in-flight phase,
  leave the subagent open and report that it is still working. Close or
  supersede only after capturing `DONE`, `DONE_WITH_CONCERNS`,
  `NEEDS_CONTEXT`, `BLOCKED`, an explicit user cancellation, or a checked
  workflow fault such as no status/evidence plus no process/file activity after
  a grace check. If an urgent user answer is needed, the controller may do a
  read-only status peek, but must not terminate the original subagent merely
  because the peek finished first.
- After external model review text is pasted, ExternalReviewManager archives
  the raw text first. LongTimeMemoryManager may update memory only after
  reading the raw archive entry, not merely a summary.
- After Codex subagent/workflow configuration changes, run or consider a
  WorkflowAuditor read-only consistency check when the change is broad,
  risky, or affects multiple protocol files. For narrow edits, the controller
  may validate directly and report that no audit subagent was needed.

Before the final response, report whether memory was updated, which subagents
were used, and whether any subagents were left open intentionally under the
low-churn lifetime policy.

## Cross-Validation Evidence Rule

External model reviews must be archived raw before they are interpreted.
ExternalReviewManager may summarize and index a pasted Claude, GPT-5.5 Pro, or
Gemini reply, but that summary is only a pointer. LongTimeMemoryManager must
read the referenced raw archive text before recommending or applying memory
updates from outside advice. The main controller decides whether the advice is
accepted, rejected, deferred, or used for execution.

If the raw external text is missing, do not treat the subagent summary as
authoritative evidence. Ask for the raw text or mark the memory/evidence state
as incomplete.

## Memory Shape

Root `memory/` stays compact and current:

- `memory/CURRENT_WORK.md`: current objective, next actions, and active
  pointers.
- `memory/ALGORITHM_PRINCIPLES.md`: current research contract.
- `memory/IMPLEMENTATION_PLAN.md`: staged plan ledger.
- `memory/ExpRecord.md`: factual current experiment dashboard.

Full historical records belong under `memory/LTM/`.

Do not reintroduce legacy attention-pointer semantics. Do not edit `.claude/`
or Claude-specific files for Codex-only workflow changes.
