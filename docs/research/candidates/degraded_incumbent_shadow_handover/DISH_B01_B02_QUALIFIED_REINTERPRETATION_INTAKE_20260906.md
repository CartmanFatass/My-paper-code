# DISH B01/B02 qualified reinterpretation intake (2026-09-06)

Written after `DISH-RENEWAL-BOUNDARY-A02-CORRECTION` was accepted (row 1,
`DISH_RENEWAL_BOUNDARY_A02_RESULT_INTAKE_20260906.md`), under the explicit rule of the archived
post-A01 Convergence decision (`ed4363a2e…`, taken in by
`DISH_POST_A01_CONVERGENCE_INTAKE_20260906.md`): B02 keeps its raw outcomes and its inside-MEI
reading, qualified as outcomes of the executed interface; the training-side concern is
source-supported inference; B01 and A03–A05 are not invalidated; no blanket quarantine; no
"timing explains the null"; no training-collection measurement is required first. This intake
revises interpretations only; it changes no recorded number, no lifecycle and no evidence
polarity.

## 1. What is now measured versus inferred

- **Measured (A01, unmodified path):** on the B02 ordinary evaluation path the flag the policy
  consumed at tick n was the native flag of tick n−1; at every admission of the two A01 windows
  the incorporated command was the copied held vector (zero), and every fresh nonzero command
  landed one tick late and was not incorporated (12 of 12 admissions, both windows).
- **Measured (A02, corrected path):** with `renew = [countdown == 0]` the consumed flag and
  native admission coincide on all 64 ticks and all 12 fresh commands are incorporated as
  native projects them; service count unchanged (60/64), energy sum higher.
- **Inferred, source-supported, still unmeasured:** the training collector consumed the same
  ordinary `_StepOutput.renew` pass-through (`collect_update`, scout map 2026-09-05), so the B01
  and B02 learners trained under the same one-tick lag and, on the A03 host's motion path,
  their ordinary rollouts never had a fresh motion command incorporated at an admission tick.
  This is the object the Pro decision allows to be stated as inference; it is not converted into
  a measurement here.

## 2. Qualified readings

- **B02 (`DISH-FORECAST-PACKAGE-B02`, sixteen updates per arm, four final-checkpoint episodes
  per arm):** the recorded service counts 572 / 447 / 433 / 428 per arm and the identical
  470-tick service in both arms stand as measured. The inside-MEI reading (no arm separation at
  the declared minimum effect) stands, qualified: it is an outcome of the executed interface, in
  which the learned fresh motion commands were never incorporated at admission and every
  admission re-committed the held vector. The reading does not say the learned motion would have
  helped, and the null is not attributed to the lag ("timing explains the null" is not claimed);
  it says that B02 did not test the learned motion policy's incorporated commands, and that a
  later learning comparison on the corrected boundary is a different object, not a repeat.
- **B01:** its recorded outcomes and its first-application-valid RETAIN/COPY/SHADOW reading
  stand; the same interface qualification applies to any motion-command-dependent
  interpretation of B01, and the same non-attribution rule.
- **A03–A05:** unchanged; they measured host information, certificate failures and synthesis
  facts that do not depend on the ordinary renewal clock.
- **Prepare/commit proposals:** A02 shows proposals now sampling on admission ticks; whether
  their native gate suffered a matching lag in B01/B02 is still unresolved (`cas_applied` never
  fired in any A01/A02 window). No reading is revised on that basis.

## 3. What is not done

No result is quarantined or annulled; no B01/B02 number is re-derived; no training-collection
replay is ordered; no learning object is selected. The corrected boundary at `3f4d447f6` is the
ordinary path from here. The next object selection belongs to `em:dish:convergence` with A02
and this intake as evidence.

scope: none
