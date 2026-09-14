# Native Monitor receipts and DM reconciliation

Parent /root in independent DM task01a09cd8-676e-7513-806d-a86b7e104518;
new native child /root/mgtap_monitor. It read the current Monitor contract and
received the exact accepted handle by followup_task; no old monitor was reparented.
Native final was the available direct return mechanism. No ACK was required.

Initial receipt's reported facts (condensed, not a verbatim message archive),
preserved as superseded observation:

> MONITOR_ADOPTED: MGTAP-EARLY-EXPOSURE-B01/master8241; supervisor /usr/local/bin/agent-task, host LAPTOP-U9TDKC8A, exact SHA0d161633e3bb6884b56ef57a0200060b659c56a8. Admission passed; native process was present, then exited.
>
> MONITOR_TERMINAL mgtap-early-8241-20260913-terminal-20260913T2353Z: process/supervisor no longer present; intermediate output episodes229446bytes, rollouts120608bytes, final_COND282869bytes, admission504bytes; no DENSE checkpoint/outer metrics; status still running.

DM fresh readback at2026-09-13T23:56:31.9038463Z reconciled the same handle:
agent-task status finished, exit_code0, pid3431953, tmux_activefalse. The actual
task.log says exit0 at2026-09-14T07:56:16+08:00, duration188s; GNU time wall188.19s,
peak RSS559316KiB, exit0. Complete summary544528bytes, episodes404614, rollouts210210,
final_COND282869/final_DENSE282893, admission504. These exact bytes and supervisor
records are retained in NATIVE_EVIDENCE.zip, not reconstructed from this receipt.

Corrected native final (condensed fact record):

> The earlier incomplete observation combined an intermediate output listing with later process absence, before reconciling the supervisor's final publication record. It is superseded and does not indicate a failed attempt.
>
> Corrected terminal receipt: complete output, exit0, outer wall188.19s, peak RSS559316KiB, admission passed; both checkpoints and summary present. No launch, retry, cleanup or scientific interpretation was performed.

DM accepts normal completion. The initial message was an observation error and
did not consume a second scientific attempt or justify a retry. The child was
instructed to reconcile current final publication/supervisor exit rather than
combine stale file state with later process absence. No shared-control code was
edited and no recurring automation was added.
