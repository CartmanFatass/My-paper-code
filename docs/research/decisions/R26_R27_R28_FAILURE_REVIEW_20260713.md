# R26-R28 Natural-Expression Failure Review

Date: 2026-07-13

Status: completed from existing evidence. This review added no rollout,
training, metric redesign, scorer refit, or threshold change.

## Decision

The frozen R28-G1 package is blocked before formal launch as
`BLOCKED_SUPPORT_OOD`. Two exact one-update local engineering smokes reached the
real PPO update path, but the common support guard disabled R28 reward before
scoring or injection. This is not a formal R28-G1 reward-efficacy `FAIL`: the
registered three-arm scientific experiment never ran and the smoke applied zero
R28 reward.

The reusable conclusion is narrower and decisive: the support envelope learned
from R27 forced, deterministic branches does not transport to the current
natural on-policy PPO trajectory domain. Do not widen the envelope, refit the
scorer, alter its features or variance floor, relax the OOD threshold, or run
the formal G1 package hoping that later updates rescue an unreachable reward.

## Cross-Round Evidence Matrix

| Gate | Promotion stage | Question | Accepted result | Constraint carried forward |
| --- | --- | --- | --- | --- |
| R26-G1a | 1: reward-off observation | Do naturally assigned skills leave held-out behavior-window signal beyond matched priors? | Arm0 update25/update30 `MIXED`, final `FAIL`, family `FAIL`; no checkpoint passed. | Natural expression was not established in the tested windows. This cannot be strengthened into "the actor has no immediate skill path." |
| R27-G1 | 0: wiring/capacity | Does the frozen actor have immediate `z_i`-conditioned action-distribution capacity, and is it lost by the GRU? | `STATIC_USED_OBSERVATIONAL_MISS`; static and synthetic controls passed 3/3, recurrent washout was not supported. | Do not repair actor/FiLM/GRU merely because R26 was negative. Persistence still required a causal test. |
| R27-G2 | 2: reward-off intervention | Under a forced hold, do labels cause persistent action processes and a local effect? | `PASS_BEHAVIOR_EFFECT`; A/B1/B2/B3/C passed at all three checkpoints. | Accept forced persistent executor capacity only. Natural use, reward usefulness, cooperation, and task gain remain unproved. |
| R28-G0 | diagnostic calibration before stage 3 | Can forced-branch terminal action features beat context/pre/sham nulls within their calibrated domain? | Accepted `PASS_TARGET_NULLS`; final scorer frozen. | The scorer is valid only under its frozen target, null, and support contract. G0 did not establish natural-domain transport. |
| R28-G1 local smoke | engineering integration, not a scientific stage | Can the exact update/checkpoint/reward guard path execute on a natural PPO rollout? | Two runs completed one real PPO update. OOD was `0.950617` and `0.9375`; both fired the support kill and applied zero R28 reward. | Formal G1 cannot start under the frozen contract. The result does not estimate reward efficacy. |
| R28-G1 formal | 3: small clipped reward | Does real reward beat matched probe-only and sham-reward continuations? | Not executed; no scientific outcome. | Do not label the unrun reward comparison PASS or FAIL. Retire this launch package because its precondition is unreachable. |

The combined state is
`FORCED_CAUSAL_CAPACITY_WITH_NATURAL_OBSERVATIONAL_NEGATIVE_AND_TRANSPORT_GAP`.

## Baseline Matrix

Baseline hierarchy and promotion stage are separate axes.

| Gate | Baseline hierarchy | Exact role |
| --- | --- | --- |
| R26-G1a | L1 diagnostic nulls | Full behavior model against prior/pre/context and matched agent, duration, and agent-duration controls. |
| R27-G1 | L1 diagnostic/wiring controls | Active versus neutral FiLM, zero-hidden versus rollout-hidden, and synthetic active versus fake-label sham. |
| R27-G2 | L1 diagnostic causal nulls | Matched forced hold, pulse, reference/same-label, inactive, fake-label, and exact-replay branches under frozen inference. |
| R28-G0 | L1 diagnostic nulls | `q_full` against capacity-matched context/pre heads, sham derangement, and hold-minus-pulse persistence null. |
| R28-G1 formal | L2 mechanism-matched HA-CTSE control | Planned `probe_only`, `sham_reward`, and `real_reward` arms differed only in the injected scalar; this comparison was never opened. |
| R25 arm0/arm2 and HMASD | frozen source/context and L4 standing reference | Reference-only; neither can rescue a failed lower-level natural-expression or support gate, and none is rerun here. |

## Failure Review

### Verified mechanism evidence

- The strict-HMASD low actor has an immediate `z_i`-conditioned action path.
- Forced label holds produce persistent action separation and a local effect
  through native H40.
- The frozen G0 heads and nulls separate labels inside the forced-branch domain.
- Both local smokes executed a genuine low-level PPO update. The first
  checkpoint diff verified changed low actor/critic tensors while preserving
  the frozen source actor-base copy; the second reproduced the same guard path.

### Instrumentation and data quality

No feature-construction defect was found:

- G0 and G1 call the same `late_action_features` implementation on `[10, 4]`
  windows in action-major `mean, std, slope` order.
- Both use `tanh(distribution.mean)` as deterministic-action evidence.
- Duration indices `0..3` map consistently to 10/20/30/40-step segments.
- Both use `sum((feature - mean)^2 / variance)` and the same frozen arrays;
  the added diagnostics are the exact per-feature absolute z residuals.
- Source checkpoint, label order, recurrent-forward capture, and support lookup
  were consistent. There is no basis for an `INVALID_MAPPING` repair rerun.

The two smokes reproduced the failure independently. In the second run, 5 of
80 structurally eligible rows were in support, the mean and p95
distance-to-threshold ratios were `94.9766` and `301.6859`, and the dominant
absolute z residuals were the four temporal action standard deviations
(`12.64`, `13.18`, `14.43`, and `20.39`). Means were only `0.85-1.74` and
slopes `1.55-2.60`, which argues against a feature permutation.

### Optimization and capacity

The smoke proves optimizer integration, not reward learning. Because the guard
set every R28 reward to zero, it supplies no evidence about whether the target
would improve the policy, no coefficient evidence, and no reason to change
actor, critic, optimizer, PPO, GAE, or collector semantics.

### Confounds and incomparable evidence

- R27/G0 forced branches advanced the environment with deterministic actions;
  G1 PPO advanced it with sampled actions while retaining same-forward
  deterministic means only as scorer evidence. Sampled actions change later
  observations and recurrent state.
- R27/G0 held the non-focal roster and assignment state fixed. Natural G1
  trajectories allowed asynchronous assignments/renewals and joint dynamics.
- The single-env, single-seed local smokes are engineering evidence, not task,
  safety, cooperation, or multi-seed reward comparisons.

The concentration of the shift in temporal-standard-deviation features is
consistent with these trajectory-domain differences. It does not identify
which difference is dominant.

### Reusable negative conclusions

- Natural behavior differentiation remains unproved for the frozen R25 policy.
- A classifier/support contract calibrated on forced deterministic holds cannot
  be treated as a plug-in natural PPO reward contract.
- Another identical smoke, coefficient sweep, classifier target, support
  relaxation, or formal reward run is not authorized by this evidence.

## Single Next Causal Edge

The next edge is:

```text
R27-proven forced skill regime
-> support-compatible action process under on-policy state visitation
```

The only next research action is a reward-off, source-identical matched-domain
diagnostic that changes trajectory execution mode while holding the forced
skill intervention, checkpoint, prefix/reset, feature function, and frozen
support scorer fixed. It must first compare deterministic versus stochastic
environment execution. Only if the forced stochastic branch remains in support
may a later matched comparison change forced hold to natural
assignment/renewal.

Outcome routing:

- forced stochastic OOD -> record an action-mode/state-visitation transport
  failure; retire this scorer family from online reward use and review the
  observational target before any algorithm change;
- forced stochastic in support, natural stochastic OOD -> localize the next
  failure to natural assignment/renewal activation and inspect that high-level
  mechanism reward-off;
- both in support -> the current smoke and matched diagnostic disagree, so audit
  only the differing collector context before any reward;
- invalid/underpowered -> repair or add support under the unchanged diagnostic
  contract; do not promote to reward.

## Status Sources

Accepted R26/R27/R28 outcomes come from `memory/ExpRecord.md`,
`docs/archive/legacy-memory/EXPERIMENT_ARCHIVE.md`, and the frozen R27/R28 designs. The new
support-block decision uses only the two registered local smoke roots:

- `logs/r28_g1_engineering_smoke_20260713_212008/real_reward/`
- `logs/r28_g1_engineering_smoke_20260713_213746/real_reward/`
