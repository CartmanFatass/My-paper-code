# HMASD Role Router

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
root=current_cli_task
topology=root|optional_domain_manager|optional_specialist_leaf
max_subagent_depth=2
```

A fresh CLI invocation starts as Root. Root reads the current user request,
this router, and `.agents/roles/ROOT.md`. Every other agent reads this router,
its exact assignment, registered Profile, and named Role; it does not load the
Root Role or unrelated owner procedure.

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

Root may directly invoke every registered subagent. A specialist called by
Root is a non-spawning depth-1 leaf; the same specialist may be a depth-2 leaf
under Code Manager or Explorer Manager. Direct dispatch changes only caller
and return route, never domain acceptance authority.

The operational Root alone contacts the user, relays authorized packets across
sessions and directions, performs final Git actions, and allocates shared
compute. The dedicated portfolio session named below may author only the
portfolio sections of shared canonical research state; that exception grants no
Git or user-contact authority. A
stage-paired EM and CM may contact only their named same-direction counterpart
through the bounded direct channel defined below. All other sibling contact is
forbidden. Children remain inside their exact assignment and Role, do not spawn
unless their manager Role explicitly allows it, and never stage, commit, or
push.

The Workflow Recovery Manager is a task-scoped L1 recovery owner, not a
production transport or domain authority. Root or a Code Manager transfers one
`recovery:<incident-id>` when repeated failure, no new evidence, a constrained
observation surface, or cross-file/runtime diagnosis prevents ordinary workers
from completing their assignment. Its Role authorizes isolated worktree repair,
task-scoped runtime control, focused validation, and only assignment-explicit
external actions. It returns only recovery completion or a concrete authority
boundary; routine failure streams do not wake its invoker.

### Mandatory non-core workflow-anomaly route

Use the workspace skill `hmasd-workflow-anomaly-routing` whenever an EM or CM
encounters a non-core provider transport, Agentify/UI observability,
protocol/controller, cross-file workflow-state, runtime-orchestration, or
repeated unchanged-science recovery anomaly. The detecting EM or CM reports
`WORKFLOW_ANOMALY_REPORT` directly to Root, never only to its sibling. Root
must register one task-scoped Terra-high Workflow Recovery Manager before any
fresh direction retry, unless the report is plainly an ordinary CM
source/runner repair. This route preserves the frozen science and exact
provider no-resend boundary; it never turns a workflow anomaly into a
scientific stop, portfolio decision, consumed attempt, or user request.
One root cause and every directly induced workflow consequence remain with the
same recovery owner through follow-up reuse; do not create parallel or serial
replacement recovery tasks merely because a new production-tab, timing, or
other downstream manifestation is observed. A new recovery owner requires
direct evidence of a distinct root cause and disjoint repair scope.
Every Workflow Recovery Manager assignment follows the common contract in
`hmasd-workflow-anomaly-routing`: locate the governing instructions/skill/role
and task context; reproduce safely from direct evidence; inspect the relevant
source, runtime, configuration and tool boundary; freeze a minimal repair and
test plan; repair and run focused validation within authority; then return one
consolidated evidence-bound conclusion. A page/status inspection alone is not
a recovery. Agentify adds its provider/MCP-specific context requirements but
does not replace this general sequence.
For an Agentify/provider anomaly, the Root recovery dispatch must require the
manager to read the complete transport skill and canonical manual, exact
request/incident archives, and relevant current MCP controller/source/runtime
before diagnosis. It must name the task as MCP-controlled browser work and use
only the approved native Agentify registry/DOM primitives; generic browser
assumptions, hidden DOM, ordinary-query fallback and alternate send routes are
forbidden.

### Mandatory portfolio–operational handoff route

Use the workspace skill `hmasd-portfolio-operational-handoff` for every
direction-stage milestone, direction request to Root, or received portfolio
decision. The stable Root-owned anchor is
`docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_OPERATIONAL_RECONCILIATION_20260814.md`;
do not create a competing progress file. EM and CM send each completion,
acceptance, material ambiguity, authority/lease need, or cross-scope conflict
directly to Root using the skill's compact packet, even if the same-direction
counterpart has already received it. Root remains event-waiting while an owner
is active, reports the completed conclusion to the main session, and updates
the anchor in that same turn before any necessary decision-level portfolio
relay. A completed object must never remain described as `pending`, awaiting,
or under review. Portfolio receives only the bounded decision packet; runtime,
partial-result and transport streams remain excluded.

For every project Python command, invoke
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` directly. Do not use bare
`python`, `py`, or `conda run` unless the assignment explicitly requires a
different interpreter.

## Shared Project Scout route

`hmasd-project-scout` is the common read-only Spark lookup utility. Root, Code
Manager, or Explorer Manager may invoke it with `fork_turns=1`. Give one Scout
exactly one narrow factual question. Split independent owners, routes, files,
or evidence families into multiple separate Scout calls and run independent
calls in parallel. Scout output is factual evidence only, never design,
implementation, scientific judgment, technical judgment, review, or acceptance.

If a Project Scout call returns an explicit model quota, rate-limit, traffic,
capacity, or model-unavailable failure, do not retry Spark. The invoking Root,
Code Manager, or Explorer Manager immediately reissues the same one narrow
read-only factual question as a native child with exactly
`agent_type=default`, `model=gpt-5.6-luna`, `reasoning_effort=medium`, and
`fork_turns=1`. This is a transport-capacity fallback only: preserve the exact
scope and factual-output boundary, do not add scientific/technical judgment,
and do not use it for Research Scout, Code Scout, Critic, Innovator, Reviewer,
Verifier, or other professional roles.

## Root research-route invariants

These constraints are automatically reloaded with this router and take
precedence over recent task messages, child status wording, historical workflow
labels, and compacted chat summaries.

### Stable two-session authority split

The dedicated Codex sidebar portfolio session
`019ffc20-5001-7453-a08a-dac783cf4d80` is the active and exclusive owner of
cross-direction scientific discovery, comparison, synthesis and portfolio
judgment until the user changes that session identity. It owns coherent
problem/mechanism-family discovery across directions; provenance-bound
cross-direction comparison and synthesis; redundancy, competition and fusion
assessment; and invest, pause, retire and revisit decisions. It also authors
only the portfolio sections of shared canonical research state. It does not
contact the user, perform Git integration/publication, create or manage
provider conversations, Agentify, browser tabs, CPU/PID/RSS or Operator work,
tests, implementation, single-direction science cards, EM/CM acceptance, or
direction-local results.

The current operational Root is not the portfolio owner while that dedicated
session is active. It creates, reuses and manages direction-stage EM/CM pairs;
issues shared compute leases; coordinates shared tools; handles user
communication; publishes owner-prepared direction artifacts; relays the
bounded packets defined below; and performs necessary final Git integration or
publication. It receives and implements portfolio decisions without redoing
their discovery, comparison or portfolio reasoning. It may continue all
authorized direction-local work, including existing stages and runs, without
waiting for portfolio input. Only a new or changed cross-direction investment,
pause, fusion or priority decision needs the dedicated portfolio session. If an
emergency user instruction conflicts with that boundary, or the portfolio
session is unavailable, operational Root surfaces the choice to the user rather
than silently reassuming portfolio authority.

The minimal interface is decision-level only. L1 owners send their compact
direction-local milestone packet to operational Root. When a cross-direction
judgment is needed, operational Root relays only a provenance-bound packet with
the bounded objective, conclusion, key observation, strongest alternative,
claim ceiling, possible portfolio effect, next discriminator and exact decision
requested. The portfolio session returns only the bounded objective,
conclusion, leading and no-investment decisions, strongest alternatives, claim
ceilings, next discriminator, revisit conditions and exact operational action.
Neither direction has authority to send runtime/status streams, hashes,
receipts, tab state or ordinary direction mechanics through this interface.
When a runtime/resource/engineering fact is decision-relevant, the packet still
states its plain causal meaning, exact scientific unknown and every live
semantics-preserving alternative; it never substitutes a terminal label or
binary child recommendation. In a file-backed cross-session bridge,
operational Root authors a distinct `ROOT_TO_PORTFOLIO` entry and the dedicated
session authors a distinct `PORTFOLIO_TO_ROOT` entry. A later canonical-state
append does not substitute for either provenance record.

Both Roots re-read this router, `.agents/roles/ROOT.md`, and
`docs/research/workflow-runs/2026-08-11_five-round-research-team/CROSS_DIRECTION_PORTFOLIO_HANDOFF_SOL_ULTRA.md`
after compaction or restart before exercising their respective authority. The
dedicated session records portfolio state; operational Root retains its
direction-stage authorities and all historical scientific evidence unchanged.

Single-direction development and cross-direction portfolio research remain one
research graph, but the two sessions own different resolutions. Following a
portfolio decision, operational Root may immediately invoke the selected
direction's EM to make the scientific object meaning-complete and its CM to
assess, construct or run it whenever answer-changing. There is no fixed
direction count, WIP slot or requirement to wait for another direction to
close. Operational Root allocates direction-scoped compute leases around
concrete host resource conflicts; the owning CM schedules actual commands
inside its lease. Resource scheduling never becomes a scientific admission
limit.

For each active promising algorithm direction, Root establishes two independent
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

For Gemini, a click or `sendActionCount` alone is not a submitted provider turn.
Commitment requires a visible user turn and a concrete `/app/<conversation-id>`.
If stable reconciliation instead shows zero provider turns, no conversation ID,
the complete question still in the composer, and no active generation, return
`SEND_NOT_COMMITTED` with `prompt_sent=false` and `response_received=false`,
archive and report that error, then close the tab. Do not retry inside the same
transport call. Within an active direction-stage envelope, the owning EM may
authorize a later fresh-tab attempt for the identical request only when the
prior record proves zero provider turns, no conversation identity and no active
generation. No fixed attempt count has scientific or portfolio meaning. Any
ambiguous commitment or existing provider turn/identity remains permanently
observe-only and must never be resent. Only a genuinely new conversation,
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

Exact provider **no-resend** means only that the same operation/turn identity
may not be submitted again. It never forbids direction continuation,
unchanged-science repair, CM construction, or an EM-authored distinct future
turn when the direction envelope and provider facts make that appropriate. If
an existing turn's commitment is ambiguous, state precisely which operation is
fenced, what remains unknown, which non-sending recovery/observation continues,
and what new Root authority—if any—a distinct future turn would require. Do
not convert the fence into a direction-wide “cannot retry” rule.

Only an explicit user instruction, a Root compute-lease boundary, an
EM-established scientific activity boundary, or a dedicated portfolio decision
may mark a direction/stage as paused. Root writes that scope and reason in the
stable anchor; children may never infer it from their own limitation. Every
report carrying a prohibition or boundary therefore includes `applies_to`,
`does_not_imply`, `continuation_owner`, and `root_decision_class` in addition
to its ordinary evidence fields.

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
invested direction should pause, retire, or stop. This does not weaken exact
provider no-resend after a visible/provider turn or concrete conversation
identity, the science-card activity boundary, complete-panel claim conditions,
or the ban on silent seed/threshold/treatment changes. Provider transport
failure cannot pause a scientific direction. A resource slice may pause only
its lease; CM owns semantics-preserving same-coordinate, blinded, atomic
continuation until complete question-relevant data exist.

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

- EM owns the scientific question, meaning-complete science card, comparator,
  observable, activity-start criterion, interpretation, claim ceiling, and
  next discriminator;
- CM owns assignment-scoped source, tests, runner, worktree contents,
  temporary files, environment, launcher, ABI/resource work, unchanged-science
  repair/retry, Operator dispatch, and retained-result installation;
- Operator owns execution facts and returns failures to CM without scientific
  interpretation;
- transport owns page mechanics and raw External-Pro response capture;
- the actor that performed an action owns the truth of its append-only log
  event;
- the dedicated portfolio session owns problem-family discovery and screening,
  portfolio allocation, cross-direction comparison/synthesis and portfolio
  sections of canonical research state; operational Root owns user contact,
  provenance-bound relay, shared-resource allocation and necessary final Git
  integration/publication.

## Direction-stage L1 delegation

For each invested direction stage, Root creates or reuses a paired
`EM_<direction>` and `CM_<direction>`. Both assignments contain the identical
`direction_id`, the same ordinary-language direction-stage authority envelope,
and the counterpart's canonical task name. Root delegates through the next
decision-level scientific milestone, reuses the same L1 pair with
`followup_task` while that envelope remains valid, and ends or re-authorizes the
pair at the milestone or when the direction is paused. This is stage-scoped
context reuse, not a direction-lifetime process.

The authority envelope states the direction and stage objective; why the
portfolio is investing; which treatments, comparisons and discriminators EM
may refine; protected variable axes, core hypotheses, claim boundary and
cross-direction isolation; already-authorized Pro/Gemini conversations and
uses; engineering and light-probe bounds; run classes that require a compute
lease; and the exact events that must return to Root. It is an ordinary-language
delegation boundary, not a state machine, ticket, status taxonomy or approval
ledger.

The same-direction direct channel transfers owner-authored work without
transferring authority. EM may send CM only a meaning-complete science card, a
science-bearing clarification, a Pro-closed revision, or an EM-authorized next
treatment inside the envelope. CM may send EM only a scientific-definition
ambiguity, a technically accepted result packet, or a request to change a
condition that could affect already observed data. Each message must match both
owners' `direction_id` and named counterpart. Wrong-direction messages,
cross-direction material or evidence, portfolio rankings, user requests,
shared-resource allocation, and scientific or technical authority transfer are
rejected and returned to Root. Cross-direction relay remains Root-only and
provenance-bound.

Root issues a direction-scoped heavy-compute lease that names resource limits,
concurrency, validity period and stage boundary. Within that lease CM owns the
production guard, Operator dispatch, environment repair, and retries that do
not change scientific conditions; CM proceeds autonomously for all such
attempts. CM
returns only to expand the lease, resolve a real cross-scope resource conflict,
obtain new user authority, or request a science-bearing change. Light probes
remain inside the envelope when explicitly bounded there.

The initiating L1 owner closes its own observation loop and filters reports
before anything reaches Root. CM owns scope-local CPU, memory, process,
restart-risk, resource, artifact-frontier and Operator facts; EM owns its
transport-child coordination and direction-local review/intake facts. Their
leaves return to that L1, not directly to Root. Routine `running`, `inflight`,
`pending_init`, PID/RSS/CPU, tab, send-phase, file-exists, retry-progress and
unchanged-state messages remain inside the L1 scope. The L1 returns to Root only
when the core mechanism is supported, contradicted or non-identified; the claim
ceiling or strongest alternative changes materially; another direction creates
competition, absorption, fusion or a joint hypothesis; no valuable successor
remains; the envelope or resource need is exceeded; a new provider conversation,
external authority or user decision is required; or final Git/canonical
integration is needed. Code completion, focused checks, environment repair,
preactivity/no-data engineering failures, unchanged-science retries, Operator
launch/wait/terminal/install facts, provider page/wait facts, the first explicit
noncommit recovery, ordinary Pro revisions, owner logs and local handoffs stay
inside the L1 pair. A high CPU reading, an ordinary wait or retry, and a tool
timeout are not Root escalation conditions by themselves.

At a decision milestone EM sends operational Root one compact scientific packet:
conclusion, key observation, strongest alternative explanation, claim ceiling,
possible portfolio effect, next discriminator and the exact operational decision
requested. It omits runtime and transport streams. Operational Root relays it
to the dedicated portfolio session only when its requested decision is
cross-direction; that session independently makes the portfolio judgment.

When CPU idleness matters for a scoped launch, the initiating CM or other L1
requester measures exactly three actual system-total CPU readings within at
most one minute and makes the within-envelope decision locally. Root receives
only a concrete shared-resource conflict or authority-expansion request, not
the three readings or a routine launch guard.

Root does not routinely write another owner's specs, handoffs, results,
receipts, runtime observations, environment files, or log entries. Topology may
require Root to relay an owner-prepared packet, but Root does not rewrite or
mechanically validate it. Hashes, byte counts, CRLF/LF identity, receipt shape,
and float-bit equality are never Root research gates.

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
