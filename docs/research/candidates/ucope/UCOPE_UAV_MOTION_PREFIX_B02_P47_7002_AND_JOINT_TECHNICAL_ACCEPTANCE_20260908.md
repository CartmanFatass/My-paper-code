# UCOPE B02 P47 — 7002 collection and joint arithmetic

**Technically accepted:** master 7002's terminal artifacts conform to the bound B02 configuration, measurement requirements and scientific caps. The authorized arithmetic-only aggregate of accepted 7001/7002 summaries also passes readback. Both selected pairs are now collected; no third pair, retry, new evaluation or further scientific execution is selected here. DM retains all-outcome interpretation and next-object decisions.

## Binding and collection

The unchanged contract is [B02 card §§2–7](UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md), [code spec §§2–6](UCOPE_UAV_MOTION_PREFIX_B02_CODE_SPEC_20260908.md) and the [P47/P48/P50 Root handoff](UCOPE_UAV_MOTION_PREFIX_B02_P47_ROOT_HANDOFF_20260908.md). Source remains **`6374063408208ba67b8cb7c69ebc0babb0f00259`**, at `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b02-p47-20260908` on `hmasd-wsl-node`. Remote HEAD/status readback confirmed that source and a clean checkout; P50's prior complete required-source byte check was not repeated. Local code at the collection checkout remains byte-identical to the accepted package/runner source.

Actual terminal supervisor: **`ucope-uav-motion-prefix-b02-7002-p47-20260908`**; `finished`, exit 0, PID `2783664`, start epoch `1788894877`. Authoritative log start is `2026-09-09T03:14:37+08:00` (2026-09-08 19:14:37 UTC), end `2026-09-09T03:19:22+08:00`; duration 285 seconds. The stored command preserves the exact cwd, `/home/wu/.venvs/hmasd/bin/python`, joined preflight/runner, seed 7002 and original output root. It uses a **3600-second complete-pair** external timeout; internal arm caps are **1800 seconds each**. CPU FP32 and the accepted one-thread source route are unchanged.

All seven output artifacts and six supervisor files were collected to `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7002-p47-20260908/`. [SCP command receipts](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7002-p47-20260908/collection-transfer.json) report exit 0 in 1.625 and 0.422 seconds. [Remote readback](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7002-p47-20260908/collection-remote-readback.json) and [byte comparison](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7002-p47-20260908/collection-byte-check.json) confirm all 13 copied files match remote size/SHA-256; readback/comparison exited 0 in 0.390 seconds. Original remote and earlier failed-handle artifacts remain unchanged.

The [read-only technical check](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7002-p47-20260908/technical-check.py) reuses the [7001 acceptance checks](UCOPE_UAV_MOTION_PREFIX_B02_P47_7001_TECHNICAL_ACCEPTANCE_20260908.md) with the recorded 7002 binding and measured resource values. It ran once, exited 0 and measured 3.297 seconds. Its [result](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7002-p47-20260908/technical-check.json) preserves the actual quantities. Collection performs only artifact arithmetic and tensor-dictionary deserialization; no model, optimizer, environment, forward, learner or evaluator is invoked.

The actual summary is `UAV_B_EXPLORE` / `COMPLETE`, object `UCOPE-UAV-MOTION-PREFIX-B02`, pair `b02`, grouping `agent_compound`, master 7002, declared masters `[7001,7002]`, and the B02 card at section 5. Full configuration is H=256, 512 training episodes per fit, 32 final episodes per T/G/H, chunk 32, 1800/3600 caps and non-fixture mode. All seven b+domain seed fields and episode reset associations match master 7002.

Checks confirmed unique complete episode/rollout coverage, four finite epoch records per rollout, actual update counters, velocity/duration/d4 count laws, t0 duration and held-command diagnostic wiring, 108 finite actor features, native row reward/J arithmetic and exact summary correspondence. All 1600 expected frames are present. Primary, hover and diagnostics are complete, limits are empty, and there is no cap breach or partial step.

Both final checkpoints are finite CPU FP32 tensor dictionaries with the exact selected configuration and 66,441 / 66,311 parameters. Their final group norms match reported exposure within FP32 tolerance; total reported displacement is T **5.466739654541016**, G **7.856598854064941**. No requirement for universal parameter/head motion was added. Counts are accepted-source post-step measurements, not inferred from an optimizer state that was not saved.

## 7002 work, admission and wall time

| Arm / phase | Episodes | Team steps | Velocity decisions | Duration decisions | d4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| T training | 512 | 131072 | 651724 | 2560 | 1212 |
| T final evaluation | 32 | 8192 | 40690 | 160 | 90 |
| G training | 512 | 131072 | 655360 | 0 | 0 |
| G final evaluation | 32 | 8192 | 40960 | 0 | 0 |
| H final evaluation | 32 | 8192 | 0 | 0 | 0 |

7002 totals: **262144 training +24576 evaluation =286720 team steps**, **2048 actual Adam calls**, 512 rollouts, 1120 complete episodes, 1600 diagnostic frames, zero partial steps. Constructor/constructor-reset counts are two; explicit resets are 1120. The native step-call counter is 286720, separately from constructor events.

Fresh admission captured `2026-09-08T19:14:37.746838Z` reports physical/effective available memory **15,646,416,896 bytes each**, both above 4,294,967,296 required; both pass fields are true with no failure reasons. `/proc/meminfo` is the recorded measurement source; cgroup-specific fields remain null.

| 7002 timing scope | Seconds |
| --- | ---: |
| T including startup/common initialization | 138.25656845699996 |
| G including H and pair publication | 134.6804691849975 |
| Runner complete pair | 272.93703864404233 |
| External joined admission/runner process | 284.84 |

External peak RSS is **554792 KiB**. Aggregate CPU remains unmeasured. The wider external clock is not substituted for internal arm clocks. Every arm and complete pair is below its respective scientific cap.

## Existing arithmetic-only aggregate

Both source summaries were technically accepted before this one aggregate invocation. The exact committed runner/study code was unchanged in the local authoring checkout; no source-currentness guard or new validation machinery was added. The original handoff command was executed once:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_uav_motion_prefix_b01.py --pair b02 --aggregate C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7001-p47-20260908/summary.json C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-7002-p47-20260908/summary.json --out C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-p47-20260908-joint
```

[Invocation receipt](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-p47-20260908-joint/aggregate-receipt.json): exit 0, external wall 0.156 seconds. [Published aggregate](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-p47-20260908-joint/summary.json) and [independent arithmetic readback](C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b02-p47-20260908-joint/technical-check.json) agree on exact input modes, distinct masters, B02 object/card/grouping and complete primary. Readback computes the mean and sample SD from the two training-pair endpoints and combines their conditional evaluation SEs as specified. No episode is treated as an extra independent training pair.

| Master | Mean J T | Mean J G | Mean J H |
| --- | ---: | ---: | ---: |
| 7001 | 0.14909714127451154 | 0.19636424569819022 | 0.17158544962861455 |
| 7002 | 0.12314745662552364 | 0.12928366243820322 | 0.14753964411323622 |

| Master / contrast | Mean | Conditional evaluation SE |
| --- | ---: | ---: |
| 7001 T−G | −0.04726710442367869 | 0.009568020281619656 |
| 7001 G−H | +0.024778796069575677 | 0.012014136875474236 |
| 7001 T−H | −0.022488308354103006 | 0.011239083046653865 |
| 7002 T−G | −0.0061362058126795795 | 0.008186926654579155 |
| 7002 G−H | −0.018255981675033013 | 0.013412586657048335 |
| 7002 T−H | −0.024392187487712595 | 0.01380510652790013 |

Machine-emitted joint fields: **n=2** training pairs; mean T−G **−0.026701655118179134**; training-endpoint sample SD **0.029083937324133818**; combined conditional evaluation SE **0.006296284224781783**; exact card-threshold label **`DOWN`**. This records arithmetic, not a scientific mechanism/causality/transfer or next-object interpretation. All per-episode values, positive and negative differences, T/G/H results and historical failures remain available.

Complete selected scientific work is **524288 training +49152 evaluation =573440 team steps**, **4096 Adam calls**, 1024 rollouts, 2240 complete episodes, 192 final evaluation episodes and 3200 diagnostic frames. Partial steps are zero. Summed external scientific invocation wall is **293.10+284.84=577.94 seconds**, below the 7200-second summed cap; summed internal pair wall is **548.2640479160473 seconds**. The observed first-start-to-second-terminal interval is **4823 seconds**, including the intervening control-plane gap; it is not summed compute work. Aggregate CPU is unmeasured.

## Preserved limitations and return

The original synthetic smoke **80.578s versus 60s** breach remains preserved under P48's task-specific functional acceptance. It was not repeated or repaired speculatively. The earlier pre-admission cwd failure remains a zero-scientific-work supervisor failure, not a third training pair. This collection added no scientific invocation or evidence selection.

Both selected pairs and their required publication paths are technically accepted; no current runtime integrity gap remains in this route. Conditional evaluation uncertainty remains distinct from training-population uncertainty. The complete arithmetic and unchanged raw evidence return to `/root/dm_ucope_p47_resume` for all-outcome intake, prediction handling and scientific disposition. No further launch or successor is inferred by CM.
