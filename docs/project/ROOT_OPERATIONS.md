# Integrated Root and independent Portfolio

OWNER_DIRECT 2026-09-06: Root uses `gpt-5.6-luna` / `xhigh` and absorbs experiment
Monitor and Pro Transport. Portfolio is a separate `gpt-6-astra` / `max` task,
running directly on main at the owner's explicit request. DM/CM models and the
scientific decision ladder are unchanged. See the migration record in
`docs/research/portfolio/decisions/2026-09-06-root-luna-portfolio-separation.md`.

## Responsibilities and routing

Root remains task `01a07249-b095-7821-8ce2-e9c32ba85267` in `C:/Projects/HMASD`.
It routes events, maintains the five-chain working set, observes accepted experiments,
executes exact Pro transport, checks delivered artifacts and integrates/pushes commits.
Scientific intake belongs to the direction DM or independent Portfolio, not to the
transport operation. Technical acceptance and complex fault investigation belong to CM.
Do not independently repeat the DM's scientific interpretation or the CM's focused checks.

Portfolio's task and checkout are in `.codex/hmasd-portfolio.toml`. It owns scientific
Portfolio text, cross-direction comparisons, candidate ordering, investment proposals,
Portfolio Pro question authoring and complete-response intake. It writes those files on
main and immediately pushes explicit-path commits. Root does not concurrently edit them;
coordinate an overlapping integration with Portfolio. CM/implementer worktree rules remain.
Portfolio does not operate the browser or approve every object. Its local session does not
replace `portfolio:cross_direction` Pro or expand the owner's standing delegation.

| Event | Root action | Next owner |
| --- | --- | --- |
| Accepted experiment handle | Adopt and activate shared wake; record direct observations | CM collects, DM intakes |
| Exact Pro handoff | Execute once under Transport skill, then observe/retain archive | DM or Portfolio intakes full fixed file |
| Pushed delivery commit | Check scope, actual artifacts and relevant acceptance; integrate/push | Return a concrete gap to original executor |
| Free direction slot | Choose first runnable ACTIVE candidate in Portfolio's current order | Existing or assigned DM |
| Scientific meaning or next-object question | Forward current evidence and concrete question | DM |
| Cross-direction priority/investment question | Forward concise evidence delta | Portfolio |
| Complex implementation, runtime or browser-tool defect | Preserve facts and commission bounded engineering | CM; Portfolio judges new cross-direction investment |

Use native collaboration for Root's existing children: `send_message` when running,
`followup_task` when idle. A separate app task sends to the exact Root task ID without
model/effort overrides. Root never sends an app message to itself for dispatch, adoption
or completion. An intentional owner-directed model migration is separate from receipts.
Portfolio receives its own Pro receipts via the declared parent ID. A DM using a native
child ID as source still declares Root as app parent; Root forwards the local receipt.

## One shared fallback wake

Owner cadence correction: use a thirty-minute recovery heartbeat because the integrated
Root has a larger workload. While actively handling a turn, finish available bounded work
and react to actual messages; do not wait for the timer to do ready work. Without another
message, terminal discovery may be delayed until the next fallback pass. A known bound does
not cause one-minute polling or a new per-run automation. No goal is created by this workflow:
use goals only for an explicitly requested finite objective, not to keep sampling while an
external request is generating.

Reuse automation `hmasd-experiment-monitor`, retargeted to Root and named HMASD Root
pending work. Its thirty-minute schedule now covers experiments and Pro observation.
The old id is retained to avoid a duplicate automation; it no longer denotes another
task. `.codex/hmasd-monitor.toml` declares the current endpoint and schedule.

The heartbeat is ACTIVE while any currently assigned experiment needs observation or
terminal notification, or any explicitly current Pro request needs reconciliation,
generation observation, archival or delivery. One completion never pauses the other work.
An explicit terminal blocker with no scheduled recovery does not require repeated wakes.
Pause only when this union is empty. Use `automation_update` on the existing id with the
full preserved prompt, schedule and Root target; read back activation before adoption ACK.
Owner pause overrides further research or Send, but does not silently abandon an already
accepted process or erase an accepted-send observation.

Each wake performs a bounded pass:

1. Read current owner instructions and current rows in `EXPERIMENT_TRACKING.md`; inspect
   each unresolved assigned handle using the configured supervisor, batching independent reads.
2. Read the explicitly current request entries/handoff paths recorded in that same table's
   Pro section and their existing request facts. Historical registry entries are not a queue.
   Inspect due Pro requests serially through CUA, using exact conversation and paired messages.
   A normally generating request is due on the next thirty-minute fallback wake; experiment checks use the same fallback cadence.
3. Persist meaningful status changes, archive complete replies and route material events to
   the responsible DM/CM or Portfolio. Local receipts have zero app-message attempts.
4. Continue ready authorized local work or return. Keep the shared wake enabled if any work
   above remains. Do not busy-poll, sleep through generation, narrate unchanged status, create
   a per-run/per-request automation, or redispatch an already accepted handoff.

A current unsent handoff may receive its first Send during normal Root work once exact
acceptance state is reconciled. A wake is not authority for a duplicate or uncertain Send.
Use `.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md` for the existing exact-input,
6 Pro verification, send identity, archive and tab rules. Browser operations remain serial,
but waiting for one conversation does not hold unrelated research. Preserve request-specific
facts and tab identities even though their heartbeat id is shared.

## Recovery and reading economy

Existing tracking rows, direction card/intake, pushed commits and request-specific archives
are the recovery sources. Record accepted handle/request, current responsible DM/CM or
Portfolio, next action and receipt status there. Do not introduce a new registry, scheduler,
daemon, approval layer or historical-replay duty. Read relevant sections and evidence deltas;
delegate a complete bounded question rather than forwarding every micro-step.

At an empty slot, follow Portfolio's recorded runnable order without another consultation.
Skip a temporarily blocked candidate with its actual reason, keeping ACTIVE/lifecycle intact.
If no recorded candidate can run or new evidence can materially change investment, ask
Portfolio for the next ordering while other admitted work continues. Root does not infer a
priority/lifecycle disposition from a technical failure or scheduling convenience.

Accepted legacy transport requests retain their original immutable handoff and Send facts.
A documented ownership transfer changes only the executor/observation route. Preserve the
old executor ID in original records and record Root's current execution ownership separately;
do not rerender a historical prompt merely to make it pass the new endpoint config.
