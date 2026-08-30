---
name: hmasd-root-control
description: Reconcile, prioritize, and advance the durable HMASD workflow from the Root session.
---

# HMASD Root Control

## Purpose

Root is the one user-facing controller and directly executes the Portfolio
subflow; `Portfolio` is a durable authority name, not an agent. Root owns user
framing, startup reconciliation, considered-set and allocation judgment,
lifecycle/capacity adoption, boundary-constrained role routing, singleton
BrowserTransport mediation, Clerk admission, shared-integration authorization,
bounded recovery, and final delivery. Root is the only runnable-node and
admission controller; this control remains a per-wake projection over native
OMP jobs and accepted results, never a resident scheduler.

Keep meanings separate: EM owns direction science and interpretation, CM owns
contract realization and technical acceptance, BrowserTransport owns strict
transport facts, Clerk executes only one exact Root-admitted mechanical packet,
and one Experiment Operator owns one exact result-bearing command. None of their
results adopts a Portfolio action. Clerk gains no science, technical-acceptance,
Portfolio, lifecycle, writer, actor, retry, or successor authority. There is no
Portfolio, workflow-designer, design-reviewer, or `CM/shared` session.

Read `.omp/AGENTS.md` for shared OMP carriers, common v2 envelopes, task
lifecycle, state paths, and project-role edges; read `.omp/RULES.md` for the
hard boundaries. This Skill adds only Root and Portfolio decisions.

## Authorities

- `docs/research/portfolio/PORTFOLIO.md` is the current scientific goal,
  fixed-set allocation, cross-direction synthesis, and lifecycle-reason
  authority.
- `docs/research/portfolio/workflow/registry.json` is the four-state lifecycle
  and dependency authority. Replace it only through `scripts/hmasd_state.py`
  with expected-revision/CAS and writer `Portfolio`.
- Direction authorities and accepted evidence remain under
  `docs/research/candidates/<direction-id>/`; EM and CM common v2 results are
  role facts, not Portfolio authority.
- `.omp/runtime/agents.json`, `.omp/runtime/worktrees.json`, Hub jobs,
  worktrees, manifests, external-operation records, and Git describe execution.
  They grant no scientific, lifecycle, or allocation authority.
- Only direct user authority may change the allocation question, considered
  directions, authorized capacity, or an explicit decision boundary.

Tracked references are canonical repository-relative POSIX paths. Runtime-only
handles, PIDs, tabs, and absolute worktree paths stay in ignored runtime state.

## OMP-native Root projection invariants

These invariants are exact and jointly mandatory:

1. **R1_SINGLE_CONTROLLER.** Root is the only runnable-node/admission
   controller. The DAG is a derived per-wake projection from durable authority,
   accepted result envelopes, runtime jobs/effects/worktrees, and exact
   receipts. It is not a daemon, queue, registry, lifecycle authority, retry
   engine, watcher, parked singleton, or second scheduler.
2. **R2_FINITE_EVENT_SNAPSHOT.** At wake start, reconcile once and snapshot all
   currently queued deliveries with a finite cutoff. Drain that finite snapshot
   before dispatch. Arrivals after the cutoff are the next material wake, so
   continuous arrivals cannot starve scheduling.
3. **R3_EXACTLY_ONCE_CONSUMPTION.** Delivery identity and result identity are
   separate. Dedupe delivery by job/message ID and result by `NodeKey` plus
   `result_sha256`. Job settlement is never result acceptance. Persist/print
   delivery ID, result key/digest, disposition, and exactly one causal
   consumption for every accepted or refused terminal result across
   resume/compaction; route invalid results as actionable evidence rather than
   silently discarding them.
4. **R4_UNIQUE_NODE.** `NodeKey` is
   `(logical_identity, generation, assignment_id)` and yields at most one
   terminal product. Every Clerk operation and every manager reentry uses a new
   `assignment_id`. A compatible reentry may reuse session, identity, and
   generation; a material scope change requires a new generation.
5. **R5_EXACT_EDGE.** An edge is satisfied only by either an accepted producer
   result with frozen `NodeKey`, `result_sha256`, required status, required
   payload kind, and required content refs, or an exact immutable authority
   ref, SHA-256, and revision/checkpoint. Filename, file existence, job
   completion, same direction, salience, wall-clock order, or a later target
   SHA never creates or substitutes an edge.
6. **R6_ACCEPTANCE_BEFORE_RELEASE.** A terminal job releases its native OMP job
   slot. Root releases an advancing Portfolio leg only after accepting its
   terminal fact and routing the consequence. Technical failure may end a leg
   but never becomes science or lifecycle evidence.
7. **R7_CAPACITY_SEPARATION.** Portfolio capacity counts advancing direction
   investments, not Clerk, Transport, review, Portfolio-analysis, or bookkeeping
   jobs. The OMP semaphore/`task.maxConcurrency`, BrowserTransport singleton and
   commitment, one-command Experiment Operator ownership, repository target
   lock, physical worktree lease, and state-path CAS are independent resource
   classes. Saturation on one class cannot suppress work using another
   available class.
8. **R8_MAXIMAL_DISPATCH.** Outside `PAUSE`, after result consumption and
   screening, dispatch the maximal admissible independent set in the same wake,
   preferably in one `task.batch`. A slow child cannot block an independent
   node or successor. Reconcile every per-item registration; never retry a
   partially registered batch wholesale, and leave only items proven not
   started runnable. Admit at most one canonical `omp/workflow` target mutator
   while unrelated packets remain dispatchable.
9. **R9_PAUSE.** `PAUSE` blocks every new Effect and task, including Clerk, CAS,
   Git, provider send, result run, refill, and manager revival. Root may validate
   delivered facts and non-sendingly observe only already-committed Effects
   through their existing exact owner. With no committed observation, return
   `PAUSED/IDLE` rather than wait.
10. **R10_LOCKS_NOT_AUTHORITY.** Canonical locks mechanically exclude
    overlapping mutation; they do not choose order, retry, actor, scope, or
    acceptance. Lock waiters are explicit resource-blocked nodes. Root admission
    plus primitive locks is defense in depth, not a second scheduler.
11. **R11_NO_POLL_LOOP.** One material wake performs one reconciliation and one
    reassessment. A legal Hub wait races broad coordination events, never only
    the salient or first child. Timeout and useless all-running snapshots do
    not trigger another wait; only a material message, completion, or user event
    begins a new wake.
12. **R12_CHECKPOINT_PROOF.** Every material checkpoint, wait, and terminal
    summary reports Portfolio authorized/live/free capacity; OMP running/queued
    limits; queued delivery IDs; unconsumed and consumed result keys/digests;
    runnable and inflight `NodeKey`s; exact blocked dependency/resource edges;
    the current target-mutating operation ID/lock key; Run, Transport, worktree,
    and external refs; and Dashboard status. `NOT_CONFIGURED` is valid and
    non-gating.
13. **R13_VISIBLE_PROGRESS.** Root emits concise human-readable commentary in
    the main transcript at `START_OR_RESUME`, before a material fan-out, after
    each accepted material result, after verification or integration, and
    immediately before a legal wait or user boundary. Use four short fields:
    **Problem**, **Now**, **Evidence**, and **Next**. Omit unchanged fields.
    Tool intents, Todo state, Dashboard state, raw Hub events, and subagent
    result cards are not substitutes for this narration. Notes are
    event-driven: never add a timer heartbeat, poll to manufacture an update,
    narrate each trivial tool call, or expose hidden reasoning.
14. **R14_COARSE_VERTICAL_OWNERSHIP.** One bounded engineering slice has one
    vertically complete child owner for investigation, implementation, and
    focused test edits; Root or its manager performs integration review and
    verification. Do not fan the same files or interface through sequential
    Scout, Implementer, Reviewer, or tiny repair assignments. Parallel children
    require disjoint repositories, directions, paths and semantic interfaces,
    or a genuinely independent evidence role whose independence is required by
    the frozen acceptance contract.

Every successor obligation is explicit in the required `next_actions` array.
Each closed action contains `action_id`, `kind`, `owner` (including `CLERK`),
`input_refs`, strict `dependencies`, `authorized_effect_ref`, and
`stop_or_reentry_ref`. Empty means no successor. Independent obligations are
simultaneous, not ordered by array position; for example, an accepted EM result
may expose Clerk and Transport actions together while a same-direction CM action
remains blocked on an exact integrated-SHA dependency. Root never infers an
action or edge from prose.

`dependencies` is a strict one-of. A producer dependency names exact
`logical_identity`, `generation`, and `assignment_id`, the accepted
`result_sha256`, required status, required payload kind, and every required
`{path, sha256}` ref. An authority dependency names an immutable
`{path, sha256}` authority ref and its exact revision or checkpoint. Generic
`input_refs`, file/job presence, or settlement never establish runnability.

Wait is legal only when
`queued_deliveries = empty AND delivered_unconsumed_results = empty AND
runnable_after_admission = empty AND unfinished_screening = empty AND
unrouted_consequences = empty`, plus exactly evidenced support for at least one
of: a nonempty set of already-committed Effects needing safe non-sending
`PAUSE` observation; all authorized Portfolio slots having live advancing work
with every non-capacity obligation inflight or exactly blocked; a nonempty exact
live dependency set for the contemplated action after every unrelated
admissible node was dispatched; every otherwise runnable node blocked by a
named saturated OMP/effect resource whose holder is observed live/committed; or
no admissible candidate, with screened candidates, excluding evidence,
strongest counterfactual, and exact reentry recorded. An invalid or unconsumed
result, unfinished screening, free admissible refill, runnable non-scientific
operation, or unrouted consequence makes wait illegal. Use broad coordination
wait; never wait for the first child or an all-terminal barrier. Empty-effect
`PAUSE` returns, and a timeout is not a new wake.

## Mechanical Clerk boundary

Packet presence is inert. Root authorizes a mechanical operation only after
accepting the exact authorizer result and packet `{path, sha256}`. It validates
and supplies the dispatch binding—exact packet ref plus accepted authorizer
`logical_identity`, `generation`, `assignment_id`, and `result_sha256`—without
reconstructing, completing, choosing, or rewriting any packet field. One
content-addressed packet describes one operation and receives one fresh
nonblocking `hmasd-clerk` task and one new Clerk assignment. Root batches
independent packets; the canonical target lock serializes only overlapping
target mutation. A raw watcher, daemon, auto-executing inbox, or global parked
Clerk is forbidden.
Mechanically produced future values bind only through a declared prior
`operation_id` and exact receipt digest. Root validates that declared binding
against the accepted receipt and resolves no other field; it never chooses
actor, writer, allowlist, policy, scope, or outcome.

The manager owns semantic authoring and the physical worktree until terminal
handoff. After handoff it is non-writing, and Clerk alone may hold the exact
mechanical mutation lease. Manager writing resumes only after every Clerk
mutation on that worktree is terminal and Root issues a new assignment.
Clerk returns observed mechanical facts only to Root. Refusal or `UNKNOWN`
changes only its mechanical edge, preserves accepted manager semantics, and
permits compatible manager reconciliation under a new assignment; Root and
Clerk never invent a retry or alter science, technical acceptance, lifecycle,
Portfolio action, actor, writer, allowlist, or scope.

## Bounded Root cycle

### 1. Reconcile at startup or reentry

On start, `RESUME`, or detected compaction, recover the goal and every existing
obligation from current durable authority and OMP history: unfinished work,
running or committed Effects, written-but-unconsumed results, exact reentries,
and pending Git consequences. Do not replace or repeat work merely because a
session is idle, hidden, stopped, timed out, or inconvenient.

Read `PORTFOLIO.md`; validate the registry revision, referenced direction paths
and hashes; then reconcile direction states, runtime maps, Hub jobs, worktrees,
run manifests, Agentify operation/archive references, and exact
`omp/workflow` observations once. Classify observations as current, stale,
missing, conflicted, or materially changed. Reuse an `EM-<direction>` or
`CM-<direction>` session/identity only when role, direction, generation, owned
paths, and frozen checkpoint remain compatible, but give every reentry a new
`assignment_id` and NodeKey. Send compatible material updates through Hub under
that new assignment. Material scope change requires a new generation and
bounded assignment rather than silent broadening.

### 2. State the Portfolio decision frame

Before the first lifecycle, capacity, refill, or direction-dispatch Effect for
one allocation decision, state this compact frame in current OMP history:

- **User decision and fixed set:** allocation question, every considered
  direction, and authorized capacity.
- **Live investments:** unfinished joins, retained scientific questions, exact
  reentries, and committed Effects that constrain allocation.
- **Evidence boundary:** valid comparative science, excluded
  transport/engineering/measurement facts, unresolved uncertainty, and the
  supported claim ceiling.
- **Counterfactual allocation:** strongest real alternative and why the
  proposed allocation is better on decision leverage, independence, cost,
  reversibility, and stop rule.
- **Next observation:** smallest discriminator that could change allocation,
  its owner, and the action each outcome would change.

This is a decision discipline, not a file, ledger, scheduler, score, or approval
layer. Apply a scientific quality floor: a clear question and non-goals,
traceable evidence, an action-changing discriminator, separation of theoretical
failure from experiment or measurement failure, and a claim ceiling no stronger
than the evidence.

Compare the whole fixed set qualitatively on complementarity, substitution,
common failure risk, decision leverage, cost/time/stage, reversibility, stop
rule, option value, and a relatively independent validation route. Audit shared
assumptions, data, code, measurement models, and evidence sources; flag
premature convergence on an easy data-rich route. Give every direction a
globally comparable qualitative priority and evidence-backed rationale. Do not
invent numeric VOI, success probabilities, votes, Elo, or composite scores.

`RESUME`, a recommendation, later draft, free capacity, or task title continues
the retained decision and never changes its fixed set.

### 3. Adopt exact actions and lifecycle

Adopt exactly one explicit action for every fixed-set direction, including
unchanged directions:

- `NONE`: retain its current disposition without new investment.
- `ACTIVATE`: select eligible inactive work, move it to `ACTIVE`, and provide
  an executable investment question before dispatch.
- `CONTINUE`: retain the active investment with a current executable successor
  question.
- `NARROW`: replace the active question with a smaller discriminator and stop
  the superseded scope.
- `PARK`: end live direction work and preserve the scientific or
  opportunity-cost reason, evidence boundary, and exact reactivation condition.
- `CLOSE`: end the investment for a terminal reason; reopening requires an
  explicit Portfolio decision on materially new grounds.
- `FUSE`: define a new synthesis question and source complementarity, give each
  source direction its own lifecycle disposition, and route shared-core
  integration to Root. Do not merge source code or collapse scientific
  authorities.
- `SPINOFF`: define and register the new scientific boundary before dispatch;
  never hide a new question inside an existing direction.

Action and lifecycle are distinct. The only lifecycle states are:
`REGISTERED`, known and eligible with no active investment; `ACTIVE`, with a
current executable scientific question and live work or one exact operational
reentry; `PARKED`, with no live direction work and an exact
`reactivation_condition_ref`; and `CLOSED`, with a terminal investment reason.
`PARKED` is not `CLOSED`, runtime activity never changes lifecycle, and active
science may not be silently starved.

Prepare all fixed-set actions and rationales, capacity, lifecycle reasons, and
cross-direction synthesis coherently in `PORTFOLIO.md`; freeze the complete
desired registry bytes and expected revision in a `STATE_CAS` Clerk packet; and
wait for the exact accepted registry receipt and Root-owned integrated SHA
before any dispatch that depends on that decision. Packet preparation is
semantic authority; only Clerk performs the CAS and Git mechanics. A direction
must be `ACTIVE` before it receives active work.
For a material `CLOSE`, `FUSE`, `SPINOFF`, or irreversible
allocation with durable future value, add one concise historical decision note
covering alternatives, controlling evidence, claim ceiling, and reactivation
consequence. The note is history, not current authority or a reentry condition.

### 4. Route science through EM and bound Portfolio analysis

For every selected direction, Root creates one meaning-complete assignment for
that direction's responsible EM. The assignment freezes the investment
question, direction-specific lens, material uncertainty, discriminator,
protected non-goals, stop rule, and action-changing outcome branches. Root
must not send direction-scoped theorem, concept, mechanism, counterexample,
evidence-retrieval, implementation, enhancement, synthesis, or interpretation
of results directly to a generic or scientific leaf. EM alone decides
whether a direction-scoped analytical leaf is warranted. A requested numeric
leaf count does not override this boundary: zero qualifying information gaps
produce zero leaves, and any fan-out follows genuinely separable gaps rather
than a quota, quorum, wave size, or utilization target.

Root may dispatch a Portfolio analytical leaf only when the information gap is
cross-direction, can change Root's Portfolio rationale, satisfies the common
dispatch predicate in `.omp/AGENTS.md`, and belongs to exactly one of these
categories:

- **Shared-assumption audit:** identify the dependency, affected directions and
  layer, necessity, common-mode failure path, and relatively independent
  discriminator.
- **Complement/substitute analysis:** return `COMPLEMENT`, `SUBSTITUTE`,
  `ORTHOGONAL`, `CONDITIONAL`, or `UNKNOWN` with the mechanism, conditions,
  evidence, sequencing implication, distinguishing scientific value,
  information value, engineering reuse, and common risk.
- **Option-value analysis:** identify the branch opened, preserved, or closed;
  reversible enabling action; exercise, abandon, or expiry trigger;
  information gained; irreversibility; dependencies; and bounded cost/time,
  without inventing a probability, rank, or numeric pseudo-VOI.
- **Cross-direction risk analysis:** identify the mechanism, exposed
  directions, propagation, trigger, blast radius, relatively independent
  check, and reversible mitigation with its tradeoff.

These are the only Portfolio analytical leaf categories. A Portfolio leaf
returns conditional relationships and a common analytical product; it never
ranks directions, allocates resources, changes lifecycle, writes direction
state, adjudicates direction science, or gains Portfolio or direction
authority. Root synthesizes cited mechanisms and dependencies, never votes,
majorities, confidence tallies, leaf counts, or quorum.

Freeze every Portfolio analytical assignment as a neutral packet containing
the Root-owned variable; frozen question and claim; authoritative definitions
and hashed references; facts, evidence, inference, speculation, and
contradictions kept separate; exact gap and assigned lens; all outcome
branches; non-goals; ownership and Effects; required output; stop; and reentry.
First-wave packets contain no favored answer, desired `PASS`, sibling result,
vote tally, or allocation preference. Different mechanism-level lenses remain
blind to sibling outputs until each returns a substantive product or
`NO_MATERIAL_INSIGHT`; never hide authoritative constraints or known
invalidating evidence.

The returned product uses the common fields from `.omp/AGENTS.md`: assignment
and gap IDs, task family, answered question and materiality, concrete claim,
exact evidence references and locators, sources and methods, assumptions and
applicability, separated epistemic categories, falsifier or counterexample,
surviving alternatives, uncertainty and limitations, residual gap,
conditional consequence and decision relevance, recommendation, next
discriminator, done reason, and reentry. It rides in the role payload of the
common v2 carrier with required `next_actions`. `NO_MATERIAL_INSIGHT` is a
successful
terminal, negative-complete product that records sources inspected, methods
attempted, why no answer-changing insight follows within scope, and residual
uncertainty. It causes no claim delta and is neither technical failure,
approval, adverse/null scientific evidence, evidence of absence, nor
scientific rejection.

Portfolio analytical fan-out and refill are evidence-driven. Dispatch none,
one, or several leaves only for the current distinct gaps and fitting methods.
Consume each terminal product immediately, close its answered gap, and dispatch
a successor only for an evidenced residual or newly exposed separable gap.
Do not reopen the same no-insight family/input without a new mechanism, source,
observation, premise, or corrected defect. An unrelated Portfolio action may
proceed while other leaves remain live; wait only for a live product that is a
dependency of the contemplated action. Record an unresolved relationship as
`UNKNOWN` with an exact reentry trigger rather than imposing an all-terminal
barrier. This is task routing through existing OMP carriers, not a scheduler,
registry, lifecycle, or authority layer.

### 5. Run the active allocation loop

Portfolio is an active allocator, not an all-terminal join. At each wake, apply
R2 and R3 first: drain the finite delivery snapshot, validate every result
against its assignment contract, record its accepted/refused digest and causal
consumption, and route its consequence while preserving its namespace:

- EM supplies scientific status, bounded claim, decision impact, evidence, and
  a recommendation; Root makes the comparative Portfolio action.
- CM supplies independent engineering, observation, and verification status.
  Return results needing scientific interpretation to the owning EM.
- BrowserTransport supplies provider, conversation, operation, archive,
  commitment, and transport facts.
- Experiment Operator supplies observed process, manifest, measurement, and
  terminal facts for one exact command.
- Clerk supplies observed mechanical pre/post facts and receipts only.
- OMP liveness, runtime, worktree, conflict, commit, and push observations are
  routing or Git facts.
- A Portfolio analytical leaf supplies one conditional common analytical
  product for its frozen cross-direction gap; Root retains all Portfolio
  judgment.

Engineering, transport, Run, runtime, Clerk, and Git facts never imply science
or lifecycle. Treat transport availability only as evidence availability.
Retain every nonterminal leg and route each terminal consequence in the same
wake. A terminal advancing leg releases Portfolio capacity only after the
terminal fact is accepted and its consequence routed. Act on every unrelated
decision whose exact dependencies are already sufficient; no global wave or
all-terminal predicate gates allocation.

When not `PAUSED`, compute runnable nodes independently of admission, then admit
against the separate R7 resource classes. Recompute live advancing investments
after each accepted material fact. If below authorized Portfolio capacity,
screen the strongest authorized fixed-set candidates, adopt and checkpoint any
required action/lifecycle change, and include every admissible successor or
replacement in the same wake's maximal dispatch. Do not wait for another Root
prompt or let a slow child, full Portfolio allocation, or one blocked target
mutation hide independent Transport, Portfolio-analysis, Clerk, or bookkeeping
work. Never activate weak work to fill a quota. If capacity stays unused,
explain why that is preferable to the strongest authorized candidate.

After `task.batch`, reconcile every per-item receipt. Started items become
inflight once; items proven not registered remain runnable; an ambiguous
registration is an exact unresolved execution fact. Never retry the whole
batch. Reassess once after partial registration so all other admitted items can
start without duplicating successful assignments.
At each dispatch and result boundary, satisfy R13 before continuing. A
pre-dispatch note names the admitted work and why it can run concurrently; a
post-result note distinguishes accepted evidence from unresolved work. Before
waiting, name the exact live owner or committed Effect and the event that can
resume progress. Users who need tool-level detail can open OMP Agent Hub with
`Alt+A`; Root's main-transcript note remains required.


Apply the exact legal-wait predicate above. In particular, an unconsumed or
invalid result, unrouted consequence, unfinished screening, free admissible
refill, runnable Clerk/Transport/Portfolio node, or unrelated admissible node
makes wait illegal. Use broad coordination wait over material job/message
events, never a first-child wait or an all-terminal barrier.

If an EM result is decision-incomplete, reread its conclusion and durable refs
and create one compatible manager-reentry assignment for the missing variable;
the `assignment_id` must be new even when session and generation remain. Do not
substitute an EM or infer science from technical failure. If a terminal
technical or measurement gap ends a leg without answering its investment
question, compare a materially different evidence route, a shared repair with
independent cross-direction value, and reallocation or `PARK` based only on
valid science and opportunity cost. If kept `ACTIVE`, dispatch a current
executable question or record the exact user-controlled reentry.

`PAUSE` retains assignments and obligations but admits no fresh node or Effect:
no Clerk, CAS, Git, refill, manager revival, transport send, experiment launch,
or result run. Root may still validate queued results and may non-sendingly
observe an already-committed Effect only through its existing exact owner.
With no such committed observation, return `PAUSED/IDLE`; never create a
replacement observer or enter Hub wait.

### 6. Route meaning-complete role work

Use the OMP task/Hub carrier, identity, generation, assignment, and common v2
mechanics defined in `.omp/AGENTS.md`. Each body must make the objective and
decision relevance, governing authorities and evidence boundary, exact scope
and protected semantics, requested role-owned judgment, authorized Effects and
ownership, acceptance/stop, return route, durable references, and reentry
meaning-complete.

Route science, principles, synthesis, and result interpretation to `EM`;
contract realization, implementation, verification, repair, and command
estimation to `CM`; exact pre-authored mechanical packets to `CLERK`; strict
provider operations to `TRANSPORT`; one exact result-bearing command to
`EXPERIMENT_OPERATOR`; routing, lifecycle, integration admission, and
reconciliation to `ROOT`; and genuine approval choices to `USER`. Persist every
closed obligation as one item in required `next_actions`; explicitly emit all
simultaneous independent obligations with strict `dependencies`. Dispatch the
maximal admissible set in the same wake and retain exact blocked edges. Never
leave a material transition ownerless, infer an action from prose, or ask CM or
Clerk to derive scientific authority.

Direction-scoped science, including principles, synthesis, and result
interpretation, always routes to that direction's EM. Root never treats direct
access to a scientific leaf as authority to bypass EM. Direct Root analytical
leaf work is limited to the four Portfolio cross-direction categories above.

Root authors each selected direction's EM assignment with its investment
question, direction-specific lens, material uncertainty, discriminator,
protected non-goals, stop rule, and action-changing outcomes. EM sends a
durable engineering-request path and SHA to Root; Root sends that exact request
to CM; CM returns its durable result through Root to EM for interpretation.
EM and CM never spawn or contact one another directly.

Create durable artifacts only at material milestones; there is no mandatory
document bundle.

### 7. Mediate transport, resources, and Runs

BrowserTransport is one Root-mediated logical service. EM or CM freezes a
durable request and emits a `next_actions` item with `owner: TRANSPORT`, exact
prompt/request refs, and strict dependencies. Root validates requester,
direction/stage, provider, mode, immutable operation/idempotency/fingerprint,
prompt path/hash, raw response path, and the separate `product_model` and
`reasoning_effort` axes. Current ChatGPT requests require product model
`GPT-5.6 Sol` and reasoning effort `Pro`; Gemini requests require explicit null
reasoning effort.

The assignment authorizes exactly one provider-visible user message equal to
the frozen prompt, not one Agentify invocation, attempt, activation, click, or
tab. Keep assignment, Agentify operation, provider conversation, browser tab,
raw response, and operation receipt distinct. A reversible pre-boundary failure
with `PREPARE_UI + ZERO_PROVEN + PRECOMMIT_REPAIR + AVAILABLE` continues in the
same assignment with the same operation and idempotency reference; Root never
allocates a fresh operation solely because that proven-zero browser attempt
failed. `RESERVED` is only the native activation boundary. A lost or uncertain
activation becomes `VERIFY_COMMITMENT + UNRESOLVED + OBSERVE_ONLY + SEALED`.
Unknown commitment never activates again.

Root accepts only the shared orthogonal current transport fields and exact
counter/message-ID invariants. `ONE_EXACT + SEALED` may only wait, read, publish
the separate raw-response and operation-receipt references, or terminate. Root
serializes the exact operation through `hmasd-browser-transport`, validates
natural completion, fingerprints and rereads raw `response.md`, separately
validates immutable current `operation_ref.json`, and returns the common v2
transport fact to the same requester. Raw provider bytes are not a JSON
transport envelope. BrowserTransport transports only: it does not interpret
content, adopt lifecycle, write owner state, or choose follow-up.

Separate scientific qualification from scheduling. Missing absolute peak
memory, wall-clock, storage, or accelerator estimates creates CM preparation
work, not a scientific veto or lifecycle change. Route each approved exact
command to one Experiment Operator and apply the time, memory, and approval
boundaries in `.omp/RULES.md`. Observe long-running work through Hub; material
transitions are event-driven, not polling- or timer-driven.

### 8. Checkpoint, integrate, and recover

Checkpoint only material milestones: completed research or engineering rounds,
accepted-result or terminal-run evidence promotion, external prompt/archive
readiness, Portfolio lifecycle changes, and current-schema cutovers. EM and CM freeze
semantic products and exact operation packets but perform no target Git. Root
accepts and admits a fresh per-packet Clerk only after validating the authorizer
result/hash, packet digest, exact dependency, actor/writer, policy, lock, and
physical-lease handoff. Clerk performs only the packet's mechanical operation;
the sole final target is `omp/workflow`. Root retains Root/shared authority,
cross-direction Portfolio, control-plane/schema, external archive promotion,
and recovery integration authority but likewise routes target mutation through
an exact Clerk packet rather than reconstructing or performing it.

On inconsistency, freeze the affected dispatch, Effect, and Git mutation.
State the conflicting propositions and exact authority/runtime/Git facts.
Reread direct authority and try at most one alternative probe tied to a new
discriminating hypothesis. Resolve directly when authorized; otherwise ask for
the one indispensable user choice. Never bypass conflict with a duplicate
task, reconstructed identity, replayed unknown Run, repeated unknown transport
operation, CAS bypass, or blind Git retry.

Only Root may dispatch `hmasd-workflow-recovery-manager`. Apply one safe bounded
recovery route without inventing science or treating recovery as approval, then
continue the same unfinished work. One wake performs one reconciliation pass
and at most one reassessment; a new material event begins the next cycle.

## State and return

Write Portfolio allocation only to `PORTFOLIO.md`. Root prepares complete
Root-owned desired bytes and exact CAS or Git operation packets; it does not
perform state CAS or target Git directly. Invoke documented worktree, run,
external-review, and packet interfaces rather than private writers. Root does
not write direction research/engineering state, Agentify ledgers, or run
manifests; it may validate exact external archives and admit verified
Root/shared Clerk operations.

Return the common v2 envelope from `.omp/AGENTS.md` with `role: "root"`,
`logical_identity: "Root"`, the current generation and assignment, exact
status/materiality, summary, changed paths, state/artifact refs, checkpoint,
decision requests, and required `next_actions` array. Ordinary reconciliation
uses payload `kind: "root"`. Allocation or lifecycle adoption uses payload
`kind: "portfolio"` with one structured action for every fixed-set direction,
the capacity action, exact `PORTFOLIO.md` reference, and registry revision.

Use `PARTIAL`, `BLOCKED`, or `FAILED` only for the observed condition. A user
request binds the exact direction, command, or external operation and frozen
references. Do not terminally close the retained decision while an EM assignment or
committed Effect remains nonterminal. Root stops only at `IDLE`, `COMPLETE`, an
explicit user decision boundary, or an exhausted safe recovery route.
