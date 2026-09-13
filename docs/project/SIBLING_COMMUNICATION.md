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
long wait for its monitor or Reviewer. Use the configured 1500000 ms default/minimum wait;
process an arriving event promptly. An unchanged timeout requires only a brief continuation of
waiting: no rereading all cards, status census, repeated assignment or progress broadcast.
The owner accepts periodic context reuse/cache refresh and brief continuation as design premises.
No per-DM keepalive messages, ACK loops, timers or separate relay are needed.

Wait only for an actual active dependency. A concrete blocker returns to its accountable owner;
an idle child with unfinished authorized work is resumed once with followup_task. Never interpret
a timeout as failed execution, a new invocation budget or permission to retry scientific work.
Owner pause/stop boundaries take precedence. No-work completion is not a reason to loop forever.

DM sends Root only actionable integration, cross-direction dependency, formal direction disposition or scope-conflict
facts, with assignment identity, commits/evidence, requested next action and uncertain effects.
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

## Recoverable ownership

Record active native names, assignments, accepted handles and pending actions in existing direction
and experiment tracking. No new messaging service or scheduler. Before transferring any already
accepted work, reconcile its current observer and undelivered notices; confirm new adoption before
releasing the old observer. Preserve external identities, evidence and invocation budgets.
