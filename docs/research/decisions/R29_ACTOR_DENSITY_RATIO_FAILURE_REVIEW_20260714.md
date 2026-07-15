# R29 Actor-Density-Ratio Failure Review

Date: 2026-07-14

Status: completed from the registered pair and archived GPT-5.6 Pro response.
No new rollout, threshold change, metric redesign, or reward retuning was used.

## Decision

Retire the R29 same-action actor-density-ratio family as online intrinsic
reward. Keep R29-G0/T10 as conditional-capacity diagnostics only. Do not run
the remaining seeds or create prior/window/scale/clip variants.

The single-seed result remains `PRELIMINARY_FAIL`, not a cross-seed efficacy
claim. Retirement follows the registered branch logic: the implementation was
valid, the target and R26-transfer gates failed, and task reward degraded
`31.56%` against a per-seed maximum of `10%`.

## Cross-Round Evidence Matrix

| Gate | Question | Accepted result | Constraint carried forward |
| --- | --- | --- | --- |
| R27-G2 | Can persistent forced skills control action trajectories and a local effect? | `PASS_BEHAVIOR_EFFECT` under deterministic branch execution. | Conditional capacity exists; natural stochastic use and reward usefulness remain open. |
| R28 transport | Does the forced deterministic scorer remain supported under policy-matched stochastic execution? | `FAIL_STOCHASTIC_SUPPORT_TRANSPORT`, OOD `0.823242`. | A forced deterministic support envelope cannot be imported into natural PPO reward. |
| R29-G0 | Is there a support-native same-state actor differentiation statistic? | Three checkpoints passed; inactive control was numerical zero. | Actor-local conditional information exists, but usefulness is not established. |
| R29-T10 | Does recurrent terminal-block density-ratio reward improve natural differentiation safely? | Implementation valid; score and R26 transfer failed; reward arm task return degraded `31.56%`. | Actor-local identifiability is not a sufficient online reward target. |
| GPT-5.6 Pro result review | Promote, modify, or retire? | `RETIRE`. | Do not rescue the family with prior, window, aggregation, coefficient, normalization, clip, or extra seeds. |

## Baseline Matrix

| Gate | Baseline level | Comparator |
| --- | --- | --- |
| R27-G2 | L1 causal diagnostic | Persistent hold against pulse, natural reference, inactive-FiLM, fake-label, and replay nulls. |
| R28 transport | L1 matched-domain diagnostic | Same checkpoint, prefix, forced label, noise, features, and scorer; deterministic versus stochastic environment execution. |
| R29-G0 | L1 diagnostic nulls | Active actor against cyclic label sham and inactive-FiLM control. |
| R29-T10 | L2 mechanism-matched control | Same source, seed, exposure, scorer, and PPO contract; `probe_only` versus `real_reward`. |

## Failure Separation

Verified mechanism evidence:

- the recurrent actor can express persistent skill-conditioned action and local
  effect under forced holds;
- R29 measures a real support-native state-conditional actor statistic;
- R29-T10 changed action-mean separation, not action variance;
- reward injection did not collapse skill usage or violate its scale guard.

Instrumentation/data quality:

- the anchored source likelihood is exact by construction, not an independent
  replay validation;
- unanchored CUDA recurrent-source drift is nonzero but balanced across arms and
  does not explain the adverse between-arm result;
- no evidence supports an `INVALID` repair rerun.

Optimization/capacity:

- terminal-block scores were heavily saturated, but both arms saturated
  similarly;
- changing coefficient, clipping, normalization, prior, or window would only
  alter pressure on the same actor-local target and would not add realized
  environmental-effect semantics.

Task evidence:

- one paired seed does not establish a population effect;
- it is nevertheless sufficient to fail the preregistered per-seed safety
  contract and block unchanged promotion.

Reusable negative conclusion:

```text
same-state skill-conditioned action-mean separation
does not imply
stable natural process differentiation or task-safe behavior
```

## Single Next Causal Edge

The nearest untested edge is:

```text
natural on-policy prefix
-> persistent skill intervention under policy-matched stochastic execution
-> task-generic realized environment-effect separation
```

This is a reward-off effect-existence question, not a new intrinsic reward.
R27 established the deterministic forced version; R28 showed stochastic
execution changes trajectory support; R29 showed actor-local separation alone
is insufficient. The next target must therefore couple skill-conditioned action
to realized environmental consequences without using environment reward,
communication fields, another semantic classifier, or an actor-only density
ratio.

Before implementation, GPT-5.6 Pro is asked to define exactly one mathematical
target and the smallest falsifiable diagnostic for this edge. A failure must
retire or revise that target before any reward comparator.

## Sources

- `docs/external-review/gpt5_6_pro/20260714_r29_t10_result/RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260714_r29_t10_result/DISPOSITION.md`
- `memory/ExpRecord.md`
- `docs/research/decisions/R26_R27_R28_FAILURE_REVIEW_20260713.md`
