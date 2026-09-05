# DISH B01 production conformance — malformed-smoke intake and C02 boundary

- Direction: `degraded_incumbent_shadow_handover`
- Scientific object: `DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01`
- Failed engineering bytes: `DISH-B01-PRODUCTION-CONFORMANCE-C01`
- New engineering attempt: `DISH-B01-PRODUCTION-CONFORMANCE-C02`
- Evidence class and claim ceiling: unchanged **B — EXPLORE** card; this intake has no
  scientific claim
- Frozen science card:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md`
- C01 objective:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_CONFORMANCE_OBJECTIVE_20260904.md`
- Prior final-suite intake:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_CONFORMANCE_TEST_INTAKE_20260904.md`
- Result-bearing launches: zero

## Direct observation

After the exact origin-predicate repair was independently reviewed with `No material finding`, CM
ran the one final focused-suite invocation authorized for those new bytes. It returned
`3 passed, 1 failed, 1 warning in 8.57s` (wrapper wall `10.097s`). The final-byte existing
regressions returned `4 passed, 1 warning in 10.93s` (wrapper wall `12.820s`). CM stopped before
`project-cost`, staging, commit, admission, or any scientific activity.

The same smoke still required a naturally reset production panel row to reach `origin_valid`
within 1,100 ticks. Direct inspection shows this does not implement C01 objective §6, which
requires the smoke to use an **explicit TEST fixture** while traversing the new production APIs
and publication path. The owned production backend already exposes
`b01_production_test_fixture(..., test_mode=0)` for exactly that technical purpose, and the native
conformance category already uses it. Natural panel rows are allowed to produce no trigger; that
outcome is a frozen B01 result-rule input only in an admitted seed invocation and is not a
technical-failure predicate.

The second failed suite therefore quarantines the C01 test harness as incomplete. It does not
refute the repaired production predicate, does not establish that a scientific row triggers or
does not trigger, and does not consume B01. No normal-panel predicate, evaluator, branch, learner,
or result rule may be changed in response.

## C02 exact objective

C02 owns only
`tests/experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/test_b01.py`.
It replaces the smoke's natural `_reset_row(..., panel()[0])` prefix and trigger assertion with
the existing native-owned `b01_production_test_fixture(width=1, origin_valid=True)`, whose state
remains `test_mode=0`. The smoke must still traverse `prepare_b01_application`, immutable
three-way `clone_b01_prepared_batches`, one branch policy forward and completion for each arm,
JSON publication, and the runner's non-result `project-cost` mode in under 60 seconds.

C02 may adjust only imports and assertions made obsolete by removing the natural prefix. It may
not edit production code, the science card, panel, predicate, learner, evaluator, runner, result
rule, other tests, or any branch semantics. It adds no test, retry loop, repeated-smoke machinery,
or section-4 item. The preceding C01 invocations remain quarantined technical evidence; this is
one explicit new-attempt invocation on different test-harness bytes. If C02's single final suite
fails, the chain stops without another local repair authorization.

Independent static review must confirm the test uses the explicit `test_mode=0` fixture and still
exercises the required production/publication path. Only after `No material finding` may CM run
the final-byte existing regressions, one C02 final focused suite, and non-result `project-cost`.
All must directly succeed before the implementation can be committed and pushed. `run`,
`admit-memory`, seeds, and scientific result roots remain forbidden.

## Decisions this intake produces

### Decision 1 — C01 smoke-harness disposition (object tier)

Options:

- **(a)** quarantine the malformed C01 smoke harness and open the test-only C02 correction above;
- **(b)** stop before technical acceptance and leave B01 unconsumed; or
- **(c)** force a normal panel row to trigger by changing the production predicate, or interpret
  the observed no-trigger as B evidence.

Recommendation: **(a)**. It implements the already frozen verification wording without inspecting
or changing any scientific outcome. Option (b) abandons an isolated test-contract defect. Option
(c) is outcome-informed and changes or pre-empts the B object.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This reversible decision authorizes only the C02 test-harness bytes, independent
review, one final suite, regressions, and non-result cost projection. It does not authorize a
result-bearing launch.

## Bounded reading and next discriminator

Claim ceiling remains the unchanged B/EXPLORE ceiling. Strongest support for the engineering
diagnosis is the exact mismatch between the smoke implementation and objective §6 plus the
existing explicit native fixture. Strongest contradiction is that the corrected fixture has not
yet passed the whole final suite on final bytes. The next discriminator is C02 static review and
its single final verification invocation; only a clean return can reopen launch admission.
