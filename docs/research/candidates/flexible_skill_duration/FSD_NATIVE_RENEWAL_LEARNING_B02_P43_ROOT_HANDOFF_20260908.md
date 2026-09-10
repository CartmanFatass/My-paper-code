# FSD B02 P43 exact Root launch binding

[P43](../../portfolio/handoffs/2026-09-08-p43-fsd-b02-panel-execution.md) allocates
one G→C→H panel under [B02 card §§2–7](FSD_NATIVE_RENEWAL_LEARNING_B02_SCIENCE_CARD_20260908.md)
and [readiness §8](FSD_NATIVE_RENEWAL_LEARNING_B02_PREPARATION_INTAKE_20260908.md).
Root launches and observes; CM `/root/fsd_cm_baseline_a01` collects; DM
`/root/dm_fsd_p13_reentry` owns scientific intake. This preparation performs no
launch, admission, production model/host/learner, test suite or readiness probe.
It is pure binding/collection, not another CM comparison or source change.

DM released the existing authoring checkout `C:/Projects/HMASD-worktrees/codex-fsd`,
`codex/fsd`, clean/pushed at `e3766876b65e31074510c2b65c3f98dbf6369fb8` after P43
reconciliation/card allocation. Only this record and three five-line scripts are
added; no card, governance, source, tests or previous result is modified.

## Source and verified command bytes

Scientific source is **d961c58268353f215d3ffddf0d83927e6318541d**, the accepted
integration of implementation `eb46e3356582d03d07b58b9480284c867c40c5f2`.
Configured node is `wsl_4070`, SSH `hmasd-wsl-node`, host `LAPTOP-U9TDKC8A`.
The prepared fresh detached cwd is
`/home/wu/hmasd-worktrees/fsd-native-renewal-b02-p43-d961c5826`.
It resolves to the bound SHA and has clean status. The configured network shell
fetched and staged source; no learner or host was constructed.

Scripts are committed at **6c7485b8c86effa553c4d43987d2c35ea5025fb6**:
[G.sh](native_renewal_learning_b02_p43_20260908/G.sh),
[C.sh](native_renewal_learning_b02_p43_20260908/C.sh),
[H.sh](native_renewal_learning_b02_p43_20260908/H.sh).
The committed Git blobs were extracted by Python `subprocess.check_output`
and `Path.write_bytes` into
`temp/directions/flexible_skill_duration/runtime/p43-command-bytes/`, then
SCP-transferred to `/home/wu/hmasd-inputs/fsd-native-renewal-b02-p43-20260908/`.
No command-body PowerShell text round-trip was used.

| Script | Bytes | Committed and staged SHA256 |
| --- | ---: | --- |
| G.sh | 543 | `fbe1554463853b5176664b535f500a4e8cc114a494e14ab023a4be02bd3fd354` |
| C.sh | 543 | `3c474b01da127a9ad839fedbce529e95ccf51ae6c0b01e1247a5df4e039be9a3` |
| H.sh | 755 | `a5e8c233dae975c3175d943348fe5d094c2fa03f62ea49cfff3544ee0b94475a` |

Every script has zero CR bytes. Remote `sha256sum` matches these committed
digests, and `bash -n` parsed all three without execution. The configured Python,
`/usr/bin/time` and `/usr/bin/timeout` are executable. At final verification the
B02 scientific root and all three proposed task directories were absent.

## Literal Root commands and full caps

Execute each line separately, once, in G/C/H order after its predecessor reaches
a terminal fact. These proposed names are **not accepted handles** until Root's
corresponding supervisor call is accepted. Do not resend ambiguous acceptance.

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b02_p43_G_d961c5826 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b02-p43-20260908/G_process_time.txt /usr/bin/timeout --signal=KILL 60s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b02-p43-20260908/G.sh'"
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b02_p43_C_d961c5826 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b02-p43-20260908/C_process_time.txt /usr/bin/timeout --signal=KILL 900s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b02-p43-20260908/C.sh'"
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b02_p43_H_d961c5826 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b02-p43-20260908/H_process_time.txt /usr/bin/timeout --signal=KILL 900s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b02-p43-20260908/H.sh'"
```

Each script changes to the bound cwd, then invokes the existing fresh physical/
effective >=4GiB memory admission, joined immediately by `&&` to `exec` of the
configured `/home/wu/.venvs/hmasd/bin/python` and exact B02 runner argv. The
scripts contain the complete argv: seed770303, bound launch SHA, fresh arm output,
and H's fresh C/G summary paths. Evaluation master770304, CPU4, FP32 learner and
FP64 host/shared reward are the accepted B02 implementation bindings.

The **outer timeout surrounds the entire script**, including admission,
interpreter/import, all construction/training/evaluation, H comparisons and
closed-file publication. G60s/C900s/H900s are complete caps, summed1860s. KILL adds
no grace period or retry. External `time` surrounds the bounded command; it writes
wall, peak RSS and exit status in command staging, so timing requires no prior
scientific directory. The runner's cooperative timer remains supplementary.

## Paths, continuation and return

Relative to the detached cwd, scientific parent is
`temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303`.
Each G/C/H output contains `admission.json`, `summary.json` and any arm-local logs.
Admission measures before creating its receipt parent; the admitted runner
creates its output. H consumes only this parent's C/G summaries.

For each proposed `fsd_native_b02_p43_<arm>_d961c5826`, existing supervisor facts
will live in `/home/wu/.agent-tasks/<handle>/`: `task.log`, `status`, `exit_code`,
`pid`, `start_time`, `runner.sh`; tmux session `agent_<handle>`.
Complete time/RSS is
`/home/wu/hmasd-inputs/fsd-native-renewal-b02-p43-20260908/<arm>_process_time.txt`.
Root records actual acceptance and observes that same identity with existing
`agent-task status`/`logs`, following
[EXPERIMENT_MONITOR](../../../project/EXPERIMENT_MONITOR.md). No adoption claim
or extra readiness ACK is made by this preparation.

Failed G does not block independent C/H, and missing C does not erase H's own
endpoint. Missing C prevents complete pair polarity; missing G only limits
references. Stop each affected arm at completion/cap/nonfinite/integrity failure,
preserving every raw outcome and actual exposure. No retry, shortened/stitched
result, extra seed/pair/endpoint, cap extension, checkpoint, Pro Send or successor.

Reuse accepted24 fake cases (complete process4.6721191s), independent RNG/identity
review and publication coverage from [technical acceptance](FSD_NATIVE_RENEWAL_LEARNING_B02_TECHNICAL_ACCEPTANCE_20260908.md).
No smoke/calibration/suite was repeated. Per-arm cost anchors remain B01's
complete G2.47/C371.89/H333.89s; actual B02 segment/optimizer work is unmeasured.
The exact cost scope is five16×400 training plus one32×400 endpoint per learner,
one32×400 G endpoint;64,000 training and38,400 scoring steps total. No effective
M is inferred from buffer sizes or segment counts. Study elapsed critical path
includes between-arm gaps; summed invocation wall and aggregate CPU are separate
facts, not inferred from these anchors. No additional measurement is allocated.

After terminal facts Root returns all raw summaries, admissions, complete time/
RSS, full logs and supervisor witnesses to this same CM (follow-up if idle).
CM collects without rerunning or filling a missing H panel outside its cap,
commits/pushes technical evidence and returns to DM for all-outcome intake.
B01/B02 stay separate training-pair rows; no pooled conditional-SE estimator.
Local editing ownership is released after this binding commit/push. Root has
the allocated launch route; CM has performed zero scientific invocations.
