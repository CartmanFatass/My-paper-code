# FSD E4 renewal/reference census — result evidence

**COMPLETE: 3/3 laws, 288/288 unique open-loop candidate rows, no learner exposure.**
Class A/RECON; claim ceiling is the numerical native timing opportunity on the frozen finite
K2 renewal host. This is one three-law census, not three learner studies or C consumption.
Card `FSD_E4_CENSUS_SCIENCE_CARD_20260905.md` was frozen005643177 before source/calibration;
the actual-node cost record4ce1e416e was pushed before the first formal invocation.
Source `bc3eaeecf5f97e630a886028db0053ba2d08d56f`; final CM acceptance591a193d2.

## Population, strongest null and raw observations

All summaries record N6/K2/Z4/two regions/H400/Delta.4, mean20, lognormal shape1, fixed
k={1,2,5,20,40}, renewal, rho0/no probe/no E5 coupling, argmax. Age0 is the full initial
dwell. Membership and region/zone ownership are fixed. A regional event invalidates leases;
native renewal pays one zero-service step without resetting dwell age. The original float64 DP
scores400 primitive steps with399 transitions. No law/phase/grid/config changed after timing.

Public greedy is the strongest same-information null: at K2 the flag and lagged cue identify
the only possible new latent. Its reference value reuses switching by construction, so this
equality is an observed source-consistency fact, not independent evidence of learning.
Fixed clocks are latent-aware references, not trained D0; the open-loop grid is not D8.

| Law | J_switch = J_greedy | Best k | J_best_fixed_k | J_open_best | m | m_dur | Best fixed minus k20 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 0.381000000000 | 20 | 0.381000000000 | 0.190500000000 | 0.190500000000 | 0 | 0 |
| geometric | 0.380050000000 | 5 | 0.282950500000 | 0.141475250000 | 0.238574750000 | 0.097099500000 | 0.045344868963 |
| rounded-lognormal | 0.379674861371 | 5 | 0.281449725138 | 0.140724862569 | 0.238949998802 | 0.098225136232 | 0.045614655901 |

Here m=J_switch-J_open_best, m_dur=J_switch-J_best_fixed_k. Rounded display does not replace
full-precision raw JSON. Complete five-point clock curve:

| k | deterministic | geometric | rounded-lognormal |
| ---: | ---: | ---: | ---: |
| 1 | 0.001000000000 | 0.001000000000 | 0.001000000000 |
| 2 | 0.201000000000 | 0.191000000000 | 0.190823536565 |
| 5 | 0.321000000000 | 0.282950500000 | 0.281449725138 |
| 20 | 0.381000000000 | 0.237605631037 | 0.235835069237 |
| 40 | 0.191000000000 | 0.165297568687 | 0.170659928606 |

The full96 rows per law are preserved in `e4_census_20260905/census_<law>.json` under
`open_candidates`. DM independently counted96 unique (four-zone map, period) pairs per law,
with16 maps at each of the six periods and all values finite. In this observed enumeration,
all16 maps have the same value within a period; these compressed values are for readability,
not a replacement for the complete rows:

| Open-loop period | deterministic | geometric | rounded-lognormal |
| --- | ---: | ---: | ---: |
| 1 | 0.000500000000 | 0.000500000000 | 0.000500000000 |
| 2 | 0.100500000000 | 0.095500000000 | 0.095411768283 |
| 5 | 0.160500000000 | 0.141475250000 | 0.140724862569 |
| 20 | 0.190500000000 | 0.118802815518 | 0.117917534619 |
| 40 | 0.095500000000 | 0.082648784343 | 0.085329964303 |
| never-renew | 0.010000000000 | 0.009999999988 | 0.009984430156 |

Stored best map is(0,0,0,0), period20 for deterministic and5 for each random law, preserving
the existing first-max tie behavior. This does not claim that the selected map alone is better.

## Law facts and numerical limits

| Law | Numerical mean | Variance | DP age cap | Hazard entries |
| --- | ---: | ---: | ---: | ---: |
| deterministic | 20 | 0 | 19 | 20 |
| geometric | 20 | 380 | 1 | 2 |
| rounded-lognormal | 19.999999999999996 | 687.3086223944757 | 399 | 400 |

Complete hazards are in each raw summary. Deterministic hazards are0 until age19 then1;
geometric hazards are.05; rounded-lognormal's observed table ranges from.009324767608598131
to.06678747712627299. Its log location is2.495691739886703, moment support cap98296,
first moment19.999999999999996, second moment1087.3086223944756, computed mass1.0 and
`1-computed_mass=0.0`. The runner explicitly reuses private `_moments()` with existing finite
calibration. The finite moment cap and H400 age cap are different quantities. Floating mass
rounding to1 does not prove a zero infinite-support tail or an exact infinite-support mean.

All stored reference discrepancies are exactly0: public greedy minus switching, maximum raw
candidate minus stored open maximum, both gap identities, and deterministic switching minus
k20. DM recomputed counts, candidate maxima and gap arithmetic from existing summaries.
Mean discrepancies are0/0/-3.552713678800501e-15; hazards, variances and masses satisfy the
card's numerical consistency ranges. These checks do not independently certify the DP or
roundoff. Reporting tolerance1e-10 is not a rigorous error enclosure; no confidence interval,
Monte Carlo seed population or variance-only causal intervention is implied.

## Frozen rule applied verbatim, in order

> 1. A cap/failed exit, nonfinite quantity, missing required output/candidate count, or unexplained
>    calibration/reference inconsistency makes that law **INCOMPLETE**, with its exact missing
>    fact; do not assign scientific polarity or salvage partial output.
> 2. Otherwise the law is **COMPLETE**. For each reported gap g, `g>tau` is positive at the
>    declared numerical resolution, `abs(g)<=tau` is unresolved at that resolution, and
>    `g<-tau` is an opposite ordering of these numerical references. No branch is a learning claim.
> 3. The object is complete only when all three law reports are complete. Stop after this census;
>    no result branch selects a second object or changes parameters.

Rule1 does not apply to any law: all three exit0, full output, finite values and consistent
records are observed. Rule2 gives COMPLETE for all three; m is positive for all, while m_dur
and best-fixed-minus-k20 are unresolved for deterministic and positive for the two random
laws. No opposite ordering occurs. Rule3 is satisfied at3/3; the selected object stops here.
There is no valid scientific failure or quarantined census attempt in this object.

## Source, admission, timing and evidence locations

Actual CPU node is configured wsl_4070 via hmasd-wsl-node. Exact detached checkout:
`/home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf`; Python
`/home/wu/.venvs/hmasd/bin/python`. Same bash-lc/default thread environment as calibration,
no configuration or core changes. Each accepted agent-task command used fresh actual-node
admission immediately joined by&& to the timeout300s runner command; CM's technical record
contains all literal commands. Runtime roots remain
`<checkout>/temp/directions/flexible_skill_duration/exp/e4_census_20260905/census_<law>/`.

| Law | Actual task | Receipt UTC | Physical = effective available bytes | Process wall s | Peak RSS KiB |
| --- | --- | --- | ---: | ---: | ---: |
| deterministic | fsd_e4_census_deterministic_bc3eaeecf_01 | 2026-09-05T16:42:02.299039Z | 15423946752 | 0.41 | 35668 |
| geometric | fsd_e4_census_geometric_bc3eaeecf_01 | 2026-09-05T16:42:30.687113Z | 15423528960 | 0.47 | 35244 |
| rounded-lognormal | fsd_e4_census_lognormal_bc3eaeecf_01 | 2026-09-05T16:43:03.165721Z | 15424434176 | 1.47 | 47500 |

All memory readings exceed4294967296 bytes; the observed range is approximately14.36 GiB,
not15.42 GiB. All process walls are below both their measured heuristic projections and their
own300s cap. External time reports process wall to.01s and RSS in KiB. Formal process wall
sum2.35s, calibration sum.74s, total calibration+formal3.09s per one complete census.
The initial failed setup test used.37s and successful test02 used.35s, giving an observed
eight accepted verification/calibration/formal process window of3.81s at display resolution.
This excludes SSH/scheduler latency, editing/review/agent usage, the short standalone mkdir
reproduction (wall unmeasured), and previous direction history. It is not total direction cost
or evidence of cross-host speed. Runner module-before-output walls are
.38466937899647746/.45196926199423615/1.4448842269921442s; output times are in raw logs.

The runner's raw resource field marks internally unmeasured peak RSS; external process time
does measure it and is retained separately, with no raw flag rewritten. Scratch telemetry
is unmeasured; this is a non-resource claim and remains valid. Supervisor rounded durations
0/1/1s and later `uptime_seconds` status ages are not substitute process-wall measurements.

Durable raw copies in `e4_census_20260905/`: each `census_<law>.json`,
`census_<law>_receipt.json`, `census_<law>_process_time.txt`,
`census_<law>_task_status.json`, `census_<law>_task_log.txt`. The latter is the unchanged content
of original task.log under a descriptive filename. Calibration summaries/receipts/process
times and both test receipts/process times are also retained. Original remote and CM local
outputs are left in place. Complete stdout logs preserve terminal0, immediate admission and
publication timing, and CM retains the original failed-test log at its supervisor path.

## Engineering acceptance, exposure and deviations

Source91 added lines,0 deleted,76 orchestration lines, O/(A+D)=83.52%; tests174 lines,
documents separately. The prospectively declared <=100-line existing-computation reuse
exception applies; independent reviewer accepted necessity, all affected science/observations/
consumers/publication and named runtime limitations. No section4 machinery or core change.
13 focused tests passed, including end-to-end toy publication and arithmetic/rule checks.
Formal H400 publication then completed for all laws; no open missing-publication-path item.

The first accepted test failed before test bodies because the fresh remote pytest basetemp
parent did not exist. The implementer reproduced the exact mkdir failure over the recorded
path/interpreter; CM created that parent and test02 passed at unchanged source with a fresh
receipt. It is a reproduced setup failure, not scientific evidence or an invalid census.
No code repair, numerical retune, failed result invocation or new platform refusal occurred.

Machine-generated exposure per raw summary: learner episodes0, learner transitions0,
optimizer updates0, checkpoint selection0, seed0 inactive. No model/optimizer/checkpoint exists,
so parameter displacement and initialization-scale ratio are not applicable. Formal108 plus
calibration18 DP calls are computational work, not126 learner runs. No learner-effect MEI applies.

## Bounded scientific reading

Deterministic full-age0 dwell aligns with k20, leaving no resolved reactive-over-best-clock
gap there. The two random laws have positive finite gaps of about.0971/.0982; k20 alone is
weaker than their best grid clock by about.0453/.0456. Thus a future claim based only on k20
would mix the timing opportunity with a weaker-clock comparison. Public greedy explains the
entire switching opportunity on every law; the result provides no D2/D8 learning advantage.
There is still no tuned generic same-information headroom record on this renewal host.

DM phase/equality predictions match; they were source-derived consistency expectations.
No magnitude or learned-method ordering was predicted for random laws. Owner prediction was
not taken(unattended). E3's18/18 valid bounded H0, small-seed2 contrary evidence and unresolved
policy-gap/optimizer/seed/team-path explanations remain unchanged. No successor is selected.
