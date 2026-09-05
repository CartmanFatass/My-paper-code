# A02 single-point technical collection

The one authorized A02 observation completed with technically complete actual and derived
measurements. No repeat, completed native tick, model, checkpoint, policy, optimizer or
source intervention occurred. DM independently applies the card rule; no successor authorized.

## Identity and originals

Task `dish_ground_source_a02_seed11_a1`, PID1653258, wsl_4070; source
`dd0e01bbc4aa0efd3c22b475585511232c1de4fc`; clean detached cwd
`/home/wu/hmasd-worktrees/dish-ground-a02-dd0e01bb`. Exact accepted command is preserved
in `DISH_GROUND_SOURCE_POINT_A02_CM_RETURN_20260905.md` and supervisor runner.sh:
actual-node admit-memory followed by `&& python -m scripts.run_dish_ground_source_point_a02`
with run --seed11 expressed as `run --seed 11`, separate receipt, absent result child.

Original summary: cwd-relative
`temp/directions/degraded_incumbent_shadow_handover/exp/ground_source_point_a02_20260905/a1/summary.json`;
receipt sibling `a1_admission.json`. Log `/home/wu/.agent-tasks/dish_ground_source_a02_seed11_a1/task.log`.
Local originals at
`C:/Projects/HMASD-worktrees/cm-n3-dish-funnel-a01-20260904/temp/directions/degraded_incumbent_shadow_handover/exp/ground_source_point_a02_20260905/`:
`a1/summary.json`, `a1/task.log`, `a1_admission.json`.
Tracked raw copy beside this record: `DISH_GROUND_SOURCE_POINT_A02_SUMMARY_20260905.json`,
4509bytes, SHA256 `2b63587a58d13c243e2139226ed420b681adfc9e14247d6312b04d40eb4eda07`.

## Actual point and separately derived quantities

Original coordinate `DISH/RBHR/R06/EVALUATION_COORDINATE/0/CLAIM/TARGET_VISUAL_MASK/K8/0`;
seed11, block0, slot0, speed4, owner0, reflection1, mask_enabled1, test_mode0,
initialized1, terminal0. Native/action tick0. Native boundary exactly equals expected
boundary. Source native xy=(-168,-120), declared source z=0; UAV declared z=90.

| Quantity | U0 owner | U1 standby |
|---|---:|---:|
| Native UAV xy | (-88,-240) | (-248,0) |
| Native camera_present | 0 | 0 |
| Native G_TO_U margin dB | -9.303396681040274 | -10.285571482315484 |
| Send-margin eligibility >=6 | false | false |
| Derived source-hop distance | 170 | 170 |
| Derived radio j1 / reverse camera j127 xyz | (-167.375,-120.9375,0.703125) | (-168.625,-119.0625,0.703125) |
| Derived terrain height | 0.8467255467868863 | 0.7901657174358243 |
| Derived terrain+8 | 8.846725546786887 | 8.790165717435825 |
| Derived terrain+5 | 5.846725546786886 | 5.7901657174358245 |
| Both strict-clearance conditions pass | false | false |

Data-only arithmetic checks independently recomputed the declared reflected terrain and
clearance sums from original JSON within1e-12, sample z=90/128, margin eligibility and
boundary identity. No native invocation or RNG was used for collection. Native flags/margins
are actual outputs; ray sample values are derived, not exported native ray flags.
Eligibility is not a received packet because no completion/next tick occurs.

Summary reports `A02-ENDPOINT-CLEARANCE-WITNESS`, boundary_matches=true. This reports
the implemented card predicate for DM intake; it neither establishes universal zero
radio reception nor authorizes changing heights, clearance, physics or B01 validity.

## Exposure, admission, timing and publication

One prepared native point, zero completed native ticks. Models/policies/optimizers
initialized0; training transitions/learner updates/optimizer steps0. Parameter displacement
null/not applicable. Source inspection and the single native-call path support these counts;
the synthetic smoke never invoked this point.

Supervisor started2026-09-05T17:53:33+08:00, exited0 at17:53:34+08:00, actual wall1s.
Adjacent external admission assessed2026-09-05T09:53:33.113076Z, physical/effective each
12932448256bytes, both floor flags and passed=true, minimum4294967296, source/proc/meminfo.
Receipt file mtime1788602013.1074119 precedes summary mtime1788602014.0084949. The accepted
shell command's && supplies admission-before-run ordering; file times are ancillary only.
No duplicate internal admission is added.

Runner measured wall0.0061659040075028315s (point/readout/Git/RSS, before serialization),
seconds_per_point same; supervisor wall includes process startup, admission and publication.
Both measured durations below60s; prospective cost15s. Peak RSS342839296bytes,
resources_unmeasured=false. Complete summary publication observed. Process exit, wall and
RSS are technical facts, not a performance claim.

No technical discrepancy or missing required measurement was observed. This point does not
observe future source receipt, a whole-path margin distribution, altered-host behavior or
a remedy. Source/spec mapping remains that implementation matches the inherited host law.
