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
BrowserTransport mediation, shared integration, bounded recovery, and final
delivery.

Keep meanings separate: EM owns direction science and interpretation, CM owns
contract realization and technical acceptance, BrowserTransport owns strict
transport facts, and one Experiment Operator owns one exact result-bearing
command. None of their results adopts a Portfolio action. There is no Portfolio,
workflow-designer, design-reviewer, or `CM/shared` session.

Read `.omp/AGENTS.md` for shared OMP carriers, common v1 envelopes, task
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
  `docs/research/candidates/<direction-id>/`; EM and CM common v1 results are
  role facts, not Portfolio authority.
- `.omp/runtime/agents.json`, `.omp/runtime/worktrees.json`, Hub jobs,
  worktrees, manifests, external-operation records, and Git describe execution.
  They grant no scientific, lifecycle, or allocation authority.
- Only direct user authority may change the allocation question, considered
  directions, authorized capacity, or an explicit decision boundary.

Tracked references are canonical repository-relative POSIX paths. Runtime-only
handles, PIDs, tabs, and absolute worktree paths stay in ignored runtime state.

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
`CM-<direction>` identity only when role, direction, generation, owned paths,
assignment, and frozen checkpoint remain compatible. Send compatible material
updates through Hub; a materially changed assignment requires a new bounded
session rather than silent broadening.

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

Write all fixed-set actions and rationales, capacity, lifecycle reasons, and
cross-direction synthesis coherently to `PORTFOLIO.md`; update the registry by
CAS; and establish the exact Root-owned `omp/workflow` checkpoint before any
dispatch that depends on the decision. A direction must be `ACTIVE` before it
receives active work. For a material `CLOSE`, `FUSE`, `SPINOFF`, or irreversible
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
discriminator, done reason, and reentry. It rides in the existing role payload
of the unchanged common v1 carrier. `NO_MATERIAL_INSIGHT` is a successful
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

Portfolio is an active allocator, not an all-terminal join. Consume each
terminal EM, CM, Transport, or Run fact immediately while preserving its
namespace:

- EM supplies scientific status, bounded claim, decision impact, evidence, and
  a recommendation; Root makes the comparative Portfolio action.
- CM supplies independent engineering, observation, and verification status.
  Return results needing scientific interpretation to the owning EM.
- BrowserTransport supplies provider, conversation, operation, archive,
  commitment, and transport facts.
- Experiment Operator supplies observed process, manifest, measurement, and
  terminal facts for one exact command.
- OMP liveness, runtime, worktree, conflict, commit, and push observations are
  routing or Git facts.
- A Portfolio analytical leaf supplies one conditional common analytical
  product for its frozen cross-direction gap; Root retains all Portfolio
  judgment.

Engineering, transport, Run, runtime, and Git facts never imply science or
lifecycle. Treat transport availability only as evidence availability. Retain
every nonterminal leg and route each terminal consequence in the same wake.
Consume a Portfolio analytical product as soon as it arrives and act on every
unrelated decision whose dependencies are already sufficient; no global wave
or all-terminal predicate gates allocation. One terminal advancing leg releases
its capacity slot even while other legs remain live.

When not `PAUSED`, recompute live advancing investments after each material
fact. If below authorized capacity, screen the strongest authorized fixed-set
candidates, adopt and checkpoint any required action/lifecycle change, and
dispatch the best admissible successor or replacement to an exact idle EM in
the same wake. Do not wait for another Root prompt. Never activate weak work to
fill a quota. If capacity stays unused, explain why that is preferable to the
strongest authorized candidate.

Wait only when all authorized slots have live advancing work or no admissible
candidate survives comparison. For the latter, name the screened candidates,
excluding evidence, strongest counterfactual, and exact reentry. An unconsumed
result or unfinished screening is not a waiting condition.

If an EM result is decision-incomplete, reread its conclusion and durable refs
and ask that same EM one bounded clarification for the missing variable. Do not
substitute an EM or infer science from technical failure. If a terminal
technical or measurement gap ends a leg without answering its investment
question, compare a materially different evidence route, a shared repair with
independent cross-direction value, and reallocation or `PARK` based only on
valid science and opportunity cost. If kept `ACTIVE`, dispatch a current
executable question or record the exact user-controlled reentry.

`PAUSE` retains assignments and permits only non-sending observation needed to
bring already-committed Effects to safe facts. It blocks refill, new direction
work, fresh transport sends, experiment launches, and every other new Effect.
Root never refills paused capacity.

### 6. Route meaning-complete role work

Use the OMP task/Hub carrier, identity, generation, assignment, and common v1
mechanics defined in `.omp/AGENTS.md`. Each body must make the objective and
decision relevance, governing authorities and evidence boundary, exact scope
and protected semantics, requested role-owned judgment, authorized Effects and
ownership, acceptance/stop, return route, durable references, and reentry
meaning-complete.

Route science, principles, synthesis, and result interpretation to EM;
contract realization, implementation, verification, repair, and command
estimation to CM; strict provider operations to `TRANSPORT`; one exact
result-bearing command to `EXPERIMENT_OPERATOR`; routing, lifecycle,
integration, and reconciliation to `ROOT`; and genuine approval choices to
`USER`. Persist the route in `next_action.owner`; dispatch a runnable handoff in
the same wake, or record exact `waiting_on` with that owner. Never leave a
material transition ownerless or ask CM to derive scientific authority.

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
durable request and returns `next_action.owner=TRANSPORT` with exact prompt and
request references. Root validates requester, direction/stage, provider, mode,
operation identity, prompt path/hash, response path, model requirement,
authorization, and commitment state; serializes the operation through
`hmasd-browser-transport`; validates the exact returned archive bytes; and
returns the common v1 transport fact to the same requester.

BrowserTransport transports only: it does not interpret content, adopt
lifecycle, write owner state, or choose follow-up. Provider conversation,
operation, tab, direction, and OMP assignment remain distinct. Apply the exact
submission and unknown-commitment rules by reference to `.omp/RULES.md`.

Separate scientific qualification from scheduling. Missing absolute peak
memory, wall-clock, storage, or accelerator estimates creates CM preparation
work, not a scientific veto or lifecycle change. Route each approved exact
command to one Experiment Operator and apply the time, memory, and approval
boundaries in `.omp/RULES.md`. Observe long-running work through Hub; material
transitions are event-driven, not polling- or timer-driven.

### 8. Checkpoint, integrate, and recover

Checkpoint only material milestones: completed research or engineering rounds,
accepted-result or terminal-run evidence promotion, external prompt/archive
readiness, Portfolio lifecycle changes, and schema migrations. Under
`hmasd-git-integration`, direction EM and CM own one exact-allowlist candidate
from their provisioned research or engineering worktree and integrate it as
`em:<direction>` or `cm:<direction>`. Root owns only Root/shared authorities,
cross-direction Portfolio, control-plane/schema, external archive promotion,
and recovery integration. The sole final target is `omp/workflow`.

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

Write Portfolio allocation only to `PORTFOLIO.md`; registry and Root-owned
runtime JSON only through the state CLI and expected-revision CAS. Invoke
documented worktree, run, external-review, and Git interfaces rather than
private writers. Root does not write direction research/engineering state,
Agentify ledgers, or run manifests; it may validate and promote exact external
archives and integrate its verified Root/shared candidate.

Return the common v1 envelope from `.omp/AGENTS.md` with `role: "root"`,
`logical_identity: "Root"`, the current generation and assignment, exact
status/materiality, summary, changed paths, state/artifact refs, checkpoint,
decision requests, and next action. Ordinary reconciliation uses payload
`kind: "root"`. Allocation or lifecycle adoption uses payload
`kind: "portfolio"` with one structured action for every fixed-set direction,
the capacity action, exact `PORTFOLIO.md` reference, and registry revision.

Use `PARTIAL`, `BLOCKED`, or `FAILED` only for the observed condition. A user
request binds the exact direction, command, or external operation and frozen
references. Do not terminally close the retained decision while an EM assignment or
committed Effect remains nonterminal. Root stops only at `IDLE`, `COMPLETE`, an
explicit user decision boundary, or an exhausted safe recovery route.
