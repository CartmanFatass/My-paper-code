# B02 observation receipt — reconciled by assigning DM

Batch MGTAP-EARLY-EXPOSURE-B02/master8242; sole accepted handle
mgtap-early-8242-20260913; child /root/mgtap_8242_monitor; parent /root in the
independent MGTAP task01a09cd8-676e-7513-806d-a86b7e104518.
The child was created fresh fork_turns=none, not reusing B01's monitor.

Child observed running PID3433252/tmux_active=true and emitted adoption event
mgtap-early-8242-20260913-adopt-20260914T0048Z. It misrouted app messages first
to overall Root and then RCLE; both forwarded the same factual event without
polling/adopting this process. No intended receipt file actually existed.
Parent preserved these wrong-route receipts, supplied explicit native-only
corrections and received the forwarded adoption. No duplicate observer or
scientific invocation was created. A later forwarded running observation's
claimed01:00:50Z timestamp was inconsistent with its162s uptime/current parent
clock and is not an accepted terminal timestamp.

Because repeated cross-task app messages continued, parent interrupted only the
monitor's agent turn, not the experiment, and made one fresh repair reconciliation
at2026-09-14T00:52:03.1530486Z. Exact supervisor: finished, exit0, pid3433252,
tmux_active=false; task log contains COMPLETE and outer wall190.58s,
peakRSS562396KiB, exit0, terminal2026-09-14T08:51:18+08:00 (=00:51:18Z).
Six current native output files exist. This coherent terminal receipt supersedes
stale running observations; it is not based on process absence alone.

Same child resumed for closeout only and returned direct native final:
active_set empty; own last observed state running; parent's fresh terminal
facts explicitly attributed; absent receipt file and misrouted messages admitted.
DM now writes this actual record and owns collection/acceptance. No additional
app reply, polling, launch/retry or Root ACK is needed. The defect concerned
observation routing, not scientific execution or output integrity.
