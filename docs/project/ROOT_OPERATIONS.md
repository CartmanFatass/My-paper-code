# Portfolio plans; Root executes

Portfolio (`gpt-6-astra` / `max`) plans the research queue and prepares bounded commands.
Root (`gpt-5.6-luna` / `xhigh`) executes those commands, integrates specified deliveries,
observes accepted experiments and performs exact Pro transport. The owner directs this
boundary. DM owns scientific decisions within its existing delegation; CM owns technical
judgment and acceptance. Existing Pro authority, scientific budgets and model settings remain.

## Endpoints and files

Root is task `01a07249-b095-7821-8ce2-e9c32ba85267` in `C:/Projects/HMASD`.
Portfolio's exact task and checkout are in `.codex/hmasd-portfolio.toml`; it works directly
on main and owns `docs/research/portfolio/PORTFOLIO.md`. Root owns operational facts in
`docs/research/portfolio/EXPERIMENT_TRACKING.md`. Coordinate overlapping edits, commit
explicit paths and push immediately. Current commands belong beside the current Portfolio
working set; their dispatch/handle/receipt facts belong in existing tracking. Historical
records are evidence, not a command queue.

## Portfolio prepares the command

Portfolio resolves readiness, direction ordering, slot replacement, task scope, dependencies
and the action to take after a return before dispatch. It reads the relevant current card,
intake and CM/DM return and sends a concrete task; it does not ask Root to choose which
candidate is runnable or infer the meaning of a failed experiment. DM and CM retain their
scientific and engineering work. Portfolio sends a missing scientific decision to the DM or
proper Pro node under the existing ladder; it does not decide for that node.

Use ordinary prose with these five items, referring to an existing card/assignment for facts:

1. **Target and action:** exact existing agent/task, and one bounded deliverable or command.
2. **Inputs:** exact current paths/sections, commit or request identity, and supplied payload.
3. **Bounds:** what this task may execute, its existing budget and its completion/stop condition.
4. **Return route:** who receives the result and which exact follow-on actions Root should execute.
5. **Report conditions:** missing input, failure, uncertain external acceptance, conflicting
   bytes/instructions, or a requested action outside those bounds; name Portfolio as recipient.

Label a batch's commands so receipts can identify them; an existing assignment/request ID is
sufficient. This is a concise handoff, not a new schema, registry or validation tool. State
independent commands explicitly and name any actual dependency. Put a preparation-only limit
on its particular command. An execution command may dispatch an already selected experiment
under its frozen assignment; Root need not ask the owner again. A new task supersedes the
completed preparation task's stop boundary only for the explicitly assigned work.

Portfolio plans toward five advancing direction chains, confirms actual dispatches and fills
vacancies with new concrete commands. Preparation, implementation and intake count as work.
A command restricted to preparation and an empty observation queue do not stop other assigned
commands. Portfolio interprets object/family stops and selects the appropriate next task.
It preserves lifecycle, priority and scientific authority; scheduling does not change them.

At every completion or exception, Portfolio handles the entire current working set before
returning: retain active assignments, resolve returned dependencies, and send all justified
independent continuations/refills as one batch. A next command for the reporting direction
alone is insufficient when other commands have ended or never reached their recipient.
Name any unfilled slot's concrete dependency; do not create redundant work to reach five.
Keep collection, intake and already-selected implementation/execution in one prewritten route
where their boundaries are known. Routine technical returns on that route do not each require
another Portfolio message. New scientific choices still belong to DM or the proper Pro node.

## Root's execution loop

Read the current owner instruction and received commands. Read only their required inputs
and the applicable execution skill; the Portfolio candidate list is planning context.

1. Dispatch every independent command once to its named recipient. Reuse an already accepted
   dispatch. Use native `send_message` for a running child and `followup_task` to resume an idle
   child. Record actual tool acceptance; an intended handoff is not a completed dispatch.
2. Report the batch's accepted dispatches and any failed/missing target to Portfolio. Then wait
   for the assigned native returns and handle accepted experiment/Pro observation. Do not wait
   after the first dispatch while other independent commands remain unsent.
   The report includes the whole current working set, not just the last command: actual native
   recipient, running/returned/unavailable status, current task and unsent commands. Reuse a
   fresh inventory until a native event changes it. If an old recipient is absent, try its
   resumable identity; an unavailable identity is a dispatch gap, not a scientific blocker.
   Apply an explicitly supplied replacement route or report that exact gap immediately.
3. On a return, execute the command's explicitly named integration, collection or intake route.
   Forward the original result and evidence path/commit to Portfolio. Technical acceptance is
   supplied by CM and scientific interpretation by DM; Root reports those claims as attributed
   returns rather than independently redoing them.
4. If an action fails, lacks a supplied input, has an uncertain external effect, conflicts with
   the command, or requires an unlisted next action, report the concrete fact to Portfolio and
   hold only that action. Continue the other issued commands. Root does not select a substitute
   direction, new scientific task, altered retry or alternative implementation.
5. While an assigned native DM/CM is still running and has not returned completion or a
   blocker, continue native waiting and process its return. Finishing one command does not end
   the other native assignments. When the batch is finished, or only experiment/Pro observation
   or a requested Portfolio reply remains, report each command's state and next sender/event,
   then return with the existing observation route retained where needed. An empty executable
   queue goes to Portfolio for the next batch; Root does not improvise work or declare the
   research programme complete.

Keep routine local execution details local: tool addressing, a supplied path, or an ordinary
read command needs no planning round. A clean, specified Git delivery may be integrated and
pushed as commanded. Merge conflicts, unexpected changed paths, missing acceptance evidence
or a required check failure are reported with the exact gap; Portfolio assigns the repair.
A clear pre-acceptance tool rejection may be retried with the same payload after its mechanical
cause is fixed. Unknown Send/launch acceptance requires observation, never a blind retry.

### Report events

| Observed event | Root action |
| --- | --- |
| Batch dispatched | Send command labels, actual recipients and tool acceptance to Portfolio. |
| Named task completed | Forward its original return and artifacts; execute the prewritten return route and include the updated whole working-set state and any vacancy for Portfolio. |
| Accepted experiment terminal | Notify its named CM for collection and Portfolio with process facts; DM intake follows the command. |
| Matching Pro response archived | Return the full fixed-file/archive location to the declared DM/Portfolio; notify Portfolio of the command completion. |
| Missing input, failed action, conflict, uncertain acceptance or extra-scope request | Send exact fact, evidence and affected command to Portfolio; continue unrelated commands. |
| Assigned direction yields or becomes unavailable | Report its actual native state and remaining dependency immediately, without waiting for the other directions or the whole batch to finish. |
| No executable command remains | Send completed/pending command states and next sender/event to Portfolio once. |

A receipt states the command label, actual result/recipient, evidence and any missing fact in
a few lines; do not repeat the original contract. Unchanged healthy observation is silent. Portfolio replies with the next concrete command or
an explicit wait dependency; Root does not repeatedly ask the same question. Routine app
messages preserve the recipient's model/effort. New Pro dispatch uses the Author-rendered
settings. Root never sends an app message to itself. A native DM source with Root as app parent
gets a local receipt forwarded to that DM through native collaboration.

Current artifacts and exact return commits outrank an old native task summary. For example,
a completed experiment's E0 return must not be replaced by its earlier implementation intake
when identifying the next owner. A committed command, an intended dispatch and a currently
running native assignment are three different facts; record the actual one. An implementation
or execution stop applies only to its named command. A later explicit continuation supersedes
that boundary within its stated scope, including authorized reversible staging repairs.

## One shared observation wake

Root observes assigned experiment handles and exact current Pro requests through the existing
`hmasd-experiment-monitor` heartbeat, every thirty minutes. Endpoint and schedule are in
`.codex/hmasd-monitor.toml`. Use `EXPERIMENT_MONITOR.md` for adoption and the Transport skill
for exact request identity, model verification, Send state, archiving and receipt delivery.
The timer observes accepted work; it does not select tasks or refill the research queue.

Keep the heartbeat ACTIVE while any assigned experiment needs observation/terminal notification
or any current Pro request needs scheduled reconciliation, generation observation, archival or
delivery. An explicit terminal blocker with no scheduled recovery is reported to Portfolio and
needs no repeated wake. Pause when that combined observation set is empty. Preserve the existing
id, full prompt, thirty-minute schedule and Root target; read back ACTIVE before adoption ACK.
A paused observation heartbeat says nothing about completion of native research tasks.

Each wake reads current assigned rows, batches independent supervisor checks, observes due Pro
requests serially and applies the report table. It executes remaining explicit commands and
return routes; unlisted actions go to Portfolio. Historical handles and requests are not adopted
by scanning archives. No new scheduler, polling task, per-request heartbeat or goal is created.

Owner pause changes the affected work first while preserving accepted-process observation and
unknown-Send evidence. Waiting for one conversation does not hold other issued commands.
Record only meaningful state changes with the exact handle/request, responsible recipient,
evidence and receipt state in existing tracking. Recover from those current facts, not by
reconstructing every direction's history.
