# Task collaboration

Control runs on Windows C:/Projects/HMASD with PowerShell. Resolve native IDs from runtime
results; resolve the independent Transport endpoint from .codex/hmasd-transport.toml.
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

DM sends Root only actionable integration, cross-direction dependency, Pro handoff or scope-conflict
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

## Independent Transport

Root sends the exact committed Pro assignment to the independent Transport using app-task
messaging. Transport retains one-Send reconciliation, observation, archive and direct Root receipts.
Cross-task messages omit model/effort overrides. Root forwards the full response to the original
DM for scientific/specification intake using followup_task. Native waits continue while native
work remains; if only Transport work remains, Root may end the turn and its receipt wakes Root.
No native agent or experiment monitor performs Pro browser operations.

## Recoverable ownership

Record active native names, assignments, accepted handles and pending actions in existing direction
and experiment tracking. No new messaging service or scheduler. Before transferring any already
accepted work, reconcile its current observer and undelivered notices; confirm new adoption before
releasing the old observer. Preserve external identities, evidence and invocation budgets.
