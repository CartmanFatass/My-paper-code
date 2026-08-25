# EHC G1 sequence-mediation prototype evidence

```text
assignment_id=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1
action_kind=bounded_nonformal_measurement_prototype
source_commit=37d6556a3a4b5bf4ed70a15834e946005354f91f
implementation_commit=1a4fb630d8c3075380cc3c6562199ee3ea28e9de
artifact=logs/nonformal_ehc_sequence_mediation_g1_20260723_pm3
formal=false
conclusion_bearing=false
disposition=MEASUREMENT_PATH_VALID_RECURRENCE_REMAINS_SUFFICIENT
conclusion_bearing_iterations_consumed=0
iterations_remaining=4
next_boundary=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION
```

## Operational closure

The registered CPU-only, one-thread `pm3` run completed 192/192 natural episodes,
384 exact-snapshot event pairs and 384 mark pairs. The two emitted JSON files
reload through the fail-closed validator with `status=COMPLETE`, exact source,
design, seed and cell identity, exact
nested measurement schemas/domains, held-out cross-field equality, and finite
measurements. The final integrated focused suite passed 92 tests.

The first `pm1` artifact exposed an order-sensitive reloaded-dictionary check;
`pm2` then exposed an insufficiently deep disk-validation boundary during the
single integrated advisory review. Both are retained only as diagnostics and
are not evidence. The final `pm3` artifact was regenerated after exact nested
schema/domain and held-out equality validation. Its
measurement tuple is exactly equal to `pm2`, proving the repair changed evidence
validation rather than scientific values.

## Measurement tuple

Values are `fitting / heldout`.

| Controller | persistence difference | instantaneous TV | event/mark sequence hamming | event/mark terminal dU | hidden correctness | natural U |
|---|---:|---:|---:|---:|---:|---:|
| `MECHANISM_CONTROL` | 1 / 1 | .981 / .981 | .667/.667 / 1/1 | .033/.033 / .050/.050 | 1 / 1 | .965 / .954 |
| `RANDOM_USE` | -.056 / -.069 | .981 / .981 | .083/.083 / .083/.083 | 0/0 / ~0/~0 | .5 / .5 | .457 / .459 |
| `EXOGENOUS_LIFETIME` | .315 / .317 | .981 / .981 | 0/0 / 0/0 | .003/.003 / .003/.003 | .588 / .555 | .581 / .546 |
| `LOGIT_WITHOUT_BEHAVIOR` | 1 / 1 | .981 / .981 | 0/0 / 0/0 | .002/.003 / .002/.003 | .5 / .5 | .529 / .509 |
| `RECURRENT_CONTROL` | 0 / 0 | 0 / 0 | 0/0 / 0/0 | 0/0 / 0/0 | 1 / 1 | .965 / .954 |
| `DUM_CONTROL` | 1 / 1 | 0 / 0 | 0/0 / 0/0 | 0/0 / 0/0 | .5 / .5 | .482 / .477 |

## Counterexample disposition

- `CE-RANDOM-USE` keeps high same-state TV but has no policy-dependent
  persistence, no correctness mediation and essentially zero terminal effect.
- `CE-EXOGENOUS-LIFETIME` creates duration structure without sequence response;
  its terminal effect is small and its natural hidden correctness remains weak.
- `CE-LOGIT-WITHOUT-BEHAVIOR` passes lifetime and instantaneous-logit surfaces
  while producing zero later sequence change and chance hidden correctness.

No named counterexample passes the corrected conditions jointly. The
measurement path therefore does the separating job for which the prototype was
built. `MECHANISM_CONTROL` shows the registered event-to-sequence-to-utility
path and transports it to held-out cells.

## Scientific limit and portfolio delta

`RECURRENT_CONTROL` reaches the same hidden correctness and natural utility as
`MECHANISM_CONTROL`. It does not masquerade as an event-held pathway—its EHC
intervention metrics are zero—but it remains a sufficient ordinary explanation
for capability on this source. The prototype therefore validates measurement,
not EHC necessity, superiority, integration, or adoption.

Retain `L-EHC-MEASUREMENT-NECESSITY` and add
`L-EHC-SEQUENCE-MEASUREMENT-EXECUTABLE`: the corrected tuple distinguishes the
three constructed nulls without conflating recurrence with EHC. Strengthen
`C-REC`; keep `C-EHC`, `C-BASE`, `C-CREDIT`, `C-BENCH`, `C-COORD`, and
`C-LINK-NULL` live. G0 remains closed and unchanged.

## Next boundary

The smallest next action is the PM-owned formal executable definition for the
already frozen `ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1` source. It must make
the access-first result contract and the ordinary-explanation outcome explicit,
then implement the trainable OR/DUM/EHC path and focused prelaunch evidence.
No formal run starts until that evidence contract is frozen; this prototype
consumes no conclusion-bearing iteration.
