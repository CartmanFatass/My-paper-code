# Task collaboration

Current control: C:/Projects/HMASD, Windows PowerShell. Equal independent DMs use Astra/max;
Transport uses Luna/high. Root is the user entry. Clerk is retired. Read endpoints, coupling
owners and main writer from .codex/hmasd-dm-sessions.toml and follow PEER_DM_COORDINATION.md.

DMs directly message affected peers and services. No standing coordinator, mandatory event
forwarding, ACK or integration permission gate. Each DM owns its records and accepted integration.
Shared-file transactions and vacancy transfer follow PEER_DM_COORDINATION.md; actual runtime
restrictions and frozen science still bind. An archived DM can discuss Portfolio advice without
resuming experiments. Questions/workflow edits alone do not pause research.


Portfolio authority: docs/project/PORTFOLIO_DECISION_PROTOCOL.md now controls direction-level
CONTINUE/RECAST/PARK/CLOSE/reopening. DM owns innovation, experiments, reports and ordinary
in-scope execution, and submits lifecycle recommendations to Portfolio. No unilateral DM PARK,
slot release or archival pending that decision. Existing references to DM lifecycle management
mean proposal, reporting and execution, not final interpretation. Web Portfolio must receive and
read the protocol's fixed repository context; local conversation/skill inheritance is not assumed.

## Independent DM role mapping

A new App task does not automatically inherit .codex/agents/hmasd-direction-manager.toml or a
native parent's developer instructions. Every independent DM must explicitly use hmasd-direction-management/SKILL.md and its
references/role.md complete duties plus current AGENTS, PEER_DM_COORDINATION and its direction intake.
A task title/model or brief ticket is not role equivalence. Supply actual authoring checkout,
full-lifecycle objective, live service routes and current owner overrides in the initial task or
an explicit continuation. Do not replace the existing DM or discard its scientific history merely
to repair instructions. At the first useful boundary record the loaded role revision and actual
next action in its existing intake; no approval handshake or recurring role-reading checklist.

Engineering/support/transport waits retain the owning DM and actual next recovery action; they
are not scientific PARK. A PARK rationale must explain the scientific/development judgment and
alternatives, not merely missing files, review access, estimate overrun or a completed allocation.
DM can select low-cost bounded repair or defer dependent work while pursuing useful independent
work. This is not a demand to manufacture experiments or disregard real scientific futility.

## Independent Transport execution

OWNER_DIRECT 2026-09-14: the registered Luna/high Transport App task uses Codex iab for
Send, concurrent Pro observation and complete archives. Dispatch and returns use
send_message_to_thread, directly between author DM and Transport. Native wait_agent
and native final are not this route. One executor per conversation, independent pending
conversations advance concurrently. Native batch reuse rules below govern other specialists.
Before migration the DM releases its old Transport from browser operation, preserves exact
request/effect/archive state and sends a takeover assignment to the registered task. Do not
rewrite accepted HANDOFF IDs; record actual current execution/return routing separately.
The Transport skill owns browser state, recovery, queue and completion behavior. No Agentify MCP.

## Native DM specialists and scientific review

OWNER_DIRECT 2026-09-13: reuse a native subagent within one bounded work batch; create a new
subagent for an independent batch. The assigning parent determines the batch from its objective
and deliverable, without Root/peer approval. A tool call, commit, empty-set final or elapsed wait
is not itself a batch boundary. Direction membership alone does not make unrelated work one batch.

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
overlap or another Send. An executor change does not require a new provider conversation.
Long waits do not trigger rotation; do not send cache keepalives or infer cache expiry from a timer.
Independent DM and Root tasks remain continuous; this rule governs their native specialists.
Owner pause takes precedence: changing this policy does not resume science or create a new batch.

DM owns engineering and acceptance, with optional direct Sol/medium implementation children and
independent Sol/high code Reviewer coverage. No CM chain. Its native Luna/low Monitor observes accepted experiment handles and returns
adoption/terminal facts directly to DM. DM collects/intakes, then records outcomes and messages only affected peers. EXPERIMENT_MONITOR.md owns the observation procedure.

Direction Pro Convergence reviews science independently through the registered independent Luna/high browser Transport.
It examines design, evidence, interpretation, conclusions and successor plans; DM reads the full
review and responds to material findings with correction/claim limits or reasoned resolution.
The Pro review does not confer funding or lifecycle authority. Preserve scientific independence
and appropriate review coverage; it is not generic optional advice or a per-step approval ritual.

Use collaboration.followup_task for a native child's concrete assignment; collaboration.send_message
for factual parent returns, noting it does not start an idle native turn. Native final completes its
bounded assignment. Real Monitor/Reviewer producers retain their actual parent/wait route;
unchanged waits do not cause repeated status, reminders or duplicate requests.

Each exact Pro conversation has one executor. Keep accepted/uncertain requests, operations and
immutable archives; verified nonacceptance permits repaired same-request Send, not a new scientific
question. Direction DM repairs complex Transport defects; the request-owning DM repairs
a Portfolio Transport defect, preserving its real parent/operator.
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
Do not send both native and App status repeatedly or broadcast child receipts to peers/Root.

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
review creates a new Root/Portfolio approval step. Ordinary tiny edits can stay with DM;
review coverage follows scope-spec §7.3 rather than a mandatory Implementer-plus-Reviewer ceremony.

## Recovery and integration

Peer DMs and Root serialize main transactions under PEER_DM_COORDINATION.md. Each DM integrates its accepted
commits and records DM decisions, returns semantic conflicts to their DM, and never implements shared
policy/code itself. Independent task session worktrees are only hosting; reuse each designated
direction authoring checkout. Accepted legacy children/requests keep their original routes until
reconciled closeout; migration does not reparent or duplicate them. No extra relay service is needed.

Control publication includes the registered session checkout and direction authoring checkout,
not only main. Root publishes the exact control revision/paths; each task's existing writer brings
those current control paths into its own checkouts at a clean boundary, preserving unrelated work
and frozen scientific inputs. Each DM records actual synchronization or the concrete conflict, not
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
