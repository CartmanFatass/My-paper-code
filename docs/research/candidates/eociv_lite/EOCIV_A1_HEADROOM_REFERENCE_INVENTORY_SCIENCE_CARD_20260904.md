# EOCIV-A1 headroom-reference inventory — science card

- Object: `EOCIV-A1-HEADROOM-REFERENCE-INVENTORY-R01`
- Direction: `eociv_lite`
- Frozen: `2026-09-04T14:03:37Z`
- Evidence class: **A/RECON**
- Result-bearing invocation: **none**; this is a read-only inventory of already committed evidence
- Claim ceiling: answerability of one headroom estimand on the cited EOCIV evidence only
- Object-tier provenance: `OWNER_DELEGATED`

## 1. Question and claim ceiling

Do the committed EOCIV B1--B7, A8, B9/B9R1 and B10 records contain, on one identical native host,
information set, evaluation population and return coordinate, both:

1. a feasible same-information native-return upper reference, `Y_upper`; and
2. a prospectively fixed or tuned competent generic baseline, `Y_generic`,

so that the raw headroom

```text
H = Y_upper - Y_generic
```

is numerically identified?

The card also asks whether any generic/control comparator already beats its treatment while the
upper reference is absent. Such a comparator win is recorded as a relative observation only. It is
not converted into `H`.

**Claim ceiling.** This A/RECON may establish only whether the required matched pair and raw gap
are present in the named committed artifacts. It cannot establish host saturation, receiver-credit
value, payload value, an achievable optimum, learner competence, a threshold, MEI, a direction
lifecycle, or a Portfolio action. It neither reruns nor reinterprets the B objects.

## 2. Frozen source set and qualification rule

The inventory covers these already completed or terminal records:

- B1 `REAL_VALVE_LEARNING_RESULT.json` and its code/science index;
- B2 `PAYLOAD_CONTENT_LEARNABILITY_RESULT.json` and its index;
- B3 `REWARD_CREDIT_LEARNABILITY_RESULT.json` and its index;
- B4 `RECURRENT_RETENTION_LEARNABILITY_RESULT.json` and its index;
- B5 `HOST_REWARD_SNR_DISCRIMINATION_RESULT.json` and its index;
- B6 `ACTOR_ANCHORED_CRITIC_CLIP_ROOT_CROSS_RESULT.json` and its index;
- B7 `EOCIV_B7_ONE_STEP_ROOT_PARTITION_FROZEN_HISTORY_RESULT.json` and its index;
- A8 `EOCIV_A8_EXACT_DYADIC_LEDGER_IDENTIFIABILITY_PROOF_RESULT.json` and its index;
- the zero-activity B9 terminal artifact and index;
- the B9R1 science card, result evidence and intake; and
- the B10 science card, durable result, result evidence and intake.

A pair qualifies only when both values are native returns on the same host version, roots,
profiles, initialisation/tape material, opportunity population, observation/information set,
legal-action set, horizon and aggregation. The generic baseline must have been frozen or tuned
without using the held-out outcome being compared. The upper reference must be a feasible policy,
an exact same-information optimum, or a valid physical/native-return upper bound.

The following do **not** qualify as `Y_upper`:

- the B9R1 one-step Adam L2 displacement bound;
- the B10 cumulative triangle bound on parameter displacement;
- the unchanged actor endpoint merely because it beats a treatment;
- a receiver-versus-source contrast where one arm is harmed more; or
- an arm, optimum or bound from a different object, population, information set or return metric.

Cross-object splicing is forbidden. A generic arm from B1/B2 and a putative reference from another
host panel cannot create a headroom estimate.

## 3. Treatment, comparator and live explanations

The A/RECON treatment is the exact read-only qualification rule above. Its comparator is the
invalid shortcut `H := -Delta_R`, or an analogous treatment-versus-baseline contrast, applied
without a matched upper reference.

The live explanations are kept separate:

1. a generic comparator may beat a treatment even though substantial unused native-return
   headroom remains;
2. a generic comparator may beat a treatment because the host is saturated;
3. a source or treatment arm may simply be harmed, making a relative contrast positive without
   establishing either absolute value or headroom; and
4. older EOCIV objects may contain useful generic controls but on populations or estimands that
   cannot be paired with B9R1/B10.

## 4. Observable, estimand and frozen result rule

For every source object, record:

- host/evaluation population and native-return coordinate;
- the treatment and strongest recorded comparator/control;
- whether a comparator win is directly observed;
- whether a prospectively tuned competent generic baseline is present;
- whether a matched same-information native-return upper reference is present; and
- `H`, only when both qualified numeric endpoints exist.

Apply this rule in order:

1. `A1-INVENTORY-INCOMPLETE`: a named committed record is unavailable, unreadable, nonfinite at a
   required cited endpoint, or cannot be assigned a treatment/comparator role from its own card or
   result.
2. `A1-MATCHED-HEADROOM-IDENTIFIED`: at least one object contains a qualified numeric
   `(Y_upper, Y_generic)` pair on the same frozen return coordinate; publish every raw `H` without
   a threshold or lifecycle inference.
3. `A1-GENERIC-COMPARATOR-WIN-WITHOUT-UPPER`: at least one committed object directly records a
   generic/control/baseline win, but no object contains a qualified matched upper-reference pair;
   publish the relative gaps and report raw headroom as **not identified**.
4. `A1-NO-QUALIFYING-GENERIC-OR-UPPER`: every other complete inventory.

There is no tolerance, MEI margin, value threshold or result-conditioned follow-up in this object.

## 5. Predictions on record

- DM forecast: `A1-GENERIC-COMPARATOR-WIN-WITHOUT-UPPER`. This is a forecast for the inventory
  branch, not independent empirical evidence: all source outcomes predate this card and were
  already available to the direction.
- Owner prediction: `not taken (unattended)`.

## 6. Budget, stop rule, exposure and cost

- Seeds, episodes, transitions, policy calls, learner calls, optimiser calls, checkpoints and
  stochastic draws created by A1: **zero**.
- Result-bearing invocations and arms: **zero**. No memory admission is applicable because no
  scientific process, model, environment or analysis runner is launched.
- Machine-time cap: **zero result-bearing machine time**; ordinary bounded repository reads only.
- Stop rule: stop when every named source has one inventory row and the rule selects one branch.
  Do not open a new evidence root, tune a comparator, construct an oracle, or launch a learner.
- Cost projection: no sweep and no executable arm, therefore no per-arm projection.
- Exposure line: no parameter initialisation or displacement; `not applicable (A/RECON, no
  learner)`.

## 7. Engineering scope, protected semantics and non-goals

This object needs **none** of the default-prohibited machinery in
`docs/project/ENGINEERING_SCOPE_SPEC.md` section 4. It adds no code, runner, test, schema,
registry, validator, telemetry, retry, resume, provenance guard or compatibility layer.

Protected semantics are the exact historical numbers, branch meanings, information sets,
comparators, invalid-attempt status and claim ceilings in the source artifacts. Historical files
are not rewritten. Permitted side effects are this card, one result evidence file, one intake, the
direction summary update and one unattended audit row.

Non-goals: no B launch; no learner; no exact-gate implementation; no RAW-EXACT or hard-open
retuning; no MEI or threshold; no claim that negative `Delta_R` is headroom; no promotion,
closure, park, lifecycle, priority, capacity, fusion, separation, registration or investment
decision; and no Transport or Pro round.

## 8. Object-tier design decision

Options:

- **(a) recommended:** complete the zero-learner A/RECON by applying the frozen inventory rule to
  the already committed evidence, publish the raw comparator gaps and any missing headroom term,
  then stop at a clean boundary;
- **(b):** treat B9R1/B10 negative `Delta_R` as observed headroom without an upper reference; or
- **(c):** launch a new learner/B object or tune a new comparator before establishing the missing
  reference pair.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This is reversible and
labelled `OWNER_DELEGATED`.
