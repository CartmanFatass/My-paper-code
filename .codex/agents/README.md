# Codex Project Agents

This directory contains HMASD project-local Codex custom agents. It is separate
from `.claude/`.

This README is project documentation, not official Codex runtime config and not
an automatic first-read file. Use it only when editing or auditing subagent
configuration, dispatch templates, role boundaries, or workflow rules. The
runtime sources are `.codex/config.toml` and `.codex/agents/*.toml`; the
project-level instruction entry point is root `AGENTS.md`.

Official Codex runtime configuration lives in `.codex/config.toml` and
`.codex/agents/*.toml`. There is intentionally no YAML project manifest
fallback: if a custom agent is not surfaced by Codex, delegation must stop until
the official config is loaded or repaired.

The current HMASD runtime uses the documented v1 Codex subagent/custom-agent
path: `.codex/config.toml` enables `multi_agent` and sets
`multi_agent_v2 = false`. Custom agents live in standalone `.codex/agents/*.toml`
files and are registered explicitly in `.codex/config.toml` with
`[agents."<name>"].config_file` entries for current runtime compatibility. Do
not restore the retired YAML manifest path. `.codex/config.toml` explicitly
records the documented `[agents]` defaults: `max_threads = 6`, `max_depth = 1`,
and `job_max_runtime_seconds = 1800`.

For subagent/workflow-rule changes, consult
`docs/subagents/hmasd-subagent-workflow-reference.md` as an exploratory living
reference for Superpowers-style subagent techniques such as status control,
file ownership, file handoffs, review packages, and parallel waves. It is not
an active skill, not a requirement to run Superpowers, and is lower priority
than the latest user request, `AGENTS.md`, and official `.codex/` runtime
config.

When a Superpowers skill is active, Superpowers defines the process shape:
task briefs, report files, progress ledger, review packages, status handling,
and review loops. HMASD project rules only map those steps onto Codex custom
agents and project memory boundaries. Do not invent a parallel Codex workflow
that contradicts an active Superpowers skill.

Each official TOML custom agent includes:

- `model`.
- `model_reasoning_effort` for Codex config naming.
- `sandbox_mode`.
- `approval_policy`.
- `nickname_candidates`.
- required official fields: `name`, `description`, and
  `developer_instructions`.

## Controller Protocol

The active Codex session is the main controller. Do not create a separate
MainAgent subagent. The controller owns user communication, task understanding,
subagent delegation, result integration, user reporting, and subagent lifetime.

The controller should:

1. Clarify the user's goal, constraints, and completion criteria when unclear.
2. Decide what must be done locally versus delegated.
3. Delegate only bounded work with a clear owner and expected output.
4. Integrate subagent results before presenting conclusions to the user.
5. Proactively translate experiment state, result facts, plan transitions, and
   subagent reports into user-facing situation, meaning, next plan,
   recommendation, core MARL impact, and remaining gates or blockers.
6. Report what happened: subagents used, results, changed files, verification,
   unresolved risk, and next owner.
7. Manage subagent lifetime with low-churn cleanup: record status and ownership,
   leave completed agents open when useful, and close deliberately only under
   the lifecycle protocol below.

Memory delegation is not governance delegation. The controller may outsource
memory maintenance to TerraLongTimeMemoryManager, but must not outsource user intent
understanding, algorithm discussion, code/execution decisions, subagent
coordination, or the final explanation to the user.

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

## Spawn Rules

Official Codex custom agents are standalone TOML files under `.codex/agents/`.
`.codex/config.toml` registers those files with explicit `config_file` entries.
Codex loads them for trusted projects, usually after a new Codex session or app
restart. If the custom agent name is surfaced by `spawn_agent`, use that custom
agent by name.

Do not repair a missing custom role by spawning built-in agents or by copying
role settings into prompts. Keep `.codex/config.toml` on the stable
`multi_agent` path, verify each role TOML and its `config_file` registration,
then trust/restart the project so Codex reloads `.codex/agents/*.toml`.

Do not spawn built-in `default`, `worker`, or `explorer` as a project-role
fallback. A fallback hides whether the official TOML profile loaded, duplicates
model settings in the prompt, and makes lifecycle and authority boundaries
unclear.

If a required custom agent name is not available, report that the project
subagent config is not loaded. The likely fixes are: trust the project, start a
new Codex session, restart the app or IDE extension, or repair
`.codex/config.toml` / the role TOML file.

Codex `spawn_agent` inherits the parent thread model when runtime fields are
omitted. For this project, do not rely on inherited defaults: every project
agent must carry explicit `model`, `model_reasoning_effort`, sandbox,
approval, service tier when supported, nicknames, and developer instructions in
its TOML file.

Runtime names state their model family directly: every `Luna*` profile uses
`gpt-5.6-luna`, every `Terra*` profile uses `gpt-5.6-terra`, and every `Sol*`
profile uses `gpt-5.6-sol`. `SparkExplicitSimplePatcher` is the sole legacy
exception on `gpt-5.3-codex-spark`; it is opt-in only, never an automatic
fallback.

Routing follows those names. `LunaSimplePatcher` is the default for trivial,
single-file mechanical work. `TerraImplementer` is for bounded
medium-complexity, multi-file non-core work, not default simple work. Sol roles
own core, high-risk, or final-review work. `SparkExplicitSimplePatcher` may run
only when the dispatch contains the literal line `Legacy Spark opt-in:
explicitly requested`. Do not silently substitute tiers, and do not use
`max`/`ultra` tiers by default.

Quick routing:

- Simple bounded work -> `LunaCodebaseScout`, `LunaSimplePatcher`, or
  `LunaTestRunner`.
- Medium-complexity non-core multi-file work -> `TerraImplementer`.
- Core algorithm or quality-critical review -> `SolPlanImplementer`,
  `SolPlanImplementerFrontier`, `SolImplementationReviewer`, or
  `SolImplementationReviewerFrontier` according to risk.
- Legacy Spark -> `SparkExplicitSimplePatcher` only with the literal opt-in
  line above.

For `SolPlanImplementer`, the official TOML uses `service_tier = "fast"` because
the Codex config reference says `fast` maps to the priority request tier.
SolPlanImplementer intentionally uses `model_reasoning_effort = "high"` for
accepted-plan core implementation. Use `SolPlanImplementerFrontier`
(`gpt-5.6-sol`, `model_reasoning_effort = "xhigh"`) only for rare bounded core
tasks whose implementation brief explicitly requires architecture or algorithm
judgment while editing.

Reviewer cost control uses explicit model-tier roles instead of reducing review
frequency. Use `TerraFastReviewer` (`gpt-5.6-terra`, medium) for small isolated
mechanical diffs, `SolImplementationReviewer` (`gpt-5.6-sol`, high) for
standard multi-file, judgment-heavy, or debugging-oriented task reviews, and
`SolImplementationReviewerFrontier` (`gpt-5.6-sol`, xhigh) for architecture,
high-risk, concurrency, shared-state, API/data-contract, and final whole-branch
reviews. Each reviewer role has an explicit `model` and
`model_reasoning_effort`; do not depend on inherited runtime defaults.

`TerraExpManager` uses `gpt-5.6-terra` with medium reasoning for factual
process/log checks, bounded CSV extracts, package handoffs, and `ExpRecord.md`
updates. `TerraResultAnalyst` uses `gpt-5.6-terra` with high reasoning for
bounded metric/gate extraction from existing artifacts. `TerraLongTimeMemoryManager`
uses `gpt-5.6-terra` with high reasoning for memory-only work.
`SolWorkflowAuditor` uses `gpt-5.6-sol` with high reasoning and a read-only
sandbox for subagent/workflow consistency checks. These assignments do not
relax file-based status or bounded-context requirements.

## Lifecycle Protocol

There is no separate project subagent that manages other subagents. The main
Codex controller owns subagent lifecycle.

Official Codex may orchestrate waiting, closing, and concurrency-limit cleanup
in some workflows. Do not fight that with high-frequency manual close/open
cycles. Treat `close_agent` as a deliberate cleanup tool, not as a mandatory
post-result reflex.

For every spawned project subagent:

1. Spawn the official custom agent by name. If the name is unavailable, stop
   delegation and surface the config-loading problem to the user.
2. Record the returned agent id, nickname, profile, task, status, and lifetime
   decision in the working notes for the current turn.
3. Wait only when the result is needed for the next controller step.
4. Capture the final result or handoff and integrate any file changes.
5. Leave completed agents open when a follow-up is plausible, when the wave is
   still being integrated, or when concurrency pressure is low. Codex can
   self-clean when the concurrency limit is reached.
6. Call `close_agent` only for explicit cancellation, superseded work, stale or
   faulty state, scarce-concurrency cleanup, or a workflow boundary that needs a
   clean slate.
7. Before final response, report whether any agents were left open
   intentionally.

If a subagent is blocked, interrupted, or superseded, record the blocker and
next owner first. Close it only when retaining it is not useful for follow-up or
when it would consume needed concurrency.

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
return the paths. A `BLOCKED` result must include the exact blocker, files or
commands involved, and what must change before retrying.

## Mandatory Dispatch Brief Gate

No project subagent may be spawned until the controller has created or
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

If the controller cannot state these fields, it must not spawn the subagent. It
must either do the work locally, write the missing brief/package first, split
the task, inspect the required files, or ask the user for the missing decision.
Do not rely on a subagent to infer ownership boundaries or completion criteria
from broad chat context.

## Runtime Output Contract

The controller must treat log and artifact placement as part of subagent
ownership. Any dispatch that may run commands, create packages, write
transcripts, or produce experiment artifacts must name the runtime output root
and whether new directories may be created.

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

## Template References

For any non-trivial subagent handoff, prefer file templates under
`.codex/agents/templates/`. The controller gives workers a task brief path and
requires a report path. TerraExpManager additionally writes an
`expmanager_checkpoint.md` before long progress/result checks so controller
soft timeouts can distinguish in-flight work from workflow faults.

Current handoff templates:

- `.codex/agents/templates/subagent-task-brief.md`
- `.codex/agents/templates/subagent-report.md`
- `.codex/agents/templates/expmanager-checkpoint.md`

## No-Blind-Retry Rule

If a subagent returns `BLOCKED` or `NEEDS_CONTEXT`, the controller must not send
the same prompt back to the same role with the same context and expect a better
result. The next action must change at least one of:

- provide the missing file, command output, threshold, or decision;
- split the task into a smaller brief;
- change the owner to a more suitable role;
- escalate to a stronger model/tier when the task is genuinely harder;
- inspect status/checkpoint files before resuming long-running experiment work;
- revise or abandon the plan;
- ask the user for the blocking decision.

For long-running experiment work, prefer checkpoint-and-resume through files
over chat-heavy retries.

## Workflow-Level Authorization And Throttling

Codex only spawns subagents when the user explicitly asks for subagents,
delegation, or parallel agent work. In this project, a user-approved subagent
workflow can be a standing explicit authorization for routine fixed hooks inside
that workflow.

When the user explicitly authorizes a plan execution, experiment workflow,
external review archive workflow, memory synchronization workflow, or workflow
configuration audit to use the project subagent system, that authorization
covers the fixed subagent hooks required by that workflow. The controller may
spawn the routine LTM, TerraExpManager, TerraResultAnalyst, or TerraExternalReviewManager
handoff without asking again at every hook, or a SolWorkflowAuditor check inside
an authorized workflow-configuration audit, provided the work stays inside the
authorized workflow and the selected official custom agent boundary.

This automation does not transfer governance. The controller still owns user
intent, code direction, algorithm discussion, experiment interpretation,
external-advice disposition, git boundaries, integration, and final explanation.

Throttle automatic hooks:

- TerraLongTimeMemoryManager: batch memory impact at plan/code/result/external-review
  boundaries. Prefer one sync per implementation wave or completed turn; do not
  run it after every small edit.
- TerraExpManager: use for meaningful experiment launches, packages, commands,
  factual log/result records, and `memory/ExpRecord.md` updates. Do not invoke
  it for ordinary implementation edits. Experiment status/progress queries are
  TerraExpManager-owned: process state, log freshness, latest update/eval rows,
  error scans, key metric extracts, and factual `memory/ExpRecord.md` updates.
  The controller presents TerraExpManager's concise summary to the user and only
  adds controller-level interpretation when needed.
  When TerraExpManager generates or verifies facts that change experiment state,
  TerraExpManager updates the factual portions of `memory/ExpRecord.md` by default.
  The controller should not make the handoff read-only unless the request is
  explicitly a dry-run/status-only probe with no persistent record. If a
  read-only probe becomes record-worthy, the controller must either issue a
  follow-up TerraExpManager record-update task or state why it is using a direct
  fallback.
  TerraExpManager dispatches must name the run/log root. New runs should default to
  `logs/<experiment-id-or-run-id>/...`; existing `logs_*` roots are acceptable
  only when the dispatch names them. TerraExpManager must not create loose
  root-level `.log`, `.out`, `.err`, CSV, or JSON runtime files.
- TerraResultAnalyst: use when existing experiment artifacts need metric-heavy
  extraction, threshold/gate tables, anomaly extracts, or typical-step
  comparisons. It writes run-local extract files when evidence is large, but it
  does not launch runs, manage processes, package experiments, update
  `memory/ExpRecord.md` by default, or decide scientific acceptance.
- Non-core but time-consuming experiment operations are Terra operations work,
  not controller busywork. Running audit/eval scripts, watching quiet background
  jobs, reading process state, and collecting operational CSV/log outputs
  should go to `TerraExpManager` when available. Metric-heavy gate tables from
  already-written artifacts should go to `TerraResultAnalyst`. Mechanical edits to
  experiment runners, packaging scripts, and audit-output fields should go to
  `TerraImplementer` when they have a bounded brief and do not touch core
  algorithm, reward, training-loop, or checkpoint semantics.
- TerraExternalReviewManager: use when raw outside-model text is pasted or when
  inbox/archive/index handoff files are needed. It preserves evidence and
  prepares handoffs; it does not decide whether advice is accepted.
- SolWorkflowAuditor: use for read-only consistency checks after subagent/workflow
  config changes, before relying on a complex custom-agent setup, or when role
  boundaries/model settings may have drifted. It reports findings only; the
  controller applies any edits.
- Implementation review: every subagent-driven implementation task receives a
  task review, final whole-branch review remains required, and accepted findings
  go through fix -> re-review. Do not reduce review frequency to save cost;
  select `TerraFastReviewer`, `SolImplementationReviewer`, or
  `SolImplementationReviewerFrontier` by task complexity and risk.
- Git and publish work: keep controller-owned by default. Batch status/stage/
  commit/push/PR work at explicit user request or branch finalization; do not
  create high-frequency git subagents for routine per-task commits.

If an automatic hook would launch a long-running process, spend external money,
touch remote systems, publish, push, or exceed the authorized scope, ask the
user first.

## Implementation Routing

Classify implementation tasks before dispatch. When uncertain, treat the task
as core.

Core, ambiguous, or high-risk code work is controller-owned by default when it
is serial and there is no clear parallelism, isolation, or review-throughput
benefit. Use `SolPlanImplementer` when an accepted plan or controller-written task
brief defines a concrete work package whose handoff is worth the communication
cost:
algorithm mechanisms, training loops, reward and intrinsic-reward paths,
model/policy architecture, optimizer/loss/advantage/value logic, collector
semantics, environment dynamics, credit assignment, team-intent and q_A/q_D
logic, transition/effect discovery targets, checkpoint semantics, and shared
config flags that change algorithm behavior. Files such as
`ha_ctse_process/standalone_agent.py`, `ha_ctse_process/train.py`, and core
modules under `ha_ctse_process/` are core unless the controller explicitly
scopes a purely mechanical edit.

Use `SolPlanImplementerFrontier` only when the controller has a concrete xhigh work
package and can state why normal high-reasoning implementation is insufficient:
unresolved architecture tradeoffs inside the implementation, risky algorithm
semantics that must be reasoned through while editing, or a high-impact change
where the implementation itself is part of the design proof. Open-ended
strategy and final scientific interpretation stay with the main controller.

Use `LunaSimplePatcher` by default for trivial single-file mechanical work. Use
`TerraImplementer` for bounded medium-complexity, multi-file non-core work from
an accepted plan or controller-written task brief: coordinated experiment
runner or packaging scripts, dist manifests with their consumers, specified
cross-file metric propagation, documentation tied to a configuration change,
focused non-core tests, and wrapper/config text changes whose effects are
explicit and isolated. `SparkExplicitSimplePatcher` is a legacy explicit-only
exception, not a default implementation tier.

Do not ask the user a vague "should I use an implementer?" question. If the
controller wants to use `SolPlanImplementer` or `SolPlanImplementerFrontier` for core
work, first present the concrete package: scope, owned files, forbidden files,
responsibilities, why a subagent helps, model/reasoning tier, and verification
gates. If that package is not explicit, keep the core implementation in the
controller session. For non-core work inside an already authorized subagent
workflow, route trivial single-file work to `LunaSimplePatcher` and bounded
medium-complexity multi-file work to `TerraImplementer` without escalating to a
Sol implementer. Only use `SparkExplicitSimplePatcher` when the brief contains
its literal legacy opt-in line.

Time cost alone does not make non-core experiment work controller-owned. If a
task is mostly running scripts, monitoring logs/processes, or collecting
operational CSV/log facts, delegate it to `TerraExpManager` when custom agents are
available. If it is a metric-heavy gate read from already-written artifacts,
use `TerraResultAnalyst`. If it is a bounded medium-complexity multi-file
script/metric-field change, use `TerraImplementer`. Keep the main controller
focused on deciding what the facts mean and what to do next.

Use `LunaSimplePatcher` by default for trivial single-file mechanical fixes.
Use `SparkExplicitSimplePatcher` only when the dispatch includes `Legacy Spark
opt-in: explicitly requested`; without that exact line it must return
`NEEDS_CONTEXT`. Use `TerraExpManager` for experiment operations and factual
records, not general code implementation. A Spark task that expands into core
code or algorithm judgment must stop and escalate to the controller or
`SolPlanImplementer`.

Implementation subagents should not receive open-ended prose prompts. For plan
work, dispatch from an accepted plan, a task brief path, or an explicit
controller-written brief. The dispatch must include requirements source, owned
files/directories, forbidden files, report path, required checks, commit
policy, and core/non-core tier.

Use `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md` for
standard handoff prompts and return formats.

## TerraExpManager And TerraResultAnalyst Workflow

`TerraExpManager` owns experiment operations and factual run-state records.
`TerraResultAnalyst` owns metric-heavy reads from artifacts that already exist. The
controller owns the scientific interpretation and next decision.

Default sequence:

1. TerraExpManager prepares the runner/package/command, launches or checks the run,
   writes status files and transcripts, and updates factual `memory/ExpRecord.md`
   fields when experiment state changes.
2. TerraResultAnalyst reads existing artifacts such as CSVs, eval rows,
   `runner_status.txt`, `runner_output.log`, manifests, checkpoints, and
   controller-provided gate definitions. It writes large evidence to run-local
   files such as `metric_extract.md`, `gate_read.md`, or `error_extract.md`.
3. The controller integrates TerraExpManager's run-state facts and TerraResultAnalyst's
   metric/gate evidence, then decides pass/fail/defer, acceptance, reward
   gating, and next action.
4. TerraExpManager records any follow-up factual experiment status only when the
   controller routes that update. TerraLongTimeMemoryManager syncs accepted
   conclusions into compact memory or LTM when project memory should change.

TerraExpManager and TerraResultAnalyst can run in the same evidence wave only when
TerraResultAnalyst reads already-written artifacts and neither agent writes the same
run directory, package path, source file, or `memory/ExpRecord.md` row. If
TerraExpManager is still creating artifacts, launching the run, or updating the same
experiment record, run the phases sequentially.

## Pre-Flight Review

Before spawning a wave, the controller builds a compact pre-flight table:

| Task | Agent | Requirements | Owns | Must not touch | Output | Checks | Dependencies | Conflict risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Do not launch the wave until predictable conflicts are resolved: overlapping
write scope, shared run directories, shared package paths, shared
`memory/ExpRecord.md` rows, shared processes, incompatible tests, missing
thresholds, missing task briefs, or unresolved architecture decisions.

When conflicts require user input, batch those questions before dispatch.

## Parallel Execution

Use parallel waves when an accepted plan or authorized workflow has independent
tasks. The controller must build a wave table before spawning:

- task id and short goal,
- task brief path and report path,
- owned files or directories,
- files that must not be touched,
- dependency or blocker status,
- required test or report path,
- assigned custom agent name, TOML profile path, and implementer tier.

Tasks can run in the same wave only when they have disjoint write scopes, no
sequential dependency, and no shared mutable runtime such as the same training
process, package path, or experiment record. Dispatch all agents in a wave in
the same response so they run concurrently.

Superpowers gets higher concurrency by dispatching the full clean wave at once,
not by adding one agent per turn. If the plan has cleanly independent domains,
dispatch the full wave up to the available runtime concurrency limit. Use
smaller waves only when scopes are fuzzy, tests share mutable state, or
integration risk is high.

Default to controller-local execution for serial core tasks. Mix
`SolPlanImplementer`, `SolPlanImplementerFrontier`, and `TerraImplementer` according
to task tier. Sidecar
read-only or evidence tasks can also run in the same wave when they do not
share state: `LunaCodebaseScout` for mapping, `TerraResultAnalyst` for existing
artifact metrics, `TerraExpManager` for process/run-state facts, `LunaTestRunner` for
focused verification, and `SolWorkflowAuditor` for config drift. Do not run two
agents that both write the same memory row, run directory, package path, or
source file.

After dispatch, wait sparingly. Continue non-overlapping controller work
instead of polling by reflex. Wait only when the next critical-path action needs
the subagent result.

Do not parallelize tasks touching the same files, training/reward/config
plumbing, shared experiment scripts, or unresolved architecture decisions. Put
those behind the main controller or run them serially.

After a wave returns, the controller integrates reports, checks for file
conflicts, runs the union of required tests, updates the progress ledger,
records subagent lifetime decisions, closes only when low-churn cleanup is
useful, and dispatches the required task reviewers with the
appropriate reviewer tier. Independent task reviews may run in parallel when
their packages and scopes do not overlap.

## Progress Ledger

For superpowers execution-plan work, the controller owns
`.superpowers/sdd/progress.md`. It is a compact execution ledger, not long-term
memory and not an LTM-owned file.

Before dispatching any wave, read the ledger if it exists. Treat tasks marked
complete there as done and do not re-dispatch them. If the ledger is missing,
reconstruct status from task reports, `git log`, and current file state before
starting old tasks again.

For each dispatched task, pass a task brief path and a report path. The task
brief is the implementation worker's source of requirements; the report file is
where the worker writes the full result. The controller should ask the worker to
return only a short status with status, commits, test summary, scope
confirmation, concerns, and report path.

After a task or wave is integrated and tested, update the ledger with task id,
status, commits or file changes, report path, tests, integration notes, and
subagent close state. After compaction or resume, trust the ledger plus git/file
state over chat memory when deciding what has already run.

## Review Packages And Batch Fixes

For every task review and final whole-branch review, prepare a review package
file or compact review package entry before spawning the selected reviewer
profile. Trivial mechanical diffs may use a short package; the review is not
skipped. The reviewer should read the package, referenced briefs/reports, and
prepared diff package rather than asking the controller to paste large diffs
into chat.

Minimum review package fields:

- review goal and risk level;
- reviewer profile/model tier selected and why;
- user request or accepted plan path;
- task brief and report paths;
- changed files and ownership scope;
- bounded diff package or diff excerpt prepared by the controller;
- commands/tests run;
- known concerns and residual risk;
- exact review questions;
- forbidden scope.

The selected reviewer reads the prepared diff exactly once, stays read-only,
does not rerun `git diff`, `git show`, or `git log`, and does not broaden to the
whole codebase beyond the package scope. Its report must include both
`Spec Compliance` and `Code Quality` verdicts.

If review finds multiple issues, the controller decides which findings are
accepted and sends one batch-fix brief to one suitable implementer. Do not
spawn one fixer per finding. After fixes, run the focused checks and re-review
the affected package for accepted fixes.

## Fixed Workflow Hooks

The controller must check subagent and memory impact at common workflow
boundaries. A hook means "make the routing decision deliberately"; it does not
mean spawning a subagent when the work has no persistent state impact.

- Plan accepted, changed, completed, or abandoned: sync
  `memory/IMPLEMENTATION_PLAN.md`, `memory/CURRENT_WORK.md`, and relevant LTM
  archive entries directly or through TerraLongTimeMemoryManager.
- Superpowers execution-plan implementation: classify each task first. Keep
  serial core, ambiguous, or high-risk code in the controller session by
  default unless the plan provides a concrete `SolPlanImplementer` or
  `SolPlanImplementerFrontier` package and the user has authorized that handoff.
  Use `LunaSimplePatcher` by default for trivial single-file mechanical
  implementation and use `TerraImplementer` for bounded medium-complexity,
  multi-file non-core implementation inside an authorized workflow.
  `SparkExplicitSimplePatcher` is available only when the dispatch contains its
  literal legacy opt-in phrase. Group independent
  tasks into Superpowers-style parallel waves with disjoint file ownership and
  dispatch each whole clean wave in the same response. Read
  `.superpowers/sdd/progress.md` before dispatch. Give each worker a task brief
  path and report path, and require short-status chat output plus a full report
  file. Prefer file paths over pasted plan history in every dispatch.
  Run the required task reviewers after a wave, using the reviewer tier that
  matches each task's complexity and risk. Run `SolImplementationReviewerFrontier`
  for final whole-branch review. Do not route default simple work to Terra or
  Spark. If a task requires architecture or algorithm
  strategy beyond the accepted plan, keep it with the main controller or create
  a new explicit `SolPlanImplementerFrontier` work package before delegation.
- Code changes verified: ask TerraLongTimeMemoryManager to sync memory if project
  direction, algorithm behavior, experiment workflow, known risks, or next
  actions changed. For trivial edits, record that no memory update is needed.
- Meaningful experiment launch: ask TerraExpManager for the factual record, command,
  package, and handoff. Use TerraLongTimeMemoryManager only if the launch changes
  current objective, plan stage, principle state, or archive-worthy context.
- Experiment handoff ready: the controller must brief the user explicitly,
  not only update `memory/ExpRecord.md`. The brief must include the experiment
  name(s), round/gate being answered, reason for running, exact command or
  script, key flags/parameters, metrics/log fields to monitor, pass/fail or
  next-decision criteria, and the follow-up action for likely outcomes.
- Experiment logs/results reviewed: TerraExpManager records factual status in
  `memory/ExpRecord.md`; the controller owns the substantive interpretation;
  the controller gives the user a situation/meaning/next-plan/recommendation
  readout; TerraLongTimeMemoryManager syncs compact memory and LTM archives from the
  accepted conclusion.
- Metric-heavy result reads: TerraResultAnalyst produces bounded metric/gate tables,
  typical-step comparisons, and run-local extracts from existing artifacts.
  TerraExpManager remains responsible for process/run-state facts and factual
  `memory/ExpRecord.md` updates; the controller remains responsible for
  scientific interpretation and next actions.
- Experiment progress requested: route the factual inspection to TerraExpManager
  when custom agents are available. The controller should avoid duplicating the
  raw querying work; it should relay TerraExpManager's summary, then separately state
  any interpretation, risks, or next action, including whether the correct move
  is wait, inspect another artifact, or change the plan.
- Experiment result interpretation uses a two-layer record. TerraExpManager owns
  factual fields: run state, commands, files inspected, latest update/eval
  rows, metric tables, failures, and anomalies. The controller owns scientific
  interpretation, accepted/rejected/deferred disposition, and next action. If
  controller interpretation should persist in `ExpRecord.md`, add it only as a
  clearly labeled decision/interpretation field after TerraExpManager's factual
  update, or ask TerraLongTimeMemoryManager to sync the accepted conclusion. The
  user-facing readout must say whether the result permits any reward or core
  MARL change, or keeps those changes blocked.
- Non-core experiment execution requested: prefer Terra operations delegation
  even when the task is small. Sequential audit/eval runs, quiet-console monitoring,
  and command-output capture belong to `TerraExpManager`; metric-heavy gate tables
  from already-written artifacts belong to `TerraResultAnalyst`. If the controller
  needs an immediate blocking fact that is faster to read directly, it may do
  so. If direct fallback is used because TerraExpManager or TerraResultAnalyst is
  unavailable, blocked, or failed, state that explicitly in the user-facing
  report.
- Long-running or quiet-console TerraExpManager tasks must use a file-based status
  contract instead of relying on subagent chat. Before each command starts,
  TerraExpManager creates or updates a status file under the assigned run/log root,
  normally `runner_status.txt`, with command, start time, expected output path,
  current phase, and PID when available. It writes stdout/stderr to
  `runner_output.log` or an equivalent transcript under that same root when
  practical, and updates the status file after each command completes or fails.
  Sequential batches are split into atomic phases with a status update before
  the next command starts.
- TerraExpManager tasks must use a context-budget contract. The controller should
  ask for bounded reads, metric tables, targeted error extracts, and file paths
  rather than pasted full logs, full CSVs, traceback clusters, or long command
  transcripts. TerraExpManager writes large evidence to files such as
  `expmanager_checkpoint.md`, `metric_extract.md`, `error_extract.md`, or a
  package handoff under the run/package directory, then returns only a compact
  status.
- Split TerraExpManager work into atomic phases: package/runner preparation, launch,
  progress check, metric extraction, and ExpRecord update. For multi-phase or
  long-running work, TerraExpManager updates `expmanager_checkpoint.md` before
  moving to the next major phase. If context grows too large or compaction risk
  appears, TerraExpManager checkpoints and exits cleanly; the controller spawns a
  fresh TerraExpManager continuation from the checkpoint instead of waiting for the
  old chat to fail.
- Controller waits on long-running or evidence-heavy subagent tasks with
  bounded soft timeouts. A `wait_agent` timeout means only that chat has not
  returned yet; it is not evidence of failure, completion, or abandonment.
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
- External review pasted: TerraExternalReviewManager archives raw text first;
  TerraLongTimeMemoryManager may update memory only after reading the raw archive
  entry.
- Subagent/workflow config changed: run or consider a SolWorkflowAuditor read-only
  consistency check when the change touches multiple protocol files, model
  settings, role boundaries, or official custom-agent runtime behavior. For
  narrow edits, the controller may validate directly and report that no audit
  subagent was needed.

Before final response, report whether memory was updated, which subagents were
used, and whether any subagents were intentionally left open under the
low-churn lifetime policy.

## Memory And Handoffs

Use `memory/CURRENT_WORK.md`, `memory/ALGORITHM_PRINCIPLES.md`,
`memory/IMPLEMENTATION_PLAN.md`, and `memory/ExpRecord.md` as compact current
memory. Use `memory/LTM/` only for historical archives or when compact memory
points there.

TerraExpManager records experiment facts, scripts, packages, commands, logs, and
operational conclusions. `memory/ExpRecord.md` factual updates are TerraExpManager's
default responsibility whenever the experiment state changes. TerraLongTimeMemoryManager
may assess memory impact and maintain records from those facts, but the main
controller owns substantive experiment interpretation and execution decisions.

TerraResultAnalyst extracts metrics and gate evidence from existing run artifacts.
It should write large evidence to run-local files such as `metric_extract.md`
or `gate_read.md` and return compact summaries. It does not update
`memory/ExpRecord.md` by default; when extracted facts should persist, the
controller routes the factual record update to TerraExpManager or asks
TerraLongTimeMemoryManager to sync accepted conclusions.

SolWorkflowAuditor audits Codex workflow consistency only. It is read-only and
does not own controller behavior, lifecycle management, memory updates, or
subagent spawning.

TerraExternalReviewManager records copy-paste Claude, GPT-5.5 Pro, and Gemini
review rounds. It must preserve raw pasted model text in
`memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` before summarizing.
TerraLongTimeMemoryManager may assess and apply memory updates from that advice,
but the main controller owns whether the advice is accepted, rejected,
deferred, or used for execution.

TerraExternalReviewManager summaries and handoffs are indexes, not evidence.
TerraLongTimeMemoryManager must read the referenced raw archive text before making a
memory update or recommendation from outside advice. If raw text is missing,
ask for recovery or mark the memory update as incomplete rather than promoting
a summary.

Do not reintroduce legacy attention-pointer semantics. Do not edit `.claude/`
or Claude-specific files for Codex-only workflow changes.
