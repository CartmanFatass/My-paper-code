# FSD B01 P38 exact Root launch binding

P38 allocates one G → C_train → H_train panel under
[the allocation](../../portfolio/handoffs/2026-09-08-p38-fsd-learning-b01-execution.md),
[P34 intake §6](FSD_NATIVE_RENEWAL_LEARNING_B01_P34_INTAKE_20260908.md#6-exact-next-allocation-need--requested-not-allocated)
and [B01 card §§2–6](FSD_NATIVE_RENEWAL_LEARNING_B01_SCIENCE_CARD_20260908.md).
This preparation is execution/collection of accepted P34, excluded from new CM
comparison; the three batches are exhausted. No scientific launch has occurred.

The designated authoring checkout is `C:/Projects/HMASD-worktrees/codex-fsd`,
branch `codex/fsd`, clean at entry `055d46100e890f2748e9a23c04782f60c6c172f4`.
Only this record and three five-line command scripts are added. No source,
configuration, test, governance or scientific meaning is changed; scope:none.
CM retains technical collection; Root launches and observes; DM interprets.

## Fixed source, prepared cwd and byte transport

- Scientific source SHA: **b3f86bb28879db239b07291c39d93a1c494abe50**.
- Node: `wsl_4070`, SSH `hmasd-wsl-node`, configured host `LAPTOP-U9TDKC8A`.
- Prepared fresh detached cwd:
  `/home/wu/hmasd-worktrees/fsd-native-renewal-b01-p38-b3f86bb28`.
- Interpreter: `/home/wu/.venvs/hmasd/bin/python`. CPU/four Torch threads,
  float32 learner and float64 host/shared reward remain pinned by the runner.
- Committed LF scripts: **018aac549737992950bb69c750dfd521d4d301d8**,
  [G.sh](native_renewal_learning_b01_p38_20260908/G.sh),
  [C.sh](native_renewal_learning_b01_p38_20260908/C.sh),
  [H.sh](native_renewal_learning_b01_p38_20260908/H.sh).
- Staged directory: `/home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908`.
  Staged filenames are `G.sh`, `C.sh`, `H.sh`.

The committed blobs were read by Python `subprocess.check_output(['git','show',
'018aac549737992950bb69c750dfd521d4d301d8:<path>'])` and written with
`Path.write_bytes` to the existing local runtime route
`temp/directions/flexible_skill_duration/runtime/p38-command-bytes/`.
`scp` transferred these files directly; no command-body PowerShell text pipeline
was used. Local committed bytes and remote `sha256sum` agree exactly:

| Script | Bytes | SHA256 |
| --- | ---: | --- |
| G.sh | 543 | `d72eaab9d2286d136bbfdd30bbdac08e47668b36e650c509b9848a5bf70ba598` |
| C.sh | 543 | `d7cca214f0acc77dd1966d6a0beb6678b860b4bc2e5733e19c8b91ce861cb1d7` |
| H.sh | 755 | `23c86bc5605319c67d5dfed7da48a2a2fe73e7d0c807fdd5be19a4f6314ce83b` |

All three contain zero CR bytes. Remote `bash -n` parsed each staged file without
execution. The configured network shell fetched the fixed source and created
the detached worktree; `rev-parse HEAD` returned the bound SHA and its status was
clean. The configured interpreter, `/usr/bin/time` and `/usr/bin/timeout` exist
and are executable. These are transport/source facts, not a learner probe.
Two initial read-only Git/SSH requests stalled; they were cancelled after the
configured network-shell fetch and independent destination verification succeeded.
No scientific process or admission was attempted by those requests.

At final preparation verification the scientific output parent and all three
proposed supervisor directories did **not** exist. No admission, scientific root,
model, learner, host episode, calibration/profile, suite or Pro Send was created.

## Exact commands — Root executes once, in order

Each following literal submits one arm through the existing supervisor. Execute
G first, wait for its terminal fact, then C, then H after C's terminal fact.
An accepted handle is established by that supervisor response, not by this table.
Do not resubmit an ambiguous or accepted name; reconcile the same identity.

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b01_p38_G_b3f86bb28 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/G_process_time.txt /usr/bin/timeout --signal=KILL 60s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/G.sh'"
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b01_p38_C_b3f86bb28 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/C_process_time.txt /usr/bin/timeout --signal=KILL 900s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/C.sh'"
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b01_p38_H_b3f86bb28 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/H_process_time.txt /usr/bin/timeout --signal=KILL 900s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/H.sh'"
```

These are a three-command list, not a wrapper that launches or retries other arms.
Scripts execute the exact intake argv, replacing only `python` with the configured
interpreter. H reads the existing C/G summaries inside H. Each script changes to
the fixed cwd, performs fresh on-node physical/effective >=4GiB admission, and
joins it immediately by `&&` to `exec` of that arm's runner. There is no gap for
another process, measurement, directory setup or script generation between the
admission and runner. A failed admission runs no model.

The timeout surrounds the **whole Bash script**, so admission, interpreter/import,
construction, all learning, evaluator construction/synchronization/scoring,
H arithmetic/readback and closed-file scientific publication are included.
`--signal=KILL` supplies no grace period or cap extension. `/usr/bin/time` surrounds
that timeout and records complete invocation wall, peak RSS and exit status even
on timeout; its output lives in command staging, so no scientific directory must
be created before admission. Caps: G60s, C900s, H900s, summed1860s. The runner's
cooperative clock is supplementary; its pre-publication timestamp is not a
replacement for external complete wall. Keep the existing supervisor exit witness.

## Prospective output, receipt and observation paths

Relative to the fixed cwd, output parent is
`temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203`.
Each `<arm>` in G/C/H has `<arm>/admission.json` and `<arm>/summary.json`.
The admission writer creates its receipt parent after measurement; the runner
creates its output. C/H learner/evaluator logs are below their own output dirs.
The scientific root remains unique to this source/attempt and is never resumed.

For each literal handle `fsd_native_b01_p38_<arm>_b3f86bb28`:

- Supervisor directory: `/home/wu/.agent-tasks/<handle>/`.
- Raw log: `task.log`; authoritative existing witnesses: `status`, `exit_code`,
  `pid`, `start_time`, `runner.sh`; tmux session: `agent_<handle>`.
- External time/RSS/exit file:
  `/home/wu/hmasd-inputs/fsd-native-renewal-b01-p38-20260908/<arm>_process_time.txt`.
- Root observes with `agent-task status <handle>` and `agent-task logs <handle> 40`
  through SSH, under [EXPERIMENT_MONITOR](../../../project/EXPERIMENT_MONITOR.md).
  Root records actual acceptance/tracking; this preparation requests no ACK or
  duplicate readiness confirmation.

P38 explicitly permits C/H after a failed G and H after a failed C. Numerical sign
never gates the next independent arm. Stop the affected invocation at cap,
nonfinite or integrity failure; retain all partial rows/counts and companions.
A failed learned arm prevents a complete learning-pair polarity. No retry,
shortened complete result, stitching, extension, seed/arm/endpoint/checkpoint
change, Pro Send or UAV change follows. Unknown acceptance is resolved before
continuation, without a blind second launch.

## Reused evidence, cost and collection return

Reuse [P34 technical acceptance](FSD_NATIVE_RENEWAL_LEARNING_B01_TECHNICAL_ACCEPTANCE_20260908.md):
18 focused synthetic tests, complete process4.4069052s and independent source
review/recheck with no remaining material findings. No suite or learner probe was
repeated. Publication coverage includes the actual synthetic main/pair path,
missing companions, nonfinite diagnostics, durable partial writes and deadlines.
Real model/runtime conformance will be observed only in P38's allocated arms.

Per-arm cost remains the [existing projection record](FSD_NATIVE_RENEWAL_LEARNING_B01_EXPOSURE_AND_COST_20260908.json):
C/H each historical505.86596735480975s anchor, G historical.27s; new effective M
and optimizer/segment work remain unknown. These are not a completion guarantee.
The exact invocation law remains five16x400 training plus one32x400 endpoint per
learned arm, one32x400 G endpoint. Sequential study elapsed critical path includes
between-arm observation gaps; summed invocation wall excludes those gaps.
Aggregate CPU has not been measured; no additional telemetry/probe is introduced.

After terminal receipts Root returns raw summaries, admission, full logs and
external time/status witnesses to this CM `/root/fsd_cm_baseline_a01` (reuse a
follow-up if idle). CM collects the same three outcomes and reports actual counts,
cap/admission facts, full/post arrays and dependent missingness without rerunning
or recomputing a missing H panel outside its cap. The DM
`/root/dm_fsd_p13_reentry` owns scientific intake from those preserved outcomes.
This handoff releases the CM's editing ownership after commit/push and supplies
Root the allocated launch route; it performs no launch itself.
