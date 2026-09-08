# Codex task communication

Use native `collaboration` tools for agents in the current Root's task tree.
Use `send_message_to_thread` for a separate app task, addressed by its exact task UUID.
The current Root, Portfolio and observation endpoints are configured in `.codex/`;
ROOT_OPERATIONS.md defines Portfolio planning, Root command execution/reporting and goal-driven observation. Portfolio sends concrete targets, actions and return routes; Root logs ordinary execution and sends actionable planning gaps to Portfolio instead of selecting a replacement task.

## Native agent messages

| Tool | Use |
| --- | --- |
| `collaboration.send_message` | Notify an existing agent when no new work is requested. It does not start a turn and is not an execution handoff. |
| `collaboration.followup_task` | Assign work or deliver a result requiring collection, intake, repair or continuation to the same non-Root agent. It wakes an idle recipient and delivers to a running recipient. |
| `collaboration.list_agents` | Resolve current canonical names and status when needed. |
| `collaboration.wait_agent` | Wait for agent messages or completion; this does not supervise an experiment process. |

Call native tools directly, outside `functions.exec`. Use the exact agent ID or
canonical task name returned by the current runtime. Across nested branches, prefer
the full canonical name. Do not substitute an app task UUID, display nickname, PID or
remote supervisor name. Use only tools exposed to the current task; report an actual
tool-access gap without inventing another route or creating a replacement task.

Choose the tool by the action requested, not a remembered running/idle status. Use
`followup_task` for every native work handoff, including terminal experiment facts or a
Pro response that requires the recipient to act. Reuse the same recipient and assignment;
do not send the same work through both tools. `send_message` is only a notification with
no new execution obligation. An agent may finish between a status read and a message.

A written return route or successful `send_message` is not dispatched work. After a work
handoff, retain its actual tool outcome; at the next event boundary check a current turn
or a new return before counting that direction as advancing. A fast completed return is
handled immediately. If earlier work was only notified to a now-idle recipient and has
no accepted continuation or result, resume the same assignment once with `followup_task`.
Do not require an ACK before other ready work, repeat a live assignment, or revive a
restricted operation. Reconcile uncertain delivery from the same recipient's state.

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
native recipient with `followup_task` when intake or continuation is required. Portfolio-authored
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

## Root records and owner communication

Root records operational facts in `docs/research/portfolio/root-log/YYYY-MM-DD.md`
(local date) and maintains `EXPERIMENT_TRACKING.md`. Each entry names time, direction,
evidence/handle and the already-assigned next action. Distinguish pending work, an accepted
work handoff and actual running/returned work; do not label a narrative next step active.
Use the observed event timestamp when available and the actual recording time otherwise;
do not invent or backdate event times. Portfolio reads these records when
planning; writing an entry never creates permission to send a message.

Portfolio handles internal requests without an automatic owner-facing report. Notify the
owner for a direct question, requested deliverable or actual owner decision. Preserve
recipient model settings. The following conditions are the single current notification rule.

## Send/no-send conditions — OWNER_DIRECT 2026-09-08

Before each Root-to-Portfolio tool call, apply these conditions in order. This is a
behavior rule, not a new validator, scheduler or required message schema.

1. If Portfolio explicitly requested this specific reply, answer it once. A general
   instruction to keep working, maintain five directions or record progress is NOT a
   request for replies. A command receipt is NOT a requested ACK.
2. Otherwise send only if Portfolio must now supply a working-set replacement,
   make a cross-direction choice, or resolve a concrete conflict beyond the assigned
   DM/CM route. First resume the original DM for direction-local acceptance, CM work,
   source integration and decisions within its standing authority. A completed step,
   ordinary repair or omitted intermediate instruction is not itself a Portfolio need.
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
| DM returns a selected card/specification or an in-scope next step | Resume that DM to organize CM and continue; no Portfolio message |
| Assigned direction has no continuation within its authority | Send one exact replacement/conflict need; do not resend while unchanged |
| Tool fails outside the assigned repair route | Send error/evidence and the concrete repair need once; retain independent work |
| Portfolio has already received a next-task request | Wait for its answer while doing other authorized work; no reminder |

Batch already-ready related routine log/tracking edits at a clean boundary. Do not create
one commit merely for every start/terminal/collection/intake notification. Do not delay
required source/card publication, a ready dispatch or a real blocker to assemble a batch.
Every created commit still pushes immediately. Portfolio does not ACK unsolicited routine
messages or turn them into owner-facing status reports.

## Portfolio response to a nonconforming Root message — OWNER_DIRECT 2026-09-08

Apply this procedure when a Root message arrives, not on a timer or heartbeat.
Portfolio first checks the received message against the send/no-send conditions above.
A genuine new replacement or unresolved conflict receives its normal substantive action.
For a nonconforming message, inspect the specific original assignment, recipient and
delivery evidence needed to locate the cause; do not reconstruct every direction.
Correct the controlling document if it is missing, contradictory or stale. If the rule
already covers the case, correct the execution and resume the affected authorized route
through Root instead of adding another rule. Send one concrete repair instruction only
when Root must act, then verify its actual acceptance or affected result. Preserve other
advancing work and all scientific, tool and uncertain-acceptance boundaries.
Do not ACK the invalid notification, create periodic scans, request routine reports or
add a scheduler. Repeated unchanged messages belong to the same open repair, not repeated
repair dispatches. This is a response procedure for received events, not a new runtime hook.

## Shared main checkout: default index owner — OWNER_DIRECT 2026-09-08

Root is the default main-index operator. Root stages, commits and cherry-picks authorized explicit paths WITHOUT asking
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
