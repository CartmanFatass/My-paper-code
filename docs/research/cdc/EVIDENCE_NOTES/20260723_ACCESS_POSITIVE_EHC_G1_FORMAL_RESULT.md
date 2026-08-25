# ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1 formal result

Date: 2026-07-23

```text
source_commit=de9a315b4969ee6920be08a3d911d559fe362f03
run=logs/formal_access_positive_ehc_g1_cpu_20260723_de9a315_r2
backend=cpu
torch_threads=1
formal=true
result=ORDINARY_EXPLANATION_G1
conclusion_bearing_iteration=2
iterations_remaining=3
```

## Evidence closure

The registered `train -> evaluate -> analyze` pipeline returned exit code zero
for all three phases. The formal validator rederived every source, evaluation,
audit and result predicate from the referenced evidence and reproduced the
registered first-match branch. All 15 final checkpoints, 60 evaluation files,
the source-control record and the causal-audit record are present; there are no
operational errors or temporary-result residues.

The source is identifiable and accessible:

- `operational_valid=true` and `source_identifiable=true`;
- 207,494 non-CREATE opportunities and 4,480 lifecycles with at least two;
- maximum arm utility `0.9349483`, CI95 `[0.9293551, 0.9420615]`, above the
  frozen access floor `0.80`.

The learned utilities are nearly identical:

| Arm | Mean utility | CI95 |
|---|---:|---:|
| OR | 0.9344202 | [0.9268957, 0.9420615] |
| DUM | 0.9344202 | [0.9268957, 0.9420615] |
| EHC | 0.9349483 | [0.9293551, 0.9410610] |

Both registered gains equal `0.0005281`, CI95
`[-0.0014028, 0.0026465]`. Their upper bounds are far below the frozen `0.10`
gain gate, so first-match step 7 selects `ORDINARY_EXPLANATION_G1`. This is a
decisive valid negative, not an underpowered result.

The lower-precedence battery is descriptive only. Complete spells populate all
three K bins, but mark-intervention TV is `0.0010994`, C-total KEEP is
`0.0000457`, and C-total RENEW is exactly zero. Opportunity presence therefore
does not imply that the learned commitment channel is behaviorally load-bearing.

## Scientific disposition

The exact G1 source, OR/DUM/EHC comparison, budgets, seeds and result contract
are permanently closed as `ORDINARY_EXPLANATION_G1`. They may not be tuned,
renamed, rerun or rescued. The result selects ordinary recurrence and link-null
as the sufficient explanations for this source. It rejects no-access and shared
base insufficiency here, and it gives no support to a credit-bottleneck rescue.

This result does not show that event-held commitment is generally useless. It
shows that a cue retained within one member lifecycle is reducible to ordinary
recurrent memory, even when event opportunities and commitment records exist.

## Smallest counterexample correction

Three counterexamples explain why this source cannot identify the stronger
algorithmic claim:

1. `CE-RECURRENT-CUE-MEMORY`: a recurrent state owned for the same lifecycle can
   store the cue and emit the required sequence without an external commitment.
2. `CE-LOCAL-UTILITY-DOMINANCE`: utility is earned by within-segment correctness,
   so high value need not depend on state surviving a membership handoff.
3. `CE-DECORATIVE-COMMITMENT-CHANNEL`: natural opportunities and K-bin coverage
   can coexist with near-zero action and utility consequences from changing the
   held mark.

The corrected conjecture is therefore narrower:

> Event-held state can separate from ordinary per-member recurrence only when a
> task-relevant commitment must survive an anonymous lifecycle handoff after the
> creator's recurrent state is no longer available, and when intervention on
> that held state changes the successor sequence and value.

An admissible separating source must satisfy all of the following before any
training claim is interpreted:

- a creator observes information, commits, then leaves before the dependent
  consequence is complete;
- a successor must act on that information after JOIN, with no identity cue or
  observation/history path that reconstructs it;
- the event-held object persists through public lifecycle events rather than a
  privileged agent identifier;
- the matched ordinary comparator has the same current observations, parameter
  scale and training exposure, but its per-member recurrent state legitimately
  resets at the handoff;
- changing the held object from an exact snapshot changes the successor action
  sequence and utility under common future randomness;
- natural mediation and held-out membership/lifetime transport are measured,
  while K bins and instantaneous logit effects remain diagnostics only.

This is an information-ownership boundary, not a request to enlarge EHC, weaken
the comparator, add reward shaping, or choose a favorable seed.

## Retained lemmas and portfolio delta

- Access and source identification remain before mechanism interpretation.
- The sequence mediation tuple remains the measurement contract; surface use,
  lifetime diversity and logit sensitivity remain insufficient.
- C-REC is selected for the exact G1 source.
- C-LINK-NULL is selected for the exact G1 source/comparator pair.
- C-EHC remains live only for cross-lifecycle or cross-member state transport.
- C-BENCH is strengthened: individual within-lifecycle cue memory is not an
  identifying benchmark for event-held commitment.
- C-MEASURE is retained because it correctly exposed the decorative link.

## Next boundary

```text
next_action=CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_EXECUTABLE_DEFINITION
action_class=zero_compute_design
formal_compute=not_launchable_until_evidence_contract_is_frozen
iteration_cost=0
iterations_remaining=3
external_review_required_now=false
```

The next action is to define the smallest anonymous creator-to-successor source
and its information-theoretic controls. It must first prove that the target bit
is unavailable after handoff to the matched per-member recurrent comparator.
No additional G1 run or parameter change is admissible.
