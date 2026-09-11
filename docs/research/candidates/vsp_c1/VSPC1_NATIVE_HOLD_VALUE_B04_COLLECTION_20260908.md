# VSPC1 B04 failed invocation collection and safe stop

P66's sole accepted supervisor handle `vspc1_hold_value_b04_8202_a33a3820fe9d`
terminated with exit127 before the launch script opened. This is a transport-path
failure with zero scientific exposure, not a native performance result. Per Root's
explicit safe-stop handoff, this consumes the P66 invocation; no correction,
restaging, retry or relaunch follows. DM owns all-outcome intake and safe closure.

[Direct terminal evidence](VSPC1_NATIVE_HOLD_VALUE_B04_COLLECTION_EVIDENCE_20260908.json)
retains exact status, full task log, actual supervisor wrapper, raw exit/status and
absence checks. Original remote files remain untouched under
`/home/wu/.agent-tasks/vspc1_hold_value_b04_8202_a33a3820fe9d/`.
A local copy of the evidence is retained at
`temp/directions/vsp_c1/collection/native_hold_value_b04_8202_a33a3820fe9d/failed_collection_evidence.json`.

## Observed boundary

Direct status: failed, exit127, PID3014192, tmux inactive. The log records start and
exit at `2026-09-09T07:55:19+08:00`, displayed duration0s. Actual wrapper payload:

```text
/bin/bash /home/wu-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh
```

The shell reports that exact path does not exist. The accepted handoff instead
bound `/home/wu/hmasd-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh` at accepted
source `a33a3820fe9d4a46a3231bcf267afc956554b6c5`. Its earlier engineering/source
staging evidence remains valid and unchanged; the submitted path differed.

Neither the actual-node admission receipt
`/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_8202_a33a3820fe9d_admission.json`
nor its corresponding output directory exists. The wrapper could not open the
script, so its admission/runner chain was never reached. Therefore there was no
remote preflight, scientific root, model/learner state, native step or evaluation.
No summary, checkpoint, endpoint, moment state or exposure measurement exists to
collect. Primary and native wall/peak-memory measurements are unavailable, not
zero-valued scientific results. Supervisor duration0s describes the failed wrapper.

Collection used only terminal/read-only shell and filesystem evidence; no model,
test, smoke, profiling, admission or payload was run. All B03 identities/evidence and
B04 accepted source/script/staging remain preserved. No scientific interpretation
or comparator/seed/budget change is made here. The same DM receives this failed
outcome for intake, then the owner-requested clean pushed stop.
