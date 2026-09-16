> Historical binding / explanatory record after the 2026-09-16 control migration.
> The preserved body below is not a daily instruction source. Current method: hmasd-loop-dispatch.
> Frozen objects retain their original source versions and exceptions.

# Task collaboration

Control runs on Windows C:/Projects/HMASD with PowerShell. Resolve native IDs from runtime
results; read Agentify/provider settings from .codex/hmasd-transport.toml.
Historical task IDs are evidence, not dispatch routes.

## Native task tree

Root coordinates DM direction chains. Each DM owns science, implementation, self-checks, repairs
and acceptance, retains independent high-risk Reviewer review, and reuses one Luna/low native
experiment-monitor child for its accepted experiments. CM and Implementer assignments are suspended.
Do not create equivalent implementation roles under generic names.

Use collaboration.followup_task for work assigned to an existing non-Root agent, including
resuming an idle monitor or delivering evidence requiring action. Use collaboration.send_message
for facts to an active/waiting parent; it does not start an idle recipient's turn. Native final
returns complete a bounded assignment. Do not send duplicate work through both tools.

Root dispatches ready independent actions before waiting. While DM work is outstanding, Root
uses native collaboration.wait_agent. DM does independent work first, then uses the same native
long wait for its monitor or Reviewer. Under the current v2 contract, the configured 1500000 ms
default/minimum is an interruptible no-event timeout: child messages, completion notices and new
user input can return control earlier. Select other waits by their actual tool contract, response
needs and real limits; preserve fault, cancellation and concurrent-service response. Process an
arriving event promptly. An unchanged timeout requires only a brief continuation of waiting: no
rereading all cards, `list_agents`, repeated status queries, repeated assignment, keepalive or
progress broadcast. Do not replace an interruptible long wait with short unchanged polling loops.
Higher-priority system/developer limits still control and any concrete conflict is reported.

An unchanged timeout stays quiet. When a bounded assignment reaches completion, hits a material
blocker or scope conflict, or has no immediate authorized work while its direction remains ACTIVE,
the DM must send one proactive action message to its parent before returning a native final or
entering idle wait. That message names the assignment, state, evidence or commit, and next action
or dependency and its owner (or none), including the executed decision's authority and limit.
Use ordinary prose and existing evidence records, not a new schema or approval item. Root treats
message/final copies at the same assignment/evidence revision as one event, without an ACK.

If accepted card/Pro/grant scope fixes the work, the same DM completes implementation, checks and
required review, publication, fresh admission, launch/Monitor, collection, technical acceptance,
scientific intake, preservation and assigned cleanup, then its authorized dependent continuation.
Neither an additional Root dispatch nor integration/ACK nor a repeat Portfolio vote is needed.
An idle child with such unfinished work is resumed once with followup_task; an already running DM
continues directly. Actual shared-writer/runtime conflicts go to Root for execution coordination.
New scientific meaning or investment/budget choices go to the proper node, authored and intaken
by the DM under AGENTS §2; Root is not an intermediate scientific approver.

Distinguish a pending external dependency from ACTIVE-idle with none. A real dependency names its
request/handle/producer and required event; after independent work, wait for that direct return.
If no authorized work or concrete unresolved question exists, record the missing fact and revisit
condition once, send ACTIVE-idle once, and remain available in native event wait. A possible future
use or instruction is a condition, not a promised outside result. Root does not reassign the same
assessment on unchanged facts. A concrete new proposal can be prepared and sent by the original DM
without Root inventing or approving its scope; repeated inputs/options/consequence reuse the last
complete answer. A timeout supplies neither a new fact nor permission to retry, request an audit,
Send again or change lifecycle. Owner pause/stop boundaries still take precedence.

DM sends Root only actionable integration, cross-direction dependency, formal direction disposition,
scope-conflict, or bounded-assignment completion/ACTIVE-idle facts, with assignment identity,
commits/evidence, requested next action and uncertain effects.
Continue independent authorized direction work after a partial handoff. Root handles the changed
direction without waiting for siblings or routinely reloading the whole portfolio. Deduplicate
message and final copies by source, assignment and evidence revision. Root accepts artifacts;
message delivery is not acceptance. Routine specialist and monitor returns go directly to DM.

## Experiment observation

Follow EXPERIMENT_MONITOR.md. DM creates/reuses its monitor; Operator uses the exact native
monitor address supplied by DM and cannot create another child. Adoption and terminal facts go
to DM. DM collects results and completes scientific intake without Root forwarding terminal events.
Root receives the resulting actionable direction handoff, not every experiment status.

## DM-owned Agentify Transport

Each DM creates/reuses one native Luna/high Transport child with minimal context. DM authors and
publishes the exact handoff, dispatches via followup_task, and waits natively for the complete
archive. Transport owns Agentify Send, observation, one-Send reconciliation and direct DM receipt.
A verified complete bound response goes directly to conformance intake even while short receipt
or metadata reconciliation remains unresolved. An uncertain effect forbids another Send; it does
not turn that complete decision into a pending scientific answer.
Root receives the DM's conformance/decision mapping and integrates it. Root and DM continue native
waits while these dependencies run; there is no independent app-task wake branch.
Different provider bindings may proceed concurrently. Serialize each exact conversation and the
shared Portfolio node under its current author. Root uses its own native Transport only for
vacancy replacement after formal pause/closure leaves fewer than four occupied direction slots;
those archives return directly to Root for complete intake and Pro-selected DM creation. Existing uncertain or accepted requests
require same-request reconciliation, never a new Send after changing executor. Transport skill
owns exact Agentify arguments and immutable archival. Experiment monitor never operates Pro.
Verified nonacceptance permits same-request repair and continuation without a parent handshake.
Transport sends one direct archive receipt and records its actual native delivery outcome; no
ACK, Root forwarding or duplicate app-task wake follows. Its final closes that same assignment.
Historical HANDOFF IDs stay immutable; an assigned native recovery route is recorded separately.
At completion, material conflict or no-current-work while its direction remains ACTIVE, each
bounded assignment sends one direct action message to its assigning parent before final:
assignment, status, evidence/commit and next step. DM sends its actionable boundary to Root;
Transport sends to DM. A factual conflict needs no completed archive. Active generation remains
ongoing work and unchanged waits require no broadcasts. A later changed boundary preserves
the prior return and sends its own update once; this is not an ACK or forwarding chain.
If a leaf runtime lacks collaboration.send_message, its actionable native final is the direct
parent return. Record that actual capability/method; never fabricate tool delivery or add an app relay.

Pure Transport engineering defects default to local repair by the author DM, including focused
helper/fixture and skill updates with proportional review. Keep the same operation and immutable
receipts; involve Root only for a shared runtime/load, cross-direction dependency or scientific
decision. If the original conversation remains unrecoverable after supported same-request repair,
the author DM may rebind the identical frozen prompt to a new conversation only with verified
pre-Send nonacceptance (`sendAttempted=false`, no provider pairing). Preserve and close the old
operation as `CONVERSATION_UNRECOVERABLE`, link the new handoff/idempotency, and never apply this
fallback to uncertain or possibly accepted effects.

## Recoverable ownership

Record active native names, assignments, accepted handles and pending actions in existing direction
and experiment tracking. No new messaging service or scheduler. Before transferring any already
accepted work, reconcile its current observer and undelivered notices; confirm new adoption before
releasing the old observer. Preserve external identities, evidence and invocation budgets.
