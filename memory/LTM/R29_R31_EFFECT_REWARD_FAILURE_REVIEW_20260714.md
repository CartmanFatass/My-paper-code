# R29/R31 Effect-Reward Failure Review

Date: 2026-07-14

## Cross-round evidence

| Round | Verified evidence | Failed causal edge | Reusable constraint |
| --- | --- | --- | --- |
| R29 | Natural skill-conditioned action-density separation exists and the implementation gate passed. | Adding that score did not preserve the natural signal, did not improve the paired score, and degraded task reward. | Action-pattern identifiability is not realized persistent environmental effect. |
| R31 | A natural fixed-window posterior achieved heldout `G_nat=0.487866` nats, CI `[0.319984, 0.638954]`. | Forced-skill between/within median ratio was `0.889613`, CI `[0.763227, 1.078315]`; skills 0/1 pooled ratios were below one and matched shuffle was `-2.068` nats. | Natural effect classification is association-dominated and cannot authorize online reward without intervention-level effect separation. |

R31 execution was scientifically valid: 1,024 natural windows, 768 posterior
training windows, 256 heldout windows, 1,024 forced windows, common random
numbers, zero policy updates, and zero forced rows in posterior training. Skill
3 had only 44 heldout rows, but the registered hard FAIL already follows from
the global causal ratio and shuffle null, so adding the identical batch cannot
reverse this branch.

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

Before another reward is implemented, determine whether a policy-matched
intervention-anchored objective can *create* between-skill persistent effects
larger than same-skill stochastic variability, rather than merely classify
natural correlations. The next external review must choose one concrete route,
one comparator, and an abandonment gate for that edge. R29/R31 coefficient,
window, prior, posterior-capacity, or null retuning is prohibited.

Runtime source:
`logs/r31_cfei_reward_off_gate_20260714_181038/result/r31_causal_effect_gate.json`.
