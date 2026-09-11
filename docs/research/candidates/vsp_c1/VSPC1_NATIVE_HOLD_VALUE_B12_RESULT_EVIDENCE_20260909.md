# B12 P78 E0 result evidence

The sole8503 invocation completed with exit0, native COMPLETE and complete
publication readback. Technical acceptance PASS; no limit/cap breach.
Frozen point regions: **CHANGE_DOWN**, C=-0.05860815861231437,
conditional SE0.01145908955291803; Delta512=-0.014981597171180248 (DOWN)
and Delta768=-0.07358975578349462 (DOWN). All four learned means exceed H,
with every individual H loss and adverse identity retained.

[Collected evidence](results/native_hold_value_b12_8503_20260909/evidence.json)
contains native summary, all160 endpoint/H rows, all five means/conditional SEs,
all paired vectors/adverse identities, checker source and process receipt,
eight matching remote/local hashes, admission and full supervisor files.
[Staging](VSPC1_NATIVE_HOLD_VALUE_B12_P78_STAGING_EVIDENCE_20260909.json),
[execution](VSPC1_NATIVE_HOLD_VALUE_B12_P78_TECHNICAL_20260909.md) and
[source acceptance](VSPC1_NATIVE_HOLD_VALUE_B12_TECHNICAL_ACCEPTANCE_20260909.md)
retain exact source/cwd/argv/output/helper and reused boundary coverage.
Raw1696 episode rows,768 rollouts and four checkpoints remain under
`temp/directions/vsp_c1/collection/native_hold_value_b12_8503_19e0d0d30368/output/` and the recorded remote output root.

## Native endpoints and paired change

One matched training pair is the independent unit. Each vector contains32
identity-matched evaluations; conditional SE is sample SD/sqrt(32). Checkpoints
and evaluation episodes are not additional independent training instances.

| Endpoint | Mean native J | Conditional SE |
| --- | ---: | ---: |
| GATED-V_512 | 0.1653390673217001 | 0.00786621189323462 |
| GATED-V_768 | 0.16116423753388723 | 0.005879899309797844 |
| MLP-V_512 | 0.18032066449288034 | 0.009290709074746856 |
| MLP-V_768 | 0.23475399331738186 | 0.009801988057968666 |
| H | 0.13949774240497692 | 0.011668954184557385 |

J=sum(reward)/256. H was evaluated once on the same bank. C's SE uses the paired
change vector, not independently combined endpoint SEs.

| Contrast | Mean | Conditional SE | Negative identities |
| --- | ---: | ---: | ---: |
| GATED-V_512_minus_MLP-V_512 | -0.014981597171180248 | 0.007221301873164606 | 20 |
| GATED-V_512_minus_H | 0.025841324916723158 | 0.010929284701044272 | 11 |
| MLP-V_512_minus_H | 0.040822922087903404 | 0.012961360088402474 | 11 |
| GATED-V_768_minus_MLP-V_768 | -0.07358975578349462 | 0.010358654286610857 | 31 |
| GATED-V_768_minus_H | 0.0216664951289103 | 0.013570936930895502 | 14 |
| MLP-V_768_minus_H | 0.09525625091240493 | 0.014361484251913985 | 5 |
| change | -0.05860815861231437 | 0.01145908955291803 | 28 |

Applicable frozen card section4 rule, verbatim:

| Observation | Reading rule |
| --- | --- |
| C<−.01 | CHANGE_DOWN: a third local decrease beyond the selected scale under the same two-endpoint protocol; retain all endpoint and native/H outcomes. |

Report the point regions and conditional noise separately. Delta512 is below
-.01 with conditional SE.00722130 near that boundary; no automatic extra panel
follows. Both negative endpoint differences remain retained alongside the
previous pairs' different endpoint observations. Positive mean returns relative
to H do not remove the11 GATED512,11 MLP512,14 GATED768 and5 MLP768 individual
H losses. H remains an attained untuned reference; matching tuned headroom is
absent. No population trend, causal budget effect, isolated hold credit, stable
superiority, usable-control/competence claim, family decision or formal UAV entry
follows. DM owns scoring, scientific intake and descriptive8501/8502/8503
comparison; older final-only768,512 and other protocols remain separate.

## Actual execution and artifact acceptance

Scientific SHA19e0d0d303686cd7590ecfe7970d2057d652eea5, master8503,
extra850300012; wrapperc1514944a1522d90f96f51e744125f3091bc90c2.
Handlevspc1_hold_value_b12_8503_19e0d0d30368, PID3043448, hmasd-wsl-node,
CPU FP32, one process/numerical thread. Start2026-09-09T10:48:37Z;
terminal10:57:02Z, exit0 and inactive tmux. Supervisor integer505s duration is
coarser than enclosing /usr/bin/time504.91s, not an additional invocation.

Artifact-only checker PASS, exit0,1.8721233000014763s whole process. No model
construction, forward, evaluation or training replay occurred during collection.
Summary, episodes, rollouts, four endpoint checkpoints and admission each match
remote hashes/sizes. Global order is GATED train512/eval512/continued768/eval768,
then MLP's same sequence, then H once. All8503 identities, reward/step/J
consistency, decision/hold counts and Config-derived cost strings agree.

Actual434176 native team steps=393216 train+40960 evaluation;3072 Adam calls,
1536 training episodes,160 evaluations,1696 scored rows,768 rollouts/3072 epoch
records, four constructors and zero partial steps. Each arm records at512
512 episodes/1024 Adam/256 rollouts and at768768/1536/384. Training-only counts
exclude evaluation; each endpoint panel records32 episodes/8192 steps/zero Adam.
Actual512/768 checkpoint exposure remains distinct from final Config768.
Identities, finite FP32 tensors, critic counts34817/34827 and ordinary-MLP
shapes agree; final parameter/gate norms reconcile with checkpoints.

## Cumulative moments and movement

Each rollout merges512 targets. Endpoint moments match checkpoint/summary/
rollout state and remain frozen during each evaluation and MLP's final H panel.
Recorded loss units are normalized-squared.

| Endpoint | Target count | Merges | Mean | M2 | Scale |
| --- | ---: | ---: | ---: | ---: | ---: |
| GATED-V_512 | 131072 | 256 | 15.657832145690918 | 31270944.0 | 15.445981979370117 |
| GATED-V_768 | 196608 | 384 | 17.977787017822266 | 52107552.0 | 16.27982521057129 |
| MLP-V_512 | 131072 | 256 | 15.974565505981445 | 31720806.0 | 15.55668830871582 |
| MLP-V_768 | 196608 | 384 | 19.37929916381836 | 56968016.0 | 17.022171020507812 |

| Endpoint | Total relative movement | Duration absolute movement | Gate absolute movement |
| --- | ---: | ---: | ---: |
| GATED-V_512 | 0.2704893505126544 | 0.12282869964838028 | 0.748530924320221 |
| GATED-V_768 | 0.3296981592727421 | 0.26299548149108887 | 0.8511881828308105 |
| MLP-V_512 | 0.2724419964130713 | 0.12969855964183807 | not applicable |
| MLP-V_768 | 0.33448970524761296 | 0.29548877477645874 | not applicable |

Relative movement from zero duration/gate initialization is undefined: collection
reports null while preserving raw legacy duration values. Movement establishes
exposure, not useful control. Nonzero held rows are2223 train/192 eval for each
arm, counting both endpoint panels. Raw return-to-go arrays were not separately
replayed/archived; accepted source coverage and actual moments/publication
establish this recorded boundary.

## Complete resources and closure

Fresh canonical actual-node admission passed at10:48:37.563514Z with15631966208
bytes both physical/effective available. Whole wall504.91s includes both learned
panels, H, publication/readback/exit; internal482.5722422829713s,
MLP transition245.6414709329838s and residual22.33775771702875s.
Conservatively charging residual yields GATED267.97922865001254s and
MLP259.26852906701623s, both below1800s; whole below3600s. Serial study critical
path and summed invocation wall504.91s. Peak RSS558932 KiB/545.83203125 MiB.
Aggregate CPU and isolated component overhead remain unmeasured; no timing cause
or extra performance disposition is inferred.

All14 bound runtime surfaces remain unchanged. No scientific or binding deviation
was observed. One accepted P78 submission spent, zero remain; no retry, extra fit/
evaluation, tuning, second pair or successor occurred. CM observation is complete,
with no live process or pending scientific action. Editing/index returns to DM
for all-outcome intake; Root owns integration and any separate next allocation.

P78 test scratch was removed. Historical CM-owned
`temp/directions/vsp_c1/test/b10_p76_focused1` remains after automatic approval
review rejected both exact cleanup commands as “blocked by policy.” No repeated
rejected operation or bypass occurred; CM retains cleanup ownership at a later
permitted boundary. Root owns completed remote-checkout reclamation.
