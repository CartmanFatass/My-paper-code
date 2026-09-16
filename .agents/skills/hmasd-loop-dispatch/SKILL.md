---
name: hmasd-loop-dispatch
description: Use when HMASD Root plans or advances the research working set, handles native direction returns, replaces an available direction slot, or is about to wait.
---

# HMASD research loop

Root maintains three occupied direction DM chains and records their actual work separately.
DM owns science, code, Pro intake, Monitor adoption, collection and authorized continuation.
Root integrates accepted work and resolves shared dependencies. ROOT_OPERATIONS.md owns routing;
AGENTS §5 and the 2026-09-13 DM autonomy consolidation own the continuous-execution boundary.

## Completion as a stable dispatch point

A DM bounded-assignment completion, material blocker/scope conflict, or ACTIVE-idle event is an
actionable native return. Root immediately runs the stable next-action trigger at that boundary:
integrate the named evidence/commit, recount occupied/reserved slots and actual work, and resume
the same DM only if authorized work is unfinished and not already continuing. When the DM has
no authorized next action or defensible unresolved question, preserve its one ACTIVE-idle event,
missing fact and revisit condition. It remains occupied and available in native event wait; a
possible future fact is not a pending external dependency. An object,
allocation, cleanup, Pro wait or child completion never releases a direction slot. Only an explicit
Portfolio or owner lifecycle pause/closure releases it and can trigger vacancy replacement.

## Stable next-action trigger

At goal-turn entry, every bounded-assignment completion or actionable native return, and before
the first wait after useful work:

1. Apply owner pause/stop boundaries. Workflow edits and status questions do not resume research.
2. Process only changed direction events. Write a brief existing-log entry with direction, event,
   evidence/commit and any Root action. DM handles routine Monitor/Transport receipts directly;
   Root does not poll their handles, recheck adoption or repeat scientific intake.
3. Integrate ready accepted work and resolve concrete dependencies when needed. The original DM
   directly carries an accepted allocation through implementation, checks/review, publication,
   fresh admission, launch/Monitor, collection, technical acceptance, scientific intake,
   preservation, assigned cleanup and its authorized dependent steps. Integration and Root ACK
   are not gates, and each step does not require another dispatch or Portfolio vote.
4. (OWNER_DIRECT 2026-09-15 21:37 PDT, `AGENTS.md` section 5 "Portfolio control".) A pause or
   closure leaves the approved set (`docs/research/portfolio/APPROVED_SET.md`) smaller. Root never
   authors a replacement or refill question and never counts slots; it advances the approved set in
   priority order within the concurrency ceiling, pulling in the next parked backup only when the
   approved set names one and capacity opens. Portfolio review is owner-triggered only.
5. Queue closing memos and lifecycle recommendations in `APPROVED_SET.md` for the next
   owner-triggered review; do not send them.
   An experiment/object/allocation ending, temporary blocker, Pro wait or idle child is not a
   direction vacancy. Resume the same DM's unfinished authorized work when necessary; a completed
   no-addition assessment with no changed input is not another unfinished assignment.
   Existing overlap above three drains without interrupting live directions; no fourth admission.
6. After useful independent work, wait natively for DM events or Root's own replacement Transport.
   Under the current v2 contract, use the configured 1500000 ms interruptible no-event timeout;
   messages, completion notices or new user input may return it early. An unchanged timeout briefly
   continues waiting without a new dispatch pass, full-record reread, `list_agents`, repeated status
   query, keepalive, progress message or Portfolio request.
   Reconcile a child with unfinished authorized work once. A documented ACTIVE-idle boundary
   with no pending producer needs no repeated assessment or invented request. Owner pause/stop
   takes precedence; a bounded final does not dispose of the direction. Never impose a sibling
   or batch barrier.

DM event visibility: unchanged waits remain quiet, but a bounded assignment completion, material
blocker/scope conflict, or ACTIVE direction entering idle must produce one proactive parent action
message before native final/idle return. Include assignment, state, evidence or commit, and the
next action/dependency and its owner (or none), plus the decision's authority and limit. Reuse
existing card/intake/audit and required owner items, without a new schema. Root deduplicates
message/final copies by assignment and evidence revision. A later substantive change gets one
new event; unchanged waits get none.

## Choose from the actual boundary

| Observed condition | Next action |
| --- | --- |
| Accepted card/Pro/grant fixes object, inputs, comparator, permitted invocations and cap | DM completes the whole object and already authorized dependent steps directly, with fresh admission and existing checks. A prepared card, failed attempt or unused time supplies no new grant/retry. |
| A concrete unresolved scientific/development choice exists | DM states the changed action and new fact or proposal relative to the complete prior decision in its existing card/intake, prepares/publishes/binds and sends to the proper node through its own Transport. No Root scope-making or approval is required. |
| New direction-tier scientific meaning, or a frozen-meaning conflict | Use the original Convergence/Innovator or deciding authority under AGENTS §2; preserve frozen meaning while dependent work waits. |
| New investment/grant or cap outside delegation, priority/capacity, lifecycle, fusion/separation, registration or vacancy choice | Portfolio decides. Direction-related authoring/intake stays with DM; Root authors vacancy replacement only after a formal slot release. Within-cap delegated object choices remain local. |
| Verified complete bound Pro response, but short receipt or effect metadata unresolved | DM intakes the full response now and applies conforming work. Transport preserves/reconciles the same request; uncertain effects forbid another Send, not intake. |
| Real pending request, accepted handle or supplied-input producer | Name the producer and awaited event; do independent work, then native wait for its direct return. |
| No authorized work or defensible unresolved question; inputs/options/consequence unchanged | Reuse the completed decision and one recorded missing fact/revisit condition. Keep ACTIVE-idle with no pending external dependency. No new audit, request, assignment, or Root approval wait is created. |

The concrete consequence can be a research/development choice; a deployment customer, positive
B result or full diagnostic is not a universal prerequisite. New facts or a concrete new proposal
let the original DM prepare the next bounded question directly. Three occupied slots do not imply
three advancing experiments/consultations. For example, two unchanged ACTIVE-idle directions and
one Monitor-adopted run mean three occupied slots, one current experiment, and no two replacement
or repeat-approval requests. Root coordinates actual shared writer/runtime conflicts and integrates
the resulting decisions; it does not supply a local substitute scientific or budget verdict.

## Bounded assignments

Use ENGINEERING_SCOPE_SPEC §7.1 for L0 and optional L1–L3 detail. Include the existing
branch/checkout and known collection, integration, intake, cleanup and selected follow-on work.
DM carries science, implementation, self-checks, repairs and acceptance through completion in
the same task. Under OWNER_DIRECT 2026-09-12, do not dispatch CM or Implementer
subagents, including generic implementation substitutes. Retain independent Reviewer review for
high-risk changes under ENGINEERING_SCOPE_SPEC §7.3; DM resolves findings and accepts.
Accepted legacy assignments close on their original routes without
successors; other specialist and independent-task routes are unchanged.

Native work uses `followup_task`; `send_message` only conveys information requiring no
new work. Retain actual dispatch outcomes and reconcile uncertain delivery before retrying.
An unavailable recipient is a Root recovery decision within the same role and scope.
A written next step does not count as active work.

Root maintains PORTFOLIO.md, EXPERIMENT_TRACKING.md and useful evidence in the existing
root-log. Combine routine record edits only when they are already ready together; never delay a
direction to manufacture a multi-direction update. Push every commit immediately.
Coordinate only actual overlapping file/index work. Follow SIBLING_COMMUNICATION.md for
native tool addressing and DM-owned Transport receipts.

Owner delegation, scientific caps, exact-source execution, memory admission and uncertain
Send rules remain binding. A repaired wrapper does not authorize another scientific attempt.
