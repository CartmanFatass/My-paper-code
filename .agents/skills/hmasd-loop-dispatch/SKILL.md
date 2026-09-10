---
name: hmasd-loop-dispatch
description: Use when HMASD Root plans or advances the research working set, handles native returns or Transport receipts, replaces an available direction slot, or is about to wait.
---

# HMASD research loop

Root coordinates execution within accepted decisions. ROOT_OPERATIONS.md owns responsibilities
and routing. Assign a relevant recently active DM to prepare Portfolio Pro materials and check
its response under `hmasd-portfolio-task`; Root does not draft or select Portfolio science.
Directions are independent rolling chains. A batch name is provenance only and never a dispatch,
intake, cleanup or completion barrier between directions.

## Stable next-action trigger

At goal-turn entry, a return or receipt, and before waiting:

1. Apply current owner instructions and pause/stop boundaries first. Control-plane edits
   and status questions do not resume research. During a pause, perform only authorized
   closeout, evidence preservation and the requested non-research work.
2. Make a short pass over each direction's changed event stream and current tracking. Identify ready continuations,
   completed deliveries needing integration and actionable vacancies. Read only the affected
   current Portfolio row and original evidence. Count actual advancing directions under AGENTS §5.
3. Dispatch already-ready independent work before lengthy acceptance, integration or planning.
   Do not dispatch a dependent launch until its own inputs are accepted and published. Short
   routing of another direction's result to its existing DM need not wait for that integration.
4. Accept one bounded delivery or resolve one vacancy from current evidence and authorized
   priorities, then dispatch its ready continuation and return to step 2. For a lengthy operation,
   service other ready work at its next recoverable boundary. Keep scientific intake with DM
   and the complete technical batch with the same DM, optionally using an Operator under ROOT_OPERATIONS.md. Root selects
   replacements within accepted priorities; an unresolved scientific choice goes through the
   designated DM to the proper Pro node. Portfolio responses return to their designated DM
   for scientific/specification checking, then Root applies the conforming decision. Never hold a
   ready direction for peer completion or to assemble a multi-direction result bundle.
5. Check that each accepted experiment has confirmed adoption by the independent Luna/low
   monitor under EXPERIMENT_MONITOR.md. DM/Operator directly adds new accepted handles to its shared active set;
   a dispatched message alone is not adoption. Route each terminal notice to its original
   DM for remaining collection/intake using followup_task, without waiting for other runs.
   Read supervisor state only for handles Root actually owns or is reconciling after lost
   observation. Route terminal evidence promptly. If Transport is idle with a pending request,
   reconcile its persisted state and resume that same observation/recovery route. App dispatch
   acceptance is not provider Send acceptance.
6. Wait only when no authorized action is ready across all directions, for the first event for at
   most 60 seconds while retaining exact dependencies. On wake, process and dispatch the waking
   direction before waiting again; do not defer a ready direction to align it with peers. A batch
   never creates a completion barrier; unresolved waits do not fill available direction slots.

## Bounded assignments

Use ENGINEERING_SCOPE_SPEC §7.1 for L0 and optional L1–L3 detail. Include the existing
branch/checkout and known collection, integration, intake, cleanup and selected follow-on work.
DM carries the engineering and scientific batch through completion; no separate CM or new
planning handoff is required for ordinary implementation steps.

Native work uses `followup_task`; `send_message` only conveys information requiring no
new work. Retain actual dispatch outcomes and reconcile uncertain delivery before retrying.
An unavailable recipient is a Root recovery decision within the same role and scope.
A written next step does not count as active work.

Root maintains PORTFOLIO.md, EXPERIMENT_TRACKING.md and useful evidence in the existing
root-log. Combine routine record edits only when they are already ready together; never delay a
direction to manufacture a multi-direction update. Push every commit immediately.
Coordinate only actual overlapping file/index work. Follow SIBLING_COMMUNICATION.md for
native tool addressing and independent Transport receipts.

Owner delegation, scientific caps, exact-source execution, memory admission and uncertain
Send rules remain binding. A repaired wrapper does not authorize another scientific attempt.
