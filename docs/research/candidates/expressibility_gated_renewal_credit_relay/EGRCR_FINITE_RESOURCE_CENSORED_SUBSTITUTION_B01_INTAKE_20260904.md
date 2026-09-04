# EGRCR finite-resource censored-substitution B01 intake — 2026-09-04

Object: `EGRCR-FRCS-B01-20260904`

Evidence class: `B/EXPLORE`

Intake decision: `ACCEPT_VALID / FRCS-D-MIXED`

## What the DM checked

I checked the result document and retained `summary.json` against the frozen card, including:

- exact object ID, production seed `2026090401`, launch SHA `3c9124396`, scientific profile, argv,
  action/mode/utility law, replacement carrier, exact Q, model equations, 32-parameter counts,
  arm order, FP32, initialization mapping, Adam configuration, shared terminal targets, RNG
  namespaces, minibatches, updates, evaluation transform, tie rule, and branch order;
- the fresh admission receipt and both 4 GiB floors;
- nonzero training transitions, learner updates/example exposures, evaluation transitions/episodes,
  exact-cell counts, parameter movement, loss and prediction finiteness, complete summary,
  terminal process observation, stdout and empty stderr;
- the machine-generated cost and exposure lines, arm/invocation wall caps, and the declared
  analytical forward-work difference;
- all `C_Q`, Q-error, source-gradient, allocation-probability, enumerated-utility, sampled-utility,
  count, and resource fields read by the result rule; and
- the rule applied verbatim: generic was competent, the two estimation differences were negative,
  native expected utility difference was positive, so only `FRCS-D-MIXED` matched.

The implementation stayed inside its owned research paths, used no section-4 machinery, and stayed
inside the 2,000-line, 600-line runner, orchestration, test-wall, and machine-time budgets. Tests and
engineering acceptance establish conformance only; the result values establish the B observation.

## Observation that bounds the result

Direct observation: `GENERIC_PAIR` was competent in `8/8` contexts and approximately halved both Q
RMSE (`0.05276` versus `0.09627`) and source-gradient L2 error (`0.05236` versus `0.09820`) relative
to `ASSOCIATION_FACTOR`. Conversely, the factorized critic assigned more probability to the matching
relation (`0.68257` versus `0.66450`) and had `0.0120448` more enumerated temperature-one expected
utility. Both arms had `8/8` greedy competence and exactly equal sampled utility `0.484375`.

Inference, not direct identification: the factorized arm's native expected-utility advantage is
consistent with scale or calibration inflation rather than more accurate credit estimation. It has
the larger Q and gradient errors, and the exact-Q reference is deliberately not an optimal ceiling;
temperature-one utility rises when an already correct ranking is made more extreme. This explanation
fits the discordance, but one seed does not identify its cause.

The result contradicts the DM prediction `FRCS-C-GENERIC-MATCHES-OR-BEATS` only at the smooth native
utility endpoint. It supports the prediction on both primary estimation quantities and generic
competence. The correct update is mixed, not a post-hoc relabeling as a generic win.

## Scientific update and claim ceiling

This result rules out a clean association-factorized finite-data estimation advantage for this exact
architecture/seed/budget. It does not rule out another factorization, multiple seeds, another budget,
common calibration, or finite-resource structured credit generally. Conversely, the positive
utility difference does not establish factorization value because it is accompanied by worse exact
estimation, equal greedy decisions, equal sampled utility, and unequal forward arithmetic.

The claim ceiling remains one fixed four-agent host, one seed, 192 sampled episodes, 128 updates,
the two frozen 32-parameter critics, and the temperature-one evaluator. There is no stable
superiority, relay-information, multi-update policy-training, transfer, variable-`N`, UAV, safety,
or deployment claim.

## Flags for the owner

- The provider-facing direction authority had not yet incorporated the 2026-09-01 Section-11
  finite-resource reactivation; this intake and `DIRECTION.md` now separate that current authority
  from the historical exact-population `PARK` recommendation.
- `resources_unmeasured` is valid because peak RSS is unavailable and this is not a resource claim.
- The factorized forward equation used three times the recorded multiplications and four times the
  additions of the generic equation, although its measured wall was lower. No compute claim is
  available from either fact.
- A common-temperature or common-gap calibration analysis would be outcome-informed. It could be a
  legitimate new B object, but it would change the question from exact critic estimation to policy
  calibration and must not be presented as a repair of this result.

## Decisions this intake produces

### Decision 1 — accept the result (object tier)

Options:

- (a) accept the complete valid result as `resources_unmeasured`;
- (b) quarantine it because peak RSS and the detached external exit code are unavailable; or
- (c) rerun solely to obtain those execution fields.

Recommendation: **(a)**. The fresh admission passed, every learner-side and rule-reading quantity is
complete, the process terminated, stdout named the retained branch, stderr is empty, and the owner
telemetry rule explicitly preserves validity when peak RSS is missing for a non-resource claim.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`.

### Decision 2 — next rung (object tier, direction consequence escalated)

Options:

- (d) run the unchanged three-seed replication despite the card reserving it for branch A;
- (e) locally define an outcome-informed common-scale/calibration B02; or
- (f) select no new local run and ask the persistent direction Convergence node whether the
  finite-resource factorization family should be recast to scale-controlled decision calibration,
  parked, or continued with one new discriminator.

Recommendation: **(f)**. Branch D supplies no clean efficiency polarity, the treatment lost both
registered estimation comparisons, and only branch A prospectively authorized unchanged
three-seed replication. Choosing a new target or family consequence locally would cross into the
direction tier.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (f).** Provenance:
`OWNER_DELEGATED`. This selection is reversible and launches nothing. The direction is parked at a
clean boundary pending `em:expressibility_gated_renewal_credit_relay:convergence`; no local direction
decision exists.

## Recommended direction-tier question

Ask Convergence to choose among `PARK_CURRENT_FACTORIZATION`,
`RECAST_SCALE_CONTROLLED_B02`, and `CONTINUE_UNCHANGED_REPLICATION`, with the DM recommendation
`PARK_CURRENT_FACTORIZATION` unless a scale-controlled object can remain an estimator-efficiency
test rather than a post-hoc policy-temperature rescue. The packet must preserve the exact-population
containment result, the valid mixed observation, the one-seed ceiling, the unequal forward work,
and the fact that no technical or transport outcome has scientific polarity.

## Next discriminator

There is no locally authorized next run. If Convergence selects a recast, the smallest candidate is
one prospectively frozen common-calibration decision test that holds action-gap scale or trust map
fixed across the two already competent critics, then measures whether any native difference remains.
That would be a new B object and cannot rewrite this mixed result.
