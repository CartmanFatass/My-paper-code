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

## Portfolio prepares the command

Use [hmasd-loop-dispatch](../../.agents/skills/hmasd-loop-dispatch/SKILL.md), Portfolio
section, on every command, completion/exception return and vacancy. It is the maintained
procedure for whole-working-set planning, five-item handoffs, actual dispatch confirmation
and prewritten collection/intake routes. Use
[hmasd-portfolio-task](../../.agents/skills/hmasd-portfolio-task/SKILL.md) for scientific
Portfolio judgment and the existing decision ladder. Planning targets five advancing
direction chains; a completed task or external wait does not count as advancing work.

## Root's execution loop

Use [hmasd-loop-dispatch](../../.agents/skills/hmasd-loop-dispatch/SKILL.md), Root section,
when receiving commands, native returns, failed dispatches or vacancies, including after
an observation wake. Read it directly from the repository if the current session's skill
catalog predates its addition. It supplies the dispatch-before-wait sequence, whole-working-set
receipt and exact conditions for reporting gaps. Root executes named choices; Portfolio
owns readiness and replacement planning. DM and CM retain their scientific/technical work.

Tool addressing and native/app message differences live in
[SIBLING_COMMUNICATION.md](SIBLING_COMMUNICATION.md). Routine app messages preserve the
recipient's model/effort; new Pro handoffs use Author-rendered settings and Transport's
identity/acceptance procedure. Root records its own receipts locally rather than app-messaging
itself. A native DM with Root as app parent receives its result through native collaboration.

### Report events

The shared skill's Root receipt is the maintained report format: result and original evidence,
whole current working set with actual recipient/status and advancing-chain count, then the
next sender/event or gap. Report a yielded/unavailable direction immediately. Known routes
continue without an extra Portfolio exchange. A changed command's scope replaces only the
specified earlier boundary; an unrelated preparation-only task does not suspend the batch.

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
requests serially and applies the shared dispatch skill. It executes remaining explicit commands and
return routes; unlisted actions go to Portfolio. Historical handles and requests are not adopted
by scanning archives. No new scheduler, polling task, per-request heartbeat or goal is created.

Owner pause changes the affected work first while preserving accepted-process observation and
unknown-Send evidence. Waiting for one conversation does not hold other issued commands.
Record only meaningful state changes with the exact handle/request, responsible recipient,
evidence and receipt state in existing tracking. Recover from those current facts, not by
reconstructing every direction's history.
