---
name: hmasd-loop-dispatch
description: Use when HMASD Root plans or advances the research working set, handles native returns or Transport receipts, replaces an available direction slot, or is about to wait.
---

# HMASD research loop

Root owns Portfolio planning and execution. Use `hmasd-portfolio-task` for scientific
comparison and proper-node decisions; use ROOT_OPERATIONS.md for execution and routing.

## Stable next-action trigger

At goal-turn entry, a return or receipt, and before waiting:

1. Apply current owner instructions and pause/stop boundaries first. Control-plane edits
   and status questions do not resume research. During a pause, perform only authorized
   closeout, evidence preservation and the requested non-research work.
2. Make a short pass over changed returns and current tracking. Identify ready continuations,
   completed deliveries needing integration and actionable vacancies. Read only the affected
   current Portfolio row and original evidence. Count actual advancing directions under AGENTS §5.
3. Dispatch already-ready independent work before lengthy acceptance, integration or planning.
   Do not dispatch a dependent launch until its own inputs are accepted and published. Short
   routing of another direction's result to its existing DM/CM need not wait for that integration.
4. Accept one bounded delivery or resolve one vacancy from current evidence and authorized
   priorities, then dispatch its ready continuation and return to step 2. For a lengthy operation,
   service other ready work at its next recoverable boundary. Keep scientific intake with DM
   and the complete technical batch with CM/Operator under ROOT_OPERATIONS.md. Root selects
   replacements directly; an unresolved scientific choice goes to the proper Pro/owner tier.
5. Check that each accepted experiment has a current observer under EXPERIMENT_MONITOR.md.
   Read supervisor state only for handles Root actually owns or is reconciling after lost
   observation. Route terminal evidence promptly. If Transport is idle with a pending request,
   reconcile its persisted state and resume that same observation/recovery route. App dispatch
   acceptance is not provider Send acceptance.
6. When no authorized action is ready, wait for the first event for at most 60 seconds,
   retaining exact dependencies. On wake, process changed facts before waiting again. A batch
   never creates a completion barrier; unresolved waits do not fill available direction slots.

## Bounded assignments

Use five concise items: deliverable and goal; owned paths, existing branch/checkout and
entry points; preserved semantics; acceptance with relevant card/spec sections; budget and
stop condition. Include known collection, integration, intake and selected follow-on work
in the assignment. Let the DM organize ordinary CM steps through completion. A missing
intermediate instruction does not require a new planning handoff.

Native work uses `followup_task`; `send_message` only conveys information requiring no
new work. Retain actual dispatch outcomes and reconcile uncertain delivery before retrying.
An unavailable recipient is a Root recovery decision within the same role and scope.
A written next step does not count as active work.

Root maintains PORTFOLIO.md, EXPERIMENT_TRACKING.md and useful evidence in the existing
root-log. Batch ready routine record edits at clean boundaries; push every commit immediately.
Coordinate only actual overlapping file/index work. Follow SIBLING_COMMUNICATION.md for
native tool addressing and independent Transport receipts.

Owner delegation, scientific caps, exact-source execution, memory admission and uncertain
Send rules remain binding. A repaired wrapper does not authorize another scientific attempt.
