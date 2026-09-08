# Codex task communication

Use native `collaboration` tools for agents in the current Root's task tree.
Use `send_message_to_thread` for a separate app task, addressed by its exact task UUID.
The current Root, Portfolio and observation endpoints are configured in `.codex/`;
ROOT_OPERATIONS.md defines Portfolio planning, Root command execution/reporting and goal-driven observation. Portfolio sends concrete targets, actions and return routes; Root logs ordinary execution and sends actionable planning gaps to Portfolio instead of selecting a replacement task.

## Native agent messages

| Tool | Use |
| --- | --- |
| `collaboration.send_message` | Send evidence, an ACK or steering to an existing agent. It does not start a new turn for an idle agent. |
| `collaboration.followup_task` | Assign continued work to an existing non-Root agent; it wakes an idle recipient. |
| `collaboration.list_agents` | Resolve current canonical names and status when needed. |
| `collaboration.wait_agent` | Wait for agent messages or completion; this does not supervise an experiment process. |

Call native tools directly, outside `functions.exec`. Use the exact agent ID or
canonical task name returned by the current runtime. Across nested branches, prefer
the full canonical name. Do not substitute an app task UUID, display nickname, PID or
remote supervisor name. Use only tools exposed to the current task; report an actual
tool-access gap without inventing another route or creating a replacement task.

Reuse the existing recipient for related work. Send evidence to a running DM/CM with
`send_message`; use `followup_task` when idle work must resume. Tool acceptance and
the recipient's ACK are distinct facts. Reconcile uncertain delivery before retrying.

## App tasks and experiment observation

All cross-session `send_message_to_thread` calls, including Root's reports to Portfolio and
Portfolio's commands to Root, omit both `model` and `thinking`. These optional fields
change the recipient task's settings; they do not describe the sender or the cost of
the message. Never copy the sender's model/effort into a recipient's message. Omission
preserves the recipient's current settings. Portfolio effort is selected by the owner
in the app; do not set or restore a fixed effort through task messages.
Root handles its own dispatch and completion locally.

OWNER_DIRECT 2026-09-07: independent Transport owns Pro Send/observation/archive. Native
DM/CM authors normally hand their ready packet to Root using native collaboration; Root
sends its exact committed handoff to the configured Transport with an app message. An explicitly
authorized child direct-send uses the same route fields: source=actual child author UUID,
parent=Root app UUID, operator=Transport app UUID. Child app UUIDs are not native tool addresses.
Transport returns once to parent=Root, never to source as a fallback or extra copy. Root matches
the request to its existing assignment and forwards the unchanged evidence to the original
native recipient (`send_message` if running, `followup_task` if idle). Portfolio-authored
requests retain their explicit Portfolio parent. Missing native recipients follow the supplied
recovery route or a concrete Portfolio repair request; they do not cause another Pro Send.
Root's receipt of a return is a dispatch-skill trigger, independent of other directions.
Portfolio receives scientific updates at its configured task. Pro handoff routing
follows Prompt Author's rendered fields and the Transport skill.

DM/CM sends accepted experiment handles directly to Root. Supply the node, accepted
supervisor identity, launch SHA, cwd, log/result/receipt paths and responsible DM/CM
through the existing run record. Follow EXPERIMENT_MONITOR.md for adoption and ACK.
Root observes the same handle; CM retains collection and technical acceptance, and
DM performs scientific intake. Transferring observation never launches another run.

Private terminal sessions do not become accessible merely by forwarding their IDs.
Use the recorded detached supervisor, process identity and existing exit witness.
Supervisor state establishes process termination; it does not establish scientific
validity. Observation runs within the owner's active goal, without a scheduled automation.

## Root-to-Portfolio notification filter

Owner correction, 2026-09-07: the observed violation was **logging and also sending the same
routine receipt**, not missing log coverage. Apply this filter at the tool call itself:
before calling `send_message_to_thread`, state the concrete action Portfolio must take now
that the existing command does not already provide. If no such action exists, omit the call.
This is a reading/behavior rule, not a new script, schema or permission gate.

Recent examples: "6701 is COMPLETE; I will integrate and execute the authorized6702" is log-only;
"I resumed the requested repair" is log-only; "I will integrate these already-authorized
commits after your ACK" adds an unauthorized waiting step and must not be sent. An actual
shared-index conflict uses the short index handoff below, without bundling scientific progress.
"Three advancing chains remain and two exhausted slots need replacement commands" is an
internal Portfolio planning request, sent once per changed need. An outstanding request has
no periodic reminder; new goal turns do not reset this rule. Reports name the missing action
first and link evidence, omitting unrelated completion history and already-known status.

Portfolio handles internal requests through commands or repairs without an automatic
user-facing response. Notify the owner for an actual owner decision, the requested aggregate
deliverable, or a direct status question; do not narrate every internal coordination event.

OWNER_DIRECT 2026-09-07: ordinary execution receipts belong in
`docs/research/portfolio/root-log/YYYY-MM-DD.md`, using the local date. Root owns this
append-only daily log. Each meaningful entry gives time with timezone, direction/command,
what changed, evidence/commit or accepted handle, and the already-assigned next action.
Link original evidence rather than copying it; maintain EXPERIMENT_TRACKING.md as the current
operational state. Batch log entries into ordinary commits at clean boundaries; no per-entry
commit, notification, new scheduler or periodic digest is required. Portfolio reads relevant
entries when planning or when asked; it need not ACK each entry or poll the log.

OWNER_DIRECT follow-up: do not forward informational Root returns into the Portfolio task,
and do not append "actionable" to a routine receipt to bypass this filter. A sent message must
name an actual Portfolio decision or repair needed. Dispatch-count confirmations, completed
pushes/index-release notifications and unchanged pending-request reminders belong in the log
unless Portfolio explicitly requested that specific response. Portfolio does not echo or send
a user-facing progress/final message solely to acknowledge an informational Root return.
Root owns the main index by default under the rule below. Ordinary index operations create
no notification exception. Only Portfolio's explicit temporary-transfer request creates a handoff.

Dispatch ACKs, integration/push receipts, accepted launches, healthy observations, intermediate
returns and terminal events with an executable named collection/intake/follow-on route are
log-only. Continue that route and notify its responsible native DM/CM as needed. A completion
requires a Portfolio message only when the assigned route is exhausted and creates an
actionable vacancy or requires a new command. Routine evidence stays available in the log.

Send Portfolio a new command/replacement or working-set decision needed, an unresolved
scope/authority/scientific conflict, or a changed dependency/uncertain external effect that
requires Portfolio action. Root also reliably escalates any problem it cannot resolve within
the supplied route: execution failure, missing input/tool/access, or uncertain state. This is
a repair request even when no scientific or Portfolio-tier decision is needed. Include the
failed action, exact error/evidence, repairs already attempted, affected dependency and help
needed. Send promptly once outside the assigned repair path; do not silently log it, wait for
the next observation pass, repeatedly retry, or stop all independent work. Portfolio owns arranging the
bounded repair and returning its next step; Root resumes at that step and reports a changed
blocker if it persists. Reconcile ordinary technical issues within the assigned route first;
never conceal a planning gap until the whole batch finishes. Name the decision/action needed,
the affected directions and relevant log/evidence, with a compact working-set delta. Coalesce
related facts and do not repeat an unchanged request. Explicit temporary-index transfers and direct
replies to an explicit Portfolio/owner request remain allowed; keep them concise. All these
messages preserve the recipient's model settings as specified above.

## Send/no-send conditions — OWNER_DIRECT 2026-09-08

Before each Root-to-Portfolio tool call, apply these conditions in order. This is a
behavior rule, not a new validator, scheduler or required message schema.

1. If Portfolio explicitly requested this specific reply, answer it once. A general
   instruction to keep working, maintain five directions or record progress is NOT a
   request for replies. A command receipt is NOT a requested ACK.
2. Otherwise send only if Portfolio must now (a) supply a missing next command or
   replacement after the supplied route is exhausted, (b) resolve a scope/science/
   authorization conflict, or (c) arrange a repair for an execution/input/tool/access
   problem or uncertain external acceptance outside the supplied repair route.
   Start with the actual action needed and cite the evidence. If none applies, DO NOT SEND.
3. If that same need was already sent and its evidence/dependency has not materially
   changed, DO NOT SEND. Waiting time, a new goal turn, another log commit, or an
   unanswered request is not a changed need. Retain the pending request and work on
   independent authorized tasks. A new failure or correction that changes the required
   action may be sent once with the precise change.
4. If an existing command already supplies collection, integration, next arm, DM intake,
   recipient resumption or another next step, perform it and log the fact. Do not request
   confirmation to execute it and do not copy its native-recipient receipt to Portfolio.

Always log-only: accepted dispatch/launch, healthy observation, terminal result with a
named return route, code acceptance, cherry-pick, commit/push, readiness resume, counts
without a new capacity decision, ordinary index operation, and default-index release.
Do not attach any of these to a message merely to turn them into a notification. Relevant
evidence may accompany a real new action request; unrelated progress must be omitted.
Do not send "please confirm index idle", "ACK", "index released", "applied", "pushed",
"still waiting" or a request to ACK a request, except the explicit transfer replies below.
The labels "action needed", "handoff" or "coordination" do not create an exception.

| Event | Required Root behavior |
| --- | --- |
| G ends; command supplies C next | Log G and launch C; no Portfolio message |
| CM code arrives; command supplies integration and DM readiness | Integrate/push and resume DM; no Portfolio message |
| Ready routine receipt edits | Commit explicit ready paths at a clean boundary; no idle query or release notice |
| DM finishes; no successor command exists | Send one exact next-command need; do not resend while unchanged |
| Tool fails outside the assigned repair route | Send error/evidence and the concrete repair need once; retain independent work |
| Portfolio has already received a next-task request | Wait for its answer while doing other authorized work; no reminder |

Batch already-ready related routine log/tracking edits at a clean boundary. Do not create
one commit merely for every start/terminal/collection/intake notification. Do not delay
required source/card publication, a ready dispatch or a real blocker to assemble a batch.
Every created commit still pushes immediately. Portfolio does not ACK unsolicited routine
messages or turn them into owner-facing status reports.

## Shared main checkout: default index owner — OWNER_DIRECT 2026-09-08

This replaces the prior per-operation mutual ACK rule. Root is the default main-index
operator. Root stages, commits and cherry-picks authorized explicit paths WITHOUT asking
Portfolio whether it is idle and WITHOUT sending a release notice afterward. Portfolio
normally edits its owned files and names the exact ready paths in its substantive command;
Root publishes them before dispatch. Root must not stage unfinished/unrelated Portfolio work.
File editing ownership remains separate: a real overlapping edit conflict is coordinated
once, not presumed for every index operation. Other worktrees are unaffected.

Only if Portfolio actually needs to stage/commit/cherry-pick itself does Portfolio request
temporary use, naming its paths/operation. Root completes any current index transaction and
push attempt, replies once granting the transfer, then starts no new main-index operation.
Portfolio waits for that grant, performs the named operation and push attempt, then sends
one return-of-index message. Root resumes default ownership without replying to that return.
While transfer is held, reads/native dispatch/other worktrees continue. A failed push retains
the commit and retry obligation; a clean index can be returned. No periodic idle check,
automatic expiry, release ACK, lockfile, lease or scheduler is added.

An in-progress cherry-pick/conflict must be resolved by its initiating session, or its explicitly
assigned resolution owner, before the other session stages any path. If unrelated authorized
edits may already be included, inspect the resulting commit and remaining diff, attribute
included paths and commit only outstanding changes. Preserve history; do not blindly repeat
the operation, reset, stash or silently rewrite it. No lockfile, lease or scheduler is introduced.
