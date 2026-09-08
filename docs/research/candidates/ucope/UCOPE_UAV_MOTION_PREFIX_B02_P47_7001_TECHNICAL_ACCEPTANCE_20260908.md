# UCOPE B02 P47 — master 7001 technical collection

**Technically accepted:** the completed 7001 pair conforms to the bound B02 configuration, required measurements and scientific caps. The existing route releases 7002 irrespective of the negative first T−G score. This is one training-pair endpoint, not the two-pair joint result or a scientific direction disposition. No retry, extra evaluation, source change or scientific execution occurred during collection.

## Binding, terminal identity and preserved earlier failures

Contract: [B02 card §§2–7](UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md), [code spec §§2–6](UCOPE_UAV_MOTION_PREFIX_B02_CODE_SPEC_20260908.md), and the [P47/P48/P50 Root handoff](UCOPE_UAV_MOTION_PREFIX_B02_P47_ROOT_HANDOFF_20260908.md). Exact source is `6374063408208ba67b8cb7c69ebc0babb0f00259`, with `b02` / `agent_compound`, master 7001 and declared masters `[7001,7002]`. The real summary binds `UCOPE-UAV-MOTION-PREFIX-B02`, the B02 card and section 5; its mode/status are `UAV_B_EXPLORE` / `COMPLETE`.

- Node: `hmasd-wsl-node`; source cwd `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b02-p47-20260908` remained clean at the exact accepted HEAD when collected. P50's complete required-source byte verification remains applicable; it was not repeated.
- Actual terminal supervisor: `ucope-uav-motion-prefix-b02-7001-p47-20260908-cwd02`; PID `2781871`; `status=finished`, `exit_code=0`. Authoritative start epoch `1788890339`, log start `2026-09-09T01:58:59+08:00` (2026-09-08 17:58:59 UTC), end `2026-09-09T02:03:52+08:00`; supervisor duration 293 seconds. These raw times control over a Root log's reporting timestamp.
- Actual runner script retains the correct `-p47-` cwd, joined `preflight && runner`, exact interpreter `/home/wu/.venvs/hmasd/bin/python`, `--pair b02 --seed 7001`, and the unchanged output root. The complete external timeout is **3600 seconds per pair**, not per arm; internal arm caps remain 1800 seconds and the selected two-pair sum cap remains 7200 seconds.
- The earlier handle without `-cwd02` remains a preserved pre-admission cwd failure with zero scientific work; its runner omitted `-p47-`. It is not an additional trained pair. P50's earlier staging/SSL facts also remain preserved.
- The historical synthetic smoke **80.578 seconds against 60 seconds** is not reclassified as conforming. P48 explicitly accepted that named task's existing functional/publication evidence. No smoke, warm-up, profile or speculative repair was repeated here.

## Collection and bounded readback

Root dispatched this named terminal collection after its 11:10 log receipt. CM used the existing local direction checkout `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, initially clean at `01fa2659d4b6518347dd83b5aae0452b90db8c59`. CM owns only this technical record; DM retains scientific/intake/card ownership.

The remote output remains at `temp/directions/ucope/exp/uav-motion-prefix-b02-7001-p47-20260908` relative to the detached cwd. Collected bytes are at `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7001-p47-20260908/`. All seven output artifacts and six supervisor files were copied over the existing authenticated SCP route and matched remote SHA-256/size readback. No remote output or failed-handle bytes were modified.

[Transfer commands/exit/timing](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7001-p47-20260908/collection-transfer.json), [remote source/artifact readback](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7001-p47-20260908/collection-remote-readback.json), and [13-file correspondence result](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7001-p47-20260908/collection-byte-check.json) retain transport evidence. Transfer operations exited 0 in 1.562 and 0.485 seconds; remote readback/byte comparison exited 0 in 0.782 seconds. At that readback the prospective 7002 handle was absent.

The [read-only technical checker](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7001-p47-20260908/technical-check.py) ran once with the installed local CPU interpreter and exited 0; its measured check wall was 1.813 seconds. [Machine-readable acceptance](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7001-p47-20260908/technical-check.json) records exact counts, endpoint arithmetic, checkpoint shapes/norms and resource facts. It deserializes tensor dictionaries with `weights_only=True`; it creates no model, optimizer or environment and performs no forward, learning or evaluation call.

Checks establish:

- Exact real configuration (H=256, 512 training episodes per fit, 32 final episodes per T/G/H, chunk 32), source/card/algorithm identity and all b+domain seed metadata. Every episode's reset seed and row identity match its arm/phase/episode association.
- Unique complete episode and rollout coverage; every episode contains 256 primitive steps. Rollout records contain 512 rows and four numbered finite epoch records each, with post-step counters totaling 1024 Adam calls per fit. These counters are accepted-source measurements, not reconstruction from absent optimizer-state checkpoints.
- Native row `J=reward_sum/256`, prefix plus suffix reward conservation and exact correspondence between evaluation rows and summary J arrays. Recomputed pair differences, mean and conditional evaluation SE agree with the summary. This checks arithmetic over preserved native measurements, not a new simulator replay.
- Velocity counts satisfy `1280−3*d4` per T episode, 1280 per G episode and zero for H; duration counts are five per T episode and zero for G/H. All 1600 selected diagnostic frames have the expected unique arm/episode/time/agent identities, 108 finite actor components, t0-only duration, t1–3 held-action masks/unchanged commands and t4 release.
- Final T/G checkpoints match the full selected configuration, are finite CPU FP32 tensor dictionaries, and contain 66,441 / 66,311 parameters. Their group final norms agree with reported exposure within FP32 tolerance. Reported total displacement is nonzero in both arms (T 8.4092951, G 8.1893864); no universal head-movement condition is imposed.
- No incomplete rows, nonfinite learning records, cap breach or missing primary/hover/diagnostic dependency is reported. All selected output paths published and read back successfully.

## Actual work and resource observations

| Arm / phase | Episodes | Team steps | Velocity decisions | Duration decisions | d4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| T training | 512 | 131072 | 651529 | 2560 | 1277 |
| T final evaluation | 32 | 8192 | 40720 | 160 | 80 |
| G training | 512 | 131072 | 655360 | 0 | 0 |
| G final evaluation | 32 | 8192 | 40960 | 0 | 0 |
| H final evaluation | 32 | 8192 | 0 | 0 | 0 |

Totals: **262144 training +24576 evaluation =286720 team steps**, 2048 actual Adam calls, 512 rollouts, 1120 complete episodes, 1600 diagnostic frames and zero partial steps. Native step-call counter is 286720. Constructor/constructor-reset counts are two and explicit resets are 1120; constructor events are reported separately from the step-call counter.

Fresh admission captured at `2026-09-08T17:58:59.296183Z`, from `/proc/meminfo`, passed physical and effective memory floors with **15,639,519,232 bytes each** against 4,294,967,296 required. Both pass fields are true; failure reasons are empty. Cgroup-specific fields are null, as recorded; no additional resource claim is inferred from them.

| Timing scope | Seconds |
| --- | ---: |
| T complete arm, including startup/common initialization | 137.78884596005082 |
| G complete arm, including H and pair publication | 137.53816204698524 |
| Runner complete pair | 275.32700927200494 |
| External joined admission/runner process | 293.10 |

`/usr/bin/time` reports peak RSS **553596 KiB**. External time includes the wider admission/process boundary; it is not substituted for internal arm clocks. The single invocation's observed critical path and sum of invocation wall are both 293.10 seconds; aggregate CPU is unmeasured. Each arm is below 1800 seconds and the complete pair is below 3600 seconds. Both-pair sum conformance is not yet asserted. No telemetry is added.

## Preserved endpoint arithmetic and continuation

| Mean J | Value |
| --- | ---: |
| T | 0.14909714127451154 |
| G | 0.19636424569819022 |
| H | 0.17158544962861455 |

| Within-master contrast | Mean | Conditional evaluation SE |
| --- | ---: | ---: |
| T−G | −0.04726710442367869 | 0.009568020281619656 |
| G−H | +0.024778796069575677 | 0.012014136875474236 |
| T−H | −0.022488308354103006 | 0.011239083046653865 |

All 32 per-arm endpoint values and every signed difference remain in the collected raw files. There is **one** observed independent training pair. Conditional episode SE is not training-population uncertainty. The two-master mean, endpoint sample SD and card's joint UP/WITHIN/DOWN reading wait for 7002; no arithmetic-only joint aggregate was executed yet.

CM's technical disposition is **accept 7001 and release the original 7002 route irrespective of score**. Root owns its fresh admission, launch and observation; DM owns per-pair scientific intake and all-outcome interpretation. This record changes no scientific allocation or failure rule. Remaining work is the already selected 7002 invocation, its technical collection, then the authorized arithmetic-only joint aggregate and DM intake.
