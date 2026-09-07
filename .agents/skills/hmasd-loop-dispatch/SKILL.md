---
name: hmasd-loop-dispatch
description: Use when HMASD Portfolio plans or refills direction work, or Root receives a command, native return, dispatch gap or working-set vacancy. Also use when only one direction advances despite available work. Not for scientific intake or provider transport mechanics themselves.
---

# HMASD Portfolio and Root dispatch

Portfolio maintains the whole working set; Root executes ready commands and per-direction return routes.
Use the section for the current role. AGENTS and the current owner instruction retain
authority; this procedure changes no scientific decision tier, model, budget or permission.
Endpoints and observation rules are in `docs/project/ROOT_OPERATIONS.md`.

OWNER_DIRECT 2026-09-07: capture the next three NEW CM engineering assignments under
`docs/project/CM_MODEL_COMPARISON_20260907.md` before implementation begins. Dispatch the same
frozen code spec/task/source to all comparison arms using that temporary protocol. Do not use
historical tasks or count comparison arms as additional research directions.

## Shared state: actual work, not remembered task names

Use current commands in `docs/research/portfolio/PORTFOLIO.md`, actual native dispatch/return
receipts and current `EXPERIMENT_TRACKING.md` facts. The original delivery artifact establishes
what completed; an old native summary does not replace a later experiment or scientific intake.
A committed command, accepted dispatch and running task are different states.
Before shared-main index mutations, use the peer handoff in
`docs/project/SIBLING_COMMUNICATION.md`; other work continues while the short Git operation runs.

Count each direction once across active native implementation/collection/intake/question work,
accepted running experiments and accepted Pro generation (OWNER_DIRECT 2026-09-07).
Unresolved transport waits, completed children and undispatched intentions do not count.
Reuse the latest native inventory until an event changes it. Resolve a missing fact once
from its current source instead of reconstructing all direction history.

## Portfolio: refill each actionable vacancy immediately

1. Read the original return and its affected card/intake sections. Apply owner overrides and
   distinguish technical completion, missing science, failed dispatch and uncertain acceptance.
2. Update the affected chain against the latest working-set facts: retain running work;
   identify completed, undelivered and waiting work; choose the next useful bounded task for
   each actionable vacancy. Plan toward
   five advancing chains. If fewer are justified, name the actual dependencies; do not fill a
   slot with duplicate preparation or invented experiments.
3. Prepare the ready follow-on or replacement without waiting for other returns or a complete
   working-set refresh. Bundle independent commands already ready at the same time; a batch
   is packaging, never a completion barrier. Preserve DM object-tier and Pro decision authority.
   Give a missing scientific choice to its DM/node rather than asking Root to decide it.
4. Update the affected current rows, commit/push, then immediately send the usable command(s)
   to Root. Check the actual dispatch receipt in the Root daily log or direct response when explicitly requested. Routine
   log entries do not wake Portfolio or require an ACK. An unaccepted command still needs routing;
   a snapshot update is not delivery.

Use the existing five-item handoff, in ordinary prose:

- **Target/action:** exact existing recipient and bounded deliverable. If the recipient may be
  unavailable, supply a concrete replacement route with the same role and assignment.
- **Inputs:** current path/section and bound revision or request identity; name the direction's
  existing authoring branch/worktree and owned paths. Reuse it across assignments under AGENTS
  section 6, with one writer for overlapping work; a new task does not create a branch.
  If actual selected work has no direction checkout, establish one on demand from accepted
  inputs; do not precreate branches for inactive directions. A temporary exception names its
  purpose and retirement event in this handoff.
- **Bounds:** allowed work, scientific/execution budget, stop and the specific earlier boundary
  this continuation supersedes. Keep preparation-only limits on their own task.
- **Return route:** name collection, integration, intake and already-selected follow-on actions.
  State real dependencies, such as technical artifact acceptance before the second frozen arm.
  Root also reconciles finished temporary branches under AGENTS section 6 and retires their
  local/remote names after preserving recovery and resolving any live delivery dependency.
  Its reclamation return follows ROOT_OPERATIONS.md's branch-routing reconciliation: retained
  branch/checkout, affected request states and unresolved delivery dependencies. Portfolio
  refreshes current command locations; Root reconciles operational records before reporting
  cleanup complete. Frozen historical handoffs are preserved, not reused as new dispatch input.
- **Report conditions:** apply SIBLING_COMMUNICATION.md's notification filter. Log ordinary
  completion and execution receipts; message Portfolio when the assigned route is exhausted,
  a vacancy needs a command, or a conflict/dependency requires Portfolio action. An unresolved
  execution/tool/input problem outside the assigned repair path is an immediate repair request
  to Portfolio even without a scientific or Portfolio-tier decision; never hide it in the log.

Bundle routine collection → technical acceptance → integration → scientific intake when their
scope is known. A delegated DM/CM decision within that route needs no extra Portfolio vote.
For example, a first arm's conforming summary may admit the already-selected second arm without
selecting on the first score. A new scientific choice or unfrozen invocation remains separate.

## Root: process each return and keep independent directions moving

1. Dispatch every independent command before waiting. Reuse accepted assignments. Use native
   `send_message` for running agents and `followup_task` to resume idle ones; follow the exact
   addressing rules in `docs/project/SIBLING_COMMUNICATION.md`.
2. If an old recipient is absent, try its resumable identity. If unavailable, use the explicitly
   supplied replacement route or report the missing target immediately. Continue other commands.
3. Execute each supplied return route as its dependency arrives; integrate/push specified clean
   deliveries and route actual artifacts to their named CM/DM. Keep technical interpretation
   with CM and science with DM. Do not replace an E0 result with an earlier implementation record.
   Dispatch that direction's ready follow-on before waiting for unrelated returns. A slow Pro
   request, experiment or comparison arm holds only actions depending on its result. During
   lengthy local work, reach a recoverable boundary and service other ready returns; do not
   finish one direction's entire collection-to-Pro lifecycle before servicing another.
   OWNER_DIRECT 2026-09-07: a precise gap in task scope, next-command selection, authorization,
   skill applicability, transport/tool permissions or cross-direction scheduling goes to
   Portfolio first. Include the affected action, original evidence/rule and existing authority.
   Do not dispatch an undefined gap to DM to obtain a replacement task or workflow approval.
   Portfolio resolves planning/applicability or issues a bounded investigation to the appropriate
   DM/CM; it cannot supply owner-only permission or override a real runtime restriction.
4. Record routine receipts in `docs/research/portfolio/root-log/YYYY-MM-DD.md` under
   SIBLING_COMMUNICATION.md's notification filter. Continue executable named routes without a
   Portfolio message. When Portfolio action is needed, send the exact decision/gap, original
   evidence and compact working-set delta; include advancing-chain count for a capacity change.
   Report an actionable vacancy when it occurs, not when the entire batch finishes. Do not send
   separate dispatch, push, launch and intake progress messages or an unchanged periodic digest.
5. Before any blocking wait, service available returns and dispatch ready named actions. Wait
   for the first completion/message, with a bounded wait of at most 60 seconds; never join all
   direction tasks or poll one task until terminal. Batch short independent status reads only.
   On wake, handle new actionable events before another observation/wait. While native work
   is running, interleave its returns with authorized external observations. When
   only external waits or a requested Portfolio reply remain, yield the current pass with those
   exact dependencies while retaining observation within the active goal; do not mark it complete.
   An exhausted route requests its next command immediately; other live directions need not
   finish. An empty queue is not programme
   completion. Unchanged healthy observation needs no repeated report or inventory polling.

| Event | Root's next action |
| --- | --- |
| Complete native return | Follow its prewritten route and log original evidence; message Portfolio only when a new command or planning decision is needed. |
| Failed dispatch, unavailable recipient or yielded direction | Report the precise gap/vacancy now; dispatch unrelated commands. |
| Reversible technical staging problem inside an assigned repair route | Keep the same CM on that authorized repair; report its concrete unresolved gap, not an invented scientific stop. |
| Unknown Send or launch acceptance | Reconcile the same identity from authoritative state; hold only the uncertain external action. |
| Object-tier science choice within an assigned DM task | Keep it with that DM under existing delegation; no additional Portfolio vote. |
| Missing task scope, extra/unlisted invocation, replacement task or workflow/authorization applicability gap | Send the exact gap to Portfolio first; continue independent assigned work. Portfolio supplies the next bounded command or identifies the actual required owner decision. |

A later explicit continuation supersedes an earlier command's stop only within its stated scope.
Successful staging after zero accepted invocations is not a scientific retry. This does not
authorize a retry of an accepted experiment, a different source/device/budget or duplicate Send.
Root follows supplied choices; it does not select a replacement direction or technical alternative.
Routine tool addressing, reads and authorized pre-acceptance mechanical corrections stay local.

Serialize only short shared-index operations and exact browser identity/Send/read actions.
After accepted Pro Send, persist the binding and resume the event loop; its tab lease is not
a global work lock. Start all independent authorized comparison arms before observing them;
the final comparison needs its required arms, but unrelated science routes do not.

Example: A returns with a named DM intake while B is generating in Pro, C is running an
experiment, D is implementing, and E exhausts its route. Root starts A's intake and asks
Portfolio once for E's replacement now, retaining B/C/D. Portfolio sends E's ready command
without waiting for A/B/C/D. A later return starts its own route immediately.

## Example: one hot direction and three silent queues

V is preparing a packet; D has a completed experiment with no DM intake; C has a terminal
technical return; U stopped before launch and has no accepted process. Portfolio sends D intake,
C intake/next-path preparation and, if selected, U's bounded staging continuation together,
while retaining V. If all four are still advancing after dispatch, Root reports **four actual
advancing chains**. An unresolved fifth direction remains a named dependency. Neither session
waits for V's packet before advancing D, C and U, or counts old DM names as active work.
