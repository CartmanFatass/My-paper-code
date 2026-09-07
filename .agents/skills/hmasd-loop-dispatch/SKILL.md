---
name: hmasd-loop-dispatch
description: Use when HMASD Portfolio plans or refills direction work, or Root receives a command, native return, dispatch gap or working-set vacancy. Also use when only one direction advances despite available work. Not for scientific intake or provider transport mechanics themselves.
---

# HMASD Portfolio and Root dispatch

Portfolio plans the whole working set; Root executes supplied batches and return routes.
Use the section for the current role. AGENTS and the current owner instruction retain
authority; this procedure changes no scientific decision tier, model, budget or permission.
Endpoints and observation rules are in `docs/project/ROOT_OPERATIONS.md`.

## Shared state: actual work, not remembered task names

Use current commands in `docs/research/portfolio/PORTFOLIO.md`, actual native dispatch/return
receipts and current `EXPERIMENT_TRACKING.md` facts. The original delivery artifact establishes
what completed; an old native summary does not replace a later experiment or scientific intake.
A committed command, accepted dispatch and running task are different states.
Before shared-main index mutations, use the peer handoff in
`docs/project/SIBLING_COMMUNICATION.md`; other work continues while the short Git operation runs.

Count advancing direction chains, not child agents: implementation, collection, intake and
question preparation count; an external wait, completed child or undispatched intention does
not. Reuse the latest native inventory until an event changes it. Resolve a missing fact once
from its current source instead of reconstructing all direction history.

## Portfolio: one return triggers a whole-working-set pass

1. Read the original return and its affected card/intake sections. Apply owner overrides and
   distinguish technical completion, missing science, failed dispatch and uncertain acceptance.
2. Account for every current chain: retain running work; identify completed, undelivered and
   waiting work; choose the next useful bounded task for each actionable vacancy. Plan toward
   five advancing chains. If fewer are justified, name the actual dependencies; do not fill a
   slot with duplicate preparation or invented experiments.
3. Prepare **one batch of all independent commands**, including follow-ons to the reporting
   direction and ready work elsewhere. Preserve DM object-tier and Pro decision authority.
   Give a missing scientific choice to its DM/node rather than asking Root to decide it.
4. Update the current rows, commit/push, then send the usable batch to Root. Check its actual
   dispatch receipt. An unaccepted command still needs routing; a snapshot update is not delivery.

Use the existing five-item handoff, in ordinary prose:

- **Target/action:** exact existing recipient and bounded deliverable. If the recipient may be
  unavailable, supply a concrete replacement route with the same role and assignment.
- **Inputs:** current path/section and bound revision or request identity; name the direction's
  existing authoring branch/worktree and owned paths. Reuse it across assignments under AGENTS
  section 6, with one writer for overlapping work; a new task does not create a branch.
- **Bounds:** allowed work, scientific/execution budget, stop and the specific earlier boundary
  this continuation supersedes. Keep preparation-only limits on their own task.
- **Return route:** name collection, integration, intake and already-selected follow-on actions.
  State real dependencies, such as technical artifact acceptance before the second frozen arm.
- **Report conditions:** completion, failed/missing dispatch, concrete conflict, uncertain
  external acceptance or unlisted next action; return them to Portfolio.

Bundle routine collection → technical acceptance → integration → scientific intake when their
scope is known. A delegated DM/CM decision within that route needs no extra Portfolio vote.
For example, a first arm's conforming summary may admit the already-selected second arm without
selecting on the first score. A new scientific choice or unfrozen invocation remains separate.

## Root: dispatch the batch, execute its routes, report the working set

1. Dispatch every independent command before waiting. Reuse accepted assignments. Use native
   `send_message` for running agents and `followup_task` to resume idle ones; follow the exact
   addressing rules in `docs/project/SIBLING_COMMUNICATION.md`.
2. If an old recipient is absent, try its resumable identity. If unavailable, use the explicitly
   supplied replacement route or report the missing target immediately. Continue other commands.
3. Execute each supplied return route as its dependency arrives; integrate/push specified clean
   deliveries and route actual artifacts to their named CM/DM. Keep technical interpretation
   with CM and science with DM. Do not replace an E0 result with an earlier implementation record.
4. Send a concise receipt with **the result, the whole working-set state, and the next event**.
   For each direction give command, actual recipient/status and any unsent action or dependency.
   Include the actual advancing-chain count. Changed facts need evidence/commit; unchanged rows
   can be a compact line. Report a vacancy when it occurs, not when the entire batch finishes.
5. While native work is running, wait for its returns and handle authorized observations. When
   only external waits or a requested Portfolio reply remain, return with those exact dependencies
   and the existing observation route. An empty queue requests a new batch; it is not programme
   completion. Unchanged healthy observation needs no repeated report or inventory polling.

| Event | Root's next action |
| --- | --- |
| Complete native return | Follow its prewritten route; report original evidence and updated working set. |
| Failed dispatch, unavailable recipient or yielded direction | Report the precise gap/vacancy now; dispatch unrelated commands. |
| Reversible technical staging problem inside an assigned repair route | Keep the same CM on that authorized repair; report its concrete unresolved gap, not an invented scientific stop. |
| Unknown Send or launch acceptance | Reconcile the same identity from authoritative state; hold only the uncertain external action. |
| New scientific choice, extra invocation or unlisted task | Send the question to Portfolio/the named decision owner; continue independent assigned work. |

A later explicit continuation supersedes an earlier command's stop only within its stated scope.
Successful staging after zero accepted invocations is not a scientific retry. This does not
authorize a retry of an accepted experiment, a different source/device/budget or duplicate Send.
Root follows supplied choices; it does not select a replacement direction or technical alternative.
Routine tool addressing, reads and authorized pre-acceptance mechanical corrections stay local.

## Example: one hot direction and three silent queues

V is preparing a packet; D has a completed experiment with no DM intake; C has a terminal
technical return; U stopped before launch and has no accepted process. Portfolio sends D intake,
C intake/next-path preparation and, if selected, U's bounded staging continuation together,
while retaining V. If all four are still advancing after dispatch, Root reports **four actual
advancing chains**. An unresolved fifth direction remains a named dependency. Neither session
waits for V's packet before advancing D, C and U, or counts old DM names as active work.
