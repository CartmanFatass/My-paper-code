# R29--R32 Effect-Creation Failure Review

Date: 2026-07-14

## Cross-round evidence

| Round | Verified evidence | Failed causal edge | Reusable constraint |
| --- | --- | --- | --- |
| R29 | Natural skill-conditioned action-density separation exists and the implementation gate passed. | Adding that score did not preserve the natural signal, did not improve the paired score, and degraded task reward. | Action-pattern identifiability is not realized persistent environmental effect. |
| R31 | A natural fixed-window posterior achieved heldout `G_nat=0.487866` nats, CI `[0.319984, 0.638954]`. | Forced-skill between/within median ratio was `0.889613`, CI `[0.763227, 1.078315]`; skills 0/1 pooled ratios were below one. | Natural effect classification is association-dominated and cannot authorize online reward without intervention-level effect separation. |
| R32 | FiLM-only IFEPG passed every implementation check and produced a positive paired causal-ratio gain `0.028746`, CI `[0.024775, 0.033320]`, without increasing within-skill noise. | Real causal ratio was only `1.015540`, between growth `1.029965x`, and natural coverage growth `1.012821x`; skills 0/1 remained below pooled ratio one. | Direct individual intervention gradients can move effects slightly, but this bottleneck is insufficient to create robust differentiation or natural transport. |

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
  fixed-window effect information establishes a causal persistent skill effect;
  directly optimizing the individual FiLM effect yields only a small valid
  shift and no material natural coverage transport.

## Single next causal edge

R32 validly failed its precommitted abandonment gate, so direct IFEPG is now
retired. The next edge must be structurally different from individual
classification, action-density reward, observational effect reward, and direct
FiLM effect maximization. External review must choose exactly one R33 route and
decide whether the missing level is complementary team composition under R30,
or another mechanism with a distinct causal intervention. Its first evidence
must remain a minimal sparse Alice--Bob gate with an explicit abandonment
branch. R29/R31/R32 coefficient, learning-rate, update-count, window, replica,
effect, threshold, posterior, or seed rescue variants are prohibited.

Runtime source:
`logs/r32_ifepg_paired_gate_20260714_193304/result/r32_ifepg_pair.json`.
