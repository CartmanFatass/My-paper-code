# HMASD OMP control-plane protocol

This document is the human-readable map of the active HMASD control plane. OMP
sessions, `task`, Hub, the state CLI, and Git remain the execution substrate;
this protocol defines how role-owned meanings move across that substrate. It
does not introduce a second scheduler, message bus, or authority layer.

## Authority and layered state

Authority is deliberately split rather than inferred from process status:

- The user fixes the scientific goal, the considered direction set, capacity,
  and any explicit decision boundary.
- Root is the single user-facing coordinator. Root executes the Portfolio
  subflow itself; there is no Portfolio agent or intermediate Portfolio
  session. `docs/research/portfolio/PORTFOLIO.md` records current
  cross-direction scientific judgment, while the registry records lifecycle
  and dependencies through expected-revision/CAS writes.
- `EM-<direction>` owns direction science and the material research cycle.
  Root routes every direction-scoped scientific question, synthesis, and
  interpretation through that direction's EM and never bypasses it with a
  direct scientific leaf. `CM-<direction>` owns an accepted engineering
  contract, implementation, observation, and technical verification. Neither
  role performs Portfolio actions.
- `BrowserTransport` is one Root-mediated logical service implemented by agent
  type `hmasd-browser-transport`. Agentify remains the external-operation
  ledger; the service never becomes scientific, lifecycle, or engineering
  authority.
- OMP task and Hub state is live execution evidence. Root reconciles it with
  `.omp/runtime/agents.json`, `.omp/runtime/worktrees.json`, durable role state,
  run manifests, external-operation references, and Git. A runtime status never
  silently changes Portfolio lifecycle or role-owned conclusions.

## OMP-native Root event projection

Root applies these exact invariants on every material wake:

1. **R1_SINGLE_CONTROLLER:** Root alone derives runnable nodes and admits work
   from durable authority, accepted envelopes, runtime jobs/effects/worktrees,
   and exact receipts. The projection is not a daemon, queue, registry,
   lifecycle authority, retry engine, watcher, or second scheduler.
2. **R2_FINITE_EVENT_SNAPSHOT:** Root reconciles once, snapshots the finite set
   of deliveries queued at the wake cutoff, and drains that set before
   scheduling. Later arrivals belong to the next material wake.
3. **R3_EXACTLY_ONCE_CONSUMPTION:** delivery ID and result identity are
   separate. Root dedupes deliveries by job/message ID and results by
   `NodeKey+result_sha256`; settlement is not acceptance. Every accepted or
   refused result receives exactly one causal disposition, and invalid results
   remain actionable evidence.
4. **R4_UNIQUE_NODE:** `NodeKey` is
   `(logical_identity,generation,assignment_id)` and has at most one terminal
   product. Every manager reentry receives a new assignment ID. The stable
   logical `Clerk` keeps its identity and service session while each sequential
   job receives a new assignment ID; material scope change requires a
   replacement assignment.
5. **R5_EXACT_EDGE:** an edge is satisfied only by an accepted producer
   NodeKey, result digest, required status/payload kind and refs, or by an
   immutable authority ref/SHA/revision or checkpoint. File/job presence,
   direction, salience, timing, settlement, and later target SHA are not edges.
6. **R6_ACCEPTANCE_BEFORE_RELEASE:** OMP natively releases its slot on job
   settlement; Root releases an advancing Portfolio leg only after accepting
   and routing its terminal fact. Technical failure is not science/lifecycle.
7. **R7_CAPACITY_SEPARATION:** advancing Portfolio capacity, OMP concurrency,
   the singleton BrowserTransport, one-command Operator ownership, exclusive
   worktree writing, Git target serialization, and state-path CAS are separate
   resource classes. A full class cannot hide work using another available
   class.
8. **R8_MAXIMAL_DISPATCH:** outside `PAUSE`, Root dispatches the maximal
   admissible independent set after consumption/screening, preferably in one
   `task.batch`. A slow child never blocks independent work. Root reconciles
   partial registration per item, retries no batch wholesale, and admits one
   canonical target mutator while unrelated jobs remain runnable.
9. **R9_PAUSE:** `PAUSE` admits no new task or Effect—Clerk, CAS, Git, send,
   Run, refill, or manager revival. Root may validate deliveries and
   non-sendingly observe only already-committed Effects through their existing
   owners. With none it returns `PAUSED/IDLE`.
10. **R10_LOCKS_NOT_AUTHORITY:** canonical locks only exclude overlapping
    mutation. They do not choose order, retry, actor, scope, or acceptance;
    waiters are explicit resource-blocked nodes.
11. **R11_NO_POLL_LOOP:** one material wake performs one reconciliation and one
    reassessment. A legal Hub wait races broad coordination events, not one
    salient/first child. Timeout and useless all-running snapshots do not start
    another wait.
12. **R12_CHECKPOINT_PROOF:** every checkpoint, wait, and terminal summary names
    Portfolio authorized/live/free capacity; OMP running/queued limits; queued
    delivery IDs; unconsumed and consumed result keys/digests; runnable/inflight
    NodeKeys; exact blocked dependency/resource edges; current target operation
    ID/lock; Run, Transport, worktree, and external refs; and Dashboard status
    (`NOT_CONFIGURED` is valid and non-gating).

Wait is legal iff queued deliveries, delivered-but-unconsumed results,
runnable-after-admission nodes, unfinished screening, and unrouted consequences
are all empty, and at least one exact reason holds: a nonempty set of
already-committed Effects needs safe non-sending `PAUSE` observation; all
Portfolio slots have live advancing work and every non-capacity obligation is
inflight or exactly blocked; the contemplated action has a nonempty exact live
dependency set after all unrelated admissible nodes were dispatched; every
otherwise runnable node is blocked on a named saturated OMP/effect resource
whose holder is observed live/committed; or no candidate is admissible and the
screened candidates, excluding evidence, strongest counterfactual, and exact
reentry are recorded. An invalid/unconsumed result, unfinished screening, free
admissible refill, runnable non-scientific operation, or unrouted consequence
makes wait illegal. Wait is broad, never first-child or all-terminal.
Empty-effect `PAUSE` returns; timeout is not a material wake.

The common result carrier requires `next_actions` and has no `next_action`
compatibility alias. Every closed item contains `action_id`, `kind`, `owner`
(including `CLERK`), `input_refs`, strict `dependencies`,
`authorized_effect_ref`, and `stop_or_reentry_ref`. Independent obligations are
simultaneous and array order is inert. Dependencies are strict one-of: an
accepted producer tuple plus result digest, status/payload kind, and refs; or an
immutable authority path/SHA plus revision/checkpoint.

Durable direction content is layered under
`docs/research/candidates/<direction-id>/`. Scientific authority is
`DIRECTION.md`. EM writes `<cycle-id>-scope-freeze.md`, material
`<cycle-id>-local-route-<route-id>.md`, `<cycle-id>-synthesis.md`, conditional
`<cycle-id>-terminal-gap.md`, and `<cycle-id>-handoff.md` under `evidence/`;
owner-authored `<cycle-id>-innovator-prompt.md`,
`<cycle-id>-convergence-prompt.md`, and
`<cycle-id>-convergence-disposition.md` under `external/`; and the current
durable CM request at `workflow/research/engineering-request.md`. CM writes
`<cycle-id>-contract.md`, `<cycle-id>-implementation.md`, conditional
`<cycle-id>-review.md`, `<cycle-id>-verification.md`, and
`<cycle-id>-result.md` under `workflow/engineering/`. Each reference is a
repository-relative path plus SHA-256, and each artifact is required only when
its named phase is reached. Raw runs, generated logs, concrete process handles,
tab mappings, and worktree paths remain outside durable scientific authority.

## Information-gap analytical dispatch

Analytical work follows an unanswered, decision-relevant information gap, not
a staffing template. An accountable manager dispatches a leaf if and only if:

1. the gap can change the manager-owned variable: Root's Portfolio rationale,
   EM's discriminator or claim ceiling, or CM's technical acceptance;
2. it is separable from manager synthesis and the leaf has a method, source,
   code-map, or tool advantage;
3. the return is inspectable as a proof step, construction, counterexample,
   source packet, dependency map, diff finding, or direct observation;
4. scope, protected semantics and Effects, positive/negative/null/ambiguous/
   failure branches, stop, and reentry can be frozen; and
5. accepted evidence does not already answer it.

Zero qualifying gaps dispatch zero leaves; one gap dispatches at most one
fitting assignment at a time; several genuinely separable gaps may fan out.
Duplicate or paraphrased gaps do not increase the count. A fixed leaf quota,
wave size, utilization target, vote, majority, or quorum is not evidence and
must not determine dispatch or a conclusion.

Each assignment receives a neutral packet with the manager-owned variable;
frozen question, claim, or contract; authoritative definitions and hashed
references; facts, evidence, inference, speculation, and contradiction kept
separate; exact gap and assigned lens; every outcome branch; non-goals;
ownership and authorized Effects; required output; stop; and reentry.
First-wave packets may differ by genuine mechanism-level lens but contain no
favored answer, desired `PASS`, sibling conclusion, vote tally, allocation
preference, or other sibling-result leakage. They remain blind to sibling
outputs until each has returned a substantive product or
`NO_MATERIAL_INSIGHT`. Authoritative constraints and known invalidating
evidence are never hidden.

Every accepted analytical return is a common analytical product containing:

- `assignment_id`, `gap_id`, `task_family`, the answered question,
  `MATERIAL_INSIGHT` or `NO_MATERIAL_INSIGHT`, and the concrete claim or
  product;
- exact source, artifact, or observation references and locators, plus sources
  inspected and methods attempted;
- assumptions and applicability boundary, with verified facts, external
  evidence, inference, speculation, and contradiction kept distinct;
- a falsifier or counterexample and surviving alternatives;
- uncertainty, limitations, the exact residual gap, and next discriminator;
- the conditional consequence and decision relevance for the manager-owned
  variable, together with a recommendation that does not adopt the manager's
  decision; and
- `DONE_REASON` and an exact reentry trigger.

The product remains inside the role-specific payload of the common v2 result
envelope; the clean-cut `next_actions` array carries every explicit successor
obligation. This adds no alternative carrier, authority, lifecycle registry, or
scheduler. `NO_MATERIAL_INSIGHT` is a successful terminal,
negative-complete analytical product: it records the sources inspected,
methods attempted, why no answer-changing insight follows within the frozen
scope, and residual uncertainty. It is not `FAILED`, approval, negative
scientific evidence, evidence of absence, or scientific rejection, and it
causes no claim delta or silent resampling. The same family/input reopens only
after a new mechanism, source, observation, premise, or corrected defect. A
valid adverse or null scientific observation may support a bounded scientific
completion; a technical failure supports no scientific update. Both remain
distinct from `NO_MATERIAL_INSIGHT`.

Fan-out and refill are evidence-driven. A manager consumes each terminal
analytical product immediately, closes the answered gap, and dispatches a
successor only for an evidenced residual or newly exposed separable gap. It
waits only for a live product on which its contemplated action depends; there
is no all-terminal analytical join.

## Root Portfolio subflow

At every Portfolio decision boundary, Root states a compact decision frame:

1. the user decision and fixed considered set, including authorized capacity;
2. live investments and already-committed Effects that constrain allocation;
3. the scientific evidence boundary, exclusions, uncertainty, and claim ceiling;
4. the strongest counterfactual allocation and why the proposed allocation is
   preferable on leverage, independence, cost, reversibility, and stop rule;
5. the next observation that could change allocation, its owner, and how each
   outcome changes an action.

Root sends each selected direction one meaning-complete investment assignment
to its responsible EM. The packet states the investment question,
direction-specific lens, material uncertainty, discriminator, protected
non-goals, stop rule, and action-changing outcome branches. Root never sends
direction-scoped theorem, concept, mechanism, counterexample,
evidence-retrieval, implementation, enhancement, synthesis, or interpretation
of results directly to a generic or scientific leaf. EM determines
which, if any, direction analytical gaps justify leaf work; a requested
numeric count cannot become a scientific quota.

Root may dispatch an analytical leaf directly only for a Portfolio-owned
cross-direction information gap in one of four categories:

- **Shared-assumption audit:** dependency, affected directions and layer,
  necessity, common-mode failure path, and relatively independent
  discriminator.
- **Complement/substitute analysis:** `COMPLEMENT`, `SUBSTITUTE`,
  `ORTHOGONAL`, `CONDITIONAL`, or `UNKNOWN`, with mechanism, conditions,
  evidence, sequencing implication, distinguishing scientific value,
  information value, engineering reuse, and common risk.
- **Option-value analysis:** branch opened, preserved, or closed; reversible
  enabling action; exercise, abandon, or expiry trigger; information gained;
  irreversibility; dependencies; and bounded cost/time, without invented
  probability, rank, or numeric pseudo-VOI.
- **Cross-direction risk analysis:** mechanism, exposed directions,
  propagation, trigger, blast radius, relatively independent check, and
  reversible mitigation with its tradeoff.

Portfolio leaves use the neutral packets and common analytical products above.
They return conditional relationships only and never rank directions, allocate
resources, change lifecycle, write direction state, adjudicate direction
science, or gain Portfolio or direction authority. Root synthesizes cited
mechanisms, dependencies, counterexamples, and limits, not votes, confidence
counts, majorities, or quorum.

Root compares every direction in that fixed set and adopts exactly one explicit
action per direction: `NONE`, `ACTIVATE`, `CONTINUE`, `NARROW`, `PARK`,
`CLOSE`, `FUSE`, or `SPINOFF`. An EM recommendation is evidence for this
comparison, not an adopted Portfolio action. Transport state, CM status, run
status, task liveness, and Git state are likewise facts at their own boundaries;
they cannot be promoted into science or lifecycle decisions.

Portfolio allocation is active, not an all-terminal join. Root consumes each
terminal EM, CM, Transport, Run, Clerk, or Portfolio analytical fact from the
finite delivery snapshot, validates and causally consumes its exact result
digest, preserves role-owned meaning, routes its consequence, recomputes live
advancing work, and dispatches the maximal admissible independent set. A
completed Portfolio analysis closes its gap or exposes an evidenced residual
gap immediately; it does not wait for sibling analyses. A slow direction never
blocks independent Transport, Portfolio analysis, or Clerk work. An unresolved
relationship terminates as `UNKNOWN` with an exact reentry trigger rather than
holding every direction at a global barrier.

When advancing work is below authorized capacity and control is not `PAUSED`,
Root screens the strongest authorized candidates and includes every admissible
successor or replacement in the same wake. Scientific analytical fan-out or
refill follows current distinct gaps and fitting methods, never a target leaf
count. Unused capacity requires an explicit comparison against the strongest
candidate and an exact reentry condition. `PAUSE` retains obligations but
blocks every fresh task and Effect. It permits delivered-result validation and
safe non-sending observation only for already-committed Effects through their
existing owners; empty-effect `PAUSE` returns `PAUSED/IDLE`.

The registry lifecycle has four states:

- `REGISTERED`: known and eligible, without active investment.
- `ACTIVE`: a current executable scientific question with live work or one
  exact operational reentry; it may not be silently starved.
- `PARKED`: no live direction work, with a supporting scientific or
  opportunity-cost reason, evidence boundary, and required
  `reactivation_condition_ref`; it is not `CLOSED`.
- `CLOSED`: terminal investment disposition, reopened only by an explicit new
  Portfolio action on materially new grounds.

Root prepares lifecycle/action authority coherently and freezes the complete
desired registry bytes, exact state path, writer, and expected revision. Root
assigns the stable Clerk service one bounded state job. Clerk invokes the
public `scripts/hmasd_state.py` interface directly with those inputs; Root does
not perform the CAS. Dependent work waits for the accepted terminal Clerk
observation and resulting revision.

## Direction cycles and durable handoffs

An EM material cycle is one bounded scientific question with
`cycle_boundary` equal to `FRESH_MATERIAL_CYCLE`, `CONTINUATION`,
`CM_RESULT_INTERPRETATION`, `EVIDENCE_INTAKE`, or
`TERMINAL_GAP_DISPOSITION`. A fresh material cycle normally includes Pro
Innovator and Pro Convergence through the exact provider product model and
reasoning-effort axes; the current ChatGPT target is product model
`GPT-5.6 Sol` with reasoning effort `Pro`. Root authorizes one provider-visible
user message, not one browser attempt, click, tab, or Agentify operation.
Evidence intake, continuation, CM-result interpretation, and terminal-gap
disposition do not manufacture another message authorization. EM separates
facts, external evidence,
inference, and speculation, preserves the claim ceiling, and sends engineering
needs to Root as durable request references.

CM is contract-first. It accepts an exact durable engineering request only from
the exact accepted same-direction EM `integrated_sha`, freezes scope, non-goals,
interfaces, protected semantics, acceptance, owned paths, and an evidence-role
policy before implementation. It reports independent `engineering_status`,
`observation_status`, and `verification_status` axes. Implementer, Reviewer,
Verifier, and Experiment Operator outputs retain their evidence roles; none is
permission or scientific judgment.

EM and CM return their semantic facts promptly with `semantic_product_ref` and
`persistence_status=PREPARED`. Durable state, `candidate_sha`, and
`integrated_sha` remain null until observed. Each manager hands Root concise,
complete intent for independent state, candidate, or integration jobs and
explicit independent `next_actions`. Same-direction EM-to-CM waits for accepted
EM `integrated_sha`; CM-to-EM result interpretation waits for accepted CM
`integrated_sha`. A Clerk refusal or unknown outcome changes only the
mechanical edge, preserves semantic acceptance, and permits compatible manager
reentry with a new assignment ID. Material scope change requires a new
generation.

## OMP communication and BrowserTransport

Every cross-role dispatch uses an OMP `task` or Hub carrier and names the common
v2 identity/generation/assignment envelope. In addition, its natural-language
body contains these meaning sections:

- **Objective and decision relevance**
- **Authorities, inputs, and evidence boundary**
- **Scope, protected non-goals, and preserved semantics**
- **Requested role work and role-owned judgment**
- **Authorized Effects and ownership**
- **Acceptance evidence and stop condition**
- **Return route, durable references, and reentry**

Results use the common v2 result envelope and role-specific payload. Literal
Codex `[WORK]`, `[RESULT]`, or `[BROWSER WORK]` headings may be historical
semantic source material, but they are not OMP routing authority, identity, or
receipts.
Assignments are vertically coarse. One engineering leaf investigates,
implements, and authors focused contract tests for one bounded slice; the
parent reviews and runs verification. Parallel leaves must own disjoint
repositories, directions, paths and semantic interfaces, or genuinely
independent evidence roles. Routine scout-to-implementer-to-reviewer chains
over the same candidate are prohibited because they duplicate context and
create competing interpretations. Independent engineering review is reserved
for a frozen high-risk candidate whose acceptance explicitly requires it.


An analytical product uses that same carrier and role-specific payload.
Required `next_actions` explicitly carries every successor; each independent
Clerk, Transport, Portfolio, manager, Operator, Root, or User obligation gets
its own action and strict dependencies. Empty means no successor. No implicit
edge or action is reconstructed from prose, file presence, or job settlement.
Root keeps orchestration visible without inventing a second scheduler. At
startup or resume, material dispatch and result boundaries, verification and
integration, and immediately before a legal wait or user boundary, it emits a
short main-transcript note with **Problem**, **Now**, **Evidence**, and
**Next**. These notes report accepted facts and exact blockers, not hidden
reasoning. They are driven only by material events; timer heartbeats,
progress-poll loops, per-tool narration, and Dashboard-only reporting are
prohibited. OMP Agent Hub (`Alt+A`) remains the detailed live subagent view.


EM and CM never send directly. They create one frozen, already-authorized
request reference and return it to Root for routing. The request fixes the
provider (`chatgpt` or `gemini`), mode (`INNOVATOR`, `CONVERGENCE`, `DIVERGENT`,
`ENGINEERING`, or `MONITOR`), product model and reasoning effort, target
conversation, prompt and response identity, operation ID, idempotency key,
request fingerprint, stable key, and operation reference. Root serializes it
through the singleton `BrowserTransport` and returns the minimal receipt to the
exact requester without interpreting provider content.

BrowserTransport follows one linear sequence: validate the exact request,
insert the exact prompt, persist `send_attempted: true` immediately before one
visible hit-tested native pointer activation of Send, observe the provider user
message ID, wait for the causal assistant message ID, and archive the exact
response bytes. A failure before `send_attempted` retries automatically on the
same immutable operation. After `send_attempted`, it only observes and never
activates Send again.

The shared snake-case receipt contains immutable target/operation/prompt/
response identities and timestamps; `send_attempted` with its nullable
timestamp; nullable observed conversation URL/ID and provider user/assistant
message IDs; nullable exact archive; and nullable one-code error. Only direct
identity, monotonic send, append-only ID/archive, and ID/archive dependency
invariants apply. No derived transport status exists. Provider conversation,
operation, tab, direction, OMP task, raw response archive, and receipt remain
distinct objects.

## Clerk, liveness, Git, and recovery

Root reuses compatible logical EM/CM sessions through OMP runtime maps and Hub.
Every manager reentry receives a new assignment ID; material scope change also
increments generation. Material transitions wake one bounded reconciliation;
delayed output does not create a poller or successor. One Experiment Operator
owns one exact result-bearing command through its terminal observation.

Managers own semantic authoring and the exclusive assignment worktree writing
window until terminal handoff. They then become non-writing. Root assigns the
one stable logical `Clerk` a concise, complete frozen mechanical job through
task or Hub. Clerk runs one active job, returns direct observations, and may
idle, park, or revive under the same identity for the next sequential job.
There is no second scheduler, persisted authorization graph, operation draft,
or per-primitive child fan-out.

Clerk is a mechanical service, never the authority actor or writer. It cannot
interpret science, decide technical acceptance or Portfolio lifecycle, choose
scope, target, allowlist, successor, or recovery, resolve conflicts, rebase,
broad-stage, retry, or resend. Root's assignment supplies the exact actor or
writer, canonical targets, inputs, authorized effects, competing refusal
outcomes, stop, and return route. Manager writing resumes only after the
assigned Clerk job is terminal and Root issues a new assignment.

Git handoff is layered over `omp/*`, with `omp/workflow` the normal shared
target. One candidate integration requires a clean canonical target, one
non-merge candidate directly parented by its declared source base, an exact
nonempty changed-path allowlist, an exact expected remote predecessor, and one
commit message and actor. Clerk applies the standard Git diff in a temporary
detached worktree and refuses path drift or conflict. Immediately before its
only push attempt it fetches and compares the remote predecessor, then uses an
exact force-with-lease condition. An ambiguous push permits one read-only
fetch/observation and never a retry. Refusal changes neither target nor remote.

Observed inconsistency routes through the OMP
`hmasd-workflow-recovery-manager`, dispatched only by Root. Recovery reconciles
existing authorities and effects; it does not invent science, resend an unknown
external operation, replay an unknown run, bypass CAS, or turn a stale runtime
observation into a lifecycle decision.
