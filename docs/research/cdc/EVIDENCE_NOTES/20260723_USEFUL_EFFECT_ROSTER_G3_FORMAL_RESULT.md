# USEFUL_EFFECT_ROSTER_G3 formal result

Date: 2026-07-23

```text
source_commit=3f636aa7ad43b406734f2f34472ba12ee4e0cd77
run=logs/formal_useful_effect_roster_g3_cpu_20260723_3f636aa_r1
backend=cpu
torch_threads=1
formal=true
result=UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3
conclusion_bearing_iteration=4
iterations_remaining=1
```

## Evidence closure

The registered Luna-low experiment operator completed the exact foreground
`train -> evaluate -> analyze` pipeline with exit code zero in every phase.
Project Manager then ran the formal validator and independently recomputed the
pure first-match selector from serialized predicate inputs.

The evidence closes 15 final update-120 checkpoints, 120 referenced evaluation
files containing 61,440 rows, 640 held-out-joint causal-audit rows, all source
controls and every checkpoint/evaluation reference. The source commit,
authorization token, CPU backend, one-thread condition, exposure, optimizer,
RNG, schema, ledger and temporary-residue contracts pass. Operational validity
and source identifiability are both true.

## Registered result

| Quantity | Mean | CI95 |
|---|---:|---:|
| NO_ROSTER utility | 0.8522461 | [0.8471680, 0.8572266] |
| TEAM_REC utility | 0.8441406 | [0.8359375, 0.8524414] |
| ROSTER_ATTN utility | 0.8938477 | [0.8633789, 0.9163086] |
| `G_team=U_ROSTER_ATTN-U_TEAM_REC` | 0.0497070 | [0.0226563, 0.0699219] |
| `G_null=U_ROSTER_ATTN-U_NO_ROSTER` | 0.0416016 | [0.0096680, 0.0651367] |

ROSTER_ATTN is the maximum-mean arm, but its access interval crosses the frozen
0.90 floor. First-match step 4 therefore returns
`UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3`. Lower-precedence gain and consequence
diagnostics cannot relabel this result.

The consequence battery is not passed. Natural utility is 0.89727 with CI95
[0.86444, 0.92539], roster-intervention TV is 0.14329 with CI95
[0.13509, 0.15451], and adapted-minus-replayed utility is 0.12695 with CI95
[0.08008, 0.16523]. Exact optimal-action probability is only 0.33648 with CI95
[0.32777, 0.34541]. This records a causal roster response without establishing
registered access, exact demand matching or a meaningful >0.10 advantage.

## Narrow diagnostic and correction

The registered held-out-joint deterministic ROSTER_ATTN replicate means are
0.89307, 0.90381, 0.92285, 0.91357 and 0.83594. The access uncertainty is thus
dominated by training-seed instability, not by a shortage of evaluation rows.
This post-result descriptive split does not change the registered branch.

Adding evaluation episodes alone is not the smallest separating action. Four
replicates approach or exceed access while one fails badly; both registered
gain UCBs are also below 0.10. A same-package rerun or larger budget would mix
algorithm stability with rescue of a completed package.

The smallest algorithmic correction is a zero-compute derivation of a
count-preserving multiset roster encoder. Softmax-normalized attention exposes
relative token mass indirectly; the next candidate must preserve absolute
standing-effect multiplicity while retaining permutation invariance, anonymous
lifecycle ownership, the same reward/source and TEAM_REC/NO_ROSTER controls.

## Disposition

The exact G3 package is validly underpowered and is now closed without rerun,
tuning, threshold relaxation or lower-branch rescue. C-EHC remains plausible but
unsupported; C-COORD gains evidence of a real roster-conditioned response but
not sufficient access or advantage.

```text
next_action=COUNT_PRESERVING_ROSTER_ENCODER_G4_DERIVATION
action_class=zero_compute_algorithmic_derivation
iteration_cost=0
iterations_remaining=1
external_review_required_now=false
```
