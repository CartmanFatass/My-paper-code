# UCOPE P24 master6902 — technical acceptance

**PASS. Both P24 invocations are terminal and technically accepted for DM intake.** This is conformance to the [P24 handoff](UCOPE_UAV_MOTION_PREFIX_B01_P24_ROOT_HANDOFF_20260907.md) and card§10, with no scientific interpretation or further execution selection. Negative and positive outcomes remain unchanged. No new UAV/optimizer call, retry, source change or trajectory replay occurred during collection/aggregation.

## Binding, terminal and resource facts

Handle `ucope-uav-motion-prefix-b01-6902-p24-20260907` on `hmasd-wsl-node`; exact source **`9c541a8047b8c33e90f09aa65e326180343a23a0`**, detached cwd `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907`. Retained supervisor reports `finished`, exit0; wrapper is LF-only with the issued `--pair p24 --seed 6902`. Actual collected summary/config bind seed6902, pair`p24`, declared masters`[6901,6902]`, card section10, correct card path and the prescribed `b=690200000` seed offsets. Both final checkpoint configurations match.

Fresh admission passed physical/effective **15,652,552,704 bytes**, both above4GiB. GNU time whole wall **280.64s**, peak RSS **555104KiB**. Runner wall272.672735s, T136.742595s, G135.930139s including H/publication. No arm or pair cap breach; CPU remains unmeasured.

Evidence root: `C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b01-6902-p24-20260907/`, containing admission, summary, three JSONLs, both final checkpoints, supervisor files and `technical_verification.json`. The [committed machine verification](UCOPE_UAV_MOTION_PREFIX_B01_6902_TECHNICAL_VERIFICATION_20260907.json) retains the complete counts, exposures, paired vectors/SEs and check scope. The intended path is complete, without the historical6801 CR deviation.

## Record-level checks

- **1120 complete episode rows**, exactly T512train/32eval → G512train/32eval → H32eval,256 steps each with prescribed reset seeds. **286720 team/UAV steps**,1024 train+96eval episodes,two constructor resets and zero partial episode work reconcile.
- **512 rollout rows**, each512 steps/two episodes/four finite epoch records, sum to **2048 actual Adam calls**,1024 per fit. Episode/summary velocity/duration/d4 counts satisfy the original held-sample law; G retains every primitive decision and H has no learner.
- Both saved checkpoints have finite FP32 weights, correct parameter counts and final norms matching exposure; total displacement is nonzero. No checkpoint was executed or optimizer resumed during readback.
- Raw return/J and prefix+suffix arithmetic agree for every episode. The final sampled T/G/H arrays match the complete episode rows; all pair differences, means and conditional SEs were independently recomputed, with no sign filtering.
- **1600 t0..4 diagnostic frames** cover all T/G evaluation episodes/agents with correct own last commands, remaining holds, masks, held command reuse, next-observation clock, reset identity, source-index limits and prefix reward sums. No hover/diagnostic gap is reported.
- Admission, exact command/source/pair/card labels, terminal exit and whole/arm bounds reconcile. Prior accepted source/review/tests remain evidence for unlogged learner likelihood/gradient semantics; no complete trajectory replay was performed.

## Exact observations and arithmetic handback

6902 final native means: T **0.11209171238425403**, G **0.16245713491694358**, H **0.14535619696314445**. T−G **−0.050365422532689566**, conditional SE **0.009784851728286003**; G−H **+0.017100937953799134**, conditional SE **0.011890814511602335**. T final sampled d4 frequency **0.45**. These are recorded observations only; DM owns their interpretation.

The existing read-only CLI ran `--pair p24 --aggregate` on the two collected P24 summaries, with no policy/UAV import or checkpoint load. [Retained P24 aggregate](UCOPE_UAV_MOTION_PREFIX_B01_P24_JOINT_AGGREGATE_20260907.json) preserves the actual6901/6902 labels, raw arrays and both signs. Separate stdlib arithmetic from endpoint arrays agrees: pair means **[0.043351866492163174, −0.050365422532689566]**, joint mean **−0.003506778020263196**, endpoint sample SD **0.06626813058389298**, joint conditional SE **0.007033641405302189**. The runner's fixed arithmetic field is `WITHIN`; no scientific conclusion is added here. This is separate from P21; four-unit descriptive work belongs to DM.

The two P24 invocations total573440 UAV steps,4096 Adam calls,2240 complete episodes and3200 diagnostic frames. Summed external wall **564.93s** is below the7200s new-pair sum; it is not study elapsed critical path, which includes the intervening technical-return interval. No aggregate CPU estimate is asserted.

Root may integrate this technical evidence and return both new outcomes to `/root/dm_ucope_p13_intake`. There is no outstanding scientific invocation in the P24 allocation. No third pair, retry, successor, promotion, fallback or cap change is supplied by this return. Scope§4 additions: **none**.
