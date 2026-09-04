# SCDMP FCEOV replacement invalid-evidence intake

- Date: `2026-08-31`
- Direction: `semigroup_consistent_duration_model_policy`
- Scientific object: `foundation_conditioned_event_order_value`
- Evidence instance: `2026-08-31.2-wave3-fceov-v3-replacement`
- Final validity: `INVALID_EVIDENCE`
- Sole scientific invalidator: `RESULT_ATOM_L_THETA_SCALE_DRIFT`
- Scientific polarity: none
- Scientific-object state: unconsumed
- Evidence-attempt state: quarantined; no resume, salvage, correction or reuse
- Quarantine boundary: no file or outcome from the old `.1` instance was read or compared

## Conclusion

The `.2` replacement is invalid scientific evidence because its create-only final result atom does
not contain the prospectively frozen lower-bound estimand. The freeze requires the single
unit-range-normalized joint lower bound `L_theta`. The implementation instead range-scales each
marginal bound into raw utility units before taking the minimum and publishes that different
quantity as its joint effect lower bound.

This is a result-atom semantic defect. It does not establish a positive, nonpass, null, negative or
mechanism conclusion. The artifact cannot be repaired by computing the required field after final
publication: create-only atomic completeness was part of the frozen assignment. Because the
assignment was not completely implemented, `.2` does not consume the scientific object.

The technical verifier's accepted structure, resource, source-byte and execution observations remain
technical provenance only. They cannot authorize interpretation of `.2` scientific outcome fields.

## Frozen requirement and stored implementation

For each gap `j`, the prospective freeze normalizes by that gap's complete support range and inverts

```text
n * kl(xbar_j || ell_j) = log(20).
```

The only publishable lower bound is

```text
required L_theta = min_j(ell_j - 0.5),
```

a unitless one-sided 95% lower bound for the minimum normalized gap. The frozen atom explicitly
requires this single `L_theta`; three marginal bounds are not standalone or simultaneous results.

The implemented analyzer instead computes

```text
stored marginal_j = R_j * (ell_j - 0.5)
stored joint      = min_j stored marginal_j,
```

where `R_j` is the component's raw support range, and passes that value through fields named
`joint_value_raw_lower` and `joint_effect_lower_bound`. The candidate gaps do not all share the same
range: the two matched/mismatched gaps use `R=B`, while the COMMON gap uses `R=2B`. Consequently the
stored minimum is a raw-utility-scale parameter and is not `L_theta`.

| Contract surface | Prospectively required | Published by `.2` |
| --- | --- | --- |
| Parameter | Minimum normalized gap | Minimum raw-scale gap |
| Formula | `min_j(ell_j-0.5)` | `min_j R_j(ell_j-0.5)` |
| Unit | Unitless normalized range | Native utility |
| Atomic field | Single `L_theta` | `joint_value_raw_lower` / `joint_effect_lower_bound` |
| Scientific disposition | Required for complete result | Scale-drifted; invalid atom |

The sign of both expressions is controlled by the same component signs, so the defect need not
alter a branch in every realization. Branch agreement cannot substitute one estimand for another or
retroactively complete a create-only result artifact.

## Validity reasoning

The following facts decide validity without using any `.2` scientific outcome:

1. `SCDMP_FCEOV_PROSPECTIVE_FINITE_SAMPLE_INFERENCE_FREEZE_20260831.md` defines `L_theta` and includes
   it in the atomic complete result.
2. `IMPLEMENTATION_THRESHOLD.md` repeats the unit-range-normalized definition and claim ceiling.
3. `analysis.py` directly shows that the implementation multiplies every marginal normalized lower
   bound by its component range before taking the minimum.
4. `artifacts.py` publishes that raw-scale minimum as the terminal joint effect lower bound.
5. The fixed component ranges differ, so the two formulas are not aliases or a common-unit
   reparameterization.

This defect existed in the pre-run implementation but escaped result-blind conformance review. Its
discovery after publication does not make it an outcome-dependent objection: the mismatch follows
from the frozen formulas and code types alone and is reproducible on synthetic fixtures without
access to `.2` values.

## Scientific interpretation boundary

Do not quote, summarize, compare or infer from `.2`:

- competence or panel outcomes;
- gap sums, point estimates or signs;
- component or joint p-value bounds;
- lower-bound values;
- terminal scientific disposition;
- apparent support ranges or tape-level patterns.

No `.2` scientific value may enter Direction science, Portfolio decisions, a successor design,
threshold selection, support tightening, sample-size choice or model changes. A technically complete
process with a semantically wrong result atom remains invalid scientific evidence.

The claim ceiling therefore remains prospectively unchanged and unobserved. No statement about
candidate-set dominance, event-order value, learned chronology, duration, semigroup composition,
another state or foundation, transfer, safety, deployment or flight is available from `.2`.

## Quarantine and nonconsumption

Retain `.2` read-only as defect and technical-execution provenance. Do not:

- edit, append or republish its final bundle;
- insert a post-hoc `L_theta` field;
- resume its master, checkpoint, tapes or panel frontier;
- relabel the stored raw-scale bound as the frozen normalized bound;
- use its outcome to modify the next assignment.

The missing atomic estimand means `.2` did not completely implement the frozen scientific
assignment. Under the project-wide incomplete-assignment rule, it is nonconsuming. This does not
create a finite retry budget: another incomplete technical attempt would also be quarantined without
polarity or consumption.

## Fresh unchanged replacement

The next eligible evidence instance is a fresh outcome-blind `.3` replacement after result-blind
repair and review. It remains the unchanged object:

- same host, public state, external `k=13`, treatment and graph-blind comparator simplex;
- same fresh graph-erased foundation, training and competence law;
- same ideal addressed fair-bit tape law;
- same `562` tapes, `24` serial slices and `3,372` cells;
- same three gaps, integer thresholds, KL-IUT, zero margin and stop rule;
- same resource ceilings, prospective assessment, per-invocation 4 GiB admissions and live
  high-watermark telemetry;
- one new canonical result root and fresh internal master, with no reuse from `.1` or `.2`.

Before `.3` is result-eligible, the implementation must:

1. represent the frozen normalized joint lower bound explicitly as `L_theta` or an equally
   unambiguous normalized field;
2. compute `min_j(ell_j-0.5)` before any component-range scaling;
3. prevent raw marginal bounds or a raw-scale joint bound from occupying the scientific `L_theta`
   field;
4. add unequal-range synthetic tests that distinguish the normalized and raw formulas and verify the
   atomic schema;
5. pass unit, fixture, TEST_ONLY native and result-blind end-to-end review without opening `.2`
   scientific values.

This repair changes only evidence representation. It must not use `.2` to change treatment,
comparator, population, endpoint, sample size, thresholds, stopping or claim ceiling.

## Portfolio-relevant consequence

Direction-local recommendation remains `REGISTERED / MEDIUM`: keep the unchanged FCEOV object live,
record `.2` only as a non-consuming invalid attempt, and admit a fresh `.3` only after the normalized
lower-bound atom is implemented and reviewed result-blind. Portfolio authority remains with Root;
this note does not edit it.

## Evidence paths

- `AGENTS.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_FCEOV_PROSPECTIVE_FINITE_SAMPLE_INFERENCE_FREEZE_20260831.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_FCEOV_REPLACEMENT_VALIDITY_AND_INTAKE_20260831.md`
- `experiments/candidates/scdmp_variable_k/foundation_conditioned_event_order_value/analysis.py`
- `experiments/candidates/scdmp_variable_k/foundation_conditioned_event_order_value/artifacts.py`

The `.2` artifact is intentionally not cited as scientific evidence. The old `.1` outcome and result
fields were not inputs to this intake.
