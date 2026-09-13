# Task collaboration

Control: C:/Projects/HMASD, Windows PowerShell. Resolve current Root/Clerk/DM endpoints and main
writer from .codex/hmasd-dm-sessions.toml; old native names and queued clientThreadIds are not routes.
Independent DMs use gpt-6-astra/max, Clerk uses gpt-5.6-luna/high. Explicit task model settings do
not inherit automatically from a custom subagent role file.

## Independent tasks

Root is the user entry. DM owns its entire direction lifecycle; Clerk coordinates and records.
Direction Pro Convergence is the independent scientific Reviewer; Portfolio is the user report.
Use send_message_to_thread for actionable DM-to-Clerk and Clerk-to-DM handoffs. A final alone does
not deliver to another independent task. Messages give event/assignment/evidence revision, actual
DM decision, next owner/action and real dependency. Keep full science in the intake/review record.
Fact-only events need no ACK. Message delivery and completed consequences are distinct; deduplicate
while preserving unfinished actions. A concrete missing action triggers follow-up, not confirmation
loops. Clerk can end a handled turn; the next message starts another turn.

DM decides continue/defer/PARK/CLOSE/reopen/recast/family/C work, responds to independent scientific
review and reports decisions to Clerk directly. Clerk records dispositions without Portfolio or
Root approval. It reports released slots rather than creating replacements. Only an explicit owner
request initiates a cross-direction change or Portfolio consultation. Reporting does not authorize
implementation; no automatic global planning queue or per-object investment request exists.

Clerk uses compact wait_threads/cursors for missing facts and read_thread only where needed. It
never waits for independent DM messages through collaboration.wait_agent. The 50-minute heartbeat
is silent recovery for missed/interrupted events, not automatic planning. Owner pause takes priority.

## Native DM specialists and scientific review

DM owns implementation and acceptance, with independent high-risk code Reviewer coverage; no new
CM/Implementer chains. Its native Luna/low Monitor observes accepted experiment handles and returns
adoption/terminal facts directly to DM. DM collects/intakes, then sends only actionable outcomes to
Clerk. EXPERIMENT_MONITOR.md owns the observation procedure.

Direction Pro Convergence reviews science independently through the DM's native Luna/high Transport.
It examines design, evidence, interpretation, conclusions and successor plans; DM reads the full
review and responds to material findings with correction/claim limits or reasoned resolution.
The Pro review does not confer funding or lifecycle authority. Preserve scientific independence
and appropriate review coverage; it is not generic optional advice or a per-step approval ritual.

Use collaboration.followup_task for a native child's concrete assignment; collaboration.send_message
for factual parent returns, noting it does not start an idle native turn. Native final completes its
bounded assignment. Real Monitor/Reviewer/Transport producers retain their actual parent/wait route;
unchanged waits do not cause repeated status, reminders or duplicate requests.

Each exact Pro conversation has one executor. Keep accepted/uncertain requests, operations and
immutable archives; verified nonacceptance permits repaired same-request Send, not a new scientific
question. Direction DM repairs complex Transport defects; Clerk assigns a related Astra DM only for
an explicitly commissioned Portfolio Transport defect, preserving its real parent/operator.
No browser executor overlap. The Transport skill owns supported recovery and screenshot use.

## Recovery and integration

Root/Clerk serialize main index through a named writer handoff. Clerk integrates explicitly accepted
commits and records DM decisions, returns semantic conflicts to their DM, and never implements shared
policy/code itself. Independent task session worktrees are only hosting; reuse each designated
direction authoring checkout. Accepted legacy children/requests keep their original routes until
reconciled closeout; migration does not reparent or duplicate them. No extra relay service is needed.
