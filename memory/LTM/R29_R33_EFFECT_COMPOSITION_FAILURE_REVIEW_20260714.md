# R29--R34 effect/composition/codebook failure review

Date: 2026-07-14

## Cross-round causal matrix

| Round | Tested edge | Valid evidence | Reusable conclusion | Retired line |
| --- | --- | --- | --- | --- |
| R29 | natural skill-conditioned action pattern -> online exploration reward | diagnostic action-information existed; endpoint density-ratio reward failed signal preservation, score, and safety | action separation need not imply stable effects or a useful reward | actor-density-ratio reward and aggregation/prior/scale variants |
| R31 | natural effect association -> causally persistent skill effects | natural heldout information `0.487866`; forced between/within ratio `0.889613` | observational effect identity can be context association without causal persistence | CFEI reward and posterior/window/null variants |
| R32 | direct individual-effect gradient -> material codebook-wide effects -> natural coverage | M0 valid; forced shift positive but causal gain `0.028746` and coverage ratio `1.012821` | the registered FiLM path responds, but individual effect magnitude is too weak and does not transport | direct IFEPG and optimizer/effect/scope variants |
| R33 | existing complete roster -> non-additive stable role swap -> high selection -> natural coverage | M0 valid; expected alignment gain `0.001955`, top-pair mass gain `0.001250`, coverage `427/429` | the existing codebook has no demonstrated material selectable team interaction; high-head fitting is not the missing transport mechanism | direct intervention-scored roster-complementarity fitting |
| R34 | unlabeled natural focal modes -> balanced hindsight labels -> recurrent distillation -> stronger causal codebook | M0 valid; real fidelity `0.5752` versus source `0.5098` and sham `0.1836`, but source-relative gain was only `0.0654`; real SNR `1.5235` fell below source `1.7608` | label-aligned imitation avoids a destructive sham but does not create stronger modes than the source policy | fixed balanced hindsight mode distillation and its clustering/epoch/scope variants |

## Baseline matrix

| Evidence role | R33 realization | Result |
| --- | --- | --- |
| Diagnostic validity | complete `4 x 4` randomized roster table, two independent replicas, additive-main-effect residual, symmetric-orientation penalty | PASS |
| Mechanism-matched control | true pair attribution versus complementary-edge pair-sham; same score multiset and eight head-only updates | real advantage positive but immaterial |
| Natural transport null | 64 paired stochastic resets; joint and role-free nonredundant position coverage | no transport; real slightly lower |
| Async controller safety | full-sync SET, switch-skill entropy/share, long/short lifetime breadth | PASS; failure is not R30 collapse |
| Task efficacy / HMASD parity | not tested | no claim |

## Failure classification

- Instrumentation/data quality: no identified failure.
- Optimization scope: both high heads moved about `2.6--2.8%` with finite
  gradients; failure is not zero wiring.
- Capacity/effect: the exact distribution learned the correct mapping only at
  approximately `0.2%` of the registered expected-score gate and `1.25%` of the
  top-pair-mass gate.
- Transport: neither joint coverage nor agent nonredundancy improved.
- Confounds: skill supply and heterogeneous lifetime use remained healthy.

R34 then isolated codebook reconstruction from sham degradation with a frozen
source anchor. Every implementation check passed, the max-Hamming sham retained
only `2.08%` label agreement, and source replay error was `2.86e-6`. The real
arm strongly beat sham, but it improved forced fidelity over source by only
`0.0654` versus `0.15`, reduced persistent SNR by `0.2962` with a wholly
negative interval, improved natural mode agreement by only `0.0488` versus
`0.10`, and did not improve paired-reset coverage over source. This is a valid
algorithmic failure, not insufficient sham disruption or R30 collapse.

## Open boundary

The individual-effect, direct-selection, and post-hoc mode-distillation lines
are exhausted. The new source anchor shows that the checkpoint already exposes
some one-block forced displacement separation, but relabel-and-clone training
does not strengthen it or transport it. The next proposal must create one
genuinely new online causal edge rather than rescore existing labels, mine and
imitate their realized trajectories, refit the high roster distribution, or
damage a sham. It must select exactly one mechanism that can make latent
semantics stronger than the frozen source under matched intervention. Scheduler
or async mechanics alone are not a learning contribution.
