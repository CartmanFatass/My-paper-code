# FSD E2 interruption-cost sweep — result evidence

Status: accepted evidence for DM intake on 2026-09-04

Evidence class: **B — EXPLORE**

Claim ceiling: a preliminary mechanism reading on the declared homogeneous relay-corridor setup;
no stable superiority, transfer, or direction-level closure claim

Frozen card: `docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_20260903.md`

Historical implementation narrative:
`docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_RESULT_20260903.md`

Study root:
`temp/directions/flexible_skill_duration/exp/E2_20260903/`

## Result first

The frozen section 5 rule returns **NEITHER**.

- Mechanism A is not supported: no finite `c` satisfies the return condition in both seeds, and
  event alignment is below `0.5` at every `c` in both seeds.
- Mechanism B is not supported: `c = 0.25` satisfies the return condition in seed 1, so the rule's
  condition that no `c` reaches the bar in either seed is false.
- Mean completed agent-segment length is non-decreasing in `c` in both seeds. The threshold controls
  persistence, but the observed boundaries are not predominantly event-aligned.
- D0's learned best arm is `k = 20` in both seeds, agreeing with the exact reference best `k`.

This is a valid B result. It narrows the homogeneous-host reading of D2; it does not retire D2,
the broader flexible-duration question, or the direction.

## Question, treatment, comparator, and non-goals

Question: on the homogeneous relay corridor at
`(lambda_1, lambda_2) = (0.02, 0.02)`, does policy-gap interruption D2 at a finite `c` reach the
best learned fixed-`k` D0 arm, with interruptions behaving as an event-driven boundary?

- Treatment: D2 at `c in {0.25, 0.5, 1.0, 2.0}`, `k_max = k_Z = 40`.
- Same-information comparator: D0 with `c = c_Z = infinity` and fixed
  `k in {1, 2, 5, 20, 40}`. Budget decisions left evidence for `k in {2, 5, 20, 40}` in seed 1
  and `k in {5, 20, 40}` in seed 2.
- Host: `N = 6`, `K = 2`, `Z = 4`, `H = 400`, `Delta = 0.4`, Bernoulli hazards, no churn,
  no probe, and coupling disabled.
- Budget per completed run: 20 rollouts, 16 lanes, 128,000 transitions, 320 training episodes,
  and four deterministic matched evaluations.
- Non-goals: heterogeneous hazards, random event durations, UAV transfer, team-asynchrony,
  any `K != 2`, a stable seed-count claim, or a C-class conclusion.

## Predictions on record

The predictions were written before launch.

- Owner: mechanism A; some finite `c` reaches or exceeds the best fixed `k` and interruptions are
  event-driven.
- Reviewer: mechanism A; best `c` lies in `[0.5, 1.0]` and event alignment there exceeds `0.5`.

Direct scoring on this setup:

- The owner's raw return prediction was not observed: the best D2 return is below the best D0
  return in each seed. Under the frozen range-tolerant rule, `c = 0.25` passes only seed 1.
- Both numerical reviewer clauses are false: the seed-mean best `c` is `0.25`, while the best
  `c` differs by seed (`0.25`, `2.0`), and alignment never exceeds `0.124685`.

## Evidence and validity receipts

### Launch and scientific surface

- Launch commit recorded by every manifest: `92243f413`.
- The valid runs record clean code SHAs between `92243f413` and `8329f4e4a` as queue and document
  decisions were committed during the detached study.
- Direct `git diff` inspection from `92243f413` to `8329f4e4a` finds no change to `config_1.py`,
  `hmasd/`, `envs/relay_corridor/`, or `scripts/run_flexible_skill_duration_e2.py`. The scientific
  execution surface therefore stayed byte-identical; the queue and result narrative changed.
- Each completed run has `manifest.json`, `preflight.json`, 20 rows in each of `metrics.jsonl`,
  `interruptions.jsonl`, and `gaps.jsonl`, four rows in `eval.jsonl`, and
  `checkpoint_final.pt`.

### Counts and resource receipts

There are 15 valid completed runs:

- 1,920,000 transitions and 4,800 training episodes;
- 53,760 deterministic matched evaluation episodes;
- 25,125 coordinator, 450,000 discoverer-actor, 450,000 discoverer-critic,
  4,500 team-discriminator, and 18,000 individual-discriminator optimizer steps;
- all 15 preflight receipts pass both the physical and effective 4 GiB floors; measured effective
  availability ranges from 8.713 to 13.753 GiB;
- every network in every completed run has a finite, positive displacement ratio against its
  initialization after rollout 1 and after rollout 20. The minimum across networks ranges from
  `0.00968` to `0.01343` after rollout 1 and from `0.03191` to `0.05293` after rollout 20.

The two `d0_k1` processes were deliberately stopped at 8/20 rollouts by the recorded budget
decision. Both directories carry `QUARANTINED`, neither has `summary.json`, and no value from either
is used here. `d0_k2` seed 2 was dropped before launch. These three absences have no technical or
scientific polarity.

### Per-run final observations

`R` is the final 2,048-episode evaluation mean; `SE` is its episode standard error; `align` is the
frozen two-step `{t_flip, t_flip + 1}` alignment fraction over all sampled positions; `seg` is the
final mean completed agent-segment length.

| arm | seed | `R` | `SE` | `align` | `seg` | run wall min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| D0 `k=2` | 1 | 0.181548421 | 0.000110889 | 0.038125 | 2.000000 | 157.31 |
| D0 `k=5` | 1 | 0.287241292 | 0.000201669 | 0.039062 | 5.000000 | 96.79 |
| D0 `k=5` | 2 | 0.287209880 | 0.000162159 | 0.042578 | 5.000000 | 92.88 |
| D0 `k=20` | 1 | 0.301320475 | 0.000400109 | 0.034375 | 20.000000 | 63.37 |
| D0 `k=20` | 2 | 0.304232422 | 0.000417492 | 0.031250 | 20.000000 | 62.97 |
| D0 `k=40` | 1 | 0.261021159 | 0.000680077 | 0.034375 | 40.000000 | 55.93 |
| D0 `k=40` | 2 | 0.175042155 | 0.000595981 | 0.037500 | 40.000000 | 55.22 |
| D2 `c=0.25` | 1 | 0.282904867 | 0.000578977 | 0.124684 | 12.121212 | 67.53 |
| D2 `c=0.25` | 2 | 0.239658285 | 0.000664227 | 0.060801 | 14.501511 | 59.02 |
| D2 `c=0.5` | 1 | 0.263682861 | 0.000660303 | 0.036540 | 17.761332 | 54.28 |
| D2 `c=0.5` | 2 | 0.238391764 | 0.000650609 | 0.053737 | 18.759160 | 55.04 |
| D2 `c=1.0` | 1 | 0.230409017 | 0.000744038 | 0.031429 | 36.571429 | 56.47 |
| D2 `c=1.0` | 2 | 0.220334961 | 0.000689292 | 0.051802 | 28.828829 | 57.71 |
| D2 `c=2.0` | 1 | 0.247683838 | 0.000631572 | 0.034375 | 40.000000 | 50.97 |
| D2 `c=2.0` | 2 | 0.253736003 | 0.000679129 | 0.037500 | 40.000000 | 45.84 |

## Frozen rule, applied verbatim

The card defines `R_best0` as the best D0 final return per seed, `R_c` as the D2 final return at
`c`, and `s` as the larger of the across-seed ranges of those two series. It then says:

1. Mechanism A requires some `c` for which `R_c >= R_best0 - s` in both seeds, alignment exceeds
   `0.5` at that `c`, and mean segment length is non-decreasing over the four `c` values in both
   seeds.
2. Mechanism B requires that no `c` reaches the return bar in either seed and that alignment is
   below `0.5` at every finite `c`.
3. Anything else is `neither`.

Direct recomputation from the 15 run summaries gives `R_best0 = 0.301320475` and `0.304232422`,
both at `k = 20`; their across-seed range is `0.002911947`.

| `c` | `R_c` seed 1 | `R_c` seed 2 | `s` | return pass seed 1/2 | align seed 1/2 | seg seed 1/2 |
| ---: | ---: | ---: | ---: | --- | --- | --- |
| 0.25 | 0.282904867 | 0.239658285 | 0.043246582 | yes / no | 0.124684 / 0.060801 | 12.121212 / 14.501511 |
| 0.5 | 0.263682861 | 0.238391764 | 0.025291097 | no / no | 0.036540 / 0.053737 | 17.761332 / 18.759160 |
| 1.0 | 0.230409017 | 0.220334961 | 0.010074056 | no / no | 0.031429 / 0.051802 | 36.571429 / 28.828829 |
| 2.0 | 0.247683838 | 0.253736003 | 0.006052165 | no / no | 0.034375 / 0.037500 | 40.000000 / 40.000000 |

The segment sequences are monotone in both seeds. There is no `c` with a return pass in both seeds
and no alignment value above `0.5`. Because `c = 0.25` passes in one seed, the B branch also fails.
The rule therefore maps the observation to **NEITHER**.

D0 sanity also passes: the learned ordering starts `20, 5` in both seeds, matching the top of the
exact reference ordering `20, 5, 40, 2, 1`.

## Deviations and engineering conformance

| item | disposition |
| --- | --- |
| Final/intermediate evaluation reduced from 4,096 each to 2,048/512 | Outcome-blind pre-launch decision; matched tape prefixes, schedule, evaluator, and final rule are unchanged. Evaluation SE is much smaller than across-seed variation. |
| Frozen 8 h whole-study cap | Breached: first valid run started 2026-09-03 14:08:55 PDT and the last ended 2026-09-04 00:23:05 PDT, an elapsed 10.236 h (2.236 h, 28.0%, over cap). The re-projections and reversible arm drops are recorded in review XII.5–XII.7. |
| D0 `k=1` pair and `k=2` seed 2 | `k=1` partials quarantined without interpretation; `k=2` seed 2 never launched. The D0 maximum uses different available sets by seed, but both select `k=20`. |
| Four-thread restoration, config-class rebinding, and instance-local measurement wrappers | Recorded implementation facts; no arm-specific numerical or RNG change was found. |
| Ordered detached queue with JSON state and `wait_for_pids` probe | Two engineering-scope section 4 items added by the historical executing instruction. They were declared retrospectively because the scope specification post-dated the launch branch. No such machinery is requested for the successor card. |
| Per-arm cost miss | The study originally projected from `k=40`; actual D0 cost follows `M = num_envs * rollout_length / k`. The accepted fit over retained arms is about `64.6 s + 0.769 s * coordinator optimizer steps` per rollout. Successor sweeps must project every arm before launch. |
| Resource telemetry | Measured for all valid runs; no `resources_unmeasured` label is needed. |

The deviations lower precision and leave an asymmetric D0 grid, but none omits a quantity read by
the rule, changes treatment/comparator semantics, changes RNG matching, or creates a learner-side
instrumentation failure. The 15 completed runs are valid B observations.

## Bounded scientific reading

Direct observation:

- D2's threshold strongly orders mean segment duration in both seeds.
- No D2 arm equals the learned best D0 arm in raw return; the range-tolerant bar is crossed only by
  `c = 0.25`, only in seed 1.
- Interruptions are not predominantly event-aligned under the frozen definition. Even the largest
  value, `0.124684`, is far below `0.5`.
- The seed-mean best `c` is `0.25`, but the per-seed best values are `0.25` and `2.0`; the treatment
  ranking is not stable.

Inference bounded by the card:

- The policy gap is a usable persistence control but is not supported here as an event-driven
  renewal signal.
- Homogeneous hazards may be the wrong population for D2 to earn a return advantage over a tuned
  fixed clock. The surviving discriminator is the registered heterogeneous-hazard host, where one
  global fixed `k` must compromise across regions.
- A simpler live explanation is seed-dependent optimization plus threshold-driven chattering that
  is mostly unrelated to events. Evaluation noise is not a strong explanation because episode SEs
  are one to two orders of magnitude smaller than the cross-seed and cross-arm differences.

The claim ceiling remains B — EXPLORE. The smallest accepted update is: **D2 controls duration on
this host, but E2 does not support its event-aligned mechanism or a two-seed return match to the best
fixed clock.**
