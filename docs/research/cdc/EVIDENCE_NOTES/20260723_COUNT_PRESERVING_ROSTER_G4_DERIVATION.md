# COUNT_PRESERVING_ROSTER_ENCODER_G4 derivation

Date: 2026-07-23

```text
input_result=UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3
input_source_commit=3f636aa7ad43b406734f2f34472ba12ee4e0cd77
action_class=zero_compute_algorithmic_derivation
iteration_cost=0
iterations_remaining=1
```

## Accepted facts

The G3 source and evidence path are identified. ROSTER_ATTN has the highest
mean held-out-joint utility and a positive roster-intervention response, but its
access CI crosses 0.90, exact optimal-action probability is low, and one of five
training seeds falls to 0.83594. Both registered gain UCBs are below 0.10. More
evaluation rows cannot remove this between-seed failure.

## Counterexamples to the current aggregation

### CE-NORMALIZED-MULTIPLICITY

For identical token embeddings and scores, softmax attention returns the same
convex-average context for one copy or any number of copies. In a variable-N
roster this makes absolute multiplicity indirect. The complete query may still
make the policy expressive, so this is not an impossibility proof; it is an
optimization and conditioning counterexample to treating normalized attention
as an explicit count representation.

### CE-BILINEAR-COUNT-RECOVERY

When normalized attention represents proportions and the query separately
represents active count, exact service counts require their interaction. The G3
head adds a query-only base term to a roster-only treatment term. Query-
conditioned attention can approximate the interaction, but exact demand-minus-
standing-count logits are not a direct linear path. Seed-sensitive learning can
therefore pass average utility without reliable exact demand matching.

### CE-DENOMINATOR-COMPETITION

Every additional roster token changes the softmax denominator and rescales all
other records. A new record with irrelevant lifecycle metadata can perturb the
entire context even when the algorithm should add one local commitment count.
This conflicts with the desired incremental semantics of asynchronous edits.

### CE-MORE-EVALUATION-WITHOUT-ACCESS

The five G3 ROSTER_ATTN replicate means are approximately
`0.893, 0.904, 0.923, 0.914, 0.836`. Increasing evaluation episodes would
estimate the last failed policy more precisely rather than make it accessible.
Support-only extension is therefore not the cheapest separating action.

## Derived necessary conditions

A corrected roster encoder must:

1. preserve absolute commitment multiplicity before any learned normalization;
2. remain invariant to roster permutation and physical-slot reassignment;
3. update additively under one JOIN/RENEW/TERMINAL_REPLACE edit;
4. expose demand-minus-standing-count as a direct low-complexity logit path;
5. retain learned lifecycle metadata without letting it erase the count path;
6. keep actor inputs free of deficit, future reference, identity and reward;
7. preserve the same source, reward, TEAM_REC comparator, budget, thresholds,
   PPO, replay, RNG and causal battery; and
8. demonstrate cross-seed access before gain or mediation is interpreted.

## Minimal algorithmic correction

For masked standing records `r_j`, let `e_j` be the raw four-way selected-effect
one-hot and `phi(r_j)` the shared learned token encoding. Define:

```text
learned_mean = sum_j mask_j * phi(r_j) / sum_j mask_j
effect_count = sum_j mask_j * e_j
count_context = learned_mean + pad(effect_count, hidden_width)
logits_SUM = base(query) + W_roster(count_context)
```

The count skip has no task reward, deficit, identity or future information. It
is a deterministic set statistic of the commitments already available to the
roster mechanism. Because query demand enters `base(query)` and standing counts
enter the additive roster treatment, a linear parameter setting can implement
demand-minus-count logits exactly. The learned mean preserves age, duration and
rejoin metadata while the raw skip prevents multiplicity erasure.

All compared policies instantiate the same complete module inventory. The
new `ROSTER_SUM` arm uses the count context; `ROSTER_ATTN` preserves the exact G3
normalized-attention path as the direct algorithmic comparator; `TEAM_REC`
preserves the ordinary recurrent comparator. Unused treatment modules retain
zero gradients.

## Portfolio delta and next boundary

- C-EHC remains unsupported, but the next test now isolates one algorithmic
  representation correction instead of changing the benchmark.
- C-BENCH remains identified and is frozen unchanged.
- C-COORD retains demand-served utility and the exact roster intervention.
- C-REC remains the strongest ordinary comparator.
- C-MEASURE requires access before lower-precedence gain or battery claims.

```text
next_action=COUNT_PRESERVING_ROSTER_G4_IMPLEMENTATION
formal_compute=not_launchable_until_implementation_acceptance
external_review_required=false
iteration_cost=0
iterations_remaining=1
```
