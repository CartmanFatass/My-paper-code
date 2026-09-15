# ACVC_CLUSTER_MAPPO_COMPARISON_B01 — E0 result evidence

## Bound object, source and rule

B/EXPLORE, one prospectively paired training block MASTER28331/EVAL38331, exactly two original fits. [Frozen card](ACVC_CLUSTER_MAPPO_COMPARISON_B01_SCIENCE_CARD_20260914.md) commit2f90398a865a0eaebc78f2af603cb4d4a54487de; exact numerical/launcher sourcee4d3f324ef2b233d0e97b347a5b94c9061ac6f52; published command bindinga14eeee5c640343276966d321ffc6466e4bfc7fe; pinned official on-policy de66d7a4b23fac2513f56f96f73b3f5cb96695ac. The Portfolio allocation is full responseade27ced0e8a0ab63b89b9396bd0a7668f1d9f2b and its completed application, not a new local investment decision.

Primary reading rule applied verbatim:
- `delta_F_M > .01`: F_ABOVE_MEI.
- `-.01 <= delta_F_M <= .01`: WITHIN_MEI, a small signed point observation, not equivalence.
- `delta_F_M < -.01`: M_ABOVE_MEI.
- Missing/incomplete bound operand: INCOMPLETE for that contrast; independent trustworthy support remains reportable.

J is the complete native team episode sum divided by256. Both fits and all four sole-final64-world panels are complete. The unrounded primary is **+.02343964960218458J**, so the frozen point rule gives **F_ABOVE_MEI**. No interval, significance, seed-SD or stronger evidence-class gate replaces that rule.

## Absolute scores and every declared contrast

| Package | Mean J | Mean episode sum S |
|---|---:|---:|
| C | .3224744244456476 | 82.55345265808579 |
| F | .35722397427519226 | 91.44933741444922 |
| own-dwell | .34500259709351333 | 88.32066485593941 |
| M | .33378432467300767 | 85.44878711628996 |

| Contrast | Mean delta J | Sample SD J | Conditional SE J | Negative/positive worlds | Worst delta J | Frozen reading |
|---|---:|---:|---:|---:|---:|---|
| F−M (primary) | +.02343964960218458 | .08322268827920017 | .01040283603490002 | 22/42 | −.21151331203707885 | F_ABOVE_MEI |
| C−M | −.011309900227360047 | .08097400196790928 | .01012175024598866 | 33/31 | −.18321525004025363 | DOWN |
| F−C | +.03474954982954462 | .07532191813786182 | .009415239767232728 | 15/49 | −.18883327302214076 | UP |
| F−own-dwell | +.012221377181678915 | .06893431555193077 | .008616789443991347 | 23/41 | −.18194364064375085 | UP |

No zero world differences occur. [COMPARISON.json](evidence/cluster_mappo_comparison_b01_20260914/COMPARISON.json) and [WORLD_DIFFERENCES.csv](evidence/cluster_mappo_comparison_b01_20260914/WORLD_DIFFERENCES.csv) retain every absolute score, matched reset address, difference and opposite-tail maximum. Differences and sample SD/sqrt64 were recomputed from the complete raw rows and agree with the frozen reducer. These are conditional world summaries for the attained fitted policies, not training-population precision. Two fitted arms form one training block; four panels do not create four independent fits. Shared worlds do not imply equal policy trajectories, recurrent state, motion draws or intervention dose.

The complete F package leads the declared untuned M recipe on this point observation even though C alone trails M. F also exceeds its own-dwell control by just.002221377181678915J beyond this card's MEI; that small excess and23 adverse worlds restrain interpretation. F has6505 retraces and own-dwell4959 interventions along their separate histories; this is not matched dose or a pure retrace/temporal-memory effect. M and C differ in GAE versus MC targets, normalization, architecture and optimizer/loss arrangements. Equal private108 execution inputs and exposure do not isolate one of those differences.

## Actual exposure, implementation and measurement limits

Each fit:4096H256 train episodes,2048 rollouts and8192 PPO minibatches,1048576 native training team ticks. C has8192 joint Adam steps and8192 epoch records; M has8192 actor plus8192 critic Adam steps and2048 records that each average four minibatches. C final3×64 and M final64 total256evalepisodes/65536evalticks. Totals:2 fits,8192train+256eval=8448 scored episode rows,2162688 native team ticks,24576 optimizer.step calls,2 fixed snapshots and4 final loads. Each actor replays20971520 rows; C critic4194304 team rows versus M critic20971520 repeated agent rows. Seven environment constructor resets are unscored and reported separately. No retry, tuning, midpoint, alternate endpoint, pilot, replacement or extra evaluation occurred.

[M verification](evidence/cluster_mappo_comparison_b01_20260914/M_LOCAL_VERIFICATION.json) and [C verification](evidence/cluster_mappo_comparison_b01_20260914/C_LOCAL_VERIFICATION.json) check every training episode identity/reset/length, ordered rollout/epoch records, finite loss/reward/gradient fields, exact final panel metadata and actual learning counts. Both source/runtime configurations match the frozen CPU FP32/one-thread recipes. C actor/critic displacement7.204831600189209/14.669486045837402; M actor/critic/head displacement9.233359336853027/8.888741493225098/1.6562280654907227, all finite. These show real parameter learning, not a causal explanation of the ranking. Final checkpoint bytes were decoded without constructing models; all actor/critic tensors are finite FP32 and metadata matches the final counts. M's saved ValueNorm state is finite and nonzero. [Checkpoint verification](evidence/cluster_mappo_comparison_b01_20260914/CHECKPOINT_VERIFICATION.json).

Raw summaries preserve inherited placeholder zero for selected_final_checkpoints in both arms and velocity_decisions/recurrent_observations in M. Those fields were not wired for this adapter and are **unmeasured**, not proof of zero M motion, no recurrence or no selected endpoint. Populated actual final_checkpoints/post_fit_loads, M actor-forward counters, native transitions, optimizer steps and raw score sequences independently support this comparison. C's similarly named recurrence/velocity counters count its training phase only. Under evidence-spec§11.8.7 the missing auxiliary instrumentation limits dependent claims; the primary does not depend on it. Original bytes are not repaired or reclassified, and no scientific rerun follows.

Prelaunch17 focused synthetic cases plus two independent analytic probes passed (about16.024s command wall), with0 native calls. A failed H8 C test fixture was corrected to H32 before its focused rerun; production code was unchanged by that repair. Independent Astra/high review inspected the full numerical, recurrent, information, final checkpoint and publication path and found no material issue. New source585lines, runner187, within frozen engineering limits. The declared missing auxiliary counters are a publication limitation, not an unreported scope-budget breach. Full review/self-check/source and ordinary Git staging repair are in [EXECUTION](evidence/cluster_mappo_comparison_b01_20260914/EXECUTION.md).

## Complete native cost and preservation

| Original | PID | Whole native wall s | User+system CPU s | Peak RSS KiB | Native/supervisor exit |
|---|---:|---:|---:|---:|---|
| C | 3714457 | 1670.62 | 1670.31 | 561040 | 0/0 |
| M | 3714507 | 1521.04 | 1521.63 | 589924 | 0/0 |

Whole-native wall sum3191.66s and aggregate CPU3191.94s; concurrent programme span is about1671s at supervisor whole-second resolution. Do not divide the summed work by the overlap or sum per-process peaks as a measured simultaneous peak. C exceeded its ordinary1400s planning estimate; M was below its ordinary2400s estimate. Neither was a cap and no stop/retry occurred. The older C1192.29s was a historical term, not a guarantee on this concurrent programme. Complete support/provider/maintenance/agent/lifetime cost remainsUNKNOWN; the original pair's native allocation cost is now measured. Summary timer samples before final process exit are not substituted for GNU whole-invocation timing.

Both actual-node adjacent admissions passed4GiB; C13,068,771,328bytes, M12,828,741,632bytes, cgroup fields null. Source/dependency bytes, admission, one-time accepted commands and terminal native/supervisor logs are separately preserved. Monitor native finals delivered actual terminal facts. Its unavailable send_message and early healthy-active finals interrupted continuous observation; the same child was resumed and its terminal event list now has empty active_set. Incorrect old timeout fields were corrected and never controlled these jobs. No live handle remains.

Each original has14 verified remote/local files including final.pt (28 total). All26 non-checkpoint originals are committed under evidence/cluster_mappo_comparison_b01_20260914/native. Exact local archives: `temp/directions/acvc/retained/cluster_mappo_comparison_b01_20260914/C_original.tar.gz`1412542bytes/SHA256f62f506a44ec15c4900ef96fbf562b05108c5ea169df27738a1fad27710a573b; M_original.tar.gz557076bytes/SHA25667b3ff30aaedc0c65eeb8d6b425d20ee88248f050a2c45f2e254f1d064055c8b. The unique checkpoints remain in these verified archives and extractions. Exact remote cleanup follows confirmed preservation; current local test scratch deletion remains policy-denied and retained.

## Bounded reading, prediction and owner pause

Strongest support: a positive fixed F−M package comparison together with retained positive F−C and F−own-dwell. Strongest contradiction/limit:22/64 F−M adverse worlds, conditional SE.010402836J, a small F−own-dwell margin and one training block. This is evidence for the attained finite-learning packages, not stable superiority, tuned same-information headroom, equivalence, default/safety promotion, population inference, transfer or K/N/component attribution. Matching tuned headroom remains absent. The earlier direct-HMASD information-right mismatch remains a separate uncompleted hierarchy question; this M comparison does not solve it.

DM forecast assigned primary F_ABOVE_MEI probability.35, while modal M_ABOVE_MEI.45 did not occur (multiclass Brier.665). Supporting C−M DOWN/F−C UP/F−dwell UP Briers.245/.095/.24. Completeness forecast.90 realized complete, binary Brier.01. Owner prediction not taken; canonical review inbox empty at intake. Prior fixed-rate losses, gate/train-through failures, consumed C evidence and recasts2 are preserved, without retrospective pooling or rescoring.

Owner now explicitly requires finish-current-and-pause. This valid B completes its two-original allocation; A/B objects do not acquire a C-style consumption state. No successor, new direction/Portfolio request or new Transport is opened. ACVC scientific disposition remains CONTINUE/MEDIUM/recasts2 with its occupied slot; the operational pause will be recorded after exact closeout. [Full intake](ACVC_CLUSTER_MAPPO_COMPARISON_B01_INTAKE_20260914.md) separates these decisions and remaining limits.
