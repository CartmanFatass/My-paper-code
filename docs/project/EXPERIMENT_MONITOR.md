# DM-owned experiment observation

Each DM creates one reusable native Luna/low experiment-monitor child on its first accepted
experiment and reuses it across that direction's handles. Use the registered HMASDExperimentMonitor
role with fork_turns=none and only this procedure plus exact handle facts. If an existing runtime has not loaded that role, spawn a default child with explicit
model gpt-5.6-luna, reasoning_effort low and fork_turns=none, supplying the role instructions
and this document. Do not inherit the DM's full research conversation merely to monitor handles.
No child is created for an idle direction. Root and DM wait natively under SIBLING_COMMUNICATION.md.

## Assignment and adoption

DM owns exact launch inputs, resource admission, collection, technical acceptance and scientific
intake. An optional Operator executes its named batch and uses the monitor address supplied by DM.
After actual launch acceptance, send MONITOR_ADD via followup_task with direction/assignment ID,
DM canonical name, node/supervisor handle, launch SHA, cwd/output/evidence paths, observation bound
and relevant stop instructions. The monitor does not discover work by scanning historical handles.

The monitor queries the exact handle, records direct status and replies MONITOR_ADOPTED to its DM
with its native identity, adopted handles, observation time and evidence. Dispatch success alone
is not adoption. DM retains pending ownership until this receipt, then stops routine process
polling and uses native long waits. A first observation may already be terminal; report both facts.
No independent app-task goal, goal-adoption handshake or Root relay is required.

## Observation loop

Keep a compact recoverable handle list in the existing direction execution record or assigned
output path: handle identity, last observation, next due check and delivery state. Reuse one child
for multiple handles; batch independent due checks. Use bounded commands and interruptible waits
no longer than 60 seconds per tool call, checking at the assignment's useful interval. Longer
check intervals can span several waits without model-visible progress messages to DM. Do not let
one inaccessible handle block observation of others. Unchanged healthy status needs no message or
commit. The DM's configured long wait supplies periodic parent continuation; the monitor does
not send artificial keepalive messages.

Use .codex/hmasd-compute.toml and supplied exact supervisor identities. Read bounded logs only
when useful. Connection failure, missing PID or wait timeout alone is unknown, not terminal.
The monitor never launches, retries, alters or stops an experiment, chooses science, gathers full
scientific results or creates children. Local work requires a stable process identity and an
accessible terminal witness, not another task's private terminal session ID.

## Terminal facts and reuse

On completion or a material observation failure, send MONITOR_TERMINAL or MONITOR_BLOCKER directly
to the DM using native send_message. Include a stable event ID, exact handle, source/output paths,
direct status, bounded evidence and unresolved effects. Deliver each event promptly without
waiting for all experiments. Save delivery state and reconcile uncertainty on the same event
before retrying. Do not require an ACK loop. Successful observation is not scientific acceptance.
DM processes the event, collects and checks outputs, obtains independent review where required,
and continues the authorized direction. Root is involved only for a concrete Root-owned action.

When the active set and pending notices are empty, return a native final with terminal event IDs
and empty active_set. Do not poll completed handles or keep an empty monitor running. If an Operator owns collection, DM resumes that same Operator
with followup_task after terminal notice; no parallel collection or polling. A later
nonempty assignment resumes the same child with followup_task. If observation must transfer,
preserve handles and notices and obtain actual replacement adoption before releasing ownership.
Owner pause/stop instructions control which observation or closeout is permitted; no new run or
research resumption follows from a monitor assignment or workflow change.
