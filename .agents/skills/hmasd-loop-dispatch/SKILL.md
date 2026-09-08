---
name: hmasd-loop-dispatch
description: Use at every HMASD Root goal turn, new command, native return, Transport receipt, failed dispatch and before waiting; also when Portfolio refills a vacancy or parallel directions stop advancing. Determines the next executable action, not science or Pro browser mechanics.
---

# HMASD Portfolio and Root dispatch

Portfolio maintains the whole working set; Root executes ready commands and per-direction return routes.
Use the section for the current role. AGENTS and the current owner instruction retain
authority; this procedure changes no scientific decision tier, model, budget or permission.
Endpoints and observation rules are in `docs/project/ROOT_OPERATIONS.md`.

## Shared state: actual work, not remembered task names

Use current commands in `docs/research/portfolio/PORTFOLIO.md`, actual native dispatch/return
receipts and current `EXPERIMENT_TRACKING.md` facts. The original delivery artifact establishes
what completed; an old native summary does not replace a later experiment or scientific intake.
A committed command, accepted dispatch and running task are different states.
Root owns the shared-main index by default (OWNER_DIRECT 2026-09-08); do not ask for
per-operation idle confirmation or send release notices. Only Portfolio's actual temporary
index request triggers the transfer steps in `docs/project/SIBLING_COMMUNICATION.md`.
Before every Root-to-Portfolio message, apply that document's **Send/no-send conditions**:
specific requested reply or new command/conflict/repair need only; supplied return routes
are log-only, and unchanged pending requests are never resent. Ordinary commits, pushes,
terminal receipts and index coordination labels do not create a notification exception.

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
State the direction deliverable and its authority boundary; let its DM carry ordinary
intermediate work through CM acceptance and authorized continuation. Preparing a selected
card/specification is not an automatic return to Portfolio for another implementation command.
For example, a first arm's conforming summary may admit the already-selected second arm without
selecting on the first score. A new scientific choice or unfrozen invocation remains separate.

## Root: process each return and keep independent directions moving

### Stable next-action trigger

OWNER_DIRECT 2026-09-07: apply this sequence at every goal-turn entry, incoming command,
native return or Transport receipt, and before any blocking wait. Read this section once
when first applicable; reuse it within the turn rather than rereading the repository. This
is an explicit skill procedure, not an automatic event subscription or a new scheduler.

Use the current command, original return and latest execution facts to choose the first
applicable action below. After that bounded action, re-enter the sequence with changed facts.
Do not wait to collect a full batch or reconstruct every direction's history.
Before a lengthy integration, send any already-known exhausted-slot
request and dispatch other independent ready commands; a long local step cannot delay those
short actions.

| Available event/fact | Next action now |
| --- | --- |
| Ready issued command or ready named follow-on | Dispatch it; issue all other independently ready work before a long local step. |
| Native delivery or Transport completion/blocker receipt | Match request/command and original recipient; do the necessary bounded acceptance/integration or forward the original receipt to its named native DM/CM, then dispatch the ready follow-on. |
| Required short index operation is busy | Retain that exact dependency and service another ready event; do not hold the whole return queue. |
| Direction-local step returned and the direction remains assigned | Resume its original DM for acceptance and the next in-scope step, including organizing CM work; record the actual continuation. |
| Direction route exhausted beyond DM authority, or target unrecoverable | Send one exact replacement/conflict need to Portfolio with the actual count delta; continue the other chains. |
| Accepted experiment needs observation | Read its supervisor state and route a terminal result; do not turn process completion into science acceptance. |
| Pending Pro request whose Transport task became idle/failed | Send the same Transport an observation/recovery-only continuation from persisted facts; no browser takeover or another Send. |
| No executable action after the above | Wait for the first event for at most 60 seconds; keep the named dependencies recoverable. |

Transport app acceptance means its task received the handoff; it is not provider Send
acceptance. Count the direction only while native work, an experiment or accepted Pro generation
is actually advancing. An unresolved idle Transport dependency cannot fill a slot. Transport
receipts are actionable Root inputs even when every other direction is still running. Root
never waits for Transport's whole request queue. Routine observations stay in the existing log.

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
   OWNER_DIRECT 2026-09-08: Root retains responsibility through acceptance and authorized
   continuation. Resume the original DM for direction-local decisions, implementation and
   repair; its CM owns technical work. An omitted intermediate instruction is not exhausted
   authority. Portfolio receives working-set replacements, cross-direction choices and actual
   conflicts beyond that DM/CM route, with the exact unresolved action and evidence. Preserve
   scientific caps, actual tool restrictions and uncertain acceptance; routing waives none.
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
   is running, interleave its returns with experiment observations and Transport receipts. When
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
| Selected card/specification or ordinary source/engineering gap in an assigned direction | Resume the original DM to organize its CM and finish the delegated work; Root integrates and continues the authorized route. |
| New direction/replacement, extra invocation outside DM authority, or unresolved cross-direction/scope conflict | Send the exact Portfolio action needed once; continue independent assigned work. |

A later explicit continuation supersedes an earlier command's stop only within its stated scope.
Successful staging after zero accepted invocations is not a scientific retry. This does not
authorize a retry of an accepted experiment, a different source/device/budget or duplicate Send.
Root retains the assigned direction and delegates its scientific/technical choices to its DM/CM.
Routine tool addressing, reads and authorized pre-acceptance mechanical corrections stay local.

Root serializes only short shared-index operations; independent Transport owns exact browser
identity/Send/read actions. After accepted app dispatch to Transport, Root resumes this event
loop. Provider Send acceptance comes from Transport's recorded facts, not the app tool ACK.

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
