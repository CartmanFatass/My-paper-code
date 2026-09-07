# Integrated Root and independent Portfolio

Root uses `gpt-5.6-luna` / `xhigh` and executes experiment observation and Pro
Transport. Portfolio is a separate `gpt-6-astra` / `max` task,
running directly on main at the owner's explicit request. DM/CM models and the
scientific decision ladder remain as configured.

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
`followup_task` when idle. Routine evidence, adoption and receipts from a separate app task
use the exact Root ID without model/effort overrides. New Pro handoff dispatch uses the
configured model/effort in the rendered Author handoff. Root never sends an app message to itself for dispatch, adoption
or completion. An intentional owner-directed model migration is separate from receipts.
Portfolio receives its own Pro receipts via the declared parent ID. A DM using a native
child ID as source still declares Root as app parent; Root forwards the local receipt.

Execute Pro transport and recovery locally in Root. Record the actual execution ID,
reconcile existing Send evidence, and preserve accepted request content. New requests
use the current renderer. Return completion to the declared parent, locally when it
is Root and by message otherwise.

## Continuing work across Root and Portfolio boundaries

OWNER_DIRECT 2026-09-06: separating Portfolio does not pause the research loop. A status
question or completed status summary is not a stop instruction. Before returning from a
normal work pass, route newly available results/Pro answers, act on ready authorized next
steps, and check vacancies against the current candidate order. Count actually advancing
direction chains, not merely registered DM names; a chain waiting only on an external
decision yields its slot when another admitted candidate has bounded work. Preparation,
implementation and intake count as work even when no experiment is running.

A completed documentation-only assignment ends that assignment, not the direction's
standing authorization. When the integrated intake/card already selects the next object,
Root gives the existing DM the next bounded implementation handoff without another owner
or Portfolio vote. A scientific stop, changed scope, missing selection or unresolved
external effect remains a real boundary. A no-additional-invocation result permits only
already authorized distinct-question preparation, never an automatic repeat or new run.

Root sends Portfolio a concise evidence delta when a result, card, dependency or available
slot changes the actionable queue; name the source/commit, next responsible agent and
concrete missing decision. Portfolio updates its snapshot/order and sends the usable action
back to Root. A committed file alone is not delivery. Root records the actual native
dispatch or concrete blocker in existing tracking and continues other ready work while
Portfolio responds. Neither side waits for the other's routine snapshot to progress an
already selected object. Reuse pending requests; do not create a second dispatch to check one.

If every recorded candidate is blocked, ask Portfolio for the next bounded ordering or
question-preparation action and record that request's responsible task. If nothing can
advance after the available scan, return the specific dependencies and next wake/message
source. Do not invent a fifth experiment, change lifecycle, or add an automation to fill time.
These are continuation instructions, not new scientific launch conditions or approval steps.

### Root's execution steps (Luna; OWNER_DIRECT 2026-09-06 clarification)

Follow these steps in order on a normal turn or fallback wake. Use the named current
records; do not reconstruct all direction history or decide missing science yourself.

1. **Check owner changes.** Apply an explicit stop or changed scope first. A question,
   status request or completed subtask alone does not revoke standing authorization.
2. **Route new evidence.** A terminal experiment goes to its CM for collection/acceptance,
   then its DM for scientific intake. An archived Pro answer goes to its named DM or
   Portfolio. An integrated intake goes to Portfolio as a concise source/commit delta.
   Reuse the existing recipient; do not resend an already delivered receipt.
3. **Continue a selected object.** If the integrated card/intake selects a next object
   and the previous assignment ended at documentation, send the existing DM a bounded
   instruction to commission CM from that card's handoff section. Record the actual
   dispatch and next owner. Do not merely recommend doing it. If the intake selects no
   further invocation, do not launch one; use only an already authorized preparation
   task, or send the missing scientific question to DM/Portfolio.
4. **Fill available slots.** Read Portfolio's current order. For each candidate, check
   its recorded next action and concrete blocker. Continue ready existing chains first;
   then assign the first runnable conditional candidate until five chains advance or
   the recorded list is exhausted. A DM waiting only for Pro does not occupy an advancing
   slot when another admitted candidate can work. Do not create a duplicate agenda or
   infer a new object from an ACTIVE label.
5. **Escalate only the missing decision.** For an exhausted/ambiguous ordering, send
   Portfolio the available slots, candidate-specific blockers and exact missing choice.
   For uncertain scientific meaning, ask the DM; for a technical defect, ask CM. Send
   once, preserve the pending route, and continue the other ready steps above. Do not
   wait for Portfolio to approve an already selected implementation.
6. **Choose the next wait from actual state.** While an assigned native DM/CM is still
   producing an intake or delivery, use native waiting and process its return before
   ending with a status summary. When only external experiment/Pro waits remain, retain
   the existing shared observation route and return. When every candidate is concretely
   blocked, record each blocker and its next responsible task/message source, then return.
   A status list, an unsent recommendation or a stale snapshot is not a completed handoff.

When reporting progress, name the action actually dispatched, its responsible agent and
the remaining dependency. If fewer than five chains advance, state the concrete reason;
do not claim that five listed directions are five active chains. This procedure adds no
experiment permission, new scheduler, mandatory diagnostic or Portfolio approval step.

## One shared fallback wake

Use a thirty-minute recovery heartbeat. While actively handling a turn, finish available bounded work
and react to actual messages; do not wait for the timer to do ready work. Without another
message, terminal discovery may be delayed until the next fallback pass. A known bound does
not cause one-minute polling or a new per-run automation. No goal is created by this workflow:
use goals only for an explicitly requested finite objective, not to keep sampling while an
external request is generating.

Use automation `hmasd-experiment-monitor`, named HMASD Root pending work, for experiment
and Pro observation. `.codex/hmasd-monitor.toml` declares its endpoint and schedule.

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
4. Apply "Continuing work across Root and Portfolio boundaries": dispatch ready work and
   refill available slots before returning a status summary. Keep the shared wake enabled if any work
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
