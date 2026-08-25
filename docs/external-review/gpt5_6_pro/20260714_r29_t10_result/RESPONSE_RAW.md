## Route: **RETIRE**

Retire the R29 actor-density-ratio family **as an online intrinsic reward**. Do not promote the unchanged `probe_only`/`real_reward` pair to seeds `29032` and `29033`.

Keep the statistical label **PRELIMINARY_FAIL**: one paired training seed is not a final three-seed efficacy estimate. The retirement decision is instead based on the preregistered decision logic and the mechanism signature. Seed `29031` already violates a safety condition that was required **in every paired seed**—task-reward degradation is `31.56%` against a `10%` maximum—so the unchanged three-seed experiment can no longer achieve its declared PASS without relaxing the gate. Additional unchanged seeds could estimate how frequently the failure occurs, but they could not rescue the preregistered claim. ([prior decision contract](sandbox:/mnt/data/hmasd_r29_t10_result_review/prior_review/RESPONSE_RAW.md); [paired result](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/r29_t10_pair.json))

## Why this is a target failure rather than an invalid run

The implementation evidence does not support an `INVALID` or simple collapse interpretation.

| Check                                |                                               Result | Interpretation                                      |
| ------------------------------------ | ---------------------------------------------------: | --------------------------------------------------- |
| Declared intervention                | Manifests differ only in reward mode and output path | Mechanism-matched comparison                        |
| Actual-source likelihood             |            Anchored source error `0` by construction | Correct under the declared anchored contract        |
| Unanchored recurrent replay drift    |                    `7.246e-3` probe, `7.069e-3` real | Real numerical limitation, but balanced across arms |
| Skill entropy                        |                              `0.996980` late in real | No usage collapse                                   |
| Maximum R29 reward/environment ratio |                                           `0.044672` | Inside the `0.05` scale guard                       |
| Complete segments                    |                                About `49.8K` per arm | Adequate exposure and all skills represented        |

The zero likelihood-parity number should not be interpreted as independent confirmation that the batched CUDA recurrent replay exactly reproduces collection. In the supplied implementation, the source raw likelihood is reconstructed from stored PPO likelihood and then checked algebraically, so zero is expected. The independent numerical diagnostic is the reported recurrent-source error. That error is nearly identical in both arms and the source column actually used in the reward is anchored, so it does not explain the adverse between-arm result. ([reward implementation](sandbox:/mnt/data/hmasd_r29_t10_result_review/code/r29_action_information_reward.py); [probe manifest](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/probe_only/run_manifest.json); [real manifest](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/real_reward/run_manifest.json))

The observed causal pattern is:

[
\text{some additional same-state action-mean separation}
;\not\Rightarrow;
\text{natural process differentiation}
]

and, in this pair,

[
\text{additional R29 reward}
;\Rightarrow;
\text{worse natural-process and task evidence}.
]

### Exact target movement was weak and nonuniform

Over the final ten updates:

[
\Delta R_{\mathrm{T10}}
=======================

# R_{\mathrm{real}}-R_{\mathrm{probe}}

0.031265,
]

below the registered `0.05` effect threshold, with interval

[
[-0.005331,;0.064452].
]

Skill 3 moved in the wrong direction:

[
(\Delta_0,\Delta_1,\Delta_2,\Delta_3)
=====================================

(0.0408,;0.0866,;0.0297,;-0.0253).
]

The raw training files also show that the T10 aggregation entered a heavily saturated regime: the late clip fraction was approximately `0.632` in probe and `0.639` in real, and the real-arm 99th percentile was `1.386069`, essentially the theoretical (\log 4) ceiling. This is an optimization inefficiency, but it is not a persuasive basis for another R29 version. Both arms had almost the same saturation, and changing normalization, clipping, or coefficient would adjust pressure without supplying the missing behavioral-effect semantics. ([probe updates](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/probe_only/train_updates.csv); [real updates](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/real_reward/train_updates.csv))

### Natural process transfer reversed

The unchanged R26 analyzer gave:

[
\begin{array}{c|cc}
& \text{probe} & \text{real}\
\hline
\text{full-minus-prior} & 0.073063 & 0.014952\
\text{post-minus-pre} & 0.061090 & -0.002817\
\text{status} & \mathrm{PASS} & \mathrm{MIXED}
\end{array}
]

so the real-minus-probe full-minus-prior change was

[
-0.058112.
]

The component scores are especially diagnostic:

* action-only accuracy fell from `0.380282` to `0.312225`;
* behavior accuracy fell from `0.352113` to `0.273527`;
* full accuracy fell from `0.352993` to `0.303430`;
* effect-only accuracy fell from `0.278169` to `0.264732`;
* the context/prior accuracy slightly increased from `0.279930` to `0.288478`.

Thus the reward did not merely fail to improve the process read. In this seed, it shifted the policy away from naturally recoverable action and post-window behavior while leaving contextual label information intact.

As a diagnostic reaggregation—not a replacement preregistered gate—I grouped the supplied row-level R26 correctness records by the twelve common test resets. Eleven of twelve resets had a lower full-minus-prior gain in `real_reward`. Resampling those reset-level differences gives an approximate 95% interval of `[-0.084, -0.033]`. This does not establish cross-seed generality, but it shows that the reported negative difference is not caused by one anomalous reset. ([probe R26](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/probe_only/r26_g1_behavior.json); [real R26](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/real_reward/r26_g1_behavior.json))

### Task safety failed broadly within the supplied evaluation

Deterministic evaluation reward changed from

[
130.4519\rightarrow89.2782,
]

a `31.56%` relative degradation. Pairing the common episode indices, reward was lower in `17/20` episodes. A diagnostic bootstrap over those episode-index differences gives an approximate real-minus-probe reward interval of `[-61.5,-22.9]`, around a mean difference of `-41.17`.

Backhaul-connected step fraction fell from `0.7776` to `0.6823`, and zero-throughput step fraction increased from `0.2224` to `0.3177`. The latter remains just inside the registered `0.10` absolute guard, but the reward-safety guard fails decisively. ([probe evaluation](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/probe_only/eval_episodes.csv); [real evaluation](sandbox:/mnt/data/hmasd_r29_t10_result_review/results/real_reward/eval_episodes.csv))

## The causal defect

R29-T10 evaluates

[
R_g
===

## \log P_{z_g}!\left(A_T\mid X^{(z_g)}\right)

\log\left[
\frac14\sum_k
P_k!\left(A_T\mid X^{(z_g)}\right)
\right],
]

where (X^{(z_g)}) is the observation path generated by the actually executed skill. Counterfactual skills receive different recurrent states, but all of them process that same source-generated environmental observation path.

Therefore, even after temporal aggregation, the objective asks:

> Which code-conditioned actor would assign the most probability to this action block when every code is evaluated on the source skill’s realized observations?

It does **not** ask:

> Which code generates a differentiated and useful natural trajectory when that code controls the environment?

Formally, increasing an actor-local quantity resembling

[
I(Z;A_T\mid X)
]

does not imply an increase in marginal natural action information (I(Z;A_T)), persistent process information (I(Z;\tau)), or task utility. State-dependent action codes can point in different directions at every fixed state while cancelling across the natural state distribution or driving environmentally irrelevant controls.

The supplied result exhibits exactly that dissociation: counterfactual same-state mean KL is somewhat larger in the reward arm, while natural action-only identifiability, post-window behavior identifiability, process transfer, and task evaluation all move adversely.

This is not repaired by a different coefficient, clip, terminal window, prior, endpoint allocation, or additional seeds. Those changes can adjust the strength or variance of the same self-referential target, but cannot add the missing link from skill-conditioned action differences to realized behavioral consequences. Adding that link would constitute a different algorithmic target, not a minimal R29 modification.

## Effect of the mean-versus-variance KL split

The split **does change the diagnosis**, but it does not make the result more favorable.

The late symmetric-KL values were approximately:

[
\begin{array}{c|cc}
& \text{probe} & \text{real}\
\hline
\text{mean component} & 0.379724 & 0.432676\
\text{variance component} & 0 & 0
\end{array}
]

so the observed late mean-component difference was about `+0.052952`.

This rules out the previously plausible explanation that R29 mainly learned a skill-specific variance code or exploited variance collapse. In the supplied computations, the candidate standard deviations are identical enough that the variance component is exactly zero throughout both runs. The realized separation is entirely through action means.

The refined diagnosis is therefore:

> **R29-T10 induces, or at least is associated with, additional state-conditional action-mean coding, but that coding is not temporally or environmentally meaningful under natural execution.**

The drop in R26 action-only accuracy despite higher same-state mean KL is particularly informative. It indicates that the mean shifts are not forming a stable natural action role for each skill; they are likely state-indexed local contrasts whose direction or consequence changes across visited states.

It would be incorrect to say that the algorithm “successfully chose the better mean mechanism instead of a variance shortcut.” Variance coding was effectively unavailable in this implementation, and mean separation itself failed the transfer test.

## Negative constraint established

The appropriately scoped negative result is:

> **For the current recurrent HA-CTSE policy class, a detached uniform-prior same-action actor-density ratio is not sufficient as an intrinsic reward for useful individual skills—even when the candidate skill is held through a complete natural lifetime, recurrently replayed, and scored on a final ten-action joint block. Actor-internal conditional identifiability can increase through action means without producing natural process differentiation or task-safe behavior.**

Consequently, R29 may remain a **diagnostic of conditional actor capacity**, consistent with R29-G0 and R27, but it should no longer be used as the low-level reward target. This retirement should include variants that only change the prior, temporal window, scaling, clipping, or aggregation of the same actor-only density ratio.

## Conclusions that remain prohibited

This result does **not** support any of the following:

* A final cross-seed or cross-environment claim that every action-information objective fails. The evidence remains one paired training seed.
* Rejection of R27’s conditional-capacity result. The actor can still express different actions and local trajectory effects under forced persistent skills.
* A claim that the low-level skill channel is absent, that asynchronous lifetimes are harmful, or that natural differentiation is impossible.
* A claim about cooperation, complementary team assignment, team intent, high-level skill selection, duration selection, or HMASD parity.
* A claim that R29 optimizes exact mutual information under learned natural skill usage.
* A claim that the raw recurrent replay has zero numerical error; only the anchored source likelihood has exact stored-policy parity.
* A claim that `probe_only` has established robust natural differentiation generally. Its R26 PASS is a single-seed checkpoint result.
* A claim that the entire `31.56%` task difference is a population-level causal effect. It is strong paired evidence within this run, sufficient to fail its per-seed safety contract, but not a multi-seed effect estimate.
