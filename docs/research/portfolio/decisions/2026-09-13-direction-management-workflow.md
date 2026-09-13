# Direction management and independent DM tasks — 2026-09-13

Authority: OWNER_DIRECT. Owner requested repair of DM/Portfolio/Root management, then authorized
one independent DM task pilot before migrating the other three. Owner clarified Root is an
**event-driven** recorder and scheduler, especially for Portfolio handoffs. Research, Pro sends
and the existing 50-minute heartbeat remain paused. This record issues no scientific disposition.

## Failure and repair

The prior control allowed an allocation to finish, prohibited interpreting it as a direction
closure, then permitted producer-free ACTIVE-idle indefinitely. No actor had to obtain the missing
capacity/lifecycle decision. The earlier tests even accepted that state as success. Root's prior
explanation that there was no legal next object incorrectly treated management work as exhausted.

A scientific no-addition answer closes its question; it does not answer an unasked direction
occupancy question. DM owns the next research/management decision, not only a supplied card.
Within existing object delegation it selects and executes; direction science goes to the existing
Innovator/Convergence; unresolved investment/capacity/lifecycle goes to Portfolio. The DM recommends
and intakes, Portfolio selects, Root implements handoffs/registration without a second approval.
An explicit deferral must identify scope, capacity treatment and revisit condition/owner. It is
reported as non-advancing and causes no empty native waiting or repeated identical consultation.

No new grant, blanket experiment approval rule, forced PARK, customer prerequisite, scientific
reinterpretation or transport retry is introduced. Earlier fixed evidence remains historical;
current procedures are replaced in their maintained sources rather than stacked as alternatives.

## Runtime architecture

Independent user-visible DM tasks own their direction across assignments. Their optional native
Transport/Monitor/Reviewer children stay local to that task. Portfolio remains a persistent Pro
node, not a fifth native manager. Root's task is the event recipient and main integrator.

DM sends Root one cross-task message for completed intake, Portfolio disposition, needed integration
or shared dependency. Root deduplicates by direction/assignment/evidence revision, applies the
consequence and can end its turn while DMs continue. Root uses wait_threads for bounded observation
and read_thread for missing facts. Native send_message/final semantics do not apply across tasks.
The owner-authorized 50-minute heartbeat is only a missed-event/interruption backstop; no per-DM
heartbeat, Relay or standing polling service is introduced. It remains paused in this migration.

Runtime facts: create_thread creates a separate task, not a native-subagent conversion. It has no
agent_type/config_file parameter. New task model/effort uses the app default unless the user asks
for an override; role duties must be explicitly loaded. Git-project tasks create a managed worktree
by default; this is not adoption of the existing direction branch. The migration retains one
existing direction authoring checkout and uses the generated checkout only to host the task.
Tool descriptions in this runtime are the source for exact message/start/wait semantics.
[Official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
confirms custom agent instructions/configuration apply to spawned agent sessions; task names alone
are not role configuration. Independent-task auto-wake beyond observed tests is not presumed.

## Bounded implementation and validation

Root owns main control edits: AGENTS, DM role/config entrypoint, ROOT_OPERATIONS,
SIBLING_COMMUNICATION, dispatch/Portfolio skills, current handoff/tracking and the routing registry.
Preserve scientific cards/results, lifecycle registry rows, provider identities, budgets and all
existing authoring checkouts. Acceptance: independent review, focused syntax/diff checks, a read-only
ACVC handoff, one ACVC-to-Root message, one Root-to-ACVC follow-up and observed completion, plus correct scenario behavior: unresolved lifecycle leads to
management work, prior explicit deferral is reused, funded steps do not need ACK, and pause blocks
Send. Only after
pilot acceptance migrate MGTAP/RCLE/FOLR using the same bounded contract. No Pro/experiment invocation.

Baseline reviewer `/root/workflow_boundary_review` independently identified the producer-free idle
trap, scientific-versus-lifecycle scope confusion, native idle-parent delivery gap and absent
whole-direction completion contract. It also identified top-level model/config and worktree
inheritance risks. This is workflow evidence, not a claim that a new scientific experiment ran.

Current application: control repair reviewed; four independent tasks created. Initial ACVC pilot
completed; owner-required Astra/max acceptance completed across all four tasks. The authoritative routing
and rollout state is `.codex/hmasd-dm-sessions.toml`; research remains owner-paused. Final validation
and actual migration receipts will be recorded here after observation.

## Pilot observations

ACVC task `01a09cd3-ae36-7071-874f-4d021bdeb225` uses session checkout
`C:/Users/fires/.codex/worktrees/4c59/HMASD`, detached `f1d05112e`, and verified the existing
`codex/acvc` authoring checkout clean at `23b5efe52`. Event `acvc-session-pilot-v1` arrived here
through send_message_to_thread, but its management answer failed: no new receiving-use fact led
back to ACTIVE-idle. Root did not accept migration on delivery alone. Independent review also
found the old AGENTS block and current next-action cells; these were replaced rather than qualified
by another override paragraph.

Root issued one bounded v2 follow-up. Event `acvc-session-pilot-v2` arrived with direct inspection
of archive `98208469a9fd922c3390c63e7eaf53680fc2122`: the response explicitly did not decide
lifecycle/capacity. The DM correctly selected management-proposal preparation after explicit
research resume, applied already explicit deferral in the counterexample, and continued a funded
step without Root ACK in the other counterexample. No Pro/experiment/child creation occurred.
This verifies cross-task message delivery to an active Root and bounded follow-up behavior;
automatic event execution while Root is ended has not been separately exercised.

## Owner model correction

Owner requires all independent DMs to use GPT-6 Astra / max. Initial creation omitted model overrides
and therefore used app defaults; that preliminary test is not target-model acceptance. Root applies
explicit model=gpt-6-astra / thinking=max follow-ups to all four tasks and repeats bounded management
acceptance under the required configuration. Registry records the required profile and actual stage.
No duplicate tasks, scientific requests or experiments follow from the model correction.

## Control-plane acceptance

Root accepted the control diff after independent review. The review's remaining-old-idle and
insufficient-behavioral-acceptance findings were fixed and rechecked with no material residual.
Both edited skills passed quick_validate; all changed TOML files parsed; local Markdown links and
git diff --check passed. The local Codex task database read confirmed all four tasks now select
`gpt-6-astra` / `max`. This metadata confirms configured model, not the scientific correctness of
responses. All four target-model task returns were subsequently received and accepted as recorded below.

The existing 50-minute automation prompt was updated through the app to recovery-backstop duties;
its actual status remains PAUSED. No recurring per-DM tasks or polling services were added.

## Target-model acceptance events

- ACVC `acvc-session-astra-max-v1`, turn `01a09cd8-cabf-72a2-aed4-3bf5f68fa98a`:
  completed and received. Read original K/post-cluster/next-use answers, correctly distinguished
  finite grant from unasked post-K capacity decision. Corrected preliminary case C: absence of a
  producer for an already authorized object means start the object, not ask Portfolio. Existing
  deferral is reused; pause means no Send. Root read this turn's rollout turn_context and confirmed
  model `gpt-6-astra`, effort `max`. Accepted independent owner, still research-paused.

Ordinary DM notifications use short deltas with evidence links; full scientific reasoning remains
in the DM intake/task. Fact-only messages do not require ACK; only a concrete next assignment
causes a follow-up. This is the event-driven Root boundary, without a reply/wake loop.

- FOLR `folr-session-astra-max-v1`, turn `01a09cd9-d6a0-7500-9d14-f9a3b7bfab38`:
  completed and received; target turn_context confirms Astra/max. Independently read the complete
  direction answer and Portfolio F: F excludes whole-direction disposition and only funds the
  completed reference-use comparison. Correctly withdrew initial ACTIVE-label-as-deferral reasoning;
  accepted the same three management branches and pause boundary. Existing cleanup inventory has
  removal_executed=false; no deletion was inferred or performed. Accepted independent owner,
  research-paused, with post-F management and scoped retention/cleanup reconciliation retained.

- MGTAP `mgtap-session-astra-max-v1`, turn `01a09cd9-d3be-7922-85ec-da2dc1766572`:
  completed and received; target turn_context confirms Astra/max. Full R explicitly excludes
  Portfolio capacity/lifecycle/investment, and prior Portfolio B/amendment concern one allocation.
  Correctly withdrew initial scope-limited scientific revisit-as-deferral reasoning. Same three
  management branches and pause respected. Old uncertain effect and local cleanup restriction stay
  evidence, not a pending scientific producer. Accepted independent owner, research-paused.

Full Pro response copies may reside in the designated direction checkout and immutable Git commits
rather than main's file tree. These are valid recoverable sources; the DM handoffs cite their exact
source and preserve the copy. Absence at main's relative path is not a missing formed decision or a
reason to resend. Current control instructions still come from main.

- RCLE `rcle-session-astra-max-v1`, turn `01a09cd9-d528-7e53-a41d-56738d296d0c`:
  completed and received; target turn_context confirms Astra/max. Read four original answers and
  the B09 erratum; B09 line138 expressly excludes lifecycle/capacity and the recipe HOLDs are
  scope-limited. Correctly retained an unresolved whole-direction management deliverable, reused
  already decided recipe scope and required no Root ACK for funded objects. No scientific action.
  Cleanup completion remains unverified in existing inventory; full response copies remain in the
  original direction checkout/immutable commits. Accepted independent owner, research-paused.

## Owner correction: independent overall Portfolio planner

The owner clarified Portfolio Pro must own overall research planning, not act merely as a DM's
finite convergence procedure. Root remains an event-driven recorder/scheduler. This prospectively
replaces the Root-vacancy-only restriction and fragmented new Portfolio dispatch routes.

The existing independently bound Pro session `portfolio:cross_direction` is reused; its registry
currently points to conversation `6a9c109e-b264-83e8-a78b-f9ea1b767b7b`, with the old RCLE request
ARCHIVED. This is a recorded binding, not fresh browser-model verification. No provider state or
accepted request was changed, and no new planning request was sent during pause.

DMs supply evidence, options and recommendations; Root is the single coordinator/publisher of new
Portfolio agendas and full-plan recording through its native Transport. Pro compares the entire
program, can reject proposals or propose new directions, and decides priorities, bounded programs/
discretion, capacity and lifecycle. Root does not choose science or use the agenda to preselect an
answer. Direction Innovator/Convergence and ordinary object work stay DM-owned. Affected DMs apply
conforming plan portions independently; a specific conflict returns to the same Pro node without
holding siblings for unanimous ratification. Historical accepted DM-owned Portfolio requests keep
their original parent/closeout route. Future planning can precede vacancies, but new admissions
still require the actual decided slot/capacity mapping.

Scientific execution and the heartbeat remain paused. Four independent DM governance migrations
are complete; the revised overall-planning Pro flow is documented but has not generated a new plan.

## Final governance acceptance

All four independent tasks completed their Astra/max evidence and behavior checks, with matching
per-turn rollout model/effort facts and unique task/authoring checkout registration. Legacy native
DMs were notified without waking them for work; they remain retired/paused as current executors.
The main lifecycle/priority table still contains the same 27 entries and unchanged lifecycle/
priority tokens. No experimental or provider execution was part of this acceptance.

The Portfolio extension was independently reviewed. Findings were repaired: apply an already
selected/funded replacement directly after formal slot release rather than reconsulting; remove
residual DM-direct new Portfolio forwarding rules; assign Transport repair to the actual parent.
Targeted recheck found no material residual. Four changed skill entrypoints validated; current
TOML and local Markdown references parse/resolve and git diff --check passes. Root accepts the
control-plane implementation under OWNER_DIRECT. This validates organization, routing and bounded
DM behavior; a new overall Pro plan and an ended-Root wake experiment have not been performed.

Current outcome: independent Astra/max DMs, event-driven Root, independent overall-planning Pro
session with a unified new-request entry. All science and heartbeat remain OWNER_PAUSED. Latest
new overall-plan state is NOT_REQUESTED; future planning requires explicit resume/commission.

The final overall-Portfolio standard published at `4d79e697f` was then delivered to all four
independent DM tasks using Astra/max. ACVC, MGTAP, RCLE and FOLR each completed a read-only
confirmation of the current Root/Sibling sections and adopted the unified new-Portfolio route,
direction-local responsibility and pause boundary. These were finite governance notices, without
another Root-message/ACK loop, new scientific work or a new Portfolio request.
