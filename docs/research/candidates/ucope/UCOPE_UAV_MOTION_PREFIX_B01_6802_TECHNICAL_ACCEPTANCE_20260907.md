# UCOPE UAV motion-prefix B01 pair6802 and joint technical return

**Pair6802 PASS; both allocated pairs are technically accepted and ready for DM joint intake.** [Card §8](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#8-current-p21-execution-allocation--2026-09-07), the [P21 handoff](UCOPE_UAV_MOTION_PREFIX_B01_P21_ROOT_HANDOFF_20260907.md) and [6801 acceptance](UCOPE_UAV_MOTION_PREFIX_B01_6801_TECHNICAL_ACCEPTANCE_20260907.md) retain their exact scientific meaning. There was no rerun, source change, additional seed/evaluation, optimizer update or UAV call during this collection/aggregation.

## Terminal evidence and checks

Execution source remained **`536949660fee3ab9ac92aba29c2c0455ffe9f6e1`**, node `hmasd-wsl-node`, cwd `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907`. Supervisor `ucope-uav-motion-prefix-b01-6802-p21-20260907` directly reports `finished`, exit0, PID2760832 and tmux inactive. Admission passed with physical/effective available **15,654,449,152 bytes**. Whole wall **286.36s**, peak RSS **557,216KiB**; runner wall279.581760s, T141.488827s, G138.092932s including H/publication. All original complete caps hold; aggregate CPU is unmeasured.

Artifacts were collected from the intended remote `temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907/` into `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-6802-p21-20260907/`, including admission, summary, three JSONLs, two final checkpoints and supervisor files. The retained wrapper is LF-only and the CR pathname problem from6801 did not recur. That historical6801 path deviation remains explicitly recorded; aggregation below uses its complete normalized local collection copy, not an assumed unsuffixed remote path.

[Machine verification](UCOPE_UAV_MOTION_PREFIX_B01_6802_TECHNICAL_VERIFICATION_20260907.json) records the same offline checks as6801:

- All **1,120 episode rows** follow exact T512train/32eval → G512train/32eval → H32eval order,256 steps each with prescribed reset seeds. Counts reconcile to **286,720 UAV steps**,1,024 train+96eval episodes, two constructors/resets and zero partial episode work.
- All **512 rollout rows** contain512 steps/two episodes/four finite epoch records, summing to **2,048 actual Adam calls**,1,024 per fit. T train velocity651838 =655360−3×1174; T eval40726 =40960−3×78. Duration counts2560/160. G velocity655360/40960 and no duration decisions; H has no learner.
- Native reward sum/J and prefix+suffix arithmetic reconcile for every episode. The complete final sampled T/G/H arrays match raw episode rows. Pair differences, means and conditional SEs were independently recomputed without outcome filtering.
- Both final checkpoints have the specified real configuration, finite FP32 tensors, correct T66441/G66311 parameter counts and final norms matching exposure; both report nonzero displacement. No optimizer state is resumed or changed by reading them.
- All **1,600 diagnostic frames** have the expected t0..4 coverage, own last commands, remaining holds, actual-decision masks, held command reuse, observation clock, index bounds and prefix rewards. No diagnostic/hover limit or cap breach is present.

These observations, together with the prior independent review and original focused tests, support technical conformance. Raw output does not independently reconstruct unlogged likelihood/gradient internals; no complete trajectory replay was performed.

## Completed two-pair arithmetic

The existing arithmetic-only CLI consumed the two local collected summaries and published `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-p21-20260907-joint/summary.json`. It loaded no UAV environment or policy checkpoint. Its result is retained as [joint aggregate](UCOPE_UAV_MOTION_PREFIX_B01_JOINT_AGGREGATE_20260907.json), including both raw T/G/H arrays, paired difference vectors and pair limits. A separate stdlib calculation from those endpoint arrays verified the mean, endpoint sample SD and joint conditional SE.

| Quantity | 6801 | 6802 |
| --- | ---: | ---: |
| T mean native J | 0.19815651099380138 | 0.17927686870918463 |
| G mean native J | 0.1914424787546125 | 0.15555605970373051 |
| H mean native J | 0.1490047481461882 | 0.14625468074141884 |
| T−G pair mean | 0.006714032239188856 | 0.023720809005454126 |
| T−G conditional episode SE | 0.011125795446968265 | 0.010131530857286448 |
| G−H pair mean | 0.04243773060842434 | 0.009301378962311667 |
| G−H conditional episode SE | 0.012071690736933637 | 0.008782791170015744 |
| Final sampled d4 frequency | 0.51875 | 0.4875 |

Joint T−G **0.015217420622321492**; sample SD of the two training-pair endpoints **0.012025607177551996**; joint conditional evaluation SE **0.007523816216520829**. The fixed point-reading rule yields **UP** because the joint mean exceeds0.01. This is the card's arithmetic branch, not a stability, transfer, causal-information or deployment conclusion. Two training-pair masters remain the independent units; episodes/agents/primitive steps were not pooled as training units. DM owns predictions, competence/attribution limits and scientific interpretation.

Combined actual work is **573,440 UAV steps,4,096 Adam calls,2,240 complete episodes and3,200 diagnostic frames**. Summed external invocation wall is **575.24s**, below7200s. This sum is not study elapsed critical path: the latter additionally includes the ordered between-pair collection/technical-return interval. No separately measured study-critical-path duration or aggregate CPU value is asserted.

## Return ownership

Root may integrate these evidence files and deliver the complete pair/joint evidence to `/root/dm_ucope_p13_intake`. Both exact allocated invocations are terminal; no additional scientific command remains in this handoff. DM records actual entry, result/intake, prediction scoring, brief/audit/owner traces at the existing B ceiling. A successor, promotion or retry is not authorized by this technical return. Scope §4 additions: **none**.
