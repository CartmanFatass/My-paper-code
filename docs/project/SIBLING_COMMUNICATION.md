# Task collaboration

Control: C:/Projects/HMASD, Windows PowerShell. Resolve current Root/Clerk/DM endpoints and main
writer from .codex/hmasd-dm-sessions.toml; old native names and queued clientThreadIds are not routes.
Independent DMs use gpt-6-astra/max, Clerk uses gpt-5.6-luna/high. Explicit task model settings do
not inherit automatically from a custom subagent role file.

## Independent tasks

Root is the user entry. DM owns its entire direction lifecycle; Clerk coordinates and records.
Direction Pro Convergence is the independent scientific Reviewer; Portfolio supplies user reports and delegated vacancy selection.
Use send_message_to_thread for actionable DM-to-Clerk and Clerk-to-DM handoffs. A final alone does
not deliver to another independent task. Messages give event/assignment/evidence revision, actual
DM decision, next owner/action and real dependency. Keep full science in the intake/review record.
Fact-only events need no ACK. Message delivery and completed consequences are distinct; deduplicate
while preserving unfinished actions. A concrete missing action triggers follow-up, not confirmation
loops. Clerk can end a handled turn; the next message starts another turn.

DM decides continue/defer/PARK/CLOSE/reopen/recast/family/C work, responds to independent scientific
review and reports decisions to Clerk directly. Clerk records dispositions without Portfolio or
Root approval. A scientific PARK includes committed PARK.md and a direct Clerk notification before
DM ends. Clerk verifies preservation/producer handover, records and archives the task, and applies
the owner-delegated Portfolio vacancy workflow in CLERK_OPERATIONS.md. This adds no ordinary DM
approval or Root ACK; other global changes still require owner scope.

DM resolves direction-local engineering, missing facts, Transport recovery and routine cost/closeout
under its existing authority. Send a needed fact directly to its registered owner; use Clerk to
find that owner or coordinate shared browser/process/resource access and actual overlapping writes.
Sharing infrastructure, a timeout or a failed first repair does not make an issue Root-owned.
Clerk keeps a concrete technical owner and next action until the consequence is handled; it does
not forward ordinary coordination to Root or require an ACK before in-scope work proceeds.

Root receives owner-requested investigations, a concrete shared policy/control-code change for
Root to implement, or an actual user choice outside delegated authority. Such a handoff names the
affected action and required change/choice; labels such as 'workflow exception' or 'shared resource'
are insufficient. Existing-policy operational repair stays with the DM and Clerk. A real owner
decision can go directly to Root without Clerk permission. Material research outcomes reach Root
through Clerk as information, without waiting for a response; do not copy routine repair/status
traffic to Root. Runtime rejection remains a real restriction, never permission to bypass it;
the DM retains diagnosis and allowed alternatives, escalating only a concrete required user action.

Clerk uses compact wait_threads/cursors for missing facts and read_thread only where needed. It
never waits for independent DM messages through collaboration.wait_agent. When enabled, the 50-minute heartbeat
silently recovers missed/interrupted events, including unfinished owner-delegated vacancy actions. Owner pause takes priority.

## Native DM specialists and scientific review

OWNER_DIRECT 2026-09-13: reuse a native subagent within one bounded work batch; create a new
subagent for an independent batch. The assigning parent determines the batch from its objective
and deliverable, without Root/Clerk approval. A tool call, commit, empty-set final or elapsed wait
is not itself a batch boundary. Direction membership alone does not make unrelated work one batch.

Transport's batch is one exact request through preparation, Send, recovery, observation and archive.
Monitor's batch is one experiment batch and its accepted handles through terminal delivery.
Reviewer reuses context for the same change and its corrective reviews; a new independent change
gets a new reviewer child. Scout, Verifier and Operator follow the same objective/closeout rule.
After a batch is complete, retain its evidence and stop assigning unrelated work to its child.

Use spawn_agent for a new batch, default fork_turns=none, with role, objective, owned paths/current
revision, needed evidence, completion condition and actual return parent. Inherit parent history
only when concrete relevant context warrants it; do not copy a long old conversation into a new
child. Use followup_task for same-batch continuation. Record batch/child identity in the existing
assignment record; no new registry, service, placeholder agent or approval checklist is required.
Reuse role configuration and designated checkout, not unrelated conversational history.

Let current accepted handles/requests reach safe closeout in their existing children. If replacement
is actually necessary, preserve same-handle/request state and transfer observation/execution without
overlap or another Send. A new Transport child does not require a new provider conversation.
Long waits do not trigger rotation; do not send cache keepalives or infer cache expiry from a timer.
Independent DM, Clerk and Root tasks remain continuous; this rule governs their native specialists.
Owner pause takes precedence: changing this policy does not resume science or create a new batch.

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

Control publication includes the registered session checkout and direction authoring checkout,
not only main. Root publishes the exact control revision/paths; each task's existing writer brings
those current control paths into its own checkouts at a clean boundary, preserving unrelated work
and frozen scientific inputs. Clerk records actual synchronization or the concrete conflict, not
message delivery as completion. In an already-running turn, the explicit current policy message
supersedes stale injected instructions; changing a role TOML does not by itself update an independent
task's instructions. Do not reread all history or restart research merely to synchronize controls.
