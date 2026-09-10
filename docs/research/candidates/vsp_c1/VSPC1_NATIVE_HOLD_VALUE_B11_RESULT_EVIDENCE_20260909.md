# B11 P77 E0 result evidence

The sole8502 invocation completed with exit0, native COMPLETE and complete
publication readback. Technical acceptance PASS; no limit/cap breach.
Frozen primary point region: **CHANGE_DOWN**, C=-0.011924250290295561,
conditional SE0.0074169720617037575. Delta512=.02131485092772898 (UP);
Delta768=.00939060063743342 (WITHIN). All four learned means exceed H,
while every individual H loss and adverse identity remains retained.

[Collected evidence](results/native_hold_value_b11_8502_20260909/evidence.json)
contains native summary, all160 endpoint/H rows, all five native means/conditional
SEs, all paired vectors/adverse identities, checker source/process receipt,
eight matching remote/local hashes, admission and full supervisor files.
[Staging](VSPC1_NATIVE_HOLD_VALUE_B11_P77_STAGING_EVIDENCE_20260909.json),
[execution](VSPC1_NATIVE_HOLD_VALUE_B11_P77_TECHNICAL_20260909.md) and
[source acceptance](VSPC1_NATIVE_HOLD_VALUE_B11_TECHNICAL_ACCEPTANCE_20260909.md)
retain exact source/cwd/argv/output/helper and reused boundary coverage.
Raw1696 episode rows,768 rollouts and four checkpoints remain under
`temp/directions/vsp_c1/collection/native_hold_value_b11_8502_7ed4c3933771/output/` and the recorded remote output root.

## Native endpoints and paired change

One matched training pair is the independent unit. Each vector contains32
identity-matched evaluations; conditional SE is sample SD/sqrt(32). Checkpoints
and evaluation episodes are not new independent training units.

| Endpoint | Mean native J | Conditional SE |
| --- | ---: | ---: |
| GATED-V_512 | 0.20911290995288803 | 0.00914988320800044 |
| GATED-V_768 | 0.20939916833462438 | 0.009185858310267542 |
| MLP-V_512 | 0.18779805902515903 | 0.01044328681897885 |
| MLP-V_768 | 0.20000856769719094 | 0.008186247018720736 |
| H | 0.1623154235179454 | 0.013201591920555361 |

J=sum(reward)/256. H was evaluated once on the same bank. C's SE uses the paired
change vector, not independently combined endpoint SEs.

| Contrast | Mean | Conditional SE | Negative identities |
| --- | ---: | ---: | ---: |
| GATED-V_512_minus_MLP-V_512 | 0.02131485092772898 | 0.004356590412006853 | 5 |
| GATED-V_512_minus_H | 0.04679748643494264 | 0.009331146689612803 | 5 |
| MLP-V_512_minus_H | 0.025482635507213653 | 0.009665856195865335 | 10 |
| GATED-V_768_minus_MLP-V_768 | 0.00939060063743342 | 0.007632995071817825 | 16 |
| GATED-V_768_minus_H | 0.047083744816678985 | 0.012223403798776655 | 7 |
| MLP-V_768_minus_H | 0.03769314417924557 | 0.011170102300392303 | 9 |
| change | -0.011924250290295561 | 0.0074169720617037575 | 22 |

Applicable frozen card section4 rule, verbatim:

| Observation | Reading rule |
| --- | --- |
| C<−.01 | CHANGE_DOWN: a second local decrease beyond the selected scale under the same two-endpoint protocol; retain all endpoint and native/H outcomes. |

C is only.00192425 below the -.01 point boundary, with conditional SE.00741697;
report region and noise separately. Delta768 remains inside MEI with conditional
noise near its boundary; WITHIN is not equivalence. Retain all H losses despite
positive means:5 GATED512,10 MLP512,7 GATED768 and9 MLP768 identities lose to H.
H remains an attained untuned reference and matching tuned headroom is absent.
No population trend, causal budget effect, isolated hold credit, stable superiority,
usable-control/competence claim, family decision or formal UAV entry follows.
DM owns scientific intake, prediction scoring and descriptive8501/8502 comparison.
Keep this protocol separate from prior final-only768,512 and older regimes.

## Actual execution and artifact acceptance

Scientific SHA7ed4c3933771f85d570b5c952052b9e8c5fbd6e1, master8502,
extra850200012; wrapper40bdcdcba7df2017d5636665b7e5b2f8d2f8f5b9.
Handlevspc1_hold_value_b11_8502_7ed4c3933771, PID3040577, hmasd-wsl-node,
CPU FP32, one process/numerical thread. Start2026-09-09T10:08:02Z;
terminal10:16:30Z, exit0 and inactive tmux. Supervisor integer508s duration
is coarser than enclosing /usr/bin/time507.29s, not an additional invocation.

Artifact-only checker PASS, exit0,2.1057732999997825s whole process. No model
construction, forward, evaluation or training replay occurred in collection.
Summary, episodes, rollouts, four endpoint checkpoints and admission each match
remote hashes/sizes. Global order is GATED train512/eval512/continued768/eval768,
then MLP's same sequence, then H once. All8502 identities, reward/step/J
consistency, decision/hold counts and Config-derived cost strings agree.

Actual434176 native team steps=393216 train+40960 evaluation;3072 Adam calls,
1536 training episodes,160 evaluations,1696 scored rows,768 rollouts/3072 epoch
records, four constructors and zero partial steps. At512 each arm records
512 episodes/1024 Adam/256 rollouts; at768768/1536/384. Training-only cumulative
counts exclude evaluations; each endpoint evaluation records32 episodes/8192
steps/zero Adam. Actual512/768 checkpoint exposure remains distinct from final
Config768. Identities, finite FP32 tensors, critic counts34817/34827 and
ordinary-MLP shapes agree; final parameter/gate norms reconcile with checkpoints.

## Moments and movement

Each rollout merges512 targets. Endpoint moments match checkpoint/summary/rollout
state, remain frozen during each evaluation and MLP's final H evaluation, and
retain normalized-squared loss units.

| Endpoint | Target count | Merges | Mean | M2 | Scale |
| --- | ---: | ---: | ---: | ---: | ---: |
| GATED-V_512 | 131072 | 256 | 20.615949630737305 | 29318826.0 | 14.956098556518555 |
| GATED-V_768 | 196608 | 384 | 22.020652770996094 | 49050832.0 | 15.7951078414917 |
| MLP-V_512 | 131072 | 256 | 19.790363311767578 | 27970848.0 | 14.608238220214844 |
| MLP-V_768 | 196608 | 384 | 20.824256896972656 | 45691536.0 | 15.244644165039062 |

| Endpoint | Total relative movement | Duration absolute movement | Gate absolute movement |
| --- | ---: | ---: | ---: |
| GATED-V_512 | 0.24895490661418998 | 0.17615483701229095 | 0.553394615650177 |
| GATED-V_768 | 0.3177228045753876 | 0.12216884642839432 | 0.6401658654212952 |
| MLP-V_512 | 0.26653140759762767 | 0.0886552482843399 | not applicable |
| MLP-V_768 | 0.3276708020337692 | 0.07761131972074509 | not applicable |

Relative movement from zero duration/gate initialization is undefined; the
collection record reports null while retaining raw legacy duration values.
Movement establishes exposure, not useful control. Nonzero held rows are
GATED2226 train/186 eval, MLP2220 train/186 eval, including both endpoints.
Raw return-to-go arrays were not separately replayed/archived; accepted source
coverage and actual moments/publication establish this recorded boundary.

## Complete resources and closure

Fresh canonical actual-node admission passed at10:08:02.935732Z with15318642688
bytes both physical/effective available. Whole wall507.29s includes both learned
endpoints, H, publication/readback/exit; internal486.76225972297834s,
MLP transition258.66727890400216s and residual20.527740277021678s.
Conservatively charging residual yields GATED279.19501918102384s and
MLP248.62272109599786s, both below1800s; whole below3600s. Serial study critical
path and summed invocation wall507.29s. Peak RSS561968 KiB/548.796875 MiB.
Aggregate CPU and isolated component overhead remain unmeasured; no timing cause
or extra performance disposition is inferred.

All14 bound runtime surfaces remain unchanged. No scientific or binding deviation
was observed. One accepted P77 submission spent, zero remain; no retry, extra fit/
evaluation, tuning, second pair or successor occurred. CM observation is complete,
with no live process or pending scientific action. Editing/index returns to DM
for all-outcome intake; Root owns integration and any separate next allocation.

P77 test scratch was removed. Historical CM-owned
`temp/directions/vsp_c1/test/b10_p76_focused1` remains after automatic approval
review rejected both exact cleanup commands as “blocked by policy.” No repeated
rejected operation or bypass occurred; CM retains cleanup ownership at a later
permitted boundary. Root owns prior remote-checkout reclamation.
