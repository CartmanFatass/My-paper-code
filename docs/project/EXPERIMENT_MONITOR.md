# Experiment observation ownership

This document owns experiment observation and handover procedure. AGENTS §5–7 controls
scientific execution, resources and Git; ROOT_OPERATIONS.md assigns planning and acceptance.
Independent Transport observes Pro requests under its own skill.

## Independent monitor — OWNER_DIRECT 2026-09-09

One reusable independent Luna/low Codex task, configured in `.codex/hmasd-monitor.toml`,
observes multiple explicitly assigned accepted experiments. DM owns launch, terminal collection, technical acceptance and separate scientific intake;
an optional Operator executes its assigned batch. After confirmed monitor adoption,
DM and Root do not maintain parallel status-polling loops. Independent Transport remains
separate and observes Pro requests.

Read the endpoint from the live primary control checkout (currently
`/home/fires/projects/HMASD/.codex/hmasd-monitor.toml`, supplied in the handoff), not a stale direction
checkout or the frozen remote scientific SHA. Endpoint currentness does not change scientific
source bindings. Root carries this exact live configuration path in new DM assignments.

The monitor uses an active goal: observe all explicitly adopted accepted experiments, deliver
each terminal notification, and finish when no observation or notification remains outstanding.
It first reads its goal state. With an active goal, update the monitored set and task instructions
and continue that goal; do not create a duplicate. With no active goal, create one only for a
nonempty assignment, without an invented token budget. New accepted
handles can join the active set by message; the goal describes this set rather than a fixed
single handle. The current goal tool only updates completion/blocked status, not objective text;
never fake an objective rewrite or mark unfinished work complete just to rename it.
A completed goal is not an idle timer: a later assignment starts a new goal in
the same task. Never claim to edit an existing goal through an unsupported tool operation.

Keep a small recoverable task-local list of assigned node, handle, launch SHA, cwd, output and
receipt paths, Root destination, original execution/DM owners, latest observation and notification state.
This is the monitor's working record, not a new repository registry, service or scheduler.
Root's existing tracking records monitor assignment and material changes. Do not discover work
by scanning historical handles or create a task/worktree per experiment.

## Assignment, adoption and return

After launch acceptance, DM/Operator sends `MONITOR_ADD` directly to the configured monitor
with the exact handle facts and original owners. This direct dispatch is authorized by
OWNER_DIRECT 2026-09-09; it does not wait for Root to forward the launch or create another goal.
The monitor itself creates or continues its set-scoped goal. A runtime without the cross-task
tool returns the exact routing gap and handle to Root for forwarding; it must not invent a
message API or silently substitute a second observer. DM records the accepted dispatch
and returns pending collection; it does not continue a routine remote-status polling loop.
The monitor checks the same supervisor and sends `MONITOR_ADOPTED` directly to Root with its
actual task ID, goal state, observation time and direct status. Root confirms adoption to the
original execution/DM owner. A dispatched message alone is not adoption: until confirmed, record adoption
as pending; a rejected/unavailable dispatch or reported observation loss returns promptly to
Root for the same-handle recovery. This pending boundary is not a second DM polling loop.
A first query may already be
terminal; then adoption and terminal facts can be delivered together.

The monitor saves direct terminal status and useful bounded log evidence in its own outputs,
then sends `MONITOR_TERMINAL` directly to Root, including a stable event ID, original execution/DM owners,
handle/source/cwd/root and evidence paths. No second Relay copy is needed. Root deduplicates
against already received native facts and uses native `followup_task` on the original execution/DM owner
when collection/intake still needs execution. If they already collected and are acting, convey
only the new facts without dispatching duplicate work. Monitor exit-zero facts are not technical
or scientific acceptance. DM collects and verifies artifacts and separately interprets the result.

Cross-task messages omit model/effort overrides. A monitor app task cannot address Root's native
children by inventing app IDs. Record accepted or uncertain message delivery. Reconcile an
uncertain terminal send by the same event ID before retrying; do not finish the goal with an
undelivered notification. Accepted app delivery does not require a Root ACK loop. Before goal
completion, reconcile newly received additions and ensure the active set and pending notices
are empty. Completed entries are retained as receipts, not polled again.

## Multiple experiments and bounded observation

Each round checks all due handles, batching independent read-only queries (including across
nodes). One experiment's terminal event is sent immediately without waiting for other experiments
to finish. A failed connection for one handle stays unknown and does not block checks or notices
for the others. Use bounded connection/command waits and interruptible intervals of about60s;
the interval is a working target, not a guaranteed delivery deadline. Do not spend an unbounded
blocking wait on a single handle or poll the monitor's own Codex task status as remote evidence.

Use the configured node/supervisor from `.codex/hmasd-compute.toml`, currently:
`ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task status <accepted-name>`.
Read bounded logs only when useful and quote supplied handles as data. SSH failure or PID absence
alone is unknown; a wait timeout is not terminal. Healthy unchanged state needs no repeated
messages or commits. The monitor never launches, retries, alters or stops scientific work,
collects full scientific results, or interprets outcomes. For local accepted work, the supplied
identity must include PID/start identity and an accessible exit witness, not a private exec ID.

If the monitor loses access or must stop, report the affected handles and uncertain effects to
Root; unrelated accessible handles continue. Root recovers this same task/handle set or confirms
another actual observer. No fresh scientific invocation follows. This goal-driven task is not a
remote callback or a guarantee of progress while the app/session is unavailable. No heartbeat or
additional scheduler is enabled by this instruction. On owner pause, follow the specific permitted
observation/closeout boundary and preserve accepted identities.

For legacy accepted CM handles, preserve the original owner and parent until explicit closeout
or transfer to DM. Role consolidation never changes a supervisor handle or authorizes a new run.
