# B13 P80 E0 result evidence

The sole master-8601 invocation finished with exit 0, native COMPLETE and complete
publication readback. Technical acceptance PASS, with no limits or cap breach.
The frozen final-only point region is **DOWN**: Delta_new=-0.032068580497115584,
conditional SE 0.010110683526267093; 25/32 paired identities are negative.
Both learned means exceed H, while all individual H losses remain retained.

[Collected evidence](results/native_hold_value_b13_8601_20260909/evidence.json)
contains the native summary, all 96 final/H episode rows, three native means/SEs,
all three 32-difference vectors and every adverse identity, checker source/process
receipt, six matching artifact/admission hashes, and full supervisor files.
[Technical acceptance and exact execution](VSPC1_NATIVE_HOLD_VALUE_B13_P80_TECHNICAL_20260909.md),
[source checks](VSPC1_NATIVE_HOLD_VALUE_B13_SOURCE_CHECKS_20260909.json) and
[staging](VSPC1_NATIVE_HOLD_VALUE_B13_P80_STAGING_EVIDENCE_20260909.json)
retain implementation/review, literal wrapper, source hashes and admission.

## Native returns and frozen rule

One matched training pair (two fits) is the independent scientific unit. J is
full native reward sum / 256. The 32 matched evaluation identities are a conditional
panel, not additional training replicates; SE is sample SD / sqrt(32).

| Controller | Mean native J | Conditional SE |
| --- | ---: | ---: |
| GATED-V | 0.14432349607139883 | 0.011874970947597617 |
| MLP-V | 0.1763920765685144 | 0.009401179652869822 |
| H | 0.1408296189671304 | 0.011045898140768612 |

| Contrast | Mean | Conditional SE | Negative identities |
| --- | ---: | ---: | ---: |
| GATED-V_minus_MLP-V | -0.032068580497115584 | 0.010110683526267093 | 25 |
| GATED-V_minus_H | 0.003493877104268443 | 0.012229797520304786 | 15 |
| MLP-V_minus_H | 0.035562457601384025 | 0.01153666233378983 | 11 |

Applicable frozen card §4 rules, verbatim:

| Observation | Reading rule and bounded consequence |
| --- | --- |
| Delta_new<-.01 | DOWN: local native counterexample for this additive package; favor the ordinary body for this instance. Not broad hold-credit or K4 failure. |
| Learned mean or episode below H | Retain all losses separately. Relative improvement alone does not establish useful control, optimality or tuned competence. |
| Conditional noise reaches MEI | Report point region and uncertainty; no extra episodes to cross or resolve a boundary. |

The primary conditional SE .01011068 slightly exceeds the .01 MEI; this does
not change the point region or allocate extra evaluation. All 15 GATED and 11 MLP
individual losses to H remain explicit in the evidence. H is an untuned attained
control; tuned same-information headroom is absent. The H contrast identity
(GATED−H)−(MLP−H)=Delta_new holds on every paired identity and supplies no replication.
No stable superiority, equivalence, unique hold credit, explanation of the old
650-parameter tradeoff, competence, transfer, C promotion or formal UAV entry follows.
This final-only intact-body protocol is kept separate from older two-panel,
width-128, unnormalized and quarantined records. DM owns prediction scoring,
scientific intake and the next unallocated recommendation.

## Source, process and publication acceptance

Scientific source `23ebb0f5e22286d9ea77a145f980bedacc32d9da`; wrapper
`83b6e2f8c28cbf5e9925252c31057446cce3362e`. Handle
`vspc1_hold_value_b13_8601_23ebb0f5e222`, PID 3052500, hmasd-wsl-node.
CPU FP32, one scientific process/numerical thread. Accepted 2026-09-09T12:49:54Z;
finished 12:57:52Z with exit 0 and inactive tmux. Actual /usr/bin/time whole
wall is 477.99s; supervisor duration 478s is its rounded process fact.

Artifact-only checker: PASS, exit 0, 1.960492999998678s whole. It loads
existing checkpoint tensors and raw records; no model construction, forward,
native evaluation or training replay. All six collected files match remote SHA256:
summary, episodes, rollouts, two final checkpoints and admission. Global order is
GATED train768/eval32, MLP train768/eval32, then H32. No 512 checkpoint or panel exists.
Actual per-episode reset identities and final768 metadata, J/reward/step identities,
decision masks, hold-row counts, counts and Config-derived cost strings agree.
Each arm records two constructors but only its training constructor in training counts.
Both final checkpoints contain complete 136→128→133→1 bodies; GATED additionally
has a 128×5 gate. Counts are 35467/34827 critic parameters, 32264 actor parameters.
This is explicitly +640 parameters, not capacity matched. Checkpoint tensors are
finite FP32 with correct source/configuration, shape and actual endpoint moments.
Each arm has 384 moment merges over 196608 unique targets; moments match exactly
before and after its evaluation, and MLP moments also match after H. Four PPO
epochs per rollout give 1536 Adam per arm, with normalized squared value-loss units.
The focused source checks and independent changed-boundary review establish common
private initialization, independent mutable state and preserved older defaults.

## Actual exposure and resources

| Quantity | Actual |
| --- | ---: |
| Fits / learned final endpoints / H banks | 2 / 2 / 1 |
| Native team steps, training / evaluation | 417792, 393216 / 24576 |
| Rollouts / Adam / moment merges | 768 / 3072 / 768 |
| Unique target rows / four-epoch terms | 393216 / 1572864 |
| Scored episodes / evaluations | 1632 / 96 |
| Constructors / constructor resets / explicit resets | 4 / 4 / 1632 |
| Velocity decisions / duration decisions / d4 choices | 2035658 / 8000 / 4114 |
| Recurrent observations / partial steps / diagnostic frames | 2048000 / 0 / 0 |

| Arm | Nonzero-r rows train / eval | Total relative parameter move | Absolute duration move |
| --- | ---: | ---: | ---: |
| GATED-V | 2235 / 96 | 0.3104761031520962 | 0.24620351195335388 |
| MLP-V | 2220 / 90 | 0.31910682722979045 | 0.1575537919998169 |

Absolute gate displacement is 0.6176927089691162.
Gate and duration heads start at zero, so their relative displacement is undefined.
Raw legacy duration epsilon-denominator fields are preserved in the native summary
but are not interpretable as relative movement; evidence explicitly records this limit.
Parameter movement and sparse gate exposure do not replace native return.

Fresh actual-node admission passed at 12:49:54.754938Z with 15323074560 bytes
physical/effective available (floor 4294967296). Whole wrapper wall includes startup,
admission, both arms, all evaluation/H, publication/readback and exit.
Runner wall 456.0979581460124s; MLP boundary 246.06745119503466s;
unpartitioned enclosing residual 21.89204185398762s is charged
conservatively to each arm for an upper bound:
GATED 267.9594930490223s and MLP 231.92254880496534s.
Both are below 1800s; whole 477.99s is below 3600s. One sequential invocation means
summed invocation wall and study execution critical path are both 477.99s; engineering
and collection are separately recorded. Peak RSS is 557784 KiB (544.7109375 MiB).
Aggregate CPU, component cost and other optional resource metrics remain unmeasured.
The original cost projection reused earlier complete-path timings; no pilot was run.

Raw 1632 episode rows, 768 rollout rows and two checkpoints remain at
`temp/directions/vsp_c1/collection/native_hold_value_b13_8601_23ebb0f5e222/output/`
and `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b13_8601_23ebb0f5e222`.
Engineering scope §4 none: 62 scientific source additions plus seven wrapper lines;
Python runner 35 lines. Focused source checks used 4.2679593s; collection checker
used 1.960493s. New B13 test scratch was removed. Historical P76 scratch remains
creator-owned after the recorded cleanup policy rejection, without another attempt.

One accepted submission is spent; zero remain. There was no retry, replacement
pair, extra panel, independent H refill or Pro Send. CM observation and technical
collection are complete. Editing/index returns to DM for intake; Root owns
integration and reclamation of the completed detached remote checkout.
