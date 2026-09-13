# Task collaboration

OWNER_DIRECT 2026-09-13: Root is the user entry point and accepts shared control-plane changes.
Clerk is the independent Luna/high mechanical coordinator; DMs remain Astra/max direction managers.
Use [Clerk operations](CLERK_OPERATIONS.md) for its delegated writes, event handling and escalation.
Current research state and all live task routes come only from `.codex/hmasd-dm-sessions.toml`.
No routine Clerk action requires a Root ACK. Scientific authority remains with DM/Pro.


Control runs on Windows C:/Projects/HMASD with PowerShell. Resolve native IDs from runtime
results; read Agentify/provider settings from .codex/hmasd-transport.toml.
Historical task IDs are evidence, not dispatch routes.

## Independent DM tasks and lightweight Clerk

For directions registered as independent tasks in `.codex/hmasd-dm-sessions.toml`, this section
replaces the native Clerk-to-DM routing below. The registry names the current Clerk and each unique
DM task, host, designated authoring checkout/branch and migration state. Resolve actual task IDs
from app results; a queued clientThreadId is not a usable threadId. Lifecycle stays in PORTFOLIO.md.

Clerk is an event-driven recorder/integrator and scheduler at Portfolio/shared-dependency boundaries.
DM runs its direction independently: object decisions, engineering, experiments, specialist
children, scientific intake, next proposals and direction-related Portfolio intake. DM does not
wait for Clerk ACK/integration between those steps. Clerk need not stay alive waiting on all DMs.

- Clerk dispatches bounded management or shared-dependency work with send_message_to_thread to the
  registered task. DM sends a concise actionable cross-task message to Clerk when integration,
  shared Portfolio access, a real cross-direction blocker or formal disposition needs action.
  A task's final does not automatically deliver its content to another independent task.
  Ordinary event messages are a short delta (about 5–10 lines): event identity, accepted result or
  decision, evidence/commit link, next action/owner, and the concrete Clerk action if any. Keep full
  scientific reasoning in the DM intake/task. A fact-only event needs recording, not a reply; send
  a follow-up only when new work is actually required. This prevents ACK and self-wake loops.
- DM reports completed intake and actionable changed boundaries once; ordinary intermediate work
  stays local. Clerk uses compact
  wait_threads snapshots with stored cursors (up to eight tasks); read_thread only for missing facts.
  Deduplicate direction/assignment/evidence revision and retain any unfinished action separately
  from delivery status. A successful tool call is not acceptance or an extra approval.
- The existing owner-authorized 50-minute heartbeat is an interruption/missed-event recovery
  backstop, not the normal scheduler. DM-to-Clerk send_message_to_thread is the primary event route.
  It may end while independent DM tasks continue. It stays quiet on unchanged/non-actionable state.
  Explicit owner pause keeps research and the heartbeat paused; migration/testing does not resume.
- A shared Portfolio queue lives in existing tracking: Clerk's current request plus waiting DM proposals.
  Clerk transmits the next ready planning agenda when the binding clears. Preparation,
  unrelated direction nodes and experiments proceed independently. Queue access is not approval.

Migration: stop/retain the old DM, give the new task a bounded read-only handoff, verify its actual
checkout/HEAD and accepted evidence, then register the sole owner. The app-created task worktree is
session hosting; reuse the existing direction authoring checkout for edits. No duplicate branch,
writer or automatic new budget. No tool here converts/reparents an old native child: preserve old
accepted requests/handles and reconcile ownership before replacement. New DM creates its own
Transport/Monitor only when there is actual work. Native names are local to their parent task tree.

OWNER_DIRECT: independent DMs use gpt-6-astra / max. Explicitly set model and thinking when
creating/resuming these DM tasks; creation without overrides only uses the app default and is not
accepted as the required profile. A custom subagent TOML is not automatically applied. The initial
prompt loads current DM duties/control from C:/Projects/HMASD even when the direction checkout is
older. Record tool/config evidence for the selected model; do not invent model self-observation.

Clerk acceptance observes a completed bootstrap turn followed by a new actionable cross-task
message, a new turn and its actual consequence. Then follow real DM proposal/Portfolio/DM handoffs.
The earlier DM migration tests are evidence in the workflow decision, not a repeated launch gate.

## Native task tree (DM-owned specialists and unmigrated legacy DMs)

Clerk coordinates DM direction chains. Each DM owns science, implementation, self-checks, repairs
and acceptance, retains independent high-risk Reviewer review, and reuses one Luna/low native
experiment-monitor child for its accepted experiments. CM and Implementer assignments are suspended.
Do not create equivalent implementation roles under generic names.

Use collaboration.followup_task for work assigned to an existing native child, including
resuming an idle monitor or delivering evidence requiring action. Use collaboration.send_message
for facts to an active/waiting parent; it does not start an idle recipient's turn. Native final
returns complete a bounded assignment. Do not send duplicate work through both tools.

Clerk uses app event routes for independent DMs and native waits only for its own Transport.
It does not wait for independent DMs through collaboration.wait_agent. DM does independent work first, then uses native
long wait for its monitor or Reviewer. Use the configured 1500000 ms default/minimum wait;
process an arriving event promptly. An unchanged timeout requires only a brief continuation of
waiting: no rereading all cards, status census, repeated assignment or progress broadcast.
The owner accepts periodic context reuse/cache refresh and brief continuation as design premises.
No per-DM keepalive messages, ACK loops, timers or separate relay are needed.

An unchanged timeout stays quiet. When a bounded assignment reaches completion, hits a material
blocker or scope conflict, or has no immediate authorized work while its direction remains ACTIVE,
the DM must send one proactive action message to its parent before returning a native final or
entering idle wait. That message names the assignment, state, evidence or commit, and next action
or dependency and its owner (or none), including the executed decision's authority and limit.
Use ordinary prose and existing evidence records, not a new schema or approval item. Clerk treats
message/final copies at the same assignment/evidence revision as one event, without an ACK.

If accepted card/Pro/grant scope fixes the work, the same DM completes implementation, checks and
required review, publication, fresh admission, launch/Monitor, collection, technical acceptance,
scientific intake, preservation and assigned cleanup, then its authorized dependent continuation.
Neither an additional Clerk dispatch nor integration/ACK nor a repeat Portfolio vote is needed.
An idle child with such unfinished work is resumed once with followup_task; an already running DM
continues directly. Actual shared-writer/runtime conflicts go to Clerk for execution coordination.
New scientific meaning or investment/budget choices go to the proper node, authored and intaken
by the DM under AGENTS §2; Clerk is not an intermediate scientific approver.

Distinguish a pending external dependency from ACTIVE-idle with none. A real dependency names its
request/handle/producer and required event; after independent work, wait for that direct return.
Without executable continuation or a real producer, DM resolves the management transition in
ROOT_OPERATIONS.md. Scientific no-addition does not answer an unasked capacity/lifecycle choice.
Explicit Portfolio/owner deferral records scope, capacity treatment and revisit condition/owner;
it ends unnecessary waiting. A possible future use alone is not a producer. Reuse prior decisions
within their actual scope; a timeout supplies no new scientific fact or retry authority.

DM sends Clerk only actionable integration, cross-direction dependency, formal direction disposition,
scope-conflict, or bounded-assignment completion/ACTIVE-idle facts, with assignment identity,
commits/evidence, requested next action and uncertain effects.
Continue independent authorized direction work after a partial handoff. Clerk handles the changed
direction without waiting for siblings or routinely reloading the whole portfolio. Deduplicate
message and final copies by source, assignment and evidence revision. Clerk accepts artifacts;
message delivery is not acceptance. Routine specialist and monitor returns go directly to DM.

## Experiment observation

Follow EXPERIMENT_MONITOR.md. DM creates/reuses its monitor; Operator uses the exact native
monitor address supplied by DM and cannot create another child. Adoption and terminal facts go
to DM. DM collects results and completes scientific intake without Clerk forwarding terminal events.
Clerk receives the resulting actionable direction handoff, not every experiment status.

## DM-owned Agentify Transport

Each DM creates/reuses one native Luna/high Transport child with minimal context. DM authors and
publishes the exact handoff, dispatches via followup_task, and waits natively for the complete
archive. Transport owns Agentify Send, observation, one-Send reconciliation and direct DM receipt.
A verified complete bound response goes directly to conformance intake even while short receipt
or metadata reconciliation remains unresolved. An uncertain effect forbids another Send; it does
not turn that complete decision into a pending scientific answer.
Clerk receives the DM's conformance/decision mapping by app message and integrates it. Each native
Transport returns to its actual parent; independent DM/Clerk coordination uses app-task messages.
Different provider bindings may proceed concurrently. Serialize each exact conversation and the
independent Portfolio session under Clerk for all new requests. DMs send proposals/evidence to Clerk;
Clerk assembles global planning agendas without scientific approval, publishes through its own native
Transport and records the full plan. Affected DMs check/apply their parts; Clerk schedules handoffs.
Accepted historical DM-owned Portfolio packets retain their original parent until closeout. Existing uncertain or accepted requests
require same-request reconciliation, never a new Send after changing executor. Transport skill
owns exact Agentify arguments and immutable archival. Experiment monitor never operates Pro.
Verified nonacceptance permits same-request repair and continuation without a parent handshake.
Transport sends one direct archive receipt and records its actual native delivery outcome; no
ACK, Clerk forwarding or duplicate app-task wake follows. Its final closes that same assignment.
Historical HANDOFF IDs stay immutable; an assigned native recovery route is recorded separately.
At completion, material conflict or no-current-work while its direction remains ACTIVE, each
bounded assignment sends one direct action message to its assigning parent before final:
assignment, status, evidence/commit and next step. DM sends its actionable boundary to Clerk;
Transport sends to DM. A factual conflict needs no completed archive. Active generation remains
ongoing work and unchanged waits require no broadcasts. A later changed boundary preserves
the prior return and sends its own update once; this is not an ACK or forwarding chain.
If a leaf runtime lacks collaboration.send_message, its actionable native final is the direct
parent return. Record that actual capability/method; never fabricate tool delivery or add an app relay.

Pure Transport engineering defects go to the direction DM, or a relevant Astra DM assigned by Clerk for a Portfolio request, including focused
helper/fixture and skill updates with proportional review. Keep the same operation and immutable
receipts; involve Clerk only for a shared runtime/load, cross-direction dependency or scientific
decision. If the original conversation remains unrecoverable after supported same-request repair,
the actual parent may rebind the identical frozen prompt to a new conversation only with verified
pre-Send nonacceptance (`sendAttempted=false`, no provider pairing). Preserve and close the old
operation as `CONVERSATION_UNRECOVERABLE`, link the new handoff/idempotency, and never apply this
fallback to uncertain or possibly accepted effects.

## Recoverable ownership

Record active native names, assignments, accepted handles and pending actions in existing direction
and experiment tracking. No new messaging service or scheduler. Before transferring any already
accepted work, reconcile its current observer and undelivered notices; confirm new adoption before
releasing the old observer. Preserve external identities, evidence and invocation budgets.
