# VSPC1 NATIVE HOLD VALUE B08 - E0 result evidence

The sole P73 invocation completed with exit 0, native status COMPLETE, complete
publication readback and no limit/cap breach. Technical acceptance is PASS.
Frozen point-estimate region: DOWN. Both learned mean returns are below H.
All outcomes are retained. No retry, extra evaluation, second pair or successor
was executed. DM owns scientific intake; CM stops after this delivery under the
owner's soft stop, received while this same accepted invocation was active.

[Collected evidence](results/native_hold_value_b08_8401_20260908/evidence.json)
retains native summary, all 96 evaluation rows, matched contrasts/all adverse
identities, checker source/results, hashes, admission and full terminal receipts.
[Staging evidence](VSPC1_NATIVE_HOLD_VALUE_B08_P73_STAGING_EVIDENCE_20260908.json)
and [execution record](VSPC1_NATIVE_HOLD_VALUE_B08_P73_TECHNICAL_20260908.md)
retain exact inputs. This first768 pair stays separate from all512 results;
no causal effect of increasing budget is identified by this comparison.

## Execution identity and terminal facts

Scientific SHA `e9a05af5d51da571642f51c5b7b8f00c96f1c6b5`, master8401, extra initialization840100012.
Wrapper commit `6a433b46e8240b4dd50d67e2f247017a88e5e582`. Handle `vspc1_hold_value_b08_8401_e9a05af5d51d`, PID3032870,
node hmasd-wsl-node, CPU FP32, one process/numerical thread.
Detached cwd `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b08-8401-e9a05af5d51d`; output `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b08_8401_e9a05af5d51d`.
Start2026-09-09 06:58:00 UTC; terminal07:06:25 UTC, exit0 and inactive tmux.
Supervisor and enclosing /usr/bin/time agree at505 seconds.
Raw local collection: `temp/directions/vsp_c1/collection/native_hold_value_b08_8401_e9a05af5d51d/`.

## Native endpoints and frozen rule

| Arm | Mean native J |
| --- | ---: |
| GATED-V | 0.11587725095166812 |
| MLP-V | 0.14974217136462054 |
| H | 0.1564698252671263 |

MLP-V is the ordinary width133 comparator, trained for768 episodes like GATED.
Each contrast has32 identity-matched evaluations conditional on this trained pair.

| Contrast | Mean | Conditional SE | Negative differences |
| --- | ---: | ---: | ---: |
| GATED-V_minus_MLP-V | -0.03386492041295242 | 0.012832801495252571 | 24 |
| GATED-V_minus_H | -0.04059257431545819 | 0.010690974368617696 | 23 |
| MLP-V_minus_H | -0.0067276539025057655 | 0.015046967261040782 | 19 |

Applicable card section4 rule, verbatim:

| Observation | Bounded reading |
| --- | --- |
| Delta<-.01 | DOWN: a native counterexample against this ordinary comparator at768 episodes; prefer wider MLP in8401 and preserve prior positive evidence. |

The point estimate is below-.01. Conditional SE and every adverse identity are
retained without converting this into a training-population statement. Both
learned means are below H, and23 GATED/19 MLP evaluation identities lose to H.
The primary remains reportable, but no usable-control or comparator-competence
claim follows. H remains an untuned attained reference; matching tuned headroom
is absent. One new768 training pair is the independent unit, not32 seeds.
Keep prior positive and negative regimes as context without pooling or assigning
a causal budget effect. The prospective UP(.55) forecast remains for DM scoring.

## Actual768 collection acceptance

Artifact-only check PASS, exit0, 2.356299399980344s complete process.
No model construction, forward, native evaluation or training replay was performed.
Remote/local SHA256 values match summary, episodes, rollouts, both final
checkpoints and admission. All1632 scored episode rows,768 rollouts and3072
epoch records reconcile with417792 native steps (393216 training/24576
evaluation),3072 Adam,1536 total training episodes,96 final evaluations, two
constructors and zero partial steps. Each arm has768 training episodes,384
rollouts and1536 Adam. Global order is GATED train/eval, MLP train/eval, then H.
Reward/J decompositions, held-decision counts, full8401 reset identities and all
three contrast means/conditional SEs agree. Actual Config-derived768 cost strings
also match the frozen train/evaluation/Adam/moment counts.

Checkpoint source/object/configuration identities and actual FP32 finite tensors
pass. Critic counts34817/34827 and wider-MLP second weight/bias(133,128)/(133,),
output weight(1,133) agree. Final parameter/gate norms reconcile with exposure.
Total relative movements are 0.31950438800732206
GATED /0.3303720280320724 MLP. Gate absolute movement
is 0.6652036309242249; duration absolute movements are
0.12950342893600464 /0.15589399635791779.
Their initial norms are zero, so relative movement is undefined; collection
supplies null for that reading while preserving the raw summary's legacy field.

Each arm records196608 targets and384 moment merges with512-row increments.
Normalized-squared losses and final moments match checkpoint/summary and remain
frozen across learned evaluation and MLP's H evaluation:

| Arm | Final mean | Final M2 | Final scale |
| --- | ---: | ---: | ---: |
| GATED-V | 12.43260669708252 | 24627244.0 | 11.19198989868164 |
| MLP-V | 18.009471893310547 | 40562028.0 | 14.363465309143066 |

Both arms have2214 nonzero held training rows and93 evaluation rows. Full raw
return-to-go arrays were not separately replayed/archived; accepted source checks
and actual recorded moment/publication state cover that boundary.

## Complete resources and soft-stop boundary

Fresh actual-node canonical admission passed both floors with
14394122240 bytes available. Whole wall505.00s includes
H/publication/readback/exit; internal pair 489.3177567520179s, MLP transition
278.02797282801475s, residual 15.682243247982115s.
Conservatively charging residual to each arm yields GATED
293.71021607599687s /MLP 226.97202717198525s,
both under1800s and whole under3600s. Serial critical path and summed invocation
wall are505.00s. Peak RSS 557948 KiB (544.87109375 MiB). Aggregate CPU
and isolated component overhead remain unmeasured; no cause of timing variation
is assigned. These optional gaps do not substitute for the measured whole caps.

No scientific or execution-binding deviation was observed. Historical P69 test-wall
qualification and accepted reused coverage remain. New source/tests/records/results
strictly decode as UTF-8. The owner-directed soft stop permitted this already
accepted invocation to finish and forbids new scientific work until resumed.
P73's sole accepted-submission allowance is spent, with zero remaining submissions.
CM has no live process or pending scientific action. DM next completes all-outcome
intake and its restart handoff/policy sync at the clean boundary, then stops.
No new object, seed, evaluation or Pro action is initiated by this delivery.
