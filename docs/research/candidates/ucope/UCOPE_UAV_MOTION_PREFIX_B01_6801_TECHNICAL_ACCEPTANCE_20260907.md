# UCOPE UAV motion-prefix B01 pair6801 technical acceptance

**PASS; the already allocated pair6802 may proceed irrespective of score.** This return follows [P21 handoff](UCOPE_UAV_MOTION_PREFIX_B01_P21_ROOT_HANDOFF_20260907.md) and [card §8](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#8-current-p21-execution-allocation--2026-09-07). No source, seed, metric, budget or scientific command changed. The independent code review and original focused tests remain the evidence for unlogged learner internals; this collection added zero UAV/optimizer calls and performed no trajectory replay.

## Terminal identity and collected evidence

- Node `hmasd-wsl-node`; accepted supervisor `ucope-uav-motion-prefix-b01-6801-p21-20260907`; full launch SHA **`536949660fee3ab9ac92aba29c2c0455ffe9f6e1`**; remote cwd `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907`.
- Direct supervisor status: `finished`, exit **0**, PID2758585, tmux inactive. Admission captured `2026-09-08T04:15:06.418375Z`: physical/effective available **15,651,278,848 bytes**, both above4GiB. Whole wall **288.88s**, peak RSS **553,808KiB** from retained GNU time output. Runner wall283.726934s; T142.355041s and G141.371892s, including its H/publication path. No cap breach; aggregate CPU unmeasured.
- Local evidence root: `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-6801-p21-20260907/`. It contains `resource_admission.json`, `summary.json`, all three JSONL files, both final checkpoints, `technical_verification.json`, and `supervisor/{runner.sh,task.log,status,pid,start_time,exit_code}`. Machine-computed collection checks and endpoints are retained in [technical verification](UCOPE_UAV_MOTION_PREFIX_B01_6801_TECHNICAL_VERIFICATION_20260907.json).

**Observed transport deviation:** `runner.sh` retained a trailing carriage return after the command supplied through Windows stdin. The admission wrote to the intended remote directory, but scientific files were written to its sibling whose name is `uav-motion-prefix-b01-6801-p21-20260907\r` (the suffix is one literal U+000D byte). `ls -lb` and the supervisor command establish this path fact. The six scientific files were copied from that existing sibling using a one-character path glob into the intended local collection root; no remote evidence was renamed/deleted and no scientific invocation was repeated. The files' configured seed/source and internal counts are unchanged. Future remote aggregation must use the actual6801 path, or aggregate the normalized local collected copies; the old unsuffixed remote6801 summary path does not exist.

## Checks and bounded result

An offline Python/Torch read over recorded bytes established:

- Exact serial episode order: T512 train/32 eval, G512 train/32 eval, H32 eval; each256 steps, prescribed reset seeds. **1,120 complete episodes**, **286,720 UAV steps**, no partial episode steps; two constructor resets.
- **512 rollout rows**, each512 steps/two episodes/four actual epochs; **2,048 Adam calls**, 1,024 per learned arm. All recorded losses/grad norms finite. T training velocity651340 =655360−3×1340 with2560 durations; T evaluation40711 =40960−3×83 with160 durations. G counts655360/40960; H has no decisions or optimizer.
- Both saved final checkpoint configurations match the real card configuration, all saved tensors are finite CPU-loaded FP32, parameter counts match T66441/G66311, and saved final norms reconcile with exposure. Both arms report nonzero absolute/relative parameter displacement.
- Every episode's raw return, time-average J and prefix+suffix arithmetic reconciles. The32 complete final T/G/H arrays match episode rows; paired differences, means and conditional SEs were independently recomputed. No favorable-outcome filtering.
- All **1,600 diagnostic frames** cover t0..4 for every T/G evaluation agent. Own last-command input, normalized remaining hold, actual decision masks, d4 hold reuse, next-observation clock, source-index limits and prefix reward sums reconcile. No diagnostic/hover limit is reported.

Native final means: T **0.19815651099380138**, G **0.1914424787546125**, H **0.1490047481461882**. Pair T−G **0.006714032239188856**, conditional episode SE **0.011125795446968265**; G−H **0.04243773060842434**, SE **0.012071690736933637**. T final sampled d4 frequency **0.51875**. These are one pair's observations, not the card's two-pair joint reading or training-population stability. DM owns scientific interpretation and actual-entry documentation.

The existing complete-path288.88s measurement now supplies a prospective cost basis for the same-work6802 pair: T approximately142.36s, G including H/publication approximately141.37s, external pair approximately288.88s, each below its original cap. These are planning estimates from6801, not guarantees or a changed stop rule. There is no new pilot, exposure or CPU estimate. Pair6802 remains allocated without a sign/MEI/competence condition.

## Exact pair6802 route and transport correction

Keep the [original pair6802 command](UCOPE_UAV_MOTION_PREFIX_B01_P21_ROOT_HANDOFF_20260907.md#pair6802--only-after-cm-technical-acceptance-of-pair6801), the same exact launch SHA/cwd/output/handle, and fresh actual-node admission. When Root sends the literal via PowerShell stdin, strip carriage returns **on the remote input stream** before Bash. Stripping only the PowerShell string before piping is insufficient because the pipeline can append CRLF. The following is the complete transport-safe PowerShell literal; the scientific argv and supervisor command are unchanged:

```powershell
@'
/usr/local/bin/agent-task run ucope-uav-motion-prefix-b01-6802-p21-20260907 "/usr/bin/time -f whole_wall_seconds=%e,peak_rss_kib=%M /usr/bin/timeout --signal=KILL 3600s /bin/bash --noprofile --norc -c 'cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --seed 6802 --out temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907'"
'@ | ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "tr -d '\015' | /bin/bash -s"
```

A harmless `printf` probe of this CR-stripping transport returned exactly `LF_TRANSPORT_OK`; it made no scientific/admission call. Root owns the actual launch once, accepted-handle observation and terminal return to this same CM. Reconcile uncertain dispatch against that handle; no retry or replacement is allocated. After6802 acceptance, use the collected6801 and6802 summaries for arithmetic aggregation so the historical CR pathname is not silently assumed absent. No code correction or new §4 machinery was added.
