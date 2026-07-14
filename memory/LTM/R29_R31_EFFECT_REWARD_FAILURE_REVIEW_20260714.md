# R29/R31 Effect-Reward Failure Review

Date: 2026-07-14

## Cross-round evidence

| Round | Verified evidence | Failed causal edge | Reusable constraint |
| --- | --- | --- | --- |
| R29 | Natural skill-conditioned action-density separation exists and the implementation gate passed. | Adding that score did not preserve the natural signal, did not improve the paired score, and degraded task reward. | Action-pattern identifiability is not realized persistent environmental effect. |
| R31 | A natural fixed-window posterior achieved heldout `G_nat=0.487866` nats, CI `[0.319984, 0.638954]`. | Forced-skill between/within median ratio was `0.889613`, CI `[0.763227, 1.078315]`; skills 0/1 pooled ratios were below one. | Natural effect classification is association-dominated and cannot authorize online reward without intervention-level effect separation. |

R31 execution was scientifically valid: 1,024 natural windows, 768 posterior
training windows, 256 heldout windows, 1,024 forced windows, common random
numbers, zero policy updates, and zero forced rows in posterior training. Skill
3 had only 44 heldout rows, but the registered hard FAIL already follows from
the direct forced-skill M2, so adding the identical batch cannot reverse this
branch. GPT-5.6 Pro corrected the matched-shuffle interpretation: a mismatched
effect generally has a negative posterior residual under the receiver label,
so `-2.068` is a disruption diagnostic rather than an independent near-zero
null failure. This correction does not change the M2-based retirement.

## Failure separation

- Verified mechanism: R30 supplies asynchronous `KEEP/SET` lifetimes, and the
  current policy produces naturally classifiable trajectories.
- Instrumentation/data quality: no operational or comparator failure was
  observed. The per-skill count shortfall is not the decisive failure.
- Optimization/capacity: the posterior fit natural effects (`full loss 0.488`
  versus context loss `1.083`); the failure is not lack of classifier capacity.
- Task evidence: none was requested or produced; reward and policy were frozen.
- Negative conclusion: neither action-density reward nor observational
  fixed-window effect information establishes a causal persistent skill effect.

## Single next causal edge

GPT-5.6 Pro selected R32-IFEPG: use two independent randomized fixed-window
skill-intervention replicas to estimate signed between-skill effect separation,
then apply a PPO-clipped auxiliary update only to the low actor's skill FiLM.
The paired Alice--Bob gate asks whether this intervention-anchored update can
*create* persistent effects larger than same-skill stochastic variability and
transport them into natural coverage without posterior, intrinsic reward,
critic, GAE, entropy, task-reward, or high-policy updates. Any valid M1--M3
failure retires direct IFEPG. R29/R31 coefficient, window, prior,
posterior-capacity, or null retuning remains prohibited.

Runtime source:
`logs/r31_cfei_reward_off_gate_20260714_181038/result/r31_causal_effect_gate.json`.
