# Persistence B01 observation recovery

This is technical observation recovery for the original current-only invocation,
source 42e337f36bd36c5dd24a7862eb71144f44fdef57, supervisor PID3695656 and handle
folr-persistence-b01-781701-current-only. It consumes no scientific invocation,
changes no budget, and has no scientific polarity.

The first native Luna/low Monitor, monitor_l_low_folr, returned an adoption
observation at23:27:29Z but finalized while the handle was running. Reusing it did
not repair its premature final. The first replacement,
monitor_l_low_folr_recovery, likewise finalized while running and left a remote
unconditional status/sleep loop. Thus neither final proved ongoing observation.
The recovery state file also contained a future observation timestamp inconsistent
with the actual remote clock; that timestamp is not accepted as evidence.

A default-role Luna/low capability fallback, monitor_l_low_folr_terminal under
the same DM, explicitly reported that collaboration.send_message was not exposed
to its runtime. An Astra Reviewer in this same task tree had used native messages;
the difference is observed, but its underlying runtime cause is unverified. The
DM does not infer a shared runtime defect or fabricate a delivered adoption.

The same honest child was resumed with one complete terminal-only observation:
read only the exact supervisor status, sleep180s while exit_code is null, and
retain/await the actual tool session until terminal or a concrete two-hour/tool
blocker. Its native final then returns the terminal facts directly to this DM.
SIBLING_COMMUNICATION.md:98–99 explicitly permits actionable native final when
send_message is absent; Root confirmed this existing route. No intermediate
adoption is asserted under this fallback; DM retains observation responsibility
until the actual terminal receipt arrives. The child is instructed to record the
real time, command/session and delivery method, and never final a running status.

At2026-09-14T23:58:16.906457Z, after verifying exact argv, the DM stopped only the
obsolete unconditional observer PID3697968 and its sleep child PID3698038. No
scientific process was stopped. OLD_OBSERVER_STOP.json preserves that receipt.
The original accepted experiment handle/source remained unchanged.

The fallback child subsequently returned a native final containing finished/exit0
for Z; CURRENT_ONLY_MONITOR_TERMINAL.json preserves its state. DM collection at
00:16:26Z independently confirmed that terminal, exact source and complete output.
The Monitor's reported00:15:18Z observation is earlier than the supervisor's
raw exit log00:15:40Z, so its observation timestamp is not accepted as terminal
timing. The complete invocation time is2930.62s; the raw supervisor log and DM
collection are retained. Native final delivery worked; exact Monitor timing did
not establish itself. The child was told to return a command-generated UTC clock
beside the status, rather than an inferred or manually carried timestamp.

After Z collection the same child was resumed for the original A handle,
folr-persistence-b01-781701-persistent, PID3698859. Its accepted source is unchanged;
its new adjacent memory admission passed at00:17:51Z. A uses the same terminal-only
direct-parent final path, with no assertion of intermediate native adoption.

A terminal-only observation completed. The child returned native final with exact
finished/exit0/PID3698859 and command-generated UTC01:06:53.5531751Z after the
180-second loop. DM collection independently confirms finished/exit0 and the raw
exit log01:05:00Z. PERSISTENT_MONITOR_TERMINAL.json preserves the actual state;
its active set is empty. This time the returned observation time is consistent
with the original supervisor terminal. The fallback's terminal return worked;
earlier failures/timestamps remain preserved and are not retrospectively corrected.
