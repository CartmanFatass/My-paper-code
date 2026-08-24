# OMP Autonomous Multi-Direction Research Workflow Concept

## Status

The role-scoped per-agent-type Advisor design below is approved as the target.
The repository still contains the previously implemented routed headless
Advisor as a provisional baseline until the detailed plan's clean cutover.
The remainder of the workflow is an implementation-ready design, not executable
state or authorization to modify HMASD or Agentify.

Detailed implementation contract:
`docs/plans/2026-08-24-omp-autonomous-multidirection-research-implementation.md`.
It resolves schemas, interfaces, phases, verification, rollout, and deletion
conditions.

## Role-scoped per-agent-type Advisors (approved target)

HMASD uses native continuous Advisors only for roles where early transcript-
delta correction is materially different from a later Reviewer:

```text
Root                         -> architecture / opencode-go/glm-5.3:high
hmasd-portfolio              -> science / openai-codex/gpt-5.6-sol:high
hmasd-em                     -> science / openai-codex/gpt-5.6-sol:high
hmasd-cm                     -> architecture + engineering / opencode-go/glm-5.3:high
hmasd-implementer            -> engineering / opencode-go/glm-5.3:high
hmasd-implementer-terra      -> engineering / opencode-go/glm-5.3:high
all other project agents     -> no Advisor
```

Root uses `advisor.enabled` and the default Advisor model role. Subagents use
`task.agentAdvisor[agentName]`; OMP resolves the choice when the child spawns
and persists it in `session_init`, including cold revival. `/agents` configures
future spawns by agent name, not an already-running Hub job by job ID. The
mapping is stable workflow configuration and is not toggled per ordinary task.

One `.omp/WATCHDOG.md` routes strictly by the primary role. No WATCHDOG roster
fixes a model, because a roster model would override the per-session Advisor
role. The Advisor continuously reviews transcript deltas but remains read-only
and advisory: it never approves, rejects, blocks, authorizes, gates, mutates,
runs tests, dispatches agents, or becomes a state authority. Root/user approval
boundaries remain authoritative.

Architecture checks control-plane simplicity, state authority, irreversible
effects, lifecycle, and recovery. Engineering checks batching, independent
parallelism, applicable C++ backends, complexity, memory, data movement, and
preservation of scientific, numerical, RNG, checkpoint, and required bit
identity. Science checks action/state growth, sparse-reward exploration,
explore/exploit balance, variable-agent robustness, variable skill-duration
k/t exploration catastrophe, discriminating experiments, grouped MARL, and
innovation not constrained by the current direction.

For research context, the science route may read `docs/new-libs` and
`/home/fires/projects/Inst-sci`. Inst-sci has been copied to that path and
recursively diff-verified against its source tree.

During the clean cutover, `.omp/WATCHDOG.md` and native Advisor configuration
replace `.omp/advisors/*`, `scripts/run_hmasd_advisor.py`, and its tests in one
boundary. The retired headless mechanism is not retained as a second Reviewer.

## Decision

HMASD will use one user-facing Root OMP session with an autonomous nested agent
tree, durable research files, local run records, and read-only visualization.
The workflow optimizes for high automation and human traceability, not frequent
human approval.

The control plane remains deliberately small:

```text
research definitions and reproducibility  -> DVC-style files and dependencies
run observation                            -> MLflow-style local manifests/artifacts
ordinary asynchronous work                -> OMP task/hub + Prefect-style light state
irreversible webpage submission            -> Agentify at-most-once transaction ledger
```

HMASD does not currently need an Airflow/Temporal/Dagster-class orchestration
platform. Roles, tests, reviews, dashboards, manifests, and historical documents
provide capability or evidence; they do not acquire authority over ordinary
reversible work.

## First principles

1. Use files, ordinary functions, process exit codes, Git, OMP task agents, and
   human scientific judgment before adding control-plane machinery.
2. A new gate, state machine, role, lease, or background service must name a
   real observed failure that is irreversible, costly, or otherwise not handled
   by a simpler mechanism.
3. Tests provide information, not permission.
4. Review provides advice and evidence, not permission.
5. A dashboard is a view, not a state source.
6. A lease exists only for a real contested resource.
7. A role divides work; it does not reject user authorization.
8. Historical documents are provenance, not executable state.
9. Reversible operations default to direct execution and ordinary error
   handling. Irreversible external effects fail closed.
10. One fact has one authoritative source.
11. Every added mechanism must state when it can be removed.

Reference systems are used as design analogies, not dependencies:

- [DVC pipelines](https://dvc.org/doc/user-guide/pipelines/defining-pipelines)
  and [DVC experiments](https://dvc.org/doc/user-guide/experiment-management):
  explicit parameters, dependencies, outputs, and reproducibility without
  turning experiment state into an approval system.
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking): runs are observed
  through parameters, metrics, code versions, and artifacts; observation does
  not imply control.
- [Prefect flows](https://docs.prefect.io/v3/concepts/flows): wrap only work that
  genuinely needs asynchronous state, retry, recovery, or remote execution.
- [Airflow](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html):
  a central recurring-batch scheduler is not justified for the current dynamic
  research workload.
- [Temporal workflows](https://docs.temporal.io/workflows) and
  [activities](https://docs.temporal.io/activities): durable idempotency ideas
  are used only for irreversible external operations.
- [Dagster](https://docs.dagster.io/): a data-asset platform is unnecessary
  while asset lineage is not itself the product.

DVC, MLflow, Prefect, Airflow, Temporal, and Dagster are not introduced as
project dependencies by this concept.

## Automation and approval boundary

The user enters one Root OMP session. The workflow advances automatically until
it reaches a real approval or decision boundary.

Ordinary automatic work includes:

- Portfolio activation, reactivation, ranking, merging, parking, and closure of
  research directions;
- EM research, specialist dispatch, local synthesis, and external-review rounds;
- CM code scouting, implementation, review, verification, ordinary recovery,
  and OMP-branch integration;
- local diagnostics, small tests, documentation, directory maintenance, and
  ordinary Git operations on the dedicated OMP branch;
- low-cost local CPU result-bearing commands;
- Gemini and Pro scientific external review;
- Agentify session monitoring, raw archival, and handoff generation;
- conflict-free direction-worktree integration into the OMP branch.

The user is interrupted only for:

- a local result-bearing command estimated to exceed two hours after a
  performance-reasonableness review has been attempted;
- an operation that affects a non-OMP branch;
- a destructive or irreversible action outside prior authorization;
- a scientific conflict that cannot be resolved from registered evidence and
  project principles;
- recovery that has exhausted every safe, materially distinct route.

Formal/production labeling alone does not require approval. Worker count alone
also does not require approval. Memory overcommit is not approval-driven: unsafe
memory plans are mechanically refused and must be reduced, batched, or sharded.
GPU/cloud execution is out of current scope; SSH-managed local GPU runs remain a
future TODO.

## OMP-native topology

```text
Root main session                              depth 0
├── Portfolio                                  depth 1
│   ├── EM-<direction>                         depth 2
│   │   ├── research scout                     depth 3
│   │   ├── research innovator                 depth 3
│   │   ├── research critic                    depth 3
│   │   ├── principles analyst                 depth 3
│   │   ├── artifact writer                    depth 3
│   │   ├── code scout                         depth 3
│   │   ├── external Pro transport             depth 3
│   │   ├── external Gemini transport          depth 3
│   │   └── librarian                          depth 3
│   └── 2–8 active directions
├── CM-<direction>                              depth 1
│   ├── project/code scout                     depth 2
│   ├── implementer                            depth 2
│   ├── routine implementer                    depth 2
│   ├── reviewer                               depth 2
│   ├── verifier                               depth 2
│   ├── experiment operator                    depth 2
│   ├── research scout                         depth 2
│   └── librarian                              depth 2
└── Root-direct project agents, task, librarian
```

The full research path requires `task.maxRecursionDepth: 3`. The provisional
baseline uses depth 2 and is not sufficient.

All project agents are non-blocking and asynchronous. Specialists are leaves and
cannot spawn further agents. Root, Portfolio, EM, and CM are the only ordinary
spawn-capable layers. Workflow Recovery is Root-only.

### Root authority

Root may directly invoke every project agent. Normal routing through Portfolio,
EM, and CM is an efficiency convention, not a permission gate. Bundled `task`
is retained but may be invoked explicitly only by Root when no project-specific
role fits. Bundled `librarian` is available to Root, Portfolio, EM, and CM.

### Portfolio authority

Portfolio owns cross-direction selection, synthesis, resource attention, shared
scientific opportunities, and direction lifecycle. It may directly invoke:

- EM instances;
- all research specialists and artifact writers;
- external Pro/Gemini transports;
- code scout for cross-direction engineering visibility;
- librarian.

Portfolio does not directly implement code.

### EM authority

Each EM owns one bounded research direction. It may invoke research specialists,
artifact writer, code scout, external-review transports, and librarian. It may
request engineering through durable direction state and Root, but cannot invoke
CM or implementers directly.

### CM authority

Each CM owns one bounded engineering scope. It may invoke all engineering
specialists, Experiment Operator, research scout, and librarian. Scientific
ambiguity returns to Root/EM rather than being silently redefined by CM.

### Agent inventory

The project will expose exactly these 18 project agent types:

1. `hmasd-portfolio`
2. `hmasd-em`
3. `hmasd-cm`
4. `hmasd-project-scout`
5. `hmasd-code-scout`
6. `hmasd-implementer`
7. `hmasd-implementer-terra`
8. `hmasd-reviewer`
9. `hmasd-verifier`
10. `hmasd-experiment-operator`
11. `hmasd-workflow-recovery-manager`
12. `hmasd-external-pro-transport`
13. `hmasd-external-gemini-transport`
14. `hmasd-research-scout`
15. `hmasd-research-innovator`
16. `hmasd-research-critic`
17. `hmasd-research-principles-analyst`
18. `hmasd-research-artifact-writer`

The obsolete engineering `hmasd-cpm-agentify-transport` is removed. Existing
Pro research transport is cleanly renamed `hmasd-external-pro-transport`.
Both external transports support provider-specific submission modes and a
provider-independent MONITOR mode.

Bundled agents retained at project scope:

- `task`
- `librarian`

Bundled `scout`, `reviewer`, `sonic`, `designer`, and `security-reviewer` are
project-disabled after all callers use explicit project roles.

## Direction instance naming

Agent definitions are shared. A file is not generated for each direction.

```text
agent type:       hmasd-em
logical identity: EM-<direction>
OMP job name:     EM<Direction>

agent type:       hmasd-cm
logical identity: CM-<direction>
OMP job name:     CM<Direction>
```

OMP job names use stable CamelCase. Direction state uses the readable hyphenated
logical name. Portfolio registry owns the unique, stable direction abbreviation
and the mapping between both forms.

## Agent lifecycle and automatic continuation

Portfolio, EM, and CM are long-lived logical identities executed through bounded
turns:

```text
persistent session/transcript
+ bounded tick
+ idle/parked when waiting
+ parent message to revive
+ generation rotation at material boundaries
```

They are not permanent inference loops. A parked OMP agent does not wake on file
changes by itself; Root or its parent manager sends a Hub message when work is
newly actionable. This is automatic inside the Root control loop and does not
require user session management.

Lifecycle policy:

- prefer revival and reuse of the existing Portfolio/EM/CM session;
- rotate generation only after a material direction redefinition, state/context
  inconsistency, untrustworthy recovery, or context exhaustion risk;
- after OMP compaction, perform a light reconciliation of current state,
  active children, pending actions, and external/run references;
- continue the generation when reconciliation succeeds;
- create a new generation from durable state when it does not.

Concrete OMP handles are local runtime data under ignored
`.omp/runtime/*.json`. Git stores only logical identity, direction, generation,
and lifecycle. Moving machines reconstructs agents from durable project state.

Root uses project `autoResume` and a persistent Goal. The Goal means: continue
advancing until the workflow reaches IDLE, a user approval, an exhausted
blocker, or COMPLETE. OMP Todo is only the current tick's execution checklist;
it is not durable direction state.

Automatic continuation is event-driven through native OMP task completion, Hub
messages, process termination, file changes, and external-review/run completion.
There is no continuous model polling. When current open directions have no
work, Portfolio performs one bounded reassessment of the registered direction
pool. If nothing qualifies, it enters IDLE.

## Agent Hub observability

Within the Root session tree, Agent Hub provides:

- flat and parent/child tree views;
- running, idle, parked, and aborted state;
- resolved model, current activity, current tool, arguments, intent, retries,
  context, usage, and cost;
- parent/child lineage, output, patch, worktree, and branch metadata;
- focus on any nested agent's live transcript;
- steering running agents, prompting idle agents, and reviving parked agents;
- persisted nested lineage and transcript access after Root resume.

Agent Hub is the detailed agent inspection surface. The project Dashboard shows
only compact logical/runtime status and links or instructions for navigating to
the corresponding Agent Hub entry.

## Concurrency

OMP's total project task concurrency remains 32. Four slots are an advisory
control/recovery reserve implemented in Skills, not a lease system or mechanical
capacity gate. Ordinary work targets at most 28 active worker slots; urgent
control or recovery work may start and let ordinary work queue naturally.

- Portfolio dynamically chooses 2–8 active directions after mechanical
  eligibility filtering and scientific ranking.
- Each EM starts two specialists by default and may expand to four when the
  material question and current capacity justify it.
- Each CM starts two specialists by default and may expand to six when file
  ownership, interface contracts, and capacity allow safe parallelism.
- External monitoring uses 1–3 existing Transport instances, selected by the
  External Review Skill, and still counts toward the total OMP limit.

No new capacity scheduler or resource lease is introduced. Real resource
conflicts may justify a later narrow mechanism only after they are observed.

Portfolio may autonomously create, register, activate, park, merge, close, and
reactivate directions. Registered directions have no hard count limit. Every
merge/closure records a material scientific reason, inheritance relationship,
and reactivation condition in the authoritative Markdown/Git history.

Mechanical eligibility filters hard blockers, duplicate IDs, dependencies, and
resource impossibility. Portfolio performs the scientific ranking using
information value, scientific potential, shared benefit, evidence, and cost.

## Project skills and hard rules

Eight project Skills are loaded through agent frontmatter `autoloadSkills`:

1. `hmasd-root-control`
2. `hmasd-portfolio-control`
3. `hmasd-em-direction-cycle`
4. `hmasd-cm-engineering-cycle`
5. `hmasd-result-run`
6. `hmasd-scientific-external-review`
7. `hmasd-workflow-recovery`
8. `hmasd-git-integration`

Skills define role procedures, scientific methods, dispatch strategy,
performance expectations, escalation, recovery reasoning, and how to use
ordinary helpers. They do not implement locks, permission, process supervision,
or hidden state.

`.omp/RULES.md` contains only hard boundaries:

- high-cost user approval;
- non-OMP branch approval;
- external-send at-most-once;
- one Operator per exact result-bearing command;
- exact destructive targets and path ownership;
- no secret exposure;
- no silent change to scientific, numerical, RNG, checkpoint, or external-effect
  semantics;
- no role, test, review, dashboard, lease, or historical document may grant or
  deny ordinary authorized work.

## Result contracts

All agents return a common scheduling envelope plus a role-specific payload.

Common envelope:

```text
status: COMPLETED | PARTIAL | BLOCKED | FAILED
materiality: NONE | LOCAL | DIRECTION | PORTFOLIO | USER
summary
changed_paths
state_refs
artifact_refs
checkpoint_sha
decision_requests
next_action
```

Ordinary `event_id` is not used. External irreversible operations retain their
Agentify idempotency and operation IDs.

Role-specific schemas cover Portfolio, EM research, CM engineering,
implementation, review, verification, run, external transport, monitor, and
artifact writing. Exact field schemas belong in the later design document.

Only material direction, portfolio, user, blocker, or terminal transitions are
actively injected into Root/Portfolio context. Full outputs remain in agent
transcripts, artifacts, files, and Agent Hub.

## Scientific and workflow state

Scientific facts and workflow pointers have separate authorities.

### Portfolio

```text
docs/research/portfolio/
├── PORTFOLIO.md                 # authoritative cross-direction science
└── workflow/
    └── registry.json            # IDs, paths, lifecycle, active flags,
                                 # dependencies and current agent/round refs
```

`PORTFOLIO.md` owns scientific ranking, relationships, synthesis, and direction
selection reasoning. `registry.json` does not duplicate that science.

### Direction

```text
docs/research/candidates/<direction-id>/
├── DIRECTION.md                 # authoritative direction science
├── workflow/
│   ├── research/state.json      # EM single-writer workflow pointers
│   ├── engineering/state.json   # CM single-writer workflow pointers
│   └── external-review/index.json
├── results/
│   ├── <accepted-result>.md     # durable scientific conclusion
│   └── <accepted-result>.json   # small accepted metrics/provenance
└── other durable research artifacts
```

`DIRECTION.md` owns the scientific question, mechanisms, evidence interpretation,
critical unknowns, current conclusions, and open scientific work. Workflow JSON
contains only lifecycle, actionable state, blockers, current round, paths, SHAs,
agent references, run references, and next mechanical action.

Direction lifecycle and waiting conditions are orthogonal:

```text
lifecycle: REGISTERED | ACTIVE | PARKED | CLOSED
actionable: boolean
blockers: [...]
waiting_on: [...]
active_round: optional reference
```

Ordinary material changes do not create immutable event files. File changes
trigger automation; Git history provides traceability. There is no tracked
generated summary JSON and no ordinary event reducer.

Long-lived JSON formats use explicit `schema_version` and small registered
one-way migrations. This applies to portfolio registry, current workflow state,
run manifests, accepted metrics, and project handoffs—not to every research
Markdown change.

## Run records and accepted results

Each result-bearing train/evaluate/analyze command writes one local manifest:

```text
temp/directions/<direction-id>/exp/<run-id>/
├── manifest.json
├── stdout/stderr
├── checkpoints
├── metrics
└── other raw artifacts
```

The manifest is MLflow-like observation, not authority. It records command,
parameters, code SHA, environment, PID, output paths, metrics, timestamps, and
terminal state. It is not committed by default.

Accepted durable results promote only:

- a Markdown scientific conclusion;
- a small metrics/provenance JSON;
- relevant parameter, code SHA, and original run reference;
- no large raw artifact unless a later storage need justifies it.

No DVC or MLflow dependency is introduced now.

### High-cost CPU runs

The local automatic threshold is two hours estimated wall time.

```text
estimated <= 2h
  -> ordinary automatic execution

estimated > 2h
  -> mandatory attempt at performance-reasonableness review
  -> Root presents estimate, implementation evidence, and Reviewer advice
  -> user approves or rejects
```

The Reviewer attempt is fail-open: failure or unavailability is reported as an
evidence gap and cannot permanently prevent Root from asking the user.

Reviewer examines whether the estimate is avoidably inflated by:

- missing environment/sample batching;
- missing independent parallelism;
- poor worker/shard selection;
- failing to use an available C++ backend;
- leaving a suitable hot path in per-step Python instead of a C++ backend;
- avoidable algorithmic complexity or data movement;
- absent or inadequate benchmark/profile evidence.

Implementer instructions and CM Engineering Skill require batching, parallelism,
and applicable C++ backend consideration. Verifier produces benchmark/profile
evidence. Reviewer does not modify code and does not acquire approval authority.
Optimization must preserve scientific, numerical, RNG, checkpoint, and required
bit-identity semantics.

Memory plans above the safe local budget are mechanically refused rather than
sent for approval. Worker count alone does not trigger approval.

Experiment Operator owns exactly one command from duplicate-process check to
terminal state. It does not reinterpret science or start a successor.

## LSP and engineering evidence

The project enables task LSP and configures Pyright and clangd. Only Implementer
receives full native LSP.

Implementer contract when a server is available:

- exported-symbol changes require references before editing;
- cross-file rename uses LSP rename/rename_file;
- affected files receive LSP diagnostics after editing.

Reviewer receives no LSP. Its direct tools are read/grep/glob plus read-only Git
and existing-evidence query surfaces. It reads code/diff, code-scout mappings,
Verifier evidence, benchmarks, and profiles. It does not run tests or commands.

Reviewer uses `openai-codex/gpt-5.6-sol` at high effort by default; task-specific
effort may raise it to xhigh.

## Model and context policy

Every project agent declares a full concrete OpenAI-Codex selector rather than a
project role alias. Existing Sol/Luna/Terra assignment is preserved, with the
new Portfolio using Sol max.

Reviewer changes from the provisional xhigh default to Sol high with optional
per-task escalation.

At user scope, every current OpenAI-Codex model receives a `contextWindow` model
override of 372,000 tokens. New catalog models require the same override when
introduced. HMASD does not override OMP compaction thresholds; it uses default
reserve-based compaction, mid-turn safety checks, and automatic continuation.
Long-lived Portfolio/EM/CM agents perform a light state reconciliation after
compaction.

## Git and worktrees

Root owns the canonical `omp/workflow` branch. Research and engineering use
separate direction-scoped worktrees/temporary branches.

A normal Python helper—not an OMP Extension—handles:

- canonical path resolution;
- assignment-owned path checks;
- base SHA checks;
- worktree creation/reuse;
- conflict detection;
- verification-result references;
- clean application into `omp/workflow`;
- structured error return to Root.

A conflict-free, path-compliant change may integrate automatically. Conflict,
stale base, or out-of-scope paths return to Root. Git operations on
`omp/workflow` do not require user approval. Other branches do.

Root commits and pushes at material checkpoints:

- research or engineering round completion;
- accepted result promotion;
- run terminal evidence promotion;
- external-review prompt or archive readiness;
- material direction/portfolio lifecycle change.

Intermediate ordinary events batch into the next checkpoint.

## External scientific review

Every active direction uses a fixed scientific external-review sequence for each
materially new frozen question/evidence version:

```text
freeze question and evidence version
  -> Gemini inspiration and Pro inspiration in parallel and mutually blind
  -> local EM research validates, rejects, and synthesizes mechanisms
  -> local direction/portfolio synthesis
  -> Pro convergence reads local synthesis and repository evidence only
  -> archive exact raw and produce handoff
```

A new external-review round is keyed by direction ID, frozen-question SHA,
evidence-set SHA, and workflow version. No material change means no repeat round.

Pro uses its GitHub connector to read `omp/workflow`. The submitted message names
repository, branch, and a repository Markdown prompt path. Prompts explicitly
keep Pro in a scientific role: code is mechanism and experiment-definition
evidence, not an invitation to generic code review.

External artifacts are organized by direction and round:

```text
docs/external-review/directions/<direction-id>/<round-id>/
├── GEMINI_DIVERGENT_PROMPT.md
├── PRO_DIVERGENT_PROMPT.md
├── PRO_CONVERGENCE_PROMPT.md
├── <provider>/NATURAL_COMPLETION_ARCHIVE.json
└── <provider>/HANDOFF.md
```

Raw JSON preserves exact response, SHA, model/session/operation references, and
provenance. Handoff Markdown is the scientific intake boundary. Both are
committed to `omp/workflow`.

### Agentify Desktop audit result

The existing `/mnt/c/Projects/agentify-desktop` already supplies the required
browser/MCP transaction substrate:

- persistent conversation/session binding;
- idempotency key, operation ID, request fingerprint, and Schema v2 ledger;
- at-most-once send count and single-click proof;
- commitment-unknown isolation and verify-existing recovery;
- two-snapshot natural-completion detection;
- raw response, SHA, model evidence, and snapshots;
- multi-tab operation with default 6 inflight queries and 12 tabs.

The Agentify ledger at
`C:\Users\fires\.agentify-desktop\review-transport.json` is the sole authority
for webpage submission and commitment. HMASD records references and exports
durable scientific archives; it does not mirror the send state machine.

No HMASD OMP Extension is created. External Review Skill and ordinary helper
functions perform archive/handoff export. The final runtime decision uses the
user-configured Windows installation at `C:\Projects\agentify-desktop`, reached
from WSL as `/mnt/c/Projects/agentify-desktop` but executed with Windows
`node.exe`. This preserves the visible Windows Chrome profile and Windows
Agentify state. A native WSL copy at `/home/fires/projects/agentify-desktop`
is retained only as a tested fallback; Linux Node/headless Chrome is not the
default runtime. Browser target recovery and conversation/session reconciliation
remain Agentify responsibilities.

External reviews keep Agentify defaults and automatically run in waves beyond
6 inflight/12 tabs. Dynamic monitoring uses 1–3 existing Transport instances.
Any Transport in MONITOR mode may inspect any provider session because monitoring
only checks session completion and performs handoff; submission remains
provider-specific. Portfolio assigns disjoint session lists. Duplicate
observation is harmless, archives are written atomically, and no persistent
monitor lease/claim is introduced.

## Dashboard and user reporting

The project provides a read-only local Web Dashboard plus material-checkpoint
terminal summaries.

Dashboard architecture:

- Python local service with static HTML/JavaScript;
- no database;
- binds only `127.0.0.1`;
- reads authoritative Markdown, compact workflow JSON, local run manifests,
  Agentify references, Git/worktrees, and ignored `.omp/runtime/*.json`;
- file events update durable views immediately;
- local agent/tab/PID status refreshes every 5–10 seconds;
- Root starts/reuses and supervises the service through OMP Hub;
- Dashboard provides links/navigation hints only—no approve, start, stop, retry,
  or state-mutating controls.

Initial views:

1. Portfolio and direction relationships/lifecycle.
2. Active logical agents and links to Agent Hub inspection.
3. Runs, local resources, terminal states, and promoted results.
4. Gemini/Pro rounds, Agentify operation references, monitoring, archives, and
   handoffs.
5. Direction worktrees, integration SHA, conflicts, and OMP-branch checkpoints.

Root emits a compact non-blocking summary at material checkpoints and continues
automatically. The user is not asked to acknowledge ordinary summaries.

## Recovery

Root process restart prefers resuming the original Root session. Startup
reconciles persisted Agent Hub lineage, local agent registry, current workflow
state, local run manifests, Agentify ledger references, Git/worktrees, and
process status. An untrustworthy Root session rotates to a new generation from
project state.

Recovery rules remain effect-specific:

- pure research tasks may restart after a proven failure with a new attempt;
- partial code work first reconciles patch/worktree state;
- unknown experiments first inspect PID/output/manifest and never relaunch
  blindly;
- Git push recovery fetches and compares remote SHA;
- external submission recovery always trusts Agentify ledger and never resends
  commitment-unknown operations;
- late outputs cannot silently overwrite a newer accepted checkpoint.

Only Root may spawn Workflow Recovery Manager. Recovery remains bounded and
advisory; exhausted safe routes become a user-visible blocker.

## Detailed implementation contract

The linked implementation plan now resolves:

1. exact JSON schemas for registry, research state, engineering state, runtime
   registries, run manifests, accepted metrics, Agentify archives, and role
   payloads;
2. project Skill bodies and agent frontmatter/tool allowlists;
3. the separately approved Agentify WSL/headless/CDP prerequisite contract;
4. the Python worktree API and automatic-integration checks;
5. the Dashboard API, file parser, UI layout, and Agent Hub navigation bridge;
6. numeric memory safety and CPU preflight calculations; and
7. state, run, Git, Agentify, Dashboard, Advisor, and recovery verification.

SSH-managed local GPU execution remains explicitly deferred.

## Non-goals

Except for the approved role-scoped Advisor target, this concept does not
authorize or introduce:

- an Airflow/Temporal/Dagster-style central control plane;
- a workflow database, event-sourcing system, or ordinary monitor lease;
- DVC, MLflow, or Prefect dependencies;
- a HMASD OMP Extension;
- Advisor coverage outside the listed critical roles or any Advisor
  approval/gating authority;
- ordinary research approval gates;
- Reviewer or test authority;
- tracked raw local run directories;
- Dashboard write controls;
- GPU/cloud execution;
- implementation changes to HMASD or Agentify Desktop merely because they are
  described by this concept or its detailed plan.
