# Portfolio plans; Root executes

Portfolio (`gpt-6-astra`, effort selected by the owner) plans the research queue and prepares bounded commands.
Root (`gpt-5.6-luna` / `xhigh`) executes those commands, integrates specified deliveries,
observes accepted experiments and dispatches exact Pro handoffs. Independent Transport
(`gpt-5.6-luna` / `high`) handles all Pro browser operations and parent receipts. The owner directs this
boundary. DM owns scientific decisions within its existing delegation; CM owns technical
judgment and acceptance. Existing Pro authority, scientific budgets and model settings remain.

## Endpoints and files

OWNER_DIRECT 2026-09-08: before messaging Portfolio, apply
`SIBLING_COMMUNICATION.md` **Send/no-send conditions**. Send only a specific requested
reply or a new unresolved command/conflict/repair need; execute supplied return routes
without reporting them. Do not repeat an unchanged pending request. Root owns the main
index by default and does not request idle confirmation or notify release for routine
commits/integrations. Only Portfolio initiates an actual temporary index transfer under
that document's exact steps. Batch ready routine receipts at clean boundaries, push every
commit immediately, and do not delay independent dispatch for logging.

Root is task `01a07249-b095-7821-8ce2-e9c32ba85267` in `C:/Projects/HMASD`.
Portfolio's exact task and checkout are in `.codex/hmasd-portfolio.toml`; it works directly
on main and owns `docs/research/portfolio/PORTFOLIO.md`. Root owns operational facts in
`docs/research/portfolio/EXPERIMENT_TRACKING.md`. Coordinate overlapping edits, commit
explicit paths and push immediately. Current commands belong beside the current Portfolio
working set; their dispatch/handle/receipt facts belong in existing tracking. Historical
records are evidence, not a command queue.

## Independent Transport and native return routing

OWNER_DIRECT 2026-09-07: reuse Transport task `01a07e52-f085-76a0-886a-4127f490421f`,
configured in `.codex/hmasd-transport.toml`, in the shared local checkout. Root owns direction
dispatch, integration, experiment observation and native forwarding. Transport alone owns Pro
browser actions, request state, tab leases, archives and its outbox. It never selects science,
refills the working set or launches experiments. Root does not wait in a provider page.

The ordinary route is native DM/CM → Root → Transport → Root → original native DM/CM.
The author supplies exact request ID, HANDOFF path/full commit, fixed TASK URL and return
target from the existing command. `source_thread_id` is the actual author UUID;
`parent_thread_id` is Root's app-task UUID for native directions, and `operator_thread_id` is
Transport's UUID. Root dispatches the unchanged handoff with `send_message_to_thread` to
Transport. A native author's direct app dispatch requires an already-authorized command and
the same Root parent; Transport must never infer parent from source. Portfolio's own requests
retain Portfolio as parent. All app messages omit model/thinking overrides.

Transport persists acceptance and handles each pending request independently. It sends one
completion or terminal-blocker receipt to the exact parent, using the existing outbox and
message key. Root matches request/command/recipient and forwards the original evidence with
native `send_message` for a running recipient or `followup_task` for an idle one. A source UUID
is not a native tool address. If the recipient is unavailable, Root uses the supplied recovery
route or asks Portfolio for the concrete missing route, preserving the receipt. A received
receipt cannot cause another Pro Send or duplicate intake. Routine receipt handling stays in
the Root log; only new command/repair needs wake Portfolio. Transport never sends a second
receipt to the source or to Portfolio as an informational copy.

While requests remain pending, Transport interleaves due observations and receipts with waits
of at most 60 seconds. Root remains free for other directions. If Transport becomes idle or
fails while a named request remains pending, Root consults its existing persisted state and
sends an observation/recovery-only continuation to the same task; this is not a new Send.
Use compact task snapshots on a meaningful event or pending-task recovery, not continuous
app polling. Neither a task restart nor migration creates a new goal, scheduler or conversation.

For migration, Root first persists and releases its browser/request writer at a recoverable
boundary; Transport verifies the named inventory before adopting it. Preserve accepted TASK,
HANDOFF, source/parent/operator metadata, provider/message identities, archives and receipt
attempts. Record the actual new `execution_thread_id` only for adopted unfinished work, with
the owner handover evidence; do not restage completed LOCAL/SENT receipts. Accepted or uncertain
requests are reconciled from their original binding, not rejected as new packets or resent to
fit the new endpoint. Unsent handoffs receive an explicit routing-only dispatch envelope naming
the new executor/high setting and the unchanged source, parent, TASK and prompt; preserve the
original and validate the envelope against current config. Only execution metadata changes.
Completed history is not imported as a pending queue. Current migration evidence is in
`TRANSPORT_SESSION_MIGRATION_20260907.md`.

## Authoring branches

Use main plus one reusable branch/checkout for each direction with actual authoring work.
Create that branch on demand from accepted inputs; do not provision idle directions or give
each DM, CM, stage or child another branch. Record the chosen checkout in the existing command
handoff. Pro uses the corresponding direction branch too, with a fixed evidence SHA and its
one scoped response path. Serialize overlapping writers and reconcile remote Pro commits before
local pushes. Extra delivery branches need a concrete special isolation reason; only these are
temporary. Existing accepted requests retain their bindings through archival/intake or explicit
obsolete-request resolution. One completed Pro round does not retire a shared branch still in use.
At completion Root integrates accepted commits, preserves other unique commits and dirty files,
reconciles live writers/PRs/delivery dependencies, and retires obsolete local and remote names.
Historical detached worktrees may retain evidence; retiring a branch does not delete their files.

### Reconcile routing when branches are retired

Root's reclamation return includes the retained direction branch/checkout and the affected
request IDs with their actual Send, delivery and archive states. Use current handoffs,
Transport's binding/request records and actual remote refs; a response merged to main does
not by itself close every request that names the branch. Resolve pending or uncertain delivery
before retiring its target. If an accepted target was already removed, preserve recovery refs
and report its exact request/base to Portfolio for a bounded restoration or delivery correction.

Portfolio updates current command locations; Root updates current operational/Transport records
under their existing single-writer coordination. Preserve old branches, bases and receipts in
the matching request history. Historical TASK/HANDOFF/archive files remain immutable evidence,
not sources for a new dispatch. A same-path file in an old checkout is not the latest handoff.
Do not mark cleanup complete while affected live routing remains unresolved; name any retained
dependency in the existing return. No new registry, scheduler or experiment gate is required.

## Portfolio prepares the command

Use [hmasd-loop-dispatch](../../.agents/skills/hmasd-loop-dispatch/SKILL.md), Portfolio
section, on every command, completion/exception return and vacancy. It is the maintained
procedure for whole-working-set planning, five-item handoffs, actual dispatch confirmation
and prewritten collection/intake routes. Use
[hmasd-portfolio-task](../../.agents/skills/hmasd-portfolio-task/SKILL.md) for scientific
Portfolio judgment and the existing decision ladder. Planning targets five advancing
direction chains. OWNER_DIRECT 2026-09-07 counts active native work, running experiments and
accepted Pro generation once per direction; completed tasks and unresolved waits do not count.

## Root's execution loop

OWNER_DIRECT 2026-09-07 rolling parallelism: each direction advances when its own dependency
arrives. A command batch is packaging and creates no completion barrier. Before each blocking
wait, service available returns, integrate the needed bounded delivery and dispatch its named
follow-on; request an exhausted slot's replacement immediately. Portfolio supplies incremental
commands without waiting for all directions. Keep unrelated native work, experiments and
accepted Pro generation advancing. Wait for the first event for at most 60 seconds, then
service new events before another observation pass. Long integration/comparison work
yields at recoverable boundaries; Transport's browser work never locks Root's event loop.
The final CM comparison may require all arms; other direction routes do not depend on it.

During the three CM comparison batches, apply CM_MODEL_COMPARISON_20260907.md at every new CM
assignment, including those forwarded by active DMs and those using an existing CM. Root directly
captures and dispatches eligible work before coding; it does not wait for Portfolio to notice a
new agent. Record batch assignment or a concrete exclusion once in the existing log. A helper
being installed is not proof that this dispatch trigger ran. Report the requested first accepted
five-arm batch once with actual identities; until then the correct state is no batch started.

Use [hmasd-loop-dispatch](../../.agents/skills/hmasd-loop-dispatch/SKILL.md), Root section,
when receiving commands, native returns, failed dispatches or vacancies, including after
an observation pass within the active goal. Read it directly from the repository if the current session's skill
catalog predates its addition. It supplies the dispatch-before-wait sequence, per-event dispatch
receipts and exact conditions for reporting gaps. Root executes named choices; Portfolio
owns readiness and replacement planning. DM and CM retain their scientific/technical work.

Tool addressing and native/app message differences live in
[SIBLING_COMMUNICATION.md](SIBLING_COMMUNICATION.md). Routine app messages preserve the
recipient's model/effort; all cross-session messages omit model/thinking overrides. New Pro
handoffs use Author-rendered provider settings inside the request packet, not as app-message
overrides, and Transport's identity/acceptance procedure. Root records its own receipts locally rather than app-messaging
itself. A native DM with Root as app parent receives its result through native collaboration.

### Report events

For the next three new CM engineering tasks, apply
`CM_MODEL_COMPARISON_20260907.md` before implementation starts: identical code spec and source,
isolated model/client arms, Codex token/time collection. Existing tasks are not replayed.

Use the single **Send/no-send conditions** section in SIBLING_COMMUNICATION.md.
A new task gap includes its evidence and actual working-set delta; routine events and
unchanged pending requests stay in the log. The routing responsibilities below do not
create additional notification exceptions.

Missing scope, next-task choices, authorization/skill applicability, transport/tool permissions
and scheduling gaps route from Root to Portfolio first, with the affected action, evidence and
existing authority. Root does not ask DM to invent the missing command or approve the workflow.
Portfolio handles the planning question and may assign a bounded scientific/technical inquiry;
DM retains object-tier decisions inside its assigned task and CM ordinary in-scope repair.
Root also sends a prompt repair request for an unresolved execution, input, access/tool or
uncertain-state problem outside its assigned repair path. Portfolio arranges the bounded fix
and returns the next step; routine-message filtering must never suppress this help channel.
This is not a new approval gate for accepted work, nor authority for Portfolio to bypass a real
runtime restriction or grant permission reserved to the owner. Unrelated authorized work continues.

## Goal-driven observation

OWNER_DIRECT 2026-09-07: the owner uses a goal to drive automatic execution and deleted the
previous observation automation. Root observes assigned experiment handles within that active
goal and receives Pro facts from independent Transport. `.codex/hmasd-monitor.toml` names
Root's experiment endpoint, not a schedule. Do not create an observation automation. Use
`EXPERIMENT_MONITOR.md` for experiment adoption; Transport uses its skill for request identity,
model verification, Send state, archiving and receipt delivery. Root does not adopt a Pro browser
as a way to monitor Transport. Observation does not select tasks or refill the research queue.

Keep pending experiments and Transport request references recoverable in their existing records.
Root observes experiments; Transport observes Pro requests and supplies receipts. An unresolved blocker goes promptly to Portfolio under the help
rule; unchanged waits need no repeated message. Empty observation state does not mean the
research goal is complete. Owner pause/end preserves accepted processes and pending request
evidence with an explicit observation handover, without a replacement scheduler.

Each Root observation pass reads current assigned experiment rows, batches independent
supervisor checks, services received Transport/native events, and applies the dispatch skill.
Transport performs its own due Pro reads. Root executes remaining explicit commands and return
routes; unlisted actions go to Portfolio. Historical handles/requests are not adopted by scanning
archives. Reuse the owner's goal; no new scheduler, polling task or replacement goal is created.

Owner pause changes the affected work first while preserving accepted-process observation and
unknown-Send evidence. Waiting for one conversation does not hold other issued commands.
Record only meaningful state changes with the exact handle/request, responsible recipient,
evidence and receipt state in existing tracking. Recover from those current facts, not by
reconstructing every direction's history.
