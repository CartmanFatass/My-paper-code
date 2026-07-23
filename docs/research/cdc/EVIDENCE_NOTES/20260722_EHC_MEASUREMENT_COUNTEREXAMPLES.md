# EHC measurement counterexample derivation

```text
assignment_id=EHC_MEASUREMENT_COUNTEREXAMPLE_DERIVATION
source_commit=3b5e86a6ef4e8731a37232df3f1828affb0d62fc
accepted_reconciliation=docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned/30_PM_CODE_SIDE_RECONCILIATION.md
accepted_reconciliation_sha256=700ca469ca131c58186a872dc3d8149dbb35f100910a632de0a81689d43d1a28
action_kind=zero_compute_cdc_derivation
prototype_selected=true
next_boundary=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1
implementation_status=requested_not_authorized
nonformal_compute_status=requested_not_authorized
formal_compute_status=unauthorized
conclusion_bearing_iterations_consumed=0
iterations_remaining=4
```

## Implication under test

Let `N` be natural nondegenerate KEEP/RENEW use, `D` realized lifetime
diversity, `I` same-state commitment/mark intervention sensitivity, `V` an
external utility gain, and `T` event-held temporal commitment. The previously
implicit implication was:

```text
N and D and I and V  =>  T
```

The implication is false. Each premise can be produced by a path that does not
make a policy-selected event persistently organize later behavior.

## Counterexamples

### CE-RANDOM-USE

A nondegenerate state-independent event head samples KEEP/RENEW with fixed
probability. A mark adapter can still alter primitive logits, and extra
capacity can improve utility.

- Preserves: natural support, event-count/lifetime spread, mark sensitivity,
  and possibly external value.
- Violates: policy-dependent persistence and an event-to-sequence-to-value
  causal path. Event timing carries no demand-related commitment.

### CE-EXOGENOUS-LIFETIME

Opportunity spacing, absence, or a fixed schedule determines realized
lifetime. KEEP/RENEW may be natural and nondegenerate, while the environment,
not the learned policy, creates duration diversity.

- Preserves: lifetime diversity, natural event support, mark sensitivity, and
  possibly external value.
- Violates: learned lifetime control. Persistence does not depend on retained
  policy context and cannot transport as a policy mechanism.

### CE-LOGIT-WITHOUT-BEHAVIOR

An uninformative latent with a strong `W_z(m*z)` adapter changes a same-state
primitive distribution and can pass an instantaneous `I_TV` diagnostic. Any
utility gain may come from capacity or immediate action calibration.

- Preserves: logit/action intervention sensitivity, natural event support, and
  possibly external value.
- Violates: stable multi-step behavioral organization, terminal consequence,
  natural mediation, and resistance to a simpler capacity explanation.

## Necessary corrected conditions

The counterexamples derive five necessary separations. They are not an
exhaustive result ontology and are not individually or jointly declared
sufficient proof.

1. **Policy-dependent persistence.** KEEP/RENEW choice and retained duration
   must depend on policy-available event context and exceed matched random-head,
   fixed-hazard, and exogenous-schedule constructions.
2. **Sequence-level intervention.** From one eligible exact snapshot, force
   KEEP versus RENEW under common environment, observation, action and replay
   randomness; measure the later action sequence and terminal completion or
   utility. Instantaneous logit TV alone is insufficient.
3. **Natural mediation.** Natural event choice must be linked through held-state
   persistence and later behavior to external value. Same-state forcing must be
   kept separate from selected natural groups so selection correlation cannot
   masquerade as mediation.
4. **Simpler-explanation resistance.** The claimed path must survive matched
   recurrence/capacity/information controls and the random-event,
   exogenous-lifetime, and uninformative-mark nulls.
5. **Held-out robustness.** The event-to-sequence consequence must persist
   under unseen durations and membership timing/rosters without calendar,
   identity, task-field, or future-reference leakage.

The corrected local support statement is therefore:

```text
access
and policy-dependent persistence
and sequence-level intervention
and natural mediation
and simpler-explanation resistance
and held-out robustness
=> evidence consistent with event-held temporal commitment
```

`N`, `D`, `I`, and `V` remain useful diagnostics. They no longer identify `T`
without the five separations above. Lower-precedence G0 diagnostics remain
unable to relabel the accepted `NO_ACCESS_THIS_BENCHMARK` result.

## Retained lemmas

- `L-BAT`: surface usage, lifetime and logit predicates admit trivial passing
  constructions.
- `L-FORCED-EVENT`: exact-snapshot forcing identifies a local continuation
  consequence; natural event groups do not.
- `L-MARK-TV`: same-state mark intervention identifies a mark-to-primitive
  path, not persistence, utility or semantic usefulness.
- `L-EHC-G0-NO-ACCESS`: the exact G0 first-match result remains closed.
- `L-EHC-MEASUREMENT-NECESSITY`: a support claim must resist all three
  counterexample families through the five necessary conditions above.

No retained lemma says EHC is sufficient, necessary, useful, or useless as an
algorithm family.

## Smallest next separating action

Further source-field completion is not useful. After this derivation, the
cheapest separating action is one bounded nonformal prototype:
`EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1`.

Its evidence contract is intentionally small:

- preserve the independent G1 hidden-duty source, OR/DUM/EHC information
  matching, anonymous lifecycle, temporary-absence freeze/restore,
  `primitive_logits=base_logits+W_z(m*z)`, and primary external utility;
- keep the two-active-step cue and duration support `{6,10,14,18}`; use
  `{6,14}` only in fitting cells and `{10,18}` only in held-out cells, with the
  held-out membership events shifted by one active opportunity and anonymously
  roster-permuted;
- include matched random-event, exogenous-lifetime, and uninformative-mark
  constructions alongside the ordinary recurrent/capacity comparator;
- keep event forcing and mark intervention as separate exact-snapshot CRN
  operations, and collect future sequence plus terminal consequence;
- report whether each of the five necessary conditions is measurable and
  whether any counterexample still passes them.

This prototype is diagnostic only. It has no formal branch, superiority
threshold, mechanism adoption decision, or conclusion-bearing iteration. Its
completion is either a concrete surviving counterexample or an executable
measurement path that distinguishes all three null families. Exact tensor
layout, batching, seeds and bounded CPU resource cap remain PM engineering and
resource-gate choices in the later executable plan.

No implementation or compute is launched by this derivation.
