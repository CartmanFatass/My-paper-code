# ACVC uncertain/delayed veto R01 — scientific intake

- Direction: `acvc`
- Object: `ACVC-B-EXPLORE-UNCERTAIN-DELAYED-VETO-R01`
- Card:
  [`ACVC_UNCERTAIN_DELAYED_VETO_R01_SCIENCE_CARD_20260904.md`](ACVC_UNCERTAIN_DELAYED_VETO_R01_SCIENCE_CARD_20260904.md)
- Evidence:
  [`ACVC_UNCERTAIN_DELAYED_VETO_R01_RESULT_EVIDENCE_20260904.md`](ACVC_UNCERTAIN_DELAYED_VETO_R01_RESULT_EVIDENCE_20260904.md)
- Machine result:
  [`ACVC_UNCERTAIN_DELAYED_VETO_R01_RESULT_20260904.json`](ACVC_UNCERTAIN_DELAYED_VETO_R01_RESULT_20260904.json)
- Intake date: `2026-09-04`

## What I checked

I checked the machine result against the frozen card rather than against process success. The
object ID, evidence class, base seed, launch SHA, exact argument vector, single result-bearing
invocation, fresh admission receipt, result-blind cost projection, per-arm wall caps, RNG
namespaces, all required counts, full paired returns, regime/field subgroups, safety and clean-loss
observables, action rates, and exposure measurements are present. The complete flag and zero exit
are consistent with those receipts but are not used as scientific evidence by themselves.

I separately inspected the implementation and the final CM return. The host law, information
boundary, treatment summary, same-information recurrent comparator, exact `DET-CF` rule,
authenticated-probe control, FP32 learner, update counts, seed ownership, reporting references,
and frozen branch logic match the card. The focused suite passed `8` tests in `14.91 s`; the final
review found no material defect. Actual wall-cap enforcement was repaired outcome-blind before the
only scientific launch. No section 4 machinery or section 5 budget breach was accepted.

## Rule applied and result

The frozen complete-result rule was applied verbatim and in order:

1. `B2-A` requires `Delta_A >= 0.25`, treatment harm compatibility, and
   `Delta_AG >= -0.10`.
2. Failing A, `B2-B` requires `Delta_G >= 0.25` and GRU harm compatibility.
3. `B2-C` holds when neither learned arm exceeds the strongest fixed comparator by `0.10` while
   harm-compatible, or every improvement of at least `0.10` breaches a harm limit.
4. Every other complete result is `B2-D`.

`DET-CF` was the strongest fixed comparator. `Delta_A = Delta_G = -0.8645507692`, both learned
arms were not harm-compatible, and `Delta_AG = 0`. Branches A and B fail; branch C holds. I accept
the valid complete result as **`B2-C / FIXED_RULE_CONTAINS`**.

## Observation that bounds the result

Both learners moved at every update, yet both greedy policies chose `PROBE` at every one of the
`49,152` evaluation opportunities and exactly matched `ALWAYS-PROBE` on all `4,096` paired episode
returns. `DET-CF` instead mixed execute and probe and gained `0.864551` return per episode on
average. This is direct evidence that the two declared learned policies are contained on this
one-seed host/budget rung.

The observation does not separate representational impossibility from shared optimizer/objective
bias. The structured history balance existed and its episode-local distributions differed by
regime, but neither learner used that information in its greedy action. A competent
history-conditioned policy has not yet been shown to beat `DET-CF`; absent that headroom fact, a
larger learner run would confound mechanism value with optimization.

## Flags for the owner

- The DM prediction on record was `B2-A`; the observed branch is `B2-C`.
- This is a scientific negative for exactly one host/budget rung, not a direction-wide negative.
- B1 and R01 now share a pattern: learned adaptation is inferior to a competent fixed rule, but for
  different reasons. B1's exact binding made the rule sufficient; R01's two learners collapsed to
  blanket probing before history value itself was established.
- No repeat, tuning, extra seed, or budget increase is licensed by this intake.
- Choosing whether to open a headroom-first family, park, or close is direction tier and is sent to
  `em:acvc:convergence`; no local direction decision is made here.

## Decisions this intake produces

### Decision 1 — accept or quarantine this attempt (object tier)

Options:

- **(a)** accept the complete result and its frozen `B2-C` reading;
- **(b)** quarantine it for a missing count, exposure field, or protected-semantic mismatch;
- **(c)** rerun the unchanged object for execution metadata or a different outcome.

Recommendation: **(a)**. Every prospective learner-side field and integrity receipt is present,
the process completed within its declared caps, and no card mismatch survives inspection. Option
(b) has no factual trigger; option (c) would be result-informed and is prohibited.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** The decision is reversible
at the next clean boundary, changes no frozen meaning, and carries provenance label
`OWNER_DELEGATED`.

### Decision 2 — disposition after a branch-C result (direction tier)

Options to the persistent Convergence node:

- **(a) `RECAST_HEADROOM_FIRST`:** open a small A/RECON family that computes or implements a
  competent same-information history-conditioned policy on the frozen host, before any learner,
  and asks whether native return headroom over `DET-CF` is materially positive;
- **(b) `LEARNER_COMPETENCE_LADDER`:** retain this host and open a result-blind optimizer/budget
  ladder before establishing history-conditioned policy headroom;
- **(c) `PARK_OR_CLOSE`:** make no further ACVC algorithm investment and retain exact binding only
  as a protocol primitive/control.

DM recommendation: **(a)**. It is the least costly discriminator of the surviving explanation. A
history-aware Bayes/dynamic-program or otherwise competent same-information policy beating
`DET-CF` would isolate an optimization problem and justify a later learner object; failure to find
material headroom would make further learner spending unnecessary. Option (b) spends exposure on
an unidentified opportunity, while option (c) is premature after one seed without the headroom
fact.

This decision is not delegated locally. It is escalated at direction tier and the direction parks
at this clean boundary until a complete archived Pro decision exists.

## Claim ceiling and next discriminator

The maximum supported claim is:

> In one complete seed-11 execution of the frozen twelve-opportunity uncertain/delayed host, both
> the structured history gate and same-information GRU learned an always-probe policy and were
> lower-return and non-harm-compatible relative to the competent memoryless confidence/freshness
> rule; this contains these learned policies at this initialization and budget but does not show
> that revealed history lacks native decision value.

The next scientific discriminator, conditional on direction-tier approval, is a headroom-first
same-information history-conditioned competent policy against `DET-CF`, not another R01 learner
run.

