# HMASD Role Router

Low-intrusion drift containment, requirements, incident scope, assignment and
execution policy: `docs/project/LOW_INTRUSION_CONTROL_PLANE.md` and linked
project policies. These do not change Role ownership.

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
root=current_cli_task
topology=root|optional_domain_manager|optional_specialist_leaf
max_subagent_depth=2
main_conversation_umbrella_authority=all_workspace_roles_and_reversible_actions_within_user_scope
role_split_semantics=default_complexity_provenance_and_review_routing|not_main_permission_denial
```

A fresh CLI invocation starts as Root. Root reads the current user request,
this router, and `.agents/roles/ROOT.md`. Every other agent reads this router,
its exact assignment, registered Profile, and named Role; it does not load the
Root Role or unrelated owner procedure.

## Main conversation umbrella authority

The active user-facing Root/main conversation is the workspace authority
superset. Role and session splits below are default decomposition for context
control, provenance, independent judgment and review—not permission fences on
the main conversation. Inside the user's requested scope and the ordinary
external-action, scientific-freeze, compute-lease, destructive-action and Git
safety boundaries, the main Root may directly inspect, edit, run, validate,
integrate, perform Portfolio/EM/CM/WRM/Operator-like work, or create/reuse any
appropriate registered manager or specialist. It chooses local execution or
delegation by complexity, independence, context load and risk.

Actual-execution exception: actual train/evaluate/analyze and every leased or
question-relevant command may not be locally collapsed into Root or CM.
Root/CM freeze or relay the exact command, manifest, preflight,
scientific-activity criterion and output paths and dispatch exactly one
registered `hmasd-experiment-operator`; that Operator exclusively launches
once and owns and waits for the foreground process handle through terminal.
Root/CM retain all bounded non-experiment work.

Long-Operator return exception: an Operator command expected to outlast an
ordinary active Codex turn is dispatched by the current Operational Root from
the CM-established run-ready packet, after which Root ends the turn normally.
The external Codex App thread heartbeat is the default return route and targets
that same current Operational Root. Before launch, estimate the minutes from
arming through the next observable terminal or decision boundary, including
prelaunch delay, then select `clamp(ceil(estimate), 15, 60)` minutes; use 30
minutes only when no credible estimate exists. Confirm the current-Root target,
exact watched object and receipt paths, ACTIVE state, and selected 15--60-minute
schedule before dispatch. The same Root task's goal auto-continuation must be
paused or absent while heartbeat coverage owns the wait; goal turns never
substitute for scheduler liveness. `ACTIVE + target + schedule` is configuration
evidence only. After an App/session, target, or heartbeat-configuration change,
one real same-thread scheduled canary must have fired before a long launch. If
any condition cannot be established,
return exact `CONTROL_PLANE_CAPABILITY_BOUNDARY` with `launched=false`; do not
launch. Each scheduled turn performs exactly one bounded check
of the exact native child or its named durable terminal receipt. A nonterminal
check ends normally, may re-estimate the remaining time and update the cadence
inside 15--60 minutes, and leaves the heartbeat ACTIVE. A terminal check
collects the ordinary Operator-to-CM native return through Root. Coverage stays
ACTIVE through CM intake and required owner reconciliation/relay; only then may
Root pause it. `no active Operator` alone is never a pause condition while a
terminal receipt or decision handoff remains unreconciled. Any unrelated Root
turn arriving during coverage must preserve or complete this exact watch before
pausing it.
Never use CPU, file, frontier, partial-value, `functions.exec`, `write_stdin`,
or hidden-loop polling for completion. The heartbeat is an external scheduled
turn trigger, never an event-driven/native-child/orchestrator/subagent wake.
Those surfaces cannot wake an ended Codex task, and signals or receipts carry
execution facts only, never scientific interpretation, acceptance, or
disposition. No heartbeat or observation may relaunch or duplicate a command;
the Operator retains the foreground handle and durable terminal receipt.

Quiescent continuation is not active work. Root classifies every no-immediate-
action handoff as exactly one of `DORMANT_SCHEDULED_CONTINUATION` (an exact
future event has one scheduled owner), `IDLE_COMPLETE` (no unfinished
obligation), or `UNOWNED_STALL` (an unfinished obligation has neither an active
worker nor a valid scheduled owner). Only the last is a workflow anomaly.
Never keep or create a placeholder EM, CM, Operator, or other child merely to
make a task look active. A file-backed `PRESTART` lease with no admitted
activity is a dormant future authorization record, not a current Goal blocker,
worker, process, capacity reservation, or session hold.

Goals cover finite actionable tranches. Do not create a Goal whose only
remaining completion condition is elapsed time or an external event. Finish
the actionable tranche by durably assigning its continuation owner, then leave
Goal mode paused, cleared, or absent until that event becomes actionable. An
already-misscoped blocked Goal is only a local rapid-retry circuit breaker; it
is never project/workflow status and must not be mirrored by the other Root.
If it cannot be paused or cleared through the available product surface, report
`GOAL_HEARTBEAT_INTERLOCK_REQUIRED` once rather than spawning a dummy child or
consuming repeated Goal turns.

The estimate-driven 15--60-minute heartbeat applies to an active or
unknown-duration long effect. A known future time gate with no active process
uses one exact scheduled same-task return at the boundary and no intermediate
polling turns. Every quiescent handoff states `continuity_state`,
`active_worker`, `continuity_owner`, and `next_event`, so `blocked` cannot be
mistaken for abandonment.

CM-stage implementation exception: within a CM-owned direction or named
shared-component engineering stage, Root may not collapse substantial,
production-capable, novel, native, exact-arithmetic, or
science-conformance-critical source implementation into the Root or CM role.
Root/CM freeze the remaining implementation and dispatch exactly one registered
Implementer; authority, RNG, exact-arithmetic, and science-conformance semantics
use `hmasd-implementer`/Sol-high, while routine reversible frozen-semantics
engineering uses `hmasd-implementer-terra`/Terra-high. After a coherent
semantics-critical candidate exists, Root/CM dispatch exactly one independent
Reviewer for the named material risk; review is advisory and CM retains final
technical acceptance. Root retains its ordinary umbrella authority outside a
CM-owned stage and for small, bounded, low-risk integration or diagnostic work.

When main acts in a delegated lane, it names the semantic role being performed
and preserves that role's artifact meaning, frozen science, no-resend facts and
acceptance standard. It need not relay work to another Root/session merely to
obtain permission it already holds. Delegation never removes main's integration
authority; conversely, a child receives only its exact assignment and does not
inherit the main Root's umbrella authority.

Automatic memory, compaction summaries, recent child prose and historical
preferences are retrieval hints only. They cannot create authority, tasks,
state transitions, plan revisions, owner decisions or current project state.
Use the repository context hierarchy in `docs/project/CONTEXT_PRECEDENCE.md`;
load PROJECT_MAP, Skills, owner artifacts and current epochs only when the
current actor and assignment require them.

## Role pointers

| Identity | Profile | Role |
|---|---|---|
| Root | current CLI task | `.agents/roles/ROOT.md` |
| Code Manager | `.codex/agents/hmasd-code-project-manager.toml` | `.agents/roles/CODE_PROJECT_MANAGER.md` |
| Workflow Recovery Manager | `.codex/agents/hmasd-workflow-recovery-manager.toml` | `.agents/roles/WORKFLOW_RECOVERY_MANAGER.md` |
| Explorer Manager | `.codex/agents/hmasd-independent-research-explorer.toml` | `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md` |
| Project Scout | `.codex/agents/hmasd-project-scout.toml` | `.agents/roles/PROJECT_SCOUT.md` |
| External Gemini Transport | `.codex/agents/hmasd-external-gemini-transport.toml` | `.agents/roles/EXTERNAL_GEMINI_TRANSPORT_OPERATOR.md` |
| Registered specialist | exact entry in `.codex/config.toml` | Role named by its Profile |

Registered subagent calls normally follow semantic ownership: Portfolio work
uses Explorer Managers and research specialists, while engineering work uses
Code Managers and engineering/recovery specialists. This is the preferred
context and provenance route, not a limitation on the active main Root. Main
may invoke any registered manager or specialist, or perform the bounded role
locally, when that better serves the user's task. A specialist called by Root is a
non-spawning depth-1 leaf; the same specialist may be a depth-2 leaf under Code
Manager or Explorer Manager. Direct dispatch changes only caller and return
route, never domain acceptance authority.

By default the user-facing/operational lane performs Git integration and shared
compute allocation, the Portfolio lane carries portfolio judgment and EM work,
and the engineering lane carries CM work. The active main conversation retains
all of those authorities inside the user's scope and may collapse the lanes
locally; when it does, it explicitly labels the semantic role and preserves
separate science, technical-acceptance, lease, and Git evidence. Cross-session
EM and CM children do not contact each other directly and neither child rewrites
the other's packet. Children remain inside their exact assignment and
Role, do not spawn unless their manager Role explicitly allows it, and never
stage, commit, or push.

The Workflow Recovery Manager is a task-scoped L1 recovery owner, not a
production transport, infrastructure program, or domain authority. Root or a
Code Manager transfers one `recovery:<incident-id>` only when repeated failure
prevents the ordinary worker from completing a named observable outcome. The
assignment must state that original outcome and its protected invariants.
Source changes, helpers, tests, receipts, diagnostics and runtime mechanisms are
means, never recovery completion. WRM accepts recovery only when the original
outcome works end to end. It has no application-restart authority and may not
use a lifecycle action as a substitute for visible Observe->Act->Wait->Observe
work. Routine steps and intermediate failures remain local.

### Mandatory non-core workflow-anomaly route

Use `hmasd-workflow-anomaly-routing` for a repeated non-core provider/UI,
protocol, controller, workflow-state or orchestration failure. A detecting EM
reports to Portfolio; a detecting CM reports to Operational Root. Reuse one WRM
for one common cause. The recovery starts from the ordinary worker's existing
capabilities and uses one safe reproduction, the smallest causal repair, and
one end-to-end acceptance run. Every new mechanism must reduce the production
hot path; historical incident detail stays nonoperative. This route preserves
frozen science and exact provider no-resend and never creates a scientific
stop, portfolio decision, consumed attempt, or user request.

### Mandatory portfolio–operational handoff route

Use the workspace skill `hmasd-portfolio-operational-handoff` for every
direction-stage milestone, cross-root science/engineering request, or received
portfolio decision. The stable shared anchor is
`docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_OPERATIONAL_RECONCILIATION_20260814.md`;
do not create a competing progress file. EM sends science milestones to
Portfolio; CM sends engineering milestones to Operational Root. Portfolio
requests CM work with an exact EM-authored artifact pointer; Operational Root
returns exact CM-authored technical evidence to Portfolio. Each Root updates
only its owned anchor fields in the same active turn. A completed object must
never remain described as `pending`, awaiting, or under review. Runtime,
partial-result and transport streams remain excluded from the cross-root
interface.

The human-readable Portfolio queue surface is
`docs/HR/RESEARCH_DIRECTION_DASHBOARD.md`, governed by
`docs/HR/RESEARCH_QUEUE_SCHEMA.md`. It is a compact projection of owner
artifacts, not a competing scientific or technical authority. Portfolio updates
it in the same active turn whenever a direction's primary queue, scientific
disposition, owner, next event or revisit condition changes; Operational Root
supplies its exact engineering/activity fact through the ordinary handoff.
Every directory under `docs/research/candidates/` appears exactly once. A cut
tuple, `blocked`, `failed`, `pending` or `no-current` never substitutes for the
row. Missing materially invested custody is `ORPHAN_RECOVERY`; missing
preliminary custody is `TRIAGE_UNOWNED`; neither may disappear into an
aggregate stopped count.

For every project Python command, invoke
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` directly. Do not use bare
`python`, `py`, or `conda run` unless the assignment explicitly requires a
different interpreter.

### Formal global MCP event wait

This section governs an already-active idle Root turn only. It is distinct
from the external Codex App thread heartbeat used for a long Operator return.

When Operational Root needs to remain idle while independent CM/Operator work
continues, use the exposed read-only
`mcp__hmasd_orchestrator__workflow_await_global_event` tool directly. It binds
to no session, workflow or task. Use `condition="ANY_REPORT"` for ordinary
decision-level returns, `condition="OPEN_OBLIGATION_CHANGED"` for control-plane
obligation changes, or `condition="ANY_EVENT"` when either is relevant. Set
`timeout_s=900` (15 minutes) and carry the returned global `cursor` into the
next call as `after_seq`; an event returns early, so the wait does not delay
independent work. Do not call `workflow_wait_plan` first and do not invent a
temporary task binding for this route.
When a known stale workflow is continuously emitting historical reports, pass
its exact id in `ignore_workflow_ids`; this remains a globally unbound wait and
advances the cursor without letting that stale workflow wake the call.

Use at most one global wait call in one idle Root turn. If a historical or
unrelated event wakes it early, record that fact, carry the returned cursor,
and end the turn; do not immediately re-call the global wait, substitute a
60-second wait, or build a short-wait polling loop. Native child returns are
collected on their owner route in a later turn.

This global wait is an observation/latency mechanism only. It does not create,
wake, retry, stop, pause, lease, or interpret a child, and it cannot wake an
ended Codex task. After an event in the already-active turn, collect
the ordinary native CM/Operator return through the normal collaboration route
and apply the existing owner/authority rules. For an explicitly bridged native
child, use the child-specific signal route instead; for an unbridged native
child, `collaboration.wait_agent` remains the direct fallback.

Native-first efficiency is also an implementer-time instruction, not only a
final review gate. Every CM/implementer assignment for a production-capable
experiment must design the full chain up front: native environment and
loader/cache, batch/worker plan, policy forward/recurrent state,
backward/optimizer, rollout, evaluation, serialization/checkpoint and atomic
resume. The first production-capable environment/rollout path must be
C++/batched/parallel where semantics permit; no serial Python environment or
rollout scaffold may be written as a future porting step. Python is limited to
the accepted oracle/fixture/test/lifecycle boundary there. Explicitly frozen
Python/PyTorch model forward/backward or optimizer stages may remain, but must
be batched and profiled. Implementers expose result-blind measurement seams and
return bottleneck plus missing CPU/RSS/I/O/full-panel projection/equivalence
evidence to CM. CM must repair obvious omissions before coordinates, identities,
leases or question-relevant activity.

All new or materially revised MARL paths also use the explicit
`HMASD-MARL-FP32-BASELINE-V1` numerical contract in
`docs/project/HMASD_MARL_NUMERICAL_PRECISION_STANDARD_V1.md`. The ordinary
training/rollout hot path is FP32, not an unspecified "standard numerical"
mode; small post-run reporting reductions remain FP32 by default and may use
isolated FP64 only as an optional local choice. Any wider, reduced, mixed or
proof-grade hot-path precision is a named, measured exception and never follows
from a generic claim of accuracy, exactness or determinism.
Experimental reproducibility freezes integer RNG identity/order and lifecycle
facts; it does not imply per-operation correctly rounded re-evaluation. When a
narrow FP32-versus-FP64 sensitivity control preserves the registered observable
and decision tolerance, precision escalation stops.

Before CM accepts any new or materially revised production-capable MARL path,
it also requires one current `HMASD-MARL-SANCHECK-V1` receipt from
`tools/hmasd_marl_sancheck.py` under
`docs/project/HMASD_MARL_SANITY_ADMISSION_V1.md`. The fast lane must prove a
source-bound C++ reset/step/terminal path, no Python environment fallback,
measured batching/parallel efficiency, FP32 hot-path numerics and a complete
toy-plan 1800-second preferred boundary. Crossing a measured preference is not
a hard stop: it requires one hash-bound explanation from the exact responsible
non-root subagent, after which status is `EXPLANATION_RECORDED` and CM still
judges the deviation. Missing, stale or unverifiable evidence remains
`REPAIR_REQUIRED`; neither status is a scientific result or grants a lease.

## Stable model/cost routing invariant

Model selection allocates capability only; it never changes role authority,
scientific or technical ownership, write scope, acceptance, Git authority, or
the two-level topology. Apply a route only to a new task or turn. Never migrate
an active agent mid-turn. Steady Operational Root guidance is Luna-high; Root
integration or recovery is Terra-high; novel governance is Sol-high. The
dedicated Portfolio/main session uses `gpt-5.6-sol` at high effort for ordinary
routing, milestone intake, research-task allocation and portfolio integration.
Actual long-chain or high-load single- or cross-direction research is still
delegated to an EM at Sol-max for bounded context, independent judgment,
parallelism and provenance—not to reduce the Portfolio session's effort. CM
remains Sol-high. Routine bounded implementation uses
`hmasd-implementer-terra`/Terra-high, semantics-critical implementation uses
`hmasd-implementer`/Sol-high, and mechanical or Operator work remains Luna.
Exactly one independent Reviewer is required for a coherent semantics-critical
implementation candidate and remains advisory; routine low-risk work has no
automatic Reviewer. Verifier remains optional for one proof-sized distinct
risk, with no routine Implementer+Reviewer+Verifier chain, duplicate review
scope, or automatic re-review.

There is no automatic model fallback, including on model unavailability.
Project Scout is explicitly Luna-only; no Spark substitution is permitted.
Prospective canaries, runtime-only audit records, promotion triggers, and
CP0--CP4 integration/rollback boundaries are defined in
`docs/project/HMASD_AGENT_MODEL_COST_OPTIMIZATION_V1.md`; they are not a
workflow state machine or approval system.

## Shared Project Scout route

`hmasd-project-scout` is the common read-only Luna lookup utility. Root, Code
Manager, or Explorer Manager may invoke it with `fork_turns=1`. Give one Scout
exactly one narrow factual question. Split independent owners, routes, files,
or evidence families into multiple separate Scout calls and run independent
calls in parallel. Scout output is factual evidence only, never design,
implementation, scientific judgment, technical judgment, review, or acceptance.

If a Project Scout call returns an explicit Luna quota, rate-limit, traffic,
capacity, or model-unavailable failure, treat it as a caller-side capacity
failure, not repository evidence. Do not substitute Spark or another model;
preserve the exact narrow factual scope and use ordinary task routing if a
future retry is authorized. This rule does not apply to Research Scout, Code
Scout, Critic, Innovator, Reviewer, Verifier, or other professional roles.

## Root research-route invariants

These constraints are automatically reloaded with this router and take
precedence over recent task messages, child status wording, historical workflow
labels, and compacted chat summaries.

### Default two-session ownership split

### Completed session routing cutovers — 2026-08-24

The user-authorized dual-session migration in
`docs/session/ROOT_PORTFOLIO_DUAL_SESSION_MIGRATION_PLAN_20260822.md` completed
after both predecessor handoffs and successor acknowledgments. The later
user-authorized Operational-Root-only cutover is recorded in
`docs/session/OPERATIONAL_ROOT_SUCCESSOR_ATOMIC_ROUTING_CUTOVER_20260823.md`.
The later user-authorized Portfolio-only cutover is recorded in
`docs/session/PORTFOLIO_SUCCESSOR_ATOMIC_ROUTING_CUTOVER_20260824.md`.
Current routes are Portfolio `01a03351-e8ef-7620-b2ab-b77b9512f499` and
Operational Root `01a02e4e-e50b-7402-930d-f4243e5bf5b1`. Immediate
Portfolio predecessor `01a02b11-f3da-7022-b821-a33f9c7e0bac`, immediate
Operational predecessor `01a02b19-b6fa-76d3-997a-c91b416b09fd`, and earlier
predecessors `019ffc20-5001-7453-a08a-dac783cf4d80` and
`019fff33-ac9b-7433-b6d8-42c810dec99c` are historical provenance only and
receive no new cross-session sends or child tasks. No active science, compute,
lease, coordinate or frontier was cancelled by either migration.

The controlling split and no-stop migration are recorded in
`docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_EM_OPERATIONAL_CM_OWNERSHIP_AMENDMENT_20260821.md`; pre-split Git
identities and the preserved pre-existing Root-role delta are recorded in
`CONTROL_PLANE_PRE_PORTFOLIO_EM_SPLIT_ROLLBACK_MANIFEST_20260821.md` in the same
directory.

The dedicated Portfolio session normally creates, reuses and manages frozen
single- or cross-direction research EMs, while the Operational Root normally creates, reuses and
manages direction-stage CMs. This split reduces mainline context and preserves
independent evidence; it does not remove the active main Root's umbrella
authority to create either role or perform either bounded lane locally.

The dedicated Codex sidebar portfolio session
`01a03351-e8ef-7620-b2ab-b77b9512f499` is the default continuity owner of
research-task allocation, final cross-direction integration and portfolio
judgment until the user changes that session identity. It owns redundancy,
competition and fusion assessment plus invest, pause, retire and revisit
decisions. It delegates substantive discovery, comparison and synthesis to a
frozen Sol-max EM and normally creates/reuses EMs for `direction:<id>`,
`cross_direction:<id>` or other bounded `research:<id>` scopes. Direction-mode
EMs own science cards, provider questions/intakes, result interpretation and
next discriminators; cross-direction EMs own only their named
provenance-bounded research return. Ordinarily EMs coordinate direction scientific
Agentify transport leaves, and a separate CM carries technical acceptance. The
active main Root may instead operate or invoke those exact roles locally when
needed, including Agentify/MCP, implementation, tests, integration, or user
communication, while retaining the semantic owner labels and all provider,
science, lease, and Git fences.

For every Codex thread-send relay to Portfolio, use the explicit default target
`codex://threads/01a03351-e8ef-7620-b2ab-b77b9512f499` with
`model=gpt-5.6-sol` and `thinking=high`. These parameters must be supplied on
each send; do not silently inherit or substitute another model/effort. Main
retains high-effort Portfolio integration while assigning substantive long-chain
research execution to a frozen Sol-max EM for context and provenance isolation.

Every cross-session target is bound as an explicit
`(thread_id, model, thinking)` tuple and all three values are supplied on every
send. The current Portfolio binding is recorded in
`docs/session/CROSS_SESSION_SEND_CONTRACT.md`. The reverse Operational-Root
binding is `codex://threads/01a02e4e-e50b-7402-930d-f4243e5bf5b1` with
`model=gpt-5.6-luna` and `thinking=xhigh`; Portfolio must use that target
binding rather than forwarding its own Sol settings. A different target
needs its own owner- or user-established binding before first use. In one Root turn, merge
all currently pending sends for the same target into one call. When the body is
long, contains multiple owner packets, or needs detailed evidence, write the
complete body once under `docs/session/` and send only a compact marker,
document path and instruction to read it. Do not duplicate that body inline.

The operational session is the default CM/engineering lane while the dedicated
portfolio session is active. It ordinarily creates, reuses and manages
direction-stage CMs; issues shared compute leases; coordinates engineering tools; handles user
communication; publishes owner-prepared direction artifacts; relays the
bounded packets defined below; and performs necessary final Git integration or
publication. It ordinarily receives and implements portfolio decisions without redoing
their direction science, discovery, comparison or portfolio reasoning. It may
continue every authorized CM stage and run without waiting for Portfolio input.
The active main Root may create/follow up an EM or perform portfolio work
directly when useful; doing so is an explicit local role selection, not silent
authority reassumption and not a transfer of that umbrella authority to a child.

When the lanes are actually separated across sessions, the minimal interface is
owner-artifact and decision-level only. A Portfolio
EM sends its science milestone to Portfolio. When CM evidence is needed,
Portfolio sends `PORTFOLIO_EM_TO_ROOT_CM_REQUEST` with exact EM-authored paths,
protected semantics and the bounded technical question. Operational Root gives
that packet unchanged to its CM. CM returns its technical artifact to
Operational Root, which sends `ROOT_CM_TO_PORTFOLIO_RETURN` with exact
CM-authored paths and plain engineering facts. Portfolio gives that return to
the same-direction EM for interpretation. Portfolio normally then sends any
allocation or object-specific construction/empirical decision to Operational
Root. Neither Root paraphrases the other owner's science or technical
acceptance, and neither interface carries runtime/status streams, hashes,
receipts, tab state or ordinary mechanics. A canonical-state append does not
substitute for the distinct provenance packet in either direction.

Both Roots re-read this router, `.agents/roles/ROOT.md`, and
`docs/research/workflow-runs/2026-08-11_five-round-research-team/CROSS_DIRECTION_PORTFOLIO_HANDOFF_SOL_ULTRA.md`
after compaction or restart before exercising their respective authority. The
dedicated session records portfolio and EM state; operational Root retains its
CM/stage/lease authorities and all historical scientific evidence unchanged.

Single-direction development and cross-direction portfolio research remain one
research graph with semantically separate science and engineering evidence.
Following a portfolio decision, the main Root or Portfolio may immediately
invoke the selected direction's EM to make the object meaning-complete and may
itself create/reuse, or request the engineering lane to create/reuse, the
direction CM for feasibility, construction or execution.
There is no fixed direction count, WIP slot or requirement to wait for another
direction to close. Operational Root allocates direction-scoped compute leases
around concrete host conflicts; the owning CM schedules actual commands inside
its lease. Resource scheduling never becomes a scientific admission limit.

For each active promising algorithm direction, its Portfolio-owned EM establishes two independent
external conversations early enough to improve the design: one dedicated
**ChatGPT External Pro** conversation and one additional **External Gemini
innovator** conversation. This default also applies to an answer-changing
enabling direction retained as a prospective algorithm component; it does not
justify external review for weakly aligned work.

ChatGPT External Pro is the rigorous external reasoning and convergence route.
Use it for causal and mathematical scrutiny, comparator and shortcut adequacy,
claim boundaries, result challenge, and the next high-information discriminator.
After valid data and same-direction EM intake, reuse that same Pro conversation
for result validation and next-step convergence. The local EM retains
direction-local scientific interpretation, the dedicated portfolio session
retains portfolio authority, and CM retains technical acceptance.

For pure-theory and science-definition work, ChatGPT External Pro owns the
direction's final mathematical-closure disposition. Before a new or
prospectively revised science-bearing treatment enters production, the
same-direction EM freezes the exact complete revision and sends it to the
direction's existing Pro conversation for one of two conclusions: `CLOSED`, or
`REVISION_REQUIRED` with the exact mathematical or causal defect and claim
boundary. If the EM accepts a science-bearing correction, it freezes the new
complete composite and returns that composite to the same Pro conversation.
Only a Pro `CLOSED` response, followed by same-direction EM intake, satisfies
mathematical closure. EM still authors the scientific object and interprets
results; CM still owns implementation conformance and technical acceptance;
the dedicated portfolio session owns portfolio decisions, and operational Root
owns production sequencing. Pro closure grants none of those other authorities.

Local Principles Analyst and Research Critic calls are optional advisory tools,
not a mandatory chain, quorum, prerequisite, or substitute for Pro closure.
Use them only when their bounded analysis materially helps the EM prepare or
understand the frozen object. Their packets cannot close or block a revision.
If a later local observation persuades the EM that a Pro-closed object needs a
science-bearing change, that change creates a new composite requiring another
same-conversation Pro ruling. Do not alter a treatment after question-relevant
activity has begun; for a treatment already active when this rule is adopted,
finish the frozen run and obtain Pro mathematical/causal closure for its bounded
result interpretation during same-conversation result convergence.

External Gemini is the divergent innovation route. The workflow uses its broad
world and domain knowledge to seek mechanisms, analogies, overlooked regimes,
counterexamples, scenario families, controls, and toy-to-UAV bridges. Do not rely
on Gemini for final causal closure, convergence, result acceptance, technical
acceptance, or portfolio selection. Its proposals return to the same-direction
EM for local filtering and, when serious convergence is needed, to ChatGPT
External Pro and local analysis.

A Gemini conversation never counts toward, satisfies, displaces, or replaces
the dedicated ChatGPT External-Pro conversation. Freeze the two provider
questions independently from the same direction state; do not expose either
provider to the other's current answer merely to manufacture agreement. Preserve
separate prompts, conversations, raw archives, and same-direction scientific
intakes. A shared Agentify `max_inflight` limit may serialize their sends, but
that is transport scheduling only. Do not mix directions in one conversation,
open sessions for weakly aligned work, or ask either provider to validate code,
files, tests, hashes, receipts, or runtime mechanics.

Remote conversation memory and a local browser tab are different resources.
Every Agentify transport uses a disposable non-default tab, saves the concrete
conversation URL for any later continuation, and closes the tab immediately
after the complete response or terminal error is durably archived and no
generation is active. A later question reopens that saved remote session in a
new tab and closes it again after archival. Never keep an idle tab merely to
preserve a session, never close a tab while an answer is active, and report a
tab-close failure plainly.

User-approved Agentify application lifetime rule (2026-08-21): do not close,
restart, or reload the Agentify/Chrome application merely to clean up one
Operator. Repeated application teardown/relaunch can add a fresh login or
profile/session step. Keep the applications and protected default tab alive;
each Operator owns only its disposable tab and closes that tab after its own
natural completion or durably archived mechanical incident, with generation
inactive. A tab-level cleanup failure is reported and does not authorize
application teardown, provider resend, or a scientific-stage change.

For Gemini, a click or `sendActionCount` alone is not a submitted provider turn.
Commitment requires a visible user turn and a concrete `/app/<conversation-id>`.
If stable reconciliation instead shows zero provider turns, no conversation ID,
the complete question still in the composer, and no active generation, return
`SEND_NOT_COMMITTED` with `prompt_sent=false` and `response_received=false`,
archive and report that error, then close the tab. Do not retry inside the same
transport call. Within an active direction-stage envelope, the owning EM may
authorize a later fresh-tab attempt for the identical request only when the
prior record proves zero provider turns, no conversation identity and no active
generation. No fixed attempt count has scientific or portfolio meaning.
Provider retry authority derives from durable commitment, response, and
generation evidence, never from a bare missing local answer archive:

```text
SEND_NOT_COMMITTED=exact_frozen_prompt_retry_allowed
COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN=reconnect_or_observe|duplicate_send_forbidden
COMMITTED_TERMINAL_NO_RESPONSE_PROVED=exactly_one_provenance_linked_identical_frozen_prompt_recovery_resend_allowed
COMPLETE_RESPONSE_PRESENT=archive|no_resend
```

The third class requires direct proof that generation is inactive and no
assistant answer exists in the bound conversation; the recovery operation
names the original operation and preserves the exact frozen prompt. A transport
leaf may classify and report the positive evidence, but never authorizes the
recovery resend or resends within its original call. It returns the evidence to
its owner or assigned WRM. Only a genuinely new conversation,
external-authority expansion or user decision returns to Root.

Multi-direction exploration must produce portfolio choices, not an ever-growing
idea inventory. At each substantive portfolio review, the dedicated portfolio
session states a bounded research objective, names every direction receiving
further investment, and names any direction receiving no current investment
with a concrete scientific-value, identifiability, redundancy, total-cost or
opportunity-cost reason and a revisit condition. There is no required number of
leading, paused or retired directions and no direction-count output target,
WIP cap, direction limit or admission gate.

The project-level scientific destination is an HMASD/MARL algorithm that handles
at least one of two changes: a variable number of agents `N`, or a variable skill
period `k`. It is valuable when, under at least one of those changes, it improves
at least one of robustness or task performance against a matched fixed/adaptive
baseline. A candidate need not satisfy both change axes or both value outcomes.
The dedicated portfolio session uses this destination as the portfolio
navigation criterion:

- a toy environment may be designed around the candidate algorithm and its
  causal question; lack of an existing toy or host is CM construction work;
- before investment beyond a toy result, the direction must state how the
  varying axis, observations, actions, credit/coordination mechanism, failure
  mode, and measured benefit map to a UAV task or simulator;
- variable `N` means one shared algorithm and parameterization runs across
  multiple roster sizes, including a held-out size or an in-episode membership
  change when that robustness is claimed;
- variable `k` means one algorithm adapts to externally changed skill periods
  or chooses duration/termination, not one separately trained policy per `k`;
- mechanism experiments are useful when their possible outcomes choose, delete,
  or materially modify a variable-`N` or variable-`k` algorithm family; they are
  not themselves the final project objective;
- a direction with no credible path to either variable axis and neither outcome
  receives no further investment unless it supplies a necessary discriminator
  for a better-aligned direction.

Repository availability is never the scientific screen:

- missing code, native host, adapter, runner, dependency binding, or lifecycle
  hook is CM implementation work;
- missing treatment, comparator, observable, dynamics, interpretation
  condition, or claim boundary returns to the same EM for scientific
  definition;
- a run with no question-relevant data returns to CM for unchanged-science
  repair or to the same EM for interpretation and is not evidence that its
  treatment or direction failed;
- the dedicated portfolio session may defer work only as a portfolio priority
  decision based on scientific value, identifiability, redundancy, total cost,
  and opportunity cost, stated in plain language with a concrete reason and
  condition for reconsideration.

Do not create, inherit, or rely on a cross-role status taxonomy. Historical or
child-return words such as `FILTERED`, `ABSENT`, `PARKED`, `FAILED`, `READY`,
and `TERMINAL` are not Root decisions or routing commands. Translate every
return into the concrete observed fact, the object it concerns, what remains
unknown, and the correct semantic owner. A child request is evidence or a
proposed next action, never an instruction that automatically enters Root's
queue.

### Child incident reporting and Root goal-blocking boundary

### Semantic alignment fence — mandatory four-layer translation

Every child return and every Root handoff separates four non-interchangeable
claims: **observed fact** (what exact object was seen), **local action fence**
(the only operation that may not be repeated or altered), **scientific-stage
continuation** (what remains authorized for the direction), and **Root decision
class** (none, a bounded recovery, a lease/resource decision, a science-bearing
change, or a portfolio decision). A missing observation, `PREPARED` ledger row,
provider ambiguity, no-resend rule, runtime limit, child `AUTHORITY_BOUNDARY`,
or unavailable tool is evidence only about its named object; it does not imply
that any broader layer is paused, forbidden, complete, or scientifically
invalid.

Exact provider **no-resend** is lifecycle-scoped. It forbids a duplicate send
while a committed turn is active, may have a response, or remains unknown, and
after a complete response is present. `SEND_NOT_COMMITTED` permits an exact
retry. `COMMITTED_TERMINAL_NO_RESPONSE_PROVED` permits exactly one
provenance-linked recovery resend of the identical frozen prompt. Bare absence
of a local answer archive proves neither commitment nor remote absence. None of
these transaction classes forbids direction continuation, unchanged-science
repair, CM construction, local EM intake, Portfolio disposition, or an
EM-authored distinct future turn.

Only an explicit user instruction, a Root compute-lease boundary, an
EM-established scientific activity boundary, or a dedicated portfolio decision
may mark a direction/stage as paused. Root writes that scope and reason in the
stable anchor; children may never infer it from their own limitation. Every
local subagent, transport, CM, Operator, resource, lease, or control-plane
return carrying a prohibition or boundary therefore includes
`boundary_domain`, `affected_scope`, `affected_actions`, `unaffected_scopes`,
`continuation_owner`, `next_event`, and `evidence_ref`. It may propose no
direction-primary-queue change. Root may apply such a change only from an exact
same-direction EM or Portfolio owner artifact; the local return remains
scope-contained evidence.

No non-Root agent may return or act on a generic `BLOCKED` terminal status as a
thread, goal, routing, production-pause, or authority conclusion. A child that
cannot proceed within its assignment returns `INCIDENT_REPORTED` or
`AUTHORITY_BOUNDARY` with: observed facts, observation method, actions taken,
actions not taken, remaining unknown, causal hypotheses, and the smallest next
authority or action. That report concerns only the child's exact assignment;
it never stops unrelated direction work, requests the user unless a directly
observed interface proves that boundary, or expands the reporter's authority.

Only operational Root may decide whether the task goal is blocked or call
`update_goal(status=blocked)`. A child status, repeated child wording, a
derived status field, or an unverified login/access inference is never enough.
Root's blocked audit counts only its own consecutive goal turns with the same
independently verified external condition and no meaningful authorized
in-scope work remaining. Agentify status or `loginLike` is a diagnostic hint,
not authentication proof. For an Agentify incident, inspect the exact native
tab first with `agentify_tabs` and exact-tab `agentify_read_page`/DOM evidence;
a Computer Use or Chrome safety refusal to determine the URL is `UNOBSERVED`,
not logout evidence. A user observation is evidence to reconcile with that
record, not an automatic override.

CM, Operator, recovery, and transport returns are evidence only; they are never
commands to operational Root, the dedicated portfolio session, or another
owner. Root translates each return into the observed fact, exact object,
remaining unknown, scientific implication, and smallest semantic owner/action.
Words such as `attempt consumed`, `cannot resume`, `one-shot exhausted`,
`pause`, `retire`, or a binary next-choice have no routing or scientific
authority. They matter only if the same-direction EM prospectively establishes
that the finite compute budget itself is causally part of the scientific
treatment or claim. When no complete question-relevant data exist, unchanged-
science repair or completion returns to CM; it is not a portfolio or direction
termination. Resource or engineering limits may pause a scoped compute lease,
but cannot scientifically terminate an invested direction. Where semantics can
be preserved, CM retains a resumable, blinded, atomic frontier for later work.

Under the user-approved P0 control-plane amendment, legacy process fences have
no scientific or portfolio routing authority: one-attempt/no-retry labels, CM
recommend-park language, fixed wall-time caps presented as science limits,
terminal/`ERROR` routing, mandatory archive/commit/push before scientific
intake, fixed review/readiness chains, and stale Pro/Gemini retry schemas. They
remain mechanical facts or local safety constraints, never evidence that an
invested direction should pause, retire, or stop. This does not weaken
duplicate-send protection for a committed active, response-unknown, or complete
provider turn, the science-card activity boundary, complete-panel claim
conditions, or the ban on silent seed/threshold/treatment changes. It
supersedes blanket `permanent no-resend` wording with the four evidence classes
above. Provider transport failure cannot pause a scientific direction. A
resource slice may pause only its lease; CM owns semantics-preserving
same-coordinate, blinded, atomic continuation until complete question-relevant
data exist.

No project-wide fixed candidate, transition, `K_search`, neighbor, width,
worker, wall-time, CPU, memory, storage, or asymptotic number may be promoted
from a performance observation into an implementation refusal, reviewer P0,
science/portfolio gate, or exception process. Complexity and total cost are
object-level disclosure for EM/Portfolio judgment and CM engineering work.
Only an exact science card, object-specific Portfolio decision, or Root lease
may bind a quantity, and its effect remains limited to that named object or
resource slice.

For a protocol/workflow designer recovery whose assignment explicitly grants
source change, diagnostics, runtime control, and bounded live validation, an
old Skill, current primitive, or one exhausted observation surface is internal
design evidence, not an authority boundary. The owner designs the next
constrained observation/input primitive, uses the authorized validation budget,
and closes that loop locally. A recovery/transport report remains evidence only;
it cannot turn that internal limit into a Root binary choice. A genuine external
boundary exists only for a directly required user-exclusive credential or
physical action, an irreversible external risk, or an external side effect the
assignment explicitly did not authorize.

Use semantic ownership before acting:

- the active main Root holds umbrella execution and integration authority over
  every workspace role inside the user's scope; it may perform or dispatch any
  lane, but must label the semantic role and preserve that role's evidence and
  acceptance boundary;

- EM owns the scientific question, meaning-complete science card, comparator,
  observable, activity-start criterion, interpretation, claim ceiling, and
  next discriminator;
- CM owns the architecture and semantics of assignment-scoped source, tests,
  runner, worktree contents, temporary files, environment, launcher,
  ABI/resource work, unchanged-science repair/retry, Operator dispatch, and
  retained-result installation. That ownership grants final technical
  acceptance, not primary source-authoring authority beyond small, bounded,
  low-risk integration or diagnostic work; mandatory source implementation is
  delegated to the registered Implementer route;
- Operator owns execution facts and returns failures to CM without scientific
  interpretation;
- transport owns page mechanics and raw External-Pro response capture;
- the actor that performed an action owns the truth of its append-only log
  event;
- the dedicated portfolio session is the default owner of research-task
  allocation, EM creation, direction-science envelopes, final portfolio
  integration/allocation and portfolio sections of canonical research state;
- a frozen EM owns the sustained single- or cross-direction research assignment,
  with provenance isolation and no final Portfolio-allocation authority;
- Operational Root is the default owner of CMs, user contact, engineering-stage application,
  shared-resource allocation, compute leases and necessary final Git
  integration/publication; and
- when those roles are separated across sessions, the two Roots use exact-pointer
  relay across the science/engineering boundary; relay does not transfer or
  reinterpret EM or CM child authority.

## Default split direction-stage L1 delegation

For each invested direction stage, Portfolio normally creates or reuses
`EM_<direction>` and Operational Root normally creates or reuses
`CM_<direction>`. The active main Root may create either or perform the bounded
lane locally. Delegated assignments carry the identical `direction_id`, exact
object/revision and compatible ordinary-language stage envelope, but neither
child is a sibling or child of the other. Each owning Root reuses only its own
L1 with `followup_task` while that envelope remains valid and ends or
reauthorizes it at the exact milestone. This is stage-scoped context reuse, not
a direction-lifetime process.

The authority envelope states the direction and stage objective; why the
portfolio is investing; which treatments, comparisons and discriminators EM
may refine; protected variable axes, core hypotheses, claim boundary and
cross-direction isolation; already-authorized Pro/Gemini conversations and
uses; engineering and light-probe bounds; run classes that require a compute
lease; and the exact events that must return to Root. It is an ordinary-language
delegation boundary, not a state machine, ticket, status taxonomy or approval
ledger.

When distinct sessions are used, the cross-root direction channel transfers
exact owner artifacts without transferring child authority. Portfolio sends Operational Root only a meaning-
complete card, science-bearing clarification, Pro-closed revision or
EM-authorized next treatment through `PORTFOLIO_EM_TO_ROOT_CM_REQUEST`.
Operational Root sends Portfolio only a CM scientific-definition ambiguity,
technically accepted result/feasibility packet or request to change a condition
through `ROOT_CM_TO_PORTFOLIO_RETURN`. Each packet must match `direction_id`,
object/revision and owner paths. The receiving Root forwards it unchanged to
its owner child. Wrong-direction material, cross-direction evidence, portfolio
ranking inside a CM return, user requests, shared-resource allocation inside an
EM card, and authority transfer are rejected to the sending Root.

Root issues a direction-scoped heavy-compute lease that names resource limits,
concurrency, validity period and stage boundary. Within that lease CM owns the
production guard, Operator dispatch, environment repair, and retries that do
not change scientific conditions; CM proceeds autonomously for all such
attempts. CM
returns only to expand the lease, resolve a real cross-scope resource conflict,
obtain new user authority, or request a science-bearing change. Light probes
remain inside the envelope when explicitly bounded there.

Each L1 closes its own observation loop and filters reports before its parent
Root sees them. CM owns scope-local CPU, memory, process, restart-risk,
artifact-frontier and Operator facts; EM owns transport-child coordination and
direction-local review/intake facts. Routine `running`, `inflight`,
`pending_init`, PID/RSS/CPU, tab, send-phase, file-exists, retry-progress and
unchanged-state messages remain inside that L1 scope. CM reaches Operational
Root only at its named technical/lease/conflict boundary. EM reaches Portfolio
only at its named science/interpretation/definition boundary. The two Roots
exchange only the exact bounded packets above; code progress and provider page
facts never cross that interface.

At a decision milestone EM sends Portfolio one compact scientific packet:
conclusion, key observation, strongest alternative explanation, claim ceiling,
possible portfolio effect and next discriminator. Portfolio independently
makes the allocation or object-specific experiment decision and sends only its
exact operational action to Operational Root.

When CPU idleness matters for a scoped launch, the initiating CM or other L1
requester measures exactly three actual system-total CPU readings within at
most one minute and makes the within-envelope decision locally. Root receives
only a concrete shared-resource conflict or authority-expansion request, not
the three readings or a routine launch guard.

Delegated children and separated sessions do not routinely write another
semantic owner's specs, handoffs, results,
receipts, runtime observations, environment files, or log entries. Topology may
require relay of an owner-prepared packet, but the receiving child does not rewrite or
mechanically validate it. Hashes, byte counts, CRLF/LF identity, receipt shape,
and float-bit equality are never research gates. The active main Root may write
or integrate any in-scope surface while explicitly acting as its semantic role;
that local collapse never changes the meaning of EM, CM, lease, or provider
evidence.

CM-stage implementation exception: within a CM-owned direction or named
shared-component engineering stage, Root may not collapse substantial,
production-capable, novel, native, exact-arithmetic, or
science-conformance-critical source implementation into the Root or CM role.
Root/CM freeze the remaining implementation and dispatch exactly one registered
Implementer; authority, RNG, exact-arithmetic, and science-conformance semantics
use `hmasd-implementer`/Sol-high, while routine reversible frozen-semantics
engineering uses `hmasd-implementer-terra`/Terra-high. After a coherent
semantics-critical candidate exists, Root/CM dispatch exactly one independent
Reviewer for the named material risk; review is advisory and CM retains final
technical acceptance. Root retains its ordinary umbrella authority outside a
CM-owned stage and for small, bounded, low-risk integration or diagnostic work.

Actual-execution exception: actual train/evaluate/analyze and every leased or
question-relevant command may not be locally collapsed into Root or CM.
Root/CM freeze or relay the exact command, manifest, preflight,
scientific-activity criterion and output paths and dispatch exactly one
registered `hmasd-experiment-operator`; that Operator exclusively launches
once and owns and waits for the foreground process handle through terminal.
Root/CM retain all bounded non-experiment work.

Long-Operator return exception: an Operator command expected to outlast an
ordinary active Codex turn is dispatched by the current Operational Root from
the CM-established run-ready packet, after which Root ends the turn normally.
The external Codex App thread heartbeat is the default return route and targets
that same current Operational Root. Before launch, estimate the minutes from
arming through the next observable terminal or decision boundary, including
prelaunch delay, then select `clamp(ceil(estimate), 15, 60)` minutes; use 30
minutes only when no credible estimate exists. Confirm the current-Root target,
exact watched object and receipt paths, ACTIVE state, and selected 15--60-minute
schedule before dispatch. The same Root task's goal auto-continuation must be
paused or absent while heartbeat coverage owns the wait; goal turns never
substitute for scheduler liveness. `ACTIVE + target + schedule` is configuration
evidence only. After an App/session, target, or heartbeat-configuration change,
one real same-thread scheduled canary must have fired before a long launch. If
any condition cannot be established,
return exact `CONTROL_PLANE_CAPABILITY_BOUNDARY` with `launched=false`; do not
launch. Each scheduled turn performs exactly one bounded check
of the exact native child or its named durable terminal receipt. A nonterminal
check ends normally, may re-estimate the remaining time and update the cadence
inside 15--60 minutes, and leaves the heartbeat ACTIVE. A terminal check
collects the ordinary Operator-to-CM native return through Root. Coverage stays
ACTIVE through CM intake and required owner reconciliation/relay; only then may
Root pause it. `no active Operator` alone is never a pause condition while a
terminal receipt or decision handoff remains unreconciled. Any unrelated Root
turn arriving during coverage must preserve or complete this exact watch before
pausing it.
Never use CPU, file, frontier, partial-value, `functions.exec`, `write_stdin`,
or hidden-loop polling for completion. The heartbeat is an external scheduled
turn trigger, never an event-driven/native-child/orchestrator/subagent wake.
Those surfaces cannot wake an ended Codex task, and signals or receipts carry
execution facts only, never scientific interpretation, acceptance, or
disposition. No heartbeat or observation may relaunch or duplicate a command;
the Operator retains the foreground handle and durable terminal receipt.

Quiescent continuation is not active work. Root classifies every no-immediate-
action handoff as exactly one of `DORMANT_SCHEDULED_CONTINUATION` (an exact
future event has one scheduled owner), `IDLE_COMPLETE` (no unfinished
obligation), or `UNOWNED_STALL` (an unfinished obligation has neither an active
worker nor a valid scheduled owner). Only the last is a workflow anomaly.
Never keep or create a placeholder EM, CM, Operator, or other child merely to
make a task look active. A file-backed `PRESTART` lease with no admitted
activity is a dormant future authorization record, not a current Goal blocker,
worker, process, capacity reservation, or session hold.

Goals cover finite actionable tranches. Do not create a Goal whose only
remaining completion condition is elapsed time or an external event. Finish
the actionable tranche by durably assigning its continuation owner, then leave
Goal mode paused, cleared, or absent until that event becomes actionable. An
already-misscoped blocked Goal is only a local rapid-retry circuit breaker; it
is never project/workflow status and must not be mirrored by the other Root.
If it cannot be paused or cleared through the available product surface, report
`GOAL_HEARTBEAT_INTERLOCK_REQUIRED` once rather than spawning a dummy child or
consuming repeated Goal turns.

The estimate-driven 15--60-minute heartbeat applies to an active or
unknown-duration long effect. A known future time gate with no active process
uses one exact scheduled same-task return at the boundary and no intermediate
polling turns. Every quiescent handoff states `continuity_state`,
`active_worker`, `continuity_owner`, and `next_event`, so `blocked` cannot be
mistaken for abandonment.

The 2026-08-21 ownership migration is prospective and non-disruptive: all in-flight stages continue unchanged to their current exact milestone under their existing EM/CM owners. Do not cancel, restart, reparent, resend, rebind coordinates or suspend a run, definition, provider turn, repair or technical stage merely to install the split. At that milestone, Operational Root stops following up the grandfathered EM; any later science stage is created by Portfolio, while Operational Root may reuse the CM. The exact grandfathered objects and task names are recorded in
`docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_EM_OPERATIONAL_CM_OWNERSHIP_AMENDMENT_20260821.md`.

The VQFP treatment already beyond its activity boundary when this contract was
adopted is grandfathered: do not retrofit its running control flow. After it
naturally terminates, any later VQFP stage uses the direction-stage pair,
envelope and compute-lease contract. SCDMP, CCIC and other new stages use this
contract from their next authorization. Existing logs and scientific evidence
remain unchanged; owner-local logging is direct and never wakes Root by itself.

After any context compaction, interruption, or long mechanical subtask, each
Root reanchors to this file, `.agents/roles/ROOT.md`, and the named portfolio
handoff document before making its owned decision. Reconstruct work from the
maintained diagnosis, frozen plan and append-only logs rather than from recent
child messages. This is a behavioral invariant, not a new approval step or
state machine.

The workspace skill `hmasd-agile-research-development` is disabled. No agent
uses or loads it unless the user explicitly re-enables it in a later request.
