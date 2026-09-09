# Native agents and Transport communication

Root combines research planning and execution. Use native `collaboration` tools for its agent
tree and `send_message_to_thread` for the independent Transport task in `.codex/hmasd-transport.toml`.
ROOT_OPERATIONS.md defines responsibility and observation. Planning, replacement selection and
Portfolio intake happen locally in Root.

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

## Independent Transport

App messages omit `model` and `thinking` to preserve the recipient's settings. Native DM/CM
authors deliver ready packets to Root; Root sends the exact committed handoff to Transport.
New requests name the actual author as source, Root as parent and Transport as operator.
Root-authored Portfolio questions use Root for both source and parent. Transport returns one
factual receipt to the declared parent; source is not a fallback receipt destination.
Root forwards direction evidence with `followup_task` when intake or continuation is required
and performs Portfolio intake itself. Preserve unknown Send state and reconcile the original
request before recovery. No second Send follows from a routing failure.

## Experiment adoption and records

DM/CM supplies Root the accepted supervisor handle, node, launch SHA, cwd, evidence paths and
responsible recipient in the existing run record. Follow EXPERIMENT_MONITOR.md for observation
adoption. Root observes the same handle; CM collects and checks technical evidence, DM performs
scientific intake. A private terminal ID does not transfer process access.

Root maintains useful execution facts in EXPERIMENT_TRACKING.md and the existing root-log:
time, direction, exact handle/request, evidence and actual continuation state. Distinguish
pending work from accepted and running work. Use observed event time or actual recording time.
Batch ready routine record edits at clean boundaries; do not delay required publication or
ready work to assemble a batch. Push every commit immediately.

Root owns main's index and ready control-plane files. Coordinate an actual overlapping edit
or index transaction with its writer; complete an in-progress conflict before another writer
stages paths. Preserve unrelated edits and inspect actual Git state before repeating operations.
Use explicit paths without reset, stash, history rewrite or automatic locking machinery.
