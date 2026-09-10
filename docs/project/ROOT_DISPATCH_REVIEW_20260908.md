# Root dispatch review — 2026-09-08

Scope: Root task `01a07249-b095-7821-8ce2-e9c32ba85267`, current P47–P53 execution,
native dispatch/return receipts, and the documents that guide its next action. This is a
review record, not another dispatch procedure. Scientific decisions and invocation budgets
are unchanged.

## Findings and corrections

### 1. Native notifications were mistaken for execution handoffs

Actual native snapshots at 2026-09-08 18:04:56 UTC showed the UCOPE DM completed;
18:10:23 UTC used `send_message` to that DM. The 18:12:53 UTC snapshot showed the DISH
DM completed; 18:16:09 UTC also used `send_message`. At 19:00:51 UTC the UCOPE, DISH
and VSPC1 DM/CM routes were completed. Root acknowledged the missing agent turns in its
19:04:51 UTC answer. `followup_task` calls at 19:05:56–19:06:16 UTC were followed by a
19:06:23 UTC snapshot showing DISH DM, UCOPE CM and VSPC1 CM running.

The old communication document already said that `send_message` does not wake an idle
agent. Root violated that instruction. Its repeated running/idle choice also depended on
a snapshot that could become stale before delivery.

Correction: [SIBLING_COMMUNICATION.md](SIBLING_COMMUNICATION.md#native-agent-messages)
now selects by intent: every work handoff uses `followup_task` to the same recipient;
`send_message` is only a notification requiring no new work. Root operations, experiment
observation and the [dispatch skill](../../.agents/skills/hmasd-loop-dispatch/SKILL.md)
use that same rule. A recorded next step does not count as dispatched or advancing work.
At the next event boundary a turn or actual return establishes progress; no ACK barrier
or repeated live assignment is added. The duplicate dispatch event table was removed.

### 2. The live tracking file contained retired procedures and omitted current handles

Before this correction, `EXPERIMENT_TRACKING.md` opened with the 2026-09-06 merged
Root/Transport route, an active heartbeat and an old no-live-handles snapshot. Its later
records reached P45, while the [Root daily log](../research/portfolio/root-log/2026-09-08.md)
contained P47 FSD, UCOPE 7001 and VSPC1 8101 accepted/terminal handles. Multiple sections
claimed to be current. A resume from this file could recover obsolete work and routing.

Correction: Root owns reconciliation of the actual current handles, outstanding returns,
recipients and accepted continuations in the existing tracking file. The previous record
is preserved under `docs/archive/operations/EXPERIMENT_TRACKING_THROUGH_P45_20260908.md`.
The live file links detailed evidence and the daily log; it updates the same current rows
on meaningful changes instead of accumulating competing current snapshots. Independent
Transport and the owner's goal are the current route. No scheduler or new registry is added.
Root published this reconciliation as `f4f87d3df`; the archive was preserved and the live
file was reduced from 498 lines to a compact current table.

### 3. A launch command disagreed with its staged checkout

The daily log's UCOPE P47 path-mismatch entry records a submitted cwd ending in
`ucope-uav-motion-prefix-b02-20260908`, while the staged checkout ended in
`ucope-uav-motion-prefix-b02-p47-20260908`. The command exited before admission. The
same CM supplied the corrected route, subsequently accepted as the `-cwd02` handle.

Correction: [ROOT_OPERATIONS.md](ROOT_OPERATIONS.md#execute-the-supplied-launch-command)
requires using the supplied committed command and comparing its bound cwd/source with
existing staging facts before submission. Windows-to-Linux wrappers preserve literal
variables and LF bytes and receive a syntax-only check. A discrepancy stays with the same
CM; supervisor acceptance, admission and scientific execution remain distinct facts.
This does not authorize an experiment retry or add a launcher framework.

### 4. A leftover routing sentence still sent ordinary continuation to Portfolio

`EXPERIMENT_MONITOR.md` said “Portfolio handles any unlisted next task,” despite the
current same-direction delegation. The daily log's VSPC1 P49 10:29 source-dependency
return illustrates the cost: known UCOPE source files led to another Portfolio command
instead of the assigned DM organizing its CM and source integration. Earlier owner
corrections fixed the principal routing documents but missed this observation entry point.

Correction: [EXPERIMENT_MONITOR.md](EXPERIMENT_MONITOR.md#bounded-observation) now sends
collection/intake and ordinary continuation to the same DM/CM. Portfolio receives only
replacement or conflicts beyond that assigned route. Frozen scientific requirements and
actual tool restrictions remain controlling.

### 5. App dispatch acceptance was not sufficient evidence of a specific Pro request advancing

The daily log records the FSD P52 app dispatch and a later idle reconciliation: the
singleton had no new corresponding Transport turn/provider Send until the same pending
route was recovered. An app response alone did not establish provider acceptance.

Correction: Root operations reconciles an otherwise unrepresented request at the next
event boundary against existing Transport request state and its current task. Recovery
uses the same idle Transport and request identity; unknown Send is preserved. Native
followup rules do not authorize a second provider Send or browser takeover.

### 6. Workspace reclamation previously stopped at branch names

The workspace audit found historical detached directories still retained after obsolete
branch names were retired. The owner-authorized cleanup removed 190 such worktrees after
verified preservation. The prevention rule was incomplete about physical reclamation.

Correction already published in `67a1896f3`: AGENTS §6, Root operations and the dispatch
skill require verified recovery, removal/unregistration of obsolete worktree directories,
and checks that each removed path is absent on disk and in `git worktree list`. An extra
retained checkout names a live dependency and cleanup owner/event. The shared direction
checkout remains while in use. Test scratch creation/creator cleanup and disabled pytest
cache were published in `f689d5040`.

## Validation and limits

Review uses actual tool kinds, recipient states and original execution records, not Root's
completion assertion alone. The native wake-up correction has an observed successful
continuation above. Documentation checks cover idle/racing/completed recipients,
notification-only messages, duplicate active assignments, mismatched cwd, same-direction
continuation and restricted operations. No scientific invocation is used as a workflow test.
An independent read-only review passed all seven document cases and found no remaining
status-based work-handoff contradiction in the four changed instruction files.
These instructions guide execution; they are not an automatic runtime enforcement hook.
