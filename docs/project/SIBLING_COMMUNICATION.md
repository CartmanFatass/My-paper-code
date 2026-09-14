# Task collaboration

Control: C:/Projects/HMASD, Windows PowerShell. Resolve current Root/Clerk/DM endpoints and main
writer from .codex/hmasd-dm-sessions.toml; old native names and queued clientThreadIds are not routes.
Independent DMs use gpt-6-astra/max, Clerk uses gpt-5.6-luna/high. Explicit task model settings do
not inherit automatically from a custom subagent role file.

## Independent tasks

Root is the user entry. DM owns its entire direction lifecycle; Clerk coordinates and records.
Direction Pro Convergence is the independent scientific Reviewer; Portfolio supplies user reports and delegated vacancy selection.
DM owns direct Portfolio scientific exchanges, including reopening questions, full-answer intake
and reasoned responses; Clerk coordinates shared conversation access and records under
CLERK_OPERATIONS.md's Direct DM–Portfolio alignment contract. Use one executor per request,
existing Portfolio binding and DM-owned browser/Transport; do not route science through Clerk
summaries. An archived DM can be resumed for focused discussion without reopening scientific work.
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
decision can go directly to Root without Clerk permission. OWNER_DIRECT 2026-09-14: Clerk must
not forward routine or material research events to Root merely as information. Record outcomes
and handle them with DMs. Only explicit user-requested reports or concrete user choices outside
delegation warrant Root messages under CLERK_OPERATIONS.md; no routine ACK/status/completion traffic. Runtime rejection remains a real restriction, never permission to bypass it;
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

DM owns engineering and acceptance, with optional direct Sol/medium implementation children and
independent Sol/high code Reviewer coverage. No CM chain. Its native Luna/low Monitor observes accepted experiment handles and returns
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

## Native child completion and prompt return

OWNER_DIRECT 2026-09-14: each native child sends its actual assigning parent one actionable
completion report before final. Report batch/event identity, completed work, artifacts/diff,
check results, remaining issues and next owner/action. Report a real blocker or required parent
decision promptly. Dispatch supplies both the native parent identity and, for an independent DM,
its actual parent_thread_id/host. Never infer the central Root thread as every child's recipient.

For an independent main task, use send_message_to_thread to that supplied parent_thread_id as the
primary report route. The App tool starts/queues a follow-up turn; it handles the case where DM
has ended its turn as well as active work. For a native-only parent without an app route, use
collaboration.send_message: it queues a native message and can wake wait_agent, but does not itself
start an idle native turn. Native final remains bounded completion evidence. If the primary route
fails, keep the failure and full report, use another available direct parent route once with the
same event ID, and end without a delivery/ACK loop. A final alone is not promised to restart an
independent App task. Do not create intermediary relay tasks or a new timer service.

Owner observation: a main task whose turn has ended and is idle is not restarted by native
child completion/message. Do not treat an active wait and an idle task as the same state.
The app report and automatic native final describe one batch event. DM deduplicates by event and
evidence revision, but completes any unfinished acceptance/continuation. Delivery success means
accepted for delivery, not that the next action ran; record the parent's first actual consequence.
Do not send both native and App status repeatedly or broadcast child receipts to Clerk/Root.

In .codex/config.toml, min_wait_timeout_ms=1500000 and default_wait_timeout_ms=1500000
(25 minutes), while max_wait_timeout_ms=3600000 (60 minutes). These bound/default the requested
timeout; 25 minutes is not the global maximum or a required silence period. Native messages and
completion notifications can wake the parent earlier; App messages also supply new input to
the independent parent. Keep these settings unchanged. On either return, DM handles the ready consequence:
inspect/accept evidence, resolve findings or dispatch the next concrete step before waiting again.
If the message arrives before the child releases its files, wait for final/edit-owner release
before overlapping writes. Already finished children with an unhandled report are not reasons
for another empty wait. Wait only for actual remaining producers after independent useful work.
No extra timers, polling service, periodic keepalive or ACK chain is introduced.

## Optional code delegation and pre-restart operation

OWNER_DIRECT 2026-09-14: DM may choose direct implementation or a complete bounded Implementer
batch. Default Implementer is gpt-5.6-sol/medium; code Reviewer is gpt-5.6-sol/high. DM may select
Astra for a concrete difficult review without asking Root. Direction Pro scientific review is
unchanged. Do not create idle placeholder children or restart accepted work to change models.

Before updated named roles are loaded, use the live generic native spawn interface explicitly:

```text
Implementer: agent_type="default", model="gpt-5.6-sol",
             reasoning_effort="medium", fork_turns="none"
Reviewer:    agent_type="default", model="gpt-5.6-sol",
             reasoning_effort="high", fork_turns="none"
```

Supply a batch-specific task_name and concise message. Include the actual native parent and
independent parent_thread_id/host return route,
role, five L0 assignment facts, the explicit completion-message rule above, and the current
corresponding role-file path. Tell the child to
read the role duties and relevant current instructions, not the whole direction history. State
that other writers exist, it owns only assigned paths, preserves their edits and creates no
children. Implementer may edit/run agreed focused non-scientific checks; return diff and evidence,
not scientific acceptance or an experiment launch. Scientific ambiguity returns to DM while
independent implementation continues. Reviewer receives the contract, source/diff and relevant
evidence without the Implementer's conversation and is instructed not to edit repository files.
A generic child does not gain a read-only sandbox merely by reading a role file; describe its
read-only assignment honestly. Use the configured read-only role once actually loaded, but live parent permission overrides
can still take precedence; retain explicit no-edit instructions.

The explicit model/effort arguments above are supported by the current runtime; check the live
spawn schema in another runtime. Full-history forks do not support these overrides. Do not claim
that editing TOML hot-reloads an already-running named role, and do not select a stale role with
fixed settings expecting a model argument to replace them. Once loaded, use the configured
Implementer/Reviewer roles with their documented defaults. Record the actual chosen role/model
from the dispatch, not just the intended configuration.

Only delegate a concrete batch when useful independent DM work can proceed alongside it. Keep
same-batch fixes with the same child; new independent batches receive new minimal-context children.
DM reviews returned artifacts and focused checks without redoing all implementation, resolves
review findings, then accepts/commits and continues the lifecycle. Neither child completion nor
review creates a new Root/Clerk/Portfolio approval step. Ordinary tiny edits can stay with DM;
review coverage follows scope-spec §7.3 rather than a mandatory Implementer-plus-Reviewer ceremony.

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

Mechanism evidence: [official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
describes model precedence, isolated context and permission inheritance. The precise wait/message
distinction above comes from the current runtime tool contracts: wait_agent returns on mailbox
activity; native send_message does not trigger a turn; App send_message_to_thread starts/queues
a follow-up. Documentation does not guarantee fault-free delivery or measured wakeup latency.
Long native waiting reduces parent status polling, not Monitor's necessary remote observation.

The [App Server lifecycle documentation](https://learn.chatgpt.com/docs/app-server) distinguishes
turn/start (begin generation), turn/steer (requires an active turn), and thread/inject_items
(append history without starting a turn). These support the distinction; they do not establish
that our native notification tool implements turn/start. Use the existing App messaging tool
for independent task continuation, not a custom raw app-server integration.

Bounded check 2026-09-14, event sol-return-route-probe-20260914-01: a generic Sol/medium child
(fork_turns=none) delivered a native report, an App report and final to the active Root parent.
Both messages were observed. This establishes live spawn/active delivery only, not idle restart
or wait latency. Validate an independent parent's next actual turn/action on the first real
completed batch; delivery receipts alone are insufficient. Do not claim idle wakeup was tested.
