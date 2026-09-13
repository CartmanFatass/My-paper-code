---
name: hmasd-portfolio-task
description: Use when the independent Portfolio Pro session plans the overall research program, Clerk assembles global planning or handoff decisions, or a DM proposes direction investment/capacity/lifecycle changes.
---

# HMASD Portfolio materials and Pro intake

Ordinary new A/B objects within an admitted direction's accepted open mechanism are DM decisions
under AGENTS.md section 2, "Ordinary direction research belongs to DM". DM declares finite object
budget/cost/stop conditions and proceeds under standing delegation; an ended prior allocation or
unselected successor does not make the entire direction's budget zero. Portfolio is required for
actual cross-direction/cumulative-resource or lifecycle choices, not every experiment. Explicit
frozen limits, scoped prohibitions and direction-node decisions remain at their actual scope.

Root is the user entry; the independent Clerk performs only delegated mechanical coordination.
Read docs/project/CLERK_OPERATIONS.md for event handling and writes. DM/Pro retain scientific
judgment. Clerk routes missing science or complex engineering repair to the relevant Astra DM;
it never turns a helper failure into a scientific stop or adds a Root ACK gate.

Portfolio is the independent persistent `portfolio:cross_direction` Pro session that owns the
whole research plan, not a direction's convergence step. It sees the current portfolio and latest
accepted plan plus changed DM evidence/opportunities, and decides composition, priorities,
investment, capacity and lifecycle within the standing authority. A formal vacancy is required
before replacement execution, not before global planning.

Clerk is the event-driven secretary/scheduler: assemble the global agenda from DM evidence, transmit
it through Clerk's native Transport, preserve the full answer, map actions/owners and execute
handoffs. Pro chooses the research plan. DMs retain direction-related proposals and scientific
conformance/intake for their parts of a global plan; they proceed independently where conforming. This
adds neither a local Portfolio manager nor another scientific approval layer.

## Overall planning and decision output

A global planning request is appropriate for an owner-requested plan, material direction-completion/
no-next-work events with unresolved management, changed priorities/resources or a Portfolio review
trigger. Clerk supplies current affected DM handoffs and the entire current portfolio index; cite
unchanged evidence instead of rereading every history. Include existing plan/decision links and
state what choices are now open. DM recommendations inform Pro; they are not preselected outcomes. Pro may compare all registered
directions (including queued/parked ones), reject proposals or recommend genuinely new directions
within the delegated Portfolio scope; it is not limited to approving the presented DM options.

Ask for an executable overall plan at the appropriate horizon: which directions advance and why;
priorities/dependencies and capacity; bounded investment scope and DM discretion where investment
is selected; continue/defer/park/close choices with reasons; who owns each next decision/action;
and the next material evidence/review trigger. Finite unanswered lifecycle scope must be explicit.
The plan can recommend new directions before slots open, but Clerk admits replacements only when
the accepted capacity/lifecycle mapping permits them. The four-DM target remains unchanged. If the complete plan already selects/funds a replacement
and its initial assignment, Clerk applies that mapping after the formal release without a repeat
Portfolio request. Ask only for genuinely unresolved choice/investment.

Portfolio may authorize a coherent bounded direction program instead of requiring a new purchase
for every internal step. Additional program discretion may be explicit in a Portfolio decision; ordinary A/B authority
already comes from standing DM delegation and needs no per-object grant. DMs design/execute within
actual direction-wide constraints. A/B experiments have
no universal Portfolio launch gate. Direction-tier scientific changes use Innovator/Convergence.

Clerk records the latest accepted overall-plan reference and its actual application in PORTFOLIO.md,
with changed decisions/intakes in existing records. Direction requests in the shared Portfolio
session cite this plan and update its affected portion instead of creating disconnected approvals.
Multiple ready changes may share a planning agenda; no direction waits for siblings to complete,
no timeout creates a fresh consultation and no unchanged answer is repeatedly requested.

## Direction-management trigger

When an ACTIVE direction has exhausted its executable work with no real producer, its DM owns
resolution of the outstanding investment/capacity/lifecycle question. A complete scientific
no-addition answer may be reused without treating it as an unasked lifecycle verdict. Read its
actual scope first; ask only the missing management choice, once. Explicit prior Portfolio/owner
deferral/disposition is applied, not repeatedly consulted. ROOT_OPERATIONS.md owns this transition.

Ask for a selected option and consequences: continued bounded investment, explicit deferral with
revisit condition/responsible owner and capacity treatment, or formal parking/closure. Do not
require new experiment facts to discuss occupancy, or invent a deployment customer as a universal
prerequisite. Preserve complete scientific answers and seek same-node correction only for a
specific unanswered/conflicting part of the posed decision. Routine delegated objects stay local.
For registered independent DM tasks, Clerk handoffs use SIBLING_COMMUNICATION.md's cross-task route;
New Portfolio transport belongs to Clerk; DM passes its proposal/evidence through the event route.
Shared Portfolio queue access is scheduling only. Direction-node Transport remains DM-owned.

## Ground the question

Start with the assigned question and current affected Portfolio rows/intakes. Read only relevant
sections of `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`: §8.1 maintains Portfolio principles,
§7 lifecycle meanings and §§11.7–11.10 investment/evidence calibration. AGENTS §§2,4.7–4.8 maintain
final authority, specification changes and asynchronous owner overrides. Use scientific-tools for
scientific reading or analysis, not for mechanical routing.

Prepare a decision-ready packet from:

- the specific choice, options, recommendation and operational consequences;
- applicable Portfolio principles, evidence class, claim ceiling, MEI/headroom and frozen limits;
- empirical and engineering experience, prior decisions and their actual effects, with exact
  evidence sources, scope, contrary results and known complete costs;
- uncertainties, the smallest useful investment and the evidence that would change the choice.

Explain how the principles/specifications/experience bear on each option. Do not just attach a
reading list. Ask Pro to state its choice, decisive reasons, uncertainty, revisit condition and
bounded consequences. Historical experience informs judgment but cannot silently amend a spec.
If a rule change is necessary, name the rule, necessity and scope for the proper node.

Relevant DMs supply decision-ready scientific proposals and current facts. Clerk assembles or
forwards these into one global Portfolio agenda, preserving competing proposals and contrary
evidence; it does not filter scientific options into a preselected answer. Clerk owns new Portfolio
transport/full-response recording. This is a single intake route, not a request for Clerk approval.
For vacancy replacement include the formal disposition and occupied/reserved slots. If a DM is
unavailable, Clerk transfers that factual/proposal assignment within the same role/scope.

## Publish and route

Use `hmasd-pro-research-prompt-author` with `workflow_node=portfolio_decision` and
`caller_role=portfolio`. These choose the node, not the author's native role. Bind every in-scope
direction in `direction_ids`. Include the current Portfolio snapshot, applicable principle/spec
sections and only needed experience/card/evidence references at their exact published revisions.
Include the machine-generated exposure line (zero new exposure when appropriate) and any required
per-arm projection; no consultation-only exposure experiment is needed.

Reuse the independent `portfolio:cross_direction` session. Clerk coordinates all **new** Portfolio
requests, creates/reuses its native Luna/high Transport, publishes/binds the exact agenda and waits
for that child's archive. Source/parent identify Clerk; operator identifies its Transport. DMs are
named proposal/evidence owners, not hidden parent routes. Accepted historical requests keep their
original author/parent/provider binding through closeout; do not rebind or resend them during migration.
Only one Portfolio request owns the conversation at a time. Clerk records the current request and
waiting DM proposals in existing tracking. Release the next ready agenda when the binding clears;
no all-DM batch or per-experiment approval. Other direction nodes run independently.


## Read the complete response and return an application mapping

Clerk reads and preserves the full immutable Pro response, not just its receipt or summary.
It checks request/source binding, completeness and current owner execution state mechanically,
then immediately records the plan and distributes relevant sections WITH the complete source to
all affected DMs. Scientific conformance is not a prerequisite for delivering the source to its
scientific owner. Each DM checks evidence class, scientific meaning, specs and budget applicability
for its portion, executes conforming actions and returns an execution mapping or exact conflict.
Clerk records each portion as pending/applied/conflict separately; no all-DM barrier or Root ACK.
A genuinely new direction's explicit provisional assignment names its Astra DM to perform that
scientific intake before dependent execution; Clerk cannot perform it instead.

Reconcile full-response delivery before interpreting a transport status as absence of a decision.
Short chat receipts/hashes are separate from full response bytes. A verified complete answer goes
to DMs while Transport repairs metadata. If no answer exists, preserve original request recovery;
no substitute question, provisional direction disposition or duplicate Send follows a blocker.
Concrete omissions/conflicts identified by the scientific owner return to the same Pro node with
exact evidence; other conforming portions continue. Clerk records the actual choices, limits,
reasons and contrary evidence as stated by Pro/DM, without reinterpretation or a second verdict.
Clerk schedules explicit handoffs under AGENTS section 4.8 without per-item owner ratification.
Specification changes use section 4.7 and Root's shared-control engineering ownership; the change
does not itself accept code or launch an experiment.

Use `hmasd-owner-item` to provide the Chinese decision packet and actual application trace.
`PRO_FINAL / OWNER_DELEGATED` records the Pro decision under owner standing delegation;
`ROOT_INTEGRATED` means integration, not a second verdict. Record planned/applied/blocked truthfully,
keep owner replies distinct and apply real asynchronous overrides at clean boundaries. Historical
unratified proposals are not automatically authorized by this prospective workflow change.

Update only the supported lifecycle/object unit under evidence-spec §7. A direction-node
recommendation to stop a package is not a whole-direction Portfolio mutation. A second recast
continues at the lowest ACTIVE sequencing priority under §11.7; do not silently PARK it. Working-set
scheduling changes no scientific meaning, lifecycle or allocation. Preserve per-result and
all-attempts-per-valid-result costs with node/device and honest unknowns in current Portfolio records.
