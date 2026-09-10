# VSPC1 NATIVE HOLD VALUE B07 - E0 result evidence

The sole P72 invocation completed with exit 0, native status COMPLETE, complete
publication readback and no limit/cap breach. Technical acceptance is PASS.
The frozen point-estimate region is UP. No second submission, retry, extra
evaluation or successor was executed. DM owns scientific intake and any
three-pair descriptive interpretation; prior 8301/8302 evidence is preserved.

[Collected evidence](results/native_hold_value_b07_8303_20260908/evidence.json)
retains the native summary, all 96 evaluation rows, all matched contrasts and
adverse identities, checker source/results, artifact hashes and full admission/
terminal receipts. [Staging evidence](VSPC1_NATIVE_HOLD_VALUE_B07_P72_STAGING_EVIDENCE_20260908.json)
and [execution record](VSPC1_NATIVE_HOLD_VALUE_B07_P72_TECHNICAL_20260908.md)
bind the exact runtime inputs.

## Execution identity

Scientific SHA `4e83312ea5d35db4472bbc821b0c2cf875e853b3`, master 8303, extra initialization 830300012.
Wrapper commit `e76c34949ae3a2301ae3fd1adc0dc78e78bff272`. Handle `vspc1_hold_value_b07_8303_4e83312ea5d3`, PID 3026966,
node hmasd-wsl-node, CPU FP32, one process/numerical thread.
Detached cwd `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b07-8303-4e83312ea5d3`; output `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b07_8303_4e83312ea5d3`.
Start 2026-09-09 06:09:59 UTC; terminal 06:15:12 UTC, exit 0 and tmux inactive.
Supervisor whole-second duration 313s; enclosing /usr/bin/time 313.50s.
Raw local collection: `temp/directions/vsp_c1/collection/native_hold_value_b07_8303_4e83312ea5d3/`.

## Native endpoints and frozen rule

| Arm | Mean native J |
| --- | ---: |
| GATED-V | 0.1736901218918796 |
| MLP-V | 0.14031220549753456 |
| H | 0.13086998202805208 |

MLP-V is the fixed ordinary width-133 comparator. Each contrast contains 32
identity-matched evaluations conditional on this single trained pair.

| Contrast | Mean | Conditional SE | Negative differences |
| --- | ---: | ---: | ---: |
| GATED-V_minus_MLP-V | 0.03337791639434502 | 0.008588205927794471 | 6 |
| GATED-V_minus_H | 0.0428201398638275 | 0.01074415193119564 | 7 |
| MLP-V_minus_H | 0.009442223469482484 | 0.010821897784159864 | 12 |

Card section 4's applicable rule, verbatim:

| Observation | Bounded reading |
| --- | --- |
| Delta>.01 with trustworthy primary | UP: a local gated-package advantage over this specified ordinary critic in8303; retain both prior width133 outcomes and H, with no stable claim or automatic successor. |

The mean difference exceeds .01. Conditional SE and every adverse identity are
retained without a population-significance inference. Both learned mean returns
exceed H; GATED is below H on 7 identities and MLP on 12. H remains an untuned
attained reference, with matching tuned headroom absent. This new independent
unit is one training pair, not 32 seeds. No stable-superiority, equivalence,
capacity-causality or specialized-hold-credit conclusion follows from checks.
The prospective WITHIN(.55) forecast remains unchanged for DM scoring.

## Technical acceptance, counts and state

Artifact-only check PASS in 2.3815832999534905s complete process, exit 0.
No model construction, forward, native episode/evaluation or training replay.
Remote/local SHA256 values match summary, episodes, rollouts, both final
checkpoints and admission. The 1120 episode rows, 512 rollouts and 2048 epoch
records reconcile: 286720 native steps (262144 training /24576 evaluation),
2048 Adam calls, 1024 training episodes, 96 final evaluations, two constructors
and zero partial steps. Reward/J decomposition, held-decision counts, full
master/reset identities and all contrast means/conditional SEs agree.

Source/object/configuration/checkpoint identities and FP32 tensor finiteness pass.
Critic counts are 34817 GATED /34827 MLP. Wider second weight/bias shapes are
(133,128)/(133,), output weight (1,133); final parameter/gate norms agree with
summary exposure. Total relative movements are
0.2559565566326407 /0.24775843450121335.
Gate absolute movement is 0.5661719441413879; duration
absolute movements 0.09483914822340012 /0.09940600395202637.
These gate/duration initial norms are zero, so relative movement is undefined.
The collected check supplies null while preserving the raw legacy summary field.

Each arm has 131072 target rows and 256 moment merges with 512-row increments.
Normalized-squared losses and final moments match checkpoint/summary and remain
fixed across learned evaluation and MLP's H evaluation:

| Arm | Final mean | Final M2 | Final scale |
| --- | ---: | ---: | ---: |
| GATED-V | 20.516817092895508 | 31541034.0 | 15.512542724609375 |
| MLP-V | 20.77504539489746 | 29015816.0 | 14.878612518310547 |

Nonzero held rows: GATED 1500 training /96 evaluation; MLP 1506 /96. Full raw
return-to-go arrays are not separately replayed/archived; unchanged accepted
source checks and actual recorded moment/publication state cover this boundary.

## Complete resources and disposition boundary

Fresh actual-node canonical admission passed both floors with
15320178688 available bytes. Whole wall
313.5s includes H/publication/readback/exit; internal pair
305.0476207679603s, MLP transition 159.12280644796556s and residual
8.452379232039675s. Conservatively charging the residual to each
arm yields GATED 167.57518568000523s and MLP
154.37719355203444s, both below 1800s; whole pair below 3600s.
Serial critical path and summed invocation wall are both 313.50s. Peak RSS
558164 KiB (545.08203125 MiB). Aggregate CPU and isolated width/
normalization overhead remain unmeasured; no cause of timing variation is assigned.

No scientific or execution-binding deviation was observed. Reused checks and
P69's historical enclosing-test-wall gap remain as recorded. New source, tests,
records and result evidence strictly decode as UTF-8. P72's accepted submission
allowance is spent; CM observation is complete. DM is next owner for all-outcome
intake and the final Root relay. No automatic successor is allocated.
