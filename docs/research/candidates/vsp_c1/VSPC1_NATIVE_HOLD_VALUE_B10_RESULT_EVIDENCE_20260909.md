# B10 P76 E0 result evidence

The sole8501 invocation finished with exit0, native COMPLETE and complete
publication readback. Technical acceptance PASS; no limit/cap breach.
The frozen primary point estimate is **CHANGE_DOWN**:
C=-0.054239093386632645, conditional SE0.00921549713046484.
Delta512=.06387970396285268 (UP); Delta768=.009640610576220038 (WITHIN).
MLP512's mean is below H; the other three learned endpoint means are above H.
Every endpoint, H loss and adverse identity remains retained.

[Collected evidence](results/native_hold_value_b10_8501_20260909/evidence.json)
contains native summary, all160 endpoint/H evaluation rows, full paired vectors,
all five native means/conditional SEs, all adverse identities, checker source and
process receipt, eight matching remote/local hashes, admission and supervisor files.
[Staging](VSPC1_NATIVE_HOLD_VALUE_B10_P76_STAGING_EVIDENCE_20260909.json),
[execution](VSPC1_NATIVE_HOLD_VALUE_B10_P76_TECHNICAL_20260909.md) and
[source acceptance](VSPC1_NATIVE_HOLD_VALUE_B10_TECHNICAL_ACCEPTANCE_20260909.md)
retain the fixed binding, scientific coverage and independent boundary review.
Raw1696 episode rows,768 rollout rows and four fixed checkpoints remain at
`temp/directions/vsp_c1/collection/native_hold_value_b10_8501_2c2c7d9d3481/output/` and the recorded remote scientific output root.

## Native means and conditional uncertainty

One matched training pair is the independent unit. Its four learned checkpoints
and32 shared evaluation identities are not independent training replicates.
All displayed SEs use sample SD/sqrt(32), conditional on these fitted endpoints.

| Endpoint | Mean native J | Conditional SE |
| --- | ---: | ---: |
| GATED-V_512 | 0.2003165067135222 | 0.00877501000152114 |
| GATED-V_768 | 0.2041025987306807 | 0.009686280650777954 |
| MLP-V_512 | 0.13643680275066952 | 0.008052180191057488 |
| MLP-V_768 | 0.19446198815446067 | 0.006921082585591354 |
| H | 0.17061603371582315 | 0.01124624459273428 |

J is native sum(reward)/256. H is evaluated once on the same32 resets and reused
only as the common reference in contrasts. C's SE is computed from the identity-
paired change vector, not from independent endpoint SEs.

| Contrast | Mean | Conditional SE | Negative identities |
| --- | ---: | ---: | ---: |
| GATED-V_512_minus_MLP-V_512 | 0.06387970396285268 | 0.007659844646370837 | 2 |
| GATED-V_512_minus_H | 0.029700472997699057 | 0.00993866482007968 | 10 |
| MLP-V_512_minus_H | -0.03417923096515363 | 0.009625718152610459 | 23 |
| GATED-V_768_minus_MLP-V_768 | 0.009640610576220038 | 0.00808773377155225 | 15 |
| GATED-V_768_minus_H | 0.033486565014857556 | 0.01123204621294023 | 10 |
| MLP-V_768_minus_H | 0.023845954438637518 | 0.010912814962417269 | 13 |
| change | -0.054239093386632645 | 0.00921549713046484 | 26 |

Applicable card section4 primary rule, verbatim:

| Observation | Reading rule |
| --- | --- |
| C<−.01 | CHANGE_DOWN: the local gated-minus-MLP difference decreases beyond the selected scale along this pair. |

This is the point-estimate reading for one prospective pair. Endpoint768 is
inside the selected MEI with conditional noise near its boundary; WITHIN is not
equivalence. The positive512 advantage and smaller positive768 difference are
both retained. Negative H identities remain10 GATED512,23 MLP512,10 GATED768
and13 MLP768. Relative advantage/change establishes neither usable control nor
comparator competence. H is an attained untuned reference; matching tuned
headroom remains absent. No population trend, causal budget effect, specialized
hold credit, stable superiority, family disposition or formal UAV entry follows.
This two-endpoint protocol stays separate from prior final-only768 and older512
regimes. DM owns prediction scoring and scientific intake; no successor is selected.

## Execution and artifact acceptance

Scientific SHA2c2c7d9d34814c9834a741ce25b2f36076347315, master8501,
extra850100012; wrapperf55ab4036fa64449f77031d565bf229146727092.
Handlevspc1_hold_value_b10_8501_2c2c7d9d3481, PID3038411, hmasd-wsl-node,
CPU FP32, one process/numerical thread. Start2026-09-09T09:23:54Z;
terminal09:31:50Z, exit0 and inactive tmux. Supervisor integer duration476s
is coarser than enclosing /usr/bin/time475.85s, not an additional invocation.

Artifact-only checker PASS, exit0,2.0442809999995006s whole process. No model
construction, forward, native evaluation or training replay occurred in collection.
Summary, episodes, rollouts, all four endpoint checkpoints and admission each
match their remote SHA256/size. Global order is GATED train512/eval512/continued
train768/eval768, then the same MLP sequence, then H once. All8501 reset identities,
reward/step/J decompositions, held-decision totals and Config-derived cost strings
agree. There are434176 native team steps:393216 train and40960 evaluation;
3072 Adam calls,1536 training episodes,160 evaluations,1696 scored rows,
768 rollouts/3072 epoch records, four constructors and zero partial steps.

Each arm has768 training episodes/1536 Adam calls; each512 endpoint records
512 episodes/1024 Adam/256 rollouts, and each768 endpoint records768/1536/384.
Training-only counts exclude both evaluations; total counts include all work.
Each endpoint has32 evaluations/8192 steps with zero optimizer updates.
Checkpoint identities/configuration, actual training_episodes512/768, finite
FP32 tensors, critic counts34817/34827 and wider-MLP shapes all agree.

## Cumulative moments and exposure

Moments merge512 targets per rollout and remain frozen across each endpoint's
evaluation. Checkpoint, summary and recorded rollout states agree at512/768;
MLP's final moments remain unchanged across H. Loss units are normalized-squared.

| Endpoint | Target count | Merges | Mean | M2 | Scale |
| --- | ---: | ---: | ---: | ---: | ---: |
| GATED-V_512 | 131072 | 256 | 18.13617706298828 | 23236986.0 | 13.31480884552002 |
| GATED-V_768 | 196608 | 384 | 19.163074493408203 | 40924724.0 | 14.427539825439453 |
| MLP-V_512 | 131072 | 256 | 19.7164363861084 | 28315830.0 | 14.69804859161377 |
| MLP-V_768 | 196608 | 384 | 21.040380477905273 | 46419948.0 | 15.365677833557129 |

| Endpoint | Total relative movement | Duration absolute movement | Gate absolute movement |
| --- | ---: | ---: | ---: |
| GATED-V_512 | 0.2505585510850311 | 0.22032798826694489 | 0.5665290355682373 |
| GATED-V_768 | 0.3028737199375479 | 0.22953803837299347 | 0.5928671956062317 |
| MLP-V_512 | 0.24124825729865026 | 0.15853376686573029 | not applicable |
| MLP-V_768 | 0.3058433763562592 | 0.17809708416461945 | not applicable |

Final parameter/gate norms reconcile with actual checkpoint tensors. Duration
and gate start at zero, so their relative movement is undefined: the collection
record supplies null while retaining raw legacy duration reporting. Movement
shows learning exposure, not useful control. Nonzero held rows are GATED2250
train/186 eval and MLP2241 train/186 eval, with both endpoint evaluations counted.
Full raw return-to-go arrays are not separately replayed/archived; accepted
source checks and the actual moment/publication record establish this boundary.

## Complete resources and closure

Fresh canonical admission passed at09:23:54.672145Z with15634325504 bytes
both physical/effective available. Whole wall475.85s includes both learned
endpoints, H, publication/readback and exit; internal458.106536434032s,
MLP transition237.49987953802338s, residual17.743463565968s.
Conservatively charging unpartitioned residual yields GATED255.24334310399138s
and MLP238.35012046197664s, both below1800s; whole below3600s. Serial study
critical path and summed invocation wall475.85s. Peak RSS556888 KiB/
543.8359375 MiB. Aggregate CPU and isolated component overhead remain unmeasured;
no timing cause or extra performance disposition is inferred.

No scientific or binding deviation was observed. Source surfaces remain fixed.
One accepted P76 submission is spent, zero remain; no retry, extra fit/evaluation,
tuning, second pair or successor occurred. CM observation is complete, with no
live process or pending scientific action. Editing/index returns to DM for
all-outcome intake and Root for integration/any separately allocated next work.

CM-owned `temp/directions/vsp_c1/test/b10_p76_focused1` remains after automatic
approval review rejected both exact cleanup commands as “blocked by policy.”
No repeated removal, bypass or escalation occurred. CM remains creator/cleanup
owner at a later permitted boundary; this housekeeping limitation is independent
of the trustworthy collected scientific output.
